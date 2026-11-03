import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random, datetime
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
    TRACE_AMBER,
    TRACE_CRIMSON,
)

st.set_page_config(
    page_title="StockShield Command Center",
    page_icon="🛡️",
    layout="wide",
)

inject_global_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
selected_label = st.sidebar.selectbox("Active Tenant", list(tenant_map.keys()))
active_tenant_id = tenant_map[selected_label]
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)
st.sidebar.divider()

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

# ─── Fetch data ───────────────────────────────────────────────────────────────
try:
    summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id)
    telemetry_up = summary.get("sensorsOnline", 0) > 0
except Exception:
    summary = {}
    telemetry_up = False

models = api.fetch_tenant_models(active_tenant_id)
ml_state = "READY" if models else "NO MODELS"

# ─── Header Banner ────────────────────────────────────────────────────────────
header_banner(
    title="StockShield Command Center",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle=f"IoT Telemetry · Anomaly Detection · Self-Trained ML  ·  {selected_tenant.get('industry', 'All Industries').upper()}",
    telemetry_online=telemetry_up,
    sector=selected_tenant.get('industry', ''),
    ml_state=ml_state,
)

# ─── Row 1: KPI Strip ─────────────────────────────────────────────────────────
sensors_online = summary.get("sensorsOnline", 0)
total_items    = summary.get("totalItems", 0)
low_stock      = summary.get("lowStockCount", 0)
active_alerts  = summary.get("activeAlerts", 0)
stock_health   = round(((total_items - low_stock) / total_items) * 100, 1) if total_items > 0 else 100.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("🟢 Sensors Online", sensors_online)
with kpi2:
    st.metric("📦 Buffer Stock Health", f"{stock_health}%",
              delta=f"{total_items - low_stock} of {total_items} OK")
with kpi3:
    st.metric("❄️ Monitored Assets", total_items)
with kpi4:
    st.metric("🔔 Active Alerts", active_alerts,
              delta=f"{active_alerts} active" if active_alerts > 0 else "All clear",
              delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 2: Charts (2:1) ─────────────────────────────────────────────────────
chart_col, feed_col = st.columns([2, 1])

with chart_col:
    section_header("📈 Live Telemetry Overview")

    # Try to get real telemetry; fall back to demo sparkline
    sensor_types = api.fetch_sensor_types(active_tenant_id)
    inventory     = api.fetch_inventory()
    locations     = sorted(list(set([
        item.get('locationId', item.get('shelfId'))
        for item in inventory if item.get('locationId') or item.get('shelfId')
    ]))) or ["shelf-01", "cold-vault-01"]

    tab_chart1, tab_chart2, tab_chart3 = st.tabs(["📡 Sensor Trend", "📊 Stock Levels", "🔔 Alert Timeline"])

    # ── Tab 1: Sensor Trend ────────────────────────────────────────────────────
    with tab_chart1:
        c1, c2 = st.columns(2)
        with c1:
            sel_loc = st.selectbox("Location", locations, key="ov_loc")
        with c2:
            codes = [s['code'] for s in sensor_types] if sensor_types else ["temperature", "humidity", "pressure"]
            sel_sensor = st.selectbox("Metric", codes, key="ov_sensor")

        telemetry_data = []
        s_def = next((s for s in sensor_types if s['code'] == sel_sensor), None)
        unit  = s_def.get('unit', '') if s_def else ''

        try:
            telemetry_data = api.fetch_generic_telemetry(active_tenant_id, sel_loc, sel_sensor, range_str="6h")
        except Exception:
            if sel_sensor in ["temperature", "humidity"]:
                try:
                    env = api.fetch_environment_history(sel_loc, range_str="6h")
                    telemetry_data = [{"timestamp": p.get("timestamp"), "value": p.get(sel_sensor)} for p in env]
                except Exception:
                    pass

        fig1 = go.Figure()

        if telemetry_data:
            df_t = pd.DataFrame(telemetry_data)
            df_t['timestamp'] = pd.to_datetime(df_t['timestamp'])
            df_t = df_t.sort_values('timestamp')

            # Safe zone fill
            if s_def and s_def.get('minSafe') is not None and s_def.get('maxSafe') is not None:
                fig1.add_hrect(y0=s_def['minSafe'], y1=s_def['maxSafe'],
                               fillcolor="rgba(16,185,129,0.07)", line_width=0,
                               annotation_text="Safe Zone",
                               annotation_font=dict(color="#10B981", size=10))

            fig1.add_trace(go.Scatter(
                x=df_t['timestamp'], y=df_t['value'],
                mode='lines+markers', name=sel_sensor,
                line=dict(color=TRACE_CYAN, width=2.5),
                marker=dict(size=4, color=TRACE_CYAN),
                fill='tozeroy', fillcolor='rgba(0,229,255,0.05)',
            ))

            # Threshold lines
            if s_def:
                for key, dash, color in [('maxSafe','dash',TRACE_AMBER),('minSafe','dash',TRACE_AMBER),
                                          ('criticalMax','dot',TRACE_CRIMSON),('criticalMin','dot',TRACE_CRIMSON)]:
                    if s_def.get(key) is not None:
                        fig1.add_hline(y=s_def[key], line_dash=dash, line_color=color, line_width=1.2)
        else:
            # Demo sparkline if no data
            now = datetime.datetime.utcnow()
            times = [now - datetime.timedelta(minutes=30*i) for i in range(12, 0, -1)]
            vals  = [20 + random.gauss(0, 3) for _ in times]
            fig1.add_trace(go.Scatter(
                x=times, y=vals, mode='lines',
                name="Demo Data",
                line=dict(color=TRACE_CYAN, width=2, dash='dot'),
                fill='tozeroy', fillcolor='rgba(0,229,255,0.04)',
            ))
            fig1.add_annotation(text="⚠ Live data unavailable — showing demo sparkline",
                                xref="paper", yref="paper", x=0.5, y=0.95,
                                showarrow=False, font=dict(color="#F59E0B", size=11))

        fig1.update_layout(**PLOTLY_LAYOUT_DEFAULTS,
                           title=f"{sel_sensor.capitalize()} @ {sel_loc} (6h)",
                           yaxis_title=f"{sel_sensor} ({unit})", height=320)
        st.plotly_chart(fig1, use_container_width=True)

    # ── Tab 2: Stock Levels ────────────────────────────────────────────────────
    with tab_chart2:
        try:
            inv = api.fetch_inventory()
            if inv:
                df_inv = pd.DataFrame(inv)
                if 'tenantId' in df_inv.columns:
                    t_inv = df_inv[df_inv['tenantId'] == active_tenant_id]
                    if not t_inv.empty:
                        df_inv = t_inv

                if 'stockPercentage' in df_inv.columns and 'name' in df_inv.columns:
                    df_inv['pct'] = (df_inv['stockPercentage'] * 100).round(1)
                    df_inv = df_inv.sort_values('pct')

                    bar_colors = [
                        TRACE_CRIMSON if p < 20 else TRACE_AMBER if p < 50 else TRACE_EMERALD
                        for p in df_inv['pct']
                    ]

                    fig2 = go.Figure(go.Bar(
                        x=df_inv['pct'],
                        y=df_inv['name'].str[:20],
                        orientation='h',
                        marker_color=bar_colors,
                        marker_line_width=0,
                        text=[f"{p}%" for p in df_inv['pct']],
                        textposition='outside',
                        textfont=dict(color='#94A3B8', size=11),
                    ))
                    fig2.update_layout(**PLOTLY_LAYOUT_DEFAULTS,
                                       title="Buffer Stock Levels by Asset",
                                       xaxis_title="Stock %",
                                       xaxis=dict(**PLOTLY_LAYOUT_DEFAULTS['xaxis'], range=[0, 115]),
                                       height=max(280, len(df_inv) * 36))
                    fig2.add_vline(x=20, line_dash="dot", line_color=TRACE_CRIMSON,
                                   annotation_text="Critical", annotation_font=dict(color=TRACE_CRIMSON, size=10))
                    fig2.add_vline(x=50, line_dash="dash", line_color=TRACE_AMBER,
                                   annotation_text="Warning", annotation_font=dict(color=TRACE_AMBER, size=10))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Stock percentage data not available.")
            else:
                st.info("No inventory data found.")
        except Exception as e:
            st.warning(f"Could not load stock chart: {e}")

    # ── Tab 3: Alert Timeline ─────────────────────────────────────────────────
    with tab_chart3:
        try:
            all_alerts = api.fetch_recent_alerts(limit=100, tenant_id=active_tenant_id)
            if all_alerts:
                df_al = pd.DataFrame(all_alerts)
                time_col = 'createdAt' if 'createdAt' in df_al.columns else 'timestamp'
                df_al['ts'] = pd.to_datetime(df_al[time_col])
                df_al['hour'] = df_al['ts'].dt.floor('H')
                sev_counts = df_al.groupby(['hour', 'severity']).size().reset_index(name='count')

                fig3 = go.Figure()
                color_map = {'CRITICAL': TRACE_CRIMSON, 'WARNING': TRACE_AMBER, 'INFO': TRACE_CYAN}
                for sev, color in color_map.items():
                    df_s = sev_counts[sev_counts['severity'] == sev]
                    if not df_s.empty:
                        fig3.add_trace(go.Bar(
                            name=sev, x=df_s['hour'], y=df_s['count'],
                            marker_color=color, marker_line_width=0,
                        ))

                fig3.update_layout(**PLOTLY_LAYOUT_DEFAULTS,
                                   title="Alert Frequency by Hour",
                                   barmode='stack', xaxis_title="Time",
                                   yaxis_title="Alert Count", height=320)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.success("✅ No alerts — all systems nominal.")
        except Exception as e:
            st.warning(f"Could not load alert timeline: {e}")

# ── Right: Alert Feed ──────────────────────────────────────────────────────────
with feed_col:
    section_header("🔔 Live Alert Feed")
    try:
        alerts = api.fetch_recent_alerts(limit=8, tenant_id=active_tenant_id)
        if alerts:
            for alert in alerts[:6]:
                severity = alert.get('severity', 'INFO')
                sev_variant = {'CRITICAL': 'crimson', 'WARNING': 'amber', 'INFO': 'cyan'}.get(severity, 'cyan')
                sensor_type = alert.get('sensorType', alert.get('type', 'general'))
                message     = alert.get('message', 'No details')[:60]
                location    = alert.get('locationId', alert.get('shelfId', '—'))
                badge_html  = badge(severity, sev_variant)
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
  <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">No active alerts</div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
<div class="glass-card">
  <span style="color:#EF4444;font-size:0.82rem;">⚠️ Alert feed unavailable: {e}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 3: Sensor Cards + System Health ─────────────────────────────────────
section_header("📡 Registered Sensor Types & Thresholds")
if sensor_types:
    grid_cols = st.columns(min(len(sensor_types), 4) or 1)
    for idx, s in enumerate(sensor_types):
        with grid_cols[idx % len(grid_cols)]:
            ml_badge_html  = badge("✅ ML ON",  "emerald") if s.get("mlEnabled") else badge("❌ ML OFF", "crimson")
            cat_badge_html = badge(s.get("category", "metric"), "cyan")
            st.markdown(f"""
<div class="glass-card" style="padding:14px;">
  <div style="font-size:0.92rem;font-weight:700;color:#F8FAFC;margin-bottom:6px;">
    {s.get('displayName', s['code'])}
  </div>
  <div style="margin-bottom:8px;">
    <code style="color:#00E5FF;font-size:0.72rem;">{s['code']}</code>&nbsp;{cat_badge_html}
  </div>
  <div style="font-size:0.75rem;color:#94A3B8;line-height:1.8;">
    Safe: <strong style="color:#F8FAFC;">{s.get('minSafe','–')}–{s.get('maxSafe','–')} {s.get('unit','')}</strong><br>
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
    No sensor types configured for <strong style="color:#F8FAFC;">{selected_tenant.get('name')}</strong>.
    Visit the <strong style="color:#00E5FF;">Sensor Registry</strong> page.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 4: System Health Tab ─────────────────────────────────────────────────
section_header("🖥️ System Health")
h1, h2, h3, h4 = st.columns(4)
with h1:
    st.metric("Backend API",  "🟢 UP" if telemetry_up else "🔴 DOWN")
with h2:
    st.metric("ML Service",   "🟢 UP" if models is not None else "🔴 DOWN")
with h3:
    st.metric("MQTT Broker",  "🟢 Active")
with h4:
    st.metric("Trained Models", len(models) if models else 0)
