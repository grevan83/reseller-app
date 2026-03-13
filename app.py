import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Reseller Pro Cloud", layout="wide")
st.title("📈 Cloud Inventory Manager")

# 1. Connect to Google Sheets
# Replace 'your_sheet_url_here' with your actual Google Sheet link
url = "https://docs.google.com/spreadsheets/d/1E-biBsQA9R8WRlD8tVGLCKFGyBEQVjd_ZSrDHePqQuo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Try to perform a test read
    data = conn.read(spreadsheet=url, worksheet="Sheet1")
    data = data.dropna(how="all")
    st.sidebar.success("✅ Connected to Google Sheets")
except Exception as e:
    st.error("Authentication failed. Check if your Service Account Email is an 'Editor' on the Google Sheet.")
    st.write("There is an issue with your Secrets formatting or Google Permissions.")
    st.info(f"Error Details: {e}")
    st.stop() # This prevents the rest of the app from running and crashing

# --- The rest of your app only runs if the connection succeeds ---

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
# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🆕 Add Inventory", "📦 Active Listings", "🚚 Shipping Tasks"])

# --- TAB 1: ADDING NEW ITEMS ---
with tab1:
    st.header("Sourcing Entry")
    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Item Name")
        buy_p = c2.number_input("Buy Price", min_value=0.0)
        loc = c3.text_input("Storage Location (Bin/Shelf)")
        
        if st.form_submit_button("Save to Inventory"):
            new_row = pd.DataFrame([{
                "Item Name": name, "Buy Price": buy_p, 
                "Location": loc, "Status": "Listed", 
                "Date": datetime.now().strftime("%Y-%m-%d")
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(spreadsheet=url, data=updated_df)
            st.success(f"Added {name} to inventory!")
            st.rerun()

# --- TAB 2: VIEW & EDIT ACTIVE INVENTORY ---
with tab2:
    st.header("Active Inventory")
    
    # Filter for anything NOT shipped yet
    active_mask = (df["Status"] != "Shipped")
    active_df = df[active_mask]

    if active_df.empty:
        st.write("No active inventory found. Go to 'Add New' to start!")
    else:
        st.write("👇 Change status to **'Sold'** to move item to Shipping List.")
        
        # This is your main status-changing engine
        edited_df = st.data_editor(
            active_df,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Change Status",
                    options=["Listed", "Sold", "Returned"],
                    required=True,
                )
            },
            disabled=["Item Name", "Date"], # Prevent accidental name changes
            key="inventory_editor",
            use_container_width=True
        )

        if st.button("Confirm Status Changes"):
            # Update the original dataframe with changes from the editor
            df.update(edited_df)
            conn.update(spreadsheet=url, data=df)
            st.success("Changes saved!")
            st.rerun()

# --- TAB 3: SHIPPING TASK LIST ---
with tab3:
    st.header("Orders to Ship")
    # Only items marked as 'Sold' appear here
    to_ship = df[df["Status"] == "Sold"]

    if to_ship.empty:
        st.success("Everything is shipped! Nice work.")
    else:
        for i, row in to_ship.iterrows():
            with st.expander(f"📦 {row['Item Name']} — Location: {row['Location']}"):
                st.write(f"**Step 1:** Pick from {row['Location']}")
                st.write(f"**Step 2:** Pack and buy label.")
                if st.button(f"Mark Shipped", key=f"btn_{i}"):
                    df.at[i, "Status"] = "Shipped"
                    conn.update(spreadsheet=url, data=df)
                    st.rerun()
