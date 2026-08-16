import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# Page configuration
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

st.title("🧾 Invoice Management System")

# Supabase Credentials from st.secrets (Ensure secrets.toml is configured properly)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase URL or Key is missing in Streamlit secrets!")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Fetch data function
def fetch_data():
    try:
        response = supabase.table("invoice_management").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df_all = fetch_data()

# --- TOP SECTION: Action Buttons & Search Box ---
col_search, col_add, col_bulk, col_download = st.columns([3, 1, 1, 1])

with col_search:
    # Instant search box (value dalte hi filter hoga)
    search_query = st.text_input("🔍 Search Invoices", placeholder="Type anything to search instantly...", label_visibility="collapsed")

with col_add:
    add_btn = st.button("➕ Add Invoice", use_container_width=True)

with col_bulk:
    bulk_btn = st.button("📁 Bulk Upload", use_container_width=True)

with col_download:
    if not df_all.empty:
        # Excel Download buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_all.to_excel(writer, index=False, sheet_name='Invoices')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download",
            data=excel_data,
            file_name="invoice_management.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button("📥 Download", disabled=True, use_container_width=True)

# --- POPUP / EXPANDER FOR ADD INVOICE ---
if add_btn:
    st.session_state['show_add_form'] = True
if 'show_add_form' not in st.session_state:
    st.session_state['show_add_form'] = False

if st.session_state['show_add_form']:
    with st.form("add_invoice_form", clear_on_submit=True):
        st.subheader("Add New Invoice")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            circle = st.text_input("Circle")
            invoice_number = st.text_input("Invoice Number")
            invoice_date = st.date_input("Invoice Date", value=None)
            basic_amount = st.number_input("Basic Amount", value=0.0, format="%.2f")
            cgst = st.number_input("CGST", value=0.0, format="%.2f")
            sgst = st.number_input("SGST", value=0.0, format="%.2f")
            igst = st.number_input("IGST", value=0.0, format="%.2f")
            total = basic_amount + cgst + sgst + igst
            st.info(f"Calculated Total: {total:.2f}")

        with c2:
            project_id = st.text_input("Project ID")
            site_id = st.text_input("Site ID")
            site_name = st.text_input("Site Name")
            po_number = st.text_input("PO Number")
            wcc_number = st.text_input("WCC Number")
            receipt_number = st.text_input("Receipt Number")
            percentage_amount = st.number_input("% Amount", value=0.0, format="%.2f")

        with c3:
            payment_1_amount = st.number_input("Payment 1 Amount", value=0.0, format="%.2f")
            payment_1_date = st.date_input("Payment 1 Date", value=None)
            payment_2_amount = st.number_input("Payment 2 Amount", value=0.0, format="%.2f")
            payment_2_date = st.date_input("Payment 2 Date", value=None)
            payment_3_amount = st.number_input("Payment 3 Amount", value=0.0, format="%.2f")
            payment_3_date = st.date_input("Payment 3 Date", value=None)
            balance = st.number_input("Balance", value=0.0, format="%.2f")

        remark = st.text_area("Remark")
        
        submit_form = st.form_submit_button("Submit Invoice")
        if submit_form:
            new_record = {
                "circle": circle, "invoice_number": invoice_number,
                "invoice_date": str(invoice_date) if invoice_date else None,
                "basic_amount": basic_amount, "cgst": cgst, "sgst": sgst, "igst": igst, "total": total,
                "project_id": project_id, "site_id": site_id, "site_name": site_name,
                "po_number": po_number, "wcc_number": wcc_number, "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "payment_1_amount": payment_1_amount, "payment_1_date": str(payment_1_date) if payment_1_date else None,
                "payment_2_amount": payment_2_amount, "payment_2_date": str(payment_2_date) if payment_2_date else None,
                "payment_3_amount": payment_3_amount, "payment_3_date": str(payment_3_date) if payment_3_date else None,
                "balance": balance, "remark": remark
            }
            try:
                supabase.table("invoice_management").insert(new_record).execute()
                st.success("Invoice added successfully!")
                st.session_state['show_add_form'] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- POPUP FOR BULK UPLOAD ---
if bulk_btn:
    st.session_state['show_bulk_form'] = True
if 'show_bulk_form' not in st.session_state:
    st.session_state['show_bulk_form'] = False

if st.session_state['show_bulk_form']:
    st.subheader("📁 Bulk Upload via Excel/CSV")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_bulk = pd.read_csv(uploaded_file)
            else:
                df_bulk = pd.read_excel(uploaded_file)
            
            st.write("Preview of Uploaded Data:", df_bulk.head())
            if st.button("Confirm & Upload to Database"):
                records = df_bulk.to_dict(orient="records")
                supabase.table("invoice_management").insert(records).execute()
                st.success("Bulk data uploaded successfully!")
                st.session_state['show_bulk_form'] = False
                st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")

st.markdown("---")

# --- DATA FILTERING & INSTANT SEARCH ---
if not df_all.empty:
    if search_query:
        # Convert all columns to string to perform global search across rows
        mask = df_all.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_filtered = df_all[mask]
    else:
        df_filtered = df_all

    # --- PAGINATION CONFIGURATION ---
    items_per_page = 10
    total_items = len(df_filtered)
    total_pages = max(1, (total_items - 1) // items_per_page + 1)

    if 'page_number' not in st.session_state:
        st.session_state['page_number'] = 1

    # Ensure page number is within bounds
    if st.session_state['page_number'] > total_pages:
        st.session_state['page_number'] = total_pages

    start_idx = (st.session_state['page_number'] - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_paginated = df_filtered.iloc[start_idx:end_idx]

    # --- MIDDLE SECTION: Main Table ---
    st.subheader(f"📊 Invoices List (Showing {start_idx + 1} to {min(end_idx, total_items)} of {total_items} entries)")
    st.dataframe(df_paginated, use_container_width=True)

    # --- PAGINATION BUTTONS (Previous & Next) ---
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ Previous Page", use_container_width=True):
            if st.session_state['page_number'] > 1:
                st.session_state['page_number'] -= 1
                st.rerun()
    with col_info:
        st.markdown(f"<p style='text-align: center;'>Page <b>{st.session_state['page_number']}</b> of <b>{total_pages}</b></p>", unsafe_allow_html=True)
    with col_next:
        if st.button("Next Page ▶", use_container_width=True):
            if st.session_state['page_number'] < total_pages:
                st.session_state['page_number'] += 1
                st.rerun()

    st.markdown("---")

    # --- BOTTOM SECTION: Edit & Delete Option ---
    st.subheader("🛠️ Edit or Delete Invoice Record")
    if not df_filtered.empty:
        invoice_options = df_filtered['id'].tolist() if 'id' in df_filtered.columns else []
        selected_id = st.selectbox("Select Invoice ID to Edit/Delete", invoice_options)
        
        if selected_id:
            row_data = df_filtered[df_filtered['id'] == selected_id].iloc[0]
            
            action_tab1, action_tab2 = st.tabs(["✏️ Edit Invoice", "🗑️ Delete Invoice"])
            
            with action_tab1:
                with st.form("edit_form"):
                    e_circle = st.text_input("Circle", value=str(row_data.get('circle', '')))
                    e_inv_num = st.text_input("Invoice Number", value=str(row_data.get('invoice_number', '')))
                    e_basic = st.number_input("Basic Amount", value=float(row_data.get('basic_amount', 0.0) or 0.0))
                    e_cgst = st.number_input("CGST", value=float(row_data.get('cgst', 0.0) or 0.0))
                    e_sgst = st.number_input("SGST", value=float(row_data.get('sgst', 0.0) or 0.0))
                    e_igst = st.number_input("IGST", value=float(row_data.get('igst', 0.0) or 0.0))
                    e_total = e_basic + e_cgst + e_sgst + e_igst
                    
                    e_remark = st.text_area("Remark", value=str(row_data.get('remark', '')))
                    
                    update_submitted = st.form_submit_button("Update Changes")
                    if update_submitted:
                        updated_values = {
                            "circle": e_circle,
                            "invoice_number": e_inv_num,
                            "basic_amount": e_basic,
                            "cgst": e_cgst,
                            "sgst": e_sgst,
                            "igst": e_igst,
                            "total": e_total,
                            "remark": e_remark
                        }
                        try:
                            supabase.table("invoice_management").update(updated_values).eq("id", selected_id).execute()
                            st.success("Record updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating: {e}")
                            
            with action_tab2:
                st.warning(f"Are you sure you want to delete Invoice ID: {selected_id}?")
                if st.button("Confirm Delete", type="primary"):
                    try:
                        supabase.table("invoice_management").delete().eq("id", selected_id).execute()
                        st.success("Record deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")
else:
    st.info("No records found in table.")
