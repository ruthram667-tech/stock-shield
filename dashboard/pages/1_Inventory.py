import streamlit as st
import pandas as pd
import api
from utils.ui_theme import (
    inject_global_css,
    header_banner,
    sidebar_tenant_card,
    section_header,
    render_breadcrumbs,
    badge,
)

st.set_page_config(page_title="Asset Inventory · StockShield", page_icon="📦", layout="wide")
inject_global_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="section-header">🏢 Organization</div>', unsafe_allow_html=True)
tenants = api.fetch_tenants()
tenant_map = {f"{t['name']} ({t.get('industry', 'general')})": t['id'] for t in tenants}
active_tenant_id = st.sidebar.selectbox("Filter Tenant", list(tenant_map.values()), index=0)
selected_tenant = next((t for t in tenants if t['id'] == active_tenant_id), {})
sidebar_tenant_card(
    tenant_name=selected_tenant.get('name', active_tenant_id),
    tenant_id=active_tenant_id,
    industry=selected_tenant.get('industry', 'universal'),
)

# ─── Breadcrumbs & Header ─────────────────────────────────────────────────────
render_breadcrumbs(["🛡️ StockShield", selected_tenant.get('name', 'Universal IoT'), "📦 Asset Inventory"])

header_banner(
    title="Asset & Stock Inventory",
    tenant_name=selected_tenant.get('name', 'Universal IoT'),
    subtitle="Universal stock tracking across warehouse shelves, tanks, cold vaults & stations",
    telemetry_online=True,
    sector=selected_tenant.get('industry', ''),
    ml_state="MONITORING",
)

# ─── Content ──────────────────────────────────────────────────────────────────
try:
    inventory = api.fetch_inventory()
    if inventory:
        df = pd.DataFrame(inventory)

        # Filter by tenant if tenantId present in items
        if 'tenantId' in df.columns:
            tenant_items = df[df['tenantId'] == active_tenant_id]
            if not tenant_items.empty:
                df = tenant_items

        # Search and filters
        section_header("🔍 Search & Filter")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search = st.text_input("Search assets by name or ID")
        with col2:
            status_filter = st.selectbox("Stock Status", ["All"] + sorted(list(df['stockLevel'].dropna().unique())))
        with col3:
            category_filter = st.selectbox("Category", ["All"] + sorted(list(df['category'].dropna().unique())))

        if search:
            df = df[df['name'].str.contains(search, case=False, na=False) | df['id'].str.contains(search, case=False, na=False)]
        if status_filter != "All":
            df = df[df['stockLevel'] == status_filter]
        if category_filter != "All":
            df = df[df['category'] == category_filter]

        if 'stockPercentage' in df.columns:
            df['Stock %'] = (df['stockPercentage'] * 100).round(1).astype(str) + '%'

        loc_col = 'locationId' if 'locationId' in df.columns else 'shelfId'
        df['Location'] = df.get(loc_col, '')

        display_cols = ['id', 'name', 'category', 'Location', 'zone', 'currentWeight', 'fullWeight', 'reorderPoint', 'unit', 'Stock %', 'stockLevel']
        available_cols = [c for c in display_cols if c in df.columns]

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("📦 Asset Registry")
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

        # Summary Metrics
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("📊 Summary")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Items Shown", len(df))
        with m2:
            reorder_count = sum(1 for _, row in df.iterrows() if row.get('needsReorder', False))
            st.metric("Items Needing Reorder", reorder_count, delta_color="inverse")
        with m3:
            avg_stock = df['stockPercentage'].mean() * 100 if 'stockPercentage' in df.columns and len(df) > 0 else 0
            st.metric("Avg Stock Level", f"{avg_stock:.1f}%")

    else:
        st.markdown("""
<div class="glass-card" style="text-align:center;padding:40px;">
  <div style="font-size:2.5rem;margin-bottom:10px;">📭</div>
  <div style="color:#94A3B8;">No inventory assets found for this tenant.</div>
</div>
""", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to load inventory: {e}")
