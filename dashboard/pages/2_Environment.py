import streamlit as st
import pandas as pd
import plotly.express as px
import api

st.set_page_config(page_title="Environment", page_icon="🌡️", layout="wide")

st.title("Environment Monitoring")

try:
    # We need to get a list of shelves. We can extract it from the inventory.
    inventory = api.fetch_inventory()
    shelves = sorted(list(set([item['shelfId'] for item in inventory if item.get('shelfId')])))
    
    if not shelves:
        st.warning("No shelves found in the inventory.")
    else:
        selected_shelf = st.selectbox("Select Shelf", shelves)
        range_val = st.selectbox("Time Range", ["1h", "24h", "7d"], index=1)
        
        env_data = api.fetch_environment_history(selected_shelf, range_str=range_val)
        
        if env_data and len(env_data) > 0:
            df = pd.DataFrame(env_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Latest reading
            latest = df.iloc[-1]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Temperature", f"{latest.get('temperature', 'N/A')} °C")
            with col2:
                st.metric("Humidity", f"{latest.get('humidity', 'N/A')} %")
                
            # Charts
            st.subheader("Temperature History")
            fig_temp = px.line(df, x='timestamp', y='temperature', title=f"Temperature - {selected_shelf}")
            st.plotly_chart(fig_temp, use_container_width=True)
            
            st.subheader("Humidity History")
            fig_hum = px.line(df, x='timestamp', y='humidity', title=f"Humidity - {selected_shelf}")
            st.plotly_chart(fig_hum, use_container_width=True)
            
        else:
            st.info(f"No environment data found for {selected_shelf} in the selected time range.")
            
except Exception as e:
    st.error(f"Failed to load environment data: {e}")
