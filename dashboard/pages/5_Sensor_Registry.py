import streamlit as st
import pandas as pd
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    section_header,
    badge,
)

st.set_page_config(page_title="Sensor Registry · StockShield", page_icon="⚙️", layout="wide")
inject_global_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Organization / Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

# ─── Header ───────────────────────────────────────────────────────────────────
header_banner(
    title="Dynamic Sensor Type Registry",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle="Configure custom IoT sensor types, metric units, categories & operational alert limits",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="CONFIGURING",
)

# ─── 2-Column Layout ──────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

# Left: List registered sensor types
with col_left:
    section_header(f"📋 Current Sensors — {selected_tenant.get('name', '')}")
    try:
        sensor_types = api.fetch_sensor_types(active_tenant_id)
        if sensor_types:
            # Styled sensor cards
            for s in sensor_types:
                ml_html  = badge("✅ ML ON",  "emerald") if s.get("mlEnabled") else badge("❌ ML OFF", "crimson")
                cat_html = badge(s.get("category", "metric"), "cyan")
                unit     = s.get('unit', '')
                st.markdown(f"""
<div class="glass-card" style="padding:14px 18px;margin-bottom:10px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <span style="font-size:0.95rem;font-weight:700;color:#F8FAFC;">{s.get('displayName', s['code'])}</span>
      &nbsp;&nbsp;<code style="font-size:0.72rem;color:#00E5FF;">{s['code']}</code>
    </div>
    <div style="display:flex;gap:6px;">{cat_html}&nbsp;{ml_html}</div>
  </div>
  <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:0.76rem;color:#94A3B8;">
    <div>Unit: <strong style="color:#F8FAFC;">{unit or '—'}</strong></div>
    <div>Safe: <strong style="color:#10B981;">{s.get('minSafe','—')} – {s.get('maxSafe','—')}</strong></div>
    <div>Critical: <strong style="color:#EF4444;">{s.get('criticalMin','—')} / {s.get('criticalMax','—')}</strong></div>
  </div>
  <div style="margin-top:8px;font-size:0.72rem;color:#64748B;">
    Aggregation: <code style="color:#94A3B8;">{s.get('aggregationMethod','mean')}</code>
  </div>
</div>
""", unsafe_allow_html=True)

            # Also render as dataframe for bulk view
            with st.expander("📊 View as Table"):
                df = pd.DataFrame(sensor_types)
                cols = ['code', 'displayName', 'unit', 'category', 'minSafe', 'maxSafe', 'criticalMin', 'criticalMax', 'mlEnabled']
                available = [c for c in cols if c in df.columns]
                st.dataframe(df[available], use_container_width=True, hide_index=True)
        else:
            st.markdown("""
<div class="glass-card" style="text-align:center;padding:40px;">
  <div style="font-size:2rem;margin-bottom:10px;">⚙️</div>
  <div style="color:#94A3B8;font-size:0.85rem;">No sensor types registered for this tenant yet.</div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching sensor types: {e}")

# Right: Register new sensor type
with col_right:
    section_header("➕ Register New Sensor Type")
    st.markdown('<div class="glass-card" style="padding:20px;">', unsafe_allow_html=True)
    with st.form("new_sensor_type_form"):
        code = st.text_input("Sensor Code (lowercase, unique)", placeholder="e.g. pressure, ph, vibration, soil_moisture")
        display_name = st.text_input("Display Name", placeholder="e.g. Chamber Pressure, Tank pH")
        unit = st.text_input("Measurement Unit", placeholder="e.g. psi, pH, g, °C, %, ppm, RPM")
        category = st.selectbox("Category", [
            "environmental", "chemical", "mechanical",
            "weight_level", "agricultural", "electrical"
        ])

        st.markdown("**Thresholds & Safe Operational Range:**")
        tc1, tc2 = st.columns(2)
        with tc1:
            min_safe     = st.number_input("Safe Minimum",    value=0.0)
            critical_min = st.number_input("Critical Minimum", value=-10.0)
        with tc2:
            max_safe     = st.number_input("Safe Maximum",    value=100.0)
            critical_max = st.number_input("Critical Maximum", value=120.0)

        ml_enabled  = st.checkbox("Enable ML Training & Anomaly Detection", value=True)
        agg_method  = st.selectbox("Aggregation Method (InfluxDB)", ["mean", "max", "min", "sum"])

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
                    res = api.create_sensor_type(payload)
                    st.success(f"Successfully registered sensor type '{code}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to register sensor type: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
