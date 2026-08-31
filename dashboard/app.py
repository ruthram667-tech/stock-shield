import streamlit as st
import pandas as pd
import plotly.express as px
import api

st.set_page_config(
    page_title="StockShield Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("StockShield Dashboard")

try:
    summary = api.fetch_dashboard_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", summary.get("totalItems", 0))
    with col2:
        st.metric("Low Stock Alerts", summary.get("lowStockAlerts", 0))
    with col3:
        st.metric("Total Shelves", summary.get("totalShelves", 0))
    with col4:
        st.metric("Active Alerts", summary.get("activeAlerts", 0))
        
    st.subheader("Recent Alerts")
    alerts = api.fetch_recent_alerts(limit=5)
    if alerts:
        alerts_df = pd.DataFrame(alerts)
        if not alerts_df.empty:
            alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
            st.dataframe(alerts_df[['timestamp', 'severity', 'type', 'message', 'shelfId']], use_container_width=True)
    else:
        st.info("No recent alerts.")
        
except Exception as e:
    st.error(f"Failed to fetch dashboard summary: {e}")
