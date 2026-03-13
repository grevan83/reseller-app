import streamlit as st
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Reseller Pro", layout="wide")
st.title("📦 Reseller Inventory Tracker")

# Initialize data storage (In a real app, this would be a database/CSV)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["Item Name", "Category", "Buy Price", "Target Sell Price", "Platform", "Status"]
    )

# --- SIDEBAR: ADD NEW ITEM ---
with st.sidebar:
    st.header("Add New Flip")
    name = st.text_input("Item Name")
    cat = st.selectbox("Category", ["Electronics", "Clothing", "Collectibles", "Other"])
    buy_p = st.number_input("Purchase Price ($)", min_value=0.0, step=1.0)
    sell_p = st.number_input("Target Sale Price ($)", min_value=0.0, step=1.0)
    plat = st.selectbox("Platform", ["eBay", "Poshmark", "FB Marketplace", "Mercari"])
    
    if st.button("Add to Inventory"):
        new_item = {
            "Item Name": name, "Category": cat, "Buy Price": buy_p, 
            "Target Sell Price": sell_p, "Platform": plat, "Status": "Listed"
        }
        st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([new_item])], ignore_index=True)
        st.success(f"Added {name}!")

# --- MAIN DASHBOARD ---
col1, col2, col3 = st.columns(3)

# Quick Stats
total_invested = st.session_state.inventory["Buy Price"].sum()
potential_revenue = st.session_state.inventory["Target Sell Price"].sum()
est_profit = potential_revenue - (total_invested * 1.13) # Rough estimate factoring 13% fees

col1.metric("Total Invested", f"${total_invested:,.2f}")
col2.metric("Potential Revenue", f"${potential_revenue:,.2f}")
col3.metric("Est. Net Profit", f"${est_profit:,.2f}", delta_color="normal")

st.divider()

# --- INVENTORY TABLE ---
st.subheader("Current Listings")
st.dataframe(st.session_state.inventory, use_container_width=True)

if st.button("Clear All Data"):
    st.session_state.inventory = pd.DataFrame(columns=st.session_state.inventory.columns)
    st.rerun()
