"""Yellowbird Telemetry — Columns Tab.

Renders the column quality table, completeness bar chart, and
key column categories (entity / financial / date).
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.components.charts import PLOTLY_LAYOUT
from app.theme import GOLD, RED_LOSS, SLATE_LIGHT, WHITE
from src.common.exceptions import ProfilingError
from src.services.export_service import ProfilingReport


def render_columns(report: ProfilingReport) -> None:
    """Render the Columns tab content.

    The completeness bar chart is constructed inline as pure
    rendering logic — it transforms report data directly into a
    Plotly figure without computing new derived metrics.

    Args:
        report: The completed profiling report.
    """
    try:
        st.markdown(
            '<div class="section-tag">Estructura de Columnas Detectada</div>',
            unsafe_allow_html=True,
        )

        col_data = []
        for cp in report.column_profiles:
            col_data.append(
                {
                    "Columna": cp.name,
                    "Tipo detectado": cp.inferred_type,
                    "% Nulos": f"{cp.null_pct:.1f}%",
                    "Valores únicos": cp.unique_count,
                    "Inconsistencias": cp.format_inconsistencies,
                    "Muestra": (str(cp.sample_values[:2]) if cp.sample_values else "—"),
                }
            )

        import pandas as pd

        st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)

        # ── Completeness bar chart ────────────────────────────
        st.markdown("**Completitud por columna:**")
        completeness_names = [cp.name for cp in report.column_profiles]
        completeness_vals = [round(100 - cp.null_pct, 1) for cp in report.column_profiles]

        fig_completeness = go.Figure(
            go.Bar(
                x=completeness_names,
                y=completeness_vals,
                marker=dict(
                    color=[
                        (GOLD if v >= 90 else (SLATE_LIGHT if v >= 70 else RED_LOSS))
                        for v in completeness_vals
                    ],
                    line=dict(width=0),
                ),
                text=[f"{v}%" for v in completeness_vals],
                textposition="auto",
                textfont=dict(color=WHITE, size=10),
            )
        )
        fig_completeness.update_layout(
            **PLOTLY_LAYOUT,
            height=320,
            yaxis=dict(
                title="Completitud (%)",
                range=[0, 105],
                gridcolor="rgba(255,255,255,0.05)",
            ),
            xaxis=dict(tickangle=-30, gridcolor="rgba(255,255,255,0.05)"),
            showlegend=False,
        )
        st.plotly_chart(fig_completeness, use_container_width=True)

        # ── Key column categories ─────────────────────────────
        st.markdown("**Columnas clave detectadas:**")
        kc1, kc2, kc3 = st.columns(3)
        with kc1:
            st.markdown(f"**Entidades:** {', '.join(report.detected_entity_columns) or '—'}")
        with kc2:
            st.markdown(f"**Financieras:** {', '.join(report.detected_financial_columns) or '—'}")
        with kc3:
            st.markdown(f"**Fechas:** {', '.join(report.detected_date_columns) or '—'}")

    except ProfilingError as exc:
        st.error(
            f"Error al renderizar el análisis de columnas: {exc}\n\n"
            "Verifique que el archivo tenga un formato tabular válido."
        )
