"""Unit tests for export_service — HTML report generation."""

from __future__ import annotations

from src.etl.profilers.excel_profiler import Finding, ProfilingReport
from src.services.export_service import generate_html_report


def _make_report() -> ProfilingReport:
    """Build a minimal ProfilingReport for export tests."""
    return ProfilingReport(
        file_path="test.xlsx",
        file_size_mb=1.0,
        total_rows=100,
        total_columns=7,
        processing_time_seconds=0.5,
        timestamp="2025-01-01T00:00:00",
        column_profiles=[],
        detected_entity_columns=[],
        detected_financial_columns=[],
        detected_date_columns=[],
        data_health_score=85.0,
        completeness_score=90.0,
        consistency_score=80.0,
        uniqueness_score=95.0,
        overall_null_pct=5.0,
        exact_duplicate_rows=1,
        near_duplicate_rows=0,
        entity_analyses=[],
        anomaly_analyses=[],
        findings=[
            Finding(
                description="Test finding",
                estimated_eur_impact=100.0,
                confidence="high",
                rows_affected=5,
                category="data_quality",
            )
        ],
        total_estimated_impact_eur=100.0,
        total_gross_revenue=50000.0,
    )


class TestHtmlExport:
    """HTML report generation contract."""

    def test_html_is_well_formed(self) -> None:
        report = _make_report()
        html = generate_html_report(report)

        assert isinstance(html, str)
        assert html.strip().startswith(("<!DOCTYPE", "<!doctype", "<html", "<HTML"))
        assert "85" in html  # health score value present

    def test_no_python_repr_in_output(self) -> None:
        report = _make_report()
        html = generate_html_report(report)

        assert "<class" not in html
        assert "object at 0x" not in html
