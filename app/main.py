"""Yellowbird Telemetry — Enterprise Audit Dashboard (Challenger Sale Edition).

A premium, schema-less data quality audit tool for the Free Audit Hook.
Upload any Excel/CSV → get a branded profiling report with € impact findings
presented as a "Margin Leakage" narrative with Plotly waterfall chart.

Run: streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ── Ensure src/ is importable ──
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Logging & Sentry (before any Streamlit widget) ──
from src.common.config.settings import get_settings  # noqa: E402
from src.common.logging import configure_logging  # noqa: E402

configure_logging()

_settings = get_settings()
if _settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=_settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment=_settings.app_env,
    )

from app.pages.anomaly_deepdive import render_anomaly_deepdive  # noqa: E402
from app.pages.columns import render_columns  # noqa: E402
from app.pages.downloads import render_downloads  # noqa: E402
from app.pages.entities import render_entities  # noqa: E402
from app.pages.executive_summary import render_executive_summary  # noqa: E402
from app.pages.sidebar import render_sidebar  # noqa: E402
from app.state import AppState  # noqa: E402
from app.theme import get_custom_css  # noqa: E402

# ── Page Config ──
st.set_page_config(
    page_title="Yellowbird Telemetry · Auditoría de Datos",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── State + Sidebar ──
state = AppState()
render_sidebar(state)

# ── Tab Layout ──
if state.has_report():
    report = state.get_report()
    assert report is not None  # guarded by has_report()

    st.divider()

    tab_exec, tab_deep, tab_ent, tab_col, tab_dl = st.tabs(
        [
            "📊 Executive Summary",
            "🔍 Anomaly Deep-Dive",
            "👥 Entidades",
            "📋 Columnas",
            "⬇ Descargar",
        ]
    )

    with tab_exec:
        render_executive_summary(report, state.get_gross_revenue(), state.get_total_anomaly_count())
    with tab_deep:
        render_anomaly_deepdive(report)
    with tab_ent:
        render_entities(report)
    with tab_col:
        render_columns(report)
    with tab_dl:
        render_downloads(report)
