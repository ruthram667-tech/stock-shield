import streamlit as st
import pandas as pd
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    sidebar_user_profile,
    section_header,
    render_breadcrumbs,
    badge,
)

st.set_page_config(page_title="Sensor Registry · StockShield", layout="wide")
inject_global_css()

# ─── RBAC Access Gate ─────────────────────────────────────────────────────────
user = st.session_state.get("user")
if not user or "error" in user:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    st.warning("Please authenticate on the main console first.")
    st.stop()

sidebar_user_profile(user)
if user.get("role", "").upper() == "EMPLOYEE":
    render_breadcrumbs(["STOCKSHIELD", "SENSOR REGISTRY", "ACCESS RESTRICTED"])
    st.error("ACCESS RESTRICTED: Facility manager credentials required.")
    st.markdown(f"""
<div class="glass-card" style="padding: 28px; text-align: center;">
  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #EF4444; margin-bottom: 8px;">
    ERROR: 403_FORBIDDEN
  </div>
  <h3 style="color: #F8FAFC; margin-bottom: 6px;">Manager Permissions Required</h3>
  <p style="color: #94A3B8; max-width: 540px; margin: 0 auto; font-size: 0.85rem;">
    Authenticated as <strong>{user.get('fullName', user.get('username'))}</strong> (Scoped to {user.get('assignedLocation') or 'Unassigned'}).
    Hardware sensor onboarding and telemetry registry modification are restricted to facility managers.
  </p>
</div>
""", unsafe_allow_html=True)
    st.stop()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Organization / Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

# ─── Breadcrumbs & Header ─────────────────────────────────────────────────────
render_breadcrumbs(["STOCKSHIELD", selected_tenant.get('name', 'FACILITY').upper(), "SENSOR REGISTRY"])

header_banner(
    title="Sensor Hardware & Type Registry",
    tenant_name=f"TENANT: {active_tenant_id}",
    subtitle="Configure edge sensor metrics, physical measurement units, and threshold limits",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="ACTIVE",
)

# ─── 2-Column Layout ──────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

# Left: List registered sensor types
with col_left:
    section_header(f"Registered Sensors // {selected_tenant.get('name', '')}")
    try:
        sensor_types = api.fetch_sensor_types(active_tenant_id)
        if sensor_types:
            for s in sensor_types:
                ml_html  = badge("ML ACTIVE", "emerald") if s.get("mlEnabled") else badge("ML OFF", "crimson")
                cat_html = badge(s.get("category", "metric"), "cyan")
                unit     = s.get('unit', '')
                st.markdown(f"""
<div class="glass-card" style="padding:14px 18px; margin-bottom:10px;">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <span style="font-size:0.95rem; font-weight:600; color:#F8FAFC;">{s.get('displayName', s['code'])}</span>
      &nbsp;&nbsp;<code style="font-size:0.75rem;">{s['code']}</code>
    </div>
    <div style="display:flex; gap:6px;">{cat_html}&nbsp;{ml_html}</div>
  </div>
  <div style="margin-top:10px; display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; font-size:0.75rem; color:#94A3B8; font-family: 'JetBrains Mono', monospace;">
    <div>UNIT: <strong style="color:#F8FAFC;">{unit or '—'}</strong></div>
    <div>SAFE: <strong style="color:#10B981;">{s.get('minSafe','—')} to {s.get('maxSafe','—')}</strong></div>
    <div>CRIT: <strong style="color:#EF4444;">{s.get('criticalMin','—')} / {s.get('criticalMax','—')}</strong></div>
  </div>
  <div style="margin-top:8px; font-size:0.7rem; color:#64748B; font-family: 'JetBrains Mono', monospace;">
    AGGREGATION: {s.get('aggregationMethod','mean').upper()}
  </div>
</div>
""", unsafe_allow_html=True)

            with st.expander("Tabular View"):
                df = pd.DataFrame(sensor_types)
                cols = ['code', 'displayName', 'unit', 'category', 'minSafe', 'maxSafe', 'criticalMin', 'criticalMax', 'mlEnabled']
                available = [c for c in cols if c in df.columns]
                st.dataframe(df[available], use_container_width=True, hide_index=True)
        else:
            st.markdown("""
<div class="glass-card" style="text-align:center; padding:36px;">
  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #64748B;">REGISTRY EMPTY</div>
  <div style="color:#94A3B8; font-size:0.85rem; margin-top: 4px;">Zero sensor types registered for this tenant.</div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching sensor types: {e}")

# Right: Register new sensor type
with col_right:
    section_header("Register Sensor Definition")
    with st.form("new_sensor_type_form"):
        code = st.text_input("Sensor Code (lowercase identifier)", placeholder="pressure, vibration, etc.")
        display_name = st.text_input("Display Name", placeholder="Chamber Pressure")
        unit = st.text_input("Physical Unit", placeholder="psi, °C, %, kg")
        category = st.selectbox("Category", [
            "environmental", "chemical", "mechanical",
            "weight_level", "agricultural", "electrical"
        ])

        st.markdown("<div style='font-size:0.75rem; color:#94A3B8; margin-top:8px;'>Operational Bounds:</div>", unsafe_allow_html=True)
        tc1, tc2 = st.columns(2)
        with tc1:
            min_safe     = st.number_input("Safe Minimum",    value=0.0)
            critical_min = st.number_input("Critical Minimum", value=-10.0)
        with tc2:
            max_safe     = st.number_input("Safe Maximum",    value=100.0)
            critical_max = st.number_input("Critical Maximum", value=120.0)

        ml_enabled  = st.checkbox("Enable ML Anomaly Tracking", value=True)
        agg_method  = st.selectbox("InfluxDB Aggregation", ["mean", "max", "min", "sum"])

        submitted = st.form_submit_button("Register Sensor Type", type="primary", use_container_width=True)
        if submitted:
            if not code or not display_name:
                st.error("Sensor code and display name are required.")
            else:
                payload = {
                    "tenantId":          active_tenant_id,
                    "code":              code.strip().lower(),
                    "displayName":       display_name.strip(),
                    "unit":              unit.strip(),
                    "category":          category,
                    "minSafe":           min_safe,
                    "maxSafe":           max_safe,
                    "criticalMin":       critical_min,
                    "criticalMax":       critical_max,
                    "mlEnabled":         ml_enabled,
                    "aggregationMethod": agg_method,
                }
                try:
                    res = api.register_sensor_type(payload)
                    st.success(f"Registered sensor '{res.get('code', code)}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration failed: {e}")
