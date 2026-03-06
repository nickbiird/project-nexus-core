"""
Yellowbird Telemetry — Chart Components
========================================

Plotly chart construction functions for the Enterprise Audit Dashboard.
Each builder returns a fully configured ``go.Figure`` ready for display.
This module is Streamlit-free and performs no I/O.
"""

from __future__ import annotations

import plotly.graph_objects as go

from app.theme import (
    GOLD,
    GREEN_GAIN,
    RED_LOSS,
    SLATE_LIGHT,
    WHITE,
)
from src.etl.profilers.excel_profiler import Anomaly, AnomalyAnalysis, ProfilingReport

# ──────────────────────────────────────────────────────────────
# Module-level constants
# ──────────────────────────────────────────────────────────────

ANOMALY_TYPE_LABELS: dict[str, str] = {
    "outlier_high": "Outlier (High)",
    "outlier_low": "Outlier (Low)",
    "zero_value": "Zero Value",
    "negative": "Negative",
    "duplicate_invoice": "Duplicate Invoice",
}
"""Human-readable labels for anomaly type codes."""

ANOMALY_TYPE_COLORS: dict[str, str] = {
    "outlier_high": RED_LOSS,
    "outlier_low": "#F6AD55",
    "zero_value": SLATE_LIGHT,
    "negative": "#FC8181",
    "duplicate_invoice": GOLD,
}
"""Colour palette for anomaly scatter markers, keyed by anomaly type."""

PLOTLY_LAYOUT: dict[str, object] = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=WHITE),
    margin=dict(l=40, r=40, t=50, b=40),
)
"""Shared Plotly layout defaults used across all chart builders."""


# ──────────────────────────────────────────────────────────────
# Chart builders
# ──────────────────────────────────────────────────────────────


def build_waterfall_chart(report: ProfilingReport, gross_revenue: float) -> go.Figure:
    """Build a 'Kill Shot' waterfall chart showing margin leakage.

    Starts with Total Gross Revenue, deducts each finding category,
    and ends with Realized Net Margin.

    Args:
        report: The completed profiling report containing findings.
        gross_revenue: The total gross revenue in EUR.

    Returns:
        A Plotly ``go.Figure`` configured as a waterfall chart.
    """
    # Aggregate findings by category for cleaner display
    category_labels: dict[str, str] = {
        "duplicate_charges": "Duplicate Invoice Leakage",
        "pricing_spread": "Pricing Inconsistencies",
        "concentration_risk": "Concentration Risk Exposure",
        "negative_margin": "Negative-Margin Transactions",
    }
    category_impacts: dict[str, float] = {}
    for f in report.findings:
        label = category_labels.get(f.category, f.category.replace("_", " ").title())
        category_impacts[label] = category_impacts.get(label, 0) + f.estimated_eur_impact

    # Build waterfall data
    labels: list[str] = ["Total Gross Revenue"]
    values: list[float] = [gross_revenue]
    measures: list[str] = ["absolute"]

    for label, impact in category_impacts.items():
        labels.append(label)
        values.append(-abs(impact))
        measures.append("relative")

    labels.append("Realized Net Margin")
    values.append(0)  # Plotly computes the total automatically
    measures.append("total")

    fig = go.Figure(
        go.Waterfall(
            name="Margin Leakage",
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            textposition="outside",
            text=[f"€{abs(v):,.0f}" for v in values],
            connector=dict(line=dict(color=SLATE_LIGHT, width=1, dash="dot")),
            increasing=dict(marker=dict(color=GREEN_GAIN)),
            decreasing=dict(marker=dict(color=RED_LOSS)),
            totals=dict(marker=dict(color=GOLD)),
        )
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=None,
        showlegend=False,
        height=420,
        xaxis=dict(
            tickangle=-25,
            tickfont=dict(size=11),
            gridcolor="rgba(255,255,255,0.05)",
        ),
        yaxis=dict(
            title="EUR (€)",
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="€",
            separatethousands=True,
        ),
    )
    return fig


def build_anomaly_scatter(anomaly_analysis: AnomalyAnalysis) -> go.Figure | None:
    """Build an interactive scatter plot of anomalies for a column.

    Args:
        anomaly_analysis: Anomaly detection results for a single financial
            column.

    Returns:
        A Plotly ``go.Figure`` with scatter traces grouped by anomaly type,
        or ``None`` if no anomalies were detected.
    """
    if not anomaly_analysis.anomalies:
        return None

    fig = go.Figure()

    # Group anomalies by type for legend
    by_type: dict[str, list[Anomaly]] = {}
    for a in anomaly_analysis.anomalies:
        by_type.setdefault(a.anomaly_type, []).append(a)

    for atype, anomalies in by_type.items():
        fig.add_trace(
            go.Scatter(
                x=[a.row_index for a in anomalies],
                y=[a.value for a in anomalies],
                mode="markers",
                name=ANOMALY_TYPE_LABELS.get(atype, atype),
                marker=dict(
                    color=ANOMALY_TYPE_COLORS.get(atype, GOLD),
                    size=10,
                    line=dict(width=1, color="rgba(255,255,255,0.3)"),
                ),
                hovertemplate=(
                    "<b>Row %{x}</b><br>Value: €%{y:,.2f}<br><extra>%{fullData.name}</extra>"
                ),
            )
        )

    # Add median reference line
    fig.add_hline(
        y=anomaly_analysis.median,
        line_dash="dash",
        line_color=GOLD,
        annotation_text=f"Median: €{anomaly_analysis.median:,.2f}",
        annotation_font_color=GOLD,
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=f"Anomalies — {anomaly_analysis.column_name}",
            font=dict(size=14, family="DM Serif Display, Georgia, serif"),
        ),
        height=380,
        xaxis=dict(
            title="Row Index",
            gridcolor="rgba(255,255,255,0.05)",
        ),
        yaxis=dict(
            title="Value (€)",
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="€",
            separatethousands=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
    )
    return fig


def build_anomaly_type_bar(anomaly_analysis: AnomalyAnalysis) -> go.Figure | None:
    """Build a horizontal bar chart of anomaly type counts.

    Args:
        anomaly_analysis: Anomaly detection results for a single financial
            column.

    Returns:
        A Plotly ``go.Figure`` showing anomaly counts per type as horizontal
        bars, or ``None`` if no anomalies were detected.
    """
    if not anomaly_analysis.anomalies:
        return None

    counts: dict[str, int] = {}
    for a in anomaly_analysis.anomalies:
        label = ANOMALY_TYPE_LABELS.get(a.anomaly_type, a.anomaly_type)
        counts[label] = counts.get(label, 0) + 1

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(
                color=[
                    RED_LOSS if "Outlier" in lbl else (SLATE_LIGHT if "Zero" in lbl else GOLD)
                    for lbl in labels
                ],
                line=dict(width=0),
            ),
            text=values,
            textposition="auto",
            textfont=dict(color=WHITE),
        )
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text="Anomaly Distribution by Type",
            font=dict(size=14, family="DM Serif Display, Georgia, serif"),
        ),
        height=280,
        xaxis=dict(
            title="Count",
            gridcolor="rgba(255,255,255,0.05)",
        ),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        showlegend=False,
    )
    return fig
