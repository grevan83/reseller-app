import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Reseller Pro Cloud", layout="wide")
st.title("📈 Cloud Inventory Manager")

# 1. Connect to Google Sheets
# Replace 'your_sheet_url_here' with your actual Google Sheet link
url = ""
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Read Existing Data
data = conn.read(spreadsheet=url, usecols=[0,1,2,3,4,5])
data = data.dropna(how="all") # Clean up empty rows

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.header("Add New Item")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Item Name")
        cat = st.selectbox("Category", ["Electronics", "Clothing", "Media", "Other"])
        buy_p = st.number_input("Buy Price", min_value=0.0)
        sell_p = st.number_input("Target Price", min_value=0.0)
        plat = st.text_input("Platform (e.g. eBay)")
        
        submit = st.form_submit_button("Save to Cloud")

    if submit:
        # Create new row
        new_row = pd.DataFrame([{
            "Item Name": name, 
            "Category": cat, 
            "Buy Price": buy_p, 
            "Target Sell Price": sell_p, 
            "Platform": plat, 
            "Status": "Listed"
        }])
        
        # Combine and update
        updated_df = pd.concat([data, new_row], ignore_index=True)
        conn.update(spreadsheet=url, data=updated_df)
        st.success("Data synced to Google Sheets!")
        st.rerun()

# --- MAIN DASHBOARD ---
st.subheader("Live Inventory")
st.dataframe(data, use_container_width=True)

# Simple Analytics
if not data.empty:
    total_spent = data["Buy Price"].sum()
    st.metric("Total Capital Deployed", f"${total_spent:,.2f}")
