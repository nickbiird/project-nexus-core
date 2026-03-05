"""
Unit tests for SABI adapter logic (sabi.py) and SABI-related model extensions.
"""

from scripts.leadgen.models import CSV_HEADERS, Lead, Vertical
from scripts.leadgen.sabi import parse_sabi_revenue, resolve_vertical, strip_legal_suffix

# ---------------------------------------------------------------------------
# parse_sabi_revenue
# ---------------------------------------------------------------------------


class TestParseSabiRevenue:
    """Revenue parsing must handle int, float, Spanish-locale strings, and nulls."""

    def test_int_input(self) -> None:
        """Plain integer in EUR thousands → whole EUR."""
        assert parse_sabi_revenue(12500) == 12_500_000

    def test_float_input(self) -> None:
        """Float value in EUR thousands → whole EUR."""
        assert parse_sabi_revenue(12500.0) == 12_500_000

    def test_spanish_string_no_decimal(self) -> None:
        """Spanish-locale string '12.500' (period = thousands sep) → 12 500 k → €12.5M."""
        assert parse_sabi_revenue("12.500") == 12_500_000

    def test_spanish_string_with_decimal(self) -> None:
        """Spanish-locale string with decimal comma: '12.500,75' → 12 500.75k → €12,500,750."""
        assert parse_sabi_revenue("12.500,75") == 12_500_750

    def test_none_returns_none(self) -> None:
        assert parse_sabi_revenue(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert parse_sabi_revenue("") is None

    def test_whitespace_returns_none(self) -> None:
        assert parse_sabi_revenue("   ") is None

    def test_garbage_returns_none(self) -> None:
        assert parse_sabi_revenue("n/a") is None

    def test_small_int(self) -> None:
        """A value of 5 in EUR thousands → €5,000."""
        assert parse_sabi_revenue(5) == 5_000


# ---------------------------------------------------------------------------
# resolve_vertical
# ---------------------------------------------------------------------------


class TestResolveVertical:
    """CNAE-to-Vertical mapping with conditional and excluded codes."""

    # Unconditional inclusions
    def test_unconditional_logistics(self) -> None:
        assert resolve_vertical("4941") == Vertical.LOGISTICS

    def test_unconditional_construction(self) -> None:
        assert resolve_vertical("4673") == Vertical.CONSTRUCTION_MATERIALS

    def test_warehousing(self) -> None:
        assert resolve_vertical("5210") == Vertical.LOGISTICS

    # Explicit exclusions
    def test_excluded_air_passenger(self) -> None:
        assert resolve_vertical("5110") == Vertical.UNKNOWN

    def test_excluded_air_freight(self) -> None:
        assert resolve_vertical("5121") == Vertical.UNKNOWN

    def test_excluded_real_estate(self) -> None:
        assert resolve_vertical("4110") == Vertical.UNKNOWN

    # Unknown code
    def test_unknown_code(self) -> None:
        assert resolve_vertical("9999") == Vertical.UNKNOWN

    # --- 5222 conditional: maritime ancillary ---
    def test_5222_with_4941_secondary(self) -> None:
        """5222 is included when secondary CNAE is 4941."""
        assert resolve_vertical("5222", cnae_secondary="4941") == Vertical.LOGISTICS

    def test_5222_without_4941_secondary(self) -> None:
        """5222 without 4941 as secondary → UNKNOWN."""
        assert resolve_vertical("5222", cnae_secondary="") == Vertical.UNKNOWN

    def test_5222_wrong_secondary(self) -> None:
        assert resolve_vertical("5222", cnae_secondary="9999") == Vertical.UNKNOWN

    # --- 4675 conditional: chemical wholesale ---
    def test_4675_with_construction_desc(self) -> None:
        """4675 included if description mentions construction keywords."""
        assert (
            resolve_vertical("4675", activity_description="Venta de adhesivos para construcción")
            == Vertical.CONSTRUCTION_MATERIALS
        )

    def test_4675_without_construction_desc(self) -> None:
        """4675 without construction keywords → UNKNOWN."""
        assert resolve_vertical("4675", activity_description="Venta de pintura") == Vertical.UNKNOWN

    def test_4675_no_desc(self) -> None:
        assert resolve_vertical("4675") == Vertical.UNKNOWN

    # --- 4690 conditional: general wholesale ---
    def test_4690_with_4673_secondary(self) -> None:
        """4690 included when secondary is 4673."""
        assert (
            resolve_vertical("4690", cnae_secondary="4673")
            == Vertical.CONSTRUCTION_MATERIALS
        )

    def test_4690_with_construction_desc(self) -> None:
        """4690 included when description mentions construction materials."""
        assert (
            resolve_vertical(
                "4690",
                activity_description="distribución de materiales de construcción",
            )
            == Vertical.CONSTRUCTION_MATERIALS
        )

    def test_4690_no_match(self) -> None:
        assert resolve_vertical("4690") == Vertical.UNKNOWN

    # Secondary CNAE fallback
    def test_secondary_fallback(self) -> None:
        """If primary is unknown, secondary is used for classification."""
        assert resolve_vertical("9999", cnae_secondary="4941") == Vertical.LOGISTICS


# ---------------------------------------------------------------------------
# strip_legal_suffix
# ---------------------------------------------------------------------------


class TestStripLegalSuffix:
    """Legal suffix removal for Spanish company names."""

    def test_strip_sl(self) -> None:
        assert strip_legal_suffix("TRANSPORTES GARCIA SL") == "TRANSPORTES GARCIA"

    def test_strip_sa(self) -> None:
        assert strip_legal_suffix("ACME SA") == "ACME"

    def test_strip_slu(self) -> None:
        assert strip_legal_suffix("EMPRESA XYZ SLU") == "EMPRESA XYZ"

    def test_strip_sau(self) -> None:
        assert strip_legal_suffix("CONSTRUCTORA SAU") == "CONSTRUCTORA"

    def test_strip_with_periods(self) -> None:
        assert strip_legal_suffix("ACME S.L.") == "ACME"

    def test_no_suffix(self) -> None:
        assert strip_legal_suffix("TRANSPORTES GARCIA") == "TRANSPORTES GARCIA"

    def test_empty(self) -> None:
        assert strip_legal_suffix("") == ""

    def test_comma_separated(self) -> None:
        assert strip_legal_suffix("TRANSPORTES GARCIA, SL") == "TRANSPORTES GARCIA"


# ---------------------------------------------------------------------------
# Model integration smoke tests
# ---------------------------------------------------------------------------


class TestLeadModelSabiFields:
    """Verify that Lead construction and CSV parity hold after SABI field additions."""

    def test_default_lead_no_args(self) -> None:
        """Lead() with zero arguments must succeed (all fields have defaults)."""
        lead = Lead()
        assert lead.source == "apollo"
        assert lead.nif == ""

    def test_csv_headers_parity(self) -> None:
        """CSV_HEADERS length must exactly match Lead().to_row() length."""
        assert len(CSV_HEADERS) == len(Lead().to_row())

    def test_sabi_lead_construction(self) -> None:
        """A SABI-sourced Lead can be constructed with the new fields."""
        lead = Lead(
            company_name="Transportes Garcia",
            nif="B12345678",
            legal_name="TRANSPORTES GARCIA PEREZ SL",
            revenue_eur=12_500_000,
            revenue_verified=True,
            vertical=Vertical.LOGISTICS,
            source="sabi",
        )
        assert lead.company_name == "Transportes Garcia"
        assert lead.source == "sabi"
        assert lead.revenue_eur == 12_500_000
        assert lead.revenue_verified is True

    def test_apollo_lead_still_works(self) -> None:
        """An Apollo-style Lead constructed without any SABI fields must still work."""
        lead = Lead(
            company_name="Acme Corp",
            contact_name="John Doe",
            email="john@acme.com",
            confidence_score=95,
            revenue_est="€10M-€20M",
            vertical=Vertical.LOGISTICS,
        )
        assert lead.source == "apollo"
        assert lead.nif == ""
        assert lead.revenue_eur == 0
