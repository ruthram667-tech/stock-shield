import streamlit as st
import pandas as pd
import plotly.express as px
import api

st.set_page_config(
    page_title="StockShield Universal Platform",
    page_icon="🛡️",
    layout="wide",
)

# ─── Sidebar: Tenant & Industry Switcher ─────────────────────────────────────
st.sidebar.title("🏢 Organization")
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}

selected_label = st.sidebar.selectbox("Active Tenant", list(tenant_map.keys()))
active_tenant_id = tenant_map[selected_label]
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

st.sidebar.markdown(f"**Tenant ID:** `{active_tenant_id}`")
st.sidebar.markdown(f"**Industry:** `{selected_tenant.get('industry', 'universal')}`")
st.sidebar.divider()

# Quick Tenant Creator in sidebar
with st.sidebar.expander("➕ Register New Tenant"):
    new_t_name = st.text_input("Company / Org Name")
    new_t_ind = st.selectbox("Industry", ["pharmaceutical", "chemical_manufacturing", "cold_chain_logistics", "agriculture", "manufacturing_machinery", "retail_grocery", "data_center"])
    if st.button("Create Tenant", use_container_width=True):
        if new_t_name:
            try:
                res = api.create_tenant(new_t_name, new_t_ind)
                st.sidebar.success(f"Created {res['name']}!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

# ─── Main Dashboard Header ──────────────────────────────────────────────────
st.title(f"🛡️ StockShield — {selected_tenant.get('name', 'Universal IoT')} Dashboard")
st.caption(f"Universal IoT Telemetry, Anomaly Detection & Self-Trained ML • Sector: **{selected_tenant.get('industry', 'All Industries').upper()}**")

try:
    summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Monitored Assets", summary.get("totalItems", 0))
    with col2:
        st.metric("Low Stock / Critical", summary.get("lowStockCount", 0))
    with col3:
        st.metric("Sensors Online", summary.get("sensorsOnline", 0))
    with col4:
        st.metric("Active Alerts", summary.get("activeAlerts", 0))

    st.divider()

    # Dynamic Sensor Overview
    st.subheader("📡 Registered Sensor Types & Thresholds")
    sensor_types = api.fetch_sensor_types(active_tenant_id)

    if sensor_types:
        cols = st.columns(min(len(sensor_types), 4) or 1)
        for idx, s in enumerate(sensor_types):
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"**{s.get('displayName', s['code'])}**")
                    st.caption(f"Code: `{s['code']}` | Category: `{s.get('category', 'metric')}`")
                    st.write(f"Safe Range: **{s.get('minSafe', '-')}** to **{s.get('maxSafe', '-')}** {s.get('unit', '')}")
                    st.write(f"Critical: **{s.get('criticalMin', '-')}** / **{s.get('criticalMax', '-')}**")
                    st.markdown(f"ML Enabled: `{'✅ Yes' if s.get('mlEnabled') else '❌ No'}`")
    else:
        st.info(f"No custom sensor types registered yet for {selected_tenant.get('name')}. Configure them in the **Sensor Registry** page.")

    st.divider()

    # Recent Alerts Feed
    st.subheader("🔔 Real-Time Alert Stream")
    alerts = api.fetch_recent_alerts(limit=8, tenant_id=active_tenant_id)
    if alerts:
        alerts_df = pd.DataFrame(alerts)
        if not alerts_df.empty:
            time_col = 'createdAt' if 'createdAt' in alerts_df.columns else 'timestamp'
            type_col = 'alertType' if 'alertType' in alerts_df.columns else 'type'
            alerts_df['Time'] = pd.to_datetime(alerts_df[time_col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            alerts_df['Severity'] = alerts_df.get('severity', '')
            alerts_df['Type'] = alerts_df.get(type_col, '')
            alerts_df['Sensor'] = alerts_df.get('sensorType', 'general')
            alerts_df['Message'] = alerts_df.get('message', '')
            alerts_df['Location'] = alerts_df.get('locationId', alerts_df.get('shelfId', ''))

            cols_to_show = ['Time', 'Severity', 'Sensor', 'Type', 'Message', 'Location']
            available = [c for c in cols_to_show if c in alerts_df.columns]
            st.dataframe(alerts_df[available], use_container_width=True, hide_index=True)
    else:
        st.success("✅ All systems operating within normal parameters. No active alerts.")

except Exception as e:
    st.error(f"Dashboard connection error: {e}")
