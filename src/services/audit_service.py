"""
Project Nexus — Audit Service
================================

Orchestrates the full upload → hash → check → profile-or-retrieve →
persist pipeline.  This module is Streamlit-free and forms the single
crossing point between the presentation layer and the persistence +
profiling layers.

Public functions
----------------
- ``compute_file_hash`` — SHA-256 hex digest of raw bytes.
- ``rehydrate_report`` — reconstruct a ``ProfilingReport`` from an ORM
  ``Audit`` instance and its children (the cache-hit path).
- ``process_audit_upload`` — the full orchestration function called by
  the sidebar for every file upload.
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from sqlalchemy.orm import Session

from src.common.exceptions import IngestionError, ProfilingError
from src.db.models import Audit
from src.db.repositories.audit_repo import AuditRepository
from src.db.repositories.client_repo import ClientRepository
from src.etl.profilers.excel_profiler import (
    Anomaly,
    AnomalyAnalysis,
    ColumnProfile,
    Finding,
    ProfilingReport,
    profile_excel,
)

logger = logging.getLogger(__name__)

_DEFAULT_CLIENT_NAME = "Nexus Pilot Client"


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def compute_file_hash(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of *data*.

    Args:
        data: Raw file bytes.

    Returns:
        A 64-character lowercase hex string.
    """
    return hashlib.sha256(data).hexdigest()


def rehydrate_report(audit: Audit) -> ProfilingReport:
    """Reconstruct a ``ProfilingReport`` from a persisted ``Audit``.

    Maps every ORM attribute back to the corresponding ``ProfilingReport``
    dataclass field.  Fields that were not persisted in the 2A schema are
    filled with their type-appropriate zero values and annotated with a
    ``# db gap`` comment.

    Args:
        audit: A fully-loaded ``Audit`` ORM instance with its child
            collections (findings, column_profiles, anomalies) eagerly
            available.

    Returns:
        A ``ProfilingReport`` structurally identical to what the profiler
        would have produced for the same input file.
    """
    findings = [
        Finding(
            description=f.description,
            estimated_eur_impact=f.estimated_eur_impact or 0.0,
            confidence=f.confidence or "medium",
            rows_affected=f.rows_affected or 0,
            category=f.category,
        )
        for f in audit.findings
    ]

    column_profiles = [
        ColumnProfile(
            name=cp.column_name,  # db: column_name → profiler: name
            inferred_type=cp.inferred_type or "text",
            total_rows=audit.total_rows or 0,  # db gap: not per-column
            null_count=0,  # db gap: null_count not persisted
            null_pct=cp.null_pct or 0.0,
            unique_count=cp.unique_count or 0,
            unique_pct=0.0,  # db gap: unique_pct not persisted
            sample_values=[],  # db gap: sample_values not persisted
            format_inconsistencies=cp.format_inconsistencies or 0,
        )
        for cp in audit.column_profiles
    ]

    # Re-group flat AuditAnomaly rows back into AnomalyAnalysis objects
    # keyed by column_name.
    anomaly_map: dict[str, list[Anomaly]] = {}
    for a in audit.anomalies:
        anomaly_map.setdefault(a.column_name, []).append(
            Anomaly(
                column_name=a.column_name,
                anomaly_type=a.anomaly_type,
                value=a.value or 0.0,
                row_index=a.row_index or 0,
                context=a.context or "",
            )
        )

    anomaly_analyses = [
        AnomalyAnalysis(
            column_name=col,
            mean=0.0,  # db gap: mean not persisted
            median=0.0,  # db gap: median not persisted
            stddev=0.0,  # db gap: stddev not persisted
            min_val=0.0,  # db gap: min_val not persisted
            max_val=0.0,  # db gap: max_val not persisted
            outlier_count=len(anomalies),  # db gap: approximated from anomaly count
            zero_count=0,  # db gap: zero_count not persisted
            negative_count=0,  # db gap: negative_count not persisted
            anomalies=anomalies,
        )
        for col, anomalies in anomaly_map.items()
    ]

    return ProfilingReport(
        file_path=audit.file_name,
        file_size_mb=0.0,  # db gap: file_size_mb not persisted
        total_rows=audit.total_rows or 0,
        total_columns=audit.total_columns or 0,
        processing_time_seconds=audit.processing_seconds
        or 0.0,  # db: processing_seconds → profiler: processing_time_seconds
        timestamp=audit.created_at.isoformat() if audit.created_at else "",
        column_profiles=column_profiles,
        detected_entity_columns=[],  # db gap: not persisted
        detected_financial_columns=[],  # db gap: not persisted
        detected_date_columns=[],  # db gap: not persisted
        data_health_score=audit.health_score
        or 0.0,  # db: health_score → profiler: data_health_score
        completeness_score=audit.completeness_score or 0.0,
        consistency_score=audit.consistency_score or 0.0,
        uniqueness_score=audit.uniqueness_score or 0.0,
        overall_null_pct=0.0,  # db gap: not persisted
        exact_duplicate_rows=0,  # db gap: not persisted
        near_duplicate_rows=0,  # db gap: not persisted
        entity_analyses=[],  # db gap: entity_analyses not persisted
        anomaly_analyses=anomaly_analyses,
        findings=findings,
        total_estimated_impact_eur=audit.total_impact_eur
        or 0.0,  # db: total_impact_eur → profiler: total_estimated_impact_eur
    )


def process_audit_upload(
    session: Session,
    file_name: str,
    file_bytes: bytes,
    on_progress: Callable[[int, str], None] | None = None,
) -> ProfilingReport:
    """Orchestrate the full upload-to-report pipeline.

    Computes a SHA-256 hash of *file_bytes*, checks the database for a
    cached audit with that hash, and either re-hydrates the cached report
    or runs the profiling engine and persists the result.

    Args:
        session: An active SQLAlchemy ``Session`` (caller owns the
            lifecycle).
        file_name: Original uploaded filename.
        file_bytes: Raw file content.
        on_progress: Optional callback ``(percent, message)`` for
            progress reporting.  Called at major pipeline stages.

    Returns:
        A ``ProfilingReport`` — either freshly profiled or re-hydrated
        from cache.

    Raises:
        IngestionError: If a non-profiling I/O error occurs.
        ProfilingError: If the profiling engine fails.
        PersistenceError: If the database write fails.
    """
    if on_progress is not None:
        on_progress(0, "Iniciando procesamiento...")

    # ── Step 1: Hash ─────────────────────────────────────────
    file_hash = compute_file_hash(file_bytes)
    logger.debug("File hash computed: %s...", file_hash[:8])

    if on_progress is not None:
        on_progress(10, "Verificando caché...")

    # ── Step 2: Cache check ──────────────────────────────────
    audit_repo = AuditRepository(session)
    cached_audit = audit_repo.get_by_file_hash(file_hash)

    if cached_audit is not None:
        logger.info(
            "Cache HIT — audit_id=%s, file=%s",
            str(cached_audit.id)[:8],
            file_name,
        )
        if on_progress is not None:
            on_progress(100, "Resultado recuperado de caché.")
        return rehydrate_report(cached_audit)

    # ── Step 3: Cache MISS → profile ─────────────────────────
    logger.info("Cache MISS — profiling file=%s", file_name)

    if on_progress is not None:
        on_progress(25, "Analizando datos...")

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=Path(file_name).suffix or ".xlsx",
            delete=False,
        ) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        if on_progress is not None:
            on_progress(50, "Ejecutando motor de perfilado...")

        report = profile_excel(tmp_path)
    except (ProfilingError, IngestionError):
        raise
    except OSError as exc:
        logger.error("I/O error during profiling: %s", exc)
        raise IngestionError(f"Error reading file {file_name!r}: {exc}") from exc
    except ValueError as exc:
        logger.error("Value error during profiling: %s", exc)
        raise IngestionError(f"Invalid data in file {file_name!r}: {exc}") from exc
    finally:
        if tmp_path is not None:
            with suppress(OSError):
                tmp_path.unlink()

    logger.info(
        "Profiling complete — file=%s, processing_seconds=%.2f",
        file_name,
        report.processing_time_seconds,
    )

    if on_progress is not None:
        on_progress(75, "Guardando resultados...")

    # ── Step 4: Bootstrap pilot client ───────────────────────
    client_repo = ClientRepository(session)
    client = client_repo.get_by_company_name(_DEFAULT_CLIENT_NAME)
    if client is None:
        client = client_repo.create_client(company_name=_DEFAULT_CLIENT_NAME)

    # ── Step 5: Persist ──────────────────────────────────────
    report.file_path = file_name
    saved_audit = audit_repo.save_audit_report(
        client_id=client.id,
        file_name=file_name,
        file_hash=file_hash,
        report=report,
    )

    logger.info("Audit persisted — audit_id=%s", str(saved_audit.id)[:8])

    if on_progress is not None:
        on_progress(100, "Completado.")

    return report
