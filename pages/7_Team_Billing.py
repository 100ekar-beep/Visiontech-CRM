import streamlit as st
import pandas as pd
import datetime
import io
import os
import math
from supabase import create_client, Client

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
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

    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }

    /* Dialog/Popup Premium Styling */
    div[data-testid="stDialog"] > div {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2 {
        color: #1e293b !important; font-weight: 800 !important; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px;
    }
    .gst-highlight { color: #10b981; font-weight: 800; font-size: 1.1rem; }
    .total-highlight { color: #3b82f6; font-weight: 900; font-size: 1.8rem; }

    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
    section[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important; 
    }
    div[data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    div[data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; border-color: transparent !important;
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

# --- AMOUNT TO WORDS CONVERTER (INDIAN SYSTEM) ---
def number_to_words(n):
    if n is None or pd.isna(n):
        return ""
    n = int(n)
    if n == 0:
        return ""
        
    words = { 1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
        11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', 15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', 19: 'Nineteen',
        20: 'Twenty', 30: 'Thirty', 40: 'Forty', 50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', 90: 'Ninety' }
    
    def num_to_words_below_1000(num):
        if num == 0: return ""
        elif num < 20: return words[num]
        elif num < 100: return words[num - num % 10] + (" " + words[num % 10] if num % 10 != 0 else "")
        else: return words[num // 100] + " Hundred" + (" and " + num_to_words_below_1000(num % 100) if num % 100 != 0 else "")

    res = ""
    if n >= 10000000:
        res += num_to_words_below_1000(n // 10000000) + " Crore "
        n %= 10000000
    if n >= 100000:
        res += num_to_words_below_1000(n // 100000) + " Lakh "
        n %= 100000
    if n >= 1000:
        res += num_to_words_below_1000(n // 1000) + " Thousand "
        n %= 1000
    if n > 0:
        res += num_to_words_below_1000(n)
        
    return res.strip() + " Rupees Only"

# --- 4. DATA FETCHING FUNCTIONS ---
def get_dropdown_data(category_name):
    try:
        res = supabase.table("dropdown_master").select("option_value").eq("category", category_name).eq("is_active", True).execute()
        if res.data:
            return [r["option_value"] for r in res.data]
    except Exception as e:
        pass
    return []

team_list = get_dropdown_data("Team Name") or ["No Teams Available"]
vendor_list = get_dropdown_data("Vendor Name") or ["No Vendors Available"]
pay_from_list = get_dropdown_data("Payment From") or ["Bank", "Cash"]
pay_type_list = get_dropdown_data("Payment Type") or ["NEFT", "RTGS", "UPI"]


# --- 5. POPUP DIALOGS FOR INVOICES ---
@st.dialog("📝 Team Invoice Entry", width="large")
def team_invoice_dialog(row_data=None):
    is_new = row_data is None
    
    def_team = row_data.get("team_name", team_list[0]) if not is_new else team_list[0]
    def_inv = row_data.get("invoice_no", "") if not is_new else ""
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = pd.to_datetime(def_date_str).date()
    
    c1, c2, c3 = st.columns(3)
    team_val = c1.selectbox("Team Name *", options=team_list, index=team_list.index(def_team) if def_team in team_list else 0)
    inv_no = c2.text_input("Invoice No *", value=def_inv)
    
    is_duplicate = False
    if inv_no:
        try:
            dup_res = supabase.table("billing_invoices").select("id").eq("invoice_no", inv_no).execute()
            if dup_res.data:
                if is_new:
                    is_duplicate = True
                else:
                    if any(r['id'] != row_data['id'] for r in dup_res.data):
                        is_duplicate = True
            
            if is_duplicate:
                st.markdown("<span style='color:#ef4444; font-weight:800; font-size:0.9rem;'>⚠️ This invoice number is already exist in VISPL CRM.</span>", unsafe_allow_html=True)
        except Exception:
            pass

    inv_date = c3.date_input("Invoice Date", value=def_date, format="DD/MM/YYYY")
    
    c4, c5, c6, c7 = st.columns(4)
    proj_id = c4.text_input("Project ID", value=row_data.get("project_id", "") if not is_new else "")
    site_id = c5.text_input("Site ID", value=row_data.get("site_id", "") if not is_new else "")
    site_name = c6.text_input("Site Name", value=row_data.get("site_name", "") if not is_new else "")
    cluster = c7.text_input("Cluster", value=row_data.get("cluster", "") if not is_new else "")
    
    c8, c9, c10, c11 = st.columns(4)
    remark = c8.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    b_amt = row_data.get("basic_amount") if not is_new else None
    g_amt = row_data.get("gst_amount") if not is_new else None
    
    start_basic = float(b_amt) if b_amt is not None and not math.isnan(b_amt) else None
    
    if start_basic and start_basic > 0 and g_amt is not None and not math.isnan(g_amt):
        start_gst_perc = (float(g_amt) / start_basic) * 100
    else:
        start_gst_perc = None

    basic_amt = c9.number_input("Basic Amount (₹)", min_value=0.0, step=1.0, value=start_basic, placeholder="0")
    safe_basic = basic_amt if basic_amt is not None else 0.0
    
    if safe_basic > 0:
        c9.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_basic)}</div>", unsafe_allow_html=True)

    gst_perc = c10.number_input("GST (%)", min_value=0.0, step=1.0, value=start_gst_perc, placeholder="0")
    safe_gst = gst_perc if gst_perc is not None else 0.0
    
    gst_amt = safe_basic * (safe_gst / 100)
    total_calc = safe_basic + gst_amt
    
    c11.markdown(f"**GST Amount:**<br><span class='gst-highlight'>₹ {gst_amt:,.0f}</span>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:right; margin-top:15px; margin-bottom:15px;'><span style='font-size:1.2rem; font-weight:700; color:#64748b;'>Grand Total: </span><span class='total-highlight'>₹ {total_calc:,.0f}</span><br><span style='color:#ef4444; font-weight:800; font-size:0.95rem;'>{number_to_words(total_calc)}</span></div>", unsafe_allow_html=True)
    
    if st.button("💾 Save Team Invoice", type="primary", use_container_width=True):
        if not inv_no:
            st.error("⚠️ Invoice No is required!")
        elif is_duplicate:
            st.error("⚠️ Cannot Save! This invoice number already exists in CRM.")
        else:
            payload = {
                "invoice_type": "Team",
                "team_name": team_val,
                "amount": total_calc,
                "basic_amount": safe_basic,
                "gst_amount": gst_amt,
                "date": str(inv_date),
                "project_id": proj_id,
                "site_id": site_id,
                "site_name": site_name,
                "invoice_no": inv_no,
                "vendor_name": "",
                "remark": remark,
                "cluster": cluster
            }
            try:
                if is_new:
                    supabase.table("billing_invoices").insert(payload).execute()
                else:
                    supabase.table("billing_invoices").update(payload).eq("id", row_data["id"]).execute()
                st.success("✅ Team Invoice Saved Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

@st.dialog("📝 Vendor Invoice Entry", width="large")
def vendor_invoice_dialog(row_data=None):
    is_new = row_data is None
    
    def_vendor = row_data.get("vendor_name", vendor_list[0]) if not is_new else vendor_list[0]
    def_team = row_data.get("team_name", team_list[0]) if not is_new else team_list[0]
    def_inv = row_data.get("invoice_no", "") if not is_new else ""
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = pd.to_datetime(def_date_str).date()
    
    c1, c2, c3 = st.columns(3)
    vendor_val = c1.selectbox("Vendor Name *", options=vendor_list, index=vendor_list.index(def_vendor) if def_vendor in vendor_list else 0)
    inv_no = c2.text_input("Invoice No *", value=def_inv)
    
    is_duplicate = False
    if inv_no:
        try:
            dup_res = supabase.table("billing_invoices").select("id").eq("invoice_no", inv_no).execute()
            if dup_res.data:
                if is_new:
                    is_duplicate = True
                else:
                    if any(r['id'] != row_data['id'] for r in dup_res.data):
                        is_duplicate = True
            
            if is_duplicate:
                st.markdown("<span style='color:#ef4444; font-weight:800; font-size:0.9rem;'>⚠️ This invoice number is already exist in VISPL CRM.</span>", unsafe_allow_html=True)
        except Exception:
            pass

    inv_date = c3.date_input("Invoice Date", value=def_date, format="DD/MM/YYYY")
    
    c4, c5, c6, c7 = st.columns(4)
    team_val = c4.selectbox("Link to Team *", options=team_list, index=team_list.index(def_team) if def_team in team_list else 0)
    remark = c5.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    b_amt = row_data.get("basic_amount") if not is_new else None
    g_amt = row_data.get("gst_amount") if not is_new else None
    
    start_basic = float(b_amt) if b_amt is not None and not math.isnan(b_amt) else None
    
    if start_basic and start_basic > 0 and g_amt is not None and not math.isnan(g_amt):
        start_gst_perc = (float(g_amt) / start_basic) * 100
    else:
        start_gst_perc = None

    basic_amt = c6.number_input("Basic Amount (₹)", min_value=0.0, step=1.0, value=start_basic, placeholder="0")
    safe_basic = basic_amt if basic_amt is not None else 0.0
    
    if safe_basic > 0:
        c6.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_basic)}</div>", unsafe_allow_html=True)

    gst_perc = c7.number_input("GST (%)", min_value=0.0, step=1.0, value=start_gst_perc, placeholder="0")
    
    safe_gst = gst_perc if gst_perc is not None else 0.0
    
    gst_amt = safe_basic * (safe_gst / 100)
    total_calc = safe_basic + gst_amt
    
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 15px; border-radius: 12px; margin-top: 10px; margin-bottom: 20px; border: 1px solid #e2e8f0;'>
            <div><span style='font-weight:700; color:#64748b;'>GST Amount:</span> <span class='gst-highlight'>₹ {gst_amt:,.0f}</span></div>
            <div style='text-align:right;'><span style='font-size:1.2rem; font-weight:700; color:#64748b;'>Grand Total: </span><span class='total-highlight'>₹ {total_calc:,.0f}</span><br><span style='color:#ef4444; font-weight:800; font-size:0.95rem;'>{number_to_words(total_calc)}</span></div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💾 Save Vendor Invoice", type="primary", use_container_width=True):
        if not inv_no:
            st.error("⚠️ Invoice No is required!")
        elif is_duplicate:
            st.error("⚠️ Cannot Save! This invoice number already exists in CRM.")
        else:
            payload = {
                "invoice_type": "Vendor",
                "team_name": team_val,
                "amount": total_calc,
                "basic_amount": safe_basic,
                "gst_amount": gst_amt,
                "date": str(inv_date),
                "project_id": "", "site_id": "", "site_name": "", "cluster": "",
                "invoice_no": inv_no,
                "vendor_name": vendor_val,
                "remark": remark
            }
            try:
                if is_new:
                    supabase.table("billing_invoices").insert(payload).execute()
                else:
                    supabase.table("billing_invoices").update(payload).eq("id", row_data["id"]).execute()
                st.success("✅ Vendor Invoice Saved Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

@st.dialog("💳 Payment Entry", width="large")
def payment_dialog(row_data=None, mode="Team"):
    is_new = row_data is None
    
    def_from = row_data.get("pay_from", pay_from_list[0]) if not is_new else (pay_from_list[0] if pay_from_list else "")
    
    pay_to_opts = team_list if mode == "Team" else vendor_list
    def_to = row_data.get("pay_to", pay_to_opts[0]) if not is_new else (pay_to_opts[0] if pay_to_opts else "")
    
    def_type = row_data.get("pay_type", pay_type_list[0]) if not is_new else (pay_type_list[0] if pay_type_list else "")
    
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = pd.to_datetime(def_date_str).date()
    
    p1, p2, p3 = st.columns(3)
    pay_from = p1.selectbox("Payment From *", options=pay_from_list, index=pay_from_list.index(def_from) if def_from in pay_from_list else 0)
    pay_to = p2.selectbox("Pay To *", options=pay_to_opts, index=pay_to_opts.index(def_to) if def_to in pay_to_opts else 0)
    pay_type = p3.selectbox("Payment Type *", options=pay_type_list, index=pay_type_list.index(def_type) if def_type in pay_type_list else 0)
    
    p4, p5, p6 = st.columns(3)
    start_amount = float(row_data.get("amount", 0.0)) if not is_new else None
    pay_amt = p4.number_input("Amount (₹)", min_value=0.0, step=1.0, value=start_amount, placeholder="0")
    safe_pay_amt = pay_amt if pay_amt is not None else 0.0
    
    if safe_pay_amt > 0:
        p4.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_pay_amt)}</div>", unsafe_allow_html=True)
    
    pay_date = p5.date_input("Payment Date", value=def_date, format="DD/MM/YYYY")
    pay_remark = p6.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(f"💾 Save {mode} Payment", type="primary", use_container_width=True):
        if pay_amt is None or pay_amt <= 0:
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
                    "mode": mode
                }
                if is_new:
                    supabase.table("billing_payments").insert(payload).execute()
                else:
                    supabase.table("billing_payments").update(payload).eq("id", row_data["id"]).execute()
                st.success(f"✅ {mode} Payment Saved Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- 6. MAIN PAGE TABS ---
st.markdown("<h1 style='color:#0f172a; margin-bottom: 20px;'>💸 Team & Vendor Billing</h1>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📄 Invoice Entry", "💳 Payment Entry", "📊 Ledger Reports"])

# ==========================================
# TAB 1: INVOICE ENTRY
# ==========================================
with tab1:
    col_search, col_tbtn, col_vbtn, col_dl = st.columns([4, 2, 2, 2])
    with col_search:
        search_inv = st.text_input("Search", placeholder="🔍 Search Invoices...", label_visibility="collapsed", key="search_inv_input")
    with col_tbtn:
        if st.button("➕ Add Team Invoice", type="primary", use_container_width=True):
            team_invoice_dialog()
    with col_vbtn:
        if st.button("➕ Add Vendor Invoice", type="primary", use_container_width=True):
            vendor_invoice_dialog()
            
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        inv_res = supabase.table("billing_invoices").select("*").order("id", desc=True).execute()
        if inv_res.data:
            df_inv = pd.DataFrame(inv_res.data)
            
            if search_inv:
                mask = df_inv.astype(str).apply(lambda x: x.str.contains(search_inv, case=False, na=False)).any(axis=1)
                df_inv = df_inv[mask]

            with col_dl:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_inv.to_excel(writer, index=False, sheet_name='Invoices')
                st.download_button(label="📥 Download Excel", data=buffer.getvalue(), file_name="Invoices_List.xlsx", use_container_width=True, type="secondary", key="dl_inv_btn")

            if not df_inv.empty:
                df_inv.insert(0, "Select", False)
                
                if "basic_amount" in df_inv.columns:
                    df_inv["Basic Amount"] = df_inv["basic_amount"]
                else:
                    df_inv["Basic Amount"] = ""
                    
                if "gst_amount" in df_inv.columns:
                    df_inv["GST Amount"] = df_inv["gst_amount"]
                else:
                    df_inv["GST Amount"] = ""
                
                if "date" in df_inv.columns:
                    df_inv["date"] = pd.to_datetime(df_inv["date"], errors="coerce").dt.date
                
                display_cols = ["Select", "id", "team_name", "invoice_no", "date", "project_id", "site_id", "site_name", "cluster", "Basic Amount", "GST Amount", "amount", "vendor_name", "remark"]
                actual_disp_cols = [c for c in display_cols if c in df_inv.columns]
                
                edited_df = st.data_editor(
                    df_inv[actual_disp_cols],
                    hide_index=True,
                    use_container_width=True,
                    height=500,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("SELECT", width="small", default=False),
                        "id": None, 
                        "team_name": "Team Name",
                        "invoice_no": "Invoice No.",
                        "date": st.column_config.DateColumn("Invoice Date", format="DD/MM/YYYY"),
                        "project_id": "Project ID",
                        "site_id": "Site ID",
                        "site_name": "Site Name",
                        "cluster": "Cluster",
                        "Basic Amount": st.column_config.NumberColumn("Basic Amount", format="₹ %d"),
                        "GST Amount": st.column_config.NumberColumn("GST Amount", format="₹ %d"),
                        "amount": st.column_config.NumberColumn("Total Amount", format="₹ %d"),
                        "vendor_name": "Vendor",
                        "remark": "Remark"
                    }
                )
                
                sel_rows = edited_df[edited_df["Select"] == True]
                if not sel_rows.empty:
                    st.markdown("---")
                    row_dict = sel_rows.iloc[0].to_dict()
                    
                    orig_dict = df_inv[df_inv['id'] == row_dict['id']].iloc[0].to_dict()
                    
                    col_act1, col_act2, _ = st.columns([2, 2, 8])
                    
                    with col_act1:
                        if st.button("👁️ Edit Selected", type="primary", use_container_width=True, key="edit_inv_btn"):
                            if orig_dict.get("invoice_type") == "Team":
                                team_invoice_dialog(orig_dict)
                            else:
                                vendor_invoice_dialog(orig_dict)
                                
                    with col_act2:
                        if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True, key="del_inv_btn"):
                            try:
                                supabase.table("billing_invoices").delete().eq("id", orig_dict["id"]).execute()
                                st.success("✅ Deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting: {e}")
            else:
                st.info("No invoices match your search.")
        else:
            st.info("No invoices found. Click the buttons above to add one.")
            with col_dl:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_inv_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

# ==========================================
# TAB 2: PAYMENT ENTRY
# ==========================================
with tab2:
    col_search_p, col_tpbtn, col_vpbtn, col_dl_p = st.columns([4, 2, 2, 2])
    with col_search_p:
        search_pay = st.text_input("Search", placeholder="🔍 Search Payments...", label_visibility="collapsed", key="search_pay_input")
    with col_tpbtn:
        if st.button("➕ Add Team Payment", type="primary", use_container_width=True):
            payment_dialog(mode="Team")
    with col_vpbtn:
        if st.button("➕ Add Vendor Payment", type="primary", use_container_width=True):
            payment_dialog(mode="Vendor")
            
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        pay_res = supabase.table("billing_payments").select("*").order("id", desc=True).execute()
        if pay_res.data:
            df_pay = pd.DataFrame(pay_res.data)
            
            if search_pay:
                mask_p = df_pay.astype(str).apply(lambda x: x.str.contains(search_pay, case=False, na=False)).any(axis=1)
                df_pay = df_pay[mask_p]

            with col_dl_p:
                buffer_p = io.BytesIO()
                with pd.ExcelWriter(buffer_p, engine='openpyxl') as writer:
                    df_pay.to_excel(writer, index=False, sheet_name='Payments')
                st.download_button(label="📥 Download Excel", data=buffer_p.getvalue(), file_name="Payments_List.xlsx", use_container_width=True, type="secondary", key="dl_pay_btn")

            if not df_pay.empty:
                df_pay.insert(0, "Select", False)
                
                if "date" in df_pay.columns:
                    df_pay["date"] = pd.to_datetime(df_pay["date"], errors="coerce").dt.date
                
                edited_pay_df = st.data_editor(
                    df_pay,
                    hide_index=True,
                    use_container_width=True,
                    height=500,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("SELECT", width="small", default=False),
                        "date": st.column_config.DateColumn("Payment Date", format="DD/MM/YYYY"),
                        "amount": st.column_config.NumberColumn("AMOUNT", format="₹ %d")
                    },
                    key="pay_editor"
                )
                
                sel_p_rows = edited_pay_df[edited_pay_df["Select"] == True]
                if not sel_p_rows.empty:
                    st.markdown("---")
                    p_row_dict = sel_p_rows.iloc[0].to_dict()
                    col_pact1, col_pact2, _ = st.columns([2, 2, 8])
                    
                    with col_pact1:
                        if st.button("👁️ Edit Selected", type="primary", use_container_width=True, key="edit_p_btn"):
                            payment_dialog(row_data=p_row_dict, mode=p_row_dict.get("mode", "Team"))
                                
                    with col_pact2:
                        if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True, key="del_p_btn"):
                            try:
                                supabase.table("billing_payments").delete().eq("id", p_row_dict["id"]).execute()
                                st.success("✅ Deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting: {e}")
            else:
                st.info("No payments match your search.")
        else:
            st.info("No payments found. Click the buttons above to add one.")
            with col_dl_p:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_p_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

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
        tot_inv = 0.0
        tot_pay = 0.0
        df_inv_rep, df_pay_rep = pd.DataFrame(), pd.DataFrame()
        
        try:
            inv_col = "team_name" if rep_mode == "Team" else "vendor_name"
            res_inv = supabase.table("billing_invoices").select("*").eq("invoice_type", rep_mode).eq(inv_col, sel_name).execute()
            if res_inv.data:
                df_inv_rep = pd.DataFrame(res_inv.data)
                tot_inv = df_inv_rep["amount"].sum()
                
                # --- NAYI LINE: Mapping required columns exactly for Reports ---
                req_cols = ["invoice_no", "date", "project_id", "site_id", "site_name", "basic_amount", "gst_amount", "amount"]
                for c in req_cols:
                    if c not in df_inv_rep.columns:
                        df_inv_rep[c] = ""
                df_inv_rep = df_inv_rep[req_cols]
                
                df_inv_rep.rename(columns={
                    "invoice_no": "Invoice No.",
                    "date": "Invoice Date",
                    "project_id": "Project ID",
                    "site_id": "Site ID",
                    "site_name": "Site Name",
                    "basic_amount": "Basic Amt",
                    "gst_amount": "GST",
                    "amount": "Total"
                }, inplace=True)
                
                if "Invoice Date" in df_inv_rep.columns:
                    df_inv_rep["Invoice Date"] = pd.to_datetime(df_inv_rep["Invoice Date"], errors="coerce").dt.strftime('%d/%m/%Y')

            res_pay = supabase.table("billing_payments").select("*").eq("mode", rep_mode).eq("pay_to", sel_name).execute()
            if res_pay.data:
                df_pay_rep = pd.DataFrame(res_pay.data)
                tot_pay = df_pay_rep["amount"].sum()
                df_pay_rep = df_pay_rep[["date", "pay_from", "pay_type", "amount", "remark"]]
                
                if "date" in df_pay_rep.columns:
                    df_pay_rep["date"] = pd.to_datetime(df_pay_rep["date"], errors="coerce").dt.strftime('%d/%m/%Y')
                    
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        bal = tot_inv - tot_pay
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Billed</div><div class='kpi-value-blue'>₹ {tot_inv:,.0f}</div></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Paid</div><div class='kpi-value-green'>₹ {tot_pay:,.0f}</div></div>", unsafe_allow_html=True)
        with k3:
            bal_color = "kpi-value-red" if bal > 0 else "kpi-value-green"
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Balance</div><div class='{bal_color}'>₹ {bal:,.0f}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### 📚 Invoices")
            st.dataframe(df_inv_rep, use_container_width=True, hide_index=True)
        with t2:
            st.markdown("#### 💸 Payments")
            st.dataframe(df_pay_rep, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        col_down1, col_down2, _ = st.columns([2, 2, 6])
        
        with col_down1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if not df_inv_rep.empty: df_inv_rep.to_excel(writer, index=False, sheet_name='Invoices')
                if not df_pay_rep.empty: df_pay_rep.to_excel(writer, index=False, sheet_name='Payments')
                summary_df = pd.DataFrame({"Name": [sel_name], "Total Billed": [tot_inv], "Total Paid": [tot_pay], "Balance": [bal]})
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
            
            st.download_button(label="📊 Download Excel", data=buffer.getvalue(), file_name=f"{sel_name}_Ledger.xlsx", type="primary", use_container_width=True)

        with col_down2:
            def generate_pdf():
                if FPDF is None:
                    raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                
                if os.path.exists("logo (1).png"):
                    pdf.image("logo (1).png", x=75, y=10, w=60)
                    pdf.ln(28) 
                
                primary_color = (15, 23, 42) 
                secondary_color = (59, 130, 246) 
                green_color = (16, 185, 129) 
                red_color = (239, 68, 68) 
                
                pdf.set_text_color(*primary_color)
                pdf.set_font("Arial", 'B', 18)
                pdf.cell(190, 10, "VISIONTECH INFRA SOLUTION PVT. LTD.", ln=True, align='C')
                
                pdf.set_text_color(*secondary_color)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(190, 8, "LEDGER & BALANCE SHEET", ln=True, align='C')
                
                pdf.set_text_color(100, 116, 139) 
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(190, 8, f"Statement For: {sel_name}", ln=True, align='C')
                pdf.ln(5)
                
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(10, pdf.get_y(), 190, 25, 'FD')
                
                pdf.set_y(pdf.get_y() + 5)
                pdf.set_font("Arial", 'B', 11)
                
                pdf.set_text_color(*secondary_color)
                pdf.cell(63, 8, f"Total Billed: Rs. {tot_inv:,.0f}", ln=False, align='C')
                
                pdf.set_text_color(*green_color)
                pdf.cell(63, 8, f"Total Paid: Rs. {tot_pay:,.0f}", ln=False, align='C')
                
                bal_color = red_color if bal > 0 else green_color
                pdf.set_text_color(*bal_color)
                pdf.cell(64, 8, f"Net Balance: Rs. {bal:,.0f}", ln=True, align='C')
                
                pdf.ln(12)
                
                def create_table(title, df, header_color):
                    if not df.empty:
                        pdf.set_font("Arial", 'B', 12)
                        pdf.set_text_color(*header_color)
                        pdf.cell(190, 8, title, ln=True, align='L')
                        
                        pdf.set_fill_color(*header_color)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_font("Arial", 'B', 8)
                        
                        cols = df.columns.tolist()
                        
                        # --- NAYI LINE: Custom column widths to perfectly fit the 8 Invoice columns in A4 PDF ---
                        if len(cols) == 8:
                            col_widths = [20, 20, 25, 28, 27, 22, 20, 28]
                        else:
                            col_widths = [190 / len(cols)] * len(cols)
                            
                        for i, col in enumerate(cols):
                            pdf.cell(col_widths[i], 8, str(col).upper().replace('_', ' '), border=1, align='C', fill=True)
                        pdf.ln()
                        
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_font("Arial", '', 7.5)
                        
                        fill = False
                        for _, row in df.iterrows():
                            if fill:
                                pdf.set_fill_color(241, 245, 249)
                            else:
                                pdf.set_fill_color(255, 255, 255)
                                
                            for i, col in enumerate(cols):
                                val = row[col]
                                col_lower = str(col).lower()
                                
                                # --- NAYI LINE: Smart formatting for Basic, GST and Total amounts in PDF ---
                                if 'amt' in col_lower or 'total' in col_lower or 'gst' in col_lower or 'basic' in col_lower or 'amount' in col_lower:
                                    try:
                                        if pd.notna(val) and str(val).strip() != "":
                                            val_str = f"Rs. {float(val):,.0f}"
                                        else:
                                            val_str = ""
                                    except:
                                        val_str = str(val)[:30]
                                else:
                                    val_str = str(val)[:30] if pd.notna(val) else ""
                                    
                                pdf.cell(col_widths[i], 7, val_str, border=1, align='C', fill=fill)
                            pdf.ln()
                            fill = not fill
                        pdf.ln(5)
                
                create_table("INVOICES (BILLED)", df_inv_rep, secondary_color)
                create_table("PAYMENTS (PAID)", df_pay_rep, green_color)
                
                return pdf.output(dest='S').encode('latin1')

            try:
                pdf_bytes = generate_pdf()
                st.download_button(label="📄 Download PDF", data=pdf_bytes, file_name=f"{sel_name}_Report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(str(e))
