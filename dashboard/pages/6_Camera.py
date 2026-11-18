import streamlit as st
import streamlit.components.v1 as components
from utils.ui_theme import inject_global_css, section_header, render_breadcrumbs, sidebar_user_profile

st.set_page_config(page_title="Camera · StockShield", page_icon="📷", layout="wide")
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

render_breadcrumbs(["🛡️ StockShield", "📷 Live Camera"])
section_header("📷 Live Shelf Camera (ESP32-CAM)")

st.caption(
    "The stream is loaded directly by your browser from the camera, so the camera "
    "must be reachable from the machine you are viewing this on (same LAN)."
)

cam_ip = st.text_input("ESP32-CAM IP address", value=st.session_state.get("cam_ip", ""),
                       placeholder="192.168.1.50")
st.session_state["cam_ip"] = cam_ip.strip()

if cam_ip.strip():
    host = cam_ip.strip()
    # Hostname/IP characters only, to keep the value safe inside the HTML below
    if not all(ch.isalnum() or ch in ".-" for ch in host):
        st.error("Enter just the IP or hostname, e.g. 192.168.1.50")
    else:
        components.html(
            f'<img src="http://{host}:81/stream" style="width:100%;max-width:960px;'
            f'border-radius:12px;" alt="Live stream">',
            height=720,
        )
        st.markdown(f"[Open single snapshot](http://{host}/capture)")
else:
    st.info("Enter the camera's IP (printed in the serial monitor at boot).")
