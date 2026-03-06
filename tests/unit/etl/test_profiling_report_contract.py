"""Contract tests for ProfilingReport invariants."""

from __future__ import annotations

import io

import pytest

from src.etl.profilers.excel_profiler import ProfilingReport, profile_excel
from src.services.demo_service import generate_demo_data


@pytest.fixture(scope="module")
def contract_report() -> ProfilingReport:
    """Profile the demo dataset and return the report for contract checks."""
    df = generate_demo_data()
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)

    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(buf.getvalue())
        tmp_path = Path(tmp.name)

    try:
        return profile_excel(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


class TestProfilingReportContract:
    """Invariants that ProfilingReport must always satisfy."""

    def test_required_fields_not_none(self, contract_report: ProfilingReport) -> None:
        assert contract_report.file_path is not None
        assert contract_report.total_rows is not None
        assert contract_report.total_columns is not None
        assert contract_report.processing_time_seconds is not None
        assert contract_report.timestamp is not None
        assert contract_report.column_profiles is not None
        assert contract_report.findings is not None

    def test_health_score_in_range(self, contract_report: ProfilingReport) -> None:
        assert 0 <= contract_report.data_health_score <= 100

    def test_component_scores_in_range(self, contract_report: ProfilingReport) -> None:
        assert 0 <= contract_report.completeness_score <= 100
        assert 0 <= contract_report.consistency_score <= 100
        assert 0 <= contract_report.uniqueness_score <= 100

    def test_findings_is_list(self, contract_report: ProfilingReport) -> None:
        assert isinstance(contract_report.findings, list)

    def test_column_profiles_length_matches(self, contract_report: ProfilingReport) -> None:
        assert len(contract_report.column_profiles) == contract_report.total_columns

    def test_total_estimated_impact_non_negative(self, contract_report: ProfilingReport) -> None:
        assert contract_report.total_estimated_impact_eur >= 0.0

    def test_total_gross_revenue_non_negative(self, contract_report: ProfilingReport) -> None:
        assert contract_report.total_gross_revenue >= 0.0

    def test_processing_seconds_positive(self, contract_report: ProfilingReport) -> None:
        assert contract_report.processing_time_seconds > 0.0
