"""
Lead validation engine — rule-based diagnostics and optional auto-fix.

Inspects fully-constructed :class:`~scripts.leadgen.models.Lead` objects and
produces structured :class:`ValidationReport` instances.  When ``auto_fix=True``
is passed to :func:`validate_leads`, auto-fixable issues are corrected via
:func:`dataclasses.replace` (respecting the frozen dataclass contract).

No I/O is performed in this module — no file reads, HTTP calls, or subprocesses.
"""

from __future__ import annotations

import dataclasses
import logging
import re
from dataclasses import dataclass, fields
from typing import Literal

from scripts.leadgen.models import Lead, Vertical

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve the default value of Lead.next_action from the live AST
# ---------------------------------------------------------------------------
_LEAD_NEXT_ACTION_DEFAULT: str = ""
for _f in fields(Lead):
    if _f.name == "next_action":
        _LEAD_NEXT_ACTION_DEFAULT = (
            _f.default if isinstance(_f.default, str) else ""
        )
        break

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PERSONAL_DOMAINS: frozenset[str] = frozenset({
    "gmail.com", "hotmail.com", "yahoo.com", "yahoo.es",
    "outlook.com", "icloud.com", "me.com",
})

_FLAGGED_COUNTRY_TLDS: frozenset[str] = frozenset({
    ".ar", ".mx", ".cl", ".co.uk", ".fr", ".de", ".it", ".pt",
})

_GENERIC_TLDS: frozenset[str] = frozenset({
    ".com", ".net", ".org", ".io", ".co",
})

_JOB_TITLE_TOKENS: frozenset[str] = frozenset({
    "director", "directora", "gerente", "responsable",
    "coordinador", "coordinadora", "jefe", "jefa", "manager",
    "ceo", "cfo", "coo", "fundador", "fundadora",
    "propietario", "propietaria",
})

_SAAS_TOKENS: frozenset[str] = frozenset({
    "software", "saas", "platform", "app", "cloud", "tech",
    "digital", "data", "analytics", "ai", "api",
    "ecommerce", "e-commerce",
})

_INFRA_TOKENS: frozenset[str] = frozenset({
    "PORT", "PORTS", "TERMINAL", "TERMINALS", "AIRPORT",
    "AEROPORT", "RAIL", "FERROVIARIO", "FERROVIARIA",
    "MARITIMO", "MARITIMA", "MARÍTIMO", "MARÍTIMA",
})

# Precompiled regex for whole-word job title matching
_JOB_TITLE_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _JOB_TITLE_TOKENS) + r")\b",
    re.IGNORECASE,
)

# Precompiled regex for whole-word SaaS token matching
_SAAS_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _SAAS_TOKENS) + r")\b",
    re.IGNORECASE,
)

# Precompiled regex for whole-word infrastructure token matching (case-insensitive)
_INFRA_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _INFRA_TOKENS) + r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """A single fired rule on a single lead."""

    lead_index: int
    rule_id: str
    severity: Literal["ERROR", "WARNING", "ADVISORY"]
    message: str
    auto_fixable: bool
    fix_value: str | None


@dataclass
class ValidationReport:
    """Aggregate validation summary across all leads."""

    total_leads: int
    clean_leads: int
    errors: list[ValidationResult]
    warnings: list[ValidationResult]
    advisories: list[ValidationResult]

    @property
    def quality_score(self) -> float:
        """Percentage of clean leads (zero ERRORs and zero WARNINGs)."""
        if self.total_leads == 0:
            return 0.0
        return round((self.clean_leads / self.total_leads) * 100, 2)

    def leads_with_errors(self) -> list[int]:
        """Sorted, deduplicated list of lead indices that have ≥1 ERROR."""
        return sorted({r.lead_index for r in self.errors})

    def leads_with_warnings(self) -> list[int]:
        """Sorted, deduplicated list of lead indices that have ≥1 WARNING."""
        return sorted({r.lead_index for r in self.warnings})

    def summary_lines(self) -> list[str]:
        """Plain-text summary of the validation run."""
        lines: list[str] = [
            f"Total leads: {self.total_leads}",
            f"Clean leads: {self.clean_leads}",
            f"Quality score: {self.quality_score}%",
            f"Errors: {len(self.errors)}",
            f"Warnings: {len(self.warnings)}",
            f"Advisories: {len(self.advisories)}",
        ]

        # Per-rule breakdown (only rules that fired)
        rule_counts: dict[str, int] = {}
        for r in self.errors + self.warnings + self.advisories:
            rule_counts[r.rule_id] = rule_counts.get(r.rule_id, 0) + 1
        if rule_counts:
            lines.append("Rule breakdown:")
            for rule_id in sorted(rule_counts):
                lines.append(f"  {rule_id}: {rule_counts[rule_id]}")

        return lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _email_domain(email: str) -> str:
    """Extract the lowercased domain from an email address."""
    if "@" not in email:
        return ""
    return email.rsplit("@", maxsplit=1)[1].strip().lower()


def _email_domain_prefix(domain: str) -> str:
    """Extract the prefix before the first dot of a domain."""
    if "." not in domain:
        return domain
    return domain.split(".")[0]


# ---------------------------------------------------------------------------
# Individual rule implementations
# ---------------------------------------------------------------------------


def _check_v001(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V001 — ERROR — Missing email."""
    if not lead.email.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V001", severity="ERROR",
            message=f"Missing email address (lead: {lead.company_name!r})",
            auto_fixable=False, fix_value=None,
        ))


def _check_v002(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V002 — ERROR — Undeliverable email (Hunter score zero)."""
    if lead.email.strip() and lead.confidence_score == 0:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V002", severity="ERROR",
            message=(
                f"Undeliverable email — Hunter confidence is 0 "
                f"(email: {lead.email!r})"
            ),
            auto_fixable=False, fix_value=None,
        ))


def _check_v003(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V003 — WARNING — Low Hunter confidence."""
    if lead.email.strip() and 0 < lead.confidence_score < 70:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V003", severity="WARNING",
            message=(
                f"Low Hunter confidence score: {lead.confidence_score} "
                f"(email: {lead.email!r})"
            ),
            auto_fixable=False, fix_value=None,
        ))


def _check_v004(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V004 — WARNING — Missing company name."""
    if not lead.company_name.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V004", severity="WARNING",
            message="Missing company name",
            auto_fixable=False, fix_value=None,
        ))


def _check_v005(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V005 — WARNING — Personal email domain."""
    domain = _email_domain(lead.email)
    if domain in _PERSONAL_DOMAINS:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V005", severity="WARNING",
            message=f"Personal email domain detected: {domain!r}",
            auto_fixable=False, fix_value=None,
        ))


def _check_v006(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V006 — WARNING — Non-Spain email domain (geographic mismatch)."""
    domain = _email_domain(lead.email)
    if not domain:
        return
    # Check if the domain ends with a flagged country-code TLD
    for tld in _FLAGGED_COUNTRY_TLDS:
        if domain.endswith(tld):
            results.append(ValidationResult(
                lead_index=idx, rule_id="V006", severity="WARNING",
                message=(
                    f"Non-Spain email domain detected: {domain!r} "
                    f"(ends with {tld!r})"
                ),
                auto_fixable=False, fix_value=None,
            ))
            return


def _check_v007(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V007 — WARNING — Unknown vertical."""
    if lead.vertical == Vertical.UNKNOWN:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V007", severity="WARNING",
            message="Vertical classification is Unknown",
            auto_fixable=False, fix_value=None,
        ))


def _check_v008(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V008 — ADVISORY — Missing LinkedIn URL."""
    if not lead.linkedin_url.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V008", severity="ADVISORY",
            message="Missing LinkedIn URL",
            auto_fixable=False, fix_value=None,
        ))


def _check_v009(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V009 — ADVISORY — Next action not set."""
    if not lead.next_action.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V009", severity="ADVISORY",
            message="Next action is empty",
            auto_fixable=True,
            fix_value=_LEAD_NEXT_ACTION_DEFAULT,
        ))


def _check_v010(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V010 — ERROR — Job title in company name field."""
    name = lead.company_name.strip()
    if not name:
        return
    if _JOB_TITLE_RE.search(name):
        results.append(ValidationResult(
            lead_index=idx, rule_id="V010", severity="ERROR",
            message=(
                f"Company name appears to contain a job title: "
                f"{lead.company_name!r}"
            ),
            auto_fixable=False, fix_value=None,
        ))


def _check_v011(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V011 — WARNING — Tech/SaaS misclassified as Logistics or Construction."""
    if lead.vertical not in (Vertical.LOGISTICS, Vertical.CONSTRUCTION_MATERIALS):
        return

    # Check company name
    if _SAAS_RE.search(lead.company_name):
        results.append(ValidationResult(
            lead_index=idx, rule_id="V011", severity="WARNING",
            message=(
                f"Possible SaaS/tech company misclassified as "
                f"{lead.vertical}: company name {lead.company_name!r}"
            ),
            auto_fixable=False, fix_value=None,
        ))
        return

    # Check email domain prefix
    domain = _email_domain(lead.email)
    if domain:
        prefix = _email_domain_prefix(domain)
        if _SAAS_RE.search(prefix):
            results.append(ValidationResult(
                lead_index=idx, rule_id="V011", severity="WARNING",
                message=(
                    f"Possible SaaS/tech company misclassified as "
                    f"{lead.vertical}: email domain prefix {prefix!r}"
                ),
                auto_fixable=False, fix_value=None,
            ))


def _check_v012(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V012 — WARNING — Infrastructure/Port operator misclassified."""
    if lead.vertical != Vertical.LOGISTICS:
        return
    if _INFRA_RE.search(lead.company_name):
        results.append(ValidationResult(
            lead_index=idx, rule_id="V012", severity="WARNING",
            message=(
                f"Possible infrastructure/port operator misclassified as "
                f"Logistics: {lead.company_name!r}"
            ),
            auto_fixable=False, fix_value=None,
        ))


# --- SABI-specific rules ---


def _check_v013(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V013 — WARNING — Revenue outside ICP range (SABI only)."""
    if lead.source != "sabi":
        return
    if lead.revenue_eur > 0 and (
        lead.revenue_eur < 5_000_000 or lead.revenue_eur > 20_000_000
    ):
        results.append(ValidationResult(
            lead_index=idx, rule_id="V013", severity="WARNING",
            message=(
                f"Revenue €{lead.revenue_eur:,} is outside the "
                f"ICP range (€5M–€20M)"
            ),
            auto_fixable=False, fix_value=None,
        ))


def _check_v014(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V014 — ADVISORY — Revenue unverified (SABI only)."""
    if lead.source != "sabi":
        return
    if not lead.revenue_verified:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V014", severity="ADVISORY",
            message="SABI revenue is unverified",
            auto_fixable=False, fix_value=None,
        ))


def _check_v015(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V015 — WARNING — Employee count anomaly (SABI only)."""
    if lead.source != "sabi":
        return
    if lead.employees < 3 and lead.revenue_eur > 5_000_000:
        results.append(ValidationResult(
            lead_index=idx, rule_id="V015", severity="WARNING",
            message=(
                f"Employee count ({lead.employees}) is suspiciously low for "
                f"revenue €{lead.revenue_eur:,} — likely a holding company"
            ),
            auto_fixable=False, fix_value=None,
        ))


def _check_v016(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V016 — ADVISORY — No website (SABI only)."""
    if lead.source != "sabi":
        return
    if not lead.website.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V016", severity="ADVISORY",
            message="No website — blocks Hunter domain search",
            auto_fixable=False, fix_value=None,
        ))


# --- Apollo-specific rule ---


def _check_v017(lead: Lead, idx: int, results: list[ValidationResult]) -> None:
    """V017 — ADVISORY — Missing revenue estimate (Apollo only)."""
    if lead.source != "apollo":
        return
    if not lead.revenue_est.strip():
        results.append(ValidationResult(
            lead_index=idx, rule_id="V017", severity="ADVISORY",
            message="Missing revenue estimate",
            auto_fixable=False, fix_value=None,
        ))


# Ordered list of all rule checkers
_ALL_RULES = [
    _check_v001, _check_v002, _check_v003, _check_v004, _check_v005,
    _check_v006, _check_v007, _check_v008, _check_v009, _check_v010,
    _check_v011, _check_v012, _check_v013, _check_v014, _check_v015,
    _check_v016, _check_v017,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_leads(
    leads: list[Lead],
    *,
    auto_fix: bool = False,
) -> tuple[ValidationReport, list[Lead]]:
    """Validate a list of leads and optionally auto-fix correctable issues.

    Args:
        leads: The list of :class:`Lead` objects to validate.
        auto_fix: When ``True``, return a new list with auto-fixable issues
            corrected via :func:`dataclasses.replace`.  When ``False``
            (the default), the original list is returned unmodified.

    Returns:
        A tuple of ``(report, output_leads)`` where *report* reflects the
        state of the **input** leads (before any fixes) and *output_leads*
        is either the original list (if ``auto_fix=False``) or a new list
        with corrected copies (if ``auto_fix=True``).
    """
    all_results: list[ValidationResult] = []

    for idx, lead in enumerate(leads):
        for rule_fn in _ALL_RULES:
            rule_fn(lead, idx, all_results)

    # Categorise results
    errors = [r for r in all_results if r.severity == "ERROR"]
    warnings = [r for r in all_results if r.severity == "WARNING"]
    advisories = [r for r in all_results if r.severity == "ADVISORY"]

    # Determine clean leads (zero ERRORs and zero WARNINGs)
    dirty_indices: set[int] = set()
    for r in errors:
        dirty_indices.add(r.lead_index)
    for r in warnings:
        dirty_indices.add(r.lead_index)
    clean_leads = len(leads) - len(dirty_indices)

    report = ValidationReport(
        total_leads=len(leads),
        clean_leads=clean_leads,
        errors=errors,
        warnings=warnings,
        advisories=advisories,
    )

    # Log summary
    for line in report.summary_lines():
        log.info(line)

    if not auto_fix:
        return report, leads

    # --- Auto-fix path ---
    # Group fixable results by lead index
    fixable_by_index: dict[int, list[ValidationResult]] = {}
    for r in all_results:
        if r.auto_fixable and r.fix_value is not None:
            fixable_by_index.setdefault(r.lead_index, []).append(r)

    fixed_leads: list[Lead] = []
    for idx, lead in enumerate(leads):
        fixes = fixable_by_index.get(idx)
        if not fixes:
            fixed_leads.append(lead)
            continue

        # Build replacement kwargs from all fixable results for this lead
        replacements: dict[str, object] = {}
        for fix_result in fixes:
            if fix_result.rule_id == "V009":
                replacements["next_action"] = fix_result.fix_value
                log.info(
                    "Auto-fix applied to lead %d (%s): next_action → %r",
                    idx,
                    lead.company_name,
                    fix_result.fix_value,
                )

        if replacements:
            fixed_leads.append(dataclasses.replace(lead, **replacements))  # type: ignore[arg-type]
        else:
            fixed_leads.append(lead)

    return report, fixed_leads
