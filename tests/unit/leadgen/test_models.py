"""
Unit tests for the Leadgen models.
"""

from scripts.leadgen.models import Lead, Tier, Vertical


class TestLead:
    """Tests for the Lead dataclass functionality and defaults."""

    def test_lead_default_values(self):
        """Lead should initialize with empty string fields and 0 score."""
        lead = Lead()
        assert lead.company_name == ""
        assert lead.contact_name == ""
        assert lead.email == ""
        assert lead.confidence_score == 0
        assert lead.revenue_est == ""
        assert lead.vertical == Vertical.UNKNOWN
        assert lead.linkedin_url == ""
        assert lead.email_1_sent == ""
        assert lead.email_1_opened == ""
        assert lead.email_2_sent == ""
        assert lead.email_3_sent == ""
        assert lead.reply_received == ""
        assert lead.reply_sentiment == ""
        assert lead.next_action == "Research & Send Email #1"

    def test_lead_to_row_column_order(self):
        """to_row() must return exactly 14 string representations in the correct order."""
        lead = Lead(
            company_name="Acme Corp",
            contact_name="John Doe",
            email="john@acme.com",
            confidence_score=95,
            revenue_est="€10M-€20M",
            vertical=Vertical.LOGISTICS,
            linkedin_url="linkedin.com/in/johndoe",
        )
        row = lead.to_row()
        assert len(row) == 14
        assert row[0] == "Acme Corp"
        assert row[1] == "John Doe"
        assert row[2] == "john@acme.com"
        assert row[3] == "95"
        assert row[4] == "€10M-€20M"
        assert row[5] == "Logistics"
        assert row[6] == "linkedin.com/in/johndoe"
        assert row[7] == ""
        assert row[8] == ""
        assert row[9] == ""
        assert row[10] == ""
        assert row[11] == ""
        assert row[12] == ""
        assert row[13] == "Research & Send Email #1"

    def test_lead_from_row_roundtrip(self):
        """Converting to a dict and back via from_row must be completely identical."""
        original = Lead(
            company_name="Acme Corp",
            contact_name="John Doe",
            email="john@acme.com",
            confidence_score=95,
            revenue_est="€10M-€20M",
            vertical=Vertical.LOGISTICS,
            linkedin_url="linkedin.com/in/johndoe",
        )
        from scripts.leadgen.models import CSV_HEADERS

        row_dict = dict(zip(CSV_HEADERS, original.to_row(), strict=True))

        reconstructed = Lead.from_row(row_dict)
        assert original == reconstructed


class TestEnums:
    """Tests for string enum values."""

    def test_vertical_enum_values(self):
        """Vertical enum should have the correct members."""
        assert Vertical.LOGISTICS == "Logistics"
        assert Vertical.CONSTRUCTION_MATERIALS == "Construction Materials"
        assert Vertical.UNKNOWN == "Unknown"

    def test_tier_enum_values(self):
        """Tier enum should have the correct members."""
        assert Tier.TIER_1 == "Tier 1"
        assert Tier.TIER_2 == "Tier 2"
        assert Tier.TIER_3 == "Tier 3"
        assert Tier.TIER_4 == "Tier 4"
