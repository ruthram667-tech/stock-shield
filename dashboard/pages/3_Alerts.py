import streamlit as st
import pandas as pd
import api

st.set_page_config(page_title="Alerts Stream", page_icon="🔔", layout="wide")

st.title("🔔 Real-Time Alerts & Threshold Breaches")
st.caption("Live monitoring of safety bounds, threshold violations, and low inventory across all monitored locations.")

# Tenant selector in sidebar
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Filter Tenant", ["All Tenants"] + list(tenant_map.values()), index=0)

try:
    tenant_param = None if active_tenant_id == "All Tenants" else active_tenant_id
    alerts = api.fetch_recent_alerts(limit=100, tenant_id=tenant_param)

    if alerts:
        df = pd.DataFrame(alerts)
        time_col = 'createdAt' if 'createdAt' in df.columns else 'timestamp'
        type_col = 'alertType' if 'alertType' in df.columns else 'type'

        df['Time'] = pd.to_datetime(df[time_col]).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Severity'] = df.get('severity', '')
        df['Type'] = df.get(type_col, '')
        df['Sensor'] = df.get('sensorType', 'general')
        df['Message'] = df.get('message', '')
        df['Location'] = df.get('locationId', df.get('shelfId', ''))
        df['Item'] = df.get('itemId', '')
        df['Tenant'] = df.get('tenantId', '')

        # Filters
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

        cols_to_display = ['Time', 'Severity', 'Tenant', 'Location', 'Sensor', 'Type', 'Message']
        available = [c for c in cols_to_display if c in df.columns]

        st.dataframe(
            df[available],
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        m1, m2 = st.columns(2)
        with m1:
            crit_count = sum(1 for _, row in df.iterrows() if row.get('Severity') == 'CRITICAL')
            st.metric("Critical Alerts", crit_count)
        with m2:
            warn_count = sum(1 for _, row in df.iterrows() if row.get('Severity') == 'WARNING')
            st.metric("Warning Alerts", warn_count)

    else:
        st.success("✅ No recent alerts found. All systems are operating within safe limits.")
except Exception as e:
    st.error(f"Failed to load alerts: {e}")
