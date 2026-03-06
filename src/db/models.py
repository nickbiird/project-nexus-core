"""
Project Nexus — ORM Domain Models
====================================

Defines the SQLAlchemy 2.0 declarative models that form the persistence
contract for the Yellowbird audit platform.  All five entities live in this
single module and share a common ``Base``.

Tables
------
- **clients** — customer organisations
- **audits** — individual data-quality profiling runs
- **audit_findings** — "surprise findings" produced by a run
- **audit_column_profiles** — per-column quality statistics
- **audit_anomalies** — individual anomalous data points
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all Project Nexus ORM models."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class Client(Base):
    """A customer organisation that commissions data-quality audits."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nif: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    vertical: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    audits: Mapped[list[Audit]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id!s:.8} company_name={self.company_name!r}>"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class Audit(Base):
    """A single data-quality profiling run against an uploaded file."""

    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    total_rows: Mapped[int | None] = mapped_column(Integer)
    total_columns: Mapped[int | None] = mapped_column(Integer)
    health_score: Mapped[float | None] = mapped_column(Float)
    completeness_score: Mapped[float | None] = mapped_column(Float)
    consistency_score: Mapped[float | None] = mapped_column(Float)
    uniqueness_score: Mapped[float | None] = mapped_column(Float)
    total_impact_eur: Mapped[float | None] = mapped_column(Float)
    processing_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    client: Mapped[Client] = relationship(back_populates="audits")
    findings: Mapped[list[AuditFinding]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    column_profiles: Mapped[list[AuditColumnProfile]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    anomalies: Mapped[list[AuditAnomaly]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Audit id={self.id!s:.8} file_name={self.file_name!r}>"


# ---------------------------------------------------------------------------
# AuditFinding
# ---------------------------------------------------------------------------


class AuditFinding(Base):
    """A concrete, euro-quantified finding produced by a profiling run."""

    __tablename__ = "audit_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("audits.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_eur_impact: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[str | None] = mapped_column(String(20))
    rows_affected: Mapped[int | None] = mapped_column(Integer)

    audit: Mapped[Audit] = relationship(back_populates="findings")

    def __repr__(self) -> str:
        return f"<AuditFinding id={self.id} category={self.category!r}>"


# ---------------------------------------------------------------------------
# AuditColumnProfile
# ---------------------------------------------------------------------------


class AuditColumnProfile(Base):
    """Per-column quality statistics for an audit run."""

    __tablename__ = "audit_column_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("audits.id"), nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inferred_type: Mapped[str | None] = mapped_column(String(50))
    null_pct: Mapped[float | None] = mapped_column(Float)
    unique_count: Mapped[int | None] = mapped_column(Integer)
    format_inconsistencies: Mapped[int | None] = mapped_column(Integer)

    audit: Mapped[Audit] = relationship(back_populates="column_profiles")

    def __repr__(self) -> str:
        return f"<AuditColumnProfile id={self.id} column_name={self.column_name!r}>"


# ---------------------------------------------------------------------------
# AuditAnomaly
# ---------------------------------------------------------------------------


class AuditAnomaly(Base):
    """An individual anomalous data point flagged during profiling."""

    __tablename__ = "audit_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("audits.id"), nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    row_index: Mapped[int | None] = mapped_column(Integer)
    context: Mapped[str | None] = mapped_column(Text)

    audit: Mapped[Audit] = relationship(back_populates="anomalies")

    def __repr__(self) -> str:
        return f"<AuditAnomaly id={self.id} anomaly_type={self.anomaly_type!r}>"
