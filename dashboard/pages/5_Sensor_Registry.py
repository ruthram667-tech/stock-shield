import streamlit as st
import pandas as pd
import api

st.set_page_config(page_title="Sensor Type Registry", page_icon="⚙️", layout="wide")

st.title("⚙️ Dynamic Sensor Type Registry")
st.caption("Configure custom IoT sensor types, metric units, categories, and operational alert limits for your organization.")

# Tenant selector in sidebar
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Organization / Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})

col_left, col_right = st.columns([3, 2])

# Left column: List registered sensor types
with col_left:
    st.subheader(f"Current Sensors for {selected_tenant.get('name')}")
    try:
        sensor_types = api.fetch_sensor_types(active_tenant_id)
        if sensor_types:
            df = pd.DataFrame(sensor_types)
            cols = ['code', 'displayName', 'unit', 'category', 'minSafe', 'maxSafe', 'criticalMin', 'criticalMax', 'mlEnabled']
            available = [c for c in cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True, hide_index=True)
        else:
            st.info("No sensor types registered yet for this tenant.")
    except Exception as e:
        st.error(f"Error fetching sensor types: {e}")

# Right column: Register new sensor type
with col_right:
    st.subheader("➕ Register New Sensor Type")
    with st.form("new_sensor_type_form"):
        code = st.text_input("Sensor Code (lowercase, unique)", placeholder="e.g. pressure, ph, vibration, soil_moisture")
        display_name = st.text_input("Display Name", placeholder="e.g. Chamber Pressure, Tank pH")
        unit = st.text_input("Measurement Unit", placeholder="e.g. psi, pH, g, °C, %, ppm, RPM")
        category = st.selectbox("Category", ["environmental", "chemical", "mechanical", "weight_level", "agricultural", "electrical"])

        st.markdown("**Thresholds & Safe Operational Range:**")
        tc1, tc2 = st.columns(2)
        with tc1:
            min_safe = st.number_input("Safe Minimum", value=0.0)
            critical_min = st.number_input("Critical Minimum", value=-10.0)
        with tc2:
            max_safe = st.number_input("Safe Maximum", value=100.0)
            critical_max = st.number_input("Critical Maximum", value=120.0)

        ml_enabled = st.checkbox("Enable ML Training & Anomaly Detection", value=True)
        agg_method = st.selectbox("Aggregation Method (InfluxDB)", ["mean", "max", "min", "sum"])

        submitted = st.form_submit_button("Register Sensor Type", type="primary", use_container_width=True)
        if submitted:
            if not code or not display_name:
                st.error("Sensor code and display name are required.")
            else:
                payload = {
                    "tenantId": active_tenant_id,
                    "code": code.strip().lower(),
                    "displayName": display_name.strip(),
                    "unit": unit.strip(),
                    "category": category,
                    "minSafe": min_safe,
                    "maxSafe": max_safe,
                    "criticalMin": critical_min,
                    "criticalMax": critical_max,
                    "mlEnabled": ml_enabled,
                    "aggregationMethod": agg_method
                }
                try:
                    res = api.create_sensor_type(payload)
                    st.success(f"Successfully registered sensor type '{code}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to register sensor type: {e}")
