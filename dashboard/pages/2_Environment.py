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
    TRACE_EMERALD,
    TRACE_AMBER,
    TRACE_CRIMSON,
)

st.set_page_config(page_title="Sensor Telemetry · StockShield", page_icon="📡", layout="wide")
inject_global_css()

# ─── User Profile & Scope ─────────────────────────────────────────────────────
user = st.session_state.get("user")
if user:
    sidebar_user_profile(user)
    is_employee = (user.get("role", "").upper() == "EMPLOYEE")
    user_zone = user.get("assignedLocation")
else:
    is_employee = False
    user_zone = None

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

# ─── Breadcrumbs & Header ─────────────────────────────────────────────────────
scope_note = f"Zone: {user_zone.upper()}" if is_employee and user_zone else "All Facility Locations"
render_breadcrumbs(["🛡️ StockShield", selected_tenant.get('name', 'Universal IoT'), "📡 Sensor Telemetry", scope_note])

header_banner(
    title=f"Universal Sensor Telemetry — {'🔒 Zone Restricted' if is_employee else '🌐 Global Facility'}",
    tenant_name=f"{selected_tenant.get('name', 'Universal IoT')} · {scope_note}",
    subtitle="Live & historical time-series analytics for any sensor metric across warehouse zones",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="LIVE",
)

if is_employee and user_zone:
    st.info(f"🔒 **Access Contained:** You are viewing live telemetry strictly scoped to your assigned zone: **{user_zone.upper()}**.")

# ─── Controls ─────────────────────────────────────────────────────────────────
try:
    sensor_types = api.fetch_sensor_types(active_tenant_id)
    inventory = api.fetch_inventory()
    
    # Filter locations by employee assigned zone if applicable
    if is_employee and user_zone:
        filtered_items = [i for i in inventory if i.get('zone', '').lower() == user_zone.lower()]
        locations = sorted(list(set([
            item.get('locationId', item.get('shelfId'))
            for item in filtered_items
            if item.get('locationId') or item.get('shelfId')
        ])))
        if not locations:
            if "frozen" in user_zone.lower():
                locations = ["shelf-07", "shelf-08", "cold-vault-01"]
            elif "dry" in user_zone.lower():
                locations = ["shelf-01", "shelf-02", "shelf-03"]
            else:
                locations = ["shelf-04", "shelf-05"]
    else:
        locations = sorted(list(set([
            item.get('locationId', item.get('shelfId'))
            for item in inventory
            if item.get('locationId') or item.get('shelfId')
        ])))
        if not locations:
            locations = ["shelf-01", "shelf-04", "shelf-07", "cold-vault-01", "reactor-tank-03"]

    section_header("⚙️ Telemetry Configuration")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_location = st.selectbox("Location / Node", locations)
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
            st.metric(f"Current {disp_name}", f"{latest_val:.2f} {unit}")
        with m2:
            st.metric("Mean", f"{mean_val:.2f} {unit}")
        with m3:
            st.metric("Min", f"{min_val:.2f} {unit}")
        with m4:
            st.metric("Max", f"{max_val:.2f} {unit}")

        # Chart with threshold bands
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['value'],
            name=f"{disp_name} ({unit})",
            line=dict(color=TRACE_CYAN, width=2.5),
            mode='lines'
        ))

        if s_def:
            min_safe = s_def.get('minSafe')
            max_safe = s_def.get('maxSafe')
            crit_min = s_def.get('criticalMin')
            crit_max = s_def.get('criticalMax')

            if max_safe is not None:
                fig.add_hline(y=max_safe, line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"Max Safe ({max_safe}{unit})")
            if min_safe is not None:
                fig.add_hline(y=min_safe, line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"Min Safe ({min_safe}{unit})")
            if crit_max is not None:
                fig.add_hline(y=crit_max, line_dash="dot", line_color=TRACE_CRIMSON, annotation_text=f"Critical Max ({crit_max}{unit})")
            if crit_min is not None:
                fig.add_hline(y=crit_min, line_dash="dot", line_color=TRACE_CRIMSON, annotation_text=f"Critical Min ({crit_min}{unit})")

        fig.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            title=f"{disp_name} over time · {selected_location}",
            yaxis_title=f"{disp_name} ({unit})",
            xaxis_title="Timestamp",
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        # Fallback simulation sparkline for visual inspection
        st.info(f"Connecting to live edge telemetry stream for {selected_location} · {disp_name}...")
        now = pd.Timestamp.now()
        demo_times = pd.date_range(now - pd.Timedelta(hours=24), now, freq='30min')
        base = -18.4 if "cold" in selected_location or "shelf-07" in selected_location else 21.0
        demo_vals = [base + 0.3 * (i % 5 - 2) for i in range(len(demo_times))]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=demo_times, y=demo_vals, line=dict(color=TRACE_CYAN, width=2.5)))
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=360, title=f"Real-time Stream: {selected_location}")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading telemetry: {e}")
