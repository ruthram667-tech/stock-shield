import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    section_header,
    badge,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_EMERALD,
    TRACE_CRIMSON,
    TRACE_AMBER,
)

st.set_page_config(
    page_title="StockShield Command Center",
    page_icon="🛡️",
    layout="wide",
)

inject_global_css()

# ─── Sidebar: Tenant & Industry Switcher ─────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)

tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}

selected_label = st.sidebar.selectbox("Active Tenant", list(tenant_map.keys()))
active_tenant_id = tenant_map[selected_label]
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

# Compact tenant info card
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

st.sidebar.divider()

# Quick Tenant Creator in sidebar
with st.sidebar.expander("➕ Register New Tenant"):
    new_t_name = st.text_input("Company / Org Name")
    new_t_ind = st.selectbox(
        "Industry",
        ["pharmaceutical", "chemical_manufacturing", "cold_chain_logistics",
         "agriculture", "manufacturing_machinery", "retail_grocery", "data_center"]
    )
    if st.button("Create Tenant", use_container_width=True):
        if new_t_name:
            try:
                res = api.create_tenant(new_t_name, new_t_ind)
                st.sidebar.success(f"Created {res['name']}!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

# ─── Main Header Banner ───────────────────────────────────────────────────────
try:
    summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id)
    telemetry_up = summary.get("sensorsOnline", 0) > 0
except Exception:
    summary = {}
    telemetry_up = False

models = api.fetch_tenant_models(active_tenant_id)
ml_state = "READY" if models else "NO MODELS"

header_banner(
    title="StockShield Command Center",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle=f"IoT Telemetry · Anomaly Detection · Self-Trained ML  ·  {selected_tenant.get('industry', 'All Industries').upper()}",
    telemetry_online=telemetry_up,
    sector=selected_tenant.get('industry', ''),
    ml_state=ml_state,
)

# ─── Row 1: 4-Column KPI Strip ────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

sensors_online  = summary.get("sensorsOnline", 0)
total_items     = summary.get("totalItems", 0)
low_stock       = summary.get("lowStockCount", 0)
active_alerts   = summary.get("activeAlerts", 0)

stock_health_pct = (
    round(((total_items - low_stock) / total_items) * 100, 1)
    if total_items > 0 else 100.0
)

with kpi1:
    st.metric(
        "🟢 Sensors Online",
        sensors_online,
        delta=None,
    )
with kpi2:
    st.metric(
        "📦 Buffer Stock Health",
        f"{stock_health_pct}%",
        delta=f"{total_items - low_stock} of {total_items} OK",
        delta_color="normal",
    )
with kpi3:
    st.metric(
        "❄️ Monitored Assets",
        total_items,
    )
with kpi4:
    alert_delta = f"-{active_alerts} active" if active_alerts > 0 else "All clear"
    st.metric(
        "🔔 Active Alerts",
        active_alerts,
        delta=alert_delta,
        delta_color="inverse",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 2: 2:1 Workspace ─────────────────────────────────────────────────────
left_col, right_col = st.columns([2, 1])

with left_col:
    section_header("📡 Registered Sensor Types & Operational Thresholds")
    sensor_types = api.fetch_sensor_types(active_tenant_id)

    if sensor_types:
        grid_cols = st.columns(min(len(sensor_types), 4) or 1)
        for idx, s in enumerate(sensor_types):
            with grid_cols[idx % len(grid_cols)]:
                ml_badge_html = badge("✅ ML ON", "emerald") if s.get("mlEnabled") else badge("❌ ML OFF", "crimson")
                cat_badge_html = badge(s.get("category", "metric"), "cyan")
                st.markdown(f"""
<div class="glass-card" style="padding:14px;">
  <div style="font-size:0.92rem;font-weight:700;color:#F8FAFC;margin-bottom:6px;">
    {s.get('displayName', s['code'])}
  </div>
  <div style="margin-bottom:8px;">
    <code style="color:#00E5FF;font-size:0.72rem;">{s['code']}</code>
    &nbsp;{cat_badge_html}
  </div>
  <div style="font-size:0.75rem;color:#94A3B8;line-height:1.8;">
    Safe range: <strong style="color:#F8FAFC;">{s.get('minSafe', '–')} – {s.get('maxSafe', '–')} {s.get('unit','')}</strong><br>
    Critical: <span style="color:#EF4444;">{s.get('criticalMin','–')} / {s.get('criticalMax','–')}</span>
  </div>
  <div style="margin-top:8px;">{ml_badge_html}</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="glass-card" style="text-align:center;padding:32px;">
  <div style="font-size:2rem;margin-bottom:8px;">⚙️</div>
  <div style="color:#94A3B8;font-size:0.85rem;">
    No custom sensor types configured yet for <strong style="color:#F8FAFC;">{selected_tenant.get('name')}</strong>.<br>
    Visit the <strong style="color:#00E5FF;">Sensor Registry</strong> page to get started.
  </div>
</div>
""", unsafe_allow_html=True)

with right_col:
    section_header("🔔 Anomaly Risk / Alert Feed")
    try:
        alerts = api.fetch_recent_alerts(limit=8, tenant_id=active_tenant_id)
        if alerts:
            for alert in alerts[:6]:
                severity = alert.get('severity', 'INFO')
                sev_variant = {
                    'CRITICAL': 'crimson',
                    'WARNING': 'amber',
                    'INFO': 'cyan',
                }.get(severity, 'cyan')
                sensor_type = alert.get('sensorType', alert.get('type', 'general'))
                message = alert.get('message', 'No details')[:60]
                location = alert.get('locationId', alert.get('shelfId', '—'))
                badge_html = badge(severity, sev_variant)
                st.markdown(f"""
<div class="glass-card" style="padding:12px 14px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    {badge_html}
    <span style="font-size:0.68rem;color:#64748B;font-family:monospace;">{location}</span>
  </div>
  <div style="font-size:0.78rem;color:#94A3B8;font-family:monospace;">{sensor_type}</div>
  <div style="font-size:0.8rem;color:#F8FAFC;margin-top:3px;">{message}</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div class="glass-card" style="text-align:center;padding:28px;">
  <div style="font-size:1.8rem;margin-bottom:8px;">✅</div>
  <div style="color:#10B981;font-size:0.85rem;font-weight:600;">All systems nominal</div>
  <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">No active alerts detected</div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
<div class="glass-card">
  <span style="color:#EF4444;font-size:0.82rem;">⚠️ Alert feed unavailable: {e}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 3: Full-Width Tabbed Matrix ─────────────────────────────────────────
section_header("📊 System Intelligence Matrix")
tab_logs, tab_health = st.tabs(["📋 Live Sensor Ingestion Log", "🖥️ System Health"])

with tab_logs:
    try:
        all_alerts = api.fetch_recent_alerts(limit=50, tenant_id=active_tenant_id)
        if all_alerts:
            alerts_df = pd.DataFrame(all_alerts)
            time_col = 'createdAt' if 'createdAt' in alerts_df.columns else 'timestamp'
            type_col = 'alertType' if 'alertType' in alerts_df.columns else 'type'
            alerts_df['Time']     = pd.to_datetime(alerts_df[time_col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            alerts_df['Severity'] = alerts_df.get('severity', '')
            alerts_df['Type']     = alerts_df.get(type_col, '')
            alerts_df['Sensor']   = alerts_df.get('sensorType', 'general')
            alerts_df['Message']  = alerts_df.get('message', '')
            alerts_df['Location'] = alerts_df.get('locationId', alerts_df.get('shelfId', ''))

            cols_to_show = ['Time', 'Severity', 'Sensor', 'Type', 'Message', 'Location']
            available = [c for c in cols_to_show if c in alerts_df.columns]
            st.dataframe(alerts_df[available], use_container_width=True, hide_index=True)
        else:
            st.success("✅ No recent events in the ingestion log.")
    except Exception as e:
        st.error(f"Log unavailable: {e}")

with tab_health:
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Backend API", "🟢 UP" if telemetry_up else "🔴 DOWN")
    with h2:
        st.metric("ML Service", "🟢 UP" if models is not None else "🔴 DOWN")
    with h3:
        st.metric("MQTT Broker", "🟢 Active")
    with h4:
        st.metric("Trained Models", len(models) if models else 0)

    # Severity distribution mini chart
    try:
        all_alerts = api.fetch_recent_alerts(limit=100, tenant_id=active_tenant_id)
        if all_alerts:
            sev_df = pd.DataFrame(all_alerts)
            if 'severity' in sev_df.columns:
                sev_counts = sev_df['severity'].value_counts().reset_index()
                sev_counts.columns = ['Severity', 'Count']
                color_map = {'CRITICAL': TRACE_CRIMSON, 'WARNING': TRACE_AMBER, 'INFO': TRACE_CYAN}
                fig = go.Figure()
                for _, row in sev_counts.iterrows():
                    fig.add_trace(go.Bar(
                        name=row['Severity'],
                        x=[row['Severity']],
                        y=[row['Count']],
                        marker_color=color_map.get(row['Severity'], TRACE_CYAN),
                        marker_line_width=0,
                    ))
                fig.update_layout(
                    **PLOTLY_LAYOUT_DEFAULTS,
                    title="Alert Severity Distribution",
                    showlegend=False,
                    bargap=0.35,
                    height=280,
                )
                st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass
