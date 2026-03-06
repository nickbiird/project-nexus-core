"""Unit tests for audit_service — all database and profiler interactions mocked."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.common.exceptions import IngestionError, ProfilingError
from src.etl.profilers.excel_profiler import ProfilingReport
from src.services.audit_service import process_audit_upload


def _make_mock_report() -> ProfilingReport:
    """Build a minimal ProfilingReport for mock tests."""
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
        findings=[],
        total_estimated_impact_eur=1234.56,
        total_gross_revenue=50000.0,
    )


class TestCacheHitPath:
    """When a cached audit is found, profiler should NOT be called."""

    def test_returns_cached_report(self) -> None:
        mock_audit = MagicMock()
        mock_audit.id = uuid.uuid4()
        mock_audit.findings = []
        mock_audit.column_profiles = []
        mock_audit.anomalies = []
        mock_audit.total_rows = 100
        mock_audit.total_columns = 7
        mock_audit.health_score = 85.0
        mock_audit.completeness_score = 90.0
        mock_audit.consistency_score = 80.0
        mock_audit.uniqueness_score = 95.0
        mock_audit.total_impact_eur = 1234.56
        mock_audit.processing_seconds = 0.5
        mock_audit.file_name = "test.xlsx"
        mock_audit.created_at = MagicMock(isoformat=MagicMock(return_value="2025-01-01"))

        session = MagicMock()
        with (
            patch("src.services.audit_service.AuditRepository") as mock_repo_cls,
            patch("src.services.audit_service.profile_excel") as mock_profiler,
        ):
            mock_repo_cls.return_value.get_by_file_hash.return_value = mock_audit

            result = process_audit_upload(session, "test.xlsx", b"test content")

            mock_profiler.assert_not_called()
            assert result.total_rows == 100


class TestCacheMissPath:
    """When no cached audit exists, profiler runs and result is persisted."""

    def test_profiler_called_once(self) -> None:
        mock_report = _make_mock_report()
        mock_saved = MagicMock()
        mock_saved.id = uuid.uuid4()

        session = MagicMock()
        with (
            patch("src.services.audit_service.AuditRepository") as mock_repo_cls,
            patch(
                "src.services.audit_service.profile_excel",
                return_value=mock_report,
            ) as mock_profiler,
            patch("src.services.audit_service.ClientRepository") as mock_client_cls,
        ):
            mock_repo_cls.return_value.get_by_file_hash.return_value = None
            mock_repo_cls.return_value.save_audit_report.return_value = mock_saved
            mock_client_cls.return_value.get_by_company_name.return_value = MagicMock(
                id=uuid.uuid4()
            )

            result = process_audit_upload(session, "test.xlsx", b"new content")

            mock_profiler.assert_called_once()
            assert result is mock_report


class TestExceptionTranslation:
    """Exception type contracts at the service boundary."""

    def test_profiling_error_propagates(self) -> None:
        session = MagicMock()
        with (
            patch("src.services.audit_service.AuditRepository") as mock_repo_cls,
            patch(
                "src.services.audit_service.profile_excel",
                side_effect=ProfilingError("engine crashed"),
            ),
        ):
            mock_repo_cls.return_value.get_by_file_hash.return_value = None

            with pytest.raises(ProfilingError, match="engine crashed"):
                process_audit_upload(session, "test.xlsx", b"data")

    def test_os_error_wrapped_as_ingestion_error(self) -> None:
        session = MagicMock()
        with (
            patch("src.services.audit_service.AuditRepository") as mock_repo_cls,
            patch(
                "src.services.audit_service.profile_excel",
                side_effect=OSError("disk full"),
            ),
        ):
            mock_repo_cls.return_value.get_by_file_hash.return_value = None

            with pytest.raises(IngestionError, match="disk full"):
                process_audit_upload(session, "test.xlsx", b"data")
