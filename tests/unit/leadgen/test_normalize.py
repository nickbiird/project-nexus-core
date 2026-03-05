"""
Unit tests for data normalization and cleaning functions.
"""

import pytest

from scripts.leadgen.models import Vertical
from scripts.leadgen.normalize import (
    classify_vertical,
    clean_value,
    extract_email,
    sanitize_company_name,
)


class TestCleanValue:
    """Tests for the general string cleaning utility."""

    def test_strips_markdown_email_links(self):
        """Must rip apart markdown link structures correctly."""
        assert clean_value("[john@example.com](mailto:john@example.com)") == "john@example.com"

    def test_strips_stray_quotes(self):
        """Must strip encapsulating quotation marks entirely."""
        assert clean_value('"company name"') == "company name"

    def test_strips_whitespace(self):
        """Must clear leading and trailing whitespace padding."""
        assert clean_value("  value  ") == "value"

    def test_empty_string_passthrough(self):
        """Must process empty strings dynamically."""
        assert clean_value("") == ""


class TestExtractEmail:
    """Tests for business email extraction functionality."""

    def test_finds_valid_email_in_parts(self):
        """Scans the CSV row representation correctly looking for the `@` struct."""
        parts = ["John Doe", "john.doe@company.es", "CEO"]
        assert extract_email(parts) == "john.doe@company.es"

    def test_excludes_gmail_addresses(self):
        """Excludes standard consumer email vectors entirely."""
        parts = ["John Doe", "john.doe@gmail.com", "CEO"]
        assert extract_email(parts) is None

    def test_returns_none_when_no_email(self):
        """Should fall through to returning None."""
        parts = ["John Doe", "No Email Available", "CEO"]
        assert extract_email(parts) is None

    def test_handles_markdown_wrapped_email(self):
        """Parses via `clean_value` during match verification phase."""
        parts = ["John Doe", "[jane@domain.com](mailto:jane@domain.com)"]
        assert extract_email(parts) == "jane@domain.com"


class TestClassifyVertical:
    """Tests mapping text keywords sequentially to target enum metrics."""

    @pytest.mark.parametrize(
        "keyword",
        ["logistics", "transporte", "trucking", "freight", "logística"],
    )
    def test_classifies_logistics_keywords(self, keyword: str):
        """Properly matches logistics domains implicitly alongside catch-all."""
        assert classify_vertical(f"{keyword.capitalize()} Corp") == Vertical.LOGISTICS

    @pytest.mark.parametrize(
        "keyword",
        ["construction", "building", "material", "materiales"],
    )
    def test_classifies_construction_keywords(self, keyword: str):
        """Correctly maps to construction enums overriding standard logic boundaries."""
        assert classify_vertical(f"Acme {keyword.upper()} SL") == Vertical.CONSTRUCTION_MATERIALS

    def test_defaults_to_logistics_when_ambiguous(self):
        """Falls back implicitly into the standard operational state machine boundaries."""
        assert classify_vertical("Random Tech Startup") == Vertical.LOGISTICS

    def test_case_insensitive_matching(self):
        """Keyword matching engine ignores case variance inherently."""
        assert classify_vertical("CONSTRUCTION SL") == Vertical.CONSTRUCTION_MATERIALS


class TestSanitizeCompanyName:
    """Tests for company name structural integrity corrections."""

    def test_removes_leading_dash(self):
        """Parses prefix dash logic consistently."""
        assert sanitize_company_name("-Pentrilo Painting") == "Pentrilo Painting"

    def test_removes_title_bleed(self):
        """Strips titles accidentally loaded preceding company designation headers."""
        assert sanitize_company_name("Directora Acme Corp") == "Acme Corp"
        assert sanitize_company_name("CEO SpaceX") == "SpaceX"

    def test_handles_clean_name_passthrough(self):
        """Doesn't modify properly clean data strings erroneously."""
        assert sanitize_company_name("Clean Corp S.A.") == "Clean Corp S.A."
