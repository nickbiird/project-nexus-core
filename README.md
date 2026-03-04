<p align="center">
  <img src="docs/architecture/nexus-logo-placeholder.svg" alt="Project Nexus" width="200"/>
</p>

<h1 align="center">Project Nexus</h1>
<h3 align="center">LLM-Augmented ETL & Conversational BI for SMB Margin Recovery</h3>

<p align="center">
  <a href="#architecture"><img src="https://img.shields.io/badge/Architecture-LLM--Augmented%20ETL-blue?style=flat-square" alt="Architecture"/></a>
  <a href="#anti-hallucination-protocol"><img src="https://img.shields.io/badge/Safety-Anti--Hallucination%20Protocol-green?style=flat-square" alt="Anti-Hallucination"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-yellow?style=flat-square&logo=python" alt="Python 3.11+"/></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql" alt="PostgreSQL"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="MIT License"/></a>
</p>

---

## The Problem

**Two-thirds of Southern European SMBs (€5M–€20M revenue) operate below high digital intensity.** They generate millions of transactional records per year in fragmented Excel spreadsheets, paper invoices, and legacy ERP exports — and cannot extract a single actionable insight from any of it.

The result is **3–8% of gross revenue silently leaking** through invisible channels: unbilled freight accessorials, unprofitable routes priced by gut instinct, duplicate vendor charges compounding year over year, and inventory mispriced against cost data that's months out of date.

Every prior solution has failed them:
- **ERPs** (€20K–€100K) demand clean data they'll never receive. 70% fail to deliver ROI.
- **BI Dashboards** render beautiful charts from garbage data — mathematically authoritative yet entirely wrong.
- **No-Code Tools** accelerate the velocity at which bad data propagates between systems.
- **The Gestoría** provides backward-looking compliance data, not forward-looking intelligence.

**Project Nexus is the only solution that fixes the data first.**

---

## Architecture

Project Nexus implements a radical separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENT EXPERIENCE (Phase 2)                      │
│                                                                     │
│   WhatsApp ──→ Intent Classification ──→ NL-to-SQL Translation     │
│                                          │                          │
│                                    ┌─────┴──────┐                   │
│                                    │ Anti-Halluc.│                   │
│                                    │  Protocol   │                   │
│                                    └─────┬──────┘                   │
│                                          │                          │
│   WhatsApp ←── Result Narration ←── SQL Execution                  │
│                                          │                          │
├──────────────────────────────────────────┼──────────────────────────┤
│                SINGLE SOURCE OF TRUTH     │                          │
│                ┌─────────────────┐       │                          │
│                │   PostgreSQL    │◄──────┘                          │
│                │   Warehouse    │                                    │
│                └────────┬───────┘                                    │
│                         │                                           │
├─────────────────────────┼───────────────────────────────────────────┤
│              DATA SURGERY ENGINE (Phase 1)                          │
│                         │                                           │
│   ┌─────────┐    ┌──────┴──────┐    ┌──────────────┐              │
│   │ Ingest  │───→│ LLM-Augmented│───→│ Schema Design│              │
│   │ (Excel, │    │ Semantic     │    │ & Loading    │              │
│   │  CSV,   │    │ Cleaning     │    │ (3NF, FK,    │              │
│   │  PDF)   │    │              │    │  Constraints)│              │
│   └─────────┘    └──────────────┘    └──────────────┘              │
│                         │                                           │
│              ┌──────────┼──────────┐                                │
│              │          │          │                                 │
│         Entity      Format     Anomaly                              │
│         Resolution  Normal.    Detection                            │
│                                                                     │
│   "Martinez SL" ═══► "Ferretería Martínez S.L."                   │
│   "15/03/2024"  ═══► 2024-03-15T00:00:00Z                         │
│   "1.234,56 €"  ═══► 1234.56                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why "LLM-Augmented ETL"?

Traditional ETL relies on **deterministic regex rules** to parse data — a Sisyphean task when confronting decades of human error across thousands of spreadsheet rows. Writing regex to match every possible misspelling of "Ferretería Martínez S.L." is prohibitively expensive and logistically impossible.

Project Nexus embeds Large Language Models **directly into the ETL pipeline** as a semantic understanding layer:

| Traditional ETL | LLM-Augmented ETL |
|---|---|
| Pattern matching (regex) | Semantic understanding (contextual) |
| Fails on unseen variations | Generalizes across entity representations |
| Requires per-client rule authoring | Zero-shot inference on new client data |
| Cannot resolve cross-file entity conflicts | Cross-references entities across all source files |
| Manual threshold tuning | Confidence-scored with human-in-the-loop fallback |

The LLM is **not** generating data. It is **classifying, clustering, and translating** — tasks where hallucination risk is minimal and measurable. Every LLM decision is logged, scored, and auditable.

---

## Anti-Hallucination Protocol

> **The single most critical architectural constraint.** One fabricated number destroys all trust with the target buyer persona — permanently.

The system enforces **Deterministic Querying, Not Generative Answering** through five layers:

| Layer | Mechanism | Implementation |
|---|---|---|
| **Prompt Engineering** | System prompt constraint | LLM is explicitly restricted to SQL translation and result narration. It is forbidden from generating numbers from parametric memory. |
| **Schema Grounding** | Full DDL injection | Complete database schema provided in every request context. SQL generation is constrained to existing tables and columns only. |
| **SQL Validation** | Pre-execution parse via `sqlglot` | Only `SELECT` permitted. All referenced tables/columns verified against schema. Query complexity limits prevent runaway joins. |
| **Result Binding** | Post-execution audit | Response generation prompt includes **only** the raw SQL result set. A post-processing step verifies every number in the natural language response appears in the query output. |
| **Uncertainty Handling** | Explicit "I don't know" | If data is unavailable or query is ambiguous, the system asks for clarification — it never guesses. |

```python
# Simplified illustration of the Anti-Hallucination pipeline
async def handle_query(user_message: str, schema: SchemaContext) -> Response:
    # Step 1: LLM translates natural language → SQL
    sql = await llm.translate_to_sql(user_message, schema=schema)

    # Step 2: Validate SQL before execution (CRITICAL)
    validated_sql = sql_validator.validate(
        sql,
        allowed_operations={"SELECT"},
        allowed_tables=schema.table_names,
        max_joins=4,
    )

    # Step 3: Execute against PostgreSQL (deterministic)
    result_set = await db.execute(validated_sql)

    # Step 4: LLM narrates the result (bound to result_set ONLY)
    response = await llm.narrate_result(
        query=user_message,
        sql=validated_sql,
        result=result_set,
        constraint="Every number must appear in the result set. Add nothing.",
    )

    # Step 5: Post-audit — verify all numbers in response exist in result
    audit_result = number_auditor.verify(response, result_set)
    if not audit_result.passed:
        return Response("I found the data but need to verify my summary. Here are the raw numbers: ...")

    return response
```

---

## Project Structure

```
project-nexus-core/
│
├── src/                          # Core application source
│   ├── etl/                      # Phase 1: Data Surgery Engine
│   │   ├── profilers/            #   → Data quality assessment (ydata-profiling, custom)
│   │   ├── cleaners/             #   → Format normalization, deduplication
│   │   ├── loaders/              #   → PostgreSQL schema loading (SQLAlchemy + Alembic)
│   │   └── validators/           #   → Great Expectations data contracts
│   │
│   ├── engine/                   # Phase 2: Conversational BI
│   │   ├── nl_to_sql/            #   → Natural language → SQL translation
│   │   ├── whatsapp/             #   → WhatsApp Business API integration
│   │   └── schedulers/           #   → Weekly digest & proactive alert delivery
│   │
│   ├── llm/                      # LLM integration layer
│   │   ├── prompts/              #   → Versioned prompt templates (entity resolution, SQL, narration)
│   │   └── entity_resolution/    #   → Semantic entity clustering & deduplication
│   │
│   └── common/                   # Shared infrastructure
│       ├── config/               #   → Pydantic settings, feature flags
│       ├── logging/              #   → Structured logging (structlog)
│       └── exceptions/           #   → Domain-specific exception hierarchy
│
├── data/
│   ├── synthetic/                # Generated test datasets (Faker-based)
│   ├── schemas/                  # PostgreSQL DDL (logistics.sql, construction.sql)
│   ├── sample_outputs/           # Example profiling reports, audit outputs
│   └── fixtures/                 # Static test data
│
├── dashboard/                    # Streamlit audit dashboard
│   ├── pages/                    #   → Multi-page Streamlit app
│   ├── components/               #   → Reusable UI components
│   └── assets/                   #   → CSS, images, branding
│
├── api/                          # FastAPI service layer
│   ├── routes/                   #   → WhatsApp webhook, health, profiling endpoints
│   ├── middleware/                #   → Auth, rate limiting, CORS
│   └── models/                   #   → Pydantic request/response schemas
│
├── scripts/
│   ├── generators/               # Synthetic data generators
│   │   └── generate_messy_logistics.py   # ← START HERE (Day 1)
│   ├── migrations/               # Alembic migration scripts
│   └── seed/                     # Database seeding scripts
│
├── tests/
│   ├── unit/                     # Fast, isolated unit tests
│   ├── integration/              # Tests requiring DB or API access
│   └── fixtures/                 # Shared test fixtures
│
├── docs/
│   ├── architecture/             # C4 diagrams, ADRs
│   ├── adr/                      # Architecture Decision Records
│   └── runbooks/                 # Operational procedures
│
├── infra/
│   ├── docker/                   # Dockerfiles, docker-compose
│   └── terraform/                # IaC for Railway/Render deployment
│
├── .github/workflows/            # CI/CD pipelines
├── pyproject.toml                # Project metadata + all dependencies
├── requirements.txt              # Pinned dependencies (pip-compatible)
├── .env.example                  # Environment template (NEVER commit .env)
├── .gitignore                    # Data exclusion rules (GDPR-aware)
└── README.md                     # ← You are here
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (local or [Supabase](https://supabase.com) free tier)
- An OpenAI API key (for LLM-augmented features)

### Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/project-nexus-core.git
cd project-nexus-core

# Create virtual environment (using uv for speed, or venv)
uv venv --python 3.11 && source .venv/bin/activate  # Option A: uv
python3.11 -m venv .venv && source .venv/bin/activate  # Option B: stdlib

# Install dependencies
uv pip install -r requirements.txt   # Option A: uv
pip install -r requirements.txt      # Option B: pip

# Configure environment
cp .env.example .env
# Edit .env with your actual credentials

# Generate synthetic test data (Day 1 deliverable)
python scripts/generators/generate_messy_logistics.py --rows 5000

# Run the profiling engine (Day 2)
python -m src.etl.profilers.excel_profiler data/synthetic/logistics_invoices.xlsx

# Launch the audit dashboard (Day 4)
streamlit run dashboard/app.py
```

---

## The "Bleeding Neck" Problems This Solves

The synthetic data generator (`scripts/generators/generate_messy_logistics.py`) reproduces the exact margin destruction patterns documented in [industry research](docs/architecture/research-sources.md):

| Problem | Real-World Impact | How We Simulate It |
|---|---|---|
| **Decimal Confusion** | `1.234,56` (EU) vs `1,234.56` (US) causes silent calculation errors | 25% of monetary values use European formatting |
| **Date Format Chaos** | `DD/MM/YYYY` vs `MM/DD/YYYY` causes mis-sorted time series | 35% of dates use non-standard formats |
| **Entity Duplication** | "Martinez SL" ≠ "Martínez S.L." fragments customer analytics | 20% of entity references are dirty variants |
| **Unbilled Accessorials** | 10–15% of freight charges incurred but never invoiced | 15% of shipments have accessorial revenue leakage |
| **Unprofitable Routes** | 62% of lanes unprofitable in a given quarter (SmartHop) | 30% of routes priced below true cost |
| **Invoice Errors** | 25% of freight invoices contain errors | 12% error rate with overcharges, undercharges, duplicates |
| **Missing Data** | Real-world spreadsheets have pervasive null fields | 8–55% null rates across columns (calibrated per field) |

---

## Target Verticals

**Regional Logistics (€10M–€20M revenue)**
> Freight invoice audit, route profitability, accessorial recovery, capacity optimization

**Construction Materials Distribution (€8M–€20M revenue)**
> SKU pricing integrity, inventory cost management, quote-level margin visibility

---

## Roadmap

- [x] **Day 1**: Synthetic data generation (messy logistics + construction datasets)
- [ ] **Day 2–3**: Python data profiling engine (quality metrics, entity detection, anomaly flagging)
- [ ] **Day 4–6**: Streamlit audit dashboard + LLM entity resolution integration
- [ ] **Day 7–9**: PostgreSQL schema, NL-to-SQL engine, WhatsApp prototype
- [ ] **Day 10–14**: Full integration testing, GTM collateral, first outreach

---

## Contributing

This project is open for contributions. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with conviction in Barcelona. Every line of code exists to answer one question for a business owner: <em>"Where is my money going?"</em></sub>
</p>
