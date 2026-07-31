import streamlit as st
import pandas as pd
import datetime
import io
from supabase import create_client, Client

# --- NAYI LINE: Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Team & Vendor Billing", page_icon="💸", layout="wide")

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Tabs Styling */
    button[data-baseweb="tab"] { font-weight: 700 !important; font-size: 1.1rem !important; }
    
    /* Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
    }
    button[data-testid="baseButton-secondary"] {
        background: #ef4444 !important; color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }
    
    /* KPI Cards for Reports */
    .kpi-card {
        background: white; border-radius: 12px; padding: 20px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;
    }
    .kpi-title { font-size: 1rem; color: #64748b; font-weight: 700; text-transform: uppercase; }
    .kpi-value-red { font-size: 2rem; color: #ef4444; font-weight: 900; }
    .kpi-value-green { font-size: 2rem; color: #10b981; font-weight: 900; }
    .kpi-value-blue { font-size: 2rem; color: #3b82f6; font-weight: 900; }

    /* Inputs */
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }

    /* =========================================================
       NAYI LINE: FIXED PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */
    section[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important; 
    }
    div[data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; 
        margin: 0.5rem 1rem !important; 
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; 
        color: #cbd5e1 !important; 
        font-weight: 600 !important;
        display: flex !important; 
        align-items: center !important; 
        gap: 12px !important; 
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a:hover { 
        background: rgba(255, 255, 255, 0.1) !important; 
        color: #ffffff !important; 
    }
    div[data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; 
        color: #ffffff !important; 
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        border-color: transparent !important;
    }
    div[data-testid="stSidebarNav"] a span { color: inherit !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 4. DATA FETCHING FUNCTIONS (From dropdown_master) ---
def get_dropdown_data(category_name):
    try:
        res = supabase.table("dropdown_master").select("option_value").eq("category", category_name).eq("is_active", True).execute()
        if res.data:
            return [r["option_value"] for r in res.data]
    except Exception as e:
        pass
    return []

# Fetch Master Data dynamically from dropdown_master
team_list = get_dropdown_data("Team Name") or ["No Teams Available"]
vendor_list = get_dropdown_data("Vendor Name") or ["No Vendors Available"]
pay_from_list = get_dropdown_data("Payment From") or ["Bank", "Cash"]
pay_type_list = get_dropdown_data("Payment Type") or ["NEFT", "RTGS", "UPI"]

# --- 5. MAIN PAGE LAYOUT ---
st.markdown("<h1 style='color:#0f172a; margin-bottom: 20px;'>💸 Team & Vendor Billing</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 Invoice Entry", "💳 Payment Entry", "📊 Ledger Reports"])

# ==========================================
# TAB 1: INVOICE ENTRY
# ==========================================
with tab1:
    col_mode, _ = st.columns([3, 7])
    with col_mode:
        invoice_mode = st.radio("Select Invoice Mode:", ["Team", "Vendor"], horizontal=True, key="inv_mode")
    
    st.markdown("---")
    
    with st.form("invoice_form", clear_on_submit=True):
        if invoice_mode == "Team":
            c1, c2, c3 = st.columns(3)
            team_val = c1.selectbox("Team Name *", options=team_list)
            inv_no = c2.text_input("Invoice No *")
            inv_date = c3.date_input("Invoice Date", value=datetime.date.today())
            
            c4, c5, c6, c7 = st.columns(4)
            proj_id = c4.text_input("Project ID")
            site_id = c5.text_input("Site ID")
            site_name = c6.text_input("Site Name")
            cluster = c7.text_input("Cluster")
            
            c8, c9, c10, c11 = st.columns(4)
            remark = c8.text_input("Remark")
            basic_amt = c9.number_input("Basic Amount", min_value=0.0, step=1.0)
            gst_perc = c10.number_input("GST %", min_value=0.0, step=1.0)
            
            # Auto Calc Display
            total_calc = basic_amt + ((basic_amt * gst_perc) / 100)
            c11.markdown(f"**Total Amount:**<br><h3 style='margin:0; color:#3b82f6;'>₹ {total_calc:,.2f}</h3>", unsafe_allow_html=True)
            vendor_val = ""
            
        else:
            c1, c2, c3 = st.columns(3)
            vendor_val = c1.selectbox("Vendor Name *", options=vendor_list)
            inv_no = c2.text_input("Invoice No *")
            inv_date = c3.date_input("Invoice Date", value=datetime.date.today())
            
            c4, c5, c6, c7 = st.columns(4)
            team_val = c4.selectbox("Link to Team *", options=team_list)
            remark = c5.text_input("Remark")
            basic_amt = c6.number_input("Basic Amount", min_value=0.0, step=1.0)
            gst_perc = c7.number_input("GST %", min_value=0.0, step=1.0)
            
            total_calc = basic_amt + ((basic_amt * gst_perc) / 100)
            st.markdown(f"**Total Amount:** <span style='color:#3b82f6; font-size:1.5rem; font-weight:bold;'>₹ {total_calc:,.2f}</span>", unsafe_allow_html=True)
            
            proj_id, site_id, site_name, cluster = "", "", "", ""
        
        st.markdown("<br>", unsafe_allow_html=True)
        sub_inv = st.form_submit_button("💾 Save Invoice", type="primary", use_container_width=True)
        
        if sub_inv:
            if not inv_no:
                st.error("⚠️ Invoice No is required!")
            else:
                try:
                    payload = {
                        "invoice_type": invoice_mode,
                        "team_name": team_val,
                        "amount": total_calc,
                        "date": str(inv_date),
                        "project_id": proj_id,
                        "site_id": site_id,
                        "site_name": site_name,
                        "invoice_no": inv_no,
                        "vendor_name": vendor_val,
                        "remark": remark,
                        "cluster": cluster
                    }
                    supabase.table("billing_invoices").insert(payload).execute()
                    st.success("✅ Invoice Saved Successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display Recent Invoices
    st.markdown("### 📋 Recent Invoices")
    try:
        inv_data = supabase.table("billing_invoices").select("*").eq("invoice_type", invoice_mode).order("id", desc=True).execute()
        if inv_data.data:
            df_inv = pd.DataFrame(inv_data.data)
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
    except:
        st.info("No data found.")

# ==========================================
# TAB 2: PAYMENT ENTRY
# ==========================================
with tab2:
    col_pmode, _ = st.columns([3, 7])
    with col_pmode:
        pay_mode = st.radio("Select Payment Mode:", ["Team", "Vendor"], horizontal=True, key="pay_mode")
    
    st.markdown("---")
    
    with st.form("payment_form", clear_on_submit=True):
        p1, p2, p3 = st.columns(3)
        pay_from = p1.selectbox("Payment From", options=pay_from_list)
        pay_to_opts = team_list if pay_mode == "Team" else vendor_list
        pay_to = p2.selectbox("Pay To", options=pay_to_opts)
        pay_type = p3.selectbox("Payment Type", options=pay_type_list)
        
        p4, p5, p6 = st.columns(3)
        pay_amt = p4.number_input("Amount (₹)", min_value=0.0, step=1.0)
        pay_date = p5.date_input("Payment Date", value=datetime.date.today())
        pay_remark = p6.text_input("Remark")
        
        st.markdown("<br>", unsafe_allow_html=True)
        sub_pay = st.form_submit_button("💾 Save Payment", type="primary", use_container_width=True)
        
        if sub_pay:
            if pay_amt <= 0:
                st.error("⚠️ Amount must be greater than zero!")
            else:
                try:
                    payload = {
                        "pay_from": pay_from,
                        "pay_to": pay_to,
                        "pay_type": pay_type,
                        "amount": pay_amt,
                        "date": str(pay_date),
                        "remark": pay_remark,
                        "mode": pay_mode
                    }
                    supabase.table("billing_payments").insert(payload).execute()
                    st.success("✅ Payment Saved Successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display Recent Payments
    st.markdown("### 💸 Recent Payments")
    try:
        pay_data = supabase.table("billing_payments").select("*").eq("mode", pay_mode).order("id", desc=True).execute()
        if pay_data.data:
            df_pay = pd.DataFrame(pay_data.data)
            st.dataframe(df_pay, use_container_width=True, hide_index=True)
    except:
        st.info("No data found.")

# ==========================================
# TAB 3: REPORTS & LEDGER
# ==========================================
with tab3:
    col_rmode, col_rname, _ = st.columns([3, 4, 3])
    with col_rmode:
        rep_mode = st.radio("Ledger Type:", ["Team", "Vendor"], horizontal=True, key="rep_mode")
    with col_rname:
        rep_opts = team_list if rep_mode == "Team" else vendor_list
        sel_name = st.selectbox("Select Name", options=["-- Select --"] + rep_opts)

    st.markdown("---")

    if sel_name and sel_name != "-- Select --":
        # Fetch Logic
        tot_inv = 0.0
        tot_pay = 0.0
        df_inv_rep, df_pay_rep = pd.DataFrame(), pd.DataFrame()
        
        try:
            # Fetch Invoices
            inv_col = "team_name" if rep_mode == "Team" else "vendor_name"
            res_inv = supabase.table("billing_invoices").select("*").eq("invoice_type", rep_mode).eq(inv_col, sel_name).execute()
            if res_inv.data:
                df_inv_rep = pd.DataFrame(res_inv.data)
                tot_inv = df_inv_rep["amount"].sum()
                if rep_mode == "Team":
                    df_inv_rep = df_inv_rep[["project_id", "site_id", "site_name", "amount", "date"]]
                else:
                    df_inv_rep = df_inv_rep[["invoice_no", "date", "team_name", "amount"]]

            # Fetch Payments
            res_pay = supabase.table("billing_payments").select("*").eq("mode", rep_mode).eq("pay_to", sel_name).execute()
            if res_pay.data:
                df_pay_rep = pd.DataFrame(res_pay.data)
                tot_pay = df_pay_rep["amount"].sum()
                df_pay_rep = df_pay_rep[["date", "pay_from", "pay_type", "amount", "remark"]]
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        # KPI Cards
        bal = tot_inv - tot_pay
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Billed</div><div class='kpi-value-blue'>₹ {tot_inv:,.2f}</div></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Paid</div><div class='kpi-value-green'>₹ {tot_pay:,.2f}</div></div>", unsafe_allow_html=True)
        with k3:
            bal_color = "kpi-value-red" if bal > 0 else "kpi-value-green"
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Balance</div><div class='{bal_color}'>₹ {bal:,.2f}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tables Side by Side
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### 📚 Invoices")
            st.dataframe(df_inv_rep, use_container_width=True, hide_index=True)
        with t2:
            st.markdown("#### 💸 Payments")
            st.dataframe(df_pay_rep, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # Download Section
        col_down1, col_down2, _ = st.columns([2, 2, 6])
        
        # 1. Excel Export
        with col_down1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if not df_inv_rep.empty: df_inv_rep.to_excel(writer, index=False, sheet_name='Invoices')
                if not df_pay_rep.empty: df_pay_rep.to_excel(writer, index=False, sheet_name='Payments')
                
                # Summary Sheet
                summary_df = pd.DataFrame({"Name": [sel_name], "Total Billed": [tot_inv], "Total Paid": [tot_pay], "Balance": [bal]})
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
            
            st.download_button(label="📊 Download Excel", data=buffer.getvalue(), file_name=f"{sel_name}_Ledger.xlsx", type="primary", use_container_width=True)

        # 2. PDF Export (using FPDF - Crash Proofed)
        with col_down2:
            def generate_pdf():
                if FPDF is None:
                    raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file in GitHub.")
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 8, "VISIONTECH INFRA SOLUTION PVT. LTD.", ln=True, align='C')
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(190, 8, "Balance Sheet", ln=True, align='C')
                pdf.cell(190, 8, f"{sel_name}", ln=True, align='C')
                pdf.ln(5)
                
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(95, 8, f"Total Billed: Rs. {tot_inv:,.2f}", ln=False)
                pdf.cell(95, 8, f"Total Paid: Rs. {tot_pay:,.2f}", ln=True, align='R')
                pdf.cell(190, 8, f"Net Balance: Rs. {bal:,.2f}", ln=True, align='C')
                pdf.ln(10)
                
                return pdf.output(dest='S').encode('latin1')

            try:
                pdf_bytes = generate_pdf()
                st.download_button(label="📄 Download PDF", data=pdf_bytes, file_name=f"{sel_name}_Report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                # Displays inline error ONLY when clicked if fpdf is missing
                st.error(str(e))
