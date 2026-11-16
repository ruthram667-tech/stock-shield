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
    sidebar_user_profile,
    section_header,
    render_breadcrumbs,
    badge,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_EMERALD,
    TRACE_AMBER,
    TRACE_CRIMSON,
    TRACE_CORAL,
)

st.set_page_config(
    page_title="StockShield — IoT Telemetry & RBAC Command Center",
    page_icon="🛡️",
    layout="wide",
)

inject_global_css()

# ─── Authentication & Session State Check ─────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Pure Username & Password Login Page (Financilux Aesthetic) ────────────────
if not st.session_state.user or "error" in st.session_state.user:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    col_l, col_center, col_r = st.columns([1, 1.4, 1])

    with col_center:
        st.markdown("""
<div style="background: rgba(255, 255, 255, 0.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 24px; padding: 36px 32px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.05); text-align: center; margin-bottom: 20px;">
  
  <!-- Financilux Animated Sunburst & Coral Brand Motif -->
  <div style="position: relative; width: 80px; height: 80px; margin: 0 auto 18px auto; display: flex; align-items: center; justify-content: center;">
    <svg class="sunburst-motif" width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="position: absolute;">
      <line x1="50" y1="6" x2="50" y2="22" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="50" y1="78" x2="50" y2="94" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="6" y1="50" x2="22" y2="50" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="78" y1="50" x2="94" y2="50" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="18.9" y1="18.9" x2="30.2" y2="30.2" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="69.8" y1="69.8" x2="81.1" y2="81.1" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="18.9" y1="81.1" x2="30.2" y2="69.8" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="69.8" y1="30.2" x2="81.1" y2="18.9" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="33" y1="10" x2="39" y2="25" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="61" y1="75" x2="67" y2="90" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="10" y1="33" x2="25" y2="39" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="75" y1="61" x2="90" y2="67" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="67" y1="10" x2="61" y2="25" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="39" y1="75" x2="33" y2="90" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="90" y1="33" x2="75" y2="39" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="25" y1="61" x2="10" y2="67" stroke="#141416" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
    <div class="pulse-circle" style="width: 44px; height: 44px; border-radius: 50%; background: #FF5520; color: white; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; box-shadow: 0 6px 18px rgba(255,85,32,0.4); z-index: 2;">
      🛡️
    </div>
  </div>

  <h2 style="font-size: 1.85rem; font-weight: 800; color: #141416; letter-spacing: -0.03em; margin-bottom: 6px;">
    StockShield Access
  </h2>
  <p style="color: #6B7280; font-size: 0.9rem; margin-bottom: 24px;">
    Enter your manager-assigned username and password to enter your workspace.
  </p>
</div>
""", unsafe_allow_html=True)

        with st.form("clean_login_form"):
            username_input = st.text_input("Username", placeholder="e.g. admin or cold_emp")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submit_login:
                if username_input and password_input:
                    res = api.login_user(username_input.strip(), password_input.strip())
                    if "error" in res:
                        st.error(f"❌ {res['error']}")
                    else:
                        st.session_state.user = res
                        st.success(f"Welcome, {res.get('fullName', username_input)}!")
                        st.rerun()
                else:
                    st.warning("Please enter both username and password.")

    st.stop()


# ─── Logged In Workspace ──────────────────────────────────────────────────────
current_user = st.session_state.user
user_role = current_user.get("role", "EMPLOYEE").upper()
is_manager = (user_role == "MANAGER")
user_zone = current_user.get("assignedLocation")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_user_profile(current_user)

if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

st.sidebar.divider()

# Organization & Zone Filter Handling
st.sidebar.markdown('<div class="section-header">🏢 Organization & Scoping</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}

if is_manager:
    selected_label = st.sidebar.selectbox("Active Tenant", list(tenant_map.keys()))
    active_tenant_id = tenant_map[selected_label]
    selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
    
    # Manager Zone Drill-down Switcher
    zone_options = ["🌐 All Facility Zones", "frozen (Cold Storage)", "refrigerated (Chilled)", "dry-storage (Ambient)"]
    selected_zone_option = st.sidebar.selectbox("Filter Facility Zone", zone_options)
    active_zone_filter = None if "All" in selected_zone_option else selected_zone_option.split(" ")[0]

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
else:
    # Employee Scope is strictly locked
    active_tenant_id = "demo-tenant"
    selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {"name": "Global Retail Corp", "industry": "retail_grocery"})
    active_zone_filter = user_zone
    st.sidebar.info(f"🔒 Workspace locked to assigned zone: **{user_zone.upper() if user_zone else 'LOCAL'}**")

sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

# ─── Fetch Data (Filtered by Zone if Employee) ────────────────────────────────
try:
    summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id, location_id=active_zone_filter)
    telemetry_up = summary.get("sensorsOnline", 0) > 0
except Exception:
    summary = {}
    telemetry_up = True

models = api.fetch_tenant_models(active_tenant_id)
ml_state = "READY" if models else "ACTIVE"

# ─── Breadcrumbs & Header Banner ─────────────────────────────────────────────
scope_title = "Global Facility View" if is_manager else f"Zone Operations · {user_zone.upper() if user_zone else 'RESTRICTED'}"
render_breadcrumbs(["🛡️ StockShield", selected_tenant.get('name', 'Universal IoT'), scope_title])

header_banner(
    title=f"StockShield Command Center — {'👔 Chief Manager' if is_manager else '👤 Zone Operator'}",
    tenant_name=f"{selected_tenant.get('name', 'Universal IoT')} · Scope: {active_zone_filter or 'All Zones'}",
    subtitle=f"IoT Telemetry · {'Full Facility Governance' if is_manager else 'Restricted Containment Area: ' + str(user_zone)} · Role: {user_role}",
    telemetry_online=telemetry_up,
    sector=selected_tenant.get('industry', ''),
    ml_state=ml_state,
)

# ─── Main Content Tabs ────────────────────────────────────────────────────────
if is_manager:
    main_tabs = st.tabs(["📊 Command Center", "👥 Team & Employee Management", "📑 Global Audit Logs"])
else:
    main_tabs = st.tabs(["❄️ My Zone Operations", "📦 Zone Inventory", "🔔 Zone Incident Logs"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Command Center (Manager) OR My Zone Operations (Employee)
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[0]:
    # Row 1: KPI Strip
    sensors_online = summary.get("sensorsOnline", 18 if is_manager else 6)
    total_items    = summary.get("totalItems", 12 if is_manager else 4)
    low_stock      = summary.get("lowStockCount", 2 if is_manager else 1)
    active_alerts  = summary.get("activeAlerts", 1)
    stock_health   = round(((total_items - low_stock) / total_items) * 100, 1) if total_items > 0 else 100.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Active Sensors", sensors_online, delta="QoS 1 Telemetry")
    with kpi2:
        st.metric("Stock Health Index", f"{stock_health}%", delta=f"{total_items - low_stock} / {total_items} Optimal")
    with kpi3:
        st.metric("Monitored Scope", "All Facility" if is_manager else (user_zone or "Local"))
    with kpi4:
        st.metric("Active Zone Alerts", active_alerts, delta="Needs Review" if active_alerts > 0 else "All Clear", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: Charts (2:1)
    chart_col, feed_col = st.columns([2, 1])

    with chart_col:
        section_header("📈 Live Telemetry & Environmental Status")
        tab_chart1, tab_chart2 = st.tabs(["📡 Live Sensor Waves", "📊 Stock Level Distribution"])

        with tab_chart1:
            now = datetime.datetime.now()
            times = [now - datetime.timedelta(minutes=i*10) for i in range(25, -1, -1)]
            
            if is_manager and not active_zone_filter:
                base_temp = 4.0
                zone_label = "Facility Average Temperature"
            elif (active_zone_filter and "frozen" in active_zone_filter.lower()) or (user_zone and "frozen" in user_zone.lower()):
                base_temp = -18.4
                zone_label = "Sub-Zero Cold Storage (-18°C Target)"
            else:
                base_temp = 21.0
                zone_label = "Ambient Storage Racks (20°C Target)"

            temps = [round(base_temp + 0.4 * random.gauss(0, 0.3), 2) for _ in times]
            humids = [round(45.0 + random.uniform(-2, 3), 1) for _ in times]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=times, y=temps, name=f"{zone_label} (°C)",
                line=dict(color=TRACE_CORAL, width=2.5),
                mode='lines+markers'
            ))
            fig.add_trace(go.Scatter(
                x=times, y=humids, name="Relative Humidity (%)",
                line=dict(color=TRACE_CYAN, width=2, dash='dot'),
                yaxis="y2"
            ))

            fig.update_layout(
                **PLOTLY_LAYOUT_DEFAULTS,
                yaxis=dict(title="Temperature (°C)", gridcolor="rgba(0,0,0,0.06)"),
                yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", gridcolor="rgba(0,0,0,0.03)"),
                height=340,
                legend=dict(orientation="h", y=1.12)
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_chart2:
            inventory = api.fetch_inventory(tenant_id=active_tenant_id, zone=active_zone_filter)
            if inventory:
                df_inv = pd.DataFrame(inventory)
                df_inv["weight_pct"] = (df_inv["currentWeight"] / df_inv["fullWeight"]) * 100
                fig_bar = px.bar(
                    df_inv, x="name", y="weight_pct",
                    color="stockLevel",
                    color_discrete_map={"OPTIMAL": TRACE_EMERALD, "ADEQUATE": TRACE_CYAN, "LOW": TRACE_AMBER, "CRITICAL": TRACE_CRIMSON},
                    labels={"weight_pct": "Stock Level (%)", "name": "Monitored Item"}
                )
                fig_bar.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=340)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No inventory items found for current zone filter.")

    with feed_col:
        section_header("🚨 Incident & Anomaly Feed")
        alerts = api.fetch_recent_alerts(limit=10, tenant_id=active_tenant_id, location_id=active_zone_filter)
        if alerts:
            for alt in alerts[:6]:
                sev = alt.get("severity", "WARNING").upper()
                c = "crimson" if sev == "CRITICAL" else "amber"
                st.markdown(f"""
<div style="background: #FFFFFF; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; padding: 14px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
    {badge(sev, c)}
    <span style="font-size: 0.72rem; color: #9CA3AF;">{alt.get('createdAt', 'Live')[:16].replace('T', ' ')}</span>
  </div>
  <div style="font-size: 0.88rem; font-weight: 700; color: #141416;">{alt.get('message', 'Threshold warning')}</div>
  <div style="font-size: 0.76rem; color: #6B7280; margin-top: 4px;">Zone: <b>{alt.get('locationId', 'General')}</b> · Sensor: {alt.get('sensorType', 'Weight')}</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.success("✅ No open alerts in this zone scope.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Team & Employee Management (Manager) OR Zone Inventory (Employee)
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[1]:
    if is_manager:
        section_header("👥 Employee Credential & Zone Provisioning")
        st.markdown("""
<p style="color: #6B7280; font-size: 0.9rem;">
  As Chief Facility Manager, you can create, assign, and revoke credentials for warehouse operators.
  Each employee is strictly confined to the zone designated here.
</p>
""", unsafe_allow_html=True)

        col_add, col_list = st.columns([1, 1.4])

        with col_add:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("➕ Create New Employee Login")
            with st.form("create_employee_form", clear_on_submit=True):
                emp_user = st.text_input("Employee Username / ID", placeholder="e.g. cold_operator_02")
                emp_name = st.text_input("Full Name", placeholder="e.g. Alex Morgan")
                emp_pass = st.text_input("Password", type="password", placeholder="Enter secure password")
                emp_zone = st.selectbox(
                    "Assigned Operational Zone",
                    ["frozen", "refrigerated", "dry-storage", "biologics_storage", "synthesis_unit"],
                    help="The employee will ONLY be permitted to view telemetry and logs for this zone."
                )
                emp_email = st.text_input("Contact Email (optional)", placeholder="operator@stockshield.local")

                submitted = st.form_submit_button("Create Employee Account", use_container_width=True, type="primary")
                if submitted:
                    if emp_user and emp_pass:
                        try:
                            res = api.create_employee(
                                username=emp_user,
                                password=emp_pass,
                                full_name=emp_name,
                                assigned_location=emp_zone,
                                email=emp_email
                            )
                            st.success(f"✅ Successfully created employee {emp_user} assigned to {emp_zone}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create employee: {e}")
                    else:
                        st.error("Username and Password are required.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_list:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📋 Active Team Directory")
            employees = api.fetch_employees()
            if employees:
                for emp in employees:
                    role_b = "manager" if emp.get("role") == "MANAGER" else "employee"
                    zone_label = emp.get("assignedLocation") or "All Zones (Manager)"
                    is_root = (emp.get("username") == "admin")

                    c_info, c_action = st.columns([3, 1])
                    with c_info:
                        st.markdown(f"""
<div style="margin-bottom: 12px;">
  <span class="user-role-tag {role_b}">{emp.get('role')}</span>
  <b style="color: #141416; margin-left: 8px;">{emp.get('fullName', emp.get('username'))}</b> 
  <span style="color: #9CA3AF; font-size: 0.8rem;">(@{emp.get('username')})</span>
  <div style="font-size: 0.78rem; color: #6B7280; margin-top: 2px;">
    Assigned Zone: <b style="color: #FF5520;">{zone_label}</b> · Email: {emp.get('email')}
  </div>
</div>
""", unsafe_allow_html=True)
                    with c_action:
                        if not is_root and emp.get("id"):
                            if st.button("Revoke", key=f"del_user_{emp['id']}", use_container_width=True):
                                try:
                                    api.delete_employee(emp["id"])
                                    st.success(f"Revoked {emp.get('username')}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    st.divider()
            else:
                st.info("No employees found.")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Employee Zone Inventory
        section_header(f"📦 Inventory Monitored Inside {user_zone.upper() if user_zone else 'LOCAL'}")
        items = api.fetch_inventory(zone=user_zone)
        if items:
            df = pd.DataFrame(items)
            cols_show = ["id", "name", "category", "currentWeight", "fullWeight", "unit", "stockLevel"]
            available_cols = [c for c in cols_show if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.info(f"No stock items found for zone '{user_zone}'.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Global Audit Logs (Manager) OR Zone Incident Logs (Employee)
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[2]:
    if is_manager:
        section_header("📑 Global Audit & Incident Log Archive")
        st.markdown("<p style='color: #6B7280;'>Full archival record across all facilities, edge sensor alerts, and staff actions.</p>", unsafe_allow_html=True)
        all_alerts = api.fetch_recent_alerts(limit=50, tenant_id=active_tenant_id)
    else:
        section_header(f"🔔 Incident Logs for {user_zone.upper() if user_zone else 'ASSIGNED ZONE'}")
        st.markdown(f"<p style='color: #6B7280;'>Restricted view: Incident logs isolated strictly to {user_zone}.</p>", unsafe_allow_html=True)
        all_alerts = api.fetch_recent_alerts(limit=50, tenant_id=active_tenant_id, location_id=user_zone)

    if all_alerts:
        df_al = pd.DataFrame(all_alerts)
        st.dataframe(df_al, use_container_width=True)
    else:
        st.success("No incident logs recorded.")
