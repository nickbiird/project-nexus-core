"""Integration tests — cache-hit deduplication behaviour."""

from __future__ import annotations

import os
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Audit
from src.services.audit_service import compute_file_hash, process_audit_upload


class TestCacheHitDeduplication:
    """Same bytes uploaded twice → one audit, one profiler call."""

    def test_second_upload_skips_profiling(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        # Use unique bytes so other tests don't pollute
        tag = os.urandom(4).hex()
        data = demo_excel_bytes + tag.encode()
        file_hash = compute_file_hash(data)

        # First call — cache miss, profiler runs
        report1 = process_audit_upload(db_session, "dedup_first.xlsx", data)

        # Patch profiler for the second call — should NOT be called
        with patch(
            "src.services.audit_service.profile_excel",
            side_effect=AssertionError("Should not be called on cache hit"),
        ):
            report2 = process_audit_upload(db_session, "dedup_second.xlsx", data)

        # Check by hash — only ONE audit with this specific hash
        audits = (
            db_session.execute(select(Audit).where(Audit.file_hash == file_hash)).scalars().all()
        )
        assert len(audits) == 1

        # Both reports have the same key fields
        assert report2.data_health_score == report1.data_health_score
        assert report2.total_rows == report1.total_rows

    def test_different_bytes_produce_two_audits(
        self, db_session: Session, demo_excel_bytes: bytes
    ) -> None:
        tag_a = os.urandom(4).hex()
        tag_b = os.urandom(4).hex()
        data_a = demo_excel_bytes + tag_a.encode()
        data_b = demo_excel_bytes + tag_b.encode()

        hash_a = compute_file_hash(data_a)
        hash_b = compute_file_hash(data_b)

        process_audit_upload(db_session, "file_a.xlsx", data_a)
        process_audit_upload(db_session, "file_b.xlsx", data_b)

        audit_a = db_session.execute(
            select(Audit).where(Audit.file_hash == hash_a)
        ).scalar_one_or_none()
        audit_b = db_session.execute(
            select(Audit).where(Audit.file_hash == hash_b)
        ).scalar_one_or_none()

        assert audit_a is not None
        assert audit_b is not None
        assert audit_a.id != audit_b.id


class TestRehydrationFidelity:
    """Cached report matches original scalar fields."""

    def test_scalar_fields_match(self, db_session: Session, demo_excel_bytes: bytes) -> None:
        tag = os.urandom(4).hex()
        data = demo_excel_bytes + tag.encode()

        original = process_audit_upload(db_session, "fidelity.xlsx", data)

        # Second call hits cache
        cached = process_audit_upload(db_session, "fidelity_again.xlsx", data)

        assert cached.data_health_score == original.data_health_score
        assert cached.total_rows == original.total_rows
        assert cached.total_columns == original.total_columns
        assert cached.total_estimated_impact_eur == original.total_estimated_impact_eur
        assert len(cached.findings) == len(original.findings)
