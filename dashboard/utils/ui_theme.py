"""
ui_theme.py — StockShield Financilux Command Center
Warm cream glassmorphism, clean typography, coral accents & dual-role styling.
Call `inject_global_css()` at the top of every page (after set_page_config).
"""

import streamlit as st

# ─── Palette constants (Financilux Aesthetic) ──────────────────────────────────
CORAL   = "#FF5520"
EMERALD = "#059669"
AMBER   = "#D97706"
CRIMSON = "#DC2626"
CYAN    = "#0284C7"
BG      = "#F5F3EF"
SURFACE = "rgba(255, 255, 255, 0.78)"
TEXT    = "#141416"
MUTED   = "#6B7280"

# ─── Master CSS ───────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

/* ── Canvas ──────────────────────────────────────────────────────────────── */
.stApp {
    background-color: #F5F3EF !important;
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
    color: #141416 !important;
}

/* Subtle architectural grid pattern */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(255, 85, 32, 0.03) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(2, 132, 199, 0.03) 0%, transparent 40%),
        linear-gradient(to right, rgba(0,0,0,0.02) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0,0,0,0.02) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 48px 48px, 48px 48px;
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
    position: relative;
    z-index: 1;
}

/* ── Typography Override ─────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    color: #141416 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, div {
    color: #141416;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.03) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #4B5563 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
}

section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    color: #141416 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}

/* ── Glass Card ──────────────────────────────────────────────────────────── */
.glass-card {
    background: rgba(255, 255, 255, 0.80);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 0, 0, 0.07);
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
    margin-bottom: 1.25rem;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.glass-card:hover {
    border-color: rgba(255, 85, 32, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.06);
}

/* ── Header Card ─────────────────────────────────────────────────────────── */
.header-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 246, 241, 0.92) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 18px;
    padding: 24px 28px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
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
    font-weight: 800;
    color: #141416;
    letter-spacing: -0.03em;
    margin: 0;
}
.header-tenant {
    font-size: 1rem;
    color: #FF5520;
    font-weight: 700;
    margin: 0;
}
.header-subtitle {
    font-size: 0.85rem;
    color: #6B7280;
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
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    font-family: 'Space Grotesk', monospace;
    white-space: nowrap;
}
.badge-cyan {
    background: rgba(2, 132, 199, 0.10);
    border: 1px solid rgba(2, 132, 199, 0.3);
    color: #0284C7;
}
.badge-emerald {
    background: rgba(5, 150, 105, 0.10);
    border: 1px solid rgba(5, 150, 105, 0.3);
    color: #059669;
}
.badge-amber {
    background: rgba(217, 119, 6, 0.10);
    border: 1px solid rgba(217, 119, 6, 0.3);
    color: #D97706;
}
.badge-crimson {
    background: rgba(220, 38, 38, 0.10);
    border: 1px solid rgba(220, 38, 38, 0.3);
    color: #DC2626;
}
.badge-coral {
    background: rgba(255, 85, 32, 0.10);
    border: 1px solid rgba(255, 85, 32, 0.3);
    color: #FF5520;
}
.badge-glow-emerald {
    animation: pulse-emerald 2s infinite;
}
@keyframes pulse-emerald {
    0%, 100% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.4); }
    50%       { box-shadow: 0 0 0 6px rgba(5, 150, 105, 0); }
}

/* ── Tenant Info Card (sidebar) ──────────────────────────────────────────── */
.tenant-card {
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}
.tenant-card-label {
    font-size: 0.68rem;
    color: #9CA3AF;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 4px;
}
.tenant-card-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #141416;
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
    font-size: 0.74rem;
}
.tenant-meta-key {
    color: #6B7280;
}
.tenant-meta-val {
    font-family: monospace;
    color: #FF5520;
    background: rgba(255, 85, 32, 0.08);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.7rem;
    font-weight: 600;
}
.tenant-meta-val-industry {
    font-family: monospace;
    color: #059669;
    background: rgba(5, 150, 105, 0.08);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── KPI Metric Card Override ────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.88) !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 16px !important;
    padding: 18px 22px !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="metric-container"]:hover {
    border-color: rgba(255, 85, 32, 0.35) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06) !important;
}
div[data-testid="metric-container"] label {
    color: #6B7280 !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #141416 !important;
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}

/* ── Dataframe / Tables ──────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: #FFFFFF !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.02) !important;
}

/* ── Inputs & Selects ────────────────────────────────────────────────────── */
.stTextInput input, .stSelectbox [data-baseweb="select"] {
    background-color: #FFFFFF !important;
    color: #141416 !important;
    border: 1.5px solid rgba(0, 0, 0, 0.12) !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
    font-family: inherit !important;
}
.stTextInput input:focus {
    border-color: #FF5520 !important;
    box-shadow: 0 0 0 3px rgba(255, 85, 32, 0.15) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 10px 24px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}
.stButton > button[kind="primary"] {
    background: #FF5520 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 8px 20px rgba(255, 85, 32, 0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #E04616 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 26px rgba(255, 85, 32, 0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #141416 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #F9FAFB !important;
    border-color: #FF5520 !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(0, 0, 0, 0.04) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 6px !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #141416 !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    color: #141416 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* ── Sidebar divider ─────────────────────────────────────────────────────── */
hr {
    border-color: rgba(0, 0, 0, 0.08) !important;
}

/* ── Section subheader ───────────────────────────────────────────────────── */
.section-header {
    font-size: 0.72rem;
    font-weight: 700;
    color: #6B7280;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

/* ── Breadcrumbs ─────────────────────────────────────────────────────────── */
.breadcrumbs-container {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 16px;
    margin-bottom: 16px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.07);
    border-radius: 12px;
    font-size: 0.78rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.breadcrumb-item {
    color: #6B7280;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-weight: 500;
}
.breadcrumb-separator {
    color: #9CA3AF;
    font-size: 0.95rem;
    font-weight: 300;
    user-select: none;
    line-height: 1;
}
.breadcrumb-active {
    color: #FF5520;
    font-weight: 700;
    letter-spacing: 0.02em;
}

/* ── Financilux User Profile Card ────────────────────────────────────────── */
.user-profile-card {
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.04);
}
.user-profile-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.user-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #FF5520;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.1rem;
    box-shadow: 0 4px 12px rgba(255, 85, 32, 0.35);
}
.user-name {
    font-weight: 800;
    font-size: 1rem;
    color: #141416;
    line-height: 1.2;
}
.user-role-tag {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 3px 10px;
    border-radius: 999px;
    margin-top: 4px;
}
.user-role-tag.manager {
    background: rgba(255, 85, 32, 0.10);
    border: 1px solid rgba(255, 85, 32, 0.35);
    color: #FF5520;
}
.user-role-tag.employee {
    background: rgba(2, 132, 199, 0.10);
    border: 1px solid rgba(2, 132, 199, 0.35);
    color: #0284C7;
}
.user-location-info {
    font-size: 0.78rem;
    color: #4B5563;
    background: #F5F3EF;
    padding: 7px 12px;
    border-radius: 10px;
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
}

/* ── Financilux Animated Motif ───────────────────────────────────────────── */
.sunburst-motif {
    animation: rotateSunburst 28s linear infinite;
    transform-origin: center;
}
@keyframes rotateSunburst {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.pulse-circle {
    animation: pulseRing 3s cubic-bezier(0.45, 0, 0.55, 1) infinite;
}
@keyframes pulseRing {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.08); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
}
</style>
"""


def inject_global_css() -> None:
    """Inject all global Financilux Command Center styles. Call on every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ─── HTML Component Helpers ───────────────────────────────────────────────────

def badge(text: str, variant: str = "coral") -> str:
    """Return an inline badge HTML string. variant: coral | emerald | amber | crimson | cyan"""
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
    """
    telem_badge = badge("● TELEMETRY ONLINE", "emerald") if telemetry_online else badge("● TELEMETRY OFFLINE", "crimson")
    sector_badge = badge(f"⬡ {sector.upper()}", "coral") if sector else ""
    ml_color = "emerald" if ml_state in ("READY", "TRAINED") else "amber"
    ml_badge = badge(f"🧠 ML {ml_state}", ml_color)

    st.markdown(f"""
<div class="header-card">
  <div class="header-left">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
      <span class="header-icon">🛡️</span>
      <p class="header-title">{title}</p>
    </div>
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


def render_breadcrumbs(items: list[str]) -> None:
    """Render a sleek glassmorphic breadcrumb trail."""
    html_parts = []
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        if is_last:
            html_parts.append(f'<span class="breadcrumb-item breadcrumb-active">{item}</span>')
        else:
            html_parts.append(f'<span class="breadcrumb-item">{item}</span>')
            html_parts.append('<span class="breadcrumb-separator">›</span>')

    trail = "".join(html_parts)
    st.markdown(f'<div class="breadcrumbs-container">{trail}</div>', unsafe_allow_html=True)


# ─── Plotly Light Theme Defaults (Financilux) ─────────────────────────────────
PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.7)",
    font=dict(color="#141416", family="Plus Jakarta Sans, sans-serif"),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.06)",
        linecolor="rgba(0,0,0,0.12)",
        tickfont=dict(color="#6B7280"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.06)",
        linecolor="rgba(0,0,0,0.12)",
        tickfont=dict(color="#6B7280"),
    ),
    margin=dict(l=40, r=40, t=50, b=40),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.08)",
        borderwidth=1,
        font=dict(color="#141416"),
    ),
)

TRACE_CYAN    = "#0284C7"
TRACE_EMERALD = "#059669"
TRACE_AMBER   = "#D97706"
TRACE_CRIMSON = "#DC2626"
TRACE_CORAL   = "#FF5520"


def sidebar_user_profile(user: dict) -> None:
    """Render the active user profile in the sidebar with role & zone containment badges."""
    role = user.get("role", "EMPLOYEE").upper()
    role_class = "manager" if role == "MANAGER" else "employee"
    role_label = "👔 Facility Manager" if role == "MANAGER" else "👤 Zone Operator"
    full_name = user.get("fullName") or user.get("username", "Authenticated User")
    initial = full_name[0].upper() if full_name else "U"
    assigned_loc = user.get("assignedLocation")

    if role == "MANAGER":
        loc_text = "🌐 Global (All Facility Zones)"
    else:
        loc_text = f"📍 {assigned_loc.replace('-', ' ').title()} (Restricted)" if assigned_loc else "📍 Unassigned Zone"

    st.sidebar.markdown(f"""
<div class="user-profile-card">
  <div class="user-profile-header">
    <div class="user-avatar">{initial}</div>
    <div>
      <div class="user-name">{full_name}</div>
      <span class="user-role-tag {role_class}">{role_label}</span>
    </div>
  </div>
  <div class="user-location-info">
    <span>{loc_text}</span>
  </div>
</div>
""", unsafe_allow_html=True)
