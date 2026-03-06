"""Yellowbird Telemetry — Anomaly Deep-Dive Tab.

Renders per-column anomaly metrics, interactive Plotly scatter and
bar charts, and expandable anomaly data tables.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import build_anomaly_scatter, build_anomaly_type_bar
from src.common.exceptions import ProfilingError
from src.services.export_service import ProfilingReport


def render_anomaly_deepdive(report: ProfilingReport) -> None:
    """Render the Anomaly Deep-Dive tab content.

    Args:
        report: The completed profiling report.
    """
    try:
        st.markdown(
            '<div class="section-tag">Anomalías Financieras · Exploración Interactiva</div>',
            unsafe_allow_html=True,
        )

        if report.anomaly_analyses:
            for aa in report.anomaly_analyses:
                st.markdown(f"### {aa.column_name}")

                am1, am2, am3, am4 = st.columns(4)
                am1.metric("Media", f"€{aa.mean:,.2f}")
                am2.metric("Mediana", f"€{aa.median:,.2f}")
                am3.metric("Outliers", str(aa.outlier_count))
                am4.metric("Negativos", str(aa.negative_count))

                if aa.anomalies:
                    chart_col1, chart_col2 = st.columns([3, 2])

                    with chart_col1:
                        scatter_fig = build_anomaly_scatter(aa)
                        if scatter_fig:
                            st.plotly_chart(scatter_fig, use_container_width=True)

                    with chart_col2:
                        bar_fig = build_anomaly_type_bar(aa)
                        if bar_fig:
                            st.plotly_chart(bar_fig, use_container_width=True)

                    with st.expander(f"Ver {len(aa.anomalies)} anomalías detectadas (tabla)"):
                        anomaly_df = pd.DataFrame(
                            [
                                {
                                    "Tipo": a.anomaly_type.replace("_", " ").title(),
                                    "Valor (€)": a.value,
                                    "Fila": a.row_index,
                                    "Detalle": a.context,
                                }
                                for a in aa.anomalies[:20]
                            ]
                        )
                        st.dataframe(
                            anomaly_df,
                            use_container_width=True,
                            hide_index=True,
                        )

                st.divider()
        else:
            st.info("No se detectaron anomalías financieras en estos datos.")

    except ProfilingError as exc:
        st.error(
            f"Error al renderizar las anomalías: {exc}\n\n"
            "Revise que los datos financieros estén en un formato válido."
        )
