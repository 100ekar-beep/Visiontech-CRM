import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client
from st_keyup import st_keyup
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Top Action Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    
    div.stButton > button p, 
    div.stButton > button span, 
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    
    div[data-testid="stDialog"] h1, 
    div[data-testid="stDialog"] h2, 
    div[data-testid="stDialog"] h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
    div[data-testid="stDialog"] p {
        color: #e2e8f0 !important; 
    }
    div[data-testid="stDialog"] button[kind="icon"] svg {
        fill: #ffffff !important; 
    }

    .modal-section-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
    }
    
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important;
        margin: 0.5rem 1rem !important;
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* =========================================================
       FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING
       ========================================================= */
    .st-key-invoice_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important;
        padding: 0px 0 !important;
    }
    .st-key-invoice_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 3400px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-invoice_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    .st-key-invoice_table_wrap div[data-testid="column"] {
        padding: 0 12px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-invoice_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    
    .st-key-invoice_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    .st-key-invoice_table_wrap .tbl-cell {
        color: #e2e8f0;
        font-size: 0.86rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-invoice_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    .st-key-invoice_table_wrap button {
        height: 32px !important;
        width: 100% !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important;
        cursor: pointer !important;
    }
    .st-key-invoice_table_wrap button:hover {
        background: #3b82f6 !important;
        border-color: #60a5fa !important;
        transform: translateY(-2px) !important;
    }

    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(1) { padding: 0 10px 0 15px !important; }
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(2),
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(3),
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(4) {
        padding: 4px 4px !important;
        border-right: none !important;
    }
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(5) {
        padding: 4px 15px 4px 4px !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"         
SUPABASE_KEY = "sb_secret_ChVw7W5z9c5k74ycI5GnYA_KBYB1blv"    

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- SAFE DATE PARSER HELPER ---
def parse_date_safely(val):
    if not val or str(val).strip() in ['', '-', 'nan', 'None']:
        return None
    val_str = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None

# --- 3.5 ADD INVOICE DIALOG FUNCTION ---
@st.dialog("📄 Add Invoice Record", width="large")
def add_invoice_dialog():
    st.caption("Configure invoice details, taxation, and milestone payments")
    
    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", placeholder="Circle name")
        with c2: invoice_number = st.text_input("Invoice_number", placeholder="Inv Number")
        with c3: 
            raw_inv_date = st.date_input("Invoice_date", value=None)
            invoice_date = raw_inv_date.strftime("%d/%m/%Y") if raw_inv_date else ""
        with c4: project_id = st.text_input("Project_id", placeholder="Project ID")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", placeholder="Site ID")
        with c6: site_name = st.text_input("Site_name", placeholder="Site Name")
        with c7: po_number = st.text_input("Po_number", placeholder="PO Number")
        with c8: wcc_number = st.text_input("Wcc_number", placeholder="WCC Number")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION (Basic + CGST + SGST + IGST = Total)</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=0.0, format="%.2f")
        with c10: cgst = st.number_input("CGST", value=0.0, format="%.2f")
        with c11: sgst = st.number_input("SGST", value=0.0, format="%.2f")
        with c12: igst = st.number_input("IGST", value=0.0, format="%.2f")
        
        total = basic_amount + cgst + sgst + igst
        with c13: 
            st.markdown(f"<p style='color:#3b82f6; font-weight:800; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", placeholder="Receipt No")
        with c15: percentage_amount = st.number_input("%Amount", value=0.0, format="%.2f")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=0.0, format="%.2f")
        with p2: 
            raw_p1_date = st.date_input("Payment_1_date", value=None)
            payment_1_date = raw_p1_date.strftime("%d/%m/%Y") if raw_p1_date else ""
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=0.0, format="%.2f")
        with p4: 
            raw_p2_date = st.date_input("Payment_2_date", value=None)
            payment_2_date = raw_p2_date.strftime("%d/%m/%Y") if raw_p2_date else ""
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=0.0, format="%.2f")
        with p6: 
            raw_p3_date = st.date_input("Payment_3_date", value=None)
            payment_3_date = raw_p3_date.strftime("%d/%m/%Y") if raw_p3_date else ""

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=0.0, format="%.2f")
        with b2: remark = st.text_input("Remark", placeholder="Enter remarks...")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            insert_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            try:
                supabase.table("invoice_management").insert(insert_data).execute()
                st.success("✅ Invoice Added Successfully!")
                st.session_state.current_page = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Saving: {e}")

# --- 3.6 EDIT INVOICE DIALOG FUNCTION ---
@st.dialog("✏️ Edit Invoice Record", width="large")
def edit_invoice_dialog(row_data):
    st.caption("Update invoice parameters")
    
    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", value=str(row_data.get('circle', '')), key="ed_circle")
        with c2: invoice_number = st.text_input("Invoice_number", value=str(row_data.get('invoice_number', '')), key="ed_inv_num")
        with c3: 
            parsed_date = parse_date_safely(row_data.get('invoice_date', ''))
            raw_inv_date = st.date_input("Invoice_date", value=parsed_date, key="ed_inv_date")
            invoice_date = raw_inv_date.strftime("%d/%m/%Y") if raw_inv_date else ""
        with c4: project_id = st.text_input("Project_id", value=str(row_data.get('project_id', '')), key="ed_proj_id")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", value=str(row_data.get('site_id', '')), key="ed_site_id")
        with c6: site_name = st.text_input("Site_name", value=str(row_data.get('site_name', '')), key="ed_site_name")
        with c7: po_number = st.text_input("Po_number", value=str(row_data.get('po_number', '')), key="ed_po_num")
        with c8: wcc_number = st.text_input("Wcc_number", value=str(row_data.get('wcc_number', '')), key="ed_wcc_num")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=float(row_data.get('basic_amount', 0.0) or 0.0), format="%.2f", key="ed_basic")
        with c10: cgst = st.number_input("CGST", value=float(row_data.get('cgst', 0.0) or 0.0), format="%.2f", key="ed_cgst")
        with c11: sgst = st.number_input("SGST", value=float(row_data.get('sgst', 0.0) or 0.0), format="%.2f", key="ed_sgst")
        with c12: igst = st.number_input("IGST", value=float(row_data.get('igst', 0.0) or 0.0), format="%.2f", key="ed_igst")
        
        total = basic_amount + cgst + sgst + igst
        with c13: 
            st.markdown(f"<p style='color:#3b82f6; font-weight:800; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", value=str(row_data.get('receipt_number', '')), key="ed_receipt")
        with c15: percentage_amount = st.number_input("%Amount", value=float(row_data.get('percentage_amount', 0.0) or 0.0), format="%.2f", key="ed_pct")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=float(row_data.get('payment_1_amount', 0.0) or 0.0), format="%.2f", key="ed_p1_amt")
        with p2: 
            p1_d = parse_date_safely(row_data.get('payment_1_date', ''))
            raw_p1 = st.date_input("Payment_1_date", value=p1_d, key="ed_p1_date")
            payment_1_date = raw_p1.strftime("%d/%m/%Y") if raw_p1 else ""
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=float(row_data.get('payment_2_amount', 0.0) or 0.0), format="%.2f", key="ed_p2_amt")
        with p4: 
            p2_d = parse_date_safely(row_data.get('payment_2_date', ''))
            raw_p2 = st.date_input("Payment_2_date", value=p2_d, key="ed_p2_date")
            payment_2_date = raw_p2.strftime("%d/%m/%Y") if raw_p2 else ""
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=float(row_data.get('payment_3_amount', 0.0) or 0.0), format="%.2f", key="ed_p3_amt")
        with p6: 
            p3_d = parse_date_safely(row_data.get('payment_3_date', ''))
            raw_p3 = st.date_input("Payment_3_date", value=p3_d, key="ed_p3_date")
            payment_3_date = raw_p3.strftime("%d/%m/%Y") if raw_p3 else ""

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=float(row_data.get('balance', 0.0) or 0.0), format="%.2f", key="ed_bal")
        with b2: remark = st.text_input("Remark", value=str(row_data.get('remark', '')), key="ed_rem")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Update Invoice", type="primary", use_container_width=True):
            update_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            try:
                supabase.table("invoice_management").update(update_data).eq("id", row_data['id']).execute()
                st.success("✅ Invoice Updated Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating: {e}")

# --- 3.7 VIEW INVOICE DIALOG (READ-ONLY) ---
@st.dialog("👁️ View Invoice Record", width="large")
def view_invoice_dialog(row_data):
    st.caption("Read-only preview")
    st.markdown('<div class="modal-section-title">🧾 GENERAL DETAILS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("Circle", value=row_data.get('circle', ''), disabled=True)
    with c2: st.text_input("Invoice Number", value=row_data.get('invoice_number', ''), disabled=True)
    with c3: st.text_input("Invoice Date", value=row_data.get('invoice_date', ''), disabled=True)
    with c4: st.text_input("Project ID", value=row_data.get('project_id', ''), disabled=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5: st.text_input("Site ID", value=row_data.get('site_id', ''), disabled=True)
    with c6: st.text_input("Site Name", value=row_data.get('site_name', ''), disabled=True)
    with c7: st.text_input("PO Number", value=row_data.get('po_number', ''), disabled=True)
    with c8: st.text_input("WCC Number", value=row_data.get('wcc_number', ''), disabled=True)

    st.markdown('<div class="modal-section-title">💰 AMOUNTS & TOTAL</div>', unsafe_allow_html=True)
    c9, c10, c11, c12, c13, c14 = st.columns(6)
    
    b_amt = float(row_data.get('basic_amount', 0) or 0)
    c_amt = float(row_data.get('cgst', 0) or 0)
    s_amt = float(row_data.get('sgst', 0) or 0)
    i_amt = float(row_data.get('igst', 0) or 0)
    t_amt = row_data.get('total')
    if not t_amt or str(t_amt).lower() in ['nan', 'none', '']:
        t_amt = b_amt + c_amt + s_amt + i_amt

    with c9: st.text_input("Basic Amount", value=str(b_amt), disabled=True)
    with c10: st.text_input("CGST", value=str(c_amt), disabled=True)
    with c11: st.text_input("SGST", value=str(s_amt), disabled=True)
    with c12: st.text_input("IGST", value=str(i_amt), disabled=True)
    with c13: st.text_input("Total", value=str(t_amt), disabled=True)
    with c14: st.text_input("% Amount", value=str(row_data.get('percentage_amount', '')), disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True):
        st.rerun()

# --- 3.8 DELETE DIALOG ---
@st.dialog("🗑️ Confirm Deletion", width="small")
def delete_invoice_dialog(rid, inv_num):
    st.warning(f"Delete invoice '{inv_num}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                supabase.table("invoice_management").delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

# --- 3.9 BULK UPLOAD DIALOG ---
@st.dialog("📤 Bulk Upload Invoices", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel file to bulk import invoice records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_inv_file")
    
    if uploaded_file and st.button("🚀 Process & Upload", type="primary", use_container_width=True):
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df_upload = pd.read_excel(uploaded_file)
            else:
                df_upload = pd.read_csv(uploaded_file, sep='\t')
            
            added = 0
            for _, row in df_upload.iterrows():
                p_id = str(row.get("project_id", row.get("Project ID", ""))).strip()
                if not p_id or p_id.lower() == "nan": continue
                
                insert_dict = {}
                for col in columns_list:
                    if col != "id" and col != "🎯 Select":
                        val = row.get(col, row.get(col.lower(), ""))
                        insert_dict[col] = str(val).strip() if pd.notna(val) and str(val).lower() != 'nan' else ""
                
                try:
                    b = float(insert_dict.get('basic_amount', 0) or 0)
                    c = float(insert_dict.get('cgst', 0) or 0)
                    s = float(insert_dict.get('sgst', 0) or 0)
                    i = float(insert_dict.get('igst', 0) or 0)
                    insert_dict['total'] = b + c + s + i
                except:
                    pass

                try:
                    supabase.table("invoice_management").insert(insert_dict).execute()
                    added += 1
                except:
                    pass
            st.success(f"✅ Bulk Upload Complete! {added} records added.")
            st.session_state.current_page = 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

# --- TOP BANNER ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🧾 Invoice Management Hub
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 4. TOP ACTION BAR ---
col_title, col_ref, col_add, col_upload, col_export = st.columns([3, 1, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>📊 Live Invoices Master</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with col_add:
    if st.button("➕ Add Invoice", use_container_width=True):
        add_invoice_dialog()
with col_upload:
    if st.button("📤 Bulk Upload", use_container_width=True):
        bulk_upload_dialog()
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH DATA FROM SUPABASE ---
table_name = "invoice_management"
columns_list = [
    "id", "circle", "invoice_number", "invoice_date", "basic_amount", "cgst", "sgst", "igst", "total",
    "project_id", "site_id", "site_name", "po_number", "wcc_number", "receipt_number", "percentage_amount",
    "payment_1_amount", "payment_1_date", "payment_2_amount", "payment_2_date", "payment_3_amount", "payment_3_date",
    "balance", "remark"
]

try:
    response = supabase.table(table_name).select("*").execute()
    data = response.data
except Exception:
    data = []

if data:
    df = pd.DataFrame(data)
    if 'id' in df.columns:
        id_numeric = pd.to_numeric(df['id'], errors='coerce')
        if id_numeric.notna().any():
            df['id_num'] = id_numeric.fillna(-1)
            df = df.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
        else:
            df = df.iloc[::-1].reset_index(drop=True)
    for col in columns_list:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=columns_list)

if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)

# Export Trigger
if st.session_state.get('action') == "export":
    export_df = df.copy()
    if "🎯 Select" in export_df.columns: export_df = export_df.drop(columns=["🎯 Select"])
    if "id" in export_df.columns: export_df = export_df.drop(columns=["id"])
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Invoices')
    st.download_button("📊 Download Excel File", data=buffer.getvalue(), file_name="Invoice_Management_Export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")
    st.session_state.action = ""

# --- LIVE SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Database Records")
with col_search:
    search_query = st_keyup("Search", placeholder="🔍 Search invoices...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- 6. PAGINATION LOGIC ---
rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.current_page > total_pages: st.session_state.current_page = total_pages
elif st.session_state.current_page < 1: st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page
df_page = df.iloc[start_idx:end_idx].copy()

keys_seq = [
    'circle', 'invoice_number', 'invoice_date', 'basic_amount', 'cgst', 'sgst', 'igst', 'total',
    'project_id', 'site_id', 'site_name', 'po_number', 'wcc_number', 'receipt_number', 'percentage_amount',
    'payment_1_amount', 'payment_1_date', 'payment_2_amount', 'payment_2_date', 'payment_3_amount', 'payment_3_date',
    'balance', 'remark'
]

COL_RATIOS = [0.3, 0.35, 0.35, 0.35] + [1.0] * len(keys_seq)
COL_LABELS = [
    "#", "👁️", "✏️", "🗑️",
    "Circle", "Invoice No", "Invoice Date", "Basic Amount", "CGST", "SGST", "IGST", "Total",
    "Project ID", "Site ID", "Site Name", "PO Number", "WCC Number", "Receipt No", "% Amount",
    "Pay 1 Amt", "Pay 1 Date", "Pay 2 Amt", "Pay 2 Date", "Pay 3 Amt", "Pay 3 Date", "Balance", "Remark"
]

with st.container(key="invoice_table_wrap", height=560):
    if df_page.empty:
        st.info("No invoice records found.")
    else:
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1
            rcols = st.columns(COL_RATIOS)

            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            with rcols[1]:
                if st.button("👁️", key=f"view_inv_{rid}", use_container_width=True):
                    view_invoice_dialog(row_dict)
            with rcols[2]:
                if st.button("✏️", key=f"edit_inv_{rid}", use_container_width=True):
                    edit_invoice_dialog(row_dict)
            with rcols[3]:
                if st.button("🗑️", key=f"del_inv_{rid}", use_container_width=True):
                    delete_invoice_dialog(rid, row_dict.get('invoice_number', ''))

            for idx, k in enumerate(keys_seq, start=4):
                val = row_dict.get(k, '')
                
                if k == 'total' and (val is None or str(val).strip() == '' or str(val).lower() == 'nan'):
                    try:
                        b = float(row_dict.get('basic_amount', 0) or 0)
                        c = float(row_dict.get('cgst', 0) or 0)
                        s = float(row_dict.get('sgst', 0) or 0)
                        i = float(row_dict.get('igst', 0) or 0)
                        val = f"{b + c + s + i:.2f}"
                    except:
                        val = '-'
                
                display_val = val if val is not None and str(val).strip() != '' else '-'
                rcols[idx].markdown(f"<div class='tbl-cell'>{display_val}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 1)):
        st.session_state.current_page -= 1
        st.rerun()
with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages)):
        st.session_state.current_page += 1
        st.rerun()
