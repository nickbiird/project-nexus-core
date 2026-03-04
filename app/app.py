"""
Yellowbird Telemetry — Audit Dashboard (Streamlit MVP)
======================================================

A premium, schema-less data quality audit tool for the Free Audit Hook.
Upload any Excel/CSV → get a branded profiling report with € impact findings.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ── Ensure src/ is importable ──
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.theme import (
    GOLD,
    NAVY,
    RED_LOSS,
    SLATE_LIGHT,
    GREEN_GAIN,
    get_custom_css,
    health_score_color,
    render_exec_summary,
    render_finding_card,
    render_header,
    render_health_score,
    render_total_impact,
)
from src.etl.profilers.excel_profiler import ProfilingReport, profile_excel

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
# Helper: Generate sample data for demo
# ──────────────────────────────────────────────────────────────


def generate_demo_data() -> pd.DataFrame:
    """Generate a small synthetic logistics dataset for instant demos."""
    np.random.seed(42)
    n = 200

    suppliers = [
        "Transportes Garcia S.L.", "Trans. Garcia", "GARCIA SL",
        "Transportes Martinez S.L.", "Martínez S.L.", "Martnez SL",
        "Logística Pérez S.A.", "Logistica Perez",
        "Iberlogística S.L.", "Mediterráneo Transport",
    ]
    routes = ["BCN-MAD", "BCN-VAL", "MAD-SEV", "BCN-ZAR", "MAD-BIL", "VAL-MAL"]
    dates_fmt = [
        lambda: f"{np.random.randint(1,28):02d}/{np.random.randint(1,12):02d}/2025",
        lambda: f"2025-{np.random.randint(1,12):02d}-{np.random.randint(1,28):02d}",
        lambda: f"{np.random.randint(1,12):02d}-{np.random.randint(1,28):02d}-2025",
    ]

    data = {
        "numero_factura": [f"FAC-{i:04d}" for i in range(n)],
        "proveedor": [suppliers[np.random.randint(0, len(suppliers))] for _ in range(n)],
        "fecha_factura": [dates_fmt[np.random.randint(0, 3)]() for _ in range(n)],
        "ruta": [routes[np.random.randint(0, len(routes))] for _ in range(n)],
        "importe_total": np.round(np.random.lognormal(7.5, 0.6, n), 2).tolist(),
        "coste_operativo": np.round(np.random.lognormal(7.3, 0.5, n), 2).tolist(),
        "peso_kg": [
            None if np.random.random() < 0.15 else int(np.random.uniform(500, 5000))
            for _ in range(n)
        ],
    }

    # Inject anomalies
    data["importe_total"][5] = 95000.0  # High outlier
    data["importe_total"][42] = 0.0     # Zero
    data["importe_total"][88] = -500.0  # Negative
    data["coste_operativo"][10] = data["importe_total"][10] + 500  # Negative margin

    # Inject duplicate invoices
    data["numero_factura"][150] = "FAC-0005"

    df = pd.DataFrame(data)
    return df


# ──────────────────────────────────────────────────────────────
# Helper: Generate HTML report for download
# ──────────────────────────────────────────────────────────────


def generate_html_report(report: ProfilingReport) -> str:
    """Generate a client-friendly HTML report from the profiling report."""
    findings_html = ""
    for f in report.findings:
        cat_label = {
            "duplicate_charges": "Cargos duplicados",
            "pricing_spread": "Inconsistencia de precios",
            "concentration_risk": "Riesgo de concentración",
            "negative_margin": "Margen negativo",
        }.get(f.category, f.category)
        findings_html += f"""
        <div style="background:#FFF5F5; border-left:3px solid #C53030; padding:1rem 1.5rem;
                     margin-bottom:0.8rem; border-radius:0 6px 6px 0;">
            <div style="font-family:Georgia,serif; font-size:1.3rem; color:#C53030;">
                €{f.estimated_eur_impact:,.0f}
            </div>
            <div style="margin-top:0.3rem; font-size:0.9rem;">{f.description}</div>
            <div style="color:#718096; font-size:0.78rem; margin-top:0.3rem;">
                {cat_label} · Confianza: {f.confidence.title()} · {f.rows_affected:,} filas
            </div>
        </div>
        """

    columns_html = ""
    for cp in report.column_profiles:
        bar_color = "#2F855A" if cp.null_pct < 10 else ("#C9943E" if cp.null_pct < 30 else "#C53030")
        columns_html += f"""
        <tr>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{cp.name}</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{cp.inferred_type}</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">
                <div style="background:#EDF2F7; border-radius:3px; height:16px; width:100px;">
                    <div style="background:{bar_color}; border-radius:3px; height:16px;
                                width:{max(2, 100 - cp.null_pct)}px;"></div>
                </div>
                {100 - cp.null_pct:.0f}% completo
            </td>
        </tr>
        """

    score_color = "#2F855A" if report.data_health_score >= 80 else (
        "#C9943E" if report.data_health_score >= 50 else "#C53030"
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yellowbird Telemetry — Informe de Auditoría de Datos</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;600;700&display=swap"
          rel="stylesheet">
    <style>
        body {{ font-family: 'DM Sans', sans-serif; color: #0B1D3A; max-width: 800px;
               margin: 0 auto; padding: 2rem; background: #FAF7F2; }}
        h1 {{ font-family: 'DM Serif Display', Georgia, serif; font-weight: 400; }}
        h2 {{ font-family: 'DM Serif Display', Georgia, serif; font-weight: 400;
              border-bottom: 1px solid #E2E8F0; padding-bottom: 0.5rem; margin-top: 2rem; }}
        .header {{ text-align: center; padding: 2rem 0; border-bottom: 2px solid #C9943E; margin-bottom: 2rem; }}
        .header h1 span {{ color: #C9943E; }}
        .header .sub {{ color: #A0AEC0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.15em; }}
        .score {{ text-align: center; margin: 2rem 0; }}
        .score .number {{ font-family: 'DM Serif Display', Georgia, serif; font-size: 4rem;
                          color: {score_color}; }}
        .score .label {{ color: #A0AEC0; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.15em; }}
        .summary {{ background: rgba(201,148,62,0.08); border-left: 3px solid #C9943E;
                    padding: 1.2rem 1.5rem; border-radius: 0 6px 6px 0; margin: 1.5rem 0;
                    font-size: 1.05rem; line-height: 1.7; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th {{ text-align: left; padding: 0.6rem 0.8rem; background: #0B1D3A; color: white;
              font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }}
        .meta {{ color: #A0AEC0; font-size: 0.78rem; margin-top: 2rem; text-align: center;
                 border-top: 1px solid #E2E8F0; padding-top: 1rem; }}
        .confidential {{ color: #C9943E; font-size: 0.7rem; text-transform: uppercase;
                        letter-spacing: 0.2em; text-align: center; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <div class="confidential">Confidencial — Preparado exclusivamente para el cliente</div>
    <div class="header">
        <h1>Yellowbird<span>.</span> Telemetry</h1>
        <div class="sub">Informe de Auditoría de Calidad de Datos</div>
    </div>

    <div class="score">
        <div class="number">{report.data_health_score:.0f}</div>
        <div class="label">Data Health Score (0–100)</div>
    </div>

    <div class="summary">{report.to_summary_str()}</div>

    <p style="color:#718096; font-size:0.85rem;">
        Archivo: {Path(report.file_path).name} · {report.total_rows:,} filas · {report.total_columns} columnas
        · Procesado en {report.processing_time_seconds:.1f}s
    </p>

    <h2>Hallazgos Clave</h2>
    {findings_html if findings_html else '<p style="color:#718096;">No se detectaron hallazgos significativos.</p>'}

    {"<div style='text-align:center; background:#FFF5F5; border:1px solid rgba(197,48,48,0.3); border-radius:8px; padding:1.2rem; margin:1.5rem 0;'><div style=\"font-family:Georgia,serif; font-size:2rem; color:#C53030;\">€" + f"{report.total_estimated_impact_eur:,.0f}" + "</div><div style='color:#A0AEC0; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.12em;'>Impacto anual estimado total</div></div>" if report.total_estimated_impact_eur > 0 else ""}

    <h2>Estructura de Columnas Detectada</h2>
    <table>
        <tr><th>Columna</th><th>Tipo Detectado</th><th>Completitud</th></tr>
        {columns_html}
    </table>

    <h2>Métricas de Calidad</h2>
    <table>
        <tr><th>Métrica</th><th>Valor</th></tr>
        <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">Completitud</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{report.completeness_score:.0f}/100</td></tr>
        <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">Consistencia</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{report.consistency_score:.0f}/100</td></tr>
        <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">Unicidad</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{report.uniqueness_score:.0f}/100</td></tr>
        <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">Tasa de nulos global</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{report.overall_null_pct:.1f}%</td></tr>
        <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">Filas duplicadas exactas</td>
            <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EDF2F7;">{report.exact_duplicate_rows:,}</td></tr>
    </table>

    <div class="meta">
        Generado por Yellowbird Telemetry · {datetime.now().strftime("%d/%m/%Y %H:%M")}
        · Este informe es confidencial y está destinado exclusivamente al propietario de los datos analizados.
    </div>
</body>
</html>"""


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
        f"© 2026 · v1.0.0</div>",
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
        st.error(f"El archivo es demasiado grande ({file_size_mb:.1f} MB). Máximo: {MAX_FILE_SIZE_MB} MB.")
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
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass

                except Exception as e:
                    st.error(
                        f"Error al procesar el archivo: {str(e)}\n\n"
                        "Asegúrese de que el archivo es un Excel (.xlsx/.xls) o CSV válido."
                    )
                    st.stop()

        # ── Display Results ──
        report = st.session_state.report
        if report is None:
            st.stop()

        st.divider()

        # ── Section: Executive Summary ──
        st.markdown('<div class="section-tag">Resumen Ejecutivo</div>', unsafe_allow_html=True)
        st.markdown(render_exec_summary(report.to_summary_str()), unsafe_allow_html=True)

        # ── Section: Health Score + Key Metrics ──
        col_score, col_metrics = st.columns([1, 2])

        with col_score:
            st.markdown(render_health_score(report.data_health_score), unsafe_allow_html=True)

        with col_metrics:
            m1, m2, m3 = st.columns(3)
            m1.metric("Completitud", f"{report.completeness_score:.0f}/100")
            m2.metric("Consistencia", f"{report.consistency_score:.0f}/100")
            m3.metric("Unicidad", f"{report.uniqueness_score:.0f}/100")

            m4, m5, m6 = st.columns(3)
            m4.metric("Filas", f"{report.total_rows:,}")
            m5.metric("Columnas", f"{report.total_columns}")
            m6.metric("Tiempo", f"{report.processing_time_seconds:.1f}s")

        st.divider()

        # ── Section: Tabs ──
        tab_findings, tab_entities, tab_anomalies, tab_columns, tab_download = st.tabs([
            "Hallazgos (€)", "Entidades", "Anomalías", "Columnas", "Descargar"
        ])

        # ── Tab: Findings ──
        with tab_findings:
            st.markdown('<div class="section-tag">Hallazgos Clave · Impacto en Euros</div>', unsafe_allow_html=True)

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

                st.markdown(render_total_impact(report.total_estimated_impact_eur), unsafe_allow_html=True)

                # Findings as DataFrame for easy reading
                with st.expander("Ver como tabla"):
                    findings_df = pd.DataFrame([
                        {
                            "Hallazgo": f.description,
                            "Impacto (€)": f"€{f.estimated_eur_impact:,.0f}",
                            "Confianza": f.confidence.title(),
                            "Filas": f.rows_affected,
                            "Categoría": f.category,
                        }
                        for f in report.findings
                    ])
                    st.dataframe(findings_df, use_container_width=True, hide_index=True)
            else:
                st.info("No se detectaron hallazgos financieros significativos en estos datos.")

        # ── Tab: Entities ──
        with tab_entities:
            st.markdown('<div class="section-tag">Análisis de Entidades Duplicadas</div>', unsafe_allow_html=True)

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
                            cluster_data.append({
                                "Nombre canónico": c.canonical,
                                "Variantes": ", ".join(c.variants[:5]),
                                "Nº variantes": len(c.variants),
                                "Similitud": f"{c.similarity_score:.0f}%",
                                "Confianza": c.confidence.title(),
                            })
                        st.dataframe(
                            pd.DataFrame(cluster_data),
                            use_container_width=True,
                            hide_index=True,
                        )
                    st.divider()
            else:
                st.info("No se detectaron columnas de entidades en estos datos.")

        # ── Tab: Anomalies ──
        with tab_anomalies:
            st.markdown('<div class="section-tag">Anomalías Financieras Detectadas</div>', unsafe_allow_html=True)

            if report.anomaly_analyses:
                for aa in report.anomaly_analyses:
                    st.markdown(f"**Columna: `{aa.column_name}`**")

                    am1, am2, am3, am4 = st.columns(4)
                    am1.metric("Media", f"€{aa.mean:,.2f}")
                    am2.metric("Mediana", f"€{aa.median:,.2f}")
                    am3.metric("Outliers", str(aa.outlier_count))
                    am4.metric("Negativos", str(aa.negative_count))

                    # Simple boxplot-like visualization using a bar chart of anomaly types
                    if aa.anomalies:
                        anomaly_df = pd.DataFrame([
                            {
                                "Tipo": a.anomaly_type.replace("_", " ").title(),
                                "Valor (€)": a.value,
                                "Fila": a.row_index,
                                "Detalle": a.context,
                            }
                            for a in aa.anomalies[:20]
                        ])

                        with st.expander(f"Ver {len(aa.anomalies)} anomalías detectadas"):
                            st.dataframe(anomaly_df, use_container_width=True, hide_index=True)

                    st.divider()
            else:
                st.info("No se detectaron anomalías financieras en estos datos.")

        # ── Tab: Columns ──
        with tab_columns:
            st.markdown('<div class="section-tag">Estructura de Columnas Detectada</div>', unsafe_allow_html=True)

            col_data = []
            for cp in report.column_profiles:
                col_data.append({
                    "Columna": cp.name,
                    "Tipo detectado": cp.inferred_type,
                    "% Nulos": f"{cp.null_pct:.1f}%",
                    "Valores únicos": cp.unique_count,
                    "Inconsistencias": cp.format_inconsistencies,
                    "Muestra": str(cp.sample_values[:2]) if cp.sample_values else "—",
                })
            st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)

            # Missing data heatmap (simplified as bar chart)
            st.markdown("**Completitud por columna:**")
            completeness_data = pd.DataFrame({
                "Columna": [cp.name for cp in report.column_profiles],
                "Completitud (%)": [round(100 - cp.null_pct, 1) for cp in report.column_profiles],
            })
            st.bar_chart(
                completeness_data.set_index("Columna"),
                color=GOLD,
                height=300,
            )

            st.markdown("**Columnas clave detectadas:**")
            kc1, kc2, kc3 = st.columns(3)
            with kc1:
                st.markdown(f"**Entidades:** {', '.join(report.detected_entity_columns) or '—'}")
            with kc2:
                st.markdown(f"**Financieras:** {', '.join(report.detected_financial_columns) or '—'}")
            with kc3:
                st.markdown(f"**Fechas:** {', '.join(report.detected_date_columns) or '—'}")

        # ── Tab: Downloads ──
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
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem;">
        <p style="font-size:1.1rem; color:rgba(255,255,255,0.75); max-width:500px; margin:0 auto 1.5rem;">
            Suba un archivo Excel o CSV con sus datos operativos.
            No necesita limpiarlo. Aceptamos cualquier formato.
        </p>
        <p style="color:rgba(160,174,192,0.7); font-size:0.85rem;">
            O pulse <strong>Generar datos de ejemplo</strong> en la barra lateral para una demostración instantánea.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<p class="trust-text">'
        "🔒 Sus datos se procesan exclusivamente en memoria. No se almacena nada. "
        "Sin cookies. Sin seguimiento. Cumplimiento RGPD."
        "</p>",
        unsafe_allow_html=True,
    )
