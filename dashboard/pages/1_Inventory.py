import streamlit as st
import pandas as pd
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    sidebar_user_profile,
    section_header,
    render_breadcrumbs,
)

st.set_page_config(page_title="Inventory Registry · StockShield", layout="wide")
inject_global_css()

user = st.session_state.get("user")
if not user or "error" in user:
    st.warning("Please authenticate on the main console first.")
    st.stop()

sidebar_user_profile(user)
is_employee = (user.get("role", "").upper() == "EMPLOYEE")
user_zone = user.get("assignedLocation")

st.sidebar.markdown('<div class="section-header">Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(selected_tenant.get('name', active_tenant_id), active_tenant_id, selected_tenant.get('industry', 'universal'))

summary = api.fetch_dashboard_summary(tenant_id=active_tenant_id, location_id=user_zone if is_employee else None)
telemetry_up = summary.get("sensorsOnline", 0) > 0

scope_note = f"ZONE: {user_zone.upper()}" if is_employee and user_zone else "ALL LOCATIONS"
render_breadcrumbs(["STOCKSHIELD", active_tenant_id.upper(), "INVENTORY", scope_note])

header_banner(
    title="Inventory & Load Cell Registry",
    tenant_name=f"TENANT: {active_tenant_id} | {scope_note}",
    subtitle="Real-time load cell weight readings, full capacity thresholds, and reorder status",
    telemetry_online=telemetry_up,
    sector=selected_tenant.get('industry', ''),
    ml_state="LIVE" if telemetry_up else "STANDBY",
)

inventory = api.fetch_inventory(tenant_id=active_tenant_id, zone=user_zone if is_employee else None)
if inventory:
    df = pd.DataFrame(inventory)
    if 'tenantId' in df.columns:
        t_df = df[df['tenantId'] == active_tenant_id]
        if not t_df.empty:
            df = t_df
    if is_employee and user_zone and 'zone' in df.columns:
        df = df[df['zone'].str.lower() == user_zone.lower()]

    section_header("Filter Inventory")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("Search by Item ID or Name")
    with col2:
        status_filter = st.selectbox("Stock Level", ["All"] + sorted(list(df['stockLevel'].dropna().unique())))
    with col3:
        category_filter = st.selectbox("Category", ["All"] + sorted(list(df['category'].dropna().unique())))

    if search:
        df = df[df['name'].str.contains(search, case=False, na=False) | df['id'].str.contains(search, case=False, na=False)]
    if status_filter != "All":
        df = df[df['stockLevel'] == status_filter]
    if category_filter != "All":
        df = df[df['category'] == category_filter]

    if 'stockPercentage' in df.columns:
        df['Fill %'] = (df['stockPercentage'] * 100).round(1).astype(str) + '%'

    loc_col = 'locationId' if 'locationId' in df.columns else 'shelfId'
    df['Node'] = df.get(loc_col, '')

    display_cols = ['id', 'name', 'category', 'Node', 'zone', 'currentWeight', 'fullWeight', 'reorderPoint', 'unit', 'Fill %', 'stockLevel']
    available_cols = [c for c in display_cols if c in df.columns]

    section_header("Monitored SKUs")
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
else:
    st.info("No inventory items returned from backend.")
