import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. PAGE CONFIG (Only once)
st.set_page_config(page_title="KDS Reselling", layout="wide")
st.title("📈 Stock Lists")

# 2. CONNECTION
url = "https://docs.google.com/spreadsheets/d/1E-biBsQA9R8WRlD8tVGLCKFGyBEQVjd_ZSrDHePqQuo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Helper to load data fresh
@st.cache_data(ttl=0)
def load_data():
    return conn.read(spreadsheet=url, worksheet="Sheet1")

data = load_data().dropna(how="all")

# Force all Statuses to be strings and remove hidden spaces
data["Status"] = data["Status"].astype(str).str.strip()
data["Status"] = data["Status"].replace("nan", "Listed") # Assume blank = Listed

# 3. NAVIGATION TABS
tab1, tab2, tab3 = st.tabs(["🆕 Add Inventory", "📦 Active Listings", "🚚 Shipping Tasks"])

# --- TAB 1: DATA ENTRY ---
with tab1:
    st.header("Log New Find")
    with st.form("new_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Item Name")
            cat = st.selectbox("Category", ["Electronics", "Clothing", "Toys", "Other"])
        with col2:
            buy_p = st.number_input("Purchase Price", min_value=0.0)
            platform = st.selectbox("Platform", ["Facebook Marketplace", "Vinted", "What Not", "Local"])
        
        if st.form_submit_button("Add to Inventory"):
            new_row = pd.DataFrame([{
                "Item Name": name, "Category": cat, "Buy Price": buy_p, 
                "Platform": platform, "Status": "Listed", "Date Added": datetime.now().strftime("%Y-%m-%d")
            }])
            updated_df = pd.concat([data, new_row], ignore_index=True)
            conn.update(spreadsheet=url, worksheet="Sheet1", data=updated_df)
            st.success(f"Added {name}!")
            st.rerun()

# --- TAB 2: ACTIVE LISTINGS ---
with tab2:
    st.header("Inventory Status")
    
    # We define the column configuration here to force the dropdown
    edited_df = st.data_editor(
        data, 
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Change item status",
                options=["Listed", "Sold", "Returned", "Shipped"],
                required=True,
            )
        },
        use_container_width=True,
        key="inventory_editor"
    )

    if st.button("Update"):
        conn.update(spreadsheet=url, worksheet="Sheet1", data=edited_df)
        st.cache_data.clear()
        st.success("Updated")
        st.rerun()

# --- TAB 3: PICK & SHIP ---
with tab3:
    st.header("Items to Ship")
    sold_items = data[data["Status"] == "Sold"]
    
    if sold_items.empty:
        st.info("✅ No items currently sold.")
    else:
        for index, row in sold_items.iterrows():
            with st.expander(f"📦 {row['Item Name']} ({row['Platform']})"):
                st.write(f"**Platform:** {row['Platform']}")
                st.write(f"**Category:** {row['Category']}")
                if st.button(f"Mark as Shipped", key=f"ship_{index}"):
                    data.at[index, "Status"] = "Shipped"
                    conn.update(spreadsheet=url, worksheet = "Sheet1", data=data)
                    st.success(f"Moved {row['Item Name']} to Shipped!")
                    st.cache_data.clear()
                    st.rerun()
