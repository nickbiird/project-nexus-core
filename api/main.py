"""Yellowbird Telemetry — FastAPI Application.

Provides the API skeleton and operational endpoints.

Routes:
- GET /health — liveness probe
- GET /api/metrics — operational dashboard metrics
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.db.models import Audit, AuditFinding

app = FastAPI(
    title="Yellowbird Telemetry API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Dependency injection ─────────────────────────────────────


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped DI."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Response models ──────────────────────────────────────────


class FindingCategory(BaseModel):
    """A finding category with its occurrence count."""

    category: str
    count: int


class MetricsResponse(BaseModel):
    """Operational metrics from the audits database."""

    total_audits: int
    audits_today: int
    average_health_score: float | None
    average_processing_seconds: float | None
    total_impact_eur_detected: float
    top_finding_categories: list[FindingCategory]


# ── Routes ───────────────────────────────────────────────────


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe for container orchestration."""
    return {"status": "ok"}


@app.get("/api/metrics", response_model=MetricsResponse)
def get_metrics(session: Session = Depends(get_db)) -> MetricsResponse:  # noqa: B008
    """Return operational dashboard metrics from the audits database."""
    try:
        # Total audits
        total_audits: int = session.scalar(select(func.count(Audit.id))) or 0

        # Audits today (UTC)
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        audits_today: int = (
            session.scalar(
                select(func.count(Audit.id)).where(Audit.created_at >= today_start)
            )
            or 0
        )

        # Averages
        avg_health = session.scalar(select(func.avg(Audit.health_score)))
        avg_processing = session.scalar(select(func.avg(Audit.processing_seconds)))

        # Total impact
        total_impact: float = session.scalar(select(func.sum(Audit.total_impact_eur))) or 0.0

        # Top 5 finding categories
        top_categories_query = (
            select(AuditFinding.category, func.count(AuditFinding.id).label("cnt"))
            .group_by(AuditFinding.category)
            .order_by(func.count(AuditFinding.id).desc())
            .limit(5)
        )
        rows = session.execute(top_categories_query).all()
        top_finding_categories = [
            FindingCategory(category=row[0], count=row[1]) for row in rows
        ]

        return MetricsResponse(
            total_audits=total_audits,
            audits_today=audits_today,
            average_health_score=round(avg_health, 1) if avg_health is not None else None,
            average_processing_seconds=(
                round(avg_processing, 2) if avg_processing is not None else None
            ),
            total_impact_eur_detected=round(total_impact, 2),
            top_finding_categories=top_finding_categories,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
