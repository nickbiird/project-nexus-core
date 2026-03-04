# PROJECT NEXUS — Technical Initialization Plan (Day 1)

**Classification:** Internal Engineering Document
**Date:** 2026-03-03
**Author:** Technical Co-Founder / CTO
**Status:** EXECUTE IMMEDIATELY

---

## 0. Preamble: What This Document Is

This is the exact technical execution plan for Day 1 of the 14-Day Sprint. It is not advisory. Every command, every file path, every dependency version has been selected against the PRD in the Master Blueprint. Execute sequentially.

---

## 1. The GitHub Monorepo Architecture

### 1.1 Repository Initialization

```bash
# Create and initialize the repository
mkdir project-nexus-core && cd project-nexus-core
git init
git branch -M main

# Set commit identity
git config user.name "Your Name"
git config user.email "your@email.com"
```

### 1.2 Complete Folder Structure

```
project-nexus-core/
│
│── src/                              ← CORE APPLICATION SOURCE
│   ├── etl/                          ← Phase 1: "Data Surgery" Engine
│   │   ├── __init__.py
│   │   ├── profilers/                ← Data quality assessment
│   │   │   ├── __init__.py
│   │   │   └── excel_profiler.py     ← Day 2 deliverable
│   │   ├── cleaners/                 ← Format normalization, dedup
│   │   │   ├── __init__.py
│   │   │   ├── numeric_normalizer.py ← EU/US decimal resolution
│   │   │   ├── date_normalizer.py    ← Multi-format date parsing
│   │   │   └── text_normalizer.py    ← Unicode, casing, whitespace
│   │   ├── loaders/                  ← PostgreSQL schema loading
│   │   │   ├── __init__.py
│   │   │   └── postgres_loader.py    ← SQLAlchemy bulk insert
│   │   └── validators/               ← Data contract enforcement
│   │       ├── __init__.py
│   │       └── reconciliation.py     ← Source ↔ warehouse totals check
│   │
│   ├── engine/                       ← Phase 2: Conversational BI
│   │   ├── __init__.py
│   │   ├── nl_to_sql/                ← Natural language → SQL
│   │   │   ├── __init__.py
│   │   │   ├── translator.py         ← LLM prompt → SQL generation
│   │   │   ├── validator.py          ← sqlglot pre-execution parse
│   │   │   └── executor.py           ← PostgreSQL query execution
│   │   ├── whatsapp/                 ← WhatsApp Business API
│   │   │   ├── __init__.py
│   │   │   ├── webhook.py            ← FastAPI webhook receiver
│   │   │   ├── sender.py             ← Outbound message dispatch
│   │   │   └── formatter.py          ← Result → WhatsApp message
│   │   └── schedulers/               ← Automated digest delivery
│   │       ├── __init__.py
│   │       └── weekly_digest.py      ← Cron-triggered weekly summary
│   │
│   ├── llm/                          ← LLM integration layer
│   │   ├── __init__.py
│   │   ├── client.py                 ← Unified OpenAI/Anthropic client
│   │   ├── cost_tracker.py           ← Token counting + spend monitoring
│   │   ├── prompts/                  ← Versioned prompt templates
│   │   │   ├── __init__.py
│   │   │   ├── entity_resolution.py  ← "Given these names, cluster..."
│   │   │   ├── sql_translation.py    ← NL→SQL system prompt
│   │   │   └── result_narration.py   ← SQL result → natural language
│   │   └── entity_resolution/        ← Semantic entity clustering
│   │       ├── __init__.py
│   │       ├── resolver.py           ← LLM + rapidfuzz hybrid
│   │       └── canonical_store.py    ← Canonical entity registry
│   │
│   └── common/                       ← Shared infrastructure
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py           ← Pydantic BaseSettings from .env
│       ├── logging/
│       │   ├── __init__.py
│       │   └── setup.py              ← structlog configuration
│       └── exceptions/
│           ├── __init__.py
│           └── domain.py             ← NexusValidationError, etc.
│
├── data/
│   ├── synthetic/                    ← Generated messy test data
│   │   ├── .gitkeep
│   │   ├── logistics_invoices.xlsx        ← Day 1 output (tracked)
│   │   └── construction_pricing.xlsx      ← Day 1 output (tracked)
│   ├── schemas/                      ← PostgreSQL DDL scripts
│   │   ├── logistics.sql             ← Day 7: normalized logistics schema
│   │   └── construction.sql          ← Day 7: normalized construction schema
│   ├── sample_outputs/               ← Example profiling/audit reports
│   │   └── .gitkeep
│   └── fixtures/                     ← Static test data for CI
│       └── .gitkeep
│
├── dashboard/                        ← Streamlit Audit Dashboard
│   ├── app.py                        ← Main Streamlit entry point
│   ├── pages/
│   │   ├── 01_upload.py              ← File upload interface
│   │   ├── 02_quality_scorecard.py   ← Data quality metrics
│   │   ├── 03_entity_resolution.py   ← Before/after entity view
│   │   └── 04_findings.py           ← Top findings + euro impact
│   ├── components/
│   │   ├── charts.py                 ← Plotly chart builders
│   │   └── metrics.py                ← KPI card components
│   └── assets/
│       └── style.css                 ← Navy/white/amber branding
│
├── api/                              ← FastAPI Service Layer
│   ├── main.py                       ← FastAPI app factory
│   ├── routes/
│   │   ├── webhook.py                ← POST /webhook/whatsapp
│   │   ├── health.py                 ← GET /health
│   │   └── profiling.py             ← POST /api/v1/profile
│   ├── middleware/
│   │   ├── auth.py                   ← API key validation
│   │   └── rate_limit.py            ← Per-client rate limiting
│   └── models/
│       ├── requests.py              ← Pydantic request schemas
│       └── responses.py             ← Pydantic response schemas
│
├── scripts/
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── generate_messy_logistics.py     ← DAY 1 TARGET SCRIPT
│   │   └── generate_messy_construction.py  ← Day 1 (second dataset)
│   ├── migrations/                   ← Alembic migration scripts
│   └── seed/
│       └── seed_from_synthetic.py    ← Load synthetic → PostgreSQL
│
├── tests/
│   ├── unit/
│   │   ├── etl/
│   │   │   ├── test_numeric_normalizer.py
│   │   │   ├── test_date_normalizer.py
│   │   │   └── test_excel_profiler.py
│   │   ├── engine/
│   │   │   ├── test_sql_validator.py
│   │   │   └── test_nl_to_sql.py
│   │   └── llm/
│   │       └── test_entity_resolver.py
│   ├── integration/
│   │   ├── test_full_pipeline.py
│   │   └── test_whatsapp_webhook.py
│   └── fixtures/
│       └── small_logistics_sample.xlsx
│
├── docs/
│   ├── architecture/
│   │   ├── c4-context.mermaid
│   │   └── data-flow.mermaid
│   ├── adr/
│   │   └── 001-llm-in-etl-pipeline.md
│   └── runbooks/
│       └── new-client-onboarding.md
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── terraform/
│       └── railway.tf
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    ← Lint + test on every PR
│       └── cd.yml                    ← Deploy on merge to main
│
├── .vscode/
│   └── extensions.json               ← Recommended extensions
│
├── pyproject.toml                    ← Project config + dependencies
├── requirements.txt                  ← Pinned deps (pip fallback)
├── .env.example                      ← Environment template
├── .gitignore                        ← GDPR-aware data exclusion
├── LICENSE                           ← MIT
└── README.md                         ← Portfolio showcase
```

### 1.3 Why This Structure

The monorepo follows three principles from the Blueprint:

**Separation of Concerns:** `src/etl/` (Phase 1: Data Surgery) is completely decoupled from `src/engine/` (Phase 2: Conversational BI). Either can be deployed independently. The `src/llm/` layer is shared infrastructure consumed by both phases.

**Client Data Isolation:** The `.gitignore` explicitly blocks `data/client/`, `data/uploads/`, and `data/raw/`. Only synthetic data and schemas are tracked. This is non-negotiable for GDPR compliance and client trust.

**Portfolio Legibility:** A Head of Data scanning this repo sees immediately: domain-driven folder names, clean `__init__.py` boundaries, test coverage at every layer, ADRs documenting key decisions. This is not a prototype — it is an enterprise codebase.

---

## 2. Developer Environment Setup

### 2.1 Exact Terminal Commands

```bash
# ─────────────────────────────────────────────────────────────
# OPTION A: uv (RECOMMENDED — 10x faster than pip)
# ─────────────────────────────────────────────────────────────

# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment pinned to Python 3.11
uv venv --python 3.11
source .venv/bin/activate

# Install all dependencies
uv pip install -r requirements.txt

# Install dev dependencies
uv pip install -r requirements.txt
uv pip install pytest pytest-cov pytest-asyncio mypy ruff pre-commit ipython

# Verify installation
python -c "import pandas, faker, streamlit, sqlglot, sqlalchemy, openai, fastapi; print('✓ All core deps OK')"

# ─────────────────────────────────────────────────────────────
# OPTION B: Standard venv + pip
# ─────────────────────────────────────────────────────────────

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio mypy ruff pre-commit ipython

# ─────────────────────────────────────────────────────────────
# OPTION C: poetry (if you prefer lockfile management)
# ─────────────────────────────────────────────────────────────

poetry init --python "^3.11"
poetry install
poetry add pandas openpyxl faker streamlit sqlglot sqlalchemy psycopg2-binary openai anthropic fastapi uvicorn
poetry add --group dev pytest pytest-cov mypy ruff pre-commit
```

### 2.2 PostgreSQL Setup

```bash
# Local PostgreSQL (macOS via Homebrew)
brew install postgresql@15
brew services start postgresql@15
createdb nexus_warehouse
psql nexus_warehouse -c "CREATE USER nexus_admin WITH PASSWORD 'dev_password_change_me';"
psql nexus_warehouse -c "GRANT ALL PRIVILEGES ON DATABASE nexus_warehouse TO nexus_admin;"

# OR: Docker PostgreSQL (any OS)
docker run -d \
  --name nexus-postgres \
  -e POSTGRES_DB=nexus_warehouse \
  -e POSTGRES_USER=nexus_admin \
  -e POSTGRES_PASSWORD=dev_password_change_me \
  -p 5432:5432 \
  postgres:15-alpine

# OR: Supabase free tier (zero-install, cloud)
# Create project at https://supabase.com → copy connection string to .env
```

### 2.3 Pre-Commit Hooks

```bash
# Initialize pre-commit
pre-commit install

# .pre-commit-config.yaml (create this file)
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
        args: ['--maxkb=5000']
      - id: detect-private-key
      - id: check-merge-conflict
EOF
```

### 2.4 Environment Configuration

```bash
cp .env.example .env
# Edit .env with real values:
#   OPENAI_API_KEY=sk-...
#   DATABASE_URL=postgresql://nexus_admin:dev_password_change_me@localhost:5432/nexus_warehouse
```

---

## 3. Agentic Tooling Strategy

### 3.1 Claude Code CLI — Copy-Paste Prompt

Open your terminal in the `project-nexus-core/` directory and paste this entire prompt into Claude Code:

```
I am building Project Nexus, an LLM-Augmented ETL system for Spanish SMB margin recovery. Read the file at scripts/generators/generate_messy_logistics.py — it contains the code contract and full implementation for our synthetic data generator.

Your task: Execute this script and verify the output. Then create the SECOND synthetic dataset: scripts/generators/generate_messy_construction.py

The construction dataset must generate 3,000 rows of a messy SKU price list for a €10M construction materials distributor ("Materiales del Mediterráneo S.A." — fictitious). It must simulate:

1. ENTITY DUPLICATION: Product names with variants ("Cemento Portland CEM I 42.5R" vs "CEMENTO PORTLAND 42.5" vs "Cem. Portland I/42.5R")
2. PRICING INCONSISTENCY: Same SKU with 3+ different prices across time periods, some using EU decimal format, some US format
3. DISCOUNT CHAOS: Columns for "Descuento %" with inconsistent formats (0.15, 15%, "15 por ciento", "quince")
4. COST DATA LATENCY: A "Coste Material" column where 40% of values are 6–18 months out of date vs current market prices
5. DEAD STOCK: 8% of SKUs with zero sales in the last 6 months but positive inventory holding cost
6. MISSING FIELDS: 10% null rate on critical columns (supplier CIF, unit weight, minimum order quantity)

The code must follow the same quality standards as the logistics generator: full type hints, docstrings, argparse CLI, Faker with es_ES locale, configurable seed, xlsx output with professional formatting. Include ground truth columns prefixed with _ for validation.
```

### 3.2 Google Antigravity IDE — Agent Prompt

In the Antigravity agent chat panel, paste:

```
@workspace I need you to build a synthetic data generator for Project Nexus. Context: this is an LLM-Augmented ETL system for Spanish SMB margin recovery.

Reference: Look at scripts/generators/generate_messy_logistics.py for the code style, structure, and quality standard I expect.

Task: Create scripts/generators/generate_messy_construction.py that generates 3,000 rows of messy SKU pricing data for a fictitious €10M Spanish construction materials distributor. Requirements:

- Entity duplication on product names (e.g., "Cemento Portland CEM I 42.5R" appearing as 5+ dirty variants)
- EU/US decimal confusion on all monetary columns
- Discount field chaos (percentages as decimals, strings, words)
- 40% of cost data is 6-18 months stale
- 8% dead stock (zero sales, positive holding cost)
- 10% nulls on critical fields
- Full type hints, docstrings, Faker es_ES locale
- argparse CLI with --rows, --seed, --output flags
- xlsx export with XlsxWriter formatting
- Ground truth columns prefixed with _

Run the logistics generator first to verify it works, then build the construction generator following the identical pattern.
```

### 3.3 Key Difference Between the Two Tools

**Claude Code** excels at: autonomous multi-file generation, running terminal commands, iterating on test failures, editing existing files. Best for: "Build this entire module end-to-end."

**Google Antigravity** excels at: workspace-aware context (reads your entire repo), inline code suggestions, visual diff reviews. Best for: "Refactor this across 5 files" or "Explain then implement."

**Recommendation for Day 1:** Use Claude Code for the initial scaffold and generators (it can run `python` and verify output). Use Antigravity for Days 2–3 when building the profiling engine (it benefits from seeing the generator output as context).

---

## 4. The Code Contract: Synthetic Data Generator

### 4.1 File: `scripts/generators/generate_messy_logistics.py`

**Status: IMPLEMENTED** (see the file in this repository)

### 4.2 Contract Specifications

| Specification | Requirement | Implementation |
|---|---|---|
| **Row count** | 5,000 rows of freight invoices | `DEFAULT_ROWS = 5_000`, configurable via `--rows` |
| **Time range** | 6 months of historical data | `2025-07-01` to `2025-12-31` |
| **Decimal confusion** | EU format (`1.234,56`) mixed with US format (`1,234.56`) | 25% EU format rate, 4 format variants |
| **Date format chaos** | `DD/MM/YYYY`, `MM-DD-YY`, `YYYY.MM.DD`, `DD-MMM-YYYY`, more | 35% non-standard rate, 6 format variants |
| **Entity duplication** | `Martinez SL` / `Martínez S.L.` / `MARTINEZ` / `Ferre. Martinez SL` | 8 canonical suppliers × 4–6 dirty variants each |
| **Unbilled accessorials** | 15% of shipments have incurred but unrecoverable charges | 6 accessorial types (waiting, tail-lift, ADR, detour, etc.) |
| **Unprofitable routes** | 30% of routes priced below true cost | 5 of 12 routes are margin-negative by design |
| **Invoice errors** | 12% error rate (overcharges, undercharges, duplicates) | 3 error types injected randomly |
| **Missing data** | 2–55% null rates calibrated per column | Critical financial fields: 40% null on true cost |
| **Duplicate invoices** | 3% exact or near-duplicate rows | Invoice number variants (e.g., `FAC ` vs `FAC`) |
| **Ground truth** | Hidden columns prefixed with `_` for validation | `_ruta_rentable`, `_suplemento_facturado`, `_margen_real` |
| **Reproducibility** | Identical output for same seed | `--seed` flag, deterministic RNG chain |

### 4.3 Validation Checklist

After running the generator, verify these assertions:

```python
import pandas as pd

df = pd.read_excel("data/synthetic/logistics_invoices_ground_truth.xlsx")

# Row count (5000 + ~3% duplicates ≈ 5150)
assert 5000 <= len(df) <= 5300, f"Row count {len(df)} outside expected range"

# Unprofitable routes exist (~30%)
unprofitable_pct = (df["_ruta_rentable"] == False).mean()
assert 0.20 <= unprofitable_pct <= 0.40, f"Unprofitable route % = {unprofitable_pct:.1%}"

# Unbilled accessorials exist
unbilled_pct = (df["_suplemento_facturado"] == False).mean()
assert 0.05 <= unbilled_pct <= 0.25, f"Unbilled accessorial % = {unbilled_pct:.1%}"

# Negative margins exist
negative_margin_pct = (df["_margen_real"] < 0).mean()
assert negative_margin_pct >= 0.15, f"Negative margin % = {negative_margin_pct:.1%}"

# Null rates on key fields
assert df["Coste Real Estimado (€)"].isna().mean() >= 0.30, "True cost null rate too low"
assert df["Matrícula"].isna().mean() >= 0.10, "Plate null rate too low"

# EU decimal format exists in monetary columns
invoiced_col = df["Importe Facturado (€)"].astype(str)
eu_format_count = invoiced_col.str.contains(r"\d{1,3}\.\d{3},\d{2}", na=False).sum()
assert eu_format_count >= 100, f"Too few EU-formatted amounts: {eu_format_count}"

# Date format chaos exists
date_col = df["Fecha Factura"].astype(str)
has_dash_month = date_col.str.contains(r"\d{2}-[A-Z][a-z]{2}-\d{4}", na=False).sum()
assert has_dash_month >= 50, f"Too few DD-MMM-YYYY dates: {has_dash_month}"

print("✓ All code contract assertions passed.")
```

---

## 5. Documentation & README Strategy

### 5.1 README Architecture (Implemented)

The README.md in this repository is structured to pass the "30-Second Head of Data Test" — a senior technical leader scanning your GitHub profile should understand three things within 30 seconds:

1. **What problem this solves** (margin leakage in data-dark SMBs)
2. **What makes the architecture novel** (LLM-Augmented ETL + Anti-Hallucination Protocol)
3. **That this is production-grade** (test coverage, type hints, CI/CD, ADRs)

### 5.2 Key Sections That Signal Architectural Maturity

**"Anti-Hallucination Protocol"** — This section signals you understand the #1 failure mode of LLM-in-production systems: fabricated outputs. By naming the protocol explicitly and documenting five enforcement layers, you demonstrate awareness of LLM safety that most engineers lack.

**"LLM-Augmented ETL" comparison table** — The Traditional ETL vs LLM-Augmented ETL table proves you can articulate WHY an LLM belongs in an ETL pipeline (semantic understanding, not generation) without falling into the "AI for everything" trap.

**"Bleeding Neck" simulation table** — Showing that your synthetic data is calibrated to industry research (with citations) proves domain expertise, not just engineering skill.

**Architecture diagram in ASCII** — Renders in any terminal, any browser, any PDF. No external tool dependencies. Shows full data flow from ingestion to WhatsApp delivery.

### 5.3 Supporting Documentation to Create (Days 2–14)

| Document | Location | Purpose |
|---|---|---|
| ADR-001: LLM in ETL Pipeline | `docs/adr/001-llm-in-etl-pipeline.md` | Why we chose LLM for entity resolution over pure fuzzy matching |
| ADR-002: Anti-Hallucination Design | `docs/adr/002-anti-hallucination-protocol.md` | Why deterministic querying, not generative answering |
| C4 Context Diagram | `docs/architecture/c4-context.mermaid` | System boundaries and external actors |
| Data Flow Diagram | `docs/architecture/data-flow.mermaid` | Excel → ETL → PostgreSQL → WhatsApp |
| New Client Runbook | `docs/runbooks/new-client-onboarding.md` | Step-by-step: receive file → profile → dashboard → deliver |

---

## 6. Day 1 Execution Sequence

Execute in this exact order:

```bash
# Step 1: Create the repository
mkdir project-nexus-core && cd project-nexus-core
git init && git branch -M main

# Step 2: Copy all files from this initialization package

# Step 3: Set up environment
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -r requirements.txt

# Step 4: Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Step 5: Generate synthetic data
python scripts/generators/generate_messy_logistics.py --rows 5000 --seed 2026

# Step 6: Verify output
python scripts/generators/generate_messy_logistics.py --rows 5000 --seed 2026 --ground-truth
ls -la data/synthetic/

# Step 7: Run validation assertions (from Section 4.3 above)

# Step 8: Initial commit
git add -A
git commit -m "feat: Day 1 — project scaffold + synthetic logistics data generator

- Enterprise monorepo structure (src/etl, src/engine, src/llm)
- 5,000-row synthetic freight invoice dataset with calibrated error injection
- EU/US decimal confusion, date format chaos, entity duplication
- Unbilled accessorial simulation (15% revenue leakage)
- Unprofitable route injection (30% margin-negative lanes)
- Ground truth columns for pipeline validation
- Portfolio-grade README with Anti-Hallucination Protocol documentation
- pyproject.toml with pinned dependencies
- GDPR-aware .gitignore excluding all client data paths"

# Step 9: Push to GitHub
gh repo create project-nexus-core --public --source=. --push
# OR:
git remote add origin git@github.com:YOUR_USERNAME/project-nexus-core.git
git push -u origin main
```

### Day 1 Success Criteria (from Master Blueprint)

> **"Datasets pass profiling with realistic error distribution"**

The generator output must satisfy:
- 5,000+ rows of freight invoices
- Visibly messy when opened in Excel (mixed decimal formats, date chaos)
- Entity variants visible on casual inspection
- Ground truth columns enable quantitative validation
- `--seed` flag produces bit-identical output on re-run

**Day 1 is complete when:** Both synthetic datasets exist in `data/synthetic/`, the repository is pushed to GitHub with a clean README, and a non-technical person opening the Excel file would say "this looks like real company data."

---

**END OF TECHNICAL INITIALIZATION PLAN**
