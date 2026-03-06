# Project Nexus Core — Technical Architecture Review & Engineering Roadmap

**Classification:** Internal — Principal Architect Reference  
**Prepared for:** Technical Co-Founder & Future Engineering Hires  
**Date:** March 6, 2026  
**Author:** Independent Architecture Review  

---

## 1. Stack Verdict

### 1.1 The Foundation: FastAPI + Streamlit + PostgreSQL + Docker + Nginx

This is the correct stack. Not merely defensible — actively correct for this specific product, this specific market, and this specific founder profile. Here is why, evaluated against the three criteria that matter.

**Time-to-market for a solo founder.** Python is the only language where a single developer can build a statistical profiling engine, a web dashboard, a REST API, database migrations, and a CLI-based lead generation pipeline without switching ecosystems. The alternative — a TypeScript/Node backend with a React frontend — would have required twice the calendar time for a product whose core intellectual property is a pandas-based ETL engine. FastAPI gives you automatic OpenAPI documentation, Pydantic validation on every request boundary, and async support when you eventually need it. Streamlit gives you a working dashboard without writing a single line of JavaScript. The tradeoff is real (Streamlit's execution model creates authentication headaches later — more on that in Section 4), but for a product that must demonstrate value to its first five clients within 90 days, the tradeoff is overwhelmingly worth it.

**Enterprise sales credibility.** When a logistics CFO's nephew who "knows computers" reviews your stack, they will find: a typed Python backend with Pydantic schemas (professional), PostgreSQL (the enterprise standard for OLTP), Docker with health checks and a non-root user (production-ready), Nginx as a reverse proxy (standard), and structured logging with Sentry integration (operational maturity). Nothing in this stack will raise a red flag. More importantly, nothing in this stack will trigger the "this is a toy" objection that would kill a Flask + SQLite + bare-metal deployment. The one area where credibility is weaker is the Streamlit frontend — it looks good for demos, but an enterprise IT team will eventually notice the lack of granular auth, the absence of role-based access control, and the non-standard session model. This is acceptable for the first 10 clients. It becomes a liability at client 20.

**Technical ceiling.** The first constraint this stack will hit is Streamlit's concurrency model. Streamlit reruns the entire script on every widget interaction. With one user, this is invisible. With five concurrent users uploading 50,000-row CSVs, you will hit memory pressure and session isolation bugs. The mitigation is already partially in place: the FastAPI backend can absorb the heavy computation (profiling, persistence) while Streamlit becomes a thin presentation layer. The second constraint is PostgreSQL connection pooling — the current architecture creates a new session per request via `SessionLocal()`. At 50 tenants with concurrent requests, you will need PgBouncer or SQLAlchemy's built-in connection pooling configured explicitly. The third constraint is the single-process Uvicorn deployment: the `docker-compose.yml` runs one Uvicorn worker. At scale, you need Gunicorn with multiple Uvicorn workers, or a separate task queue (Celery/ARQ) for profiling jobs that take more than a few seconds.

None of these constraints require a rewrite. They all require configuration changes and architectural extensions within the existing stack. That is the hallmark of a well-chosen foundation.

### 1.2 The Decoupling Assessment

The split of the 990-line `app.py` monolith into FastAPI backend, Streamlit frontend, and shared service/ETL layer was appropriately timed — neither premature nor too conservative.

**What would have broken first without the split.** The immediate failure mode was testability. The monolith mixed Streamlit session state management with profiling logic, chart construction, and HTML generation in a single procedural flow. You could not unit-test the profiling engine without importing Streamlit. You could not test the HTML report generator without running a Streamlit session. The profiler's output was being mutated after construction (`report.file_path = file_name`), violating immutability and creating unpredictable state. Phase 3 correctly identified this as the critical defect and fixed it by introducing the service layer as the orchestration boundary. The `AuditService.run_audit()` method now owns the workflow: hash computation → cache check → profiling → persistence. The Streamlit frontend calls the service. The FastAPI API will call the same service. That is clean architecture.

**What the current API surface tells us about the product's future.** The `api/main.py` currently exposes two endpoints: `GET /health` and `GET /api/metrics`. The metrics endpoint is surprisingly sophisticated for a Phase 3 deliverable — it queries aggregate statistics across audits, computes averages, and returns top finding categories. This is not a placeholder; this is the skeleton of an operational dashboard API. The fact that the response model (`MetricsResponse`) is a Pydantic `BaseModel` with typed fields means the API contract is already machine-readable. When you build the client-facing dashboard or a partner integration, the API schema is ready. The dependency injection pattern (`get_db()` as a generator with `Depends`) is the FastAPI standard and will extend naturally to authentication middleware.

What is missing from the API is the core product endpoint: `POST /api/audits` (upload a file, return a profiling report). This endpoint does not yet exist because the profiling flow currently runs synchronously inside the Streamlit process. Moving it to the API is a Phase 4/5 deliverable, and the service layer abstraction makes that migration straightforward.

### 1.3 The ETL Engine — Code Quality Verdict

The profiling engine is the most commercially important component in the system, and based on the architecture description and the HTML report output, it is genuinely impressive for a solo founder's work. Let me be specific about what is good, what is adequate, and what a data scientist would flag.

**What is good.** The column type inference system uses a priority-ordered classifier (date → identifier → financial → numeric → entity/categorical) with a name-guard that prevents invoice number columns from being misclassified as financial. This is a non-obvious design decision that most junior data engineers get wrong — they classify any column with numbers as numeric, which causes invoice numbers like `FAC-2024-0001` to be treated as outliers in financial analysis. The name-guard pattern (checking for substrings like "factura", "id", "codigo") is heuristic but correct for the target data domain. The entity deduplication using `rapidfuzz` with legal suffix normalisation (`_normalize_entity()` strips S.L., S.A., etc.) is domain-specific and valuable — this is the kind of Spanish-market knowledge that a generic profiling tool would miss entirely.

**The IQR-based anomaly detection.** For the target data (logistics invoices, 60–5,000 rows), IQR is the appropriate statistical method. It is distribution-free (does not assume normality), computationally trivial (O(n log n) for the sort), and produces interpretable results. The alternative — z-score based detection — assumes a Gaussian distribution that financial data almost never follows (invoice amounts are typically right-skewed with fat tails). A data scientist would say: "IQR is the correct first choice. For datasets above 10,000 rows, consider adding Isolation Forest as a complementary detector for multivariate anomalies that IQR misses (e.g., an invoice that is normal in amount but anomalous in the combination of route + weight + cost)." That is a Phase 7+ enhancement, not a current deficiency.

**The health score penalty model.** The score of 82/100 on the test dataset is commercially brilliant. Here is why: a naive profiler that simply checks completeness would have returned 98 or 99, which tells the client nothing and creates no urgency. The penalty model (base structural score minus 2 points per financial anomaly and 2 points per entity cluster) produces a number that is high enough to avoid insulting the client's data practices but low enough to signal genuine room for improvement. When a logistics CFO sees 82/100, they think: "We're doing okay, but there's clearly something to fix." That is the precise emotional state the Challenger Sale requires. If you showed them 52/100, they would feel attacked and disengage. If you showed them 97/100, they would see no reason to buy.

Could you explain the 82 to a CFO without pushback? Yes, if the explanation is structured correctly: "Your data completeness is excellent — 98 out of 100. Your uniqueness is perfect — no duplicates. But we found six pricing inconsistencies and three probable duplicate suppliers, each of which carries a financial impact. Those findings reduce the score from a structural 97 to an operational 82. The gap between 82 and 97 is where the €122,000 in estimated impact lives." That explanation is defensible, quantified, and maps directly to the findings in the report.

**What a data scientist would flag.** Three things. First, the financial impact estimation methodology is not documented in the report itself. The €97,715 finding for pricing inconsistency across 38 rows is plausible, but the calculation path from "4 entities show >10% price variation" to "€97,715" is not transparent. A sophisticated client will ask "how did you compute that number?" and the report does not answer. The profiler should include a tooltip or footnote explaining the estimation formula. Second, the revenue concentration risk finding (€4,814 for "top entity represents 41.7% of total") is categorized as "Low confidence," which is honest but may confuse a non-technical reader who does not understand that concentration risk is structural rather than anomalous. Third, the 88% completeness on `peso_kg` is reported but not connected to a financial impact — missing weight data in logistics invoices could indicate unbilled weight-based surcharges, which is a finding worth surfacing.

### 1.4 The Frozen Dataclass Architecture

The `ProfilingReport` as a frozen dataclass is a deliberately conservative architectural choice, and it is the right one.

**What it makes easy.** Immutability eliminates an entire class of bugs: no component can silently mutate the report after construction. This means the report that is persisted to the database is guaranteed to be identical to the report that was generated by the profiler. It means the report can be safely passed between threads or processes without defensive copying. It means serialisation to JSON is deterministic — the same input always produces the same output. For a product whose credibility depends on the accuracy of its findings, immutability is not a luxury; it is a commercial requirement.

**What it makes hard.** Schema evolution. When you add a new field to `ProfilingReport` (and you will — client requests will drive this within the first three months), you face a migration challenge on two fronts. First, the Alembic migration must add the corresponding column to the database. Second, existing serialised reports in the database will not have the new field. You need a default value strategy: either the field is `Optional` with a `None` default (acceptable for additive fields), or you write a data migration that backfills existing records. The frozen dataclass makes in-place mutation impossible by design, so you cannot "patch" old reports — you must either accept the missing field or re-run the profiler on the original file.

**How it interacts with Alembic.** The current design stores the `ProfilingReport` as structured relational data across multiple tables (`audits`, `audit_findings`, `column_profiles`, `anomaly_analyses`). This is correct — it avoids the antipattern of storing the report as a JSON blob, which would make querying across audits impossible. But it creates a tight coupling between the dataclass schema and the database schema. Every field addition requires a coordinated change: dataclass → Alembic migration → repository serialisation → repository deserialisation. The mitigation is to version the report schema explicitly (add a `schema_version: int` field to the dataclass and the `audits` table) so that the deserialisation layer can handle both v1 and v2 reports during the transition period.

### 1.5 Infrastructure Maturity Score

**Overall: 6.5 out of 10** relative to a typical Series A B2B SaaS.

Components above the curve:
- **Docker configuration (8/10).** Multi-stage build, non-root user, health checks, `.venv` isolation, `uv` for fast dependency resolution. This is production-grade container hygiene. The only missing piece is a `.dockerignore` file (which should exclude `.git/`, `data/`, `tests/`, `*.pyc`, and IDE artifacts to reduce build context size).
- **Structured logging (8/10).** `structlog` with environment-dependent output, Sentry integration with conditional initialisation, and six named audit events. This is better than most Series A companies, which typically have `print()` statements in production.
- **Test discipline (7/10).** 80%+ coverage with integration tests against real SQLite, contract tests for the report schema, and Streamlit smoke tests. The test pyramid is correctly shaped: many unit tests, fewer integration tests, minimal UI tests.
- **CI/CD (7/10).** GitHub Actions with ruff, mypy strict, and pytest. The two known defects (SQLite hack and removed pip-audit) lower the score, but the pipeline exists and is green.

Components below the curve:
- **Authentication and authorisation (1/10).** Non-existent. Any authenticated SaaS requires this before production.
- **Secret management (3/10).** `.env` file with `env_file` in Docker Compose. Acceptable for development; inadequate for production. Secrets should be injected via environment variables from a secrets manager (Vault, AWS SSM, or even Docker Swarm secrets), not stored in a file that could be committed to version control.
- **Backup and recovery (2/10).** PostgreSQL data lives in a Docker volume (`postgres_data`). There is no backup strategy, no point-in-time recovery configuration, and no documented restoration procedure. A volume deletion or host failure means total data loss.
- **Monitoring and alerting (3/10).** The `/api/metrics` endpoint exists but there is no alerting system. Nobody is notified when an audit fails, when the database is unreachable, or when the disk fills up. Sentry handles application errors, but infrastructure failures are invisible.
- **Rate limiting and abuse protection (1/10).** No rate limiting on any endpoint. No file size limits enforced at the API level. A malicious or accidentally large upload could consume all available memory.

---

## 2. The Five Scaled Technical Risks

These are ranked by (probability × severity) as requested.

### Risk 1: Tenant Data Leakage (Probability: High if multi-tenancy is implemented incorrectly | Severity: Catastrophic)

**Risk score: 9/10.** This is the company-killer. If Client A can see Client B's audit findings — even once, even accidentally — the product is dead. The current architecture has no tenant isolation whatsoever. Every query hits a global database with no `WHERE tenant_id = ?` filter. The `GET /api/metrics` endpoint returns aggregate metrics across all clients. When multi-tenancy is added, every single database query must be scoped to the authenticated tenant, and there must be no code path that bypasses this filter.

**Failure mode:** A developer forgets to add the tenant filter to a new query. A client sees another client's data in the metrics response. The client contacts their lawyer. GDPR Article 33 requires notification within 72 hours. The product's reputation is destroyed before it has ten clients.

**Mitigation:** Implement tenant isolation at the repository layer, not the endpoint layer. Every repository method must accept a `tenant_id` parameter. Create a SQLAlchemy event listener or a custom `Session` subclass that automatically appends `WHERE tenant_id = :tid` to every SELECT query. Write a dedicated integration test that creates two tenants, inserts data for each, and asserts that querying as Tenant A never returns Tenant B's data. Run this test on every CI build. See Section 4.3 for the complete implementation design.

### Risk 2: Profiling Engine Timeout on Large Files (Probability: High | Severity: High)

**Risk score: 7/10.** The profiling engine runs synchronously. On a 60-row test dataset, this takes 0.1 seconds. On a 50,000-row real-world logistics dataset with 200+ unique entities requiring fuzzy matching, the `rapidfuzz` entity deduplication step alone could take 30–120 seconds (fuzzy matching is O(n²) on the number of unique entities). If this runs inside a Streamlit request or a synchronous FastAPI endpoint, the user sees a spinner that never stops, the connection times out, and the audit is lost.

**Failure mode:** The first real client uploads their actual operational data (12 months of invoices, 15,000 rows). The profiler runs for 90 seconds. The Nginx reverse proxy (default timeout: 60 seconds) kills the connection. The client sees an error. The demo fails. The relationship is burned.

**Mitigation:** Move profiling to an asynchronous task. The immediate fix (achievable in a weekend): add `proxy_read_timeout 300s;` to the Nginx config for the Streamlit upstream. The proper fix (Phase 4/5): introduce a task queue. The Streamlit frontend submits the file, receives a task ID, and polls for completion. The profiling runs in a background worker. The simplest implementation: a FastAPI background task with `BackgroundTasks` for files under 5,000 rows, and an ARQ (async Redis queue) worker for larger files. Redis is a single additional service in docker-compose.

### Risk 3: No Backup or Disaster Recovery (Probability: Medium | Severity: Catastrophic)

**Risk score: 7/10.** The PostgreSQL data volume is the only copy of all client audit data. There is no backup schedule, no point-in-time recovery, no off-host replication. A single `docker volume rm postgres_data` command — or a host disk failure — destroys every audit ever run.

**Failure mode:** The VPS host experiences a disk failure. All client data is lost. Clients who relied on historical audit comparisons (the longitudinal value proposition) lose trust permanently.

**Mitigation:** Before the first real client, implement a daily `pg_dump` to an off-host location. The simplest approach: a cron job on the host that runs `docker exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > /backups/yellowbird_$(date +%Y%m%d).sql.gz` and syncs to an S3-compatible object store (Backblaze B2 at €0.005/GB/month). Enable PostgreSQL WAL archiving for point-in-time recovery. Document the restoration procedure and test it once before going live.

### Risk 4: GDPR Non-Compliance on Data Retention and Deletion (Probability: High | Severity: High)

**Risk score: 7/10.** The product processes commercially sensitive operational data from EU businesses. GDPR applies from Day 1. There is currently no data deletion mechanism, no retention policy, no data processing agreement (DPA), and no documented legal basis for processing. Under GDPR Article 17, a client can request deletion of all their data, and the controller must comply without undue delay. The current system has no way to identify which data belongs to which client (no tenant isolation), let alone delete it comprehensively.

**Failure mode:** A pilot client decides not to continue and requests deletion of their data. You cannot prove that the data has been deleted because there is no audit trail of the deletion itself. The client's data controller (often their accountant or legal advisor) escalates this to the AEPD (Spain's data protection authority). Even without a fine, the reputational damage in the tight-knit Spanish SME market is devastating.

**Mitigation:** See Section 4.6 for the complete GDPR deletion implementation. The minimum viable compliance posture before the first client: a signed Data Processing Agreement (DPA) that specifies the legal basis (legitimate interest or contract performance), the categories of data processed, the retention period, and the deletion procedure. You must have a `DELETE /api/clients/{tenant_id}/data` endpoint that cascade-deletes all audit data for a tenant and logs the deletion event to an immutable audit log.

### Risk 5: Single Point of Failure on the Solo Founder (Probability: Certain | Severity: High)

**Risk score: 6/10.** This is not a technical risk in the traditional sense, but it is the highest-probability risk on the register. If the founder is unavailable for two weeks (illness, the Gartner internship, travel to Tsinghua), client audits stop, bugs go unfixed, and sales conversations go cold. The product has no self-service mode — every audit requires the founder to be in the loop.

**Failure mode:** During the Gartner internship (June 26 – August 28), a client reports a bug in the profiler that produces incorrect financial impact numbers. The founder cannot dedicate meaningful time to debugging. The client loses confidence. The case study is compromised.

**Mitigation:** Before June 26, the product must be capable of running unattended. This means: automated deployment (CI/CD auto-deploys on merge to main), automated alerting (Sentry notifications for application errors, Uptime Robot or equivalent for availability monitoring), and a documented runbook that Lucas can follow for common issues (restart the Docker stack, check the logs, escalate to the founder). The profiling engine must be robust enough that it does not produce incorrect results on well-formed input — which means the contract tests and integration tests are not optional, they are the insurance policy against this exact risk.

---

## 3. Phase 4 Implementation Plan: Security & Multi-Tenancy

### 3.1 Auth Provider Selection — The Definitive Recommendation

**Recommendation: Supabase Auth.**

Here is the evaluation of each candidate against the specific stack:

**Auth0.** The industry standard for B2B SaaS authentication. Excellent documentation, mature SDKs, robust RBAC. However: the free tier is limited to 7,500 monthly active users (more than enough), but the integration with Streamlit is non-trivial. Auth0's standard flow requires a browser redirect to an Auth0-hosted login page, which Streamlit cannot control directly without `st.components.v1.html` hacks. The Python SDK exists but is designed for Flask/Django, not Streamlit. The FastAPI integration is clean (well-documented JWT verification via JWKS). Verdict: technically correct but operationally painful for a solo founder integrating with Streamlit. The complexity is not justified at this stage.

**Supabase Auth.** Built on GoTrue, the same auth server used by Netlify. Provides email/password auth, magic links, OAuth providers, and JWT issuance out of the box. The key advantage: Supabase provides a hosted auth service with a REST API that any HTTP client can call — including Streamlit via `requests`. The JWT contains a `sub` (user ID) that maps directly to a `tenant_id`. The JWKS endpoint is public and cacheable, so FastAPI can verify tokens without a round-trip to Supabase on every request. The free tier includes 50,000 monthly active users. The Supabase Python SDK (`supabase-py`) is thin and does not impose framework-specific patterns. Verdict: the best fit for this specific stack. Clean HTTP-based auth flow, standard JWTs, no framework coupling.

**Clerk.** Excellent developer experience, beautiful prebuilt UI components. However: the UI components are React-only. The Python SDK is nascent. Integrating Clerk with Streamlit requires either embedding React components (which Streamlit does not support natively) or using the raw API, which eliminates Clerk's primary advantage. Verdict: wrong tool for this stack.

**`streamlit-authenticator`.** A community library that stores usernames and hashed passwords in a YAML file. No JWT issuance, no token-based auth for the FastAPI backend, no tenant isolation, no password reset flow, no OAuth. This is a toy for internal dashboards, not a foundation for multi-tenant SaaS. Verdict: eliminated.

**The call: Supabase Auth.** Use Supabase's hosted auth service for user registration, login, and JWT issuance. Use the JWT `sub` claim as the `user_id`, and map users to tenants via a `user_tenants` table in your PostgreSQL database. Use Supabase's JWKS endpoint for stateless JWT verification in FastAPI.

### 3.2 The Token Flow Architecture — Step by Step

Here is the complete flow from browser open to authenticated database write.

**Step 1: User opens the Streamlit dashboard.**
Component: Streamlit (`app/main.py`).
The `AppState` class checks `st.session_state` for an `access_token` key. If absent, the user is not authenticated. The sidebar renders a login form (email + password fields, a "Sign In" button, and a "Sign Up" link).
Failure mode: If `st.session_state` is lost (Streamlit process restart), the user must re-authenticate. This is acceptable — Streamlit sessions are ephemeral by design.

**Step 2: User submits login credentials.**
Component: Streamlit → Supabase Auth API (HTTPS).
The login button's callback calls `supabase.auth.sign_in_with_password(email, password)` via the Supabase Python SDK. Supabase returns a response containing `access_token` (JWT, short-lived, 1 hour default), `refresh_token` (long-lived, 30 days), and `user` (containing `id`, `email`, `user_metadata`).
Data passed: email, password (over HTTPS to Supabase).
Failure modes: Invalid credentials → Supabase returns 400 → display "Invalid email or password" in `st.error()`. Network failure → timeout → display "Authentication service unavailable, please try again."
Security boundary: Credentials never touch your FastAPI backend. They go directly to Supabase over HTTPS.

**Step 3: Tokens are stored in session state.**
Component: Streamlit (`app/state.py`).
The `AppState` class stores the `access_token`, `refresh_token`, and `user_id` in `st.session_state`. New accessor methods: `AppState.is_authenticated() → bool`, `AppState.get_access_token() → str | None`, `AppState.get_user_id() → str | None`.
Security note: `st.session_state` is server-side (stored in the Streamlit server's memory, not in the browser). The tokens are never sent to the client browser.

**Step 4: Authenticated user uploads a file for profiling.**
Component: Streamlit → FastAPI (`POST /api/audits`).
The Streamlit frontend calls the FastAPI backend via `httpx` (or `requests`), passing the file as multipart form data and the JWT in the `Authorization: Bearer <token>` header.
Data passed: file bytes, JWT.
Security boundary: The FastAPI backend, not Streamlit, performs the audit. Streamlit is a presentation layer only.

**Step 5: FastAPI verifies the JWT.**
Component: FastAPI middleware (`api/dependencies/auth.py`).
A FastAPI dependency (`get_current_user`) extracts the `Authorization` header, decodes the JWT using the cached JWKS public keys from Supabase, verifies the signature, checks the expiration, and extracts the `sub` claim (user ID). The dependency looks up the user's `tenant_id` from the `user_tenants` table.
Failure modes: Expired token → 401 Unauthorized → Streamlit catches this and triggers a token refresh (Step 6). Invalid signature → 401 → log a security warning. Missing header → 401 → redirect to login.
Security boundary: Every protected endpoint depends on `get_current_user`, which returns a `CurrentUser` dataclass. No endpoint can access data without a verified tenant context.

**Step 6: Token refresh.**
Component: Streamlit → Supabase Auth API.
When the FastAPI backend returns 401, the Streamlit frontend calls `supabase.auth.refresh_session(refresh_token)` to obtain a new access token. If the refresh token is also expired (>30 days since login), the user is redirected to the login form.
Security boundary: The refresh token is stored server-side in `st.session_state` and never exposed to the browser.

**Step 7: Profiling result is written to the database with tenant isolation.**
Component: FastAPI → AuditService → AuditRepository → PostgreSQL.
The `AuditService.run_audit()` method receives the `tenant_id` from the `CurrentUser` dependency. It passes the `tenant_id` to the repository's `save_audit_report()` method, which writes the `Audit` record with the `tenant_id` column populated. The `AuditFinding`, `ColumnProfile`, and `AnomalyAnalysis` records inherit the tenant context through their foreign key to the `Audit` table.
Security boundary: Row-level tenant isolation is enforced at the repository layer. Every `SELECT` query includes `WHERE audit.tenant_id = :tid`.

### 3.3 Multi-Tenancy Database Design

**Migration strategy.** The existing tables (`clients`, `audits`, `audit_findings`, `column_profiles`, `anomaly_analyses`) must gain tenant isolation without breaking the existing pilot data.

**Alembic migration — `add_tenant_isolation`:**

The `tenants` table is new. It stores the tenant identity.

```
tenants
├── id: UUID (PK, default uuid4)
├── name: str (company name)
├── supabase_org_id: str | None (for future Supabase org mapping)
├── created_at: datetime (server default now())
└── is_active: bool (default True)
```

The `user_tenants` table maps Supabase users to tenants (many-to-many, supporting future multi-tenant users like consultants who audit multiple clients):

```
user_tenants
├── id: UUID (PK)
├── user_id: str (Supabase user ID from JWT sub claim)
├── tenant_id: UUID (FK → tenants.id)
├── role: str (enum: 'owner', 'viewer', 'admin')
└── created_at: datetime
```

For each existing table, the `tenant_id` placement:

- **`audits`:** Add `tenant_id: UUID (FK → tenants.id, NOT NULL)` directly. This is the primary tenant anchor. Index: `CREATE INDEX ix_audits_tenant_id ON audits (tenant_id)`. Composite index for common queries: `CREATE INDEX ix_audits_tenant_hash ON audits (tenant_id, file_hash)`.
- **`audit_findings`:** `tenant_id` is *not* added here. It is derived through the join to `audits`. Adding it would be denormalisation that creates an update anomaly risk (if a finding's tenant_id somehow diverges from its parent audit's tenant_id, which should be impossible but becomes possible with denormalisation). The query path is: `audit_findings JOIN audits ON audit_findings.audit_id = audits.id WHERE audits.tenant_id = :tid`.
- **`column_profiles`:** Same as `audit_findings` — derived through join to `audits`. No direct `tenant_id`.
- **`anomaly_analyses`:** Same — derived through join.
- **`clients`:** This table should be renamed to `tenants` or merged into it. If the current `clients` table stores client metadata separately from tenant identity, add `tenant_id: UUID (FK → tenants.id)` and index it. However, re-reading the schema description, `clients` likely *is* the tenant anchor — in which case, rename it to `tenants` and add the Supabase mapping fields.

**Migration that preserves pilot data.** The migration must:
1. Create the `tenants` table.
2. Create a "default" tenant record for the existing pilot client.
3. Add `tenant_id` to `audits` as a nullable column.
4. Update all existing `audits` rows to set `tenant_id` to the default tenant's ID.
5. Alter `tenant_id` to NOT NULL.
6. Add the indexes.
7. Create the `user_tenants` table.

This is a safe, reversible migration. The downgrade drops the new columns and tables.

**Repository method signatures enforcing tenant isolation:**

```python
class AuditRepository:
    def get_audit_by_hash(
        self, *, file_hash: str, tenant_id: uuid.UUID, session: Session
    ) -> Audit | None:
        """Return cached audit for this tenant, or None."""
        ...

    def save_audit_report(
        self, *, report: ProfilingReport, tenant_id: uuid.UUID,
        file_hash: str, file_name: str, session: Session
    ) -> Audit:
        """Persist a profiling report scoped to a tenant."""
        ...

    def list_audits(
        self, *, tenant_id: uuid.UUID, session: Session,
        limit: int = 50, offset: int = 0
    ) -> list[Audit]:
        """Return audits for a single tenant, paginated."""
        ...

    def delete_tenant_data(
        self, *, tenant_id: uuid.UUID, session: Session
    ) -> int:
        """Cascade-delete all audit data for a tenant. Returns count of deleted audits."""
        ...
```

The critical design constraint: there is no repository method that queries across tenants except for a super-admin metrics method:

```python
    def get_global_metrics(
        self, *, session: Session, require_admin: bool = True
    ) -> MetricsResponse:
        """Aggregate metrics across all tenants. Admin-only."""
        ...
```

### 3.4 FastAPI Security Middleware Design

**The JWT verification dependency:**

```python
# api/dependencies/auth.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient

from src.common.config.settings import get_settings

_settings = get_settings()
_jwks_client = PyJWKClient(
    uri=f"{_settings.supabase_url}/auth/v1/.well-known/jwks.json",
    cache_keys=True,
    lifespan=3600,  # Cache JWKS for 1 hour
)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str          # Supabase user ID (JWT 'sub' claim)
    tenant_id: str        # Resolved from user_tenants table
    email: str            # From JWT claims
    role: str             # 'owner' | 'viewer' | 'admin' — from user_tenants
    is_super_admin: bool  # For global metrics access


def get_current_user(request: Request) -> CurrentUser:
    """FastAPI dependency: verify JWT and resolve tenant context."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ", 1)[1]

    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{_settings.supabase_url}/auth/v1",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    user_id = payload.get("sub")
    email = payload.get("email", "")

    # Resolve tenant from database (cached per-request)
    # This requires a DB lookup — see tenant resolution below
    tenant_id, role, is_super_admin = _resolve_tenant(user_id, request)

    return CurrentUser(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
        role=role,
        is_super_admin=is_super_admin,
    )


# Type alias for dependency injection
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
```

**The `/api/metrics` endpoint differentiation:**

```python
@app.get("/api/metrics", response_model=MetricsResponse)
def get_metrics(
    user: AuthenticatedUser,
    session: Annotated[Session, Depends(get_db)],
) -> MetricsResponse:
    if user.is_super_admin:
        return audit_repo.get_global_metrics(session=session)
    return audit_repo.get_tenant_metrics(
        tenant_id=user.tenant_id, session=session
    )
```

**How Streamlit passes the token to FastAPI:**

```python
# app/api_client.py
import httpx
from app.state import AppState

class APIClient:
    def __init__(self, state: AppState) -> None:
        self._base_url = "http://api:8000"  # Docker service name
        self._state = state

    def _headers(self) -> dict[str, str]:
        token = self._state.get_access_token()
        if not token:
            raise AuthenticationRequired()
        return {"Authorization": f"Bearer {token}"}

    def upload_audit(self, file_bytes: bytes, file_name: str) -> dict:
        response = httpx.post(
            f"{self._base_url}/api/audits",
            headers=self._headers(),
            files={"file": (file_name, file_bytes)},
            timeout=300.0,  # 5 minutes for large files
        )
        if response.status_code == 401:
            # Trigger token refresh in the caller
            raise TokenExpired()
        response.raise_for_status()
        return response.json()
```

### 3.5 The Streamlit Auth Integration Challenge

**Where the JWT is stored between reruns.** The JWT access token and refresh token are stored in `st.session_state["_auth_tokens"]`. This is the correct location because `st.session_state` persists across Streamlit reruns within a single browser session and is stored server-side (not in the browser). It is not stored in a cookie (which would be accessible to JavaScript and create an XSS vector), not in a URL parameter (which would leak the token in browser history and server logs), and not in `st.cache_data` (which would persist across sessions and create a token reuse vulnerability).

**How token refresh is handled.** The `AppState` class wraps token access with an expiry check:

```python
# app/state.py (additions)
import time
import jwt as pyjwt  # For decoding without verification (just to read exp)

class AppState:
    def get_access_token(self) -> str | None:
        tokens = st.session_state.get("_auth_tokens")
        if not tokens:
            return None

        # Check if the access token is within 5 minutes of expiry
        try:
            payload = pyjwt.decode(
                tokens["access_token"],
                options={"verify_signature": False}
            )
            if payload.get("exp", 0) - time.time() < 300:
                # Token expires in <5 minutes — refresh proactively
                self._refresh_tokens()
        except Exception:
            self._refresh_tokens()

        return st.session_state.get("_auth_tokens", {}).get("access_token")

    def _refresh_tokens(self) -> None:
        tokens = st.session_state.get("_auth_tokens")
        if not tokens or "refresh_token" not in tokens:
            self._clear_auth()
            return
        try:
            response = supabase_client.auth.refresh_session(
                tokens["refresh_token"]
            )
            st.session_state["_auth_tokens"] = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        except Exception:
            self._clear_auth()  # Force re-login

    def _clear_auth(self) -> None:
        st.session_state.pop("_auth_tokens", None)
        st.session_state.pop("_user_id", None)
```

**Session state keys:**
- `_auth_tokens`: `{"access_token": str, "refresh_token": str}`
- `_user_id`: `str` (Supabase user ID)
- `_tenant_id`: `str` (resolved from first API call)
- `_user_email`: `str`

The `AppState` accessor methods: `is_authenticated()`, `get_access_token()`, `get_user_id()`, `get_tenant_id()`, `get_user_email()`, `login(email, password)`, `logout()`, `_refresh_tokens()`, `_clear_auth()`.

### 3.6 GDPR Compliance Implementation

**The `DELETE /api/tenants/{tenant_id}/data` endpoint:**

```python
@app.delete("/api/tenants/{tenant_id}/data")
def delete_tenant_data(
    tenant_id: str,
    user: AuthenticatedUser,
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    # Only tenant owners or super-admins can delete
    if user.tenant_id != tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Log the deletion request BEFORE deleting (immutable audit trail)
    deletion_log = DeletionAuditLog(
        tenant_id=tenant_id,
        requested_by=user.user_id,
        requested_at=datetime.now(UTC),
        status="in_progress",
    )
    session.add(deletion_log)
    session.flush()  # Get the log ID

    try:
        # Delete in dependency order (children first)
        # 1. anomaly_analyses (FK → audit_findings)
        # 2. column_profiles (FK → audits)
        # 3. audit_findings (FK → audits)
        # 4. audits (FK → tenants)
        count = audit_repo.delete_tenant_data(
            tenant_id=tenant_id, session=session
        )
        deletion_log.status = "completed"
        deletion_log.records_deleted = count
        deletion_log.completed_at = datetime.now(UTC)
        session.commit()
        return {"status": "completed", "records_deleted": count}
    except Exception as exc:
        deletion_log.status = "failed"
        deletion_log.error_message = str(exc)
        session.commit()  # Commit the failure log
        raise HTTPException(status_code=500, detail="Deletion failed") from exc
```

**Handling partial deletion (network failure mid-transaction).** The entire deletion runs within a single database transaction. If the process crashes mid-deletion, the transaction is rolled back automatically by PostgreSQL. The `deletion_log` record with status `"in_progress"` remains, signaling that a retry is needed. A background health check (scheduled task or startup hook) should scan for `in_progress` deletion logs older than 5 minutes and re-execute them.

**The `data_retention_days` scheduled job.** This should be a FastAPI background task triggered by a lightweight cron-like scheduler (not a separate container, not a system cron — both create operational complexity for a solo founder). The simplest implementation: use `apscheduler` with a daily interval, running inside the API process.

```python
# api/tasks/retention.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("cron", hour=3, minute=0)  # Run at 3 AM UTC
async def enforce_retention_policy():
    """Delete audit data older than the configured retention period."""
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.data_retention_days)
    with SessionLocal() as session:
        expired_audits = session.execute(
            select(Audit).where(Audit.created_at < cutoff)
        ).scalars().all()
        for audit in expired_audits:
            # Log each deletion
            log = DeletionAuditLog(
                tenant_id=audit.tenant_id,
                requested_by="system:retention_policy",
                ...
            )
            session.add(log)
            # Cascade delete
            session.delete(audit)
        session.commit()
```

The scheduler is started in the FastAPI `lifespan` event:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()
```

**The audit trail paradox.** The `DeletionAuditLog` table stores: `tenant_id`, `requested_by`, `requested_at`, `completed_at`, `status`, `records_deleted`, `error_message`. It does *not* store any of the deleted data content. It stores only the fact that a deletion occurred, when, by whom, and how many records were affected. This satisfies the GDPR accountability requirement (Article 5(2)) without retaining the personal data that was deleted. The `DeletionAuditLog` table itself has its own retention policy (e.g., 7 years for legal compliance), defined in the DPA.

---

## 4. CI Technical Debt Fixes

### The SQLite Hack in CI

**Risk profile: Correctness concern.** The CI pipeline overrides `DATABASE_URL` to point to a flat SQLite file instead of PostgreSQL. This means the integration tests run against a different database engine than production. SQLite has different type affinity rules, different constraint enforcement (e.g., SQLite does not enforce foreign key constraints by default — you must `PRAGMA foreign_keys = ON`), and different transaction isolation semantics. A query that works in SQLite CI may silently fail in PostgreSQL production.

**The exact fix:**

Add a PostgreSQL service to the GitHub Actions workflow:

```yaml
# .github/workflows/ci.yml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: yellowbird_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

env:
  DATABASE_URL: postgresql://test:test@localhost:5432/yellowbird_test
```

Then update the test setup to run Alembic migrations against this database before executing tests. The `conftest.py` fixture should use the real PostgreSQL URL, not an in-memory SQLite override.

### The Removed pip-audit Step

**Risk profile: Security concern.** `pip-audit` scans installed packages against the OSV vulnerability database. Removing it means known-vulnerable dependencies can enter production undetected. The crash was caused by `pip-audit` failing to resolve the private `project-nexus-core` package, which is not published to PyPI.

**The exact fix:**

Add the `--skip-editable` flag to exclude the local package from the audit:

```yaml
# In the CI workflow
- name: Audit dependencies
  run: pip-audit --skip-editable --desc
```

If `--skip-editable` is insufficient (some versions of `pip-audit` require the package to be installed), use `--requirement requirements.txt` mode instead, which audits only the explicitly declared dependencies:

```yaml
- name: Audit dependencies
  run: pip-audit -r requirements.txt
```

Generate `requirements.txt` from `pyproject.toml` as a CI step if it does not exist:

```yaml
- name: Export requirements
  run: uv pip compile pyproject.toml -o requirements.txt
- name: Audit dependencies
  run: pip-audit -r requirements.txt
```

---

## 5. Where Machine Learning Can Realistically Be Introduced

This section is written for a founder who has completed ML and deep learning coursework and will have access to Tsinghua faculty. It distinguishes between what ML can do for this specific product, what it cannot, and what should remain rule-based.

### What Should Be ML-ified

**Entity resolution.** The current `rapidfuzz` approach compares entity name strings using edit distance after legal suffix normalisation. This works well for simple variations ("Transp. Garcia SL" vs "Transportes García, S.L.") but fails for semantic equivalences ("ACME Logistics Barcelona" vs "ACME BCN Transportes") and for entities that share similar names but are different companies ("Garcia Transportes Tarragona" vs "Garcia Logística Girona"). A trained embedding model — fine-tuned on Spanish company names — could map entities to a vector space where semantic similarity is meaningful. The specific approach: fine-tune a sentence-transformer model (e.g., `all-MiniLM-L6-v2`) on a dataset of Spanish company name pairs labeled as same/different. The training data can be bootstrapped from SABI (which maps company names to CIF numbers, providing ground truth for whether two name variants refer to the same legal entity). The dataset size needed: approximately 5,000–10,000 labeled pairs. The realistic uplift: entity clustering accuracy from ~85% (current, estimated) to ~95%.

**Anomaly classification.** The current engine detects anomalies (via IQR) and categorises them using hardcoded rules (pricing inconsistency, concentration risk, negative margin, etc.). An ML classifier could learn to categorise anomalies based on features beyond what the rules capture: column relationships (an invoice amount that is normal individually but anomalous given the route distance and weight), temporal patterns (a supplier whose prices spike in Q4 every year — normal seasonality vs. genuine anomaly), and cross-entity patterns (all invoices from a specific supplier are 15% above the median for the same route — potential overcharging). The specific model: a gradient boosted classifier (XGBoost or LightGBM) trained on labeled anomaly data. The training data source: the first 50 client audits, where each detected anomaly is manually labeled by the founder or client as "true finding" or "false positive." At 50 audits × ~10 findings each = 500 labeled examples, which is borderline for a useful classifier. At 200 audits, the model becomes meaningfully better than rules.

**Column type inference.** The current priority-ordered heuristic is good but brittle — it depends on column name substrings in Spanish. An ML classifier trained on column metadata (name, sample values, value distribution statistics) could generalise to unseen column names and to data in other languages. This becomes important when the product expands beyond Spain.

### What Should NOT Be ML-ified

**The health score calculation.** The penalty model is simple, interpretable, and commercially defensible. Replacing it with an ML-predicted score would make it a black box. When a CFO asks "why is my score 82?", you need to say "because of these 6 specific findings, each of which reduces the score by 2 points." You cannot say "because the model predicted 82." Interpretability is a commercial requirement, not a nice-to-have.

**The financial impact estimation.** The euro-denominated impact for each finding must be deterministic and auditable. If you tell a CFO "you're losing €122,000," that number must be traceable to a specific calculation on their specific data. An ML model that predicts "this anomaly is worth approximately €97,000" is not auditable. Keep the impact estimation rule-based, even if the anomaly detection becomes ML-powered.

**IQR-based outlier detection.** IQR is transparent, fast, and well-understood by anyone who has taken a statistics course. Replacing it with Isolation Forest or an autoencoder would add complexity without meaningful accuracy improvement for univariate outlier detection on datasets under 50,000 rows. Add ML-based multivariate anomaly detection as a *complement* to IQR, not a replacement.

### Realistic Timeline

**Months 1–3 (Tsinghua, September–November 2026):** Research phase. Assemble the Spanish company name dataset from SABI. Prototype the entity resolution embedding model. Benchmark against the current `rapidfuzz` approach on the same test set. If the improvement is not measurable, abandon the approach. Timeline: 3 months is sufficient for a focused prototype, given faculty access and the founder's ML coursework.

**Months 4–6 (December 2026–February 2027):** If the entity model shows improvement, integrate it into the profiling engine as an optional enhancement (feature flag, not a replacement for the rule-based approach). Begin collecting labeled anomaly data from pilot clients for the anomaly classifier.

**Month 6+ (March 2027+):** With 200+ audits of labeled data, train the anomaly classifier. A/B test against the rule-based categorisation. Deploy if and only if precision improves (false positive rate decreases). This is the point where ML becomes a genuine moat — the model improves with every client, which means a competitor starting today can never catch up because they do not have the labeled data.

### Prioritised Engineering Backlog — Next 12 Months

1. **March 2026:** Production deployment on a single VPS. Domain, SSL, CI/CD auto-deploy. Single-tenant. First pilot client live.
2. **April 2026:** PDF report generation. Automated email delivery. This is the artefact that travels through the client's organisation and generates referrals.
3. **May 2026:** Supabase Auth integration. Multi-tenancy database migration. FastAPI security middleware. GDPR deletion endpoint.
4. **June 2026:** Stabilisation sprint. Bug fixes from pilot clients. Profiler hardening for edge cases in real-world data. Handover documentation for the Gartner period.
5. **July–August 2026 (Gartner period):** Maintenance mode. Automated monitoring. Lucas handles client communication. No new features.
6. **September–November 2026 (Tsinghua):** ML entity resolution research. Spanish company name embedding model prototype.
7. **December 2026–February 2027:** ML entity resolution integration. Anomaly classifier data collection. Self-service onboarding flow (reduce founder dependency).
8. **March 2027:** Anomaly classifier training and A/B test. Expansion planning beyond Catalonia.
