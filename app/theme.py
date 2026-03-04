"""
Yellowbird Telemetry — Streamlit Theme & Styling
=================================================

Brand constants and CSS injection for the audit dashboard.
Matches the landing page: navy (#0B1D3A), gold (#C9943E), DM Serif Display + DM Sans.
"""

# Brand colors
NAVY = "#0B1D3A"
NAVY_DEEP = "#06101F"
NAVY_MID = "#132B4F"
GOLD = "#C9943E"
GOLD_LIGHT = "#E5BE6F"
GOLD_PALE = "#F5E6C8"
CREAM = "#FAF7F2"
WHITE = "#FFFFFF"
SLATE = "#4A5568"
SLATE_LIGHT = "#A0AEC0"
RED_LOSS = "#C53030"
GREEN_GAIN = "#2F855A"


def get_custom_css() -> str:
    """Return the full custom CSS to inject into the Streamlit app."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,300..700&display=swap');

        /* ── Global overrides ── */
        .stApp {{
            background-color: {NAVY};
            color: {WHITE};
            font-family: 'DM Sans', -apple-system, sans-serif;
        }}

        /* Main content area */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1000px;
        }}

        /* ── Typography ── */
        h1, h2, h3 {{
            font-family: 'DM Serif Display', Georgia, serif !important;
            color: {WHITE} !important;
            font-weight: 400 !important;
        }}

        h1 {{
            font-size: 2.2rem !important;
            letter-spacing: -0.01em;
        }}

        p, li, span, div {{
            font-family: 'DM Sans', -apple-system, sans-serif;
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background-color: {NAVY_DEEP};
            border-right: 1px solid rgba(201, 148, 62, 0.15);
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {{
            color: {WHITE} !important;
        }}

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            color: {SLATE_LIGHT};
        }}

        /* ── Metrics ── */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 1rem 1.2rem;
        }}

        [data-testid="stMetricValue"] {{
            font-family: 'DM Serif Display', Georgia, serif !important;
            color: {GOLD} !important;
            font-size: 2.4rem !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {SLATE_LIGHT} !important;
            font-size: 0.8rem !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        /* ── File uploader ── */
        [data-testid="stFileUploader"] {{
            background: rgba(255, 255, 255, 0.03);
            border: 2px dashed rgba(201, 148, 62, 0.3);
            border-radius: 8px;
            padding: 1.5rem;
        }}

        [data-testid="stFileUploader"]:hover {{
            border-color: {GOLD};
            background: rgba(201, 148, 62, 0.05);
        }}

        /* ── Buttons ── */
        .stButton > button {{
            background: linear-gradient(135deg, {GOLD} 0%, #D4A853 100%) !important;
            color: {NAVY_DEEP} !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.7rem 2rem !important;
            box-shadow: 0 4px 15px rgba(201, 148, 62, 0.25) !important;
            transition: all 0.3s ease !important;
        }}

        .stButton > button:hover {{
            box-shadow: 0 8px 25px rgba(201, 148, 62, 0.4) !important;
            transform: translateY(-2px);
        }}

        /* ── Download buttons ── */
        .stDownloadButton > button {{
            background: transparent !important;
            color: {GOLD} !important;
            border: 1px solid rgba(201, 148, 62, 0.4) !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            font-size: 0.78rem !important;
        }}

        .stDownloadButton > button:hover {{
            background: rgba(201, 148, 62, 0.1) !important;
            border-color: {GOLD} !important;
        }}

        /* ── DataFrames/Tables ── */
        [data-testid="stDataFrame"] {{
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            overflow: hidden;
        }}

        /* ── Expanders ── */
        [data-testid="stExpander"] {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
        }}

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {SLATE_LIGHT};
            font-weight: 500;
            padding: 0.8rem 1.5rem;
            border-bottom: 2px solid transparent;
        }}

        .stTabs [aria-selected="true"] {{
            color: {GOLD} !important;
            border-bottom: 2px solid {GOLD} !important;
            background: transparent !important;
        }}

        /* ── Progress bar ── */
        .stProgress > div > div {{
            background-color: {GOLD} !important;
        }}

        /* ── Slider ── */
        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background-color: {GOLD} !important;
        }}

        /* ── Alerts / Info boxes ── */
        .stAlert {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
        }}

        /* ── Divider ── */
        hr {{
            border-color: rgba(201, 148, 62, 0.15) !important;
        }}

        /* ── Custom classes ── */
        .brand-header {{
            text-align: center;
            padding: 1rem 0 2rem;
            border-bottom: 1px solid rgba(201, 148, 62, 0.15);
            margin-bottom: 2rem;
        }}

        .brand-header h1 {{
            margin-bottom: 0.3rem;
        }}

        .brand-header .dot {{
            color: {GOLD};
        }}

        .brand-header .subtitle {{
            color: {SLATE_LIGHT};
            font-size: 0.85rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        .health-score-box {{
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            margin: 1rem 0;
        }}

        .health-score-number {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 5rem;
            line-height: 1;
            margin-bottom: 0.5rem;
        }}

        .health-score-label {{
            color: {SLATE_LIGHT};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
        }}

        .finding-card {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 3px solid {RED_LOSS};
            border-radius: 0 6px 6px 0;
            padding: 1.2rem 1.5rem;
            margin-bottom: 0.8rem;
        }}

        .finding-card .amount {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 1.4rem;
            color: {RED_LOSS};
        }}

        .finding-card .desc {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 0.9rem;
            margin-top: 0.3rem;
        }}

        .finding-card .meta {{
            color: {SLATE_LIGHT};
            font-size: 0.78rem;
            margin-top: 0.4rem;
        }}

        .exec-summary {{
            background: rgba(201, 148, 62, 0.08);
            border-left: 3px solid {GOLD};
            border-radius: 0 6px 6px 0;
            padding: 1.5rem 2rem;
            margin: 1.5rem 0;
            font-size: 1.05rem;
            line-height: 1.7;
            color: rgba(255, 255, 255, 0.9);
        }}

        .trust-text {{
            color: {SLATE_LIGHT};
            font-size: 0.78rem;
            text-align: center;
            padding: 0.8rem;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 4px;
            margin-top: 0.8rem;
        }}

        .section-tag {{
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: {GOLD};
            margin-bottom: 0.5rem;
        }}

        .total-impact-box {{
            text-align: center;
            background: linear-gradient(135deg, rgba(197, 48, 48, 0.1) 0%, rgba(197, 48, 48, 0.05) 100%);
            border: 1px solid rgba(197, 48, 48, 0.3);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }}

        .total-impact-box .amount {{
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 2.4rem;
            color: {RED_LOSS};
        }}

        .total-impact-box .label {{
            color: {SLATE_LIGHT};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-top: 0.3rem;
        }}
    </style>
    """


def render_header():
    """Render the branded header HTML."""
    return """
    <div class="brand-header">
        <h1>Yellowbird<span class="dot">.</span> Telemetry</h1>
        <div class="subtitle">Auditoría de Calidad de Datos</div>
    </div>
    """


def health_score_color(score: float) -> str:
    """Return a hex color based on the health score."""
    if score >= 80:
        return GREEN_GAIN
    elif score >= 50:
        return GOLD
    else:
        return RED_LOSS


def health_score_label(score: float) -> str:
    """Return a human-readable label for the health score."""
    if score >= 80:
        return "Bueno"
    elif score >= 50:
        return "Requiere atención"
    else:
        return "Crítico"


def render_health_score(score: float) -> str:
    """Render the Data Health Score as styled HTML."""
    color = health_score_color(score)
    label = health_score_label(score)
    return f"""
    <div class="health-score-box">
        <div class="health-score-number" style="color: {color};">{score:.0f}</div>
        <div class="health-score-label">{label} · Data Health Score</div>
    </div>
    """


def render_finding_card(description: str, amount: float, confidence: str, rows: int, category: str) -> str:
    """Render a single finding as a styled card."""
    conf_badge = {"high": "Alta", "medium": "Media", "low": "Baja"}.get(confidence, confidence)
    cat_label = {
        "duplicate_charges": "Cargos duplicados",
        "pricing_spread": "Inconsistencia de precios",
        "concentration_risk": "Riesgo de concentración",
        "negative_margin": "Margen negativo",
    }.get(category, category)
    return f"""
    <div class="finding-card">
        <div class="amount">€{amount:,.0f}</div>
        <div class="desc">{description}</div>
        <div class="meta">{cat_label} · Confianza: {conf_badge} · {rows:,} filas afectadas</div>
    </div>
    """


def render_total_impact(amount: float) -> str:
    """Render the total estimated impact box."""
    return f"""
    <div class="total-impact-box">
        <div class="amount">€{amount:,.0f}</div>
        <div class="label">Impacto anual estimado total</div>
    </div>
    """


def render_exec_summary(text: str) -> str:
    """Render the executive summary block."""
    return f"""
    <div class="exec-summary">
        {text}
    </div>
    """
