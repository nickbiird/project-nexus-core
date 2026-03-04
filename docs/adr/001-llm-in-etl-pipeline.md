# ADR-001: LLM Integration in ETL Pipeline

**Status:** Accepted
**Date:** 2026-03-03
**Deciders:** Founder / CTO

## Context

Project Nexus ingests decades of messy spreadsheet data from Spanish SMBs. The core ETL challenge is entity resolution and format normalization across files with no consistent schema. Traditional approaches (regex, rule-based matching) require per-client rule authoring and fail on unseen entity variations.

## Decision

We embed LLM API calls (GPT-4o primary, Claude fallback) directly into the ETL pipeline for three specific tasks:

1. **Entity resolution**: Clustering supplier/customer name variants into canonical entities
2. **Format classification**: Detecting whether a numeric column uses EU or US decimal conventions
3. **Anomaly narration**: Generating human-readable descriptions of statistical outliers

The LLM is NOT used for:
- Generating financial figures
- Making business recommendations
- Any task where hallucination would produce incorrect data in the warehouse

## Consequences

**Positive:**
- Zero-shot generalization on new client data (no per-client rule authoring)
- 90%+ entity clustering accuracy on synthetic benchmarks
- Dramatically reduced onboarding time per client

**Negative:**
- API cost per ETL run (~€0.50–€2.00 depending on data volume)
- Latency: LLM calls add 30–120 seconds to full pipeline execution
- Dependency on external API availability (mitigated by retry + local model fallback)

**Mitigations:**
- Cost ceiling enforced via `llm_cost_limit_per_run_usd` in settings
- All LLM decisions logged with confidence scores for audit
- rapidfuzz used as a fast pre-filter; LLM only invoked for ambiguous clusters
