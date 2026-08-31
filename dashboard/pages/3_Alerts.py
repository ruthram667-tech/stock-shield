import streamlit as st
import pandas as pd
import api

st.set_page_config(page_title="Alerts", page_icon="🔔", layout="wide")

st.title("System Alerts")

try:
    alerts = api.fetch_recent_alerts(limit=100)
    if alerts:
        df = pd.DataFrame(alerts)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "WARNING", "INFO"])
        with col2:
            type_filter = st.selectbox("Type", ["All"] + list(df['type'].unique()))
            
        if severity_filter != "All":
            df = df[df['severity'] == severity_filter]
        if type_filter != "All":
            df = df[df['type'] == type_filter]
            
        st.dataframe(
            df[['timestamp', 'severity', 'type', 'message', 'shelfId', 'itemId']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No alerts found.")
except Exception as e:
    st.error(f"Failed to load alerts: {e}")
