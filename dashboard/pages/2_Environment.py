import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    section_header,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_EMERALD,
    TRACE_AMBER,
    TRACE_CRIMSON,
)

st.set_page_config(page_title="Sensor Telemetry · StockShield", page_icon="📡", layout="wide")
inject_global_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Active Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

# ─── Header ───────────────────────────────────────────────────────────────────
header_banner(
    title="Universal Sensor Telemetry",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle="Live & historical time-series analytics for any sensor metric across any facility or zone",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="LIVE",
)

# ─── Controls ─────────────────────────────────────────────────────────────────
try:
    sensor_types = api.fetch_sensor_types(active_tenant_id)
    inventory = api.fetch_inventory()
    locations = sorted(list(set([
        item.get('locationId', item.get('shelfId'))
        for item in inventory
        if item.get('locationId') or item.get('shelfId')
    ])))
    if not locations:
        locations = ["shelf-01", "shelf-04", "cold-vault-01", "reactor-tank-03"]

    section_header("⚙️ Telemetry Configuration")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_location = st.selectbox("Location / Zone", locations)
    with col2:
        available_sensor_codes = [s['code'] for s in sensor_types] if sensor_types else [
            "temperature", "humidity", "pressure", "vibration", "ph", "weight"
        ]
        selected_sensor = st.selectbox("Sensor Metric", available_sensor_codes)
    with col3:
        time_range = st.selectbox("Time Window", ["1h", "6h", "24h", "7d", "30d"], index=2)

    s_def = next((s for s in sensor_types if s['code'] == selected_sensor), None)
    unit = s_def.get('unit', '') if s_def else ''
    disp_name = s_def.get('displayName', selected_sensor.capitalize()) if s_def else selected_sensor.capitalize()

    # ─── Fetch telemetry ──────────────────────────────────────────────────────
    telemetry_data = []
    try:
        telemetry_data = api.fetch_generic_telemetry(active_tenant_id, selected_location, selected_sensor, range_str=time_range)
    except Exception:
        if selected_sensor in ["temperature", "humidity"]:
            try:
                env_history = api.fetch_environment_history(selected_location, range_str=time_range)
                for pt in env_history:
                    telemetry_data.append({"timestamp": pt.get("timestamp"), "value": pt.get(selected_sensor)})
            except Exception:
                pass

    st.markdown("<br>", unsafe_allow_html=True)

    if telemetry_data and len(telemetry_data) > 0:
        df = pd.DataFrame(telemetry_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        latest_val = float(df['value'].iloc[-1])
        min_val    = float(df['value'].min())
        max_val    = float(df['value'].max())
        mean_val   = float(df['value'].mean())

        # KPI strip
        section_header("📊 Current Reading Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Latest Reading", f"{latest_val:.2f} {unit}")
        with m2:
            st.metric("Minimum", f"{min_val:.2f} {unit}")
        with m3:
            st.metric("Maximum", f"{max_val:.2f} {unit}")
        with m4:
            st.metric("Average", f"{mean_val:.2f} {unit}")

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("📈 Live Telemetry Chart")

        # ─── Plotly chart ─────────────────────────────────────────────────────
        fig = go.Figure()

        # Safe-range fill
        if s_def and s_def.get('minSafe') is not None and s_def.get('maxSafe') is not None:
            fig.add_hrect(
                y0=s_def['minSafe'], y1=s_def['maxSafe'],
                fillcolor="rgba(16,185,129,0.06)",
                line_width=0,
                annotation_text="Safe Zone",
                annotation_position="top left",
                annotation_font=dict(color="#10B981", size=10),
            )

        # Main telemetry trace
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['value'],
            mode='lines+markers',
            name=disp_name,
            line=dict(color=TRACE_CYAN, width=2.5),
            marker=dict(size=4, color=TRACE_CYAN),
            fill='tozeroy',
            fillcolor='rgba(0,229,255,0.05)',
        ))

        # Threshold lines
        if s_def:
            line_specs = [
                ('maxSafe',    'dash',  TRACE_AMBER,   'top left'),
                ('minSafe',    'dash',  TRACE_AMBER,   'bottom left'),
                ('criticalMax','dot',   TRACE_CRIMSON, 'top right'),
                ('criticalMin','dot',   TRACE_CRIMSON, 'bottom right'),
            ]
            for key, dash, color, pos in line_specs:
                if s_def.get(key) is not None:
                    lbl = key.replace('S', ' S').replace('c', 'C').replace('M', ' M')
                    fig.add_hline(
                        y=s_def[key], line_dash=dash, line_color=color, line_width=1.5,
                        annotation_text=f"{lbl} ({s_def[key]} {unit})",
                        annotation_position=pos,
                        annotation_font=dict(color=color, size=10),
                    )

        fig.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            title=f"Live Telemetry — {disp_name} @ {selected_location}",
            xaxis_title="Time",
            yaxis_title=f"{disp_name} ({unit})",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.markdown(f"""
<div class="glass-card" style="text-align:center;padding:48px;">
  <div style="font-size:2.5rem;margin-bottom:12px;">📡</div>
  <div style="color:#94A3B8;font-size:0.9rem;">
    Awaiting telemetry for <strong style="color:#F8FAFC;">{disp_name}</strong>
    at <strong style="color:#00E5FF;">{selected_location}</strong>
    over <strong style="color:#F8FAFC;">{time_range}</strong>.
  </div>
  <div style="color:#64748B;font-size:0.78rem;margin-top:8px;">
    Data streams live from MQTT edge sensors — run the edge-simulator to generate test traffic.
  </div>
</div>
""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error fetching sensor telemetry: {e}")
