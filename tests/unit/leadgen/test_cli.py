"""
Unit tests for the Lead Generation Pipeline CLI orchestration.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.leadgen.cli import main
from scripts.leadgen.exceptions import EmptyExportError, InvalidSABIFormatError
from scripts.leadgen.models import Lead, Tier
from scripts.leadgen.validator import ValidationReport
from scripts.leadgen.verify import HunterCapExceededError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _lead(**kwargs: object) -> Lead:
    return Lead(**kwargs)  # type: ignore[arg-type]


def _empty_report() -> ValidationReport:
    return ValidationReport(
        total_leads=1,
        clean_leads=1,
        errors=[],
        warnings=[],
        advisories=[],
    )


_MOCK_MODULE = "scripts.leadgen.cli"


# ---------------------------------------------------------------------------
# Apollo full pipeline path
# ---------------------------------------------------------------------------


class TestApolloPipeline:
    """Assert correct function calls and ordering for the Apollo path."""

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_full_pipeline(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Apollo pipeline calls ingest → validate → score → write."""
        csv_file = tmp_path / "apollo.csv"
        csv_file.touch()
        out_file = tmp_path / "output.csv"

        raw_leads = [_lead(company_name="A", email="a@b.com")]
        validated_leads = [_lead(company_name="A", email="a@b.com")]
        scored_leads = [_lead(company_name="A", email="a@b.com", score=80, tier=Tier.TIER_1)]
        report = _empty_report()

        mock_ingest.return_value = raw_leads
        mock_validate.return_value = (report, validated_leads)
        mock_score.return_value = scored_leads

        code = main(["--source", "apollo", "--output", str(out_file), str(csv_file)])

        assert code == 0
        mock_ingest.assert_called_once_with(csv_file)
        mock_validate.assert_called_once_with(raw_leads, auto_fix=False)
        mock_score.assert_called_once_with(validated_leads, report=report)
        mock_write.assert_called_once_with(scored_leads, out_file)


# ---------------------------------------------------------------------------
# SABI full pipeline path
# ---------------------------------------------------------------------------


class TestSABIPipeline:
    """Assert correct function calls for the SABI path."""

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_sabi_xlsx")
    def test_full_pipeline(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
    ) -> None:
        xlsx_file = tmp_path / "sabi.xlsx"
        xlsx_file.touch()
        out_file = tmp_path / "output.csv"

        raw_leads = [_lead(company_name="B", source="sabi")]
        report = _empty_report()
        mock_ingest.return_value = raw_leads
        mock_validate.return_value = (report, raw_leads)
        mock_score.return_value = raw_leads

        code = main(["--source", "sabi", "--output", str(out_file), str(xlsx_file)])

        assert code == 0
        mock_ingest.assert_called_once_with(xlsx_file)


# ---------------------------------------------------------------------------
# --auto-fix flag
# ---------------------------------------------------------------------------


class TestAutoFixFlag:
    """Assert auto_fix reaches validate_leads."""

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_auto_fix_true(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
    ) -> None:
        f = tmp_path / "in.csv"
        f.touch()
        mock_ingest.return_value = [_lead()]
        mock_validate.return_value = (_empty_report(), [_lead()])
        mock_score.return_value = [_lead()]

        main(["--source", "apollo", "--auto-fix", str(f)])

        mock_validate.assert_called_once_with([_lead()], auto_fix=True)

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_auto_fix_false(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
    ) -> None:
        f = tmp_path / "in.csv"
        f.touch()
        mock_ingest.return_value = [_lead()]
        mock_validate.return_value = (_empty_report(), [_lead()])
        mock_score.return_value = [_lead()]

        main(["--source", "apollo", str(f)])

        mock_validate.assert_called_once_with([_lead()], auto_fix=False)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Assert CLI exits with code 1 on errors."""

    def test_missing_input_file(self, tmp_path: Path) -> None:
        code = main(["--source", "apollo", str(tmp_path / "nonexistent.csv")])
        assert code == 1

    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_file_not_found_from_ingest(self, mock_ingest: MagicMock, tmp_path: Path) -> None:
        f = tmp_path / "in.csv"
        f.touch()
        mock_ingest.side_effect = FileNotFoundError("gone")

        code = main(["--source", "apollo", str(f)])
        assert code == 1

    @patch(f"{_MOCK_MODULE}.from_sabi_xlsx")
    def test_invalid_sabi_format(self, mock_ingest: MagicMock, tmp_path: Path) -> None:
        f = tmp_path / "bad.xlsx"
        f.touch()
        mock_ingest.side_effect = InvalidSABIFormatError("bad format")

        code = main(["--source", "sabi", str(f)])
        assert code == 1

    @patch(f"{_MOCK_MODULE}.from_sabi_xlsx")
    def test_empty_export_error(self, mock_ingest: MagicMock, tmp_path: Path) -> None:
        f = tmp_path / "empty.xlsx"
        f.touch()
        mock_ingest.side_effect = EmptyExportError("zero leads")

        code = main(["--source", "sabi", str(f)])
        assert code == 1


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


class TestEnrichment:
    """Assert enrichment flag and Hunter cap handling."""

    def test_enrich_no_api_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--enrich without HUNTER_API_KEY exits 1."""
        f = tmp_path / "in.csv"
        f.touch()
        monkeypatch.delenv("HUNTER_API_KEY", raising=False)

        code = main(["--source", "apollo", "--enrich", str(f)])
        assert code == 1

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    @patch(f"{_MOCK_MODULE}.HunterClient")
    def test_hunter_cap_exceeded_continues(
        self,
        mock_hunter_cls: MagicMock,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HunterCapExceededError mid-enrichment does not abort pipeline."""
        f = tmp_path / "in.csv"
        f.touch()
        monkeypatch.setenv("HUNTER_API_KEY", "test_key")

        leads = [
            _lead(company_name="A", email="a@b.com", confidence_score=0),
            _lead(company_name="B", email="b@c.com", confidence_score=0),
        ]
        report = _empty_report()

        mock_ingest.return_value = leads
        mock_validate.return_value = (report, leads)
        mock_score.return_value = leads

        # First verify succeeds, second triggers cap
        mock_client = MagicMock()
        mock_client.verify_email.side_effect = [85, HunterCapExceededError("cap")]
        mock_hunter_cls.return_value = mock_client

        code = main(["--source", "apollo", "--enrich", str(f)])

        assert code == 0
        mock_write.assert_called_once()


# ---------------------------------------------------------------------------
# Output verification
# ---------------------------------------------------------------------------


class TestOutputVerification:
    """Assert validation summary and success message appear in stdout."""

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_validation_summary_in_stdout(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        f = tmp_path / "in.csv"
        f.touch()
        out = tmp_path / "out.csv"

        mock_ingest.return_value = [_lead()]
        report = _empty_report()
        mock_validate.return_value = (report, [_lead()])
        mock_score.return_value = [_lead()]

        main(["--source", "apollo", "--output", str(out), str(f)])

        captured = capsys.readouterr()
        assert "Total leads:" in captured.out
        assert "Clean leads:" in captured.out

    @patch(f"{_MOCK_MODULE}.write_leads_csv")
    @patch(f"{_MOCK_MODULE}.score_leads")
    @patch(f"{_MOCK_MODULE}.validate_leads")
    @patch(f"{_MOCK_MODULE}.from_apollo_csv")
    def test_success_message_contains_output_path(
        self,
        mock_ingest: MagicMock,
        mock_validate: MagicMock,
        mock_score: MagicMock,
        mock_write: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        f = tmp_path / "in.csv"
        f.touch()
        out = tmp_path / "result.csv"

        mock_ingest.return_value = [_lead()]
        mock_validate.return_value = (_empty_report(), [_lead()])
        mock_score.return_value = [_lead()]

        main(["--source", "apollo", "--output", str(out), str(f)])

        captured = capsys.readouterr()
        assert str(out) in captured.out
        assert "Wrote 1 leads" in captured.out
