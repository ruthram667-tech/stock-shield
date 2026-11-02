"""
ui_theme.py — StockShield Command Center
Centralized CSS injection and reusable HTML component helpers.
Call `inject_global_css()` at the top of every page (after set_page_config).
"""

import streamlit as st

# ─── Palette constants (mirrors .streamlit/config.toml) ──────────────────────
CYAN    = "#00E5FF"
EMERALD = "#10B981"
AMBER   = "#F59E0B"
CRIMSON = "#EF4444"
BG      = "#0B0F17"
SURFACE = "#111827"
TEXT    = "#F8FAFC"
MUTED   = "#94A3B8"

# ─── Master CSS ───────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Canvas ──────────────────────────────────────────────────────────────── */
.stApp {
    background-color: #0B0F17 !important;
}
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0D1322 !important;
    border-right: 1px solid rgba(0, 229, 255, 0.12) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #94A3B8 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #111827 !important;
    border: 1px solid rgba(0, 229, 255, 0.18) !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

/* ── Glass Card ──────────────────────────────────────────────────────────── */
.glass-card {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 229, 255, 0.18);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}
.glass-card:hover {
    border-color: rgba(0, 229, 255, 0.45);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
}

/* ── Header Card ─────────────────────────────────────────────────────────── */
.header-card {
    background: linear-gradient(135deg, rgba(17,24,39,0.9) 0%, rgba(13,19,34,0.95) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 229, 255, 0.22);
    border-radius: 14px;
    padding: 24px 28px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(0, 229, 255, 0.06);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.header-icon {
    font-size: 2rem;
    line-height: 1;
}
.header-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: -0.02em;
    margin: 0;
}
.header-tenant {
    font-size: 1rem;
    color: #00E5FF;
    font-weight: 600;
    margin: 0;
}
.header-subtitle {
    font-size: 0.8rem;
    color: #94A3B8;
    margin: 0;
}
.header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}

/* ── Status Pills & Badges ───────────────────────────────────────────────── */
.badge-base {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    font-family: monospace;
    white-space: nowrap;
}
.badge-cyan {
    background: rgba(0, 229, 255, 0.10);
    border: 1px solid rgba(0, 229, 255, 0.35);
    color: #00E5FF;
}
.badge-emerald {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #10B981;
}
.badge-amber {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #F59E0B;
}
.badge-crimson {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #EF4444;
}
.badge-glow-emerald {
    animation: pulse-emerald 2s infinite;
}
@keyframes pulse-emerald {
    0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
    50%       { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
}

/* ── Tenant Info Card (sidebar) ──────────────────────────────────────────── */
.tenant-card {
    background: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(0, 229, 255, 0.15);
    border-radius: 10px;
    padding: 12px 14px;
    margin: 8px 0 4px 0;
}
.tenant-card-label {
    font-size: 0.68rem;
    color: #64748B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tenant-card-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: #F8FAFC;
    margin-bottom: 8px;
}
.tenant-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.tenant-meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
}
.tenant-meta-key {
    color: #64748B;
}
.tenant-meta-val {
    font-family: monospace;
    color: #00E5FF;
    background: rgba(0, 229, 255, 0.07);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.68rem;
}
.tenant-meta-val-industry {
    font-family: monospace;
    color: #10B981;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.68rem;
}

/* ── KPI Metric Card Override ────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: rgba(17, 24, 39, 0.75) !important;
    border: 1px solid rgba(0, 229, 255, 0.15) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="metric-container"]:hover {
    border-color: rgba(0, 229, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}
div[data-testid="metric-container"] label {
    color: #94A3B8 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}

/* ── Dataframe / Tables ──────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid rgba(0, 229, 255, 0.12) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00E5FF 0%, #0099CC 100%) !important;
    color: #0B0F17 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    letter-spacing: 0.04em;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(17,24,39,0.5) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(0, 229, 255, 0.1) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: #94A3B8 !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0, 229, 255, 0.12) !important;
    color: #00E5FF !important;
    font-weight: 600 !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(17, 24, 39, 0.6) !important;
    border: 1px solid rgba(0, 229, 255, 0.12) !important;
    border-radius: 8px !important;
    color: #94A3B8 !important;
    font-size: 0.82rem !important;
}

/* ── Sidebar divider ─────────────────────────────────────────────────────── */
hr {
    border-color: rgba(0, 229, 255, 0.10) !important;
}

/* ── Section subheader ───────────────────────────────────────────────────── */
.section-header {
    font-size: 0.72rem;
    font-weight: 600;
    color: #64748B;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(0, 229, 255, 0.10);
}
</style>
"""


def inject_global_css() -> None:
    """Inject all global dark-mode Command Center styles. Call on every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ─── HTML Component Helpers ───────────────────────────────────────────────────

def badge(text: str, variant: str = "cyan") -> str:
    """Return an inline badge HTML string. variant: cyan | emerald | amber | crimson"""
    extra = " badge-glow-emerald" if variant == "emerald" else ""
    return f'<span class="badge-base badge-{variant}{extra}">{text}</span>'


def glass_card(content_html: str) -> None:
    """Render arbitrary HTML inside a glass card."""
    st.markdown(f'<div class="glass-card">{content_html}</div>', unsafe_allow_html=True)


def header_banner(
    title: str,
    tenant_name: str,
    subtitle: str,
    telemetry_online: bool = True,
    sector: str = "",
    ml_state: str = "READY",
) -> None:
    """
    Render the top 2-column glass banner with live status pills.
    All arguments are display-only strings; no session state is touched.
    """
    telem_badge = badge("● TELEMETRY ONLINE", "emerald") if telemetry_online else badge("● TELEMETRY OFFLINE", "crimson")
    sector_badge = badge(f"⬡ {sector.upper()}", "cyan") if sector else ""
    ml_color = "emerald" if ml_state in ("READY", "TRAINED") else "amber"
    ml_badge = badge(f"🧠 ML {ml_state}", ml_color)

    st.markdown(f"""
<div class="header-card">
  <div class="header-left">
    <span class="header-icon">🛡️</span>
    <p class="header-title">{title}</p>
    <p class="header-tenant">{tenant_name}</p>
    <p class="header-subtitle">{subtitle}</p>
  </div>
  <div class="header-right">
    {telem_badge}
    {sector_badge}
    {ml_badge}
  </div>
</div>
""", unsafe_allow_html=True)


def sidebar_tenant_card(tenant_name: str, tenant_id: str, industry: str) -> None:
    """
    Render the compact tenant info card in the sidebar.
    Call AFTER the selectbox so values are already resolved.
    """
    st.sidebar.markdown(f"""
<div class="tenant-card">
  <div class="tenant-card-label">Active Organization</div>
  <div class="tenant-card-name">{tenant_name}</div>
  <div class="tenant-meta">
    <div class="tenant-meta-row">
      <span class="tenant-meta-key">Tenant ID</span>
      <span class="tenant-meta-val">{tenant_id}</span>
    </div>
    <div class="tenant-meta-row">
      <span class="tenant-meta-key">Industry</span>
      <span class="tenant-meta-val-industry">{industry}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def section_header(text: str) -> None:
    """Render an uppercase muted section divider label."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


# ─── Plotly dark theme defaults ───────────────────────────────────────────────
PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(17,24,39,0.5)",
    font=dict(color="#F8FAFC", family="sans-serif"),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(0,229,255,0.15)",
        tickfont=dict(color="#94A3B8"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(0,229,255,0.15)",
        tickfont=dict(color="#94A3B8"),
    ),
    margin=dict(l=40, r=40, t=50, b=40),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(17,24,39,0.8)",
        bordercolor="rgba(0,229,255,0.2)",
        borderwidth=1,
        font=dict(color="#94A3B8"),
    ),
)

TRACE_CYAN    = "#00E5FF"
TRACE_EMERALD = "#10B981"
TRACE_AMBER   = "#F59E0B"
TRACE_CRIMSON = "#EF4444"

