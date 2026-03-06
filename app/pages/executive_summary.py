"""Yellowbird Telemetry — Executive Summary Tab.

Renders the "Kill Shot" margin-leakage dashboard: metric cards,
waterfall chart, executive summary text, health score, quality
metrics, and detailed finding cards.
"""

from __future__ import annotations

import streamlit as st

from app.components.charts import build_waterfall_chart
from app.theme import (
    render_exec_summary,
    render_finding_card,
    render_health_score,
    render_margin_leakage_header,
    render_total_impact,
)
from src.common.exceptions import ProfilingError
from src.services.export_service import ProfilingReport


def render_executive_summary(
    report: ProfilingReport,
    gross_revenue: float,
    total_anomaly_count: int,
) -> None:
    """Render the Executive Summary tab content.

    All values are pre-computed; this function only emits widgets.

    Args:
        report: The completed profiling report.
        gross_revenue: Pre-computed gross revenue in EUR.
        total_anomaly_count: Pre-computed total anomaly count.
    """
    try:
        st.markdown(render_margin_leakage_header(), unsafe_allow_html=True)

        # ── Margin Leakage Metric Cards ───────────────────────
        leakage = report.total_estimated_impact_eur
        net_margin = gross_revenue - leakage  # noqa: F841

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Gross Revenue", f"€{gross_revenue:,.0f}")
        m2.metric("Anomalies Detected", f"{total_anomaly_count}")
        m3.metric(
            "Est. Margin Leakage",
            f"€{leakage:,.0f}",
            delta=(f"-{leakage / gross_revenue * 100:.1f}%" if gross_revenue > 0 else None),
            delta_color="inverse",
        )
        m4.metric("Data Health Score", f"{report.data_health_score:.0f}/100")

        st.markdown("")  # spacer

        # ── Waterfall Chart ───────────────────────────────────
        if report.findings and gross_revenue > 0:
            waterfall_fig = build_waterfall_chart(report, gross_revenue)
            st.plotly_chart(waterfall_fig, use_container_width=True)
        else:
            st.info("No se detectaron hallazgos financieros para generar el análisis de cascada.")

        st.divider()

        # ── Executive Summary Text ────────────────────────────
        st.markdown(
            '<div class="section-tag">Resumen Ejecutivo</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            render_exec_summary(report.to_summary_str()),
            unsafe_allow_html=True,
        )

        # ── Health Score + Quality Metrics ─────────────────────
        col_score, col_metrics = st.columns([1, 2])

        with col_score:
            st.markdown(
                render_health_score(report.data_health_score),
                unsafe_allow_html=True,
            )

        with col_metrics:
            q1, q2, q3 = st.columns(3)
            q1.metric("Completitud", f"{report.completeness_score:.0f}/100")
            q2.metric("Consistencia", f"{report.consistency_score:.0f}/100")
            q3.metric("Unicidad", f"{report.uniqueness_score:.0f}/100")

            q4, q5, q6 = st.columns(3)
            q4.metric("Filas", f"{report.total_rows:,}")
            q5.metric("Columnas", f"{report.total_columns}")
            q6.metric("Tiempo", f"{report.processing_time_seconds:.1f}s")

        st.divider()

        # ── Findings Cards ────────────────────────────────────
        st.markdown(
            '<div class="section-tag">Hallazgos Clave · Impacto en Euros</div>',
            unsafe_allow_html=True,
        )

        if report.findings:
            for f in report.findings:
                st.markdown(
                    render_finding_card(
                        f.description,
                        f.estimated_eur_impact,
                        f.confidence,
                        f.rows_affected,
                        f.category,
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown(
                render_total_impact(report.total_estimated_impact_eur),
                unsafe_allow_html=True,
            )
        else:
            st.info("No se detectaron hallazgos financieros significativos en estos datos.")

    except ProfilingError as exc:
        st.error(
            f"Error al renderizar el resumen ejecutivo: {exc}\n\n"
            "Se muestran los datos parciales disponibles."
        )
