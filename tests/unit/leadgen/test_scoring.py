"""
Unit tests for the Lead priority scoring and tier mapping pipeline.
"""

import pytest

from scripts.leadgen.models import Lead, Tier, Vertical
from scripts.leadgen.scoring import assign_tier, compute_icp_score


@pytest.fixture
def perfect_lead() -> Lead:
    """Provides a perfectly optimal target matched to standard configuration weights."""
    return Lead(
        company_name="Logistics Iberia SL",
        confidence_score=100,  # Max confidence
        vertical=Vertical.LOGISTICS,  # Valid vertical
        email="info@logisticsiberia.es",  # Local domain
        linkedin_url="https://linkedin.com/company/logisticsiberia",  # Has URL
    )


class TestComputeIcpScore:
    """Tests evaluating exactly how individual target params cascade into scores."""

    def test_perfect_lead_scores_100(self, perfect_lead: Lead):
        """A full match lead maxes the entire scoring tree natively bounding at 100."""
        import dataclasses

        # perfect lead: confidence(100) -> 40 points
        # vertical -> 20 points
        # explicit revenue needed for 10 points
        lead = dataclasses.replace(perfect_lead, revenue_est="€10M-€20M")
        # clean company name -> 10 points
        # email valid domain -> 10 points
        # linkedin url -> 10 points
        assert compute_icp_score(lead) == 100

    def test_zero_confidence_penalises_score(self, perfect_lead: Lead):
        """Lack of Hunter visibility severely drops the rating weight."""
        import dataclasses

        lead = dataclasses.replace(perfect_lead, confidence_score=0, revenue_est="€10M-€20M")
        score = compute_icp_score(lead)
        assert score == 60  # Missed out on the full 40 confidence

    def test_unknown_vertical_penalises_score(self, perfect_lead: Lead):
        """Incorrect/unknown domains drop matching weighting fully."""
        import dataclasses

        lead = dataclasses.replace(perfect_lead, vertical=Vertical.UNKNOWN)
        score = compute_icp_score(lead)
        assert score == 70  # Missed out on 30 points

    def test_foreign_domain_penalises_score(self, perfect_lead: Lead):
        """Foreign domains drop 10 points instead of gaining it locally or via penalty."""
        import dataclasses

        lead = dataclasses.replace(
            perfect_lead, email="info@logisticsiberia.com.ar", revenue_est="€10M-€20M"
        )
        score = compute_icp_score(lead)
        assert score == 90

    def test_missing_linkedin_penalises_score(self, perfect_lead: Lead):
        """Missing structural metadata causes minor negative drift."""
        import dataclasses

        lead = dataclasses.replace(perfect_lead, linkedin_url="", revenue_est="€10M-€20M")
        score = compute_icp_score(lead)
        assert score == 90

    def test_score_bounded_0_to_100(self, perfect_lead: Lead):
        """No scenario allows calculation beyond boundary edges naturally."""
        # Force a severely negative rating (fake email format check)
        bad_lead = Lead(
            company_name="-",
            confidence_score=0,
            vertical=Vertical.UNKNOWN,
            email="spammy@gmail.com",
            linkedin_url="",
        )
        assert compute_icp_score(bad_lead) == 0  # Bounded to 0

        # Attempt to overcalculate perfect leads beyond 100
        import dataclasses

        lead = dataclasses.replace(perfect_lead, confidence_score=150)
        assert compute_icp_score(lead) == 100  # Bounded to 100


class TestAssignTier:
    """Tests boundary tracking for structural string Tier matching."""

    def test_tier_1_assignment(self, perfect_lead: Lead):
        """Max matching targets map to the premier tier securely."""
        assert assign_tier(perfect_lead) == Tier.TIER_1

    def test_tier_4_assignment(self):
        """Disqualified metrics cascade directly to the discard rating."""
        bad_lead = Lead(company_name="none", confidence_score=0)
        assert assign_tier(bad_lead) == Tier.TIER_4

    def test_tier_boundaries_are_exclusive(self, perfect_lead: Lead):
        """Exact matching at boundary points defaults into the specific lower segment natively."""
        import dataclasses

        lead = dataclasses.replace(
            perfect_lead,
            revenue_est="€10M-€20M",
            confidence_score=75,
            email="invalid",
            linkedin_url="",
        )
        # Drop 20 points (email/linkedin)
        # 100 max - 20 missing properties - 10 from confidence drop (75 * .4)
        assert compute_icp_score(lead) == 70
        assert assign_tier(lead) == Tier.TIER_2
