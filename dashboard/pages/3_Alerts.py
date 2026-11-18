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
    badge,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_AMBER,
    TRACE_CRIMSON,
)

st.set_page_config(page_title="Incident Stream · StockShield", layout="wide")
inject_global_css()

# ─── User Profile & Scope ─────────────────────────────────────────────────────
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
is_employee = (user.get("role", "").upper() == "EMPLOYEE")
user_zone = user.get("assignedLocation")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Filter Tenant", ["All Tenants"] + list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
if active_tenant_id != "All Tenants":
    sidebar_tenant_card(
        tenant_name=selected_tenant.get('name', active_tenant_id),
        tenant_id=active_tenant_id,
        industry=selected_tenant.get('industry', 'universal'),
    )

# ─── Breadcrumbs & Header ─────────────────────────────────────────────────────
scope_note = f"ZONE: {user_zone.upper()}" if is_employee and user_zone else "ALL LOCATIONS"
tenant_label = selected_tenant.get('name', 'All Tenants') if active_tenant_id != "All Tenants" else "ALL TENANTS"
render_breadcrumbs(["STOCKSHIELD", tenant_label.upper(), "ALERTS", scope_note])

header_banner(
    title="Incident & Threshold Audit Archive",
    tenant_name=f"TENANT: {active_tenant_id} | {scope_note}",
    subtitle="Safety bounds violation logs, critical anomalies, and hardware heartbeat timeouts",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="ACTIVE",
)

if is_employee and user_zone:
    st.info(f"CONTAINMENT ACTIVE: Scoped strictly to {user_zone.upper()}.")

# ─── Content ──────────────────────────────────────────────────────────────────
try:
    tenant_param = None if active_tenant_id == "All Tenants" else active_tenant_id
    location_param = user_zone if is_employee else None
    alerts = api.fetch_recent_alerts(limit=100, tenant_id=tenant_param, location_id=location_param)

    if alerts:
        df = pd.DataFrame(alerts)
        time_col = 'createdAt' if 'createdAt' in df.columns else 'timestamp'
        type_col = 'alertType' if 'alertType' in df.columns else 'type'

        df['Time']     = pd.to_datetime(df[time_col], format="ISO8601").dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Severity'] = df.get('severity', '')
        df['Type']     = df.get(type_col, '')
        df['Sensor']   = df.get('sensorType', 'general')
        df['Message']  = df.get('message', '')
        df['Location'] = df.get('locationId', df.get('shelfId', ''))
        df['Item']     = df.get('itemId', '')
        df['Tenant']   = df.get('tenantId', '')

        if is_employee and user_zone:
            df = df[df['Location'].str.lower().str.contains(user_zone.lower()) | df['Message'].str.lower().str.contains(user_zone.lower())]

        # ─── Filters ──────────────────────────────────────────────────────────
        section_header("Filter Incidents")
        col1, col2, col3 = st.columns(3)
        with col1:
            severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "WARNING", "INFO"])
        with col2:
            type_filter = st.selectbox("Alert Type", ["All"] + sorted(list(df['Type'].dropna().unique())))
        with col3:
            sensor_filter = st.selectbox("Sensor Type", ["All"] + sorted(list(df['Sensor'].dropna().unique())))

        if severity_filter != "All":
            df = df[df['Severity'] == severity_filter]
        if type_filter != "All":
            df = df[df['Type'] == type_filter]
        if sensor_filter != "All":
            df = df[df['Sensor'] == sensor_filter]

        # ─── KPI strip ────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Incident Statistics")
        m1, m2, m3, m4 = st.columns(4)
        crit_count = len(df[df['Severity'] == 'CRITICAL']) if 'Severity' in df.columns else 0
        warn_count = len(df[df['Severity'] == 'WARNING'])  if 'Severity' in df.columns else 0
        info_count = len(df[df['Severity'] == 'INFO'])     if 'Severity' in df.columns else 0
        with m1:
            st.metric("Total Logged", len(df))
        with m2:
            st.metric("Critical", crit_count, delta_color="inverse")
        with m3:
            st.metric("Warning", warn_count, delta_color="inverse")
        with m4:
            st.metric("Info", info_count)

        # ─── Table ────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Audit Log")
        cols_to_display = ['Time', 'Severity', 'Tenant', 'Location', 'Sensor', 'Type', 'Message']
        available = [c for c in cols_to_display if c in df.columns]
        st.dataframe(df[available], use_container_width=True, hide_index=True)

        # ─── Severity distribution chart ──────────────────────────────────────
        if 'Severity' in df.columns and not df.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("Severity Breakdown")
            sev_counts = df['Severity'].value_counts().reset_index()
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
                title="Severity Distribution",
                showlegend=False,
                bargap=0.4,
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.markdown("""
<div class="glass-card" style="text-align:center;padding:48px;">
  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #10B981; margin-bottom: 6px;">STATUS: NOMINAL</div>
  <div style="color: #94A3B8; font-size: 0.88rem;">All monitored telemetry parameters operating within nominal bounds.</div>
</div>
""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading incidents: {e}")
