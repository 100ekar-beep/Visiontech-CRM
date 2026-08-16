import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# Page configuration
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

st.title("🧾 Invoice Management System")

# Supabase Credentials
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://bpwcraaasqjgmwpclxfb.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_secret_ChVw7W5z9c5k74ycI5GnYA_KBYB1blv")

@st.cache_resource
def init_supabase():
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
    search_query = st.text_input("🔍 Search Invoices", placeholder="Type anything to search instantly...", label_visibility="collapsed")

with col_add:
    add_btn = st.button("➕ Add Invoice", use_container_width=True)

with col_bulk:
    bulk_btn = st.button("📁 Bulk Upload", use_container_width=True)

with col_download:
    if not df_all.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_all.to_excel(writer, index=False, sheet_name='Invoices')
        st.download_button(label="📥 Download", data=output.getvalue(), file_name="invoice_management.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.button("📥 Download", disabled=True, use_container_width=True)

# --- ADD INVOICE LOGIC ---
if add_btn: st.session_state['show_add_form'] = True
if 'show_add_form' not in st.session_state: st.session_state['show_add_form'] = False

if st.session_state['show_add_form']:
    with st.form("invoice_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            circle = st.text_input("Circle")
            invoice_number = st.text_input("Invoice_number")
            invoice_date = st.date_input("Invoice_date")
            basic_amount = st.number_input("Basic_amount", value=0.0)
            cgst = st.number_input("CGST", value=0.0)
            sgst = st.number_input("SGST", value=0.0)
            igst = st.number_input("IGST", value=0.0)
            total = basic_amount + cgst + sgst + igst
        with col2:
            project_id = st.text_input("Project_id")
            site_id = st.text_input("Site_id")
            site_name = st.text_input("Site_name")
            po_number = st.text_input("Po_number")
            wcc_number = st.text_input("Wcc_number")
            receipt_number = st.text_number("Receipt_number")
            percentage_amount = st.number_input("%Amount", value=0.0)
        with col3:
            payment_1_amount = st.number_input("Paymet_1_amount", value=0.0)
            payment_1_date = st.date_input("Payment_1_date", value=None)
            payment_2_amount = st.number_input("Paymet_2_amount", value=0.0)
            payment_2_date = st.date_input("Payment_2_date", value=None)
            payment_3_amount = st.number_input("Paymet_3_amount", value=0.0)
            payment_3_date = st.date_input("Payment_3_date", value=None)
            balance = st.number_input("Balance", value=0.0)
        remark = st.text_area("Remark")
        if st.form_submit_button("Save"):
            supabase.table("invoice_management").insert({"circle": circle, "invoice_number": invoice_number, "invoice_date": str(invoice_date), "basic_amount": basic_amount, "cgst": cgst, "sgst": sgst, "igst": igst, "total": total, "project_id": project_id, "site_id": site_id, "site_name": site_name, "po_number": po_number, "wcc_number": wcc_number, "receipt_number": receipt_number, "percentage_amount": percentage_amount, "payment_1_amount": payment_1_amount, "payment_1_date": str(payment_1_date), "payment_2_amount": payment_2_amount, "payment_2_date": str(payment_2_date), "payment_3_amount": payment_3_amount, "payment_3_date": str(payment_3_date), "balance": balance, "remark": remark}).execute()
            st.session_state['show_add_form'] = False
            st.rerun()

# --- BULK UPLOAD LOGIC ---
if bulk_btn: st.session_state['show_bulk_form'] = True
if 'show_bulk_form' not in st.session_state: st.session_state['show_bulk_form'] = False
if st.session_state['show_bulk_form']:
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file and st.button("Confirm Bulk Upload"):
        df_b = pd.read_excel(file)
        supabase.table("invoice_management").insert(df_b.to_dict(orient="records")).execute()
        st.session_state['show_bulk_form'] = False
        st.rerun()

# --- SEARCH & PAGINATION ---
if not df_all.empty:
    df_f = df_all[df_all.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)] if search_query else df_all
    page = st.session_state.get('page', 1)
    df_p = df_f.iloc[(page-1)*10 : page*10]
    st.dataframe(df_p, use_container_width=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("Previous") and page > 1: st.session_state['page'] = page - 1; st.rerun()
    c2.write(f"Page {page}")
    if c3.button("Next") and page < (len(df_f)-1)//10 + 1: st.session_state['page'] = page + 1; st.rerun()

    # --- EDIT/DELETE ---
    with st.expander("🛠 Edit or Delete"):
        sel_id = st.selectbox("Select ID", df_f['id'].tolist())
        row = df_f[df_f['id'] == sel_id].iloc[0]
        with st.form("edit"):
            new_val = st.text_input("New Remark", value=row['remark'])
            if st.form_submit_button("Update"):
                supabase.table("invoice_management").update({"remark": new_val}).eq("id", sel_id).execute(); st.rerun()
        if st.button("Delete Selected"):
            supabase.table("invoice_management").delete().eq("id", sel_id).execute(); st.rerun()
