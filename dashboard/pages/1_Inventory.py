import streamlit as st
import pandas as pd
import api

st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")

st.title("Inventory Management")

try:
    inventory = api.fetch_inventory()
    if inventory:
        df = pd.DataFrame(inventory)
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("Search items by name or SKU")
        with col2:
            status_filter = st.selectbox("Status", ["All", "In Stock", "Low Stock", "Out of Stock"])
            
        # Filter dataframe
        if search:
            df = df[df['name'].str.contains(search, case=False, na=False) | df['sku'].str.contains(search, case=False, na=False)]
        
        if status_filter != "All":
            df = df[df['status'] == status_filter]
            
        st.dataframe(
            df[['id', 'name', 'sku', 'currentQuantity', 'minQuantity', 'shelfId', 'status']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No inventory items found.")
except Exception as e:
    st.error(f"Failed to load inventory: {e}")
