"""
Lead priority scoring logic.
"""

from __future__ import annotations

import dataclasses
import functools
import logging
from typing import TYPE_CHECKING

from scripts.leadgen.models import Lead, Tier, Vertical
from scripts.leadgen.normalize import sanitize_company_name

if TYPE_CHECKING:
    from scripts.leadgen.validator import ValidationReport

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Score component constants (new engine)
# ---------------------------------------------------------------------------

# Revenue fit — max 30 points
REVENUE_HIGH_BAND_MIN: int = 10_000_000  # €10M
REVENUE_HIGH_BAND_MAX: int = 20_000_000  # €20M
REVENUE_LOW_BAND_MIN: int = 5_000_000  # €5M
REVENUE_HIGH_BAND_POINTS: int = 30
REVENUE_LOW_BAND_POINTS: int = 15

# Vertical alignment — max 20 points
VERTICAL_PRIMARY_POINTS: int = 20  # Logistics
VERTICAL_SECONDARY_POINTS: int = 10  # Construction Materials
VERTICAL_UNKNOWN_POINTS: int = 0

# Contact quality — max 30 points total
CONFIDENCE_HIGH_THRESHOLD: int = 80
CONFIDENCE_MED_THRESHOLD: int = 50
CONFIDENCE_HIGH_POINTS: int = 20
CONFIDENCE_MED_POINTS: int = 10
CONFIDENCE_LOW_POINTS: int = 0
LINKEDIN_BONUS_POINTS: int = 10

# Validation penalties
WARNING_PENALTY_POINTS: int = 5


# ---------------------------------------------------------------------------
# Existing scoring functions (unchanged — existing tests depend on them)
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1024)
def compute_icp_score(lead: Lead) -> int:
    """Computes a 0-100 Ideal Customer Profile (ICP) fit score.

    Weights:
    - 40%: Confidence score
    - 20%: Vertical clarity (not UNKNOWN)
    - 10%: Company name cleanliness
    - 10%: Revenue estimated and not empty/homogeneous
    - 10%: LinkedIn URL present
    - 10%: Email domain is valid corporate (.es or .com)

    Args:
        lead (Lead): The lead to score.

    Returns:
        int: Total ICP fit score (0-100).

    Example:
        >>> lead = Lead(confidence_score=90, vertical=Vertical.LOGISTICS, email="test@test.es", company_name="Test")
        >>> compute_icp_score(lead)
        86
    """
    total_score = 0

    # 40%: Confidence score (direct proportion: confidence_score * 0.4)
    total_score += int(lead.confidence_score * 0.4)

    # 20%: Vertical clarity (not UNKNOWN)
    if lead.vertical != Vertical.UNKNOWN and lead.vertical != "Unknown":
        total_score += 20

    # 10%: Company name cleanliness (no artifacts)
    # If the clean version matches the original, it was already clean
    if lead.company_name and lead.company_name == sanitize_company_name(lead.company_name):
        total_score += 10

    # 10%: Revenue populated and not merely whitespace/empty
    if lead.revenue_est and lead.revenue_est.strip():
        # Could enhance by checking for homogeneous values if necessary,
        # but basic population check meets base requirement
        total_score += 10

    # 10%: linkedin_url present
    if lead.linkedin_url and lead.linkedin_url.strip():
        total_score += 10

    # 10%: email domain is .es or .com (not .com.ar or gmail)
    email_lower = lead.email.lower()
    if email_lower and ("@" in email_lower):
        domain = email_lower.split("@")[-1]
        if (
            (domain.endswith(".es") or domain.endswith(".com"))
            and not domain.endswith(".com.ar")
            and "gmail.com" not in domain
        ):
            total_score += 10

    # Cap at 100 just in case
    return min(100, total_score)


@functools.lru_cache(maxsize=1024)
def assign_tier(lead: Lead) -> Tier:
    """Assigns a priority tier based on ICP score and Hunter confidence.

    Tiering rules:
    - TIER_1: icp_score >= 85 AND confidence_score >= 88
    - TIER_2: icp_score >= 70 AND confidence_score >= 75
    - TIER_3: icp_score >= 50
    - TIER_4: everything else

    Args:
        lead (Lead): The lead to tier.

    Returns:
        Tier: The assigned tier enumeration.

    Example:
        >>> lead = Lead(confidence_score=90)
        >>> # Assuming compute_icp_score(lead) gives something high...
        >>> assign_tier(lead)
        <Tier.TIER_1: 'Tier 1'>
    """
    icp_score = compute_icp_score(lead)

    if icp_score >= 85 and lead.confidence_score >= 88:
        return Tier.TIER_1
    elif icp_score >= 70 and lead.confidence_score >= 75:
        return Tier.TIER_2
    elif icp_score >= 50:
        return Tier.TIER_3
    else:
        return Tier.TIER_4


# ---------------------------------------------------------------------------
# New scoring engine — score_leads (Priority 4)
# ---------------------------------------------------------------------------


def _revenue_points(lead: Lead) -> int:
    """Revenue fit component (max 30 points)."""
    rev = lead.revenue_eur
    if rev <= 0:
        return 0
    if REVENUE_HIGH_BAND_MIN <= rev <= REVENUE_HIGH_BAND_MAX:
        return REVENUE_HIGH_BAND_POINTS
    if REVENUE_LOW_BAND_MIN <= rev < REVENUE_HIGH_BAND_MIN:
        return REVENUE_LOW_BAND_POINTS
    return 0


def _vertical_points(lead: Lead) -> int:
    """Vertical alignment component (max 20 points)."""
    if lead.vertical == Vertical.LOGISTICS:
        return VERTICAL_PRIMARY_POINTS
    if lead.vertical == Vertical.CONSTRUCTION_MATERIALS:
        return VERTICAL_SECONDARY_POINTS
    return VERTICAL_UNKNOWN_POINTS


def _contact_points(lead: Lead) -> int:
    """Contact quality component (max 30 points)."""
    points = 0
    # Hunter confidence sub-signal
    if lead.confidence_score >= CONFIDENCE_HIGH_THRESHOLD:
        points += CONFIDENCE_HIGH_POINTS
    elif lead.confidence_score >= CONFIDENCE_MED_THRESHOLD:
        points += CONFIDENCE_MED_POINTS
    # LinkedIn presence sub-signal (additive)
    if lead.linkedin_url.strip():
        points += LINKEDIN_BONUS_POINTS
    return points


def _penalty_points(
    lead_index: int,
    report: ValidationReport | None,
) -> int:
    """Validation WARNING penalty (deducted per warning)."""
    if report is None:
        return 0
    count = sum(1 for w in report.warnings if w.lead_index == lead_index)
    return count * WARNING_PENALTY_POINTS


def _assign_scored_tier(score: int) -> Tier:
    """Map a clamped 0–100 score to a Tier enum value."""
    if score >= 80:
        return Tier.TIER_1
    if score >= 50:
        return Tier.TIER_2
    return Tier.TIER_3


def score_leads(
    leads: list[Lead],
    *,
    report: ValidationReport | None = None,
) -> list[Lead]:
    """Score and tier a list of leads using the composable sub-rule engine.

    Returns a **new** list of :class:`Lead` objects (same length, same order)
    with ``score`` and ``tier`` populated.  The original list and its lead
    objects are never mutated.

    Args:
        leads: Input leads to score.
        report: Optional :class:`ValidationReport` — when provided, WARNING
            results deduct points from the relevant lead.

    Returns:
        A new list of scored leads.
    """
    scored: list[Lead] = []

    for idx, lead in enumerate(leads):
        rev = _revenue_points(lead)
        vert = _vertical_points(lead)
        contact = _contact_points(lead)
        penalty = _penalty_points(idx, report)

        raw = rev + vert + contact - penalty
        final = max(0, min(100, raw))
        tier = _assign_scored_tier(final)

        log.debug(
            "Lead %d (%s): revenue=%d vertical=%d contact=%d penalty=%d → score=%d tier=%s",
            idx,
            lead.company_name,
            rev,
            vert,
            contact,
            penalty,
            final,
            tier,
        )
        log.info(
            "Scored lead %d (%s): %d → %s",
            idx,
            lead.company_name,
            final,
            tier,
        )

        scored.append(dataclasses.replace(lead, score=final, tier=tier))

    return scored
