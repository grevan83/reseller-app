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
            with st.expander(f"SHIP: {row['Item Name']} ({row['Platform']})"):
                st.write(f"**Platform:** {row['Platform']}")
                st.write(f"**Category:** {row['Category']}")
                if st.button(f"Mark as Shipped", key=f"ship_{index}"):
                    data.at[index, "Status"] = "Shipped"
                    conn.update(spreadsheet=url, data=data)
                    st.success(f"Moved {row['Item Name']} to Archive")
                    st.rerun()
