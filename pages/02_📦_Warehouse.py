import streamlit as st
import pandas as pd
import math
import io
import requests # <--- NEW: Added requests for WhatsApp API
import smtplib  # <--- NEW: For Email Sending
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Warehouse Hub", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'wh_mat_count' not in st.session_state:
    st.session_state.wh_mat_count = 1

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

    /* Pagination Text & Button Font Color Fix */
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
    
    /* FIX FOR DIALOG TITLE AND CAPTION COLOR */
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
    
    /* FIX FOR FIELD LABELS COLOR (Make them bright white) */
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* Make disabled/read-only input text inside Warehouse Site Info strictly BLACK and BOLD */
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important;
        font-weight: 700 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Individual Sidebar Links / Buttons */
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

    /* Hover Effect for Sidebar Links */
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }

    /* Active/Selected Page Button */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Clean up the default Streamlit styling overrides */
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* =========================================================
       FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING
       ========================================================= */
    .st-key-wh_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important; /* Enables both Horizontal & Vertical Scroll */
        padding: 0px 0 !important;
    }
    /* Force inner rows to be extremely wide so they NEVER squish or overlap */
    .st-key-wh_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 3500px !important; /* MAGIC FIX FOR HORIZONTAL SCROLL */
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-wh_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    /* Cell padding and border */
    .st-key-wh_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; /* Proper spacing */
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-wh_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    
    .st-key-wh_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    /* Strict nowrap with ellipsis to prevent column bleeding */
    .st-key-wh_table_wrap .tbl-cell {
        color: #e2e8f0;
        font-size: 0.86rem;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.4;
        width: 100%;
    }
    .st-key-wh_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    /* Fixed native Action Buttons strictly constrained to their columns */
    .st-key-wh_table_wrap button {
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
        pointer-events: auto !important; /* Force clickability */
        cursor: pointer !important;
    }
    .st-key-wh_table_wrap button:hover {
        background: #3b82f6 !important;
        border-color: #60a5fa !important;
        transform: translateY(-2px) !important;
    }

    /* -------------------------------------------------------------
       FIXED FORCE LEFT BUTTON CSS: Action Columns (2, 3, 4)
       ------------------------------------------------------------- */
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(1) {
        padding: 0 10px 0 15px !important;
    }
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(2) .tbl-head,
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(3) .tbl-head,
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(4) .tbl-head {
        color: #94a3b8; 
    }
    /* Remove borders and padding between action button columns to merge them visually */
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(2),
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(3) {
        padding: 4px 4px !important;
        border-right: none !important;
    }
    .st-key-wh_table_wrap div[data-testid="column"]:nth-child(4) {
        padding: 4px 15px 4px 4px !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* Round, color-coded, compact action icon buttons */
    .st-key-wh_table_wrap div[class*="st-key-vbtn_"] button,
    .st-key-wh_table_wrap div[class*="st-key-ebtn_"] button,
    .st-key-wh_table_wrap div[class*="st-key-dbtn_"] button {
        width: 100% !important; 
        max-width: 34px !important;
        height: 32px !important;
        padding: 0 !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
        margin: 0 auto !important;
    }
    div[class*="st-key-vbtn_"] button { background: rgba(34,197,94,0.15) !important; border: 1px solid rgba(34,197,94,0.3) !important; }
    div[class*="st-key-ebtn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-dbtn_"] button { background: rgba(239,68,68,0.15) !important; border: 1px solid rgba(239,68,68,0.3) !important; }
    
    /* Status badge pill */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.4px;
        white-space: normal;
        word-break: break-word;
        text-align: center;
    }
    .status-green  { background: rgba(34,197,94,0.18);  color: #4ade80; }
    .status-blue   { background: rgba(59,130,246,0.18); color: #60a5fa; }
    .status-yellow { background: rgba(234,179,8,0.18);  color: #facc15; }
    .status-red    { background: rgba(239,68,68,0.18);  color: #f87171; }
    .status-grey   { background: rgba(148,163,184,0.15); color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"       
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- HELPER FUNCTIONS ---
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

def get_site_projects():
    try:
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("site_data").select("*").eq("workspace", active_ws).execute()
        return res.data if res.data else []
    except Exception as e:
        st.toast(f"Database Error: {e}", icon="❌")
        return []

# --- 3.5 WAREHOUSE MATERIAL ADD DIALOG (POP-UP) ---
@st.dialog("📦 Add New Warehouse Material", width="large")
def add_warehouse_material_dialog():
    st.caption("Manage transaction items and asset movements against Project IDs")
    
    all_dd = get_all_dropdowns()
    site_records = get_site_projects()
    
    unique_proj_ids = []
    for r in site_records:
        pid, wh_mat = "", ""
        for k, v in r.items():
            k_clean = str(k).strip().lower().replace("_", " ")
            if k_clean == "project id":
                pid = v
            elif k_clean == "wh material":
                wh_mat = v
                
        if str(pid).strip() and str(wh_mat).strip().lower() == "required":
            unique_proj_ids.append(str(pid).strip())
            
    unique_proj_ids = list(set(unique_proj_ids))
    unique_proj_ids.sort()
    
    if not unique_proj_ids:
        st.toast("Koi bhi Project ID 'WH Material = Required' status ke sath nahi mili!", icon="ℹ️")
        
    proj_id_opts = ["Select Project ID"] + unique_proj_ids

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            proj_id = st.selectbox("PROJECT ID *", proj_id_opts)
            
        site_id_val, site_name_val, cluster_val, team_val = "", "", "", ""
        if proj_id != "Select Project ID":
            for r in site_records:
                curr_pid = ""
                for k, v in r.items():
                    if str(k).strip().lower().replace("_", " ") == "project id":
                        curr_pid = str(v).strip()
                        break
                
                if curr_pid == proj_id:
                    for k, v in r.items():
                        k_clean = str(k).strip().lower().replace("_", " ")
                        if k_clean == "site id": site_id_val = str(v)
                        elif k_clean == "site name": site_name_val = str(v)
                        elif k_clean == "cluster": cluster_val = str(v)
                        elif k_clean == "team name" or k_clean == "team": team_val = str(v)
                    break

        with c2:
            st.text_input("SITE ID", value=site_id_val, disabled=True)
        with c3:
            st.text_input("SITE NAME", value=site_name_val, disabled=True)
        with c4:
            st.text_input("CLUSTER", value=cluster_val, disabled=True)
        with c5:
            st.text_input("TEAM", value=team_val, disabled=True)
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, key="w_srn_status")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        w_trans_types, w_boqs, w_item_codes, w_descs, w_qtys = [], [], [], [], []
        w_statuses, w_dates, w_stn_statuses, w_remarks = [], [], [], []
        
        for i in range(st.session_state.wh_mat_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"w_trans_{i}")
                w_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER *", placeholder="BOQ No", key=f"w_boq_{i}")
                w_boqs.append(boq_no)
            with mc3:
                i_code = st.text_input("ITEM CODE *", placeholder="Type & Press Enter", key=f"w_icode_{i}")
                w_item_codes.append(i_code)

            auto_desc = ""
            auto_stn = "Select"
            code_val = i_code.strip()
            if code_val:
                try:
                    item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                    if not item_res.data:
                        item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                        
                    if item_res.data:
                        fetched_desc = str(item_res.data[0].get("item_description", ""))
                        fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                        
                        st.session_state[f"w_idesc_{i}"] = fetched_desc
                        if fetched_stn in stn_status_opts:
                            st.session_state[f"w_stn_{i}"] = fetched_stn
                            
                        st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                    else:
                        st.toast("Item Code not found in database ⚠️", icon="⚠️")
                except Exception as e:
                    pass

            with mc4:
                current_desc_val = st.session_state.get(f"w_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"w_idesc_{i}")
                w_descs.append(i_desc)
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"w_iqty_{i}")
                w_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"w_mstat_{i}")
                w_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"w_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                w_dates.append(d_date)
            with mc8:
                default_stn = "Select"
                if code_val and 'item_res' in locals() and item_res.data:
                    default_stn = fetched_stn if fetched_stn in stn_status_opts else "Select"
                
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"w_stn_{i}")
                w_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"w_rem_{i}")
                w_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_m_add, col_m_rem, _ = st.columns([3, 3, 4])
        with col_m_add:
            if st.button("➕ Add Item", key="btn_add_wh_mat", use_container_width=True):
                st.session_state.wh_mat_count += 1
        with col_m_rem:
            if st.session_state.wh_mat_count > 1:
                if st.button("➖ Remove Item", key="btn_rem_wh_mat", use_container_width=True):
                    st.session_state.wh_mat_count -= 1
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            save_mat = st.button("💾 Save Material", type="primary", use_container_width=True)
            
        if save_mat:
            has_m_err = False
            
            if proj_id == "Select Project ID":
                st.error("⚠️ Project ID select karna compulsory hai!")
                has_m_err = True

            seen_codes = set()
            if not has_m_err:
                for idx, (b, ic) in enumerate(zip(w_boqs, w_item_codes)):
                    if not b:
                        st.error(f"⚠️ Item {idx+1}: BOQ Number dalna compulsory hai!")
                        has_m_err = True
                        break
                    
                    code_str = ic.strip()
                    if not code_str:
                        st.error(f"⚠️ Item {idx+1}: Item Code cannot be empty!")
                        has_m_err = True
                        break
                    
                    if code_str in seen_codes:
                        st.error(f"⚠️ Item {idx+1}: You entered duplicate Item Code '{code_str}' in this form!")
                        has_m_err = True
                        break
                    seen_codes.add(code_str)

            if not has_m_err:
                for ic in w_item_codes:
                    code_str = ic.strip()
                    try:
                        dup_check = supabase.table("warehouse_data").select("Item Code").eq("Project ID", proj_id).eq("Item Code", code_str).execute()
                        if dup_check.data and len(dup_check.data) > 0:
                            st.error(f"❌ This item '{code_str}' already exist against this project id '{proj_id}'.")
                            has_m_err = True
                            break
                    except Exception as db_err:
                        pass 
                        
            if not has_m_err:
                try:
                    for i in range(len(w_item_codes)):
                        insert_dict = {
                            "workspace": st.session_state.get('active_workspace', 'VISPL'),
                            "Project ID": proj_id,
                            "Site ID": site_id_val,
                            "Site Name": site_name_val,
                            "Cluster": cluster_val,
                            "Team": team_val,
                            "SRN Status": srn_status if srn_status != "Select" else "",
                            "Transaction Type": w_trans_types[i] if w_trans_types[i] != "Select" else "",
                            "BOQ Number": w_boqs[i],
                            "Item Code": w_item_codes[i].strip(),
                            "Item Description": w_descs[i],
                            "Indus Qty": w_qtys[i],
                            "Material Status": w_statuses[i] if w_statuses[i] != "Select" else "",
                            "Dispatch Date": w_dates[i],
                            "STN Status": w_stn_statuses[i] if w_stn_statuses[i] != "Select" else "",
                            "Remark": w_remarks[i]
                        }
                        supabase.table("warehouse_data").insert(insert_dict).execute()
                        
                    st.success("✅ Warehouse Material Successfully Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving Material: {e}")

# --- 3.6 EDIT WAREHOUSE MATERIAL DIALOG FUNCTION ---
@st.dialog("✏️ Edit Warehouse Material", width="large")
def edit_warehouse_material_dialog(row_data):
    st.caption("Update transaction items and asset movements")
    all_dd = get_all_dropdowns()
    
    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True, key="ed_w_pid")
        with c2:
            st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True, key="ed_w_sid")
        with c3:
            st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True, key="ed_w_sname")
        with c4:
            st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True, key="ed_w_clu")
        with c5:
            st.text_input("TEAM", value=row_data.get('Team', ''), disabled=True, key="ed_w_team")
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, index=get_idx(row_data.get('SRN Status'), srn_opts), key="ed_w_srn")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            t_type = st.selectbox("TRANSACTION TYPE", trans_types, index=get_idx(row_data.get('Transaction Type'), trans_types), key="ed_w_trans")
        with mc2:
            boq_no = st.text_input("BOQ NUMBER *", value=row_data.get('BOQ Number', ''), key="ed_w_boq")
        with mc3:
            i_code = st.text_input("ITEM CODE *", value=row_data.get('Item Code', ''), key="ed_w_icode")
        with mc4:
            i_desc = st.text_input("ITEM DESCRIPTION", value=row_data.get('Item Description', ''), key="ed_w_idesc")
        with mc5:
            try:
                indus_val = float(row_data.get('Indus Qty', 0))
            except:
                indus_val = 0.0
            i_qty = st.number_input("INDUS QTY", value=indus_val, key="ed_w_iqty")
            
        mc6, mc7, mc8, mc9 = st.columns(4)
        with mc6:
            m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, index=get_idx(row_data.get('Material Status'), mat_status_opts), key="ed_w_mstat")
        with mc7:
            val_date = str(row_data.get('Dispatch Date', ''))
            d_date = st.text_input("DISPATCH DATE (DD/MM/YYYY)", value=val_date if val_date != 'nan' else "", key="ed_w_ddate")
        with mc8:
            stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=get_idx(row_data.get('STN Status'), stn_status_opts), key="ed_w_stn")
        with mc9:
            val_rem = str(row_data.get('Remark', ''))
            rem = st.text_input("REMARKS", value=val_rem if val_rem != 'nan' else "", key="ed_w_rem")

        st.markdown("<br>", unsafe_allow_html=True)
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            update_mat = st.button("💾 Update Material", type="primary", use_container_width=True)
            
        if update_mat:
            if not boq_no:
                st.error("⚠️ BOQ Number dalna compulsory hai!")
            elif not i_code.strip():
                st.error("⚠️ Item Code cannot be empty!")
            else:
                try:
                    update_dict = {
                        "SRN Status": srn_status if srn_status != "Select" else "",
                        "Transaction Type": t_type if t_type != "Select" else "",
                        "BOQ Number": boq_no,
                        "Item Code": i_code.strip(),
                        "Item Description": i_desc,
                        "Indus Qty": i_qty,
                        "Material Status": m_stat if m_stat != "Select" else "",
                        "Dispatch Date": d_date,
                        "STN Status": stn_stat if stn_stat != "Select" else "",
                        "Remark": rem
                    }
                    supabase.table("warehouse_data").update(update_dict).eq("id", row_data['id']).execute()
                    st.success("✅ Warehouse Material Successfully Updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Updating Material: {e}")

# --- 3.7 NEW: VIEW RECORD DIALOG FUNCTION (READ-ONLY) ---
@st.dialog("👁️ View Warehouse Material", width="large")
def view_record_dialog(row_data):
    st.caption("Read-only preview of transaction items and asset movements")

    st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True)
    with c2: st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True)
    with c3: st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True)
    with c4: st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True)
    with c5: st.text_input("TEAM", value=row_data.get('Team', ''), disabled=True)
    with c6: st.text_input("SRN STATUS", value=row_data.get('SRN Status', ''), disabled=True)

    st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1: st.text_input("TRANSACTION TYPE", value=row_data.get('Transaction Type', ''), disabled=True)
    with mc2: st.text_input("BOQ NUMBER", value=row_data.get('BOQ Number', ''), disabled=True)
    with mc3: st.text_input("ITEM CODE", value=row_data.get('Item Code', ''), disabled=True)
    with mc4: st.text_input("ITEM DESCRIPTION", value=row_data.get('Item Description', ''), disabled=True)
    with mc5: st.text_input("INDUS QTY", value=str(row_data.get('Indus Qty', '')), disabled=True)

    mc6, mc7, mc8, mc9 = st.columns(4)
    with mc6: st.text_input("MATERIAL STATUS", value=row_data.get('Material Status', ''), disabled=True)
    with mc7: st.text_input("DISPATCH DATE", value=row_data.get('Dispatch Date', ''), disabled=True)
    with mc8: st.text_input("STN STATUS", value=row_data.get('STN Status', ''), disabled=True)
    with mc9: st.text_input("REMARKS", value=row_data.get('Remark', ''), disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True):
        st.rerun()

# --- 3.9 EXPORT DIALOG FUNCTION ---
@st.dialog("📥 Export Data", width="large")
def export_dialog(df_export):
    st.caption("Download your live database records as an Excel file.")
    
    export_df = df_export.copy()
    if "🎯 Select" in export_df.columns:
        export_df = export_df.drop(columns=["🎯 Select"])
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Warehouse Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="Warehouse_Data_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_ref, col_add, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>📦 Warehouse Material Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun() 
with col_add:
    if st.button("➕ Add New Material", use_container_width=True):
        st.session_state.wh_mat_count = 1 
        add_warehouse_material_dialog() 
with col_export:
    if st.button("📥 Download", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH & PREPARE DATA FROM WAREHOUSE ---
table_name = "warehouse_data"
try:
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    response = supabase.table(table_name).select("*").eq("workspace", active_ws).execute()
    data = response.data
except Exception:
    data = []

columns_list = [
    "id", "Project ID", "Site ID", "Site Name", "Cluster", "Team", 
    "SRN Status", "Transaction Type", "BOQ Number", "Item Code", 
    "Item Description", "Indus Qty", "Material Status", "Dispatch Date", 
    "STN Status", "Remark"
]

if data:
    df_raw = pd.DataFrame(data)
    df = pd.DataFrame()
    for col in columns_list:
        matched = False
        for raw_col in df_raw.columns:
            if str(raw_col).strip().lower().replace("_", " ") == str(col).strip().lower().replace("_", " "):
                df[col] = df_raw[raw_col]
                matched = True
                break
        if not matched:
            df[col] = ""
else:
    df = pd.DataFrame(columns=columns_list)

if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)
else:
    df["🎯 Select"] = False

# --- EXPORT LOGIC TRIGGER AFTER DF LOAD ---
if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 5.5 LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Live Warehouse Records")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- 6. PAGINATION LOGIC (10 lines per page) ---
if 'wh_current_page' not in st.session_state:
    st.session_state.wh_current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.wh_current_page > total_pages:
    st.session_state.wh_current_page = total_pages
elif st.session_state.wh_current_page < 1:
    st.session_state.wh_current_page = 1

start_idx = (st.session_state.wh_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 7. NEW: PROPER BORDERED TABLE WITH ALL COLUMNS & FIXED BUTTONS ---
df_page = df.iloc[start_idx:end_idx].copy()

def status_badge(val):
    v = str(val).strip()
    if not v or v.lower() in ("nan", "none", "-"):
        return "<span class='tbl-cell'>-</span>"
    vl = v.lower()
    if "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<span class='status-badge {cls}'>{v}</span>"

# Exact 19 columns ratios: Total 19 cols (1 Sr No + 3 Buttons + 15 Data)
COL_RATIOS = [
    0.3, 0.35, 0.35, 0.35,       # 0-3 (Sr No, Actions: View, Edit, Delete)
    1.2, 1.0, 1.5, 1.0, 1.0,     # 4-8
    1.0, 1.2, 1.0, 1.0, 1.5,     # 9-13
    0.8, 1.2, 1.2, 1.0, 1.5      # 14-18
]

COL_LABELS = [
    "#", "👁️", "✏️", "🗑️", 
    "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "TEAM", 
    "SRN STATUS", "TRANSACTION TYPE", "BOQ NUMBER", "ITEM CODE", 
    "ITEM DESCRIPTION", "INDUS QTY", "MATERIAL STATUS", "DISPATCH DATE", 
    "STN STATUS", "REMARK"
]

with st.container(key="wh_table_wrap", height=560):
    if df_page.empty:
        st.info("No records found.")
    else:
        # --- HEADER ROW ---
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)

        # --- DATA ROWS ---
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1

            rcols = st.columns(COL_RATIOS)

            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)

            with rcols[1]:
                with st.container(key=f"vbtn_{rid}"):
                    if st.button("👁️", key=f"view_{rid}", help="View", use_container_width=True):
                        view_record_dialog(row_dict)
            with rcols[2]:
                with st.container(key=f"ebtn_{rid}"):
                    if st.button("✏️", key=f"edit_{rid}", help="Edit", use_container_width=True):
                        edit_warehouse_material_dialog(row_dict)
            with rcols[3]:
                with st.container(key=f"dbtn_{rid}"):
                    if st.button("🗑️", key=f"del_{rid}", help="Delete", use_container_width=True):
                        st.session_state[f"confirm_del_{rid}"] = True

            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[7].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            rcols[8].markdown(f"<div class='tbl-cell'>{row_dict.get('Team','') or '-'}</div>", unsafe_allow_html=True)
            rcols[9].markdown(status_badge(row_dict.get('SRN Status', '')), unsafe_allow_html=True)
            rcols[10].markdown(f"<div class='tbl-cell'>{row_dict.get('Transaction Type','') or '-'}</div>", unsafe_allow_html=True)
            rcols[11].markdown(f"<div class='tbl-cell'>{row_dict.get('BOQ Number','') or '-'}</div>", unsafe_allow_html=True)
            rcols[12].markdown(f"<div class='tbl-cell'>{row_dict.get('Item Code','') or '-'}</div>", unsafe_allow_html=True)
            rcols[13].markdown(f"<div class='tbl-cell'>{row_dict.get('Item Description','') or '-'}</div>", unsafe_allow_html=True)
            rcols[14].markdown(f"<div class='tbl-cell'>{row_dict.get('Indus Qty','') or '-'}</div>", unsafe_allow_html=True)
            rcols[15].markdown(status_badge(row_dict.get('Material Status', '')), unsafe_allow_html=True)
            rcols[16].markdown(f"<div class='tbl-cell'>{row_dict.get('Dispatch Date','') or '-'}</div>", unsafe_allow_html=True)
            rcols[17].markdown(status_badge(row_dict.get('STN Status', '')), unsafe_allow_html=True)
            rcols[18].markdown(f"<div class='tbl-cell'>{row_dict.get('Remark','') or '-'}</div>", unsafe_allow_html=True)

            # Inline delete confirmation
            if st.session_state.get(f"confirm_del_{rid}"):
                wc1, wc2, wc3 = st.columns([6, 1, 1])
                with wc1:
                    st.warning(f"Delete record '{row_dict.get('Item Code','')}' / '{row_dict.get('Project ID','')}'? This cannot be undone.")
                with wc2:
                    if st.button("✅ Confirm", key=f"confirm_yes_{rid}", use_container_width=True):
                        try:
                            supabase.table(table_name).delete().eq("id", rid).execute()
                            st.session_state[f"confirm_del_{rid}"] = False
                            st.success("✅ Record Successfully Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error Deleting Record: {e}")
                with wc3:
                    if st.button("❌ Cancel", key=f"confirm_no_{rid}", use_container_width=True):
                        st.session_state[f"confirm_del_{rid}"] = False
                        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.wh_current_page == 1)):
        st.session_state.wh_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.wh_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.wh_current_page == total_pages)):
        st.session_state.wh_current_page += 1
        st.rerun()
