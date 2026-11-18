import time
import requests
import streamlit as st
import api
from utils.ui_theme import inject_global_css, section_header, render_breadcrumbs, sidebar_user_profile

st.set_page_config(page_title="Simulator · StockShield", page_icon="🎛️", layout="wide")
inject_global_css()

# ─── RBAC Access Gate (same pattern as the other pages) ──────────────────────
user = st.session_state.get("user")
if not user or "error" in user:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    st.warning("🔒 Please sign in from the main portal first.")
    st.stop()

sidebar_user_profile(user)

TENANT = "demo-tenant"
LOCATION = "sim-shelf-01"

render_breadcrumbs(["🛡️ StockShield", "🎛️ Simulator"])
section_header("🎛️ Live Data Simulator")
st.caption(
    f"Move a slider and the new value is sent to the backend right away as "
    f"`{TENANT}` / `{LOCATION}`. This is separate from the real ESP32 (`shelf-01`). "
    f"Open the Environment page and pick node `{LOCATION}` to watch it respond."
)


def post_reading(sensor_type: str, value: float):
    try:
        res = requests.post(
            f"{api.API_BASE}/ingest",
            json={
                "tenantId": TENANT,
                "locationId": LOCATION,
                "readings": [{"sensorType": sensor_type, "value": float(value)}],
            },
            timeout=5,
        )
        ok = res.status_code == 200 and res.json().get("accepted", 0) > 0
        st.session_state["sim_status"] = (
            f"✅ Sent {sensor_type} = {value}" if ok else f"❌ Backend rejected ({res.status_code})"
        )
    except Exception as e:
        st.session_state["sim_status"] = f"❌ Backend unreachable: {e}"
    st.session_state["sim_last_sent"] = time.strftime("%H:%M:%S")


def on_temp():
    post_reading("temperature", st.session_state["sim_temp"])


def on_hum():
    post_reading("humidity", st.session_state["sim_hum"])


col1, col2 = st.columns(2)
with col1:
    st.slider("🌡️ Temperature (°C)", -20.0, 80.0, 22.0, 0.5, key="sim_temp", on_change=on_temp)
with col2:
    st.slider("💧 Humidity (%)", 0.0, 100.0, 50.0, 1.0, key="sim_hum", on_change=on_hum)

if st.button("Send both now", type="primary"):
    post_reading("temperature", st.session_state["sim_temp"])
    post_reading("humidity", st.session_state["sim_hum"])

if "sim_status" in st.session_state:
    st.info(f"{st.session_state['sim_status']}  ·  {st.session_state.get('sim_last_sent', '')}")

# Latest values the backend actually stored for this shelf
section_header("📡 Stored by backend (last 15 min)")
for sensor in ("temperature", "humidity"):
    try:
        pts = api.fetch_generic_telemetry(TENANT, LOCATION, sensor, range_str="15m")
    except Exception:
        pts = []
    if pts:
        last = pts[-1]
        st.metric(sensor.capitalize(), f"{last['value']:.1f}", help=f"at {last['time']}")
    else:
        st.write(f"No {sensor} data yet. Move a slider to send one.")
