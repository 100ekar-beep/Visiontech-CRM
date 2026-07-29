import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Site Data Hub", page_icon="🏗️", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'po_count' not in st.session_state:
    st.session_state.po_count = 1

if 'mat_count' not in st.session_state:
    st.session_state.mat_count = 1

if 'add_mat_count' not in st.session_state:
    st.session_state.add_mat_count = 1

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

# --- HELPER: FETCH ITEM MASTER DETAILS FOR AUTO-FILL IN MATERIAL MODAL ---
def get_item_master_details():
    mapping = {}
    table_names_to_try = ["Item Code", "item_code"]
    
    for t_name in table_names_to_try:
        try:
            res = supabase.table(t_name).select("*").execute()
            if res.data:
                for item in res.data:
                    code = str(item.get("item_code", "")).strip()
                    if code:
                        mapping[code] = {
                            "description": str(item.get("item_description", "") or ""),
                            "stn_status": str(item.get("stn_status", "Required") or "Required"),
                            "material_of": str(item.get("material_of", "Indus") or "Indus"),
                            "rate": item.get("rate")
                        }
                return mapping 
        except Exception as e:
            continue
            
    return mapping

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
                    st.toast("Site Data Auto-Fetched Successfully! ✅", icon="✅")
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
                raw_p_d = st.date_input("PO DATE", value=None, key=f"po_date_{i}")
                p_d = raw_p_d.strftime("%d/%m/%Y") if raw_p_d else ""
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
        
        # --- FIXED ADD/REMOVE PO BUTTONS ---
        col_btn_add, col_btn_rem, _ = st.columns([3, 3, 4])
        with col_btn_add:
            if st.button("➕ Add Additional PO", use_container_width=True):
                st.session_state.po_count += 1
        with col_btn_rem:
            if st.session_state.po_count > 1:
                if st.button("➖ Remove PO", use_container_width=True):
                    st.session_state.po_count -= 1
            
        # -------------------------------------------------------------
        # NEW SECTION: WAREHOUSE MATERIAL TRACKING IN ADD RECORD
        # -------------------------------------------------------------
        st.markdown('<div class="modal-section-title">📦 WAREHOUSE MATERIAL TRACKING (OPTIONAL)</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        a_mat_trans_types, a_mat_boqs, a_mat_item_codes, a_mat_descs, a_mat_qtys = [], [], [], [], []
        a_mat_statuses, a_mat_dates, a_mat_stn_statuses, a_mat_remarks = [], [], [], []
        
        for i in range(st.session_state.add_mat_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"a_trans_{i}")
                a_mat_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER", placeholder="BOQ No", key=f"a_boq_{i}")
                a_mat_boqs.append(boq_no)
            with mc3:
                i_code = st.text_input("ITEM CODE", placeholder="Type & Press Enter", key=f"a_icode_{i}")
                a_mat_item_codes.append(i_code)

            code_val = i_code.strip()
            if code_val:
                try:
                    item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                    if not item_res.data:
                        item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                        
                    if item_res.data:
                        fetched_desc = str(item_res.data[0].get("item_description", ""))
                        fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                        
                        st.session_state[f"a_idesc_{i}"] = fetched_desc
                        if fetched_stn in stn_status_opts:
                            st.session_state[f"a_stn_{i}"] = fetched_stn
                            
                        st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                    else:
                        st.toast("Item Code not found in database ⚠️", icon="⚠️")
                except Exception as e:
                    st.toast(f"Table Error: {e} ❌", icon="❌")

            with mc4:
                current_desc_val = st.session_state.get(f"a_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"a_idesc_{i}")
                a_mat_descs.append(i_desc)
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"a_iqty_{i}")
                a_mat_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"a_mstat_{i}")
                a_mat_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"a_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                a_mat_dates.append(d_date)
            with mc8:
                default_stn = "Select"
                if code_val and 'item_res' in locals() and item_res.data:
                    default_stn = fetched_stn if fetched_stn in stn_status_opts else "Select"
                
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"a_stn_{i}")
                a_mat_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"a_rem_{i}")
                a_mat_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE MATERIAL BUTTONS ---
        col_a_add, col_a_rem, _ = st.columns([3, 3, 4])
        with col_a_add:
            if st.button("➕ Add Material Item", key="btn_a_add_mat", use_container_width=True):
                st.session_state.add_mat_count += 1
        with col_a_rem:
            if st.session_state.add_mat_count > 1:
                if st.button("➖ Remove Material", key="btn_a_rem_mat", use_container_width=True):
                    st.session_state.add_mat_count -= 1

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- SUBMIT LOGIC ---
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
                val = po_date_list[i] if i < len(po_date_list) else ""
                p_d = st.text_input("PO DATE (DD/MM/YYYY)", value=val if val else "", key=f"e_po_date_{i}")
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
        
        # --- FIXED ADD/REMOVE PO BUTTONS ---
        col_btn_add, col_btn_rem, _ = st.columns([3, 3, 4])
        with col_btn_add:
            if st.button("➕ Add Additional PO", key="e_add_po", use_container_width=True):
                st.session_state.edit_po_count += 1
        with col_btn_rem:
            if st.session_state.edit_po_count > 1:
                if st.button("➖ Remove PO", key="e_rem_po", use_container_width=True):
                    st.session_state.edit_po_count -= 1
            
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

# --- 3.7 WAREHOUSE MATERIAL POP-UP DIALOG FUNCTION ---
@st.dialog("📦 Warehouse Material Tracking", width="large")
def material_movement_dialog(row_data):
    st.caption("Manage transaction items and asset movements for selected site")
    all_dd = get_all_dropdowns()
    
    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True, key="m_pid")
        with c2:
            st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True, key="m_sid")
        with c3:
            st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True, key="m_sname")
        with c4:
            st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True, key="m_clu")
        with c5:
            st.text_input("TEAM", value=row_data.get('Team Name', ''), disabled=True, key="m_team")
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, key="m_srn_status")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        mat_trans_types, mat_boqs, mat_item_codes, mat_descs, mat_qtys = [], [], [], [], []
        mat_statuses, mat_dates, mat_stn_statuses, mat_remarks = [], [], [], []
        
        for i in range(st.session_state.mat_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"m_trans_{i}")
                mat_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER *", placeholder="BOQ No", key=f"m_boq_{i}")
                mat_boqs.append(boq_no)
            
            with mc3:
                i_code = st.text_input("ITEM CODE *", placeholder="Type & Press Enter", key=f"m_icode_{i}")
                mat_item_codes.append(i_code)

            code_val = i_code.strip()
            if code_val:
                try:
                    item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                    if not item_res.data:
                        item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                        
                    if item_res.data:
                        fetched_desc = str(item_res.data[0].get("item_description", ""))
                        fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                        
                        st.session_state[f"m_idesc_{i}"] = fetched_desc
                        if fetched_stn in stn_status_opts:
                            st.session_state[f"m_stn_{i}"] = fetched_stn
                            
                        st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                    else:
                        st.toast("Item Code not found in database ⚠️", icon="⚠️")
                except Exception as e:
                    st.toast(f"Table Error: {e} ❌", icon="❌")

            with mc4:
                current_desc_val = st.session_state.get(f"m_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"m_idesc_{i}")
                mat_descs.append(i_desc)
                
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"m_iqty_{i}")
                mat_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"m_mstat_{i}")
                mat_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"m_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                mat_dates.append(d_date)
            with mc8:
                default_stn = "Select"
                if code_val and 'item_res' in locals() and item_res.data:
                    default_stn = fetched_stn if fetched_stn in stn_status_opts else "Select"
                
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"m_stn_{i}")
                mat_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"m_rem_{i}")
                mat_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE MATERIAL BUTTONS ---
        col_m_add, col_m_rem, _ = st.columns([3, 3, 4])
        with col_m_add:
            if st.button("➕ Add Item", key="btn_add_mat_item", use_container_width=True):
                st.session_state.mat_count += 1
        with col_m_rem:
            if st.session_state.mat_count > 1:
                if st.button("➖ Remove Item", key="btn_rem_mat_item", use_container_width=True):
                    st.session_state.mat_count -= 1
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            save_mat = st.button("💾 Save Material", type="primary", use_container_width=True)
            
        if save_mat:
            has_m_err = False
            for b in mat_boqs:
                if not b:
                    st.error("⚠️ BOQ Number dalna compulsory hai!")
                    has_m_err = True
                    break
                    
            if not has_m_err:
                try:
                    st.success("✅ Warehouse Material Successfully Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving Material: {e}")

# --- 3.8 BULK UPLOAD DIALOG FUNCTION ---
@st.dialog("📤 Bulk Upload Site Data", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel (.xlsx) or .tsv file to bulk import site records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_site_file")
    
    if uploaded_file:
        if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file, sep='\t')
                    
                added_count = 0
                for index, row in df_upload.iterrows():
                    p_id = str(row.get("Project ID", row.get("project_id", ""))).strip()
                    if not p_id or p_id == "nan":
                        continue
                    
                    insert_dict = {}
                    for col in columns_list:
                        if col != "id" and col != "🎯 Select":
                            val = row.get(col, row.get(col.lower(), ""))
                            insert_dict[col] = str(val) if pd.notna(val) else ""
                            
                    try:
                        supabase.table("site_data").insert(insert_dict).execute()
                        added_count += 1
                    except Exception:
                        pass
                        
                st.success(f"✅ Bulk Upload Complete! {added_count} records added successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

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

# --- EDIT, DELETE & 3RD MATERIAL ACTION BUTTONS ---
selected_rows = edited_df[edited_df["🎯 Select"] == True]
if not selected_rows.empty:
    st.markdown("---")
    col_ed1, col_ed2, col_mat, col_ed3 = st.columns([1, 1, 1.2, 5.8])
    
    row_to_edit = selected_rows.iloc[0].to_dict()
    is_wh_required = str(row_to_edit.get("WH Material", "")).strip().lower() == "required"
    
    with col_ed1:
        if st.button("✏️ Edit Selected", type="primary", use_container_width=True):
            if 'edit_po_count' in st.session_state:
                del st.session_state['edit_po_count']
            edit_record_dialog(row_to_edit)
            
    with col_ed2:
        if st.button("🗑️ Delete Selected", type="primary", use_container_width=True):
            try:
                supabase.table(table_name).delete().eq("id", row_to_edit["id"]).execute()
                st.success("✅ Record Successfully Deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Deleting Record: {e}")
                
    with col_mat:
        if st.button("📦 Material", type="primary", use_container_width=True, disabled=not is_wh_required):
            if 'mat_count' in st.session_state:
                st.session_state.mat_count = 1
            material_movement_dialog(row_to_edit)
            
        if not is_wh_required:
            st.caption("🔒 WH Material not Required")

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
