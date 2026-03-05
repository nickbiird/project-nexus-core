"""
SABI (Bureau van Dijk) data transformation helpers.

Handles Spanish-locale revenue parsing, CNAE-to-vertical mapping,
and company name normalisation for SABI XLSX exports.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from scripts.leadgen.models import Vertical

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Revenue parsing
# ---------------------------------------------------------------------------


def parse_sabi_revenue(raw_value: Any) -> int | None:
    """Convert a SABI revenue field (EUR *thousands*) to whole EUR.

    SABI stores ``Ingresos de explotación`` in thousands of EUR.
    A numeric value of ``12500`` means €12,500,000.  A Spanish-locale
    string ``"12.500"`` also means 12 500 thousands → €12,500,000.

    Args:
        raw_value: The cell value from ``openpyxl`` — may be ``int``,
            ``float``, ``str`` (Spanish locale), or ``None``.

    Returns:
        Revenue in whole EUR, or ``None`` if the value is missing
        or unparseable.
    """
    if raw_value is None or raw_value == "":
        return None

    if isinstance(raw_value, (int, float)):
        return int(raw_value * 1000)

    s = str(raw_value).strip()
    if not s:
        return None

    # Spanish locale: period = thousands separator, comma = decimal
    s = s.replace(".", "")   # strip thousands separator
    s = s.replace(",", ".")  # decimal comma → decimal point
    try:
        return int(float(s) * 1000)
    except ValueError:
        log.warning("Unparseable SABI revenue value: %r", raw_value)
        return None


# ---------------------------------------------------------------------------
# CNAE-to-Vertical mapping  (Section 2.3 of LEADGEN_ARCHITECTURE.md)
# ---------------------------------------------------------------------------
#
# Each entry is  code → (vertical_label, unconditionally_included, reason)
#
CNAE_VERTICAL_MAP: dict[str, tuple[str, bool, str]] = {
    # ─── LOGISTICS / TRANSPORT ───────────────────────────────
    "4941": ("Logistics", True, "Road freight transport — core target"),
    "4942": ("Logistics", True, "Removal services — fleet operators"),
    "5210": ("Logistics", True, "Warehousing and storage"),
    "5221": ("Logistics", True, "Land transport ancillary — forwarding, brokerage"),
    "5224": ("Logistics", True, "Cargo handling — loading/unloading"),
    "5229": ("Logistics", True, "Other transport ancillary — fleet mgmt, planning"),
    "5320": ("Logistics", True, "Courier and express services"),
    "7712": ("Logistics", True, "Truck rental and leasing"),
    # Conditional logistics
    "5222": ("Logistics", False, "Maritime ancillary — include only if also 4941"),
    # Excluded logistics
    "5110": ("Logistics", False, "EXCLUDED: Air passenger transport"),
    "5121": ("Logistics", False, "EXCLUDED: Air freight — large carriers only"),
    "4910": ("Logistics", False, "EXCLUDED: Rail passenger — public sector"),
    "4920": ("Logistics", False, "EXCLUDED: Rail freight — capital-intensive"),
    "5020": ("Logistics", False, "EXCLUDED: Maritime shipping — large operators"),
    "5223": ("Logistics", False, "EXCLUDED: Airport ground handling"),
    "4950": ("Logistics", False, "EXCLUDED: Pipeline transport"),
    # ─── CONSTRUCTION MATERIALS ──────────────────────────────
    # Wholesale / distribution
    "4673": ("Construction Materials", True, "Wholesale — building materials, timber, sanitary"),
    "4674": ("Construction Materials", True, "Wholesale — hardware, plumbing, HVAC"),
    # Cement, concrete, plaster
    "2351": ("Construction Materials", True, "Cement manufacturing"),
    "2352": ("Construction Materials", True, "Lime and plaster manufacturing"),
    "2361": ("Construction Materials", True, "Precast concrete elements"),
    "2362": ("Construction Materials", True, "Plaster construction elements"),
    "2369": ("Construction Materials", True, "Other concrete/cement products"),
    # Ceramics
    "2331": ("Construction Materials", True, "Ceramic tiles and flags"),
    "2332": ("Construction Materials", True, "Bricks and roof tiles"),
    # Glass
    "2311": ("Construction Materials", True, "Flat glass manufacturing"),
    "2312": ("Construction Materials", True, "Flat glass processing — windows, facades"),
    # Metal
    "2511": ("Construction Materials", True, "Steel structures and components"),
    "2512": ("Construction Materials", True, "Metal joinery — doors, windows, frames"),
    # Timber
    "1610": ("Construction Materials", True, "Timber sawmilling"),
    "1623": ("Construction Materials", True, "Timber structures and carpentry"),
    # Quarrying / aggregates
    "0811": ("Construction Materials", True, "Ornamental and building stone extraction"),
    "0812": ("Construction Materials", True, "Sand and gravel extraction"),
    "2370": ("Construction Materials", True, "Stone cutting and finishing"),
    # Conditional construction
    "4675": ("Construction Materials", False, "Chemical wholesale — only if construction-related"),
    "4690": ("Construction Materials", False, "General wholesale — only if secondary CNAE is 4673"),
    # Excluded construction-adjacent
    "4110": ("Construction Materials", False, "EXCLUDED: Real estate promotion"),
    "4121": ("Construction Materials", False, "EXCLUDED: Residential construction"),
    "4321": ("Construction Materials", False, "EXCLUDED: Electrical installation"),
    "4322": ("Construction Materials", False, "EXCLUDED: Plumbing/HVAC installation"),
    "7111": ("Construction Materials", False, "EXCLUDED: Architecture services"),
    "7112": ("Construction Materials", False, "EXCLUDED: Engineering services"),
    "6201": ("Construction Materials", False, "EXCLUDED: Software/SaaS"),
}

# Pre-computed sets for fast look-up
_EXCLUDED_PREFIXES = {"EXCLUDED:"}
_UNCONDITIONAL_CODES: set[str] = {
    code for code, (_, included, reason) in CNAE_VERTICAL_MAP.items()
    if included and not any(reason.startswith(p) for p in _EXCLUDED_PREFIXES)
}

# Keywords that signal a conditional 4675 / 4690 entry is construction-related
_CONSTRUCTION_KEYWORDS = {
    "construcción", "construccion", "adhesivos", "impermeabilización",
    "impermeabilizacion", "materiales de construcción",
    "materiales de construccion", "building material",
    "construction material",
}


def resolve_vertical(
    cnae_primary: str,
    cnae_secondary: str = "",
    activity_description: str = "",
) -> Vertical:
    """Map CNAE code(s) to a :class:`Vertical`, respecting conditional rules.

    Conditional rules (from architecture spec):
    * **5222** (maritime ancillary): included *only* if ``cnae_secondary`` is ``"4941"``.
    * **4675** (chemical wholesale): included *only* if the activity
      description mentions construction-related keywords.
    * **4690** (general wholesale): included *only* if ``cnae_secondary``
      is ``"4673"`` or the description mentions construction materials.

    Explicitly excluded codes (those whose reason string starts with
    ``"EXCLUDED:"``) always map to :pyattr:`Vertical.UNKNOWN`.

    Args:
        cnae_primary: 4-digit CNAE 2009 code (primary activity).
        cnae_secondary: Optional secondary CNAE code.
        activity_description: Free-text activity description from the filing.

    Returns:
        The resolved :class:`Vertical`, or ``Vertical.UNKNOWN`` if the
        code is not in the map, is excluded, or fails a conditional check.
    """
    primary = cnae_primary.strip()
    secondary = cnae_secondary.strip()
    desc_lower = activity_description.lower()

    def _try_code(code: str) -> Vertical | None:
        entry = CNAE_VERTICAL_MAP.get(code)
        if entry is None:
            return None

        vertical_label, unconditional, reason = entry

        # Explicitly excluded codes
        if reason.startswith("EXCLUDED:"):
            return None

        # Unconditionally included
        if unconditional:
            return Vertical(vertical_label)

        # --- Conditional logic ---
        if code == "5222":
            if secondary == "4941":
                return Vertical(vertical_label)
            return None

        if code == "4675":
            if any(kw in desc_lower for kw in _CONSTRUCTION_KEYWORDS):
                return Vertical(vertical_label)
            return None

        if code == "4690":
            if secondary == "4673" or any(kw in desc_lower for kw in _CONSTRUCTION_KEYWORDS):
                return Vertical(vertical_label)
            return None

        # Fallback for any other conditional entry not explicitly handled
        return None

    result = _try_code(primary)
    if result is not None:
        return result

    # If primary didn't resolve, try secondary
    if secondary:
        result = _try_code(secondary)
        if result is not None:
            log.info(
                "Primary CNAE %s unmatched; classified via secondary CNAE %s",
                primary,
                secondary,
            )
            return result

    return Vertical.UNKNOWN


# ---------------------------------------------------------------------------
# Company name helpers
# ---------------------------------------------------------------------------

_LEGAL_SUFFIX_RE = re.compile(
    r",?\s*\b(S\.?L\.?U?\.?|S\.?A\.?U?\.?|S\.?C\.?C?\.?L?\.?P?\.?|S\.?C\.?P\.?)\s*\.?\s*$",
    re.IGNORECASE,
)


def strip_legal_suffix(name: str) -> str:
    """Remove trailing Spanish legal-form suffixes from a company name.

    Handles: SL, SA, SLU, SAU, SCCLP, SCP (with or without periods).

    Args:
        name: Raw company name (e.g. ``"TRANSPORTES GARCIA PEREZ SL"``).

    Returns:
        Name without the legal suffix, stripped of trailing whitespace.
    """
    return _LEGAL_SUFFIX_RE.sub("", name).strip()
