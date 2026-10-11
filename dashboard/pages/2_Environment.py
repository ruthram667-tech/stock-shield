import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api

st.set_page_config(page_title="Sensor Telemetry", page_icon="📡", layout="wide")

st.title("📡 Universal Sensor Telemetry")
st.caption("Live and historical time-series analytics for any sensor metric across any facility or zone.")

# Tenant selector in sidebar
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Active Tenant", list(tenant_map.values()), index=0)

try:
    # Fetch registered sensor types for this tenant
    sensor_types = api.fetch_sensor_types(active_tenant_id)

    # Also discover available locations from inventory
    inventory = api.fetch_inventory()
    locations = sorted(list(set([
        item.get('locationId', item.get('shelfId'))
        for item in inventory
        if item.get('locationId') or item.get('shelfId')
    ])))

    # Fallback default locations if empty
    if not locations:
        locations = ["shelf-01", "shelf-04", "cold-vault-01", "reactor-tank-03"]

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_location = st.selectbox("Location / Zone", locations)
    with col2:
        available_sensor_codes = [s['code'] for s in sensor_types] if sensor_types else ["temperature", "humidity", "pressure", "vibration", "ph", "weight"]
        selected_sensor = st.selectbox("Sensor Metric", available_sensor_codes)
    with col3:
        time_range = st.selectbox("Time Window", ["1h", "6h", "24h", "7d", "30d"], index=2)

    # Find definition for selected sensor
    s_def = next((s for s in sensor_types if s['code'] == selected_sensor), None)
    unit = s_def.get('unit', '') if s_def else ''
    disp_name = s_def.get('displayName', selected_sensor.capitalize()) if s_def else selected_sensor.capitalize()

    # Query telemetry data
    telemetry_data = []
    try:
        telemetry_data = api.fetch_generic_telemetry(active_tenant_id, selected_location, selected_sensor, range_str=time_range)
    except Exception:
        # Fallback to legacy environment or weight endpoint
        if selected_sensor in ["temperature", "humidity"]:
            try:
                env_history = api.fetch_environment_history(selected_location, range_str=time_range)
                for pt in env_history:
                    telemetry_data.append({
                        "timestamp": pt.get("timestamp"),
                        "value": pt.get(selected_sensor)
                    })
            except Exception:
                pass

    if telemetry_data and len(telemetry_data) > 0:
        df = pd.DataFrame(telemetry_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        latest_val = float(df['value'].iloc[-1])
        min_val = float(df['value'].min())
        max_val = float(df['value'].max())
        mean_val = float(df['value'].mean())

        # Metric KPI cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Latest Reading", f"{latest_val:.2f} {unit}")
        with m2:
            st.metric("Minimum", f"{min_val:.2f} {unit}")
        with m3:
            st.metric("Maximum", f"{max_val:.2f} {unit}")
        with m4:
            st.metric("Average", f"{mean_val:.2f} {unit}")

        # Interactive Plotly Chart with User-Defined Threshold Bands
        fig = go.Figure()

        # Telemetry trace
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['value'],
            mode='lines+markers',
            name=f'{disp_name}',
            line=dict(color='#00D26A', width=2),
            marker=dict(size=4)
        ))

        # Add Threshold horizontal lines if defined
        if s_def:
            if s_def.get('maxSafe') is not None:
                fig.add_hline(y=s_def['maxSafe'], line_dash="dash", line_color="orange",
                              annotation_text=f"Safe Max ({s_def['maxSafe']} {unit})", annotation_position="top left")
            if s_def.get('minSafe') is not None:
                fig.add_hline(y=s_def['minSafe'], line_dash="dash", line_color="orange",
                              annotation_text=f"Safe Min ({s_def['minSafe']} {unit})", annotation_position="bottom left")
            if s_def.get('criticalMax') is not None:
                fig.add_hline(y=s_def['criticalMax'], line_dash="dot", line_color="red",
                              annotation_text=f"Critical Max ({s_def['criticalMax']} {unit})", annotation_position="top right")
            if s_def.get('criticalMin') is not None:
                fig.add_hline(y=s_def['criticalMin'], line_dash="dot", line_color="red",
                              annotation_text=f"Critical Min ({s_def['criticalMin']} {unit})", annotation_position="bottom right")

        fig.update_layout(
            title=f"Live Telemetry: {disp_name} at Location '{selected_location}'",
            xaxis_title="Time",
            yaxis_title=f"{disp_name} ({unit})",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(f"Awaiting telemetry data for **{disp_name}** at location **{selected_location}** in time range **{time_range}**.")
        st.caption("Data is streamed in real-time from MQTT edge sensors. Run the edge-simulator to generate live test traffic.")

except Exception as e:
    st.error(f"Error fetching sensor telemetry: {e}")
