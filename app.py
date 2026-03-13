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
            platform = st.selectbox("Primary Platform", ["eBay", "Poshmark", "Mercari", "Local"])
        
        if st.form_submit_button("Add to Inventory"):
            new_data = pd.DataFrame([{
                "Item Name": name, "Category": cat, "Buy Price": buy_p, 
                "Platform": platform, "Status": "Listed", "Date Added": datetime.now().strftime("%Y-%m-%d")
            }])
            updated_df = pd.concat([data, new_data], ignore_index=True)
            conn.update(spreadsheet=url, data=updated_df)
            st.success("Item Listed!")
            st.rerun()

# --- TAB 2: STATUS MANAGER ---
with tab2:
    st.header("Inventory Status")
    st.info("Change an item to 'Sold' here to move it to the Shipping list.")
    
    # We only show items that aren't 'Shipped' or 'Archived'
    active_items = data[data["Status"].isin(["Listed", "Sold"])]
    
    edited_data = st.data_editor(
        active_items,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=["Listed", "Sold", "Returned"])
        },
        use_container_width=True,
        key="status_editor"
    )

    if st.button("Update Statuses"):
        # This logic merges the edits back into the main Google Sheet
        data.update(edited_data)
        conn.update(spreadsheet=url, data=data)
        st.success("Inventory Updated!")
        st.rerun()

# --- TAB 3: PICK & SHIP (The Task List) ---
with tab3:
    st.header("Items to Ship")
    # Only items marked as 'Sold' appear here
    shipping_list = data[data["Status"] == "Sold"]
    
    if shipping_list.empty:
        st.write("✅ All orders shipped! Time to source more.")
    else:
      for index, row in shipping_list.iterrows():
    with st.expander(f"📦 SHIP: {row['Item Name']} (Location: {row.get('Storage Location', 'N/A')})"):
        st.write(f"**Go to:** {row.get('Storage Location', 'Unknown')}") # Tells you where to walk
        if st.button("Mark as Shipped", key=f"ship_{index}"):
            # ... (shipping logic)
                    data.at[index, "Status"] = "Shipped"
                    conn.update(spreadsheet=url, data=data)
                    st.success(f"Moved {row['Item Name']} to Archive")
                    st.rerun()
