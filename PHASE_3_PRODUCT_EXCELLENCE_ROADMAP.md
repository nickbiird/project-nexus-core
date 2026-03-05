# PHASE_3_PRODUCT_EXCELLENCE_ROADMAP.md — Yellowbird Telemetry

**Document Type:** Strategic Architecture Roadmap  
**Classification:** Internal — Principal Architect Reference  
**Repository:** `nickbiird/project-nexus-core`  
**Phase:** 3 — Core Product & Software Excellence  
**Date:** March 6, 2026  
**Author:** Architecture Review  
**Prerequisite:** Phase 2 (GTM Lead Generation Pipeline) — 100% Complete. 190/190 tests passing. Zero lint violations. Full `mypy --strict` compliance.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Assessment](#2-current-state-assessment)
3. [Architectural Guardrails](#3-architectural-guardrails)
4. [Execution Epics](#4-execution-epics)
   - [Priority 1: Application Architecture Decomposition](#priority-1-application-architecture-decomposition)
   - [Priority 2: Data & ETL Maturation](#priority-2-data--etl-maturation)
   - [Priority 3: Infrastructure, CI/CD, & Deployment](#priority-3-infrastructure-cicd--deployment)
   - [Priority 4: Observability & Production Readiness](#priority-4-observability--production-readiness)
   - [Priority 5: Testing Strategy V2](#priority-5-testing-strategy-v2)
5. [Dependency Audit & Rationalization](#5-dependency-audit--rationalization)
6. [Risk Register](#6-risk-register)

---

## 1. Executive Summary

### Philosophy

Phase 2 proved that strict engineering discipline — immutability, pure functions, deterministic validation, zero-I/O scoring, mocked-to-the-teeth unit tests — produces systems that work on the first real run. The leadgen backend is the internal gold standard. Phase 3 applies that identical discipline to the two layers that currently lack it: the Streamlit frontend (`app/`) and the core ETL product (`src/etl/`).

The objective is not cosmetic refactoring. The objective is to make the revenue-generating product — the Data Surgery audit dashboard and its underlying profiling engine — as architecturally rigorous as the pipeline that finds the clients who buy it.

### Core Objectives

1. **Decouple business logic from UI rendering.** The `app.py` monolith currently mixes data loading, statistical computation, chart construction, HTML generation, session state management, and layout orchestration in a single 990-line procedural script. This is the `process_leads.py` of the frontend — it works, but it cannot scale, cannot be tested, and cannot be maintained without regression risk.

2. **Harden data ingestion for the actual product.** The ETL profiler (`excel_profiler.py`) is the engine that powers the Challenger Sale "Kill Shot." It currently operates on flat files with no persistence, no schema migration, and no audit trail. Phase 3 moves it to a proper data layer with SQLAlchemy 2.0, strict repository patterns, and deterministic schema evolution via Alembic.

3. **Make the system deployable.** The `Dockerfile` and `docker-compose.yml` exist as scaffolds. They do not build a working container. Phase 3 produces a single `docker compose up` command that starts the full stack: Streamlit dashboard, FastAPI backend, and PostgreSQL database.

4. **Instrument everything.** The leadgen pipeline has structured `logging` with per-module loggers. The dashboard has zero observability. No error tracking. No performance metrics. No way to know if a client's audit failed silently. Phase 3 introduces `structlog` across all layers, Sentry for error tracking, and basic Prometheus-compatible metrics.

5. **Extend the testing perimeter.** 190 unit tests cover the leadgen backend. Zero tests cover the dashboard. Zero tests cover the profiler's integration with real data. Phase 3 adds integration tests for the ETL pipeline, contract tests for the profiler's output schema, and smoke tests for the Streamlit UI.

---

## 2. Current State Assessment

### 2.1 What Is Good

**The leadgen backend is exemplary.** Frozen dataclasses, `StrEnum`-based domain modeling, pure-function scoring, strict exit codes from the CLI, 100% `mypy --strict` compliance, and 190 heavily-mocked unit tests. This is the engineering standard Phase 3 must replicate.

**The `theme.py` module is well-structured.** Brand constants are defined as module-level constants (`NAVY`, `GOLD`, `RED_LOSS`). CSS generation is centralized in `get_custom_css()`. HTML rendering helpers (`render_finding_card`, `render_health_score`, `render_total_impact`) are pure functions that accept data and return strings. This module is already close to the Phase 2 standard — it has no side effects, no state, and no I/O. It needs only minor hardening (type annotations, docstring completion).

**The `pyproject.toml` is comprehensive and well-organized.** Dependency groups are logical (core data engineering, LLM integration, web framework, dashboard, dev tools). Ruff configuration is aggressive and appropriate. Pytest markers (`slow`, `integration`, `llm`) are forward-looking. The build system is correctly configured with `setuptools`.

**CI/CD exists and is green.** GitHub Actions runs `ruff`, `mypy`, and `pytest` on push. This is a solid foundation to extend.

### 2.2 What Is Technical Debt

**`app.py` is a 990-line monolith with at least six distinct responsibilities fused into procedural spaghetti.**

Specifically:

- **Data ingestion and temp file management** (lines 596–648): Raw file handling with inline `tempfile` creation, manual `unlink()` calls wrapped in bare `except Exception`, and direct mutation of the `ProfilingReport` object (`report.file_path = file_name`, `report.processing_time_seconds = round(elapsed, 2)`). This violates immutability and makes the report object's state unpredictable.

- **Demo data generation** (lines 87–134): `generate_demo_data()` contains hardcoded synthetic data construction with inline anomaly injection (`data["importe_total"][5] = 95000.0`). This is fixture logic embedded in the application module.

- **Chart construction** (lines 142–352): Three Plotly builder functions (`build_waterfall_chart`, `build_anomaly_scatter`, `build_anomaly_type_bar`) contain ~210 lines of visualization code with duplicated layout dictionaries, hardcoded type-to-color mappings, and repeated label translation dictionaries (the same `type_labels` dict appears twice, at lines 227 and 303).

- **HTML report generation** (lines 360–491): `generate_html_report()` is a 130-line function that constructs an entire HTML document via f-string interpolation with inline CSS. This is an untestable, unreviewable wall of string concatenation.

- **Session state management** (lines 557–567): Bare `if "report" not in st.session_state` checks scattered throughout. No centralized state schema. No validation of state transitions.

- **Layout orchestration** (lines 660–990): The tab-based UI layout mixes data access (`report.findings`), conditional rendering, metric computation (`gross_revenue` calculation at lines 679–695), and Streamlit widget calls in deeply nested `with` blocks.

**The `app.py` → `excel_profiler.py` boundary is a direct function call with no abstraction.** Line 620: `report = profile_excel(tmp_path)`. If the profiler's interface changes, the UI breaks. If the profiler raises an unexpected exception, the UI shows a raw Python traceback wrapped in a generic `st.error()`. There is no service layer, no result type, and no error taxonomy.

**The `src/etl/` directory is almost entirely empty.** The `cleaners/`, `loaders/`, `validators/` subdirectories contain only `__init__.py` files. The `profilers/` directory contains a single file (`excel_profiler.py`). The ETL "layer" is a single module doing all the work, with no separation between schema detection, statistical analysis, anomaly detection, entity resolution, and finding generation.

**There is no database layer.** The `pyproject.toml` declares `sqlalchemy>=2.0.25`, `psycopg2-binary>=2.9.9`, and `alembic>=1.13.0` as dependencies, but zero code in the repository uses them. Every data flow is file-in, report-out, ephemeral. No audit history. No client tracking. No persistence of profiling results across sessions.

**The Docker infrastructure is a scaffold.** The `infra/docker/` directory contains a `Dockerfile` and `docker-compose.yml`, but based on the repo structure (no `.dockerignore`, no multi-stage build evidence, no health checks), these are not production-ready.

**`great-expectations` and `ydata-profiling` are declared but unused.** These are heavyweight dependencies (ydata-profiling alone pulls in ~40 transitive packages) that add install time and attack surface with zero current value. The profiling engine is custom-built in `excel_profiler.py`.

### 2.3 What Is Missing

| Gap | Impact | Severity |
|-----|--------|----------|
| No service layer between UI and profiler | UI crashes propagate unrecoverably; profiler cannot be called from API or CLI without importing Streamlit | **Critical** |
| No database persistence | Every audit is ephemeral; no client history; no longitudinal analysis; cannot demonstrate improvement over time | **Critical** |
| No error boundaries in the UI | Any exception in profiling, charting, or rendering crashes the entire page with a Python traceback | **High** |
| No integration tests for ETL | The profiler has unit tests but no tests with real-world messy data that exercise the full pipeline | **High** |
| No deployment automation | Cannot ship the product to a client-accessible URL without manual server configuration | **High** |
| No observability in the dashboard | Silent failures in production; no way to diagnose "the audit didn't work" reports from clients | **High** |
| No API layer for the profiler | The FastAPI skeleton exists (`api/`) but has no routes; cannot integrate with WhatsApp bot or external systems | **Medium** |
| No rate limiting or abuse prevention | The public-facing audit tool has no file size enforcement beyond a client-side check | **Medium** |
| No export to PDF | The HTML export exists but clients expect branded PDF reports | **Medium** |

---

## 3. Architectural Guardrails

Phase 3 operates under the same strict engineering rules established in Phase 2. No exceptions. No "we'll clean it up later."

### Rule 1: Strict Layer Separation

```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                         │
│  app/pages/*.py — Streamlit page modules (rendering only)    │
│  app/components/*.py — Reusable UI widgets                    │
│  app/theme.py — Brand constants & CSS (already clean)        │
├──────────────────────────────────────────────────────────────┤
│                    SERVICE LAYER                              │
│  src/services/audit_service.py — Orchestrates profiling      │
│  src/services/export_service.py — JSON/HTML/PDF generation   │
│  src/services/demo_service.py — Synthetic data generation    │
├──────────────────────────────────────────────────────────────┤
│                    DOMAIN LAYER                               │
│  src/etl/profilers/ — Statistical analysis & anomaly detect  │
│  src/etl/cleaners/ — Data normalization                      │
│  src/etl/validators/ — Schema & quality validation           │
│  src/llm/ — Entity resolution, prompt management             │
├──────────────────────────────────────────────────────────────┤
│                    DATA ACCESS LAYER                          │
│  src/db/models.py — SQLAlchemy 2.0 ORM models               │
│  src/db/repositories/ — Repository pattern (one per entity)  │
│  src/db/migrations/ — Alembic migration scripts              │
├──────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                             │
│  src/common/config/ — Settings, env loading                  │
│  src/common/logging/ — structlog configuration               │
│  src/common/exceptions/ — Typed exception hierarchy          │
│  infra/ — Docker, Terraform, nginx                           │
└──────────────────────────────────────────────────────────────┘
```

**Enforcement:** No module in a higher layer may import from a lower layer except through the layer directly beneath it. The presentation layer never touches the database. The service layer never emits HTML. The domain layer never reads environment variables.

### Rule 2: Immutable Domain Objects

All data transfer objects between layers use `@dataclass(frozen=True)` or `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True)`. The `ProfilingReport` returned by the profiler is immutable after construction. The UI does not mutate it (the current `report.file_path = file_name` violation is eliminated).

### Rule 3: Explicit Error Types

Every service method returns a typed result or raises a typed exception from the `src/common/exceptions/` hierarchy. No bare `except Exception`. No `st.error(str(e))`. The exception hierarchy:

```
NexusError (base)
├── IngestionError
│   ├── UnsupportedFileFormatError
│   ├── FileTooLargeError
│   ├── CorruptFileError
│   └── EmptyDatasetError
├── ProfilingError
│   ├── SchemaDetectionError
│   ├── AnomalyDetectionError
│   └── EntityResolutionError
├── PersistenceError
│   ├── ConnectionError
│   ├── MigrationError
│   └── IntegrityError
└── ExportError
    ├── TemplateRenderError
    └── PDFGenerationError
```

### Rule 4: Zero Raw SQL

All database access goes through SQLAlchemy 2.0's typed ORM with the 2.0-style `select()` API. No `session.execute(text("SELECT ..."))`. No string interpolation in queries. The `sqlglot` dependency in `pyproject.toml` is reserved exclusively for the NL-to-SQL engine (`src/engine/nl_to_sql/`), not for the data access layer.

### Rule 5: Every Public Function Has a Type Signature and Docstring

Enforced by `mypy --strict` and a custom `ruff` rule (`ANN` category, already enabled). No `Any` return types. No untyped function arguments. The `ANN001`, `ANN201`, and `ANN401` ignores currently in `pyproject.toml` are to be progressively removed as each module is hardened.

### Rule 6: No Business Logic in Presentation

Streamlit page modules may call service methods and render their results. They may not perform calculations, data transformations, filtering, aggregation, or conditional business logic. The `gross_revenue` computation currently at `app.py:679-695` is a business logic violation — it belongs in the service layer.

### Rule 7: Configuration via Environment, Not Code

All runtime configuration (database URLs, API keys, feature flags, file size limits) flows through `pydantic-settings` from environment variables or `.env` files. No hardcoded `MAX_FILE_SIZE_MB = 50` in application code. The existing `src/common/config/settings.py` module is the single source of truth.

---

## 4. Execution Epics

---

### Priority 1: Application Architecture Decomposition

**Objective:** Decompose the `app.py` monolith into a layered, testable, maintainable architecture. Eliminate all business logic from the presentation layer. Establish the service layer as the single orchestration boundary.

**Estimated Effort:** 25–30 hours

#### 1.1 Create the Service Layer

**Files to create:**

| File | Responsibility |
|------|---------------|
| `src/services/__init__.py` | Package init |
| `src/services/audit_service.py` | Orchestrates file ingestion → profiling → report construction. Accepts a file path or byte stream, returns an immutable `AuditResult`. Handles all error translation from domain exceptions to service-level results. |
| `src/services/export_service.py` | Generates JSON, HTML, and (future) PDF exports from an `AuditResult`. Contains the HTML template logic currently in `generate_html_report()`. |
| `src/services/demo_service.py` | Contains `generate_demo_data()`, currently at `app.py:87-134`. Synthetic data generation is a service concern, not a UI concern. |

**Key design decisions:**

- `AuditService.run_audit(file_path: Path, config: AuditConfig) -> AuditResult` is a pure orchestration method. It does not know about Streamlit, sessions, or progress bars. It accepts an optional callback (`on_progress: Callable[[int, str], None] | None`) to decouple progress reporting from UI framework.

- `AuditResult` is a `@dataclass(frozen=True)` that wraps the `ProfilingReport` with additional metadata (original filename, processing duration, audit ID). The UI layer never sees `ProfilingReport` directly — it only sees `AuditResult`.

- The current pattern of `report.file_path = file_name` (mutating the report after construction) is replaced by passing the original filename into `AuditService.run_audit()`, which constructs the `AuditResult` with the correct metadata from the start.

#### 1.2 Decompose the Presentation Layer

**Files to create:**

| File | Responsibility |
|------|---------------|
| `app/app.py` | Reduced to ~50 lines: page config, CSS injection, routing to the active page. No business logic. |
| `app/state.py` | Centralized session state schema using a `@dataclass` that wraps `st.session_state`. All state reads and writes go through typed accessor methods. No more bare `st.session_state["report"]`. |
| `app/pages/__init__.py` | Package init |
| `app/pages/upload.py` | The file upload + demo data landing page. Calls `AuditService`, stores result in state. |
| `app/pages/executive_summary.py` | Tab 1: margin leakage metrics, waterfall chart, health score, findings cards. Reads from state, renders only. |
| `app/pages/anomaly_deepdive.py` | Tab 2: anomaly scatter, type distribution bar chart, anomaly table. |
| `app/pages/entities.py` | Tab 3: entity cluster analysis. |
| `app/pages/columns.py` | Tab 4: column quality profiles, completeness chart. |
| `app/pages/downloads.py` | Tab 5: JSON and HTML export buttons. Calls `ExportService`. |
| `app/components/__init__.py` | Package init |
| `app/components/charts.py` | All Plotly chart builder functions (`build_waterfall_chart`, `build_anomaly_scatter`, `build_anomaly_type_bar`, `build_completeness_bar`). Extracted from `app.py` with zero modification to chart logic. |
| `app/components/cards.py` | Finding cards, health score box, total impact box — re-exports from `theme.py` render functions with any additional component wrappers. |

**Files to delete:**

- `app/app.py` (current version) — replaced by the decomposed structure above. The original is preserved in git history.

#### 1.3 Implement Error Boundaries

Each page module wraps its rendering in a structured error handler:

- Profiling errors → user-friendly message with file format guidance, not a Python traceback.
- Chart rendering errors → graceful degradation to a text summary ("Chart unavailable — X anomalies detected in column Y").
- Export errors → explicit error message with retry button.

The pattern: the service layer raises typed exceptions. The page module catches the specific exception class and renders the appropriate Streamlit widget (`st.error`, `st.warning`, `st.info`). No generic `except Exception` at the UI level.

#### 1.4 Definition of Done

- `app.py` is under 80 lines.
- No file in `app/pages/` imports from `src/etl/` or `src/db/` directly.
- Every page module imports only from `src/services/`, `app/components/`, `app/state.py`, and `app/theme.py`.
- `generate_demo_data()` is callable from a unit test without importing Streamlit.
- `generate_html_report()` is callable from a unit test without importing Streamlit.
- All chart builder functions are callable from unit tests with mock data.
- `mypy --strict` passes on all new files.
- Zero `ruff` violations.
- The dashboard renders identically to the current version (visual regression check).

#### 1.5 Traps to Avoid

- **Do not introduce a web framework abstraction layer over Streamlit.** The goal is separation of concerns within Streamlit, not a migration away from it. Streamlit's execution model (full re-run on every interaction) is a constraint to work within, not around.
- **Do not create a "controller" layer between pages and services.** Two layers (page → service) is sufficient. A third layer adds indirection without value at this scale.
- **Do not refactor the chart styling.** The Plotly configurations in `build_waterfall_chart` and friends are correct and battle-tested. Extract them as-is. Styling changes belong in a separate design epic.

---

### Priority 2: Data & ETL Maturation

**Objective:** Introduce a proper data persistence layer. Harden the profiling engine. Move from ephemeral file-in/report-out to a system that tracks audits, stores results, and enables longitudinal analysis.

**Estimated Effort:** 30–35 hours

#### 2.1 Database Schema Design (SQLAlchemy 2.0)

**Files to create:**

| File | Responsibility |
|------|---------------|
| `src/db/__init__.py` | Package init, engine and session factory |
| `src/db/models.py` | SQLAlchemy 2.0 Mapped classes for all entities |
| `src/db/repositories/__init__.py` | Package init |
| `src/db/repositories/audit_repository.py` | CRUD for `Audit` and `AuditFinding` |
| `src/db/repositories/client_repository.py` | CRUD for `Client` |
| `src/db/session.py` | Session factory with context manager, connection pooling config |

**Core ORM models (SQLAlchemy 2.0 Mapped style):**

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| `Client` | `id`, `company_name`, `nif`, `contact_email`, `vertical`, `created_at` | The company receiving the audit. Links a leadgen `Lead` to an audit client. |
| `Audit` | `id`, `client_id` (FK), `file_name`, `file_hash` (SHA-256), `total_rows`, `total_columns`, `health_score`, `completeness_score`, `consistency_score`, `uniqueness_score`, `total_impact_eur`, `processing_seconds`, `created_at` | One record per audit run. The `file_hash` enables deduplication — re-uploading the same file returns the cached result. |
| `AuditFinding` | `id`, `audit_id` (FK), `category`, `description`, `estimated_eur_impact`, `confidence`, `rows_affected` | One-to-many from `Audit`. Maps directly to the current `ProfilingReport.findings` list. |
| `AuditColumnProfile` | `id`, `audit_id` (FK), `column_name`, `inferred_type`, `null_pct`, `unique_count`, `format_inconsistencies` | Per-column quality metadata. |
| `AuditAnomaly` | `id`, `audit_id` (FK), `column_name`, `anomaly_type`, `value`, `row_index`, `context` | Individual anomaly records for the deep-dive analysis. |

**Database selection strategy:**

- **Development and single-tenant deployment:** SQLite. Zero configuration. The file lives at `data/yellowbird.db` (gitignored). Alembic migrations target SQLite by default.
- **Multi-tenant or hosted deployment:** PostgreSQL. The `psycopg2-binary` dependency is already declared. The `src/common/config/settings.py` module reads `DATABASE_URL` from the environment. SQLAlchemy's URL dispatch handles the driver switch transparently.

#### 2.2 Alembic Migration Infrastructure

**Files to create:**

| File | Responsibility |
|------|---------------|
| `src/db/migrations/env.py` | Alembic environment config, auto-imports all models |
| `src/db/migrations/versions/001_initial_schema.py` | First migration: creates `clients`, `audits`, `audit_findings`, `audit_column_profiles`, `audit_anomalies` |
| `alembic.ini` | Top-level Alembic config, `sqlalchemy.url` reads from env |

**Migration discipline:** Every schema change is a numbered migration. No manual `CREATE TABLE`. No `Base.metadata.create_all()` in production. Alembic `--autogenerate` is used for drafting only — every migration is reviewed and hand-edited before commit.

#### 2.3 Repository Pattern

Each repository class encapsulates all database access for its entity. Repository methods use the SQLAlchemy 2.0 `select()` API exclusively.

Pattern for `AuditRepository`:

- `save_audit(session: Session, audit: AuditResult) -> Audit` — Persists an audit and all its child entities (findings, column profiles, anomalies) in a single transaction.
- `get_audit(session: Session, audit_id: UUID) -> Audit | None` — Retrieves by primary key.
- `get_audits_for_client(session: Session, client_id: UUID) -> Sequence[Audit]` — Historical audits for longitudinal analysis.
- `get_audit_by_file_hash(session: Session, file_hash: str) -> Audit | None` — Deduplication lookup.

**No repository method accepts or returns Streamlit objects, Pandas DataFrames, or raw SQL strings.**

#### 2.4 Harden the Profiling Engine

The existing `excel_profiler.py` remains the core analysis engine. Phase 3 hardens it without rewriting it:

- **Extract the `ProfilingReport` and all sub-dataclasses** (e.g., `ColumnProfile`, `Finding`, `AnomalyAnalysis`, `EntityAnalysis`) into `src/etl/profilers/models.py`. These are domain objects that multiple layers need to import. They must not be defined inside the profiler module.
- **Add input validation** at the `profile_excel()` entry point: file existence check, file size check, extension validation, encoding detection for CSV. Raise `IngestionError` subtypes, not generic `ValueError`.
- **Add SHA-256 file hashing** before profiling. This hash is used by the database layer for deduplication and by the audit trail for integrity verification.
- **Formalize the `profile_excel()` return contract** with a Protocol or ABC: any future profiler (e.g., `profile_csv`, `profile_parquet`) must return the same `ProfilingReport` type.

#### 2.5 Populate the Empty ETL Directories

The `src/etl/cleaners/`, `src/etl/loaders/`, and `src/etl/validators/` directories currently contain only `__init__.py`. Phase 3 gives them purpose:

| Directory | First Module | Responsibility |
|-----------|-------------|---------------|
| `cleaners/` | `type_coercion.py` | Deterministic type coercion rules: date parsing (multi-format, as seen in the demo data), numeric extraction from mixed-format strings, currency symbol stripping. Currently inline in `excel_profiler.py`. |
| `loaders/` | `file_loader.py` | Unified file ingestion: reads Excel (`.xlsx`, `.xls` via LibreOffice conversion), CSV (with delimiter detection), and (future) Parquet. Returns a `pandas.DataFrame` with metadata. Replaces the inline `tempfile` logic in `app.py`. |
| `validators/` | `schema_validator.py` | Post-load schema validation: minimum row count, minimum column count, detects header-only files, validates column name uniqueness. Uses the exception hierarchy from Rule 3. |

#### 2.6 Definition of Done

- `alembic upgrade head` creates all tables in a fresh SQLite database.
- `AuditRepository.save_audit()` persists a profiling result and all child entities in a single transaction.
- `AuditRepository.get_audit_by_file_hash()` returns a cached audit for a previously profiled file.
- The `ProfilingReport` dataclass and all sub-types live in `src/etl/profilers/models.py`, not inside `excel_profiler.py`.
- `profile_excel()` raises `IngestionError` subtypes for invalid inputs, not generic exceptions.
- `mypy --strict` passes on all new `src/db/` and `src/etl/` modules.
- Zero `ruff` violations.
- `great-expectations` and `ydata-profiling` are removed from `pyproject.toml` dependencies (see Section 5).

#### 2.7 Traps to Avoid

- **Do not over-normalize the schema.** The audit report is a document, not a transactional system. Store findings as a one-to-many relationship, not as a normalized star schema. The goal is persistence and retrieval, not OLAP.
- **Do not use `Base.metadata.create_all()` anywhere except in test fixtures.** Production schema management goes exclusively through Alembic.
- **Do not introduce an async ORM pattern.** The Streamlit execution model is synchronous. SQLAlchemy's synchronous session is correct here. Async (`asyncpg`, `SQLAlchemy AsyncSession`) adds complexity without benefit until the FastAPI layer is actively serving traffic.
- **Do not attempt to migrate `excel_profiler.py` internals.** The profiler's statistical logic is working and tested. Phase 3 extracts its types and hardens its interface. Internal refactoring of the profiler is a separate, lower-priority effort.

---

### Priority 3: Infrastructure, CI/CD, & Deployment

**Objective:** Produce a reproducible, single-command deployment. Harden the Docker configuration. Extend CI/CD to cover the full stack.

**Estimated Effort:** 15–20 hours

#### 3.1 Docker Production Configuration

**Files to create or replace:**

| File | Responsibility |
|------|---------------|
| `infra/docker/Dockerfile` | Multi-stage build: `builder` stage installs dependencies, `runtime` stage copies only the installed packages. Non-root user (`yellowbird`). Health check endpoint. |
| `infra/docker/Dockerfile.dev` | Development image with hot reload, dev dependencies, and mounted volumes. |
| `infra/docker/docker-compose.yml` | Full stack: `app` (Streamlit), `api` (FastAPI), `db` (PostgreSQL 16), `nginx` (reverse proxy with TLS termination). |
| `infra/docker/docker-compose.dev.yml` | Development override: SQLite instead of PostgreSQL, volume mounts for live reload, exposed debug ports. |
| `infra/docker/.dockerignore` | Excludes `.git/`, `data/`, `tests/`, `*.pyc`, `__pycache__/`, `.env`, `*.bak`, `lead_gen.log`, `node_modules/`. |
| `infra/docker/nginx/nginx.conf` | Reverse proxy config: routes `/` to Streamlit (port 8501), `/api/` to FastAPI (port 8000). Rate limiting. Security headers. |

**Dockerfile design principles:**

- **Pin the base image.** `python:3.11-slim-bookworm` (not `python:3.11` — the full image is 1.2GB). Pin to a specific digest for reproducibility.
- **Install system dependencies first** (libpq-dev for psycopg2, build-essential for native extensions), then copy `pyproject.toml` and `requirements.txt` to leverage Docker layer caching.
- **Non-root execution.** The container runs as `yellowbird:yellowbird` (UID 1000). No `--privileged`. No `SYS_ADMIN` capability.
- **Health check.** `HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1` for Streamlit. FastAPI gets its own `/health` endpoint.

#### 3.2 CI/CD Pipeline Hardening

**Files to modify:**

| File | Changes |
|------|---------|
| `.github/workflows/ci.yml` | Add: Docker build test (`docker build --target builder .`). Add: Alembic migration test (`alembic upgrade head` against a fresh SQLite). Add: dependency vulnerability scan (`pip-audit`). Add: test coverage gate (fail if coverage drops below 80%). |

**New CI stages (in order):**

1. **Lint** — `ruff check .` (existing)
2. **Type Check** — `mypy --strict src/ scripts/ app/` (extend to `app/`)
3. **Unit Tests** — `pytest tests/unit/ --cov=src --cov=scripts --cov=app --cov-fail-under=80`
4. **Integration Tests** — `pytest tests/integration/ -m "not slow"` (new, requires SQLite)
5. **Docker Build** — `docker build -f infra/docker/Dockerfile --target builder .`
6. **Migration Test** — `alembic upgrade head && alembic downgrade base` (roundtrip)
7. **Security Scan** — `pip-audit --require-hashes --strict`

#### 3.3 Environment Configuration

**Files to create:**

| File | Responsibility |
|------|---------------|
| `.env.example` | Documented template with all required and optional environment variables. |
| `src/common/config/settings.py` | Refactor: use `pydantic-settings` `BaseSettings` with `SettingsConfigDict(env_file=".env")`. Typed settings for: `DATABASE_URL`, `HUNTER_API_KEY`, `ANTHROPIC_API_KEY`, `MAX_UPLOAD_SIZE_MB`, `LOG_LEVEL`, `SENTRY_DSN`, `ENVIRONMENT` (dev/staging/prod). |

#### 3.4 Definition of Done

- `docker compose -f infra/docker/docker-compose.yml up` starts the full stack from a cold state in under 60 seconds.
- `docker compose -f infra/docker/docker-compose.dev.yml up` starts the development stack with live reload.
- The CI pipeline runs all seven stages and completes in under 5 minutes.
- `pip-audit` reports zero known vulnerabilities in production dependencies.
- The `.env.example` file documents every environment variable with type, default value, and purpose.

#### 3.5 Traps to Avoid

- **Do not use `docker compose` profiles for dev vs. prod.** Use separate compose files with `docker compose -f base.yml -f dev.yml up`. Profiles create implicit configuration that is harder to audit.
- **Do not bake secrets into Docker images.** All secrets come from environment variables or Docker secrets at runtime. The `Dockerfile` never contains `ENV HUNTER_API_KEY=...`.
- **Do not use `latest` tags for any base image.** Pin to specific versions (`python:3.11.8-slim-bookworm`, `postgres:16.2-alpine`, `nginx:1.25-alpine`).
- **Do not add Kubernetes configuration yet.** Single-host Docker Compose is the correct deployment model for an early-revenue SaaS product. Kubernetes adds operational overhead that is unjustified before product-market fit.

---

### Priority 4: Observability & Production Readiness

**Objective:** Instrument the application so that failures are detected, diagnosed, and resolved without asking the client "can you send me the file again?"

**Estimated Effort:** 12–15 hours

#### 4.1 Structured Logging with `structlog`

**Files to create or modify:**

| File | Responsibility |
|------|---------------|
| `src/common/logging/__init__.py` | Configure `structlog` with: JSON output in production, human-readable colored output in development. Bind `environment`, `version`, `request_id` (if API) to every log event. |

**Migration path:** Replace all `logging.getLogger(__name__)` calls in `src/` and `app/` with `structlog.get_logger()`. The leadgen pipeline's existing `logging` usage in `scripts/leadgen/` is left as-is (it's a CLI tool, not a web service — structured JSON logging is overkill for terminal output).

**Key log events for the dashboard:**

| Event | Level | Context Fields |
|-------|-------|---------------|
| `audit.started` | INFO | `file_name`, `file_size_bytes`, `file_hash` |
| `audit.profiling_complete` | INFO | `file_hash`, `rows`, `columns`, `duration_seconds` |
| `audit.finding_detected` | INFO | `file_hash`, `category`, `impact_eur`, `confidence` |
| `audit.completed` | INFO | `file_hash`, `health_score`, `total_impact_eur`, `duration_seconds` |
| `audit.failed` | ERROR | `file_hash`, `error_type`, `error_message`, `traceback` |
| `export.generated` | INFO | `file_hash`, `format` (json/html/pdf), `size_bytes` |

#### 4.2 Error Tracking with Sentry

**Files to modify:**

| File | Changes |
|------|---------|
| `pyproject.toml` | Add `sentry-sdk[pure_eval]>=2.0.0` to dependencies |
| `src/common/config/settings.py` | Add `SENTRY_DSN: str | None = None` field |
| `app/app.py` | Initialize Sentry at startup: `sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)` |

Sentry captures unhandled exceptions with full context (file name, file size, profiling stage). The `traces_sample_rate=0.1` captures 10% of transactions for performance monitoring without overwhelming the free tier.

#### 4.3 Application Metrics

**For the initial deployment, keep metrics minimal and file-based.** Do not introduce Prometheus/Grafana until there is a multi-client production deployment.

Track the following in the database `audits` table (already designed in Priority 2):

- Audits per day
- Average processing time
- Average health score
- Total estimated impact detected (cumulative — this is a sales metric)
- Most common finding categories

A simple `GET /api/metrics` endpoint on the FastAPI layer exposes these as JSON for a future admin dashboard.

#### 4.4 Definition of Done

- Every audit run produces at least 4 structured log events (`started`, `profiling_complete`, `completed` or `failed`).
- Unhandled exceptions in the dashboard are captured by Sentry with file context.
- `structlog` outputs JSON in production (`ENVIRONMENT=prod`) and human-readable format in development.
- The `GET /api/metrics` endpoint returns audit volume and average health score.

#### 4.5 Traps to Avoid

- **Do not add `structlog` to the leadgen CLI.** The CLI already has adequate logging via Python's `logging` module. Mixing `structlog` and `logging` in the same process creates configuration conflicts.
- **Do not over-instrument.** Every log event should answer a question someone will actually ask during an incident. "What file was the client uploading?" "At what stage did it fail?" "How long did it take?" Those are the questions. "What was the median outlier value?" is not an operational question — it's an analytics question and belongs in the audit report, not in the logs.
- **Do not use Sentry's performance monitoring as a replacement for application metrics.** Sentry is for errors. The database-backed metrics endpoint is for business intelligence.

---

### Priority 5: Testing Strategy V2

**Objective:** Extend the testing perimeter from the leadgen backend to the dashboard, ETL pipeline, and database layer. Achieve 80%+ coverage across the entire codebase.

**Estimated Effort:** 20–25 hours

#### 5.1 Integration Tests for the ETL + Database Pipeline

**Files to create:**

| File | Responsibility |
|------|---------------|
| `tests/integration/__init__.py` | Package init |
| `tests/integration/test_audit_pipeline.py` | End-to-end: file upload → profiling → database persistence → retrieval. Uses a real SQLite database (in-memory or temp file). Uses the synthetic demo dataset as the input fixture. |
| `tests/integration/test_audit_deduplication.py` | Profiling the same file twice returns the cached audit (matched by `file_hash`). |
| `tests/integration/test_alembic_migrations.py` | `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` roundtrip on a fresh SQLite database. Verifies migration reversibility. |

**Fixture strategy:** Use `pytest` fixtures with `tmp_path` for database files and `conftest.py` in `tests/integration/` for shared session factories.

#### 5.2 Contract Tests for the Profiler Output

**Files to create:**

| File | Responsibility |
|------|---------------|
| `tests/unit/etl/test_profiling_report_contract.py` | Validates that `ProfilingReport` returned by `profile_excel()` conforms to the expected schema: all required fields present, types correct, scores in 0–100 range, findings list is never `None`, column profiles list length equals `total_columns`. |

This is critical because the database layer's `save_audit()` method depends on the profiler's output shape. If the profiler's return type changes (new field, renamed field, changed type), the contract test catches it before the integration test does — and the error message is precise.

#### 5.3 Service Layer Unit Tests

**Files to create:**

| File | Responsibility |
|------|---------------|
| `tests/unit/services/test_audit_service.py` | Tests `AuditService.run_audit()` with a mocked profiler and mocked repository. Verifies: correct delegation to profiler, correct persistence call, correct error translation (profiler exception → service exception). |
| `tests/unit/services/test_export_service.py` | Tests HTML export generation with a mock `AuditResult`. Validates: HTML is well-formed, contains the expected data values, does not contain raw Python objects. |
| `tests/unit/services/test_demo_service.py` | Tests synthetic data generation: correct row count, expected columns present, anomalies injected at expected positions. |

#### 5.4 UI Smoke Tests

**Files to create:**

| File | Responsibility |
|------|---------------|
| `tests/smoke/__init__.py` | Package init |
| `tests/smoke/test_dashboard_renders.py` | Uses `streamlit.testing.v1.AppTest` (Streamlit's built-in testing framework) to verify: the app loads without errors, the demo data button triggers profiling, the tabs render without exceptions. |

**Scope limitation:** Smoke tests verify that the UI does not crash. They do not verify visual correctness (that's a manual QA step) or chart content (that's covered by unit tests on the chart builder functions).

#### 5.5 Test Infrastructure Updates

**Files to modify:**

| File | Changes |
|------|---------|
| `pyproject.toml` | Add `pytest-xdist>=3.5.0` to `[dev]` for parallel test execution. Add `pytest-sugar>=1.0.0` for readable output. Update `addopts` to include `--cov-fail-under=80`. |
| `tests/conftest.py` | Add shared fixtures: `mock_profiling_report()` (returns a realistic frozen `ProfilingReport`), `sqlite_session()` (in-memory SQLAlchemy session for integration tests), `demo_dataframe()` (the demo data as a fixture). |

#### 5.6 Coverage Targets

| Layer | Current Coverage | Phase 3 Target |
|-------|-----------------|----------------|
| `scripts/leadgen/` | ~95% (190 tests) | Maintain ≥95% |
| `src/etl/profilers/` | ~60% (unit tests exist) | ≥80% |
| `src/services/` | 0% (does not exist yet) | ≥90% |
| `src/db/` | 0% (does not exist yet) | ≥85% |
| `app/` | 0% | ≥70% (smoke + component tests) |

#### 5.7 Definition of Done

- `pytest tests/` runs the full suite (unit + integration + smoke) and reports ≥80% total coverage.
- Integration tests use a real SQLite database, not mocks.
- The migration roundtrip test passes.
- The Streamlit smoke test loads the app and triggers a demo audit without crashing.
- CI fails if coverage drops below 80%.

#### 5.8 Traps to Avoid

- **Do not mock the database in integration tests.** The entire point of integration tests is to exercise real I/O boundaries. Use an in-memory SQLite database — it's fast enough for CI and catches real SQL errors.
- **Do not write Selenium/Playwright tests for the Streamlit UI.** Streamlit's `AppTest` framework is sufficient for smoke testing. Browser-based E2E tests are fragile, slow, and provide low ROI at this stage.
- **Do not aim for 100% coverage.** The goal is 80% with high-value coverage — service orchestration logic, error paths, and data contracts. Covering every Plotly style parameter is not worth the maintenance cost.

---

## 5. Dependency Audit & Rationalization

Phase 3 includes a dependency cleanup to reduce install time, attack surface, and cognitive overhead.

### Dependencies to Remove

| Dependency | Current Status | Action | Rationale |
|-----------|---------------|--------|-----------|
| `ydata-profiling>=4.6.0` | Declared, unused | **Remove** | Pulls ~40 transitive dependencies. The profiling engine is custom-built. If needed in the future, add it as an optional dependency group. |
| `great-expectations>=0.18.0` | Declared, unused | **Remove** | Heavyweight validation framework. The custom `validators/` module in `src/etl/` replaces this for the current scope. Revisit when data validation requirements exceed what can be maintained in-house. |
| `python-Levenshtein>=0.25.0` | Declared, likely redundant | **Evaluate** | `rapidfuzz` already provides Levenshtein distance computation with a C++ backend. Unless a specific function from `python-Levenshtein` is used that `rapidfuzz` doesn't provide, remove it. |

### Dependencies to Add

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `sentry-sdk[pure_eval]` | `>=2.0.0` | Error tracking (Priority 4) |
| `pytest-xdist` | `>=3.5.0` | Parallel test execution (Priority 5, dev only) |

### Dependencies to Pin More Tightly

The current `pyproject.toml` uses lower-bound pins (`>=X.Y.Z`) for all dependencies. For production stability, add upper-bound pins on fast-moving libraries: `streamlit>=1.31.0,<2.0`, `fastapi>=0.109.0,<1.0`, `pydantic>=2.6.0,<3.0`. The data engineering stack (`pandas`, `numpy`, `sqlalchemy`) already has appropriate upper bounds.

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Streamlit execution model (full re-run) creates state management complexity during decomposition | High | Medium | Centralize all state in `app/state.py` with typed accessors. Use `st.cache_resource` for expensive initializations (database connections, service singletons). |
| Alembic migration conflicts when multiple developers work on schema changes | Low (single contributor) | High | Enforce sequential migration numbering. Never auto-merge migration files. Revisit if the team grows beyond 2. |
| SQLite concurrent write limitations under multi-user load | Medium | Medium | SQLite is correct for single-tenant deployment. The PostgreSQL path is already architected (same ORM models, different `DATABASE_URL`). Switch when concurrent users exceed 5. |
| Docker image size exceeds 1GB due to scientific Python stack (pandas, numpy, plotly) | High | Low | Multi-stage build discards build tools. Use `--no-cache-dir` for pip. Target < 800MB for the runtime image. Accept that the scientific stack has an irreducible size. |
| `structlog` + `logging` coexistence creates configuration conflicts | Medium | Medium | Configure `structlog` as a wrapper around `logging` (use `structlog.stdlib.ProcessorPipeline`). Do not run both systems independently. |
| Phase 3 scope creep into WhatsApp bot or NL-to-SQL engine | Medium | High | Phase 3 is exclusively about the audit dashboard, ETL pipeline, database layer, deployment, and testing. The `src/engine/` directory is explicitly out of scope. |

---

**END OF PHASE_3_PRODUCT_EXCELLENCE_ROADMAP.md**

*Implementation begins with Priority 1 (Application Architecture Decomposition). Each priority is a self-contained epic that can be merged independently. Do not start Priority 2 until Priority 1's Definition of Done is met — the service layer is a prerequisite for the database integration.*
