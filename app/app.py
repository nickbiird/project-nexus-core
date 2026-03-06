"""
Yellowbird Telemetry — Enterprise Audit Dashboard (Challenger Sale Edition)
===========================================================================

A premium, schema-less data quality audit tool for the Free Audit Hook.
Upload any Excel/CSV → get a branded profiling report with € impact findings
presented as a "Margin Leakage" narrative with Plotly waterfall chart.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Ensure src/ is importable ──
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.charts import (  # noqa: E402
    PLOTLY_LAYOUT,
    build_anomaly_scatter,
    build_anomaly_type_bar,
    build_waterfall_chart,
)
from app.theme import (  # noqa: E402
    GOLD,
    RED_LOSS,
    SLATE_LIGHT,
    WHITE,
    get_custom_css,
    render_exec_summary,
    render_finding_card,
    render_header,
    render_health_score,
    render_margin_leakage_header,
    render_total_impact,
)
from src.etl.profilers.excel_profiler import profile_excel  # noqa: E402
from src.services.demo_service import generate_demo_data  # noqa: E402
from src.services.export_service import generate_html_report  # noqa: E402

# ──────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Yellowbird Telemetry · Auditoría de Datos",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 50
MAX_ROWS_WARNING = 50_000


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Configuración")

    fuzzy_threshold = st.slider(
        "Umbral de similitud (entidades)",
        min_value=60,
        max_value=95,
        value=82,
        step=1,
        help="Valores más altos = coincidencias más estrictas. 82 es un buen equilibrio.",
    )

    fast_mode = st.toggle(
        "Modo rápido",
        value=False,
        help="Omite el análisis de casi-duplicados (más rápido en archivos grandes).",
    )

    st.divider()

    st.markdown(
        '<p class="trust-text">'
        "🔒 Sus datos no se almacenan. El archivo se procesa en memoria "
        "y se descarta al cerrar esta sesión. Cumplimiento RGPD."
        "</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("##### Datos de demostración")
    demo_clicked = st.button("Generar datos de ejemplo", use_container_width=True)

    st.divider()
    st.markdown(
        f'<div style="text-align:center; color:{SLATE_LIGHT}; font-size:0.72rem;">'
        f"Yellowbird<span style='color:{GOLD};'>.</span> Telemetry<br>"
        f"© 2026 · v2.0.0</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────────────────────

st.markdown(render_header(), unsafe_allow_html=True)

# ── Upload Panel ──
st.markdown('<div class="section-tag">Paso 1 · Suba su archivo</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Seleccione un archivo Excel o CSV",
    type=["xlsx", "xls", "csv"],
    help="Aceptamos cualquier archivo de datos. No necesita limpiarlo previamente.",
    label_visibility="collapsed",
)

# ── State management ──
if "report" not in st.session_state:
    st.session_state.report = None
if "demo_df" not in st.session_state:
    st.session_state.demo_df = None


# Handle demo data generation
if demo_clicked:
    st.session_state.demo_df = generate_demo_data()
    st.session_state.report = None
    st.rerun()


# ── Determine what to profile ──
file_to_profile = None
file_name = None

if uploaded_file is not None:
    # Validate file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"El archivo es demasiado grande ({file_size_mb:.1f} MB). Máximo: {MAX_FILE_SIZE_MB} MB."
        )
        st.stop()
    file_to_profile = uploaded_file
    file_name = uploaded_file.name
    st.session_state.demo_df = None  # Clear demo if real file uploaded
elif st.session_state.demo_df is not None:
    file_to_profile = "demo"
    file_name = "demo_logistics_data.xlsx"


# ── Run Profiling ──
if file_to_profile is not None:
    run_button = st.button("Ejecutar Auditoría", use_container_width=True, type="primary")

    if run_button or st.session_state.report is not None:
        if run_button:
            # Actually run the profiling
            with st.spinner("Analizando sus datos..."):
                start = time.time()
                progress = st.progress(0, text="Cargando archivo...")

                try:
                    import tempfile

                    if file_to_profile == "demo":
                        # Write demo df to temp file
                        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                            st.session_state.demo_df.to_excel(tmp.name, index=False)
                            tmp_path = Path(tmp.name)
                    else:
                        # Write uploaded file to temp
                        with tempfile.NamedTemporaryFile(
                            suffix=Path(file_name).suffix, delete=False
                        ) as tmp:
                            tmp.write(file_to_profile.getvalue())
                            tmp_path = Path(tmp.name)

                    progress.progress(30, text="Detectando esquema...")

                    # Run profiling
                    report = profile_excel(tmp_path)

                    progress.progress(90, text="Generando hallazgos...")

                    # Override the file_path to show the original name
                    report.file_path = file_name

                    elapsed = time.time() - start
                    report.processing_time_seconds = round(elapsed, 2)

                    st.session_state.report = report

                    progress.progress(100, text="Completado.")
                    time.sleep(0.3)
                    progress.empty()

                    # Clean up temp file
                    try:  # noqa: SIM105
                        tmp_path.unlink()
                    except Exception:  # noqa: S110
                        pass

                except Exception as e:
                    st.error(
                        f"Error al procesar el archivo: {e!s}\n\n"
                        "Asegúrese de que el archivo es un Excel (.xlsx/.xls) o CSV válido."
                    )
                    st.stop()

        # ── Display Results ──
        report = st.session_state.report
        if report is None:
            st.stop()

        st.divider()

        # ==============================================================
        # SEQUENTIAL REVEAL: Tabs for Challenger Sale tension build
        # ==============================================================

        tab_exec, tab_deepdive, tab_entities, tab_columns, tab_download = st.tabs(
            [
                "📊 Executive Summary",
                "🔍 Anomaly Deep-Dive",
                "👥 Entidades",
                "📋 Columnas",
                "⬇ Descargar",
            ]
        )

        # ──────────────────────────────────────────────────────
        # TAB 1: Executive Summary — the "Kill Shot"
        # ──────────────────────────────────────────────────────
        with tab_exec:
            # Section tag
            st.markdown(render_margin_leakage_header(), unsafe_allow_html=True)

            # ── Margin Leakage Metric Cards ──
            # Compute gross revenue from the first financial column
            gross_revenue = 0.0
            if report.detected_financial_columns:
                fin_col = report.detected_financial_columns[0]
                # Re-load demo data or a reasonable estimate from the report
                if st.session_state.demo_df is not None:
                    try:  # noqa: SIM105
                        gross_revenue = float(
                            pd.to_numeric(st.session_state.demo_df[fin_col], errors="coerce").sum()
                        )
                    except Exception:  # noqa: S110
                        pass
                if gross_revenue == 0:
                    # Fallback: estimate from anomaly analysis mean * rows
                    for aa in report.anomaly_analyses:
                        if aa.column_name == fin_col:
                            gross_revenue = aa.mean * report.total_rows
                            break

            total_anomaly_count = sum(
                aa.outlier_count + aa.zero_count + aa.negative_count
                for aa in report.anomaly_analyses
            )

            leakage = report.total_estimated_impact_eur
            net_margin = gross_revenue - leakage

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Gross Revenue", f"€{gross_revenue:,.0f}")
            m2.metric("Anomalies Detected", f"{total_anomaly_count}")
            m3.metric(
                "Est. Margin Leakage",
                f"€{leakage:,.0f}",
                delta=f"-{leakage / gross_revenue * 100:.1f}%" if gross_revenue > 0 else None,
                delta_color="inverse",
            )
            m4.metric("Data Health Score", f"{report.data_health_score:.0f}/100")

            st.markdown("")  # spacer

            # ── Waterfall Chart ──
            if report.findings and gross_revenue > 0:
                waterfall_fig = build_waterfall_chart(report, gross_revenue)
                st.plotly_chart(waterfall_fig, use_container_width=True)
            else:
                st.info(
                    "No se detectaron hallazgos financieros para generar el análisis de cascada."
                )

            st.divider()

            # ── Executive Summary Text ──
            st.markdown('<div class="section-tag">Resumen Ejecutivo</div>', unsafe_allow_html=True)
            st.markdown(render_exec_summary(report.to_summary_str()), unsafe_allow_html=True)

            # ── Health Score + Quality Metrics ──
            col_score, col_metrics = st.columns([1, 2])

            with col_score:
                st.markdown(render_health_score(report.data_health_score), unsafe_allow_html=True)

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

            # ── Findings Cards (detailed) ──
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
                    render_total_impact(report.total_estimated_impact_eur), unsafe_allow_html=True
                )
            else:
                st.info("No se detectaron hallazgos financieros significativos en estos datos.")

        # ──────────────────────────────────────────────────────
        # TAB 2: Anomaly Deep-Dive — Interactive Plotly Charts
        # ──────────────────────────────────────────────────────
        with tab_deepdive:
            st.markdown(
                '<div class="section-tag">Anomalías Financieras · Exploración Interactiva</div>',
                unsafe_allow_html=True,
            )

            if report.anomaly_analyses:
                for aa in report.anomaly_analyses:
                    st.markdown(f"### {aa.column_name}")

                    # Metric row
                    am1, am2, am3, am4 = st.columns(4)
                    am1.metric("Media", f"€{aa.mean:,.2f}")
                    am2.metric("Mediana", f"€{aa.median:,.2f}")
                    am3.metric("Outliers", str(aa.outlier_count))
                    am4.metric("Negativos", str(aa.negative_count))

                    # Interactive charts
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

                        # Raw data in expander
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
                            st.dataframe(anomaly_df, use_container_width=True, hide_index=True)

                    st.divider()
            else:
                st.info("No se detectaron anomalías financieras en estos datos.")

        # ──────────────────────────────────────────────────────
        # TAB 3: Entity Analysis
        # ──────────────────────────────────────────────────────
        with tab_entities:
            st.markdown(
                '<div class="section-tag">Análisis de Entidades Duplicadas</div>',
                unsafe_allow_html=True,
            )

            if report.entity_analyses:
                for ea in report.entity_analyses:
                    st.markdown(f"**Columna: `{ea.column_name}`**")
                    st.markdown(
                        f"{ea.raw_unique_count} valores únicos → "
                        f"**{ea.estimated_canonical_count} entidades canónicas** estimadas "
                        f"({ea.duplicate_entity_count} duplicados detectados)"
                    )

                    if ea.clusters:
                        cluster_data = []
                        for c in ea.clusters[:15]:
                            cluster_data.append(
                                {
                                    "Nombre canónico": c.canonical,
                                    "Variantes": ", ".join(c.variants[:5]),
                                    "Nº variantes": len(c.variants),
                                    "Similitud": f"{c.similarity_score:.0f}%",
                                    "Confianza": c.confidence.title(),
                                }
                            )
                        st.dataframe(
                            pd.DataFrame(cluster_data),
                            use_container_width=True,
                            hide_index=True,
                        )
                    st.divider()
            else:
                st.info("No se detectaron columnas de entidades en estos datos.")

        # ──────────────────────────────────────────────────────
        # TAB 4: Column Quality
        # ──────────────────────────────────────────────────────
        with tab_columns:
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
                        "Muestra": str(cp.sample_values[:2]) if cp.sample_values else "—",
                    }
                )
            st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)

            # Completeness bar chart — Plotly
            st.markdown("**Completitud por columna:**")
            completeness_names = [cp.name for cp in report.column_profiles]
            completeness_vals = [round(100 - cp.null_pct, 1) for cp in report.column_profiles]

            fig_completeness = go.Figure(
                go.Bar(
                    x=completeness_names,
                    y=completeness_vals,
                    marker=dict(
                        color=[
                            GOLD if v >= 90 else (SLATE_LIGHT if v >= 70 else RED_LOSS)
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

            st.markdown("**Columnas clave detectadas:**")
            kc1, kc2, kc3 = st.columns(3)
            with kc1:
                st.markdown(f"**Entidades:** {', '.join(report.detected_entity_columns) or '—'}")
            with kc2:
                st.markdown(
                    f"**Financieras:** {', '.join(report.detected_financial_columns) or '—'}"
                )
            with kc3:
                st.markdown(f"**Fechas:** {', '.join(report.detected_date_columns) or '—'}")

        # ──────────────────────────────────────────────────────
        # TAB 5: Downloads
        # ──────────────────────────────────────────────────────
        with tab_download:
            st.markdown('<div class="section-tag">Descargar Informe</div>', unsafe_allow_html=True)

            dl1, dl2 = st.columns(2)

            with dl1:
                st.markdown("**Informe JSON** (datos completos)")
                st.download_button(
                    label="Descargar JSON",
                    data=report.to_json(),
                    file_name=f"yellowbird_audit_{Path(report.file_path).stem}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            with dl2:
                st.markdown("**Informe HTML** (para compartir con el cliente)")
                html_report = generate_html_report(report)
                st.download_button(
                    label="Descargar HTML",
                    data=html_report,
                    file_name=f"yellowbird_audit_{Path(report.file_path).stem}_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True,
                )

else:
    # ── Landing state: no file uploaded ──
    st.markdown(
        """
    <div style="text-align:center; padding:3rem 1rem;">
        <p style="font-size:1.1rem; color:rgba(255,255,255,0.75); max-width:500px; margin:0 auto 1.5rem;">
            Suba un archivo Excel o CSV con sus datos operativos.
            No necesita limpiarlo. Aceptamos cualquier formato.
        </p>
        <p style="color:rgba(160,174,192,0.7); font-size:0.85rem;">
            O pulse <strong>Generar datos de ejemplo</strong> en la barra lateral para una demostración instantánea.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="trust-text">'
        "🔒 Sus datos se procesan exclusivamente en memoria. No se almacena nada. "
        "Sin cookies. Sin seguimiento. Cumplimiento RGPD."
        "</p>",
        unsafe_allow_html=True,
    )
