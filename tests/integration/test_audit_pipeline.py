"""Integration tests — full audit pipeline (cache-miss path)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.exceptions import PersistenceError, ProfilingError
from src.db.models import Audit, Client
from src.db.repositories.audit_repo import AuditRepository
from src.services.audit_service import compute_file_hash, process_audit_upload


def _unique_bytes(base: bytes, tag: str) -> bytes:
    """Append a tag to make bytes unique per test."""
    return base + tag.encode()


class TestFullPipelineCacheMiss:
    """Cache-miss: novel file is profiled, persisted, and returned."""

    def test_returns_report_with_non_zero_fields(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        data = _unique_bytes(demo_excel_bytes, "nonzero")
        report = process_audit_upload(db_session, "test_pipeline.xlsx", data)

        assert report.total_rows > 0
        assert report.total_columns > 0
        assert report.data_health_score > 0.0
        assert len(report.findings) > 0

    def test_audit_persisted_in_database(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        data = _unique_bytes(demo_excel_bytes, "persist")
        report = process_audit_upload(db_session, "test_persist.xlsx", data)

        file_hash = compute_file_hash(data)
        repo = AuditRepository(db_session)
        audit = repo.get_by_file_hash(file_hash)

        assert audit is not None
        assert audit.file_name == "test_persist.xlsx"
        assert audit.health_score == report.data_health_score


class TestPilotClientBootstrap:
    """Default pilot client is created idempotently."""

    def test_pilot_client_created(self, db_session: Session, demo_excel_bytes: bytes) -> None:
        data = _unique_bytes(demo_excel_bytes, "pilot")
        process_audit_upload(db_session, "pilot_test.xlsx", data)

        clients = (
            db_session.execute(select(Client).where(Client.company_name == "Nexus Pilot Client"))
            .scalars()
            .all()
        )
        assert len(clients) >= 1

    def test_audit_linked_to_pilot_client(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        data = _unique_bytes(demo_excel_bytes, "linked")
        process_audit_upload(db_session, "linked_test.xlsx", data)

        client = (
            db_session.execute(select(Client).where(Client.company_name == "Nexus Pilot Client"))
            .scalars()
            .first()
        )
        assert client is not None

        file_hash = compute_file_hash(data)
        audit = db_session.execute(select(Audit).where(Audit.file_hash == file_hash)).scalar_one()
        assert audit.client_id == client.id


class TestPipelineErrorPaths:
    """Error translation at the service boundary."""

    def test_profiling_error_propagates(self, db_session: Session, demo_excel_bytes: bytes) -> None:
        data = _unique_bytes(demo_excel_bytes, "proferr" + os.urandom(4).hex())
        with (
            patch(
                "src.services.audit_service.profile_excel",
                side_effect=ProfilingError("Engine crashed"),
            ),
            pytest.raises(ProfilingError, match="Engine crashed"),
        ):
            process_audit_upload(db_session, "error_test.xlsx", data)

        # No partial audit committed
        repo = AuditRepository(db_session)
        file_hash = compute_file_hash(data)
        assert repo.get_by_file_hash(file_hash) is None

    def test_persistence_error_propagates(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        data = _unique_bytes(demo_excel_bytes, "dberr" + os.urandom(4).hex())
        with (
            patch.object(
                AuditRepository,
                "save_audit_report",
                side_effect=PersistenceError("DB write failed"),
            ),
            pytest.raises(PersistenceError, match="DB write failed"),
        ):
            process_audit_upload(db_session, "db_error_test.xlsx", data)
