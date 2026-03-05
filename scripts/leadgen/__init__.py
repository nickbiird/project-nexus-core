"""
Lead Generation Pipeline for Yellowbird Telemetry.
Exports core models, processing functions, and API clients.
"""

from scripts.leadgen.io import from_apollo_csv, from_sabi_xlsx, write_leads_csv
from scripts.leadgen.models import CSV_HEADERS, Lead, Tier, Vertical
from scripts.leadgen.normalize import (
    classify_vertical,
    clean_value,
    extract_email,
    extract_linkedin,
    sanitize_company_name,
)
from scripts.leadgen.scoring import assign_tier, compute_icp_score
from scripts.leadgen.verify import HunterCapExceededError, HunterClient

__all__ = [
    "CSV_HEADERS",
    "HunterCapExceededError",
    # API Clients
    "HunterClient",
    # Data Models
    "Lead",
    "Tier",
    "Vertical",
    "assign_tier",
    "classify_vertical",
    # Normalization (exporting for specific case needs just in case)
    "clean_value",
    # Priority Scoring
    "compute_icp_score",
    "extract_email",
    "extract_linkedin",
    # IO Adapters
    "from_apollo_csv",
    "from_sabi_xlsx",
    "sanitize_company_name",
    "write_leads_csv",
]
