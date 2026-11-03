import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    section_header,
    render_breadcrumbs,
    badge,
    PLOTLY_LAYOUT_DEFAULTS,
    TRACE_CYAN,
    TRACE_EMERALD,
)

st.set_page_config(page_title="AI Model Studio · StockShield", page_icon="🧠", layout="wide")
inject_global_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Organization / Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)
st.sidebar.divider()

# ─── Breadcrumbs & Header ─────────────────────────────────────────────────────
render_breadcrumbs(["🛡️ StockShield", selected_tenant.get('name', 'Universal IoT'), "🧠 AI Model Studio"])

header_banner(
    title="Custom AI Model Studio",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle="Train custom forecasting & anomaly-detection models on your own telemetry data",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="STUDIO",
)

# ─── Sensor Types ─────────────────────────────────────────────────────────────
sensor_types = api.fetch_sensor_types(active_tenant_id)
available_codes = [s['code'] for s in sensor_types] if sensor_types else [
    "temperature", "humidity", "pressure", "vibration", "ph", "weight"
]

tabs = st.tabs(["🚀 Train New Model", "🔮 Forecast & Anomaly Detection", "📚 Model Repository"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Train New Model
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    section_header("1 · Select Sensor Metric to Train")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        target_sensor = st.selectbox("Sensor Type", available_codes)
    with col_s2:
        s_match = next((s for s in sensor_types if s['code'] == target_sensor), None)
        unit     = s_match.get('unit', '')     if s_match else ''
        category = s_match.get('category', 'metric') if s_match else 'metric'
        st.markdown(f"""
<div class="glass-card" style="padding:12px 16px;">
  <div style="font-size:0.75rem;color:#64748B;margin-bottom:6px;">Selected Target</div>
  <div>
    {badge(target_sensor, 'cyan')}
    &nbsp;{badge(unit or 'unit', 'emerald')}
    &nbsp;{badge(category, 'amber')}
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("2 · Data Source")
    data_source_mode = st.radio(
        "Choose training data source:",
        ["Streamed InfluxDB Live Telemetry", "Upload Custom Historical CSV Dataset"],
        horizontal=True,
    )

    if data_source_mode == "Upload Custom Historical CSV Dataset":
        st.markdown("""
<div class="glass-card" style="padding:16px;">
  <div style="font-size:0.82rem;color:#94A3B8;">
    Upload your organization's CSV data. Required columns:<br>
    &nbsp;• <code style="color:#00E5FF;">timestamp</code> (or <code style="color:#00E5FF;">ds</code>)<br>
    &nbsp;• <code style="color:#00E5FF;">value</code> (or <code style="color:#00E5FF;">y</code>)<br>
    Optional: <code style="color:#10B981;">locationId</code>
  </div>
</div>
""", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.dataframe(preview_df.head(5), use_container_width=True)
                st.success(f"Loaded CSV with {len(preview_df)} rows — columns: {list(preview_df.columns)}")
                uploaded_file.seek(0)
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    else:
        training_window = st.selectbox("Historical Window to Train On", ["7d", "14d", "30d", "60d", "90d"], index=2)

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("3 · Model Hyperparameters")
    hp_c1, hp_c2 = st.columns(2)
    with hp_c1:
        service_level = st.slider(
            "Confidence Level / Anomaly Sensitivity",
            min_value=0.80, max_value=0.99, value=0.95, step=0.01,
            help="Higher values create wider safe boundaries; lower values increase anomaly sensitivity.",
        )
    with hp_c2:
        lead_time = st.number_input("Lead Time / Planning Horizon (Days)", min_value=1, max_value=30, value=3)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Train Custom Model Now", type="primary", use_container_width=True):
        with st.spinner(f"Training AI model on {target_sensor} data for {selected_tenant.get('name')}..."):
            try:
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

                train_result = api.train_custom_model(
                    tenant_id=active_tenant_id,
                    sensor_type=target_sensor,
                    training_window=train_win,
                    service_level=service_level,
                )

                st.success("🎉 Model Trained Successfully!")

                section_header("📊 Training Results")
                rc1, rc2, rc3, rc4 = st.columns(4)
                with rc1:
                    st.metric("Model Algorithm", train_result.get("model_type", "Prophet").upper())
                with rc2:
                    st.metric("Data Points Used", train_result.get("data_points_used", 0))
                with rc3:
                    st.metric("In-Sample MAE", f"{train_result.get('mae', 0):.4f}")
                with rc4:
                    st.metric("In-Sample RMSE", f"{train_result.get('rmse', 0):.4f}")

                thresh = train_result.get("learned_thresholds", {})
                st.markdown("<br>", unsafe_allow_html=True)
                section_header("🎯 Dynamic Thresholds Discovered from Your Data")
                tc1, tc2, tc3, tc4, tc5 = st.columns(5)
                with tc1:
                    st.metric("Safe Min",       f"{thresh.get('min_safe', '-')} {unit}")
                with tc2:
                    st.metric("Safe Max",       f"{thresh.get('max_safe', '-')} {unit}")
                with tc3:
                    st.metric("Critical Lower", f"{thresh.get('critical_min', '-')} {unit}")
                with tc4:
                    st.metric("Critical Upper", f"{thresh.get('critical_max', '-')} {unit}")
                with tc5:
                    st.metric("Baseline Mean",  f"{thresh.get('mean', '-')} {unit}")

                if s_match and st.button("💾 Apply Learned Thresholds to Live Alert System"):
                    api.update_sensor_type(s_match["id"], {
                        "minSafe":     thresh.get("min_safe"),
                        "maxSafe":     thresh.get("max_safe"),
                        "criticalMin": thresh.get("critical_min"),
                        "criticalMax": thresh.get("critical_max"),
                    })
                    st.success("Updated live sensor thresholds in database!")

            except Exception as e:
                st.error(f"Training failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Forecast & Anomaly Detection
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    section_header("🔮 Run Forecast Using Your Trained Model")
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        f_sensor = st.selectbox("Select Model to Evaluate", available_codes, key="eval_sensor")
    with f_c2:
        f_horizon = st.selectbox(
            "Forecast Horizon", [12, 24, 48, 72, 168], index=1,
            format_func=lambda x: f"{x} Hours ({x//24} Days)" if x >= 24 else f"{x} Hours",
        )

    if st.button("Generate Forecast", type="primary"):
        with st.spinner("Generating AI prediction with user-trained model..."):
            try:
                pred_result = api.predict_custom_model(
                    tenant_id=active_tenant_id,
                    sensor_type=f_sensor,
                    horizon_hours=f_horizon,
                )

                section_header(f"Forecast Results — {pred_result.get('model_used', '').upper()} Model")

                if pred_result.get("anomaly_detected"):
                    st.markdown(f"""
<div class="glass-card" style="border-color:rgba(239,68,68,0.45);background:rgba(239,68,68,0.08);">
  <span style="color:#EF4444;font-weight:700;">⚠️ ANOMALY DETECTED</span>
  <span style="color:#94A3B8;font-size:0.85rem;margin-left:12px;">
    Latest reading ({pred_result.get('latest_reading')}) breaches learned model boundaries.
  </span>
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div class="glass-card" style="border-color:rgba(16,185,129,0.45);background:rgba(16,185,129,0.07);">
  <span style="color:#10B981;font-weight:700;">✅ Normal Operation</span>
  <span style="color:#94A3B8;font-size:0.85rem;margin-left:12px;">
    Latest reading ({pred_result.get('latest_reading')}) is within learned safe envelope.
  </span>
</div>
""", unsafe_allow_html=True)

                f_points = pred_result.get("forecast", [])
                if f_points:
                    f_df = pd.DataFrame(f_points)
                    f_df['timestamp'] = pd.to_datetime(f_df['timestamp'])

                    fig = go.Figure()

                    # Confidence envelope
                    fig.add_trace(go.Scatter(
                        x=f_df['timestamp'].tolist() + f_df['timestamp'].tolist()[::-1],
                        y=f_df['upper_bound'].tolist() + f_df['lower_bound'].tolist()[::-1],
                        fill='toself',
                        fillcolor='rgba(16,185,129,0.10)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo="skip",
                        name="Confidence Interval",
                    ))

                    # Forecast line
                    fig.add_trace(go.Scatter(
                        x=f_df['timestamp'],
                        y=f_df['predicted_value'],
                        mode='lines+markers',
                        name='AI Predicted Value',
                        line=dict(color=TRACE_EMERALD, width=3),
                        marker=dict(size=5, color=TRACE_EMERALD),
                    ))

                    fig.update_layout(
                        **PLOTLY_LAYOUT_DEFAULTS,
                        title=f"Forecasted Trajectory — '{f_sensor}' (Next {f_horizon} Hours)",
                        xaxis_title="Future Timestamp",
                        yaxis_title="Predicted Value",
                        height=420,
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.warning(f"Could not generate forecast: {e}. Ensure you have trained a model for '{f_sensor}' first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Model Repository
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    section_header(f"📚 Saved AI Models — {selected_tenant.get('name', active_tenant_id)}")
    try:
        models = api.fetch_tenant_models(active_tenant_id)
        if models:
            m_list = []
            for m in models:
                thresh = m.get("learned_thresholds", {})
                m_list.append({
                    "Sensor Metric": m.get("sensor_type"),
                    "Algorithm":     m.get("model_type", "").upper(),
                    "Trained At":    m.get("trained_at", m.get("last_trained")),
                    "Data Points":   m.get("data_points_used"),
                    "MAE":           m.get("mae"),
                    "RMSE":          m.get("rmse"),
                    "Learned Min":   thresh.get("min_safe", "—"),
                    "Learned Max":   thresh.get("max_safe", "—"),
                })
            st.dataframe(pd.DataFrame(m_list), use_container_width=True, hide_index=True)
        else:
            st.markdown(f"""
<div class="glass-card" style="text-align:center;padding:48px;">
  <div style="font-size:2.5rem;margin-bottom:12px;">🧠</div>
  <div style="color:#94A3B8;font-size:0.88rem;">
    No custom models trained yet for <strong style="color:#F8FAFC;">{selected_tenant.get('name')}</strong>.
    <br>Use the <strong style="color:#00E5FF;">Train New Model</strong> tab to get started.
  </div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error listing models: {e}")
