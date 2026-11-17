"""
ui_theme.py — StockShield Financilux-Inspired Warm Cream Theme
Warm beige backgrounds, glassmorphism panels, smooth rounded edges,
Inter font family, clean professional aesthetic.
"""

import streamlit as st

# ─── Palette Constants ────────────────────────────────────────────────────────
CREAM       = "#F5F0EB"       # Main background
WARM_WHITE  = "#FDFCFA"       # Card / surface
SAND        = "#E8E0D8"       # Borders
CHARCOAL    = "#2D2A26"       # Primary text
MUTED       = "#7A7570"       # Secondary text
ACCENT      = "#C8956C"       # Warm accent (copper/terracotta)
ACCENT_DARK = "#A87B55"       # Accent hover
SUCCESS     = "#5B9A6F"       # Green
WARNING     = "#D4A843"       # Amber
DANGER      = "#C7544A"       # Red
INFO        = "#6B8FA3"       # Cool blue-gray

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background-color: #F5F0EB !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #2D2A26 !important;
}

.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #2D2A26 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, div {
    color: #4A4541;
}

code {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #A87B55 !important;
    background: rgba(200, 149, 108, 0.12) !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #FDFCFA !important;
    border-right: 1px solid #E8E0D8 !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #7A7570 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* ── Glassmorphism Card ──────────────────────────────────────────────────── */
.glass-card {
    background: rgba(253, 252, 250, 0.72);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(232, 224, 216, 0.6);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(45, 42, 38, 0.06);
}

/* ── Top Console Header Bar ──────────────────────────────────────────────── */
.header-card {
    background: rgba(253, 252, 250, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid #E8E0D8;
    border-left: 4px solid #C8956C;
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 16px rgba(45, 42, 38, 0.05);
}
.header-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.header-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #2D2A26;
    letter-spacing: -0.02em;
    margin: 0;
}
.header-tenant {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #C8956C;
    font-weight: 500;
    margin: 0;
}
.header-subtitle {
    font-size: 0.82rem;
    color: #7A7570;
    margin: 0;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Status Badges ───────────────────────────────────────────────────────── */
.badge-base {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    white-space: nowrap;
}
.badge-cyan, .badge-coral {
    background: rgba(107, 143, 163, 0.12);
    border: 1px solid rgba(107, 143, 163, 0.3);
    color: #5A8092;
}
.badge-emerald {
    background: rgba(91, 154, 111, 0.12);
    border: 1px solid rgba(91, 154, 111, 0.3);
    color: #4E8A60;
}
.badge-amber {
    background: rgba(212, 168, 67, 0.12);
    border: 1px solid rgba(212, 168, 67, 0.3);
    color: #B8922E;
}
.badge-crimson {
    background: rgba(199, 84, 74, 0.12);
    border: 1px solid rgba(199, 84, 74, 0.3);
    color: #B84840;
}

/* ── Sidebar Cards ───────────────────────────────────────────────── */
.tenant-card, .user-profile-card {
    background: rgba(245, 240, 235, 0.65);
    backdrop-filter: blur(10px);
    border: 1px solid #E8E0D8;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 8px 0;
}
.tenant-card-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    color: #7A7570;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.tenant-card-name, .user-name {
    font-size: 0.92rem;
    font-weight: 600;
    color: #2D2A26;
    margin-bottom: 6px;
}
.tenant-meta-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.74rem;
    padding: 3px 0;
}
.tenant-meta-key { color: #7A7570; }
.tenant-meta-val, .tenant-meta-val-industry {
    font-family: 'Inter', sans-serif;
    color: #C8956C;
    font-size: 0.72rem;
    font-weight: 500;
}

.user-role-tag {
    display: inline-block;
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
}
.user-role-tag.manager {
    background: rgba(200, 149, 108, 0.15);
    border: 1px solid rgba(200, 149, 108, 0.35);
    color: #A87B55;
}
.user-role-tag.employee {
    background: rgba(122, 117, 112, 0.1);
    border: 1px solid rgba(122, 117, 112, 0.25);
    color: #7A7570;
}
.user-location-info {
    font-family: 'Inter', sans-serif;
    font-size: 0.74rem;
    color: #7A7570;
    background: #F5F0EB;
    border: 1px solid #E8E0D8;
    padding: 6px 12px;
    border-radius: 8px;
    margin-top: 8px;
}

/* ── KPI Metric Containers ───────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: rgba(253, 252, 250, 0.72) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid #E8E0D8 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    box-shadow: 0 2px 12px rgba(45, 42, 38, 0.04) !important;
}
div[data-testid="metric-container"] label {
    color: #7A7570 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #2D2A26 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.65rem !important;
    font-weight: 600 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.74rem !important;
}

/* ── Inputs, Buttons & Tabs ──────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div {
    background-color: #FDFCFA !important;
    color: #2D2A26 !important;
    border: 1px solid #E8E0D8 !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #C8956C !important;
    box-shadow: 0 0 0 2px rgba(200, 149, 108, 0.2) !important;
}
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    border: 1px solid #E8E0D8 !important;
    background: #FDFCFA !important;
    color: #2D2A26 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #F5F0EB !important;
    border-color: #C8956C !important;
}
.stButton > button[kind="primary"] {
    background: #2D2A26 !important;
    border-color: #2D2A26 !important;
    color: #FDFCFA !important;
}
.stButton > button[kind="primary"]:hover {
    background: #4A4541 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(253, 252, 250, 0.6) !important;
    border: 1px solid #E8E0D8 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #7A7570 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #2D2A26 !important;
    color: #FDFCFA !important;
    font-weight: 600 !important;
}

.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 0.74rem;
    font-weight: 600;
    color: #7A7570;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #E8E0D8;
}

.breadcrumbs-container {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    margin-bottom: 12px;
    background: rgba(253, 252, 250, 0.6);
    backdrop-filter: blur(8px);
    border: 1px solid #E8E0D8;
    border-radius: 20px;
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
}
.breadcrumb-item { color: #7A7570; }
.breadcrumb-separator { color: #C8C0B8; }
.breadcrumb-active { color: #C8956C; font-weight: 600; }

/* ── DataFrames ──────────────────────────────────────────────────────────── */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
details {
    border: 1px solid #E8E0D8 !important;
    border-radius: 12px !important;
    background: rgba(253, 252, 250, 0.5) !important;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {
    border-color: #E8E0D8 !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F5F0EB; }
::-webkit-scrollbar-thumb { background: #D8D0C8; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #C8C0B8; }

/* ── Login page animated element ─────────────────────────────────────────── */
@keyframes float-pulse {
    0%, 100% { transform: translateY(0) scale(1); opacity: 0.7; }
    50% { transform: translateY(-12px) scale(1.05); opacity: 1; }
}
@keyframes orbit {
    0% { transform: rotate(0deg) translateX(60px) rotate(0deg); }
    100% { transform: rotate(360deg) translateX(60px) rotate(-360deg); }
}
@keyframes spin-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
.login-animation-container {
    position: relative;
    width: 200px;
    height: 200px;
    margin: 0 auto 24px;
}
.anim-ring {
    position: absolute;
    border: 2px solid rgba(200, 149, 108, 0.2);
    border-radius: 50%;
    animation: spin-slow 20s linear infinite;
}
.anim-ring-1 { width: 180px; height: 180px; top: 10px; left: 10px; }
.anim-ring-2 { width: 140px; height: 140px; top: 30px; left: 30px; border-color: rgba(200, 149, 108, 0.12); animation-duration: 30s; animation-direction: reverse; }
.anim-ring-3 { width: 100px; height: 100px; top: 50px; left: 50px; border-color: rgba(200, 149, 108, 0.08); animation-duration: 25s; }
.anim-dot {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #C8956C;
    animation: orbit 8s linear infinite;
}
.anim-dot-1 { top: 96px; left: 96px; }
.anim-dot-2 { top: 96px; left: 96px; animation-duration: 12s; animation-direction: reverse; width: 6px; height: 6px; background: #A87B55; }
.anim-dot-3 { top: 96px; left: 96px; animation-duration: 16s; width: 5px; height: 5px; background: #D4A843; }
.anim-center {
    position: absolute;
    top: 82px;
    left: 82px;
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #C8956C, #A87B55);
    border-radius: 10px;
    animation: float-pulse 4s ease-in-out infinite;
    display: flex;
    align-items: center;
    justify-content: center;
}
.anim-center-inner {
    width: 14px;
    height: 14px;
    background: rgba(255, 255, 255, 0.4);
    border-radius: 4px;
}
</style>
"""


def inject_global_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def badge(text: str, variant: str = "cyan") -> str:
    return f'<span class="badge-base badge-{variant}">{text}</span>'


def glass_card(content_html: str) -> None:
    st.markdown(f'<div class="glass-card">{content_html}</div>', unsafe_allow_html=True)


def login_animation() -> str:
    return """
<div class="login-animation-container">
  <div class="anim-ring anim-ring-1"></div>
  <div class="anim-ring anim-ring-2"></div>
  <div class="anim-ring anim-ring-3"></div>
  <div class="anim-dot anim-dot-1"></div>
  <div class="anim-dot anim-dot-2"></div>
  <div class="anim-dot anim-dot-3"></div>
  <div class="anim-center"><div class="anim-center-inner"></div></div>
</div>
"""


def header_banner(
    title: str,
    tenant_name: str,
    subtitle: str,
    telemetry_online: bool = True,
    sector: str = "",
    ml_state: str = "READY",
) -> None:
    telem_badge = badge("Online", "emerald") if telemetry_online else badge("Standby", "crimson")
    sector_badge = badge(sector.upper(), "cyan") if sector else ""
    ml_color = "emerald" if ml_state in ("READY", "TRAINED", "LIVE") else "amber"
    ml_badge = badge(f"ML: {ml_state}", ml_color)

    st.markdown(f"""
<div class="header-card">
  <div class="header-left">
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
    st.sidebar.markdown(f"""
<div class="tenant-card">
  <div class="tenant-card-label">Organization</div>
  <div class="tenant-card-name">{tenant_name}</div>
  <div class="tenant-meta-row">
    <span class="tenant-meta-key">Tenant ID</span>
    <span class="tenant-meta-val">{tenant_id}</span>
  </div>
  <div class="tenant-meta-row">
    <span class="tenant-meta-key">Sector</span>
    <span class="tenant-meta-val-industry">{industry}</span>
  </div>
</div>
""", unsafe_allow_html=True)


def section_header(text: str) -> None:
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def render_breadcrumbs(items: list[str]) -> None:
    html_parts = []
    for i, item in enumerate(items):
        if i == len(items) - 1:
            html_parts.append(f'<span class="breadcrumb-item breadcrumb-active">{item}</span>')
        else:
            html_parts.append(f'<span class="breadcrumb-item">{item}</span>')
            html_parts.append('<span class="breadcrumb-separator">/</span>')
    st.markdown(f'<div class="breadcrumbs-container">{"".join(html_parts)}</div>', unsafe_allow_html=True)


PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#F5F0EB",
    font=dict(color="#4A4541", family="Inter, sans-serif", size=12),
    xaxis=dict(
        gridcolor="#E8E0D8",
        linecolor="#D8D0C8",
        tickfont=dict(color="#7A7570", family="Inter, sans-serif"),
    ),
    yaxis=dict(
        gridcolor="#E8E0D8",
        linecolor="#D8D0C8",
        tickfont=dict(color="#7A7570", family="Inter, sans-serif"),
    ),
    margin=dict(l=40, r=40, t=40, b=36),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(253, 252, 250, 0.9)",
        bordercolor="#E8E0D8",
        borderwidth=1,
        font=dict(color="#2D2A26", size=11),
    ),
)

TRACE_CYAN    = "#6B8FA3"
TRACE_EMERALD = "#5B9A6F"
TRACE_AMBER   = "#D4A843"
TRACE_CRIMSON = "#C7544A"
TRACE_CORAL   = "#C8956C"


def sidebar_user_profile(user: dict) -> None:
    role = user.get("role", "EMPLOYEE").upper()
    role_class = "manager" if role == "MANAGER" else "employee"
    role_label = "Facility Manager" if role == "MANAGER" else "Zone Operator"
    full_name = user.get("fullName") or user.get("username", "Operator")
    assigned_loc = user.get("assignedLocation")

    if role == "EMPLOYEE":
        st.markdown("""
        <style>
        [data-testid="stSidebarNav"] li:has(a[href*="Model_Training"]),
        [data-testid="stSidebarNav"] li:has(a[href*="Sensor_Registry"]) {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

    loc_text = "Scope: All Zones" if role == "MANAGER" else f"Zone: {(assigned_loc or 'Unassigned').capitalize()}"

    st.sidebar.markdown(f"""
<div class="user-profile-card">
  <div class="user-name">{full_name}</div>
  <span class="user-role-tag {role_class}">{role_label}</span>
  <div class="user-location-info">{loc_text}</div>
</div>
""", unsafe_allow_html=True)
