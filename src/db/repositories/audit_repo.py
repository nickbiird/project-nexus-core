"""
Project Nexus — Audit Repository
====================================

Database operations for the ``Audit`` entity and its child entities
(``AuditFinding``, ``AuditColumnProfile``, ``AuditAnomaly``).

The ``save_audit_report`` method is the critical write path: it maps a
``ProfilingReport`` dataclass to ORM instances and persists the entire
object graph in a single atomic transaction.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.common.exceptions import PersistenceError
from src.db.models import Audit, AuditAnomaly, AuditColumnProfile, AuditFinding
from src.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from src.etl.profilers.excel_profiler import ProfilingReport


class AuditRepository(BaseRepository):
    """Persist and retrieve ``Audit`` entities with all child records."""

    def get_by_id(self, audit_id: uuid.UUID) -> Audit | None:
        """Return the audit with the given primary key, or ``None``.

        Uses ``session.get()`` for efficient identity-map lookup.
        """
        return self._session.get(Audit, audit_id)

    def get_by_file_hash(self, file_hash: str) -> Audit | None:
        """Return a previously cached audit matching *file_hash*, or ``None``.

        This is the deduplication gate: if a re-uploaded file has the same
        SHA-256 digest, the caller can skip profiling and return the cached
        result.  The ``file_hash`` column is ``unique=True`` and indexed.
        """
        stmt = select(Audit).where(Audit.file_hash == file_hash)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_by_client(self, client_id: uuid.UUID) -> Sequence[Audit]:
        """Return all audits for *client_id*, newest first.

        Results are ordered by ``created_at`` descending so the most
        recent audit appears at index 0.
        """
        stmt = select(Audit).where(Audit.client_id == client_id).order_by(Audit.created_at.desc())
        return self._session.execute(stmt).scalars().all()

    def save_audit_report(
        self,
        client_id: uuid.UUID,
        file_name: str,
        file_hash: str,
        report: ProfilingReport,
    ) -> Audit:
        """Persist a complete profiling report as an ``Audit`` with children.

        Constructs one ``Audit`` ORM instance from the scalar fields of
        *report*, then iterates through the report's findings, column
        profiles, and anomaly lists to build child ORM instances.  All
        children are appended to the audit's relationship collections so
        that SQLAlchemy's ``cascade="all, delete-orphan"`` handles the
        ``audit_id`` linkage automatically.

        The entire object graph is committed in a single transaction.
        On failure the transaction is rolled back and a
        ``PersistenceError`` is raised wrapping the original exception.

        Field mapping divergences (profiler → ORM):
            - ``data_health_score`` → ``health_score``
            - ``total_estimated_impact_eur`` → ``total_impact_eur``
            - ``processing_time_seconds`` → ``processing_seconds``
            - ``ColumnProfile.name`` → ``AuditColumnProfile.column_name``

        Args:
            client_id: UUID of the owning ``Client``.
            file_name: Original uploaded filename.
            file_hash: SHA-256 hex digest of the uploaded file.
            report: The ``ProfilingReport`` dataclass returned by the
                profiling engine.

        Returns:
            The persisted ``Audit`` instance.

        Raises:
            PersistenceError: If any part of the transaction fails.
        """
        try:
            audit = Audit(
                client_id=client_id,
                file_name=file_name,
                file_hash=file_hash,
                total_rows=report.total_rows,
                total_columns=report.total_columns,
                health_score=report.data_health_score,  # profiler: data_health_score → db: health_score
                completeness_score=report.completeness_score,
                consistency_score=report.consistency_score,
                uniqueness_score=report.uniqueness_score,
                total_impact_eur=report.total_estimated_impact_eur,  # profiler: total_estimated_impact_eur → db: total_impact_eur
                processing_seconds=report.processing_time_seconds,  # profiler: processing_time_seconds → db: processing_seconds
            )

            # --- Findings ---
            for finding in report.findings:
                audit.findings.append(
                    AuditFinding(
                        category=finding.category,
                        description=finding.description,
                        estimated_eur_impact=finding.estimated_eur_impact,
                        confidence=finding.confidence,
                        rows_affected=finding.rows_affected,
                    )
                )

            # --- Column Profiles ---
            for cp in report.column_profiles:
                audit.column_profiles.append(
                    AuditColumnProfile(
                        column_name=cp.name,  # profiler: name → db: column_name
                        inferred_type=cp.inferred_type,
                        null_pct=cp.null_pct,
                        unique_count=cp.unique_count,
                        format_inconsistencies=cp.format_inconsistencies,
                    )
                )

            # --- Anomalies ---
            # The ProfilingReport stores anomalies nested inside
            # AnomalyAnalysis objects.  Each AnomalyAnalysis has a list
            # of Anomaly items — we flatten them into AuditAnomaly rows.
            for analysis in report.anomaly_analyses:
                for anomaly in analysis.anomalies:
                    audit.anomalies.append(
                        AuditAnomaly(
                            column_name=anomaly.column_name,
                            anomaly_type=anomaly.anomaly_type,
                            value=anomaly.value,
                            row_index=anomaly.row_index,
                            context=anomaly.context,
                        )
                    )

            self._session.add(audit)
            self._session.commit()
            self._session.refresh(audit)
        except PersistenceError:
            raise
        except Exception as exc:
            self._session.rollback()
            raise PersistenceError(f"Failed to save audit report for file {file_name!r}") from exc

        return audit
