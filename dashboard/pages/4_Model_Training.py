import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import api

st.set_page_config(page_title="AI Model Studio", page_icon="🧠", layout="wide")

st.title("🧠 Custom AI Model Studio — Train Your Own Models")
st.markdown("""
**Universal Machine Learning for Any Industry.**
Train custom forecasting and anomaly-detection models on **your own telemetry data** — whether you monitor cold-chain temperatures, chemical reactor pressure, soil moisture, machine vibration, or product consumption.
""")

# Tenant selector in sidebar
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Organization / Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

st.sidebar.markdown(f"**Industry:** `{selected_tenant.get('industry', 'universal')}`")
st.sidebar.divider()

# Fetch sensor types defined for this tenant
sensor_types = api.fetch_sensor_types(active_tenant_id)
available_codes = [s['code'] for s in sensor_types] if sensor_types else ["temperature", "humidity", "pressure", "vibration", "ph", "weight"]

tabs = st.tabs(["🚀 Train New Model", "🔮 Forecast & Anomaly Detection", "📚 Model Repository"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Train New Model
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("1. Select Sensor Metric to Train")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        target_sensor = st.selectbox("Sensor Type", available_codes)
    with col_s2:
        s_match = next((s for s in sensor_types if s['code'] == target_sensor), None)
        unit = s_match.get('unit', '') if s_match else ''
        category = s_match.get('category', 'metric') if s_match else 'metric'
        st.info(f"Target: **{target_sensor}** ({unit}) • Category: **{category}**")

    st.subheader("2. Data Source")
    data_source_mode = st.radio(
        "Choose training data source:",
        ["Streamed InfluxDB Live Telemetry", "Upload Custom Historical CSV Dataset"],
        horizontal=True
    )

    if data_source_mode == "Upload Custom Historical CSV Dataset":
        st.markdown("""
        Upload your organization's CSV data. Requirements:
        - Must contain columns: `timestamp` (or `ds`) and `value` (or `y`).
        - Optional: `locationId`.
        """)
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.dataframe(preview_df.head(5), use_container_width=True)
                st.success(f"Loaded CSV with {len(preview_df)} rows and columns: {list(preview_df.columns)}")
                uploaded_file.seek(0)
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    else:
        training_window = st.selectbox("Historical Window to Train On", ["7d", "14d", "30d", "60d", "90d"], index=2)

    st.subheader("3. Model Hyperparameters")
    hp_c1, hp_c2 = st.columns(2)
    with hp_c1:
        service_level = st.slider(
            "Confidence Level / Anomaly Sensitivity",
            min_value=0.80, max_value=0.99, value=0.95, step=0.01,
            help="Higher values create wider safe boundaries; lower values increase anomaly sensitivity."
        )
    with hp_c2:
        lead_time = st.number_input("Lead Time / Planning Horizon (Days)", min_value=1, max_value=30, value=3)

    st.divider()

    # Train Button Action
    if st.button("🚀 Train Custom Model Now", type="primary", use_container_width=True):
        with st.spinner(f"Training AI model on {target_sensor} data for {selected_tenant.get('name')}..."):
            try:
                # If CSV mode, upload data first
                if data_source_mode == "Upload Custom Historical CSV Dataset":
                    if uploaded_file is None:
                        st.error("Please select a CSV file first.")
                        st.stop()
                    csv_bytes = uploaded_file.read()
                    up_res = api.upload_training_csv(active_tenant_id, target_sensor, csv_bytes, uploaded_file.name)
                    st.toast(f"Imported {up_res.get('rows_imported', 0)} data points into InfluxDB!", icon="📥")
                    train_win = "90d"
                else:
                    train_win = training_window

                # Call ML train API
                train_result = api.train_custom_model(
                    tenant_id=active_tenant_id,
                    sensor_type=target_sensor,
                    training_window=train_win,
                    service_level=service_level
                )

                st.success(f"🎉 Model Trained Successfully!")

                # Display Results in Cards
                rc1, rc2, rc3, rc4 = st.columns(4)
                with rc1:
                    st.metric("Model Algorithm", train_result.get("model_type", "Prophet").upper())
                with rc2:
                    st.metric("Data Points Used", train_result.get("data_points_used", 0))
                with rc3:
                    st.metric("In-Sample MAE", f"{train_result.get('mae', 0):.4f}")
                with rc4:
                    st.metric("In-Sample RMSE", f"{train_result.get('rmse', 0):.4f}")

                # Display Learned Thresholds
                thresh = train_result.get("learned_thresholds", {})
                st.subheader("📊 Dynamic Thresholds Discovered from Your Data")
                st.markdown(
                    "The model analyzed your time-series distribution and calculated the statistical operational envelope:"
                )

                tc1, tc2, tc3, tc4, tc5 = st.columns(5)
                with tc1:
                    st.metric("Learned Safe Min", f"{thresh.get('min_safe', '-')} {unit}")
                with tc2:
                    st.metric("Learned Safe Max", f"{thresh.get('max_safe', '-')} {unit}")
                with tc3:
                    st.metric("Critical Lower", f"{thresh.get('critical_min', '-')} {unit}")
                with tc4:
                    st.metric("Critical Upper", f"{thresh.get('critical_max', '-')} {unit}")
                with tc5:
                    st.metric("Baseline Mean", f"{thresh.get('mean', '-')} {unit}")

                # Option to sync learned thresholds back to DB
                if s_match and st.button("💾 Apply Learned Thresholds to Live Alert System"):
                    api.update_sensor_type(s_match["id"], {
                        "minSafe": thresh.get("min_safe"),
                        "maxSafe": thresh.get("max_safe"),
                        "criticalMin": thresh.get("critical_min"),
                        "criticalMax": thresh.get("critical_max")
                    })
                    st.success("Updated live sensor thresholds in database!")

            except Exception as e:
                st.error(f"Training failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Forecast & Anomaly Detection
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("🔮 Run Forecast Using Your Trained Model")
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        f_sensor = st.selectbox("Select Model to Evaluate", available_codes, key="eval_sensor")
    with f_c2:
        f_horizon = st.selectbox("Forecast Horizon", [12, 24, 48, 72, 168], index=1, format_func=lambda x: f"{x} Hours ({x//24} Days)" if x >= 24 else f"{x} Hours")

    if st.button("Generate Forecast", type="primary"):
        with st.spinner("Generating AI prediction with user-trained model..."):
            try:
                pred_result = api.predict_custom_model(
                    tenant_id=active_tenant_id,
                    sensor_type=f_sensor,
                    horizon_hours=f_horizon
                )

                st.subheader(f"Forecast Results ({pred_result.get('model_used', '').upper()} Model)")

                # Anomaly Status Banner
                if pred_result.get("anomaly_detected"):
                    st.error(f"⚠️ ANOMALY DETECTED: Latest reading ({pred_result.get('latest_reading')}) breaches learned model boundaries!")
                else:
                    st.success(f"✅ Normal Operation: Latest reading ({pred_result.get('latest_reading')}) is within learned safe envelope.")

                f_points = pred_result.get("forecast", [])
                if f_points:
                    f_df = pd.DataFrame(f_points)
                    f_df['timestamp'] = pd.to_datetime(f_df['timestamp'])

                    # Plot Forecast with Upper and Lower Confidence Bounds
                    fig = go.Figure()

                    # Confidence Envelope
                    fig.add_trace(go.Scatter(
                        x=f_df['timestamp'].tolist() + f_df['timestamp'].tolist()[::-1],
                        y=f_df['upper_bound'].tolist() + f_df['lower_bound'].tolist()[::-1],
                        fill='toself',
                        fillcolor='rgba(0, 210, 106, 0.15)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo="skip",
                        name="Confidence Interval"
                    ))

                    # Forecast Line
                    fig.add_trace(go.Scatter(
                        x=f_df['timestamp'],
                        y=f_df['predicted_value'],
                        mode='lines+markers',
                        name='AI Predicted Value',
                        line=dict(color='#00D26A', width=3)
                    ))

                    fig.update_layout(
                        title=f"Forecasted Trajectory for '{f_sensor}' (Next {f_horizon} Hours)",
                        xaxis_title="Future Timestamp",
                        yaxis_title="Predicted Value",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.warning(f"Could not generate forecast: {e}. Please ensure you have trained a model for '{f_sensor}' first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Model Repository
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader(f"📚 Saved AI Models for {selected_tenant.get('name', active_tenant_id)}")
    try:
        models = api.fetch_tenant_models(active_tenant_id)
        if models:
            m_list = []
            for m in models:
                thresh = m.get("learned_thresholds", {})
                m_list.append({
                    "Sensor Metric": m.get("sensor_type"),
                    "Algorithm": m.get("model_type", "").upper(),
                    "Trained At": m.get("trained_at", m.get("last_trained")),
                    "Data Points": m.get("data_points_used"),
                    "MAE": m.get("mae"),
                    "RMSE": m.get("rmse"),
                    "Learned Min": thresh.get("min_safe", "-"),
                    "Learned Max": thresh.get("max_safe", "-")
                })
            st.dataframe(pd.DataFrame(m_list), use_container_width=True, hide_index=True)
        else:
            st.info(f"No custom models trained yet for {selected_tenant.get('name')}. Use the **Train New Model** tab to train your first model!")
    except Exception as e:
        st.error(f"Error listing models: {e}")
