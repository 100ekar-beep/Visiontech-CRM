import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Page configuration
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

st.title("🧾 Invoice Management System")

# Supabase Credentials (st.secrets ya direct keys use karein)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Tabs for Viewing and Adding Data
tab1, tab2 = st.tabs(["📊 View Invoices", "➕ Add New Invoice"])

with tab1:
    st.subheader("All Invoices List")
    try:
        response = supabase.table("invoice_management").select("*").execute()
        data = response.data
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No invoice records found in Supabase.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

with tab2:
    st.subheader("Add New Invoice Record")
    
    with st.form("invoice_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            circle = st.text_input("Circle")
            invoice_number = st.text_input("Invoice Number")
            invoice_date = st.date_input("Invoice Date")
            basic_amount = st.number_input("Basic Amount", value=0.0, format="%.2f")
            cgst = st.number_input("CGST", value=0.0, format="%.2f")
            sgst = st.number_input("SGST", value=0.0, format="%.2f")
            igst = st.number_input("IGST", value=0.0, format="%.2f")
            
            # Total calculation (Basic + CGST + SGST + IGST)
            total = basic_amount + cgst + sgst + igst
            st.info(f"Calculated Total: {total:.2f}")

        with col2:
            project_id = st.text_input("Project ID")
            site_id = st.text_input("Site ID")
            site_name = st.text_input("Site Name")
            po_number = st.text_input("PO Number")
            wcc_number = st.text_input("WCC Number")
            receipt_number = st.text_input("Receipt Number")
            percentage_amount = st.number_input("% Amount", value=0.0, format="%.2f")

        with col3:
            payment_1_amount = st.number_input("Payment 1 Amount", value=0.0, format="%.2f")
            payment_1_date = st.date_input("Payment 1 Date", value=None)
            payment_2_amount = st.number_input("Payment 2 Amount", value=0.0, format="%.2f")
            payment_2_date = st.date_input("Payment 2 Date", value=None)
            payment_3_amount = st.number_input("Payment 3 Amount", value=0.0, format="%.2f")
            payment_3_date = st.date_input("Payment 3 Date", value=None)
            balance = st.number_input("Balance", value=0.0, format="%.2f")

        remark = st.text_area("Remark")
        
        submitted = st.form_submit_button("Save Invoice")
        
        if submitted:
            new_record = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": str(invoice_date) if invoice_date else None,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "total": total,  # IGST ke baad Total column
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": str(payment_1_date) if payment_1_date else None,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": str(payment_2_date) if payment_2_date else None,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": str(payment_3_date) if payment_3_date else None,
                "balance": balance,
                "remark": remark
            }
            
            try:
                supabase.table("invoice_management").insert(new_record).execute()
                st.success("Invoice successfully added to Supabase! 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"Error inserting data: {e}")
