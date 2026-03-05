"""
Command-line interface for the Lead Generation Pipeline.

Orchestrates ingestion → validation → enrichment → scoring → export.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from scripts.leadgen.exceptions import EmptyExportError, InvalidSABIFormatError
from scripts.leadgen.io import from_apollo_csv, from_sabi_xlsx, write_leads_csv
from scripts.leadgen.models import Lead
from scripts.leadgen.scoring import score_leads
from scripts.leadgen.validator import ValidationReport, validate_leads
from scripts.leadgen.verify import HunterCapExceededError, HunterClient

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="leadgen",
        description="Run the Lead Generation Pipeline end-to-end.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input file (.csv or .xlsx).",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["apollo", "sabi"],
        help="Data source: 'apollo' or 'sabi'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: <input>_processed.csv).",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        default=False,
        help="Enable auto-fix for correctable validation issues.",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        help="Activate Hunter.io email enrichment.",
    )
    return parser


def _resolve_output_path(input_path: Path, explicit_output: Path | None) -> Path:
    """Derive the output CSV path from the input filename if not provided."""
    if explicit_output is not None:
        return explicit_output
    stem = input_path.stem
    return Path.cwd() / f"{stem}_processed.csv"


# ---------------------------------------------------------------------------
# Enrichment helper
# ---------------------------------------------------------------------------


def _enrich_leads(leads: list[Lead], client: HunterClient) -> list[Lead]:
    """Run Hunter.io verification on leads with email but zero confidence.

    Returns a new list — original objects are never mutated.
    """
    enriched: list[Lead] = []
    cap_hit = False

    for lead in leads:
        if cap_hit or not lead.email.strip() or lead.confidence_score != 0:
            enriched.append(lead)
            continue

        try:
            score = client.verify_email(lead.email)
            enriched.append(dataclasses.replace(lead, confidence_score=score))
        except HunterCapExceededError:
            log.warning("Hunter cap exceeded — remaining leads will proceed unenriched")
            cap_hit = True
            enriched.append(lead)

    return enriched


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the lead generation pipeline CLI.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path: Path = args.input_file
    source: str = args.source
    output_path = _resolve_output_path(input_path, args.output)
    auto_fix: bool = args.auto_fix
    enrich: bool = args.enrich

    # --- Pre-flight checks ---
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    if enrich:
        api_key = os.environ.get("HUNTER_API_KEY", "")
        if not api_key:
            print(
                "Error: --enrich requires HUNTER_API_KEY environment variable",
                file=sys.stderr,
            )
            return 1

    # --- Stage 1: Ingest ---
    try:
        if source == "apollo":
            leads = from_apollo_csv(input_path)
        else:
            leads = from_sabi_xlsx(input_path)
    except (
        FileNotFoundError,
        InvalidSABIFormatError,
        EmptyExportError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # --- Stage 2: Validate ---
    report: ValidationReport
    report, leads = validate_leads(leads, auto_fix=auto_fix)

    for line in report.summary_lines():
        print(line)

    # --- Stage 3: Enrich (conditional) ---
    if enrich:
        client = HunterClient(api_key=api_key)
        leads = _enrich_leads(leads, client)

    # --- Stage 4: Score ---
    leads = score_leads(leads, report=report)

    # --- Stage 5: Export ---
    try:
        write_leads_csv(leads, output_path)
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # --- Stage 6: Summary ---
    print(f"Wrote {len(leads)} leads to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
