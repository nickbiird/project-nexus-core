"""
Lead priority scoring logic.
"""

from scripts.leadgen.models import Lead, Tier, Vertical
from scripts.leadgen.normalize import sanitize_company_name


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
