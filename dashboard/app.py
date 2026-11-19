import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    sidebar_user_profile,
    section_header,
    render_breadcrumbs,
    badge,
    login_animation,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_EMERALD,
    TRACE_AMBER,
    TRACE_CRIMSON,
    TRACE_CORAL,
)

st.set_page_config(
    page_title="StockShield — Smart Inventory & Telemetry",
    layout="wide",
)

inject_global_css()

if "user" not in st.session_state:
    st.session_state.user = None

# ─── Login Screen (Clean Financilux Aesthetic: ONLY Username + Password) ─────
if not st.session_state.user or "error" in st.session_state.user:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"], [data-testid="stSidebarNav"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1.1, 1.2, 1.1])

    with col_center:
        # Small animated geometric design motif (replaces video)
        st.markdown(login_animation(), unsafe_allow_html=True)

        st.markdown("""
<div class="glass-card" style="padding: 32px 32px 20px 32px; text-align: center;">
  <div style="font-family: 'Inter', sans-serif; font-size: 0.76rem; color: #C8956C; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 6px;">
    StockShield Platform
  </div>
  <h2 style="font-size: 1.6rem; font-weight: 600; color: #2D2A26; margin-bottom: 6px;">
    Welcome back
  </h2>
  <p style="color: #7A7570; font-size: 0.88rem; margin-bottom: 20px;">
    Enter your credentials to access the workspace
  </p>
</div>
""", unsafe_allow_html=True)

        with st.form("clean_login_form"):
            username_input = st.text_input("Username", placeholder="e.g. admin or operator id")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submit_login:
                if username_input and password_input:
                    res = api.login_user(username_input.strip(), password_input.strip())
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.session_state.user = res
                        st.rerun()
                else:
                    st.warning("Please enter both username and password.")
    st.stop()


# ─── Authenticated Console ────────────────────────────────────────────────────
current_user = st.session_state.user
user_role = current_user.get("role", "EMPLOYEE").upper()
is_manager = (user_role == "MANAGER")
user_zone = current_user.get("assignedLocation")

sidebar_user_profile(current_user)

if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

st.sidebar.divider()

auto_refresh = st.sidebar.toggle("Auto-Refresh (5s)", value=False)
if st.sidebar.button("Refresh Now", use_container_width=True):
    st.rerun()

# ─── Simulator & Hardware Mode Controls (Manager Only) ──────────────────────
if is_manager:
    st.sidebar.divider()
    st.sidebar.markdown('<div class="section-header">Hardware / Simulator Mode</div>', unsafe_allow_html=True)

    if "sim_running" not in st.session_state:
        st.session_state.sim_running = True

    if st.session_state.sim_running:
        st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
  <div style="width: 10px; height: 10px; border-radius: 50%; background: #5B9A6F; animation: pulse-gentle 2s ease-in-out infinite;"></div>
  <span style="font-size: 0.78rem; color: #5B9A6F; font-weight: 500;">Simulator Active</span>
</div>
""", unsafe_allow_html=True)
        if st.sidebar.button("Switch to Hardware Only (Reset Fake Data)", use_container_width=True, type="primary"):
            api.reset_hardware_mode()
            st.session_state.sim_running = False
            st.toast("Switched to Hardware Mode! All fake records cleared.")
            st.rerun()
    else:
        st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
  <div style="width: 10px; height: 10px; border-radius: 50%; background: #C8956C;"></div>
  <span style="font-size: 0.78rem; color: #C8956C; font-weight: 500;">Hardware Mode (Waiting for ESP32)</span>
</div>
""", unsafe_allow_html=True)
        if st.sidebar.button("Reset Sensor Data to 0", use_container_width=True):
            api.reset_hardware_mode()
            st.toast("Sensors reset to OFFLINE, alerts cleared.")
            st.rerun()

        if st.sidebar.button("Enable Simulated Stream", use_container_width=True):
            st.session_state.sim_running = True
            st.rerun()

    st.sidebar.caption("Hardware Mode clears simulated records so only physical ESP32 packets show.")

st.sidebar.divider()

st.sidebar.markdown('<div class="section-header">Organization & Scope</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}

if is_manager:
    selected_label = st.sidebar.selectbox("Active Organization", list(tenant_map.keys()))
    active_tenant_id = tenant_map[selected_label]
    selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

    zone_options = ["All Zones", "dry-storage", "refrigerated", "frozen"]
    selected_zone_option = st.sidebar.selectbox("Zone Filter", zone_options)
    active_zone_filter = None if selected_zone_option == "All Zones" else selected_zone_option

    with st.sidebar.expander("Register Organization"):
        new_t_name = st.text_input("Organization Name")
        new_t_ind = st.selectbox(
            "Sector",
            ["retail_grocery", "cold_chain_logistics", "pharmaceutical", "chemical_manufacturing", "agriculture"]
        )
        if st.button("Create Tenant", use_container_width=True):
            if new_t_name:
                try:
                    api.create_tenant(new_t_name, new_t_ind)
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
else:
    active_tenant_id = "demo-tenant"
    selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {"name": "StockShield Demo", "industry": "retail_grocery"})
    active_zone_filter = user_zone

sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id, location_id=active_zone_filter)
sensors_online = summary.get("sensorsOnline", 0)
telemetry_up = sensors_online > 0

models = api.fetch_tenant_models(active_tenant_id)
ml_state = "READY" if models else "STANDBY"

scope_title = "Global View" if is_manager else f"Zone: {(user_zone or 'Restricted').capitalize()}"
render_breadcrumbs(["StockShield", selected_tenant.get('name', 'Facility'), scope_title])

header_banner(
    title=f"Dashboard — {'Manager Console' if is_manager else 'Employee Workspace'}",
    tenant_name=f"{selected_tenant.get('name', active_tenant_id)} · Scope: {active_zone_filter or 'All Zones'}",
    subtitle="Live shelf inventory weight, environmental telemetry, and real-time alerts",
    telemetry_online=telemetry_up,
    sector=selected_tenant.get('industry', ''),
    ml_state=ml_state,
)

if not telemetry_up:
    st.info("Awaiting hardware telemetry: Connect your ESP32 shelf nodes to Mosquitto (Port 1883) to begin live tracking.")

if is_manager:
    main_tabs = st.tabs(["Overview", "Employee Accounts", "Alert Logs"])
else:
    main_tabs = st.tabs(["Zone Telemetry", "Zone Inventory", "Zone Alerts"])

with main_tabs[0]:
    total_items   = summary.get("totalItems", 0)
    low_stock     = summary.get("lowStockCount", 0)
    active_alerts = summary.get("activeAlerts", 0)
    stock_health  = round(((total_items - low_stock) / total_items) * 100, 1) if total_items > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Sensors Online", sensors_online, delta="Active" if sensors_online > 0 else "Offline")
    with kpi2:
        st.metric("Stock Health", f"{stock_health}%", delta=f"{total_items - low_stock}/{total_items} items")
    with kpi3:
        st.metric("Avg Temp / Humidity", f"{summary.get('avgTemperature', 0.0):.1f} °C", delta=f"{summary.get('avgHumidity', 0.0):.1f} %")
    with kpi4:
        st.metric("Active Alerts", active_alerts, delta="Requires review" if active_alerts > 0 else "All clear", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    chart_col, feed_col = st.columns([2.1, 1])

    with chart_col:
        section_header("Live Sensor Telemetry")
        tab_chart1, tab_chart2 = st.tabs(["Telemetry Inspector", "Shelf Load Fill %"])

        with tab_chart1:
            inventory = api.fetch_inventory(tenant_id=active_tenant_id, zone=active_zone_filter)
            available_shelves = sorted(list({
                i.get("locationId", i.get("shelfId", "shelf-01"))
                for i in inventory if i.get("locationId") or i.get("shelfId")
            })) or ["shelf-01"]

            c_sel1, c_sel2 = st.columns([2, 1])
            with c_sel1:
                selected_shelf = st.selectbox("Shelf / Location Node", available_shelves, index=0, key="cmd_shelf_select")
            with c_sel2:
                selected_window = st.selectbox("Window", ["1h", "6h", "24h"], index=0, key="cmd_win_select")

            # Fetch all 3 readings: weight, temperature, humidity
            weight_pts = api.fetch_telemetry(selected_shelf, range_str=selected_window)
            if not weight_pts:
                weight_pts = api.fetch_generic_telemetry(active_tenant_id, selected_shelf, "weight", range_str=selected_window)

            env_pts = api.fetch_environment_history(selected_shelf, range_str=selected_window)
            if not env_pts:
                temp_pts = api.fetch_generic_telemetry(active_tenant_id, selected_shelf, "temperature", range_str=selected_window)
                hum_pts  = api.fetch_generic_telemetry(active_tenant_id, selected_shelf, "humidity", range_str=selected_window)
                env_pts  = temp_pts + hum_pts

            # Show latest reading cards for all 3 metrics
            latest_weight = None
            latest_temp = None
            latest_hum = None

            if weight_pts:
                try:
                    latest_weight = float(weight_pts[-1].get("value", 0))
                except (IndexError, ValueError, TypeError):
                    pass
            if env_pts:
                for pt in reversed(env_pts):
                    m = pt.get("measurement", pt.get("sensorType", ""))
                    if m == "temperature" and latest_temp is None:
                        try:
                            latest_temp = float(pt.get("value", 0))
                        except (ValueError, TypeError):
                            pass
                    if m == "humidity" and latest_hum is None:
                        try:
                            latest_hum = float(pt.get("value", 0))
                        except (ValueError, TypeError):
                            pass

            # ─── Threshold Check & Alarm ──────────────────────────────────────
            TEMP_MIN, TEMP_MAX = 20.0, 25.0
            HUM_MIN, HUM_MAX = 40.0, 60.0
            alarm_messages = []

            if latest_temp is not None:
                if latest_temp < TEMP_MIN:
                    alarm_messages.append(f"TEMPERATURE LOW: {latest_temp:.1f} °C (below {TEMP_MIN} °C)")
                elif latest_temp > TEMP_MAX:
                    alarm_messages.append(f"TEMPERATURE HIGH: {latest_temp:.1f} °C (above {TEMP_MAX} °C)")

            if latest_hum is not None:
                if latest_hum < HUM_MIN:
                    alarm_messages.append(f"HUMIDITY LOW: {latest_hum:.1f}% (below {HUM_MIN}%)")
                elif latest_hum > HUM_MAX:
                    alarm_messages.append(f"HUMIDITY HIGH: {latest_hum:.1f}% (above {HUM_MAX}%)")

            # Play buzzer alarm sound if any threshold is breached
            if alarm_messages:
                st.markdown("""
<script>
(function() {
    if (window._ssAlarmPlayed) return;
    window._ssAlarmPlayed = true;
    try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        function beep(freq, startTime, duration) {
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'square';
            osc.frequency.value = freq;
            gain.gain.value = 0.3;
            osc.start(startTime);
            osc.stop(startTime + duration);
        }
        // 3 rapid alarm beeps
        var t = ctx.currentTime;
        beep(880, t, 0.15);
        beep(880, t + 0.25, 0.15);
        beep(880, t + 0.50, 0.15);
        beep(1200, t + 0.75, 0.3);
        setTimeout(function(){ window._ssAlarmPlayed = false; }, 6000);
    } catch(e) {}
})();
</script>
""", unsafe_allow_html=True)

                for msg in alarm_messages:
                    st.error(f"ALERT: {msg}")

                st.markdown(f"""
<div class="glass-card" style="padding: 16px 20px; border-left: 4px solid #C7544A; background: rgba(199, 84, 74, 0.08);">
  <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
    <div style="width: 12px; height: 12px; border-radius: 50%; background: #C7544A; animation: pulse-gentle 1s ease-in-out infinite;"></div>
    <span style="font-size: 0.88rem; font-weight: 600; color: #C7544A;">THRESHOLD BREACH DETECTED</span>
  </div>
  <div style="font-size: 0.82rem; color: #4A4541;">
    Safe Range: Temperature {TEMP_MIN}°C – {TEMP_MAX}°C | Humidity {HUM_MIN}% – {HUM_MAX}%
  </div>
</div>
""", unsafe_allow_html=True)

            # ─── Metric Cards ─────────────────────────────────────────────────
            temp_ok = latest_temp is not None and TEMP_MIN <= latest_temp <= TEMP_MAX
            hum_ok = latest_hum is not None and HUM_MIN <= latest_hum <= HUM_MAX

            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Load Cell (Weight)", f"{latest_weight:.2f} kg" if latest_weight is not None else "No data", delta="HX711 Strain Gauge" if latest_weight is not None else "Waiting")
            with r2:
                temp_delta = "Normal (20-25°C)" if temp_ok else ("ALERT! Out of range" if latest_temp is not None else "Waiting")
                st.metric("Temperature", f"{latest_temp:.1f} °C" if latest_temp is not None else "No data", delta=temp_delta, delta_color="normal" if temp_ok else "inverse")
            with r3:
                hum_delta = "Normal (40-60%)" if hum_ok else ("ALERT! Out of range" if latest_hum is not None else "Waiting")
                st.metric("Humidity", f"{latest_hum:.1f} %" if latest_hum is not None else "No data", delta=hum_delta, delta_color="normal" if hum_ok else "inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            if weight_pts or env_pts:
                # Parse all data with safe datetime parsing
                def safe_dt(series):
                    return pd.to_datetime(series, utc=True, format="mixed")

                # ─── Chart 1: Temperature vs Time (Line Chart) ───────────────
                section_header("Temperature Over Time")
                if env_pts:
                    df_e = pd.DataFrame(env_pts)
                    ts_col = "time" if "time" in df_e.columns else "timestamp"
                    df_e[ts_col] = safe_dt(df_e[ts_col])
                    df_e = df_e.sort_values(ts_col)
                    if "measurement" in df_e.columns:
                        df_t = df_e[df_e["measurement"] == "temperature"]
                        df_h = df_e[df_e["measurement"] == "humidity"]
                    else:
                        df_t = pd.DataFrame()
                        df_h = pd.DataFrame()

                    if not df_t.empty:
                        fig_temp = go.Figure()
                        fig_temp.add_trace(go.Scatter(
                            x=df_t[ts_col], y=df_t["value"],
                            name="Temperature (°C)",
                            line=dict(color=TRACE_CORAL, width=2.5),
                            mode="lines+markers", fill="tozeroy",
                            fillcolor="rgba(200,149,108,0.1)"
                        ))
                        # Add threshold lines
                        fig_temp.add_hline(y=TEMP_MAX, line_dash="dash", line_color=TRACE_CRIMSON, annotation_text=f"Max Safe ({TEMP_MAX}°C)")
                        fig_temp.add_hline(y=TEMP_MIN, line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"Min Safe ({TEMP_MIN}°C)")
                        fig_temp.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=300,
                            yaxis_title="Temperature (°C)", xaxis_title="Time")
                        st.plotly_chart(fig_temp, use_container_width=True)
                    else:
                        st.info("No temperature data available.")
                else:
                    st.info("No environment data available.")

                # ─── Chart 2: Humidity vs Time (Area Chart) ───────────────────
                section_header("Humidity Over Time")
                if env_pts and not df_h.empty:
                    fig_hum = go.Figure()
                    fig_hum.add_trace(go.Scatter(
                        x=df_h[ts_col], y=df_h["value"],
                        name="Humidity (%)",
                        line=dict(color=TRACE_CYAN, width=2),
                        mode="lines+markers", fill="tozeroy",
                        fillcolor="rgba(107,143,163,0.12)"
                    ))
                    fig_hum.add_hline(y=HUM_MAX, line_dash="dash", line_color=TRACE_CRIMSON, annotation_text=f"Max Safe ({HUM_MAX}%)")
                    fig_hum.add_hline(y=HUM_MIN, line_dash="dash", line_color=TRACE_AMBER, annotation_text=f"Min Safe ({HUM_MIN}%)")
                    fig_hum.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=300,
                        yaxis_title="Humidity (%)", xaxis_title="Time")
                    st.plotly_chart(fig_hum, use_container_width=True)
                else:
                    st.info("No humidity data available.")

                # ─── Chart 3: Weight / Load Cell vs Time (Bar Chart) ──────────
                section_header("Load Cell Weight Over Time")
                if weight_pts:
                    df_w = pd.DataFrame(weight_pts)
                    ts_col_w = "time" if "time" in df_w.columns else "timestamp"
                    df_w[ts_col_w] = safe_dt(df_w[ts_col_w])
                    df_w = df_w.sort_values(ts_col_w)

                    fig_wt = go.Figure()
                    fig_wt.add_trace(go.Bar(
                        x=df_w[ts_col_w], y=df_w["value"],
                        name="Weight (kg)",
                        marker_color=TRACE_EMERALD,
                        marker_line_width=0,
                    ))
                    fig_wt.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=300,
                        yaxis_title="Weight (kg)", xaxis_title="Time", bargap=0.3)
                    st.plotly_chart(fig_wt, use_container_width=True)
                else:
                    st.info("No weight/load cell data available.")
            else:
                st.markdown(f"""
<div class="glass-card" style="padding: 32px 24px; text-align: center;">
  <div style="font-size: 0.85rem; font-weight: 600; color: #C8956C; margin-bottom: 6px;">
    Awaiting Telemetry Stream
  </div>
  <div style="font-weight: 500; font-size: 0.95rem; color: #2D2A26;">
    No telemetry points recorded yet for node <code>{selected_shelf}</code> ({selected_window})
  </div>
  <div style="font-size: 0.82rem; color: #7A7570; margin-top: 6px;">
    Real ESP32 hardware will stream to <code>stockshield/shelf/{selected_shelf}/...</code>
  </div>
</div>
""", unsafe_allow_html=True)

        with tab_chart2:
            if inventory:
                df_inv = pd.DataFrame(inventory)
                df_inv["weight_pct"] = (df_inv["currentWeight"] / df_inv["fullWeight"]) * 100

                # Bar Chart: Fill % per item
                section_header("Shelf Fill Ratio (Bar Chart)")
                fig_bar = px.bar(
                    df_inv, x="name", y="weight_pct",
                    color="stockLevel",
                    color_discrete_map={
                        "FULL": TRACE_EMERALD,
                        "OPTIMAL": TRACE_EMERALD,
                        "ADEQUATE": TRACE_CYAN,
                        "LOW": TRACE_AMBER,
                        "CRITICAL": TRACE_CRIMSON,
                        "EMPTY": TRACE_CRIMSON
                    },
                    labels={"weight_pct": "Fill Ratio (%)", "name": "Item"}
                )
                fig_bar.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=320)
                st.plotly_chart(fig_bar, use_container_width=True)

                # Pie Chart: Stock Level Distribution
                section_header("Stock Level Distribution (Pie Chart)")
                stock_counts = df_inv["stockLevel"].value_counts().reset_index()
                stock_counts.columns = ["Stock Level", "Count"]
                color_map = {
                    "FULL": TRACE_EMERALD, "OPTIMAL": TRACE_EMERALD,
                    "ADEQUATE": TRACE_CYAN, "LOW": TRACE_AMBER,
                    "CRITICAL": TRACE_CRIMSON, "EMPTY": TRACE_CRIMSON
                }
                fig_pie = px.pie(
                    stock_counts, names="Stock Level", values="Count",
                    color="Stock Level", color_discrete_map=color_map,
                    hole=0.4
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#F5F0EB",
                    font=dict(color="#4A4541", family="Inter, sans-serif"),
                    height=320,
                    legend=dict(font=dict(size=11)),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

                # Horizontal Bar: Current Weight vs Full Weight
                section_header("Current vs Full Capacity (Gauge)")
                fig_gauge = go.Figure()
                fig_gauge.add_trace(go.Bar(
                    y=df_inv["name"], x=df_inv["fullWeight"],
                    name="Full Capacity", orientation="h",
                    marker_color="rgba(232,224,216,0.5)",
                    marker_line_width=0,
                ))
                fig_gauge.add_trace(go.Bar(
                    y=df_inv["name"], x=df_inv["currentWeight"],
                    name="Current Stock", orientation="h",
                    marker_color=TRACE_EMERALD,
                    marker_line_width=0,
                ))
                gauge_layout = dict(PLOTLY_LAYOUT_DEFAULTS)
                gauge_layout["height"] = 300
                gauge_layout["barmode"] = "overlay"
                gauge_layout["xaxis_title"] = "Weight (kg)"
                gauge_layout["yaxis_title"] = ""
                gauge_layout["legend"] = dict(orientation="h", y=1.1)
                fig_gauge.update_layout(**gauge_layout)
                st.plotly_chart(fig_gauge, use_container_width=True)
            else:
                st.info("No inventory items found for this selection.")

    with feed_col:
        section_header("Recent Incidents")
        alerts = api.fetch_recent_alerts(limit=10, tenant_id=active_tenant_id, location_id=active_zone_filter)
        if alerts:
            for alt in alerts[:6]:
                sev = alt.get("severity", "WARNING").upper()
                c = "crimson" if sev == "CRITICAL" else "amber"
                st.markdown(f"""
<div class="glass-card" style="padding: 14px 16px; margin-bottom: 8px;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
    {badge(sev, c)}
    <span style="font-size: 0.72rem; color: #7A7570;">{str(alt.get('createdAt', ''))[:19].replace('T', ' ')}</span>
  </div>
  <div style="font-size: 0.88rem; font-weight: 500; color: #2D2A26;">{alt.get('message', '')}</div>
  <div style="font-size: 0.74rem; color: #7A7570; margin-top: 6px;">
    Node: {alt.get('locationId', 'N/A')} | Metric: {alt.get('sensorType', 'weight')}
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div class="glass-card" style="padding: 24px; text-align: center;">
  <div style="font-size: 0.85rem; font-weight: 600; color: #5B9A6F;">All Systems Nominal</div>
  <div style="font-size: 0.82rem; color: #7A7570; margin-top: 4px;">Zero unacknowledged alerts in active scope.</div>
</div>
""", unsafe_allow_html=True)

with main_tabs[1]:
    if is_manager:
        section_header("Create & Manage Employee Credentials")
        col_add, col_list = st.columns([1, 1.4])

        with col_add:
            with st.form("create_employee_form", clear_on_submit=True):
                st.markdown("<p style='font-size: 0.85rem; font-weight: 500; margin-bottom: 8px;'>Provision New Employee</p>", unsafe_allow_html=True)
                emp_user = st.text_input("Username", placeholder="e.g. cold_emp_02")
                emp_name = st.text_input("Full Name", placeholder="Employee Name")
                emp_pass = st.text_input("Password", type="password")
                emp_zone = st.selectbox("Assigned Storage Area", ["cold storage", "dry storage", "refrigerated", "frozen"])
                emp_email = st.text_input("Email", placeholder="employee@stockshield.local")

                if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                    if emp_user and emp_pass:
                        try:
                            # Map clean names to zone keys
                            zone_val = emp_zone.replace(" ", "-") if " " in emp_zone else emp_zone
                            api.create_employee(emp_user, emp_pass, emp_name, zone_val, emp_email)
                            st.success(f"Account '{emp_user}' created successfully for {emp_zone}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create employee: {e}")

        with col_list:
            st.markdown("<p style='font-size: 0.85rem; font-weight: 500; margin-bottom: 8px;'>Active Team Members</p>", unsafe_allow_html=True)
            employees = api.fetch_employees()
            if employees:
                for emp in employees:
                    role_b = "manager" if emp.get("role") == "MANAGER" else "employee"
                    zone_label = emp.get("assignedLocation") or "All Zones"
                    is_root = (emp.get("username") == "admin")

                    c_info, c_action = st.columns([3.2, 1])
                    with c_info:
                        st.markdown(f"""
<div style="padding: 6px 0;">
  <span class="user-role-tag {role_b}">{emp.get('role')}</span>
  <strong style="color: #2D2A26; margin-left: 8px; font-size: 0.92rem;">{emp.get('fullName', emp.get('username'))}</strong>
  <code style="margin-left: 6px;">@{emp.get('username')}</code>
  <div style="font-size: 0.76rem; color: #7A7570; margin-top: 4px;">
    Assigned Area: <strong>{zone_label}</strong> | Email: {emp.get('email', 'N/A')}
  </div>
</div>
""", unsafe_allow_html=True)
                    with c_action:
                        if not is_root and emp.get("id"):
                            if st.button("Delete", key=f"del_user_{emp['id']}", use_container_width=True):
                                api.delete_employee(emp["id"])
                                st.rerun()
                    st.divider()
    else:
        section_header(f"Zone Inventory — {(user_zone or 'Assigned Area').capitalize()}")
        items = api.fetch_inventory(zone=user_zone)
        if items:
            df = pd.DataFrame(items)
            cols_show = ["id", "name", "category", "currentWeight", "fullWeight", "unit", "stockLevel"]
            st.dataframe(df[[c for c in cols_show if c in df.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("No inventory items found in your assigned storage area.")

with main_tabs[2]:
    section_header(f"Incident Audit Log — {'All Zones' if is_manager else user_zone.capitalize() if user_zone else 'Scoped'}")
    all_alerts = api.fetch_recent_alerts(
        limit=50,
        tenant_id=active_tenant_id,
        location_id=None if is_manager else user_zone
    )
    if all_alerts:
        st.dataframe(pd.DataFrame(all_alerts), use_container_width=True, hide_index=True)
    else:
        st.info("No incidents logged.")

if auto_refresh:
    time.sleep(5)
    st.rerun()
