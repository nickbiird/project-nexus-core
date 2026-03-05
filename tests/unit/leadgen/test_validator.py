"""
Unit tests for the lead validation engine (validator.py).
"""

from __future__ import annotations

from scripts.leadgen.models import Lead, Vertical
from scripts.leadgen.validator import (
    _LEAD_NEXT_ACTION_DEFAULT,
    validate_leads,
)

# ---------------------------------------------------------------------------
# Helpers — explicit Lead fixtures
# ---------------------------------------------------------------------------


def _clean_apollo_lead(**overrides: object) -> Lead:
    """A fully clean Apollo lead that should fire no rules."""
    defaults: dict[str, object] = {
        "company_name": "Transportes García",
        "contact_name": "Juan García",
        "email": "juan@transportesgarcia.es",
        "confidence_score": 90,
        "revenue_est": "€10M–€20M",
        "vertical": Vertical.LOGISTICS,
        "linkedin_url": "https://linkedin.com/in/juangarcia",
        "next_action": "Research & Send Email #1",
        "source": "apollo",
    }
    defaults.update(overrides)
    return Lead(**defaults)  # type: ignore[arg-type]


def _clean_sabi_lead(**overrides: object) -> Lead:
    """A fully clean SABI lead that should fire no rules."""
    defaults: dict[str, object] = {
        "company_name": "Transportes García",
        "contact_name": "Juan García",
        "email": "juan@transportesgarcia.es",
        "confidence_score": 90,
        "revenue_est": "€12.5M",
        "vertical": Vertical.LOGISTICS,
        "linkedin_url": "https://linkedin.com/in/juangarcia",
        "next_action": "Research & Send Email #1",
        "source": "sabi",
        "nif": "B12345678",
        "legal_name": "TRANSPORTES GARCIA SL",
        "revenue_eur": 12_500_000,
        "revenue_verified": True,
        "ebitda_eur": 1_500_000,
        "employees": 55,
        "website": "transportesgarcia.es",
        "city": "Barcelona",
        "province": "Barcelona",
        "cnae_primary": "4941",
    }
    defaults.update(overrides)
    return Lead(**defaults)  # type: ignore[arg-type]


# ===================================================================
# V001 — Missing email
# ===================================================================


class TestV001:
    def test_fires_when_empty(self) -> None:
        lead = _clean_apollo_lead(email="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V001" in rule_ids

    def test_fires_when_whitespace(self) -> None:
        lead = _clean_apollo_lead(email="   ")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V001" in rule_ids

    def test_does_not_fire_when_present(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V001" not in rule_ids


# ===================================================================
# V002 — Undeliverable email
# ===================================================================


class TestV002:
    def test_fires_when_email_present_score_zero(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es", confidence_score=0)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V002" in rule_ids

    def test_does_not_fire_when_email_empty(self) -> None:
        """V001 covers this case; V002 must not double-fire."""
        lead = _clean_apollo_lead(email="", confidence_score=0)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V002" not in rule_ids

    def test_does_not_fire_when_score_positive(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es", confidence_score=80)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V002" not in rule_ids


# ===================================================================
# V003 — Low Hunter confidence
# ===================================================================


class TestV003:
    def test_fires_when_low_score(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es", confidence_score=50)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V003" in rule_ids

    def test_does_not_fire_at_zero(self) -> None:
        """Score==0 is V002, not V003."""
        lead = _clean_apollo_lead(email="test@empresa.es", confidence_score=0)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V003" not in rule_ids

    def test_does_not_fire_at_70(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es", confidence_score=70)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V003" not in rule_ids


# ===================================================================
# V004 — Missing company name
# ===================================================================


class TestV004:
    def test_fires_on_empty(self) -> None:
        lead = _clean_apollo_lead(company_name="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V004" in rule_ids

    def test_does_not_fire_when_present(self) -> None:
        lead = _clean_apollo_lead(company_name="Acme Corp")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V004" not in rule_ids


# ===================================================================
# V005 — Personal email domain
# ===================================================================


class TestV005:
    def test_fires_on_gmail(self) -> None:
        lead = _clean_apollo_lead(email="test@gmail.com", confidence_score=50)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V005" in rule_ids

    def test_does_not_fire_on_corporate(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V005" not in rule_ids


# ===================================================================
# V006 — Non-Spain email domain
# ===================================================================


class TestV006:
    def test_fires_on_dot_ar(self) -> None:
        lead = _clean_apollo_lead(email="test@welivery.com.ar")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V006" in rule_ids

    def test_does_not_fire_on_dot_es(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.es")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V006" not in rule_ids

    def test_does_not_fire_on_generic_dot_com(self) -> None:
        lead = _clean_apollo_lead(email="test@empresa.com")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V006" not in rule_ids


# ===================================================================
# V007 — Unknown vertical
# ===================================================================


class TestV007:
    def test_fires_on_unknown(self) -> None:
        lead = _clean_apollo_lead(vertical=Vertical.UNKNOWN)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V007" in rule_ids

    def test_does_not_fire_on_logistics(self) -> None:
        lead = _clean_apollo_lead(vertical=Vertical.LOGISTICS)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V007" not in rule_ids


# ===================================================================
# V008 — Missing LinkedIn URL
# ===================================================================


class TestV008:
    def test_fires_on_empty(self) -> None:
        lead = _clean_apollo_lead(linkedin_url="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V008" in rule_ids

    def test_does_not_fire_when_present(self) -> None:
        lead = _clean_apollo_lead(linkedin_url="https://linkedin.com/in/test")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V008" not in rule_ids


# ===================================================================
# V009 — Next action not set (auto-fixable)
# ===================================================================


class TestV009:
    def test_fires_on_empty(self) -> None:
        lead = _clean_apollo_lead(next_action="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V009" in rule_ids

    def test_does_not_fire_when_set(self) -> None:
        lead = _clean_apollo_lead(next_action="Send follow-up")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V009" not in rule_ids

    def test_auto_fix_false_preserves_original(self) -> None:
        """auto_fix=False: result recorded but lead list unchanged."""
        lead = _clean_apollo_lead(next_action="")
        report, out_leads = validate_leads([lead], auto_fix=False)
        v009 = [r for r in report.advisories if r.rule_id == "V009"]
        assert len(v009) == 1
        assert v009[0].auto_fixable is True
        assert v009[0].fix_value == _LEAD_NEXT_ACTION_DEFAULT
        # Original lead returned unchanged
        assert out_leads[0] is lead
        assert out_leads[0].next_action == ""

    def test_auto_fix_true_returns_corrected_copy(self) -> None:
        """auto_fix=True: new Lead with corrected next_action."""
        original = _clean_apollo_lead(next_action="")
        report, fixed = validate_leads([original], auto_fix=True)
        # Report reflects INPUT state
        v009 = [r for r in report.advisories if r.rule_id == "V009"]
        assert len(v009) == 1
        # Fixed lead has corrected value
        assert fixed[0].next_action == _LEAD_NEXT_ACTION_DEFAULT
        # Original is NOT mutated
        assert original.next_action == ""
        # It's a new object
        assert id(original) != id(fixed[0])

    def test_auto_fix_true_no_copy_when_clean(self) -> None:
        """Clean leads are passed through as-is (same object reference)."""
        lead = _clean_apollo_lead()
        _, fixed = validate_leads([lead], auto_fix=True)
        assert fixed[0] is lead


# ===================================================================
# V010 — Job title in company name
# ===================================================================


class TestV010:
    def test_directora_fires(self) -> None:
        lead = _clean_apollo_lead(company_name="Directora")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V010" in rule_ids

    def test_constructora_directa_does_not_fire(self) -> None:
        """'Constructora Directa SL' must NOT trigger — partial substring."""
        lead = _clean_apollo_lead(company_name="Constructora Directa SL")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V010" not in rule_ids

    def test_ceo_fires(self) -> None:
        lead = _clean_apollo_lead(company_name="CEO de Logística")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V010" in rule_ids

    def test_does_not_fire_on_normal_name(self) -> None:
        lead = _clean_apollo_lead(company_name="Transportes García SL")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.errors}
        assert "V010" not in rule_ids


# ===================================================================
# V011 — Tech/SaaS misclassified
# ===================================================================


class TestV011:
    def test_flowbox_pattern(self) -> None:
        """Flowbox platform misclassified as Logistics."""
        lead = _clean_apollo_lead(
            company_name="Flowbox platform",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V011" in rule_ids

    def test_saas_in_email_domain_no_match(self) -> None:
        """V011 does not fire when SaaS token is only a substring, not a whole word."""
        lead = _clean_apollo_lead(
            company_name="Xpert Co",
            email="info@mysaasly.com",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V011" not in rule_ids

    def test_does_not_fire_on_unknown_vertical(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Tech Solutions",
            vertical=Vertical.UNKNOWN,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V011" not in rule_ids

    def test_does_not_fire_on_normal_logistics(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Transportes García",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V011" not in rule_ids

    def test_fires_on_construction_vertical_too(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Digital Materials Platform",
            vertical=Vertical.CONSTRUCTION_MATERIALS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V011" in rule_ids


# ===================================================================
# V012 — Infrastructure/Port operator misclassified
# ===================================================================


class TestV012:
    def test_hutchison_ports_pattern(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Hutchison Ports BEST",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V012" in rule_ids

    def test_terminal_fires(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Barcelona Terminal Marítima",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V012" in rule_ids

    def test_does_not_fire_on_construction(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Port Materials SL",
            vertical=Vertical.CONSTRUCTION_MATERIALS,
        )
        report, _ = validate_leads([lead])
        # V012 only applies to Logistics
        v012_ids = {r.rule_id for r in report.warnings if r.rule_id == "V012"}
        assert "V012" not in v012_ids

    def test_does_not_fire_on_normal_logistics(self) -> None:
        lead = _clean_apollo_lead(
            company_name="Transportes Barcelona SL",
            vertical=Vertical.LOGISTICS,
        )
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V012" not in rule_ids


# ===================================================================
# V013–V016 — SABI-specific rules
# ===================================================================


class TestV013:
    def test_fires_below_icp(self) -> None:
        lead = _clean_sabi_lead(revenue_eur=3_000_000)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V013" in rule_ids

    def test_fires_above_icp(self) -> None:
        lead = _clean_sabi_lead(revenue_eur=25_000_000)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V013" in rule_ids

    def test_does_not_fire_in_range(self) -> None:
        lead = _clean_sabi_lead(revenue_eur=12_500_000)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V013" not in rule_ids

    def test_does_not_fire_on_apollo_lead(self) -> None:
        lead = _clean_apollo_lead()
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V013" not in rule_ids


class TestV014:
    def test_fires_when_unverified(self) -> None:
        lead = _clean_sabi_lead(revenue_verified=False)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V014" in rule_ids

    def test_does_not_fire_when_verified(self) -> None:
        lead = _clean_sabi_lead(revenue_verified=True)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V014" not in rule_ids

    def test_does_not_fire_on_apollo(self) -> None:
        lead = _clean_apollo_lead()
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V014" not in rule_ids


class TestV015:
    def test_fires_on_holding_pattern(self) -> None:
        lead = _clean_sabi_lead(employees=1, revenue_eur=10_000_000)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V015" in rule_ids

    def test_does_not_fire_on_normal(self) -> None:
        lead = _clean_sabi_lead(employees=55, revenue_eur=10_000_000)
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.warnings}
        assert "V015" not in rule_ids


class TestV016:
    def test_fires_on_empty_website(self) -> None:
        lead = _clean_sabi_lead(website="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V016" in rule_ids

    def test_does_not_fire_when_present(self) -> None:
        lead = _clean_sabi_lead(website="transportesgarcia.es")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V016" not in rule_ids

    def test_does_not_fire_on_apollo(self) -> None:
        lead = _clean_apollo_lead(website="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V016" not in rule_ids


# ===================================================================
# V017 — Apollo-specific: Missing revenue estimate
# ===================================================================


class TestV017:
    def test_fires_on_empty_revenue_est(self) -> None:
        lead = _clean_apollo_lead(revenue_est="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V017" in rule_ids

    def test_does_not_fire_when_present(self) -> None:
        lead = _clean_apollo_lead(revenue_est="€10M–€20M")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V017" not in rule_ids

    def test_does_not_fire_on_sabi(self) -> None:
        lead = _clean_sabi_lead(revenue_est="")
        report, _ = validate_leads([lead])
        rule_ids = {r.rule_id for r in report.advisories}
        assert "V017" not in rule_ids


# ===================================================================
# ValidationReport aggregate tests
# ===================================================================


class TestValidationReport:
    def test_empty_list(self) -> None:
        report, out = validate_leads([])
        assert report.total_leads == 0
        assert report.clean_leads == 0
        assert report.quality_score == 0.0
        assert report.errors == []
        assert report.warnings == []
        assert report.advisories == []
        assert out == []

    def test_quality_score_100_percent(self) -> None:
        lead = _clean_apollo_lead()
        report, _ = validate_leads([lead])
        assert report.quality_score == 100.0

    def test_quality_score_50_percent(self) -> None:
        clean = _clean_apollo_lead()
        dirty = _clean_apollo_lead(email="", company_name="")
        report, _ = validate_leads([clean, dirty])
        assert report.quality_score == 50.0

    def test_quality_score_0_percent(self) -> None:
        dirty = _clean_apollo_lead(email="")
        report, _ = validate_leads([dirty])
        assert report.quality_score == 0.0

    def test_leads_with_errors_sorted_deduped(self) -> None:
        lead0 = _clean_apollo_lead(email="test@empresa.es", confidence_score=0)
        lead1 = _clean_apollo_lead()  # clean
        lead2 = _clean_apollo_lead(email="")
        report, _ = validate_leads([lead0, lead1, lead2])
        assert report.leads_with_errors() == [0, 2]

    def test_leads_with_warnings_sorted_deduped(self) -> None:
        lead0 = _clean_apollo_lead(vertical=Vertical.UNKNOWN)
        lead1 = _clean_apollo_lead()  # clean
        lead2 = _clean_apollo_lead(company_name="", vertical=Vertical.UNKNOWN)
        report, _ = validate_leads([lead0, lead1, lead2])
        assert report.leads_with_warnings() == [0, 2]

    def test_summary_lines_not_empty(self) -> None:
        lead = _clean_apollo_lead(email="")
        report, _ = validate_leads([lead])
        lines = report.summary_lines()
        assert len(lines) > 0
        assert any("Total leads" in line for line in lines)

    def test_advisory_only_counts_as_clean(self) -> None:
        """A lead with only ADVISORYs is still 'clean'."""
        lead = _clean_apollo_lead(linkedin_url="")  # fires V008 (ADVISORY)
        report, _ = validate_leads([lead])
        assert report.clean_leads == 1
        assert report.quality_score == 100.0


# ===================================================================
# Cross-cutting integration tests
# ===================================================================


class TestCrossCutting:
    def test_all_three_severity_levels_on_one_lead(self) -> None:
        """One lead that fires ERROR, WARNING, and ADVISORY simultaneously."""
        lead = _clean_apollo_lead(
            email="test@empresa.es",
            confidence_score=0,       # V002 ERROR
            vertical=Vertical.UNKNOWN,  # V007 WARNING
            linkedin_url="",           # V008 ADVISORY
        )
        report, _ = validate_leads([lead])
        assert len(report.errors) >= 1
        assert len(report.warnings) >= 1
        assert len(report.advisories) >= 1
        error_ids = {r.rule_id for r in report.errors}
        warning_ids = {r.rule_id for r in report.warnings}
        advisory_ids = {r.rule_id for r in report.advisories}
        assert "V002" in error_ids
        assert "V007" in warning_ids
        assert "V008" in advisory_ids

    def test_mixed_sabi_and_apollo_source_gating(self) -> None:
        """SABI rules don't fire on Apollo leads and vice versa."""
        apollo_lead = _clean_apollo_lead(revenue_est="", website="")
        sabi_lead = _clean_sabi_lead(revenue_est="", website="")

        report, _ = validate_leads([apollo_lead, sabi_lead])

        # V017 fires on Apollo (idx 0) but not SABI (idx 1)
        v017_indices = {r.lead_index for r in report.advisories if r.rule_id == "V017"}
        assert 0 in v017_indices
        assert 1 not in v017_indices

        # V016 fires on SABI (idx 1) but not Apollo (idx 0)
        v016_indices = {r.lead_index for r in report.advisories if r.rule_id == "V016"}
        assert 1 in v016_indices
        assert 0 not in v016_indices

    def test_gmail_with_low_confidence(self) -> None:
        """V005 and V003 fire but NOT V001 and NOT V002."""
        lead = _clean_apollo_lead(
            email="test@gmail.com",
            confidence_score=50,
        )
        report, _ = validate_leads([lead])
        all_ids = {r.rule_id for r in report.errors + report.warnings + report.advisories}
        assert "V005" in all_ids
        assert "V003" in all_ids
        assert "V001" not in all_ids
        assert "V002" not in all_ids

    def test_corporate_es_email_score_zero(self) -> None:
        """V002 fires but NOT V001, V003, V005."""
        lead = _clean_apollo_lead(
            email="test@empresa.es",
            confidence_score=0,
        )
        report, _ = validate_leads([lead])
        error_ids = {r.rule_id for r in report.errors}
        warning_ids = {r.rule_id for r in report.warnings}
        assert "V002" in error_ids
        assert "V001" not in error_ids
        assert "V003" not in warning_ids
        assert "V005" not in warning_ids
