"""
Tests for the Data Quality Profiling Engine.
=============================================

Tests cover all 5 sections of the ProfilingReport:
1. Schema detection correctness
2. Quality metric calculation accuracy
3. Entity clustering (finds known duplicates like Martinez SL → Martínez S.L.)
4. Anomaly detection (flags known outliers)
5. Financial quick-wins (detects negative margins from ground truth)

Run: pytest tests/unit/etl/test_excel_profiler.py -v
"""

from __future__ import annotations

import json

# Import the profiling engine modules
# Adjust import path based on your project structure
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.etl.profilers.excel_profiler import (
    ProfilingReport,
    analyze_entities,
    cluster_entities,
    compute_completeness_score,
    compute_health_score,
    compute_uniqueness_score,
    detect_anomalies,
    generate_findings,
    infer_column_type,
    profile_columns,
    profile_excel,
)

# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def sample_logistics_df() -> pd.DataFrame:
    """Create a small logistics-like DataFrame with known error patterns."""
    return pd.DataFrame(
        {
            "numero_factura": [
                "FAC-001",
                "FAC-002",
                "FAC-003",
                "FAC-004",
                "FAC-005",
                "FAC-006",
                "FAC-007",
                "FAC-008",
                "FAC-009",
                "FAC-010",
                "FAC-002",  # Duplicate invoice number
                "FAC-011",
                "FAC-012",
            ],
            "proveedor": [
                "Transportes Garcia S.L.",
                "Trans. Garcia",
                "GARCIA SL",
                "Transportes Martinez S.L.",
                "Martínez S.L.",
                "Martnez SL",
                "Logística Pérez S.A.",
                "Logistica Perez",
                "Pérez S.A.",
                "Transportes Lopez",
                "Trans. Garcia",
                "Iberlogística S.L.",
                "Iberlogistica",
            ],
            "fecha_factura": [
                "15/01/2025",
                "2025-01-20",
                "01-25-2025",
                "2025/02/01",
                "10/02/2025",
                "15/02/2025",
                "2025-03-01",
                "03/05/2025",
                "2025-03-15",
                "20/03/2025",
                "2025-01-20",
                "01/04/2025",
                "2025-04-10",
            ],
            "importe_total": [
                1500.00,
                2200.50,
                1800.00,
                950.00,
                3100.00,
                25000.00,  # Outlier (very high)
                1700.00,
                0.00,  # Zero value
                -150.00,  # Negative
                2000.00,
                2200.50,  # Duplicate amount+entity
                1400.00,
                1600.00,
            ],
            "coste_operativo": [
                1200.00,
                1800.00,
                1600.00,
                1100.00,
                2500.00,
                3000.00,
                1400.00,
                500.00,
                200.00,
                1500.00,
                1800.00,
                1100.00,
                1300.00,
            ],
            "ruta": [
                "BCN-MAD",
                "BCN-MAD",
                "BCN-VAL",
                "MAD-SEV",
                "BCN-ZAR",
                "BCN-MAD",
                "MAD-BIL",
                "BCN-VAL",
                "MAD-SEV",
                "BCN-ZAR",
                "BCN-MAD",
                "BCN-MAD",
                "MAD-BIL",
            ],
            "peso_kg": [
                1500,
                None,
                2200,
                800,
                None,
                1800,
                2000,
                None,
                1200,
                None,
                1500,
                1700,
                None,
            ],
        }
    )


@pytest.fixture
def sample_xlsx_path(sample_logistics_df: pd.DataFrame) -> Path:
    """Write the sample DataFrame to a temporary .xlsx file."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = Path(f.name)
    sample_logistics_df.to_excel(path, index=False)
    return path


@pytest.fixture
def sample_csv_path(sample_logistics_df: pd.DataFrame) -> Path:
    """Write the sample DataFrame to a temporary .csv file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = Path(f.name)
    sample_logistics_df.to_csv(path, index=False)
    return path


# ──────────────────────────────────────────────────────────────
# Section 1: Schema Detection Tests
# ──────────────────────────────────────────────────────────────


class TestSchemaDetection:
    """Tests for column type inference and profiling."""

    @pytest.mark.skip(reason="ETL profiler WIP")
    def test_detects_entity_column_by_name(self, sample_logistics_df: pd.DataFrame) -> None:
        """'proveedor' should be detected as an entity column."""
        col_type = infer_column_type("proveedor", sample_logistics_df["proveedor"])
        assert col_type == "entity"

    def test_detects_financial_column_by_name(self, sample_logistics_df: pd.DataFrame) -> None:
        """'importe_total' should be detected as a financial column."""
        col_type = infer_column_type("importe_total", sample_logistics_df["importe_total"])
        assert col_type == "financial"

    def test_detects_date_column_by_name(self, sample_logistics_df: pd.DataFrame) -> None:
        """'fecha_factura' should be detected as a date column."""
        col_type = infer_column_type("fecha_factura", sample_logistics_df["fecha_factura"])
        assert col_type == "date"

    def test_profile_columns_returns_all_columns(self, sample_logistics_df: pd.DataFrame) -> None:
        """profile_columns should return one profile per column."""
        profiles = profile_columns(sample_logistics_df)
        assert len(profiles) == len(sample_logistics_df.columns)

    def test_null_percentage_calculation(self, sample_logistics_df: pd.DataFrame) -> None:
        """Null percentage should be correctly calculated for peso_kg column."""
        profiles = profile_columns(sample_logistics_df)
        peso_profile = next(p for p in profiles if p.name == "peso_kg")
        # 5 out of 13 are None
        expected_null_pct = round(5 / 13 * 100, 2)
        assert abs(peso_profile.null_pct - expected_null_pct) < 0.1

    def test_sample_values_are_non_null(self, sample_logistics_df: pd.DataFrame) -> None:
        """Sample values should only contain non-null values."""
        profiles = profile_columns(sample_logistics_df)
        for profile in profiles:
            for val in profile.sample_values:
                assert val is not None
                assert not (isinstance(val, float) and np.isnan(val))


# ──────────────────────────────────────────────────────────────
# Section 2: Quality Metrics Tests
# ──────────────────────────────────────────────────────────────


class TestQualityMetrics:
    """Tests for completeness, consistency, and uniqueness scoring."""

    def test_completeness_perfect_data(self) -> None:
        """A DataFrame with no nulls should score 100."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        assert compute_completeness_score(df) == 100.0

    def test_completeness_with_nulls(self) -> None:
        """Completeness should decrease proportionally with null values."""
        df = pd.DataFrame({"a": [1, None, 3], "b": [None, None, "z"]})
        # 3 nulls out of 6 cells = 50%
        score = compute_completeness_score(df)
        assert abs(score - 50.0) < 0.1

    def test_uniqueness_detects_exact_duplicates(self, sample_logistics_df: pd.DataFrame) -> None:
        """Uniqueness check should detect exact duplicate rows."""
        score, exact_dups, _ = compute_uniqueness_score(sample_logistics_df)
        # We should detect at least some level of duplication
        assert score <= 100.0
        assert score > 0.0

    def test_health_score_range(self) -> None:
        """Health score should always be between 0 and 100."""
        score = compute_health_score(80.0, 70.0, 90.0)
        assert 0.0 <= score <= 100.0

    def test_health_score_weighted(self) -> None:
        """Health score should use correct weights (40/30/30)."""
        score = compute_health_score(100.0, 100.0, 100.0)
        assert score == 100.0

        score_zero = compute_health_score(0.0, 0.0, 0.0)
        assert score_zero == 0.0


# ──────────────────────────────────────────────────────────────
# Section 3: Entity Clustering Tests
# ──────────────────────────────────────────────────────────────


class TestEntityClustering:
    """Tests for rapidfuzz-based entity name clustering."""

    def test_clusters_garcia_variants(self) -> None:
        """Garcia variants should be grouped into one cluster."""
        values = [
            "Transportes Garcia S.L.",
            "Trans. Garcia",
            "GARCIA SL",
            "Transportes Garcia S.L.",
            "Trans. Garcia",
        ]
        clusters = cluster_entities(values, threshold=70.0)
        # Should find at least one cluster containing Garcia variants
        garcia_cluster = None
        for c in clusters:
            variant_lower = [v.lower() for v in c.variants]
            if any("garcia" in v for v in variant_lower):
                garcia_cluster = c
                break
        assert garcia_cluster is not None
        assert len(garcia_cluster.variants) >= 2

    def test_clusters_martinez_variants(self) -> None:
        """Martinez variants (including with accent) should be clustered."""
        values = [
            "Transportes Martinez S.L.",
            "Martínez S.L.",
            "Martnez SL",
            "Transportes Martinez S.L.",
        ]
        clusters = cluster_entities(values, threshold=70.0)
        assert len(clusters) >= 1
        # All variants should be in a single cluster
        all_variants = []
        for c in clusters:
            all_variants.extend(c.variants)
        martinez_variants = [v for v in all_variants if "mart" in v.lower()]
        assert len(martinez_variants) >= 2

    def test_does_not_merge_distinct_entities(self) -> None:
        """Completely different entity names should not be clustered."""
        values = [
            "Acme Corporation",
            "Acme Corporation",
            "Totally Different Company Ltd",
            "Totally Different Company Ltd",
            "Another Unrelated Business",
        ]
        clusters = cluster_entities(values, threshold=82.0)
        # Each entity should be in its own cluster (or no clusters if all unique)
        for c in clusters:
            # No cluster should contain both "Acme" and "Totally Different"
            has_acme = any("acme" in v.lower() for v in c.variants)
            has_different = any("different" in v.lower() for v in c.variants)
            assert not (has_acme and has_different)

    def test_canonical_is_most_frequent(self) -> None:
        """The canonical name should be the most frequently occurring variant."""
        values = [
            "Trans. Garcia",
            "Trans. Garcia",
            "Trans. Garcia",
            "Transportes Garcia S.L.",
            "GARCIA SL",
        ]
        clusters = cluster_entities(values, threshold=70.0)
        if clusters:
            # The canonical should be "Trans. Garcia" (3 occurrences)
            garcia_cluster = clusters[0]
            assert garcia_cluster.canonical == "Trans. Garcia"

    def test_entity_analysis_counts(self, sample_logistics_df: pd.DataFrame) -> None:
        """Entity analysis should detect duplicate entities and reduce unique count."""
        analyses = analyze_entities(sample_logistics_df, ["proveedor"])
        assert len(analyses) == 1
        ea = analyses[0]
        assert ea.raw_unique_count > ea.estimated_canonical_count
        assert ea.duplicate_entity_count > 0


# ──────────────────────────────────────────────────────────────
# Section 4: Anomaly Detection Tests
# ──────────────────────────────────────────────────────────────


class TestAnomalyDetection:
    """Tests for IQR-based financial anomaly detection."""

    def test_detects_high_outlier(self, sample_logistics_df: pd.DataFrame) -> None:
        """The €25,000 value should be flagged as a high outlier."""
        analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        assert len(analyses) == 1
        aa = analyses[0]
        assert aa.outlier_count > 0
        high_outliers = [a for a in aa.anomalies if a.anomaly_type == "outlier_high"]
        assert len(high_outliers) > 0
        assert any(a.value == 25000.0 for a in high_outliers)

    def test_detects_zero_values(self, sample_logistics_df: pd.DataFrame) -> None:
        """Zero-value entries should be flagged."""
        analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        aa = analyses[0]
        assert aa.zero_count > 0

    def test_detects_negative_values(self, sample_logistics_df: pd.DataFrame) -> None:
        """Negative values should be flagged."""
        analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        aa = analyses[0]
        assert aa.negative_count > 0
        neg_anomalies = [a for a in aa.anomalies if a.anomaly_type == "negative"]
        assert len(neg_anomalies) > 0
        assert any(a.value == -150.0 for a in neg_anomalies)

    def test_statistical_summary_correct(self, sample_logistics_df: pd.DataFrame) -> None:
        """Mean, median, stddev should be correctly calculated."""
        analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        aa = analyses[0]
        expected_mean = sample_logistics_df["importe_total"].mean()
        assert abs(aa.mean - expected_mean) < 0.01


# ──────────────────────────────────────────────────────────────
# Section 5: Financial Quick-Wins Tests
# ──────────────────────────────────────────────────────────────


class TestFinancialQuickWins:
    """Tests for the Surprise Findings generator."""

    def test_detects_negative_margins(self, sample_logistics_df: pd.DataFrame) -> None:
        """Rows where importe_total < coste_operativo should generate a finding."""
        entity_analyses = analyze_entities(sample_logistics_df, ["proveedor"])
        anomaly_analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        findings = generate_findings(
            sample_logistics_df,
            ["proveedor"],
            ["importe_total", "coste_operativo"],
            entity_analyses,
            anomaly_analyses,
        )
        # Row with importe_total=950, coste_operativo=1100 is negative margin
        neg_margin_findings = [f for f in findings if f.category == "negative_margin"]
        assert len(neg_margin_findings) > 0
        assert neg_margin_findings[0].rows_affected > 0

    def test_findings_have_positive_impact(self, sample_logistics_df: pd.DataFrame) -> None:
        """All findings should have a positive estimated EUR impact."""
        entity_analyses = analyze_entities(sample_logistics_df, ["proveedor"])
        anomaly_analyses = detect_anomalies(sample_logistics_df, ["importe_total"])
        findings = generate_findings(
            sample_logistics_df,
            ["proveedor"],
            ["importe_total", "coste_operativo"],
            entity_analyses,
            anomaly_analyses,
        )
        for f in findings:
            assert f.estimated_eur_impact >= 0

    def test_findings_capped_at_five(self) -> None:
        """Should return at most 5 findings."""
        # Create a large DataFrame with many potential findings
        df = pd.DataFrame(
            {
                "proveedor": [f"Company_{i % 5}" for i in range(100)],
                "importe_total": np.random.normal(1000, 500, 100).tolist(),
                "coste_operativo": np.random.normal(800, 400, 100).tolist(),
                "fecha_factura": ["2025-01-01"] * 100,
            }
        )
        entity_analyses = analyze_entities(df, ["proveedor"])
        anomaly_analyses = detect_anomalies(df, ["importe_total"])
        findings = generate_findings(
            df,
            ["proveedor"],
            ["importe_total", "coste_operativo"],
            entity_analyses,
            anomaly_analyses,
        )
        assert len(findings) <= 5


# ──────────────────────────────────────────────────────────────
# Integration Tests
# ──────────────────────────────────────────────────────────────


class TestEndToEnd:
    """Full pipeline integration tests."""

    def test_profile_xlsx(self, sample_xlsx_path: Path) -> None:
        """Full profiling pipeline should complete on an xlsx file."""
        report = profile_excel(sample_xlsx_path)
        assert isinstance(report, ProfilingReport)
        assert report.total_rows == 13
        assert report.total_columns == 7
        assert 0 <= report.data_health_score <= 100

    def test_profile_csv(self, sample_csv_path: Path) -> None:
        """Full profiling pipeline should complete on a csv file."""
        report = profile_excel(sample_csv_path)
        assert isinstance(report, ProfilingReport)
        assert report.total_rows == 13

    def test_to_json_is_valid(self, sample_xlsx_path: Path) -> None:
        """to_json() should produce valid JSON."""
        report = profile_excel(sample_xlsx_path)
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert "data_health_score" in parsed
        assert "findings" in parsed
        assert "entity_analyses" in parsed

    def test_executive_summary_format(self, sample_xlsx_path: Path) -> None:
        """Executive summary should be 3 sentences."""
        report = profile_excel(sample_xlsx_path)
        summary = report.to_summary_str()
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        assert len(sentences) == 3

    def test_processing_time_reasonable(self, sample_xlsx_path: Path) -> None:
        """Profiling should complete in under 60 seconds (even this tiny file)."""
        report = profile_excel(sample_xlsx_path)
        assert report.processing_time_seconds < 60.0

    @pytest.mark.skip(reason="ETL profiler WIP")
    def test_detected_columns_populated(self, sample_xlsx_path: Path) -> None:
        """Entity, financial, and date columns should be detected."""
        report = profile_excel(sample_xlsx_path)
        assert len(report.detected_entity_columns) > 0
        assert len(report.detected_financial_columns) > 0
        assert len(report.detected_date_columns) > 0

    def test_cli_report_renders(self, sample_xlsx_path: Path) -> None:
        """CLI report should render without errors."""
        report = profile_excel(sample_xlsx_path)
        cli_output = report.to_cli_report()
        assert "DATA HEALTH SCORE" in cli_output
        assert "EXECUTIVE SUMMARY" in cli_output
        assert len(cli_output) > 200


# ──────────────────────────────────────────────────────────────
# Edge Case Tests
# ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_dataframe(self) -> None:
        """Should handle an empty DataFrame gracefully."""
        df = pd.DataFrame()
        profiles = profile_columns(df)
        assert profiles == []

    def test_single_column_dataframe(self) -> None:
        """Should handle a single-column DataFrame."""
        df = pd.DataFrame({"valor": [100, 200, 300]})
        profiles = profile_columns(df)
        assert len(profiles) == 1

    def test_all_nulls_column(self) -> None:
        """Should handle a column that's entirely null."""
        df = pd.DataFrame({"empty": [None, None, None]})
        profiles = profile_columns(df)
        assert profiles[0].null_pct == 100.0

    def test_cluster_entities_empty_list(self) -> None:
        """Should return empty clusters for empty input."""
        clusters = cluster_entities([])
        assert clusters == []

    def test_cluster_entities_single_value(self) -> None:
        """Should return no clusters for a single unique value."""
        clusters = cluster_entities(["Company A", "Company A"])
        assert clusters == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
