"""
Yellowbird Telemetry — Report Export Service
=============================================

Generates client-friendly HTML reports from profiling results.  This module is
Streamlit-free and produces a self-contained HTML string suitable for download
or email delivery.
"""

from __future__ import annotations

import contextlib
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.etl.profilers.excel_profiler import (  # explicit re-exports
    ProfilingReport as ProfilingReport,
)
from src.etl.profilers.excel_profiler import (
    profile_excel as profile_excel,
)


def compute_gross_revenue(
    report: ProfilingReport,
    demo_df: pd.DataFrame | None,
) -> float:
    """Derive gross revenue from the first detected financial column.

    Resolution order:

    1. If *demo_df* is provided, sum the financial column directly.
    2. Fallback: estimate as ``anomaly_analysis.mean × total_rows``
       for the matching column.
    3. If neither succeeds, return ``0.0``.

    Args:
        report: A completed profiling report.
        demo_df: The demo DataFrame, or ``None`` when a real file
            was uploaded.

    Returns:
        The estimated gross revenue in EUR.
    """
    gross_revenue = 0.0
    if not report.detected_financial_columns:
        return gross_revenue

    fin_col = report.detected_financial_columns[0]

    if demo_df is not None:
        with contextlib.suppress(Exception):
            gross_revenue = float(pd.to_numeric(demo_df[fin_col], errors="coerce").sum())

    if gross_revenue == 0.0:
        for aa in report.anomaly_analyses:
            if aa.column_name == fin_col:
                gross_revenue = aa.mean * report.total_rows
                break

    return gross_revenue


def compute_total_anomaly_count(report: ProfilingReport) -> int:
    """Count all anomalies across every anomaly analysis in *report*.

    Sums ``outlier_count + zero_count + negative_count`` for each
    financial column that was analysed.

    Args:
        report: A completed profiling report.

    Returns:
        The total number of anomalies detected.
    """
    return sum(
        aa.outlier_count + aa.zero_count + aa.negative_count for aa in report.anomaly_analyses
    )


def generate_html_report(report: ProfilingReport) -> str:
    """Generate a client-friendly HTML report from the profiling report.

    Args:
        report: A completed ``ProfilingReport`` containing column profiles,
            findings, quality scores, and metadata.

    Returns:
        A self-contained HTML document string with embedded CSS, ready to be
        served as a download or sent via email.
    """
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
        bar_color = (
            "#2F855A" if cp.null_pct < 10 else ("#C9943E" if cp.null_pct < 30 else "#C53030")
        )
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

    score_color = (
        "#2F855A"
        if report.data_health_score >= 80
        else ("#C9943E" if report.data_health_score >= 50 else "#C53030")
    )

    impact_html = ""
    if report.total_estimated_impact_eur > 0:
        impact_amount = f"{report.total_estimated_impact_eur:,.0f}"
        impact_html = (
            "<div style='text-align:center; background:#FFF5F5; "
            "border:1px solid rgba(197,48,48,0.3); border-radius:8px; "
            "padding:1.2rem; margin:1.5rem 0;'>"
            '<div style="font-family:Georgia,serif; font-size:2rem; color:#C53030;">'
            f"&euro;{impact_amount}"
            "</div>"
            "<div style='color:#A0AEC0; font-size:0.8rem; "
            "text-transform:uppercase; letter-spacing:0.12em;'>"
            "Impacto anual estimado total</div></div>"
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
        body {{ font-family: 'DM Sans', sans-serif; color: #0B132B; max-width: 800px;
               margin: 0 auto; padding: 2rem; background: #FAF7F2; }}
        h1 {{ font-family: 'DM Serif Display', Georgia, serif; font-weight: 400; }}
        h2 {{ font-family: 'DM Serif Display', Georgia, serif; font-weight: 400;
              border-bottom: 1px solid #E2E8F0; padding-bottom: 0.5rem; margin-top: 2rem; }}
        .header {{ text-align: center; padding: 2rem 0; border-bottom: 2px solid #D4AF37; margin-bottom: 2rem; }}
        .header h1 span {{ color: #D4AF37; }}
        .header .sub {{ color: #A0AEC0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.15em; }}
        .score {{ text-align: center; margin: 2rem 0; }}
        .score .number {{ font-family: 'DM Serif Display', Georgia, serif; font-size: 4rem;
                          color: {score_color}; }}
        .score .label {{ color: #A0AEC0; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.15em; }}
        .summary {{ background: rgba(212,175,55,0.08); border-left: 3px solid #D4AF37;
                    padding: 1.2rem 1.5rem; border-radius: 0 6px 6px 0; margin: 1.5rem 0;
                    font-size: 1.05rem; line-height: 1.7; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th {{ text-align: left; padding: 0.6rem 0.8rem; background: #0B132B; color: white;
              font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }}
        .meta {{ color: #A0AEC0; font-size: 0.78rem; margin-top: 2rem; text-align: center;
                 border-top: 1px solid #E2E8F0; padding-top: 1rem; }}
        .confidential {{ color: #D4AF37; font-size: 0.7rem; text-transform: uppercase;
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

    {impact_html}

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
