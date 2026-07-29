import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Site Data Hub", page_icon="🏗️", layout="wide")

# --- INITIALIZE PO COUNT SESSION STATE ---
if 'po_count' not in st.session_state:
    st.session_state.po_count = 1

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
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 3.1 HELPER FOR DYNAMIC DROPDOWNS ---
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

# --- 3.5 ADD RECORD DIALOG FUNCTION (POP-UP) ---
@st.dialog("📄 Add Site Data", width="large")
def add_record_dialog():
    st.caption("Configure comprehensive site metrics and procurement status")
    
    all_dd = get_all_dropdowns() 
    
    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
        
        # Row 1
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dept = st.selectbox("DEPARTMENT", get_opts("Department", all_dd))
        with c2:
            operator = st.selectbox("OPERATOR", get_opts("Operator", all_dd))
        with c3:
            proj_name = st.selectbox("PROJECT NAME", get_opts("Project Name", all_dd))
        with c4:
            proj_id = st.text_input("PROJECT ID * (REQUIRED)", placeholder="Project ID")
            
        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            site_id = st.text_input("Site ID * (REQUIRED)", placeholder="Enter Site ID")
            
        site_name_val = ""
        cluster_val = ""
        area_val = "N/A"
        km_val = "N/A"
        lat_val = "N/A"
        long_val = "N/A"
        tech_val = "N/A"
        fse_val = "N/A"
        aom_val = "N/A"
        
        if site_id:
            try:
                master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id.strip()).execute()
                if master_res.data:
                    site_name_val = master_res.data[0].get("Site Name", "")
                    cluster_val = master_res.data[0].get("Cluster", "")
                    area_val = master_res.data[0].get("Area", "N/A")
                    km_val = master_res.data[0].get("KM", "N/A")
                    lat_val = master_res.data[0].get("Lat", "N/A")
                    long_val = master_res.data[0].get("Long", "N/A")
                    tech_val = master_res.data[0].get("Technician Detail", "N/A")
                    fse_val = master_res.data[0].get("FSE Detail", "N/A")
                    aom_val = master_res.data[0].get("AOM Detail", "N/A")
                    st.toast("Data Auto-Fetched Successfully! ✅", icon="✅")
                else:
                    st.toast("Site ID not found in Excalation Matrix table ⚠️", icon="⚠️")
            except Exception as e:
                st.toast(f"Table Error: {e} ❌", icon="❌")

        with c6:
            site_name = st.text_input("SITE NAME", value=site_name_val, placeholder="Auto Fetch")
        with c7:
            cluster = st.text_input("CLUSTER", value=cluster_val, placeholder="Auto Fetch")
        with c8:
            site_status = st.selectbox("SITE STATUS", get_opts("Site Status", all_dd))

        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 8px; margin-top: 5px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-around; margin-bottom: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🏢 Area: <span style="color: #3b82f6;">{area_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">📍 KM: <span style="color: #3b82f6;">{km_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🌍 LAT LONG: <span style="color: #3b82f6; white-space: pre;">{lat_val}  {long_val}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">🧑‍🔧 Technician: <span style="color: #3b82f6;">{tech_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👨‍💼 FSE: <span style="color: #3b82f6;">{fse_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👑 AOM: <span style="color: #3b82f6;">{aom_val}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
            
        st.markdown('<div class="modal-section-title">📦 MATERIAL, BILLING & RFAI DETAILS</div>', unsafe_allow_html=True)
        
        work_desc = st.text_input("WORK DESCRIPTION", placeholder="Enter detailed work description")
        
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            product = st.selectbox("PRODUCT", get_opts("Product", all_dd))
        with c10:
            rfai_status = st.selectbox("RFAI STATUS", get_opts("RFAI Status", all_dd))
        with c11:
            wh_material = st.selectbox("WH MATERIAL", get_opts("WH Material", all_dd))
        with c12:
            team_name = st.selectbox("TEAM NAME", get_opts("Team Name", all_dd))
            
        c13, c14, c15 = st.columns(3)
        with c13:
            ex_opts = get_opts("Extra Approval", all_dd)
            def_extra = ex_opts.index("Not Available") if "Not Available" in ex_opts else 0
            extra_approval = st.selectbox("EXTRA APPROVAL", ex_opts, index=def_extra)
        with c14:
            tb_opts = get_opts("Team Billing Status", all_dd)
            def_team = tb_opts.index("Pending") if "Pending" in tb_opts else 0
            team_billing = st.selectbox("TEAM BILLING STATUS", tb_opts, index=def_team)
        with c15:
            vb_opts = get_opts("Vision Billing Status", all_dd)
            def_vis = vb_opts.index("Pending") if "Pending" in vb_opts else 0
            vision_billing = st.selectbox("VISION BILLING STATUS", vb_opts, index=def_vis)

        st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        po_nos, po_dates, po_statuses, wcc_nums, wcc_statuses = [], [], [], [], []
        
        for i in range(st.session_state.po_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
            
            c17, c18, c19, c20, c21 = st.columns(5)
            with c17:
                p_n = st.text_input("PO NO.", placeholder="11 digits", key=f"po_no_{i}")
                po_nos.append(p_n)
            with c18:
                p_d = st.date_input("PO DATE", value=None, key=f"po_date_{i}")
                po_dates.append(p_d)
            with c19:
                p_s = st.selectbox("PO STATUS", get_opts("PO Status", all_dd), key=f"po_status_{i}")
                po_statuses.append(p_s)
            with c20:
                w_n = st.text_input("WCC NUMBER", placeholder="11 digits", key=f"wcc_num_{i}")
                wcc_nums.append(w_n)
            with c21:
                w_s = st.selectbox("WCC STATUS", get_opts("WCC Status", all_dd), key=f"wcc_status_{i}")
                wcc_statuses.append(w_s)
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_add, _ = st.columns([3, 7])
        with col_btn_add:
            if st.button("➕ Add Additional PO", use_container_width=True):
                st.session_state.po_count += 1
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.button("💾 Save All Data", type="primary", use_container_width=True)
            
        if submitted:
            has_error = False
            if not proj_id or not site_id:
                st.error("⚠️ Project ID aur Site ID dalna compulsory hai!")
                has_error = True
            for p in po_nos:
                if p and (not p.isdigit() or len(p) != 11):
                    st.error(f"⚠️ PO NO. '{p}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            for w in wcc_nums:
                if w and (not w.isdigit() or len(w) != 11):
                    st.error(f"⚠️ WCC NUMBER '{w}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            
            if not has_error:
                try:
                    dup_check = supabase.table("site_data").select("Project ID").eq("Project ID", proj_id).execute()
                    if len(dup_check.data) > 0:
                        st.error("❌ Project ID already exist")
                        has_error = True
                except Exception:
                    pass
                    
            if not has_error:
                insert_data = {
                    "Department": dept if dept != "Select" else "",
                    "Operator": operator if operator != "Select" else "",
                    "Project Name": proj_name if proj_name != "Select" else "",
                    "Project ID": proj_id,
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Cluster": cluster,
                    "Site Status": site_status if site_status != "Select" else "",
                    "Work Description": work_desc,
                    "Product": product if product != "Select" else "",
                    
                    "PO No.": ", ".join([p for p in po_nos if p]),
                    "PO Date": ", ".join([str(d) for d in po_dates if d]),
                    "PO Status": ", ".join([ps if ps != "Select" else "" for ps in po_statuses]),
                    
                    "RFAI Status": rfai_status if rfai_status != "Select" else "",
                    "WH Material": wh_material if wh_material != "Select" else "",
                    "Team Name": team_name if team_name != "Select" else "",
                    "Team Billing Status": team_billing if team_billing != "Select" else "",
                    "Extra Approval": extra_approval if extra_approval != "Select" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Select" else "",
                    
                    "WCC Number": ", ".join([w for w in wcc_nums if w]),
                    "WCC Status": ", ".join([ws if ws != "Select" else "" for ws in wcc_statuses])
                }
                
                try:
                    supabase.table("site_data").insert(insert_data).execute()
                    st.success("✅ Record Successfully Added!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"❌ Error Saving Data: {e}")

# --- 3.6 EDIT RECORD DIALOG FUNCTION ---
@st.dialog("✏️ Edit Site Data", width="large")
def edit_record_dialog(row_data):
    st.caption("Update comprehensive site metrics and procurement status")
    all_dd = get_all_dropdowns() 
    
    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dept_opts = get_opts("Department", all_dd)
            dept = st.selectbox("DEPARTMENT", dept_opts, index=get_idx(row_data.get('Department'), dept_opts), key="ed_dept")
        with c2:
            op_opts = get_opts("Operator", all_dd)
            operator = st.selectbox("OPERATOR", op_opts, index=get_idx(row_data.get('Operator'), op_opts), key="ed_op")
        with c3:
            pn_opts = get_opts("Project Name", all_dd)
            proj_name = st.selectbox("PROJECT NAME", pn_opts, index=get_idx(row_data.get('Project Name'), pn_opts), key="ed_pn")
        with c4:
            proj_id = st.text_input("PROJECT ID * (REQUIRED)", value=row_data.get('Project ID', ''), disabled=True, key="ed_pid")
            
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            site_id = st.text_input("Site ID * (REQUIRED)", value=row_data.get('Site ID', ''), key="ed_sid")
            
        area_val, km_val, lat_val, long_val, tech_val, fse_val, aom_val = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
        if site_id:
            try:
                master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id.strip()).execute()
                if master_res.data:
                    area_val = master_res.data[0].get("Area", "N/A")
                    km_val = master_res.data[0].get("KM", "N/A")
                    lat_val = master_res.data[0].get("Lat", "N/A")
                    long_val = master_res.data[0].get("Long", "N/A")
                    tech_val = master_res.data[0].get("Technician Detail", "N/A")
                    fse_val = master_res.data[0].get("FSE Detail", "N/A")
                    aom_val = master_res.data[0].get("AOM Detail", "N/A")
            except:
                pass

        with c6:
            site_name = st.text_input("SITE NAME", value=row_data.get('Site Name', ''), key="ed_sname")
        with c7:
            cluster = st.text_input("CLUSTER", value=row_data.get('Cluster', ''), key="ed_clu")
        with c8:
            ss_opts = get_opts("Site Status", all_dd)
            site_status = st.selectbox("SITE STATUS", ss_opts, index=get_idx(row_data.get('Site Status'), ss_opts), key="ed_ss")

        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 8px; margin-top: 5px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-around; margin-bottom: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🏢 Area: <span style="color: #3b82f6;">{area_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">📍 KM: <span style="color: #3b82f6;">{km_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🌍 LAT LONG: <span style="color: #3b82f6; white-space: pre;">{lat_val}  {long_val}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">🧑‍🔧 Technician: <span style="color: #3b82f6;">{tech_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👨‍💼 FSE: <span style="color: #3b82f6;">{fse_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👑 AOM: <span style="color: #3b82f6;">{aom_val}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
            
        st.markdown('<div class="modal-section-title">📦 MATERIAL, BILLING & RFAI DETAILS</div>', unsafe_allow_html=True)
        
        work_desc = st.text_input("WORK DESCRIPTION", value=row_data.get('Work Description', ''), key="ed_wd")
        
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            prod_opts = get_opts("Product", all_dd)
            product = st.selectbox("PRODUCT", prod_opts, index=get_idx(row_data.get('Product'), prod_opts), key="ed_prod")
        with c10:
            rfai_opts = get_opts("RFAI Status", all_dd)
            rfai_status = st.selectbox("RFAI STATUS", rfai_opts, index=get_idx(row_data.get('RFAI Status'), rfai_opts), key="ed_rfai")
        with c11:
            wh_opts = get_opts("WH Material", all_dd)
            wh_material = st.selectbox("WH MATERIAL", wh_opts, index=get_idx(row_data.get('WH Material'), wh_opts), key="ed_wh")
        with c12:
            team_opts = get_opts("Team Name", all_dd)
            team_name = st.selectbox("TEAM NAME", team_opts, index=get_idx(row_data.get('Team Name'), team_opts), key="ed_team")
            
        c13, c14, c15 = st.columns(3)
        with c13:
            ex_opts = get_opts("Extra Approval", all_dd)
            extra_approval = st.selectbox("EXTRA APPROVAL", ex_opts, index=get_idx(row_data.get('Extra Approval'), ex_opts), key="ed_ex")
        with c14:
            tb_opts = get_opts("Team Billing Status", all_dd)
            team_billing = st.selectbox("TEAM BILLING STATUS", tb_opts, index=get_idx(row_data.get('Team Billing Status'), tb_opts), key="ed_tb")
        with c15:
            vb_opts = get_opts("Vision Billing Status", all_dd)
            vision_billing = st.selectbox("VISION BILLING STATUS", vb_opts, index=get_idx(row_data.get('Vision Billing Status'), vb_opts), key="ed_vb")

        st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        po_no_list = [x.strip() for x in str(row_data.get("PO No.", "")).split(",") if x.strip()]
        po_date_list = [x.strip() for x in str(row_data.get("PO Date", "")).split(",") if x.strip()]
        po_status_list = [x.strip() for x in str(row_data.get("PO Status", "")).split(",") if x.strip()]
        wcc_num_list = [x.strip() for x in str(row_data.get("WCC Number", "")).split(",") if x.strip()]
        wcc_status_list = [x.strip() for x in str(row_data.get("WCC Status", "")).split(",") if x.strip()]
        
        max_boxes = max(1, len(po_no_list), len(wcc_num_list))
        if 'edit_po_count' not in st.session_state:
            st.session_state.edit_po_count = max_boxes
            
        po_nos, po_dates, po_statuses, wcc_nums, wcc_statuses = [], [], [], [], []
        
        for i in range(st.session_state.edit_po_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
            
            c17, c18, c19, c20, c21 = st.columns(5)
            with c17:
                val = po_no_list[i] if i < len(po_no_list) else ""
                p_n = st.text_input("PO NO.", value=val, key=f"e_po_no_{i}")
                po_nos.append(p_n)
            with c18:
                val = po_date_list[i] if i < len(po_date_list) else None
                p_d = st.text_input("PO DATE (YYYY-MM-DD)", value=val if val else "", key=f"e_po_date_{i}")
                po_dates.append(p_d)
            with c19:
                val = po_status_list[i] if i < len(po_status_list) else "Select"
                ps_opts = get_opts("PO Status", all_dd)
                p_s = st.selectbox("PO STATUS", ps_opts, index=get_idx(val, ps_opts), key=f"e_po_status_{i}")
                po_statuses.append(p_s)
            with c20:
                val = wcc_num_list[i] if i < len(wcc_num_list) else ""
                w_n = st.text_input("WCC NUMBER", value=val, key=f"e_wcc_num_{i}")
                wcc_nums.append(w_n)
            with c21:
                val = wcc_status_list[i] if i < len(wcc_status_list) else "Select"
                ws_opts = get_opts("WCC Status", all_dd)
                w_s = st.selectbox("WCC STATUS", ws_opts, index=get_idx(val, ws_opts), key=f"e_wcc_status_{i}")
                wcc_statuses.append(w_s)
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_add, _ = st.columns([3, 7])
        with col_btn_add:
            if st.button("➕ Add Additional PO", key="e_add_po", use_container_width=True):
                st.session_state.edit_po_count += 1
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.button("💾 Update Data", type="primary", use_container_width=True)
            
        if submitted:
            has_error = False
            if not site_id:
                st.error("⚠️ Site ID dalna compulsory hai!")
                has_error = True
            for p in po_nos:
                if p and (not p.isdigit() or len(p) != 11):
                    st.error(f"⚠️ PO NO. '{p}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            for w in wcc_nums:
                if w and (not w.isdigit() or len(w) != 11):
                    st.error(f"⚠️ WCC NUMBER '{w}' strict 11 digit ka number hona chahiye!")
                    has_error = True
                    
            if not has_error:
                update_data = {
                    "Department": dept if dept != "Select" else "",
                    "Operator": operator if operator != "Select" else "",
                    "Project Name": proj_name if proj_name != "Select" else "",
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Cluster": cluster,
                    "Site Status": site_status if site_status != "Select" else "",
                    "Work Description": work_desc,
                    "Product": product if product != "Select" else "",
                    
                    "PO No.": ", ".join([p for p in po_nos if p]),
                    "PO Date": ", ".join([str(d) for d in po_dates if d]),
                    "PO Status": ", ".join([ps if ps != "Select" else "" for ps in po_statuses]),
                    
                    "RFAI Status": rfai_status if rfai_status != "Select" else "",
                    "WH Material": wh_material if wh_material != "Select" else "",
                    "Team Name": team_name if team_name != "Select" else "",
                    "Team Billing Status": team_billing if team_billing != "Select" else "",
                    "Extra Approval": extra_approval if extra_approval != "Select" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Select" else "",
                    
                    "WCC Number": ", ".join([w for w in wcc_nums if w]),
                    "WCC Status": ", ".join([ws if ws != "Select" else "" for ws in wcc_statuses])
                }
                
                try:
                    supabase.table("site_data").update(update_data).eq("id", row_data['id']).execute()
                    st.success("✅ Record Successfully Updated!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"❌ Error Updating Data: {e}")

# --- 3.7 BULK UPLOAD DIALOG FUNCTION ---
@st.dialog("📤 Bulk Upload Data", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel (.xlsx) or .tsv file to bulk insert records matching table columns.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"])
    
    if uploaded_file:
        if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file, sep='\t')
                    
                res = supabase.table("site_data").select("Project ID").execute()
                existing_pids = [str(row["Project ID"]) for row in res.data] if res.data else []
                
                added_count = 0
                skipped_pids = []
                
                for index, row in df_upload.iterrows():
                    pid = str(row.get("Project ID", ""))
                    if not pid or pid == "nan":
                        continue
                        
                    if pid in existing_pids:
                        skipped_pids.append(pid)
                    else:
                        insert_dict = {}
                        for col in df_upload.columns:
                            val = row[col]
                            if pd.notna(val):
                                insert_dict[col] = str(val)
                        
                        try:
                            supabase.table("site_data").insert(insert_dict).execute()
                            added_count += 1
                            existing_pids.append(pid) 
                        except Exception as db_e:
                            st.error(f"Error saving Project ID {pid}: {db_e}")
                            
                st.success(f"✅ Upload Complete! {added_count} New Sites Added.")
                if skipped_pids:
                    st.warning(f"⚠️ Skipped {len(skipped_pids)} duplicate sites.")
                    st.info(f"Skipped Project IDs: {', '.join(skipped_pids)}")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- 3.8 EXPORT DIALOG FUNCTION ---
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
        export_df.to_excel(writer, index=False, sheet_name='Site Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="Site_Data_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_ref, col_add, col_upload, col_export = st.columns([3.5, 1, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🏗️ Site Data Master</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun() 
with col_add:
    if st.button("➕ Add Record", use_container_width=True):
        st.session_state.action = "add"
        st.session_state.po_count = 1 
        add_record_dialog() 
with col_upload:
    if st.button("📤 Bulk Upload", use_container_width=True):
        bulk_upload_dialog() 
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH & PREPARE DATA ---
table_name = "site_data"
try:
    response = supabase.table(table_name).select("*").execute()
    data = response.data
except Exception:
    data = []

columns_list = [
    "id", "Department", "Operator", "Project Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Site Status", "Work Description", "Product", "PO No.", 
    "PO Date", "PO Status", "RFAI Status", "WH Material", "Team Name", 
    "Team Billing Status", "Extra Approval", "Vision Billing Status", 
    "WCC Number", "WCC Status"
]

if data:
    df = pd.DataFrame(data)
    for col in columns_list:
        if col not in df.columns:
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
    st.markdown("##### 🗄️ Live Database Records")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- 6. PAGINATION LOGIC (10 lines per page) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages
elif st.session_state.current_page < 1:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 7. ORIGINAL LAVISH DATA TABLE (st.data_editor) ---
df_page = df.iloc[start_idx:end_idx].copy()

edited_df = st.data_editor(
    df_page, 
    use_container_width=True, 
    hide_index=True,
    height=400, 
    column_config={
        "id": None, 
        "🎯 Select": st.column_config.CheckboxColumn("Select", default=False)
    }
)

# --- 7.5 CHIPKE HUE CHOTE EDIT (GREEN) & DELETE (RED) BUTTONS BELOW TABLE ---
selected_rows = edited_df[edited_df["🎯 Select"] == True]
if not selected_rows.empty:
    row_to_edit = selected_rows.iloc[0].to_dict()
    
    st.markdown("""
        <style>
        div.row-widget.stButton > button {
            padding: 2px 10px !important;
            font-size: 0.8rem !important;
            min-height: 28px !important;
            border-radius: 4px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    b_col1, b_col2, _ = st.columns([0.8, 0.8, 8.4])
    with b_col1:
        if st.button("✏️ Edit", key="quick_edit", use_container_width=True, type="primary"):
            if 'edit_po_count' in st.session_state:
                del st.session_state['edit_po_count']
            edit_record_dialog(row_to_edit)
    with b_col2:
        if st.button("🗑️ Delete", key="quick_del", use_container_width=True):
            try:
                supabase.table(table_name).delete().eq("id", row_to_edit["id"]).execute()
                st.success("✅ Deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS ---
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
