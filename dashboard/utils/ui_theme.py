"""
ui_theme.py — StockShield Industrial Telemetry Console
Clean dark-slate engineering interface (#0B0F17), 1px structural borders,
monospace telemetry readouts, and zero emoji clutter.
"""

import streamlit as st

# ─── Palette Constants ────────────────────────────────────────────────────────
CYAN    = "#06B6D4"
EMERALD = "#10B981"
AMBER   = "#F59E0B"
CRIMSON = "#EF4444"
CORAL   = "#06B6D4"  # Mapped to cyan for backward compatibility
BG      = "#0B0F17"
SURFACE = "#111827"
TEXT    = "#F8FAFC"
MUTED   = "#94A3B8"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

.stApp {
    background-color: #0B0F17 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #F8FAFC !important;
}

.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #F8FAFC !important;
    letter-spacing: -0.02em !important;
}

p, span, label, div {
    color: #E2E8F0;
}

code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: #38BDF8 !important;
    background: rgba(56, 189, 248, 0.1) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #94A3B8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Engineering Panel Card ──────────────────────────────────────────────── */
.glass-card {
    background: #111827;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 1rem;
}

/* ── Top Console Header Bar ──────────────────────────────────────────────── */
.header-card {
    background: #111827;
    border: 1px solid #1E293B;
    border-left: 3px solid #06B6D4;
    border-radius: 8px;
    padding: 18px 24px;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.header-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #F8FAFC;
    letter-spacing: -0.02em;
    margin: 0;
}
.header-tenant {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #06B6D4;
    font-weight: 500;
    margin: 0;
}
.header-subtitle {
    font-size: 0.8rem;
    color: #64748B;
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
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    white-space: nowrap;
}
.badge-cyan, .badge-coral {
    background: rgba(6, 182, 212, 0.12);
    border: 1px solid rgba(6, 182, 212, 0.35);
    color: #22D3EE;
}
.badge-emerald {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34D399;
}
.badge-amber {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #FBBF24;
}
.badge-crimson {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #F87171;
}

/* ── Sidebar Cards ───────────────────────────────────────────────── */
.tenant-card, .user-profile-card {
    background: #111827;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 12px 14px;
    margin: 8px 0;
}
.tenant-card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #64748B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.tenant-card-name, .user-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #F8FAFC;
    margin-bottom: 6px;
}
.tenant-meta-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    padding: 2px 0;
}
.tenant-meta-key { color: #64748B; }
.tenant-meta-val, .tenant-meta-val-industry {
    font-family: 'JetBrains Mono', monospace;
    color: #38BDF8;
    font-size: 0.7rem;
}

.user-role-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
}
.user-role-tag.manager {
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid rgba(6, 182, 212, 0.4);
    color: #22D3EE;
}
.user-role-tag.employee {
    background: rgba(148, 163, 184, 0.15);
    border: 1px solid rgba(148, 163, 184, 0.3);
    color: #CBD5E1;
}
.user-location-info {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #94A3B8;
    background: #0B0F17;
    border: 1px solid #1E293B;
    padding: 6px 10px;
    border-radius: 4px;
    margin-top: 8px;
}

/* ── KPI Metric Containers ───────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: #111827 !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    padding: 16px 18px !important;
}
div[data-testid="metric-container"] label {
    color: #64748B !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.65rem !important;
    font-weight: 600 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* ── Inputs, Buttons & Tabs ──────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div {
    background-color: #0B0F17 !important;
    color: #F8FAFC !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
}
.stButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    border: 1px solid #334155 !important;
    background: #1E293B !important;
    color: #F8FAFC !important;
}
.stButton > button[kind="primary"] {
    background: #0891B2 !important;
    border-color: #06B6D4 !important;
    color: #FFFFFF !important;
}
.stButton > button[kind="primary"]:hover {
    background: #06B6D4 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
    padding: 3px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 4px !important;
    color: #64748B !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
}
.stTabs [aria-selected="true"] {
    background: #1E293B !important;
    color: #F8FAFC !important;
    font-weight: 600 !important;
}

.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    color: #94A3B8;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1E293B;
}

.breadcrumbs-container {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 10px;
    margin-bottom: 10px;
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
}
.breadcrumb-item { color: #64748B; }
.breadcrumb-separator { color: #475569; }
.breadcrumb-active { color: #38BDF8; font-weight: 600; }
</style>
"""


def inject_global_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def badge(text: str, variant: str = "cyan") -> str:
    return f'<span class="badge-base badge-{variant}">{text}</span>'


def glass_card(content_html: str) -> None:
    st.markdown(f'<div class="glass-card">{content_html}</div>', unsafe_allow_html=True)


def header_banner(
    title: str,
    tenant_name: str,
    subtitle: str,
    telemetry_online: bool = True,
    sector: str = "",
    ml_state: str = "READY",
) -> None:
    telem_badge = badge("MQTT ONLINE", "emerald") if telemetry_online else badge("MQTT STANDBY", "crimson")
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
    plot_bgcolor="#0B0F17",
    font=dict(color="#94A3B8", family="Inter, sans-serif", size=12),
    xaxis=dict(
        gridcolor="#1E293B",
        linecolor="#334155",
        tickfont=dict(color="#64748B", family="JetBrains Mono, monospace"),
    ),
    yaxis=dict(
        gridcolor="#1E293B",
        linecolor="#334155",
        tickfont=dict(color="#64748B", family="JetBrains Mono, monospace"),
    ),
    margin=dict(l=40, r=40, t=40, b=36),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(17, 24, 39, 0.9)",
        bordercolor="#1E293B",
        borderwidth=1,
        font=dict(color="#E2E8F0", size=11),
    ),
)

TRACE_CYAN    = "#06B6D4"
TRACE_EMERALD = "#10B981"
TRACE_AMBER   = "#F59E0B"
TRACE_CRIMSON = "#EF4444"
TRACE_CORAL   = "#38BDF8"


def sidebar_user_profile(user: dict) -> None:
    role = user.get("role", "EMPLOYEE").upper()
    role_class = "manager" if role == "MANAGER" else "employee"
    role_label = "FACILITY MANAGER" if role == "MANAGER" else "ZONE OPERATOR"
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

    loc_text = "SCOPE: ALL ZONES" if role == "MANAGER" else f"ZONE: {(assigned_loc or 'UNASSIGNED').upper()}"

    st.sidebar.markdown(f"""
<div class="user-profile-card">
  <div class="user-name">{full_name}</div>
  <span class="user-role-tag {role_class}">{role_label}</span>
  <div class="user-location-info">{loc_text}</div>
</div>
""", unsafe_allow_html=True)
