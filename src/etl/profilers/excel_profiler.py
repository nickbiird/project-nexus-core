"""
Project Nexus — Data Quality Profiling Engine
==============================================

Day 2 Deliverable: Automated data quality assessment for the Free Audit Hook.

Accepts any .xlsx or .csv file, runs a comprehensive battery of quality checks,
and outputs a structured ProfilingReport with "Surprise Findings" quantified in euros.

Usage:
    python -m src.etl.profilers.excel_profiler data/synthetic/logistics_invoices.xlsx
    python -m src.etl.profilers.excel_profiler data.csv --output report.json

Performance target: <60 seconds on 50,000 rows.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

# ──────────────────────────────────────────────────────────────
# Data Classes (Typed Output Structures)
# ──────────────────────────────────────────────────────────────


@dataclass
class ColumnProfile:
    """Quality profile for a single column."""

    name: str
    inferred_type: str  # numeric, date, text, categorical, entity, financial
    total_rows: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    sample_values: list[Any]
    format_inconsistencies: int = 0
    format_details: str = ""


@dataclass
class EntityCluster:
    """A group of text values that likely refer to the same real-world entity."""

    cluster_id: int
    canonical: str
    variants: list[str]
    confidence: str  # high, medium, low
    similarity_score: float


@dataclass
class EntityAnalysis:
    """Entity deduplication analysis for a single column."""

    column_name: str
    raw_unique_count: int
    estimated_canonical_count: int
    duplicate_entity_count: int
    clusters: list[EntityCluster]


@dataclass
class Anomaly:
    """A single detected anomaly in a financial column."""

    column_name: str
    anomaly_type: str  # outlier_high, outlier_low, zero_value, negative, duplicate_invoice
    value: float
    row_index: int
    context: str  # human-readable description


@dataclass
class AnomalyAnalysis:
    """Anomaly detection results for a single financial column."""

    column_name: str
    mean: float
    median: float
    stddev: float
    min_val: float
    max_val: float
    outlier_count: int
    zero_count: int
    negative_count: int
    anomalies: list[Anomaly]


@dataclass
class Finding:
    """A 'Surprise Finding' — a concrete, euro-quantified insight for the audit."""

    description: str
    estimated_eur_impact: float
    confidence: str  # high, medium, low
    rows_affected: int
    category: str  # duplicate_charges, pricing_spread, concentration_risk, negative_margin


@dataclass
class ProfilingReport:
    """Complete data quality profiling report."""

    # Metadata
    file_path: str
    file_size_mb: float
    total_rows: int
    total_columns: int
    processing_time_seconds: float
    timestamp: str

    # Section 1: Schema Detection
    column_profiles: list[ColumnProfile]
    detected_entity_columns: list[str]
    detected_financial_columns: list[str]
    detected_date_columns: list[str]

    # Section 2: Quality Metrics
    data_health_score: float  # 0–100
    completeness_score: float
    consistency_score: float
    uniqueness_score: float
    overall_null_pct: float
    exact_duplicate_rows: int
    near_duplicate_rows: int

    # Section 3: Entity Analysis
    entity_analyses: list[EntityAnalysis]

    # Section 4: Anomaly Flagging
    anomaly_analyses: list[AnomalyAnalysis]

    # Section 5: Financial Quick-Wins
    findings: list[Finding]
    total_estimated_impact_eur: float

    def to_json(self) -> str:
        """Serialize to JSON for Streamlit consumption."""
        return json.dumps(asdict(self), indent=2, default=str, ensure_ascii=False)

    def to_summary_str(self) -> str:
        """Generate the 3-sentence executive summary for the audit dashboard."""
        entity_dupes = sum(ea.duplicate_entity_count for ea in self.entity_analyses)
        anomaly_count = sum(
            aa.outlier_count + aa.zero_count + aa.negative_count for aa in self.anomaly_analyses
        )

        lines = [
            f"We analyzed {self.total_rows:,} records across {self.total_columns} columns.",
            f"We found {entity_dupes} probable duplicate entities and {anomaly_count} financial anomalies.",
            f"Estimated annual financial impact: €{self.total_estimated_impact_eur:,.0f}.",
        ]
        return " ".join(lines)

    def to_cli_report(self) -> str:
        """Generate a formatted CLI output for human review."""
        sep = "─" * 70
        lines = [
            "",
            sep,
            "  YELLOWBIRD TELEMETRY — Data Quality Profiling Report",
            sep,
            "",
            f"  File:            {self.file_path}",
            f"  Size:            {self.file_size_mb:.2f} MB",
            f"  Rows:            {self.total_rows:,}",
            f"  Columns:         {self.total_columns}",
            f"  Processing Time: {self.processing_time_seconds:.2f}s",
            "",
            sep,
            f"  DATA HEALTH SCORE:  {self.data_health_score:.0f} / 100",
            f"    Completeness:     {self.completeness_score:.0f}",
            f"    Consistency:      {self.consistency_score:.0f}",
            f"    Uniqueness:       {self.uniqueness_score:.0f}",
            sep,
            "",
            f"  Overall Null Rate:      {self.overall_null_pct:.1f}%",
            f"  Exact Duplicate Rows:   {self.exact_duplicate_rows:,}",
            f"  Near-Duplicate Rows:    {self.near_duplicate_rows:,}",
            "",
        ]

        # Entity Analysis
        if self.entity_analyses:
            lines.append("  ENTITY ANALYSIS")
            lines.append(sep)
            for ea in self.entity_analyses:
                lines.append(
                    f"  Column: {ea.column_name} — "
                    f"{ea.raw_unique_count} raw → {ea.estimated_canonical_count} canonical "
                    f"({ea.duplicate_entity_count} duplicates)"
                )
                for cluster in ea.clusters[:5]:  # Show top 5
                    variants_str = ", ".join(cluster.variants[:4])
                    if len(cluster.variants) > 4:
                        variants_str += f", +{len(cluster.variants) - 4} more"
                    lines.append(
                        f"    [{cluster.confidence.upper()}] '{cluster.canonical}' ← {variants_str}"
                    )
            lines.append("")

        # Anomaly Analysis
        if self.anomaly_analyses:
            lines.append("  ANOMALY ANALYSIS")
            lines.append(sep)
            for aa in self.anomaly_analyses:
                lines.append(
                    f"  Column: {aa.column_name} — "
                    f"mean: €{aa.mean:,.2f}, median: €{aa.median:,.2f}, "
                    f"σ: €{aa.stddev:,.2f}"
                )
                lines.append(
                    f"    Outliers: {aa.outlier_count}, "
                    f"Zeros: {aa.zero_count}, "
                    f"Negatives: {aa.negative_count}"
                )
            lines.append("")

        # Findings
        if self.findings:
            lines.append("  SURPRISE FINDINGS")
            lines.append(sep)
            for i, f in enumerate(self.findings, 1):
                lines.append(f"  {i}. [{f.confidence.upper()}] {f.description}")
                lines.append(
                    f"     Estimated Impact: €{f.estimated_eur_impact:,.0f} "
                    f"({f.rows_affected:,} rows affected)"
                )
            lines.append("")
            lines.append(sep)
            lines.append(
                f"  TOTAL ESTIMATED ANNUAL IMPACT: €{self.total_estimated_impact_eur:,.0f}"
            )
            lines.append(sep)

        # Executive Summary
        lines.append("")
        lines.append("  EXECUTIVE SUMMARY")
        lines.append(f"  {self.to_summary_str()}")
        lines.append("")

        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Column Type Detection
# ──────────────────────────────────────────────────────────────

# Common Spanish column name patterns for entity detection
ENTITY_KEYWORDS = [
    "proveedor",
    "supplier",
    "cliente",
    "customer",
    "empresa",
    "company",
    "transportista",
    "carrier",
    "nombre",
    "name",
    "destinatario",
    "remitente",
    "fabricante",
    "manufacturer",
    "distribuidor",
    "distributor",
    "razón social",
    "razon_social",
    "entidad",
]

# Common Spanish column name patterns for financial detection
FINANCIAL_KEYWORDS = [
    "importe",
    "amount",
    "precio",
    "price",
    "coste",
    "cost",
    "total",
    "factura",
    "invoice",
    "tarifa",
    "rate",
    "margen",
    "margin",
    "iva",
    "subtotal",
    "descuento",
    "discount",
    "cargo",
    "charge",
    "recargo",
    "surcharge",
    "base_imponible",
    "neto",
    "bruto",
    "beneficio",
    "profit",
    "gasto",
    "expense",
    "ingreso",
    "revenue",
    "eur",
    "€",
]

# Date column keywords
DATE_KEYWORDS = [
    "fecha",
    "date",
    "dia",
    "day",
    "mes",
    "month",
    "año",
    "year",
    "periodo",
    "period",
    "vencimiento",
    "due",
    "emision",
    "created",
    "modified",
    "updated",
    "entrega",
    "delivery",
]


def _is_entity_column(col_name: str, series: pd.Series) -> bool:
    """Detect if a column likely contains entity names (companies, people, products)."""
    col_lower = col_name.lower().replace("_", " ")
    if any(kw in col_lower for kw in ENTITY_KEYWORDS):
        return True
    # Heuristic: text column with moderate cardinality (not too few, not too many)
    if series.dtype == object:
        nunique = series.nunique()
        total = len(series.dropna())
        if total > 0:
            ratio = nunique / total
            # Entity columns typically have 5-500 unique values with some repetition
            if 5 <= nunique <= 500 and 0.01 < ratio < 0.5:
                # Check if values look like names (contain uppercase, reasonable length)
                sample = series.dropna().head(20)
                avg_len = sample.str.len().mean()
                if 3 < avg_len < 60:
                    return True
    return False


def _is_financial_column(col_name: str, series: pd.Series) -> bool:
    """Detect if a column likely contains financial amounts."""
    col_lower = col_name.lower().replace("_", " ")
    if any(kw in col_lower for kw in FINANCIAL_KEYWORDS):
        return True
    return False


def _is_date_column(col_name: str, series: pd.Series) -> bool:
    """Detect if a column likely contains dates."""
    col_lower = col_name.lower().replace("_", " ")
    if any(kw in col_lower for kw in DATE_KEYWORDS):
        return True
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    return False


def _detect_eu_decimal_format(series: pd.Series) -> int:
    """Count values that appear to use EU decimal format (1.234,56 instead of 1,234.56)."""
    if series.dtype != object:
        return 0
    count = 0
    sample = series.dropna().head(500)
    for val in sample:
        val_str = str(val).strip()
        # EU format: digits, optional dot thousands sep, comma decimal sep
        # e.g., "1.234,56" or "234,56"
        if (
            "," in val_str
            and val_str.replace(".", "")
            .replace(",", "")
            .replace("-", "")
            .replace(" ", "")
            .isdigit()
        ):
            parts = val_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                count += 1
    return count


def _detect_date_format_inconsistencies(series: pd.Series) -> int:
    """Count rows with inconsistent date formats in a date column."""
    if series.dtype != object:
        return 0
    formats_seen: set[str] = set()
    sample = series.dropna().head(500)
    for val in sample:
        val_str = str(val).strip()
        if "/" in val_str:
            parts = val_str.split("/")
            if len(parts) == 3:
                fmt = f"{len(parts[0])}{'/' if '/' in val_str else '-'}{len(parts[1])}/{len(parts[2])}"
                formats_seen.add(fmt)
        elif "-" in val_str and not val_str.startswith("-"):
            parts = val_str.split("-")
            if len(parts) == 3:
                fmt = f"{len(parts[0])}-{len(parts[1])}-{len(parts[2])}"
                formats_seen.add(fmt)
    return max(0, len(formats_seen) - 1)


def infer_column_type(col_name: str, series: pd.Series) -> str:
    """Infer the semantic type of a column."""
    if _is_date_column(col_name, series):
        return "date"
    if pd.api.types.is_numeric_dtype(series):
        if _is_financial_column(col_name, series):
            return "financial"
        return "numeric"
    if series.dtype == object:
        if _is_financial_column(col_name, series):
            return "financial"
        if _is_entity_column(col_name, series):
            return "entity"
        nunique = series.nunique()
        if nunique <= 20:
            return "categorical"
        return "text"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    return "text"


# ──────────────────────────────────────────────────────────────
# Schema Detection (Section 1)
# ──────────────────────────────────────────────────────────────


def profile_columns(df: pd.DataFrame) -> list[ColumnProfile]:
    """Generate a quality profile for every column in the dataframe."""
    profiles = []
    for col in df.columns:
        series = df[col]
        col_type = infer_column_type(col, series)
        null_count = int(series.isna().sum())
        total = len(series)

        # Sample values (first 3 non-null)
        non_null = series.dropna()
        samples = non_null.head(3).tolist() if len(non_null) > 0 else []

        # Format inconsistency detection
        format_issues = 0
        format_detail = ""
        if col_type == "date":
            format_issues = _detect_date_format_inconsistencies(series)
            if format_issues > 0:
                format_detail = f"{format_issues} different date formats detected"
        elif col_type == "financial" and series.dtype == object:
            eu_count = _detect_eu_decimal_format(series)
            if eu_count > 0:
                format_issues = eu_count
                format_detail = f"{eu_count} values use EU decimal format (comma as decimal)"

        profiles.append(
            ColumnProfile(
                name=col,
                inferred_type=col_type,
                total_rows=total,
                null_count=null_count,
                null_pct=round(null_count / total * 100, 2) if total > 0 else 0.0,
                unique_count=int(series.nunique()),
                unique_pct=round(series.nunique() / total * 100, 2) if total > 0 else 0.0,
                sample_values=samples,
                format_inconsistencies=format_issues,
                format_details=format_detail,
            )
        )
    return profiles


# ──────────────────────────────────────────────────────────────
# Quality Metrics (Section 2)
# ──────────────────────────────────────────────────────────────


def compute_completeness_score(df: pd.DataFrame) -> float:
    """Score 0–100 based on percentage of non-null cells."""
    total_cells = df.shape[0] * df.shape[1]
    if total_cells == 0:
        return 0.0
    null_cells = int(df.isna().sum().sum())
    return float(round((1 - null_cells / total_cells) * 100, 2))


def compute_consistency_score(profiles: list[ColumnProfile]) -> float:
    """Score 0–100 based on format consistency across columns."""
    if not profiles:
        return 100.0
    total_issues = sum(p.format_inconsistencies for p in profiles)
    # Penalize: each inconsistency deducts from 100, capped at 0
    penalty = min(total_issues * 2, 100)  # Each inconsistency costs 2 points
    return max(0.0, 100.0 - penalty)


def compute_uniqueness_score(df: pd.DataFrame) -> tuple[float, int, int]:
    """
    Score 0–100 based on duplicate row analysis.
    Returns (score, exact_dup_count, near_dup_count).
    """
    total = len(df)
    if total == 0:
        return 100.0, 0, 0

    # Exact duplicates
    exact_dups = int(df.duplicated(keep="first").sum())

    # Near-duplicates: rows where >90% of fields match another row
    # For performance, sample and use a hash-based approach
    near_dups = 0
    if total <= 10000:
        str_df = df.astype(str)
        for i in range(min(total, 2000)):
            row = str_df.iloc[i]
            for j in range(i + 1, min(total, i + 50)):
                other = str_df.iloc[j]
                match_pct = (row == other).sum() / len(row)
                if match_pct > 0.9:
                    near_dups += 1
    else:
        # On large datasets, estimate from sample
        sample_size = 2000
        sample_df = df.sample(n=min(sample_size, total), random_state=42).astype(str)
        for i in range(min(len(sample_df), 500)):
            row = sample_df.iloc[i]
            for j in range(i + 1, min(len(sample_df), i + 20)):
                other = sample_df.iloc[j]
                match_pct = (row == other).sum() / len(row)
                if match_pct > 0.9:
                    near_dups += 1
        # Scale estimate
        near_dups = int(near_dups * (total / sample_size))

    dup_rate = (exact_dups + near_dups) / total
    score = max(0.0, round((1 - dup_rate) * 100, 2))
    return score, exact_dups, near_dups


def compute_health_score(completeness: float, consistency: float, uniqueness: float) -> float:
    """
    Weighted composite Data Health Score (0–100).
    Weights: completeness 40%, consistency 30%, uniqueness 30%.
    """
    return round(completeness * 0.4 + consistency * 0.3 + uniqueness * 0.3, 1)


# ──────────────────────────────────────────────────────────────
# Entity Analysis (Section 3) — rapidfuzz clustering
# ──────────────────────────────────────────────────────────────


def cluster_entities(
    values: list[str],
    threshold: float = 82.0,
) -> list[EntityCluster]:
    """
    Cluster entity name variations using rapidfuzz token_sort_ratio.

    Groups values with >threshold% similarity. The most frequent variant
    in each cluster becomes the canonical name.
    """
    if not values:
        return []

    # Deduplicate while preserving order and frequency
    value_counts: dict[str, int] = defaultdict(int)
    for v in values:
        cleaned = str(v).strip()
        if cleaned and cleaned.lower() != "nan":
            value_counts[cleaned] += 1

    unique_values = list(value_counts.keys())
    if len(unique_values) <= 1:
        return []

    # Build clusters using greedy approach
    assigned: set[int] = set()
    clusters: list[EntityCluster] = []
    cluster_id = 0

    for i, val_i in enumerate(unique_values):
        if i in assigned:
            continue

        cluster_members = [val_i]
        assigned.add(i)
        scores = []

        for j, val_j in enumerate(unique_values):
            if j in assigned or j == i:
                continue
            score = fuzz.token_sort_ratio(val_i.lower(), val_j.lower())
            if score >= threshold:
                cluster_members.append(val_j)
                scores.append(score)
                assigned.add(j)

        if len(cluster_members) > 1:
            # Canonical = most frequent variant
            canonical = max(cluster_members, key=lambda v: value_counts.get(v, 0))
            avg_score = np.mean(scores) if scores else threshold

            # Confidence based on similarity score
            if avg_score >= 95:
                confidence = "high"
            elif avg_score >= 85:
                confidence = "medium"
            else:
                confidence = "low"

            clusters.append(
                EntityCluster(
                    cluster_id=cluster_id,
                    canonical=canonical,
                    variants=cluster_members,
                    confidence=confidence,
                    similarity_score=round(float(avg_score), 1),
                )
            )
            cluster_id += 1

    # Sort by number of variants (most duplicated first)
    clusters.sort(key=lambda c: len(c.variants), reverse=True)
    return clusters


def analyze_entities(df: pd.DataFrame, entity_columns: list[str]) -> list[EntityAnalysis]:
    """Run entity clustering on all detected entity columns."""
    analyses = []
    for col in entity_columns:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        raw_values = series.tolist()
        raw_unique = series.nunique()

        clusters = cluster_entities(raw_values)
        # Estimated canonical count = raw unique - duplicate entities found in clusters
        duplicate_count = sum(len(c.variants) - 1 for c in clusters)
        estimated_canonical = max(1, raw_unique - duplicate_count)

        analyses.append(
            EntityAnalysis(
                column_name=col,
                raw_unique_count=raw_unique,
                estimated_canonical_count=estimated_canonical,
                duplicate_entity_count=duplicate_count,
                clusters=clusters,
            )
        )
    return analyses


# ──────────────────────────────────────────────────────────────
# Anomaly Detection (Section 4) — IQR method
# ──────────────────────────────────────────────────────────────


def _coerce_to_numeric(series: pd.Series) -> pd.Series:
    """Attempt to coerce a series to numeric, handling EU decimal format."""
    if pd.api.types.is_numeric_dtype(series):
        return series

    # Try EU format conversion: replace dots (thousands) and commas (decimal)
    def try_parse(val: Any) -> float | None:
        if pd.isna(val):
            return np.nan
        s = str(val).strip().replace(" ", "").replace("€", "").replace("EUR", "")
        # Try EU format first (1.234,56)
        if "," in s and "." in s:
            # Check if comma is decimal separator (EU) or thousands (US)
            comma_pos = s.rfind(",")
            dot_pos = s.rfind(".")
            if comma_pos > dot_pos:
                # EU format: 1.234,56
                s = s.replace(".", "").replace(",", ".")
            # else US format: 1,234.56
            else:
                s = s.replace(",", "")
        elif "," in s:
            # Could be EU decimal: 234,56
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        try:
            return float(s)
        except (ValueError, TypeError):
            return np.nan

    return series.apply(try_parse)


def detect_anomalies(df: pd.DataFrame, financial_columns: list[str]) -> list[AnomalyAnalysis]:
    """Run IQR-based anomaly detection on all financial columns."""
    analyses = []
    for col in financial_columns:
        if col not in df.columns:
            continue

        numeric = _coerce_to_numeric(df[col])
        valid = numeric.dropna()
        if len(valid) < 10:
            continue

        mean_val = float(valid.mean())
        median_val = float(valid.median())
        std_val = float(valid.std())
        min_val = float(valid.min())
        max_val = float(valid.max())

        # IQR method
        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies: list[Anomaly] = []

        # Outliers
        outlier_mask = (valid < lower_bound) | (valid > upper_bound)
        outlier_indices = valid[outlier_mask].index.tolist()
        for idx in outlier_indices[:20]:  # Cap at 20 for performance
            val = float(valid.loc[idx])
            atype = "outlier_high" if val > upper_bound else "outlier_low"
            anomalies.append(
                Anomaly(
                    column_name=col,
                    anomaly_type=atype,
                    value=val,
                    row_index=int(idx),
                    context=f"Value €{val:,.2f} outside IQR bounds [€{lower_bound:,.2f}, €{upper_bound:,.2f}]",
                )
            )

        # Zero values
        zero_mask = valid == 0
        zero_count = int(zero_mask.sum())
        for idx in valid[zero_mask].index.tolist()[:5]:
            anomalies.append(
                Anomaly(
                    column_name=col,
                    anomaly_type="zero_value",
                    value=0.0,
                    row_index=int(idx),
                    context=f"Zero-value entry in financial column '{col}'",
                )
            )

        # Negative values
        neg_mask = valid < 0
        neg_count = int(neg_mask.sum())
        for idx in valid[neg_mask].index.tolist()[:5]:
            anomalies.append(
                Anomaly(
                    column_name=col,
                    anomaly_type="negative",
                    value=float(valid.loc[idx]),
                    row_index=int(idx),
                    context=f"Negative value €{valid.loc[idx]:,.2f} — credit, refund, or error?",
                )
            )

        analyses.append(
            AnomalyAnalysis(
                column_name=col,
                mean=round(mean_val, 2),
                median=round(median_val, 2),
                stddev=round(std_val, 2),
                min_val=round(min_val, 2),
                max_val=round(max_val, 2),
                outlier_count=int(outlier_mask.sum()),
                zero_count=zero_count,
                negative_count=neg_count,
                anomalies=anomalies,
            )
        )
    return analyses


# ──────────────────────────────────────────────────────────────
# Financial Quick-Wins / Surprise Findings (Section 5)
# ──────────────────────────────────────────────────────────────


def generate_findings(
    df: pd.DataFrame,
    entity_columns: list[str],
    financial_columns: list[str],
    entity_analyses: list[EntityAnalysis],
    anomaly_analyses: list[AnomalyAnalysis],
) -> list[Finding]:
    """Generate actionable 'Surprise Findings' quantified in euros."""
    findings: list[Finding] = []

    # ── Finding 1: Probable Duplicate Charges ──
    # Same amount + same entity + same date = likely duplicate invoice
    if financial_columns and entity_columns:
        amount_col = financial_columns[0]
        entity_col = entity_columns[0]
        numeric_amount = _coerce_to_numeric(df[amount_col])

        # Look for date columns
        date_cols = [c for c in df.columns if _is_date_column(c, df[c])]
        if date_cols:
            group_cols = [entity_col, date_cols[0]]
            temp = df[[entity_col, date_cols[0]]].copy()
            temp["__amount__"] = numeric_amount
            temp = temp.dropna(subset=["__amount__", entity_col])

            # Group by entity + date, find groups with identical amounts
            dup_charges = temp.groupby(group_cols).agg(
                count=("__amount__", "size"),
                total=("__amount__", "sum"),
                nunique=("__amount__", "nunique"),
            )
            dup_charges = dup_charges[dup_charges["count"] > 1]
            if len(dup_charges) > 0:
                # Estimate: for each group with duplicates, the excess charges
                excess_amount = 0.0
                excess_rows = 0
                for _, row in dup_charges.iterrows():
                    if row["nunique"] < row["count"]:
                        excess_rows += int(row["count"] - row["nunique"])
                        excess_amount += row["total"] * (1 - row["nunique"] / row["count"])

                if excess_amount > 0:
                    # Annualize: if data covers N months, scale to 12
                    findings.append(
                        Finding(
                            description=(
                                f"Probable duplicate charges detected: {excess_rows} entries "
                                f"with identical entity + date + amount combinations"
                            ),
                            estimated_eur_impact=round(abs(excess_amount), 2),
                            confidence="medium",
                            rows_affected=excess_rows,
                            category="duplicate_charges",
                        )
                    )

    # ── Finding 2: Pricing Spread (Inconsistent Pricing) ──
    # For each entity or product, check if the same entity pays wildly different prices
    for fin_col in financial_columns[:2]:
        for ent_col in entity_columns[:2]:
            if fin_col not in df.columns or ent_col not in df.columns:
                continue
            numeric = _coerce_to_numeric(df[fin_col])
            temp = pd.DataFrame({"entity": df[ent_col], "amount": numeric}).dropna()
            if len(temp) < 10:
                continue

            stats = temp.groupby("entity")["amount"].agg(["mean", "std", "count"])
            stats = stats[stats["count"] >= 3]  # Need at least 3 transactions
            stats["cv"] = stats["std"] / stats["mean"].replace(0, np.nan)
            high_spread = stats[stats["cv"] > 0.10]  # >10% coefficient of variation

            if len(high_spread) > 0:
                avg_spread_eur = float((high_spread["std"] * high_spread["count"]).sum())
                total_affected = int(high_spread["count"].sum())
                findings.append(
                    Finding(
                        description=(
                            f"Pricing inconsistency: {len(high_spread)} entities in '{ent_col}' "
                            f"show >10% price variation in '{fin_col}'"
                        ),
                        estimated_eur_impact=round(
                            avg_spread_eur * 0.25, 2
                        ),  # Conservative: 25% of spread is recoverable
                        confidence="medium",
                        rows_affected=total_affected,
                        category="pricing_spread",
                    )
                )
                break  # One finding per financial column
        else:
            continue
        break

    # ── Finding 3: Revenue Concentration Risk ──
    if financial_columns and entity_columns:
        fin_col = financial_columns[0]
        ent_col = entity_columns[0]
        numeric = _coerce_to_numeric(df[fin_col])
        temp = pd.DataFrame({"entity": df[ent_col], "amount": numeric}).dropna()
        if len(temp) > 0:
            entity_totals = temp.groupby("entity")["amount"].sum().sort_values(ascending=False)
            total_amount = entity_totals.sum()
            if total_amount > 0:
                top_entity_pct = float(entity_totals.iloc[0] / total_amount * 100)
                _top_10_pct = float(entity_totals.head(10).sum() / total_amount * 100)
                if top_entity_pct > 25:
                    findings.append(
                        Finding(
                            description=(
                                f"Revenue concentration risk: top entity ('{entity_totals.index[0]}') "
                                f"represents {top_entity_pct:.1f}% of total {fin_col}"
                            ),
                            estimated_eur_impact=round(float(entity_totals.iloc[0]) * 0.05, 2),
                            confidence="low",
                            rows_affected=int((temp["entity"] == entity_totals.index[0]).sum()),
                            category="concentration_risk",
                        )
                    )

    # ── Finding 4: Negative Margin Rows ──
    # Look for paired cost/revenue columns
    cost_keywords = ["coste", "cost", "gasto", "expense", "compra"]
    revenue_keywords = [
        "importe",
        "amount",
        "ingreso",
        "revenue",
        "venta",
        "precio",
        "price",
        "tarifa",
    ]

    cost_cols = [c for c in financial_columns if any(kw in c.lower() for kw in cost_keywords)]
    rev_cols = [c for c in financial_columns if any(kw in c.lower() for kw in revenue_keywords)]

    if cost_cols and rev_cols:
        cost_numeric = _coerce_to_numeric(df[cost_cols[0]])
        rev_numeric = _coerce_to_numeric(df[rev_cols[0]])
        margin = rev_numeric - cost_numeric
        negative_margin = margin[margin < 0].dropna()
        if len(negative_margin) > 0:
            loss_amount = float(abs(negative_margin.sum()))
            findings.append(
                Finding(
                    description=(
                        f"Negative-margin transactions: {len(negative_margin)} rows where "
                        f"'{rev_cols[0]}' < '{cost_cols[0]}' (revenue below cost)"
                    ),
                    estimated_eur_impact=round(loss_amount, 2),
                    confidence="high",
                    rows_affected=len(negative_margin),
                    category="negative_margin",
                )
            )

    # ── Finding 5: Outlier-driven leakage (from anomaly analysis) ──
    for aa in anomaly_analyses:
        if aa.outlier_count > 0:
            outlier_total = sum(
                abs(a.value - aa.median)
                for a in aa.anomalies
                if a.anomaly_type.startswith("outlier")
            )
            if outlier_total > 0:
                findings.append(
                    Finding(
                        description=(
                            f"Pricing anomalies in '{aa.column_name}': {aa.outlier_count} values "
                            f"deviate significantly from median (€{aa.median:,.2f})"
                        ),
                        estimated_eur_impact=round(
                            outlier_total * 0.15, 2
                        ),  # 15% assumed recoverable
                        confidence="medium",
                        rows_affected=aa.outlier_count,
                        category="pricing_spread",
                    )
                )

    # Sort by estimated impact (highest first)
    findings.sort(key=lambda f: f.estimated_eur_impact, reverse=True)

    # Keep top 5 findings
    return findings[:5]


# ──────────────────────────────────────────────────────────────
# Main Profiling Function
# ──────────────────────────────────────────────────────────────


def load_file(path: Path) -> pd.DataFrame:
    """Load an Excel or CSV file into a DataFrame."""
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        # Read all sheets and concatenate if multiple
        xls = pd.ExcelFile(path)
        if len(xls.sheet_names) == 1:
            return pd.read_excel(path, sheet_name=0)
        else:
            frames = []
            for sheet in xls.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet)
                df["__source_sheet__"] = sheet
                frames.append(df)
            return pd.concat(frames, ignore_index=True)
    elif suffix == ".csv":
        # Try UTF-8 first, fall back to latin-1
        try:
            return pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .xlsx, .xls, or .csv")


def profile_excel(path: Path) -> ProfilingReport:
    """
    Run the complete data quality profiling pipeline on any Excel/CSV file.

    This is the top-level entry point. Returns a fully populated ProfilingReport
    with all sections: schema detection, quality metrics, entity analysis,
    anomaly flagging, and financial quick-wins.

    Args:
        path: Path to the .xlsx, .xls, or .csv file.

    Returns:
        ProfilingReport with all sections populated.
    """
    start_time = time.time()

    # Load data
    df = load_file(path)
    file_size_mb = path.stat().st_size / (1024 * 1024)

    # Section 1: Schema Detection
    column_profiles = profile_columns(df)

    entity_columns = [p.name for p in column_profiles if p.inferred_type == "entity"]
    financial_columns = [p.name for p in column_profiles if p.inferred_type == "financial"]
    date_columns = [p.name for p in column_profiles if p.inferred_type == "date"]

    # Section 2: Quality Metrics
    completeness = compute_completeness_score(df)
    consistency = compute_consistency_score(column_profiles)
    uniqueness, exact_dups, near_dups = compute_uniqueness_score(df)
    health_score = compute_health_score(completeness, consistency, uniqueness)

    overall_null = 0.0
    total_cells = df.shape[0] * df.shape[1]
    if total_cells > 0:
        overall_null = round(float(df.isna().sum().sum()) / total_cells * 100, 2)

    # Section 3: Entity Analysis
    entity_analyses = analyze_entities(df, entity_columns)

    # Section 4: Anomaly Detection
    anomaly_analyses = detect_anomalies(df, financial_columns)

    # Section 5: Financial Quick-Wins
    findings = generate_findings(
        df, entity_columns, financial_columns, entity_analyses, anomaly_analyses
    )
    total_impact = sum(f.estimated_eur_impact for f in findings)

    processing_time = time.time() - start_time

    return ProfilingReport(
        file_path=str(path),
        file_size_mb=round(file_size_mb, 2),
        total_rows=len(df),
        total_columns=len(df.columns),
        processing_time_seconds=round(processing_time, 2),
        timestamp=pd.Timestamp.now().isoformat(),
        column_profiles=column_profiles,
        detected_entity_columns=entity_columns,
        detected_financial_columns=financial_columns,
        detected_date_columns=date_columns,
        data_health_score=health_score,
        completeness_score=completeness,
        consistency_score=consistency,
        uniqueness_score=uniqueness,
        overall_null_pct=overall_null,
        exact_duplicate_rows=exact_dups,
        near_duplicate_rows=near_dups,
        entity_analyses=entity_analyses,
        anomaly_analyses=anomaly_analyses,
        findings=findings,
        total_estimated_impact_eur=round(total_impact, 2),
    )


# ──────────────────────────────────────────────────────────────
# CLI Interface
# ──────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for the profiling engine."""
    parser = argparse.ArgumentParser(
        description="Yellowbird Telemetry — Data Quality Profiling Engine",
        epilog="Example: python -m src.etl.profilers.excel_profiler data/synthetic/logistics_invoices.xlsx",
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the .xlsx, .xls, or .csv file to profile",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to write JSON report (default: print to stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted report",
    )

    args = parser.parse_args()
    path = Path(args.file)

    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Profiling {path.name}...", file=sys.stderr)
    report = profile_excel(path)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report.to_json(), encoding="utf-8")
        print(f"Report written to {output_path}", file=sys.stderr)
    elif args.json:
        print(report.to_json())
    else:
        print(report.to_cli_report())


if __name__ == "__main__":
    main()
