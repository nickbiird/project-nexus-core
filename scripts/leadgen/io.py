"""
File input/output adapters for lead integration and export.
"""

import csv
import logging
from pathlib import Path

from scripts.leadgen.models import CSV_HEADERS, Lead
from scripts.leadgen.normalize import (
    classify_vertical,
    clean_value,
    extract_email,
    extract_linkedin,
)

log = logging.getLogger(__name__)


def from_apollo_csv(path: Path) -> list[Lead]:
    """Parse raw Apollo.io CSV exports into a list of Lead objects.

    Ported directly from the original ingestion logic. Performed line-by-line
    reading with manual splitting to handle Apollo's specific formatting.

    Args:
        path (Path): The pathlib.Path to the Apollo CSV.

    Returns:
        list[Lead]: A list of assembled Lead objects (unverified).
    """
    leads: list[Lead] = []

    with open(path, encoding="utf-8-sig") as f:
        # Skip header
        next(f, None)

        for line in f:
            if len(line.strip()) < 10:
                continue

            # Raw split since Apollo puts email at index 5 or 6 and quote structure is messy
            parts = line.split(",")

            first_name = clean_value(parts[0]) if len(parts) > 0 else ""
            last_name = clean_value(parts[1]) if len(parts) > 1 else ""
            name = f"{first_name} {last_name}".strip()

            company = clean_value(parts[3]) if len(parts) > 3 else ""

            email = extract_email(parts)
            if not email:
                continue

            linkedin = extract_linkedin(parts) or ""
            vertical = classify_vertical(line)

            lead = Lead(
                company_name=company,
                contact_name=name,
                email=email,
                revenue_est="€5M-€20M",  # Matches original hardcoded process_leads logic
                vertical=vertical,
                linkedin_url=linkedin,
                confidence_score=0,
                next_action="Research & Send Email #1",
            )
            leads.append(lead)

    return leads


def from_sabi_xlsx(path: Path) -> list[Lead]:
    """Parse SABI (Bureau van Dijk) XLSX exports into CRM leads.

    NOT YET IMPLEMENTED.

    Expected SABI Columns:
    - Legal Name
    - Trade Name
    - CNAE Code
    - Province
    - Operating Revenue
    - EBITDA
    - Employees
    - Website

    Mapping & Normalisation rules:
    - company_name: "Trade Name" preferred, fallback to "Legal Name"
    - vertical: Map "CNAE Code" string to Vertical enum
    - revenue_est: Parse "Operating Revenue" number to nearest million bucket

    Args:
        path (Path): Path to the SABI Excel file.

    Returns:
        list[Lead]: A list of Lead objects.

    Raises:
        NotImplementedError: Future feature stub.
    """
    # TODO: Implement full SABI extraction logic based on the mappings above.
    raise NotImplementedError(
        "SABI Excel parser not yet implemented. Please refer to docstring for expected spec."
    )


def write_leads_csv(leads: list[Lead], path: Path) -> None:
    """Write Lead objects to a properly formatted CRM CSV file.

    Uses csv.DictWriter with the explicit module CSV_HEADERS to ensure
    perfect column alignment regardless of dataclass shifts.

    Args:
        leads (list[Lead]): The list of processed Lead objects.
        path (Path): Where to save the output CSV.
    """
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()

        for lead in leads:
            # Convert lead.to_row() list back to dict using CSV_HEADERS
            row_dict = dict(zip(CSV_HEADERS, lead.to_row(), strict=True))
            writer.writerow(row_dict)

    log.info("Wrote %d leads to %s", len(leads), path)
