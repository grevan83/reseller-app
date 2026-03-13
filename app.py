import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. PAGE SETUP
st.set_page_config(page_title="Reseller Flow", layout="wide", initial_sidebar_state="collapsed")
st.title("🚀 Reseller Operations")

# 2. DATA CONNECTION
# Make sure your 'spreadsheet' and 'worksheet' keys are in your Secrets!
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="0s") # Set ttl to 0 so it always pulls fresh data

df = load_data()

# 3. THE WORKFLOW TABS
tab_add, tab_manage, tab_ship = st.tabs(["➕ Add Item", "📋 Inventory Manager", "🚚 Ship Orders"])

# --- TAB: ADD ITEM (Sourcing Phase) ---
with tab_add:
    with st.form("quick_add", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        name = col1.text_input("Item Name", placeholder="What did you find?")
        buy_p = col2.number_input("Cost", min_value=0.0, step=1.0)
        loc = col3.text_input("Location", placeholder="Bin A, Shelf 1...")
        
        if st.form_submit_button("Log Item"):
            new_entry = pd.DataFrame([{
                "Item Name": name, "Cost": buy_p, "Location": loc,
                "Status": "Listed", "Added": datetime.now().strftime("%Y-%m-%d")
            }])
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(data=updated_df)
            st.success(f"Logged {name} to {loc}!")
            st.rerun()

# --- TAB: MANAGE (Active Status Phase) ---
with tab_manage:
    # We only want to see things we still have in the house
    active_df = df[df["Status"] != "Shipped"].copy()
    
    st.subheader(f"Current Stock ({len(active_df)} items)")
    
    # The 'on the fly' editor
    # Changing a status here to 'Sold' automatically sends it to the Ship tab
    edited_df = st.data_editor(
        active_df,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status", options=["Listed", "Sold", "Returned"], required=True
            ),
            "Cost": st.column_config.NumberColumn(format="$%.2f")
        },
        use_container_width=True,
        key="editor",
        hide_index=True
    )
    
    if st.button("Save All Status Changes"):
        # Update main dataframe with edited rows
        df.update(edited_df)
        conn.update(data=df)
        st.success("Cloud Updated!")
        st.rerun()

# --- TAB: SHIP (Fulfillment Phase) ---
with tab_ship:
    sold_items = df[df["Status"] == "Sold"]
    
    if sold_items.empty:
        st.info("No pending shipments. Go find some more profit!")
    else:
        st.subheader(f"Items to Pick & Pack ({len(sold_items)})")
        for i, row in sold_items.iterrows():
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.write(f"**{row['Item Name']}**")
                st.caption(f"📍 Location: {row['Location']} | Cost: ${row['Cost']}")
            
            # This is your final workflow trigger
            if col_btn.button("Mark Shipped", key=f"ship_{i}"):
                df.at[i, "Status"] = "Shipped"
                conn.update(data=df)
                st.toast(f"Shipped {row['Item Name']}!")
                st.rerun()
