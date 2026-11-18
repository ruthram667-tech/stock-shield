import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    sidebar_user_profile,
    section_header,
    render_breadcrumbs,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_AMBER,
    TRACE_CRIMSON,
)

st.set_page_config(page_title="Sensor Telemetry · StockShield", layout="wide")
inject_global_css()

user = st.session_state.get("user")
if not user or "error" in user:
    st.warning("Please authenticate on the main console first.")
    st.stop()

sidebar_user_profile(user)
is_employee = (user.get("role", "").upper() == "EMPLOYEE")
user_zone = user.get("assignedLocation")

st.sidebar.markdown('<div class="section-header">Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(selected_tenant.get('name', active_tenant_id), active_tenant_id, selected_tenant.get('industry', 'universal'))

if st.sidebar.button("Refresh Telemetry", use_container_width=True):
    st.rerun()

summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id, location_id=user_zone if is_employee else None)
telemetry_online = summary.get("sensorsOnline", 0) > 0

scope_note = f"ZONE: {user_zone.upper()}" if is_employee and user_zone else "ALL LOCATIONS"
render_breadcrumbs(["STOCKSHIELD", active_tenant_id.upper(), "TELEMETRY", scope_note])

header_banner(
    title="Hardware Sensor Telemetry Inspector",
    tenant_name=f"TENANT: {active_tenant_id} | {scope_note}",
    subtitle="InfluxDB time-series readout with configured warning and critical threshold bounds",
    telemetry_online=telemetry_online,
    sector=selected_tenant.get('industry', ''),
    ml_state="LIVE" if telemetry_online else "STANDBY",
)

sensor_types = api.fetch_sensor_types(active_tenant_id)
inventory = api.fetch_inventory(tenant_id=active_tenant_id, zone=user_zone if is_employee else None)

locations = sorted(list({
    item.get('locationId', item.get('shelfId'))
    for item in inventory if item.get('locationId') or item.get('shelfId')
})) or ["shelf-01"]

section_header("Query Parameters")
col1, col2, col3 = st.columns(3)
with col1:
    selected_location = st.selectbox("Node ID", locations)
with col2:
    available_sensor_codes = [s['code'] for s in sensor_types] if sensor_types else ["weight", "temperature", "humidity"]
    selected_sensor = st.selectbox("Metric", available_sensor_codes)
with col3:
    time_range = st.selectbox("Window", ["1h", "6h", "24h", "7d", "30d"], index=0)

s_def = next((s for s in sensor_types if s['code'] == selected_sensor), None)
unit = s_def.get('unit', '') if s_def else ('kg' if selected_sensor == 'weight' else '')
disp_name = s_def.get('displayName', selected_sensor.upper()) if s_def else selected_sensor.upper()

telemetry_data = api.fetch_generic_telemetry(active_tenant_id, selected_location, selected_sensor, range_str=time_range)
if not telemetry_data and selected_sensor == "weight":
    telemetry_data = api.fetch_telemetry(selected_location, range_str=time_range)
elif not telemetry_data and selected_sensor in ["temperature", "humidity"]:
    env_pts = api.fetch_environment_history(selected_location, range_str=time_range)
    telemetry_data = [p for p in env_pts if p.get("measurement") == selected_sensor]

st.markdown("<br>", unsafe_allow_html=True)

if telemetry_data:
    df = pd.DataFrame(telemetry_data)
    ts_col = 'time' if 'time' in df.columns else 'timestamp'
    df[ts_col] = pd.to_datetime(df[ts_col], format="ISO8601")
    df = df.sort_values(ts_col)

    latest_val = float(df['value'].iloc[-1])
    min_val    = float(df['value'].min())
    max_val    = float(df['value'].max())
    mean_val   = float(df['value'].mean())

    section_header("Signal Statistics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Latest ({disp_name})", f"{latest_val:.2f} {unit}")
    m2.metric("Mean", f"{mean_val:.2f} {unit}")
    m3.metric("Min", f"{min_val:.2f} {unit}")
    m4.metric("Max", f"{max_val:.2f} {unit}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[ts_col], y=df['value'],
        name=f"{disp_name} ({unit})",
        line=dict(color=TRACE_CYAN, width=2.2),
        mode='lines+markers'
    ))

    if s_def:
        if s_def.get('maxSafe') is not None:
            fig.add_hline(y=s_def['maxSafe'], line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"MAX_SAFE ({s_def['maxSafe']}{unit})")
        if s_def.get('minSafe') is not None:
            fig.add_hline(y=s_def['minSafe'], line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"MIN_SAFE ({s_def['minSafe']}{unit})")
        if s_def.get('criticalMax') is not None:
            fig.add_hline(y=s_def['criticalMax'], line_dash="dot", line_color=TRACE_CRIMSON, annotation_text=f"CRIT_MAX ({s_def['criticalMax']}{unit})")
        if s_def.get('criticalMin') is not None:
            fig.add_hline(y=s_def['criticalMin'], line_dash="dot", line_color=TRACE_CRIMSON, annotation_text=f"CRIT_MIN ({s_def['criticalMin']}{unit})")

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=f"{selected_location} // {disp_name} ({time_range})",
        yaxis_title=f"{disp_name} ({unit})",
        xaxis_title="Timestamp (UTC)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown(f"""
<div class="glass-card" style="padding: 36px 24px;">
  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #F59E0B; margin-bottom: 6px;">
    NO_DATA_IN_WINDOW
  </div>
  <div style="font-weight: 600; font-size: 0.95rem; color: #F8FAFC;">
    Zero hardware points in InfluxDB for <code>{selected_location}</code> / <code>{selected_sensor}</code> ({time_range})
  </div>
  <div style="font-size: 0.82rem; color: #64748B; margin-top: 6px;">
    Ensure your ESP32 is connected to Wi-Fi and publishing to Mosquitto (Port 1883).
  </div>
</div>
""", unsafe_allow_html=True)
