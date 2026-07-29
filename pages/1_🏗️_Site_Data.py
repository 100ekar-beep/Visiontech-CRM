import streamlit as st
import pandas as pd
import math
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
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Pagination Text */
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    
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
        fill: #ffffff !important; /* Close button color fix */
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
            
        # ------------------------------------------------------------------
        # SITE ID DALNE PAR AUTO-FETCH (Area, KM, Lat Long)
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 2 LINES MEIN WHITE COLOR DETAILS WITH AREA, KM, & LAT/LONG
        # ------------------------------------------------------------------
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
        
        # --- UPDATE: Row 3 (Team Billing and Vision Billing shifted up here) ---
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            product = st.selectbox("PRODUCT", get_opts("Product", all_dd))
        with c10:
            team_billing = st.selectbox("TEAM BILLING STATUS", get_opts("Team Billing Status", all_dd))
        with c11:
            vision_billing = st.selectbox("VISION BILLING STATUS", get_opts("Vision Billing Status", all_dd))
        with c12:
            po_status = st.selectbox("PO STATUS", get_opts("PO Status", all_dd))
            
        # Row 4
        c13, c14, c15, c16 = st.columns(4)
        with c13:
            rfai_status = st.selectbox("RFAI STATUS", get_opts("RFAI Status", all_dd))
        with c14:
            wh_material = st.selectbox("WH MATERIAL *", get_opts("WH Material", all_dd))
        with c15:
            team_name = st.selectbox("TEAM NAME", get_opts("Team Name", all_dd))
        with c16:
            extra_approval = st.selectbox("EXTRA APPROVAL", get_opts("Extra Approval", all_dd))

        # --- UPDATE: DYNAMIC MULTIPLE PO SECTION ---
        st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        po_nos = []
        po_dates = []
        wcc_nums = []
        wcc_statuses = []
        
        # Loop to generate dynamic PO Rows
        for i in range(st.session_state.po_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
            
            c17, c18, c19, c20 = st.columns(4)
            with c17:
                p_n = st.text_input("PO NO.", placeholder="11 digits", key=f"po_no_{i}")
                po_nos.append(p_n)
            with c18:
                p_d = st.date_input("PO DATE", value=None, key=f"po_date_{i}")
                po_dates.append(p_d)
            with c19:
                w_n = st.text_input("WCC NUMBER", placeholder="11 digits", key=f"wcc_num_{i}")
                wcc_nums.append(w_n)
            with c20:
                w_s = st.selectbox("WCC STATUS", get_opts("WCC Status", all_dd), key=f"wcc_status_{i}")
                wcc_statuses.append(w_s)
                
        # Additional PO Button
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_add, _ = st.columns([3, 7])
        with col_btn_add:
            if st.button("➕ Add Additional PO", use_container_width=True):
                st.session_state.po_count += 1
                st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Form Submit Buttons
        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.button("💾 Save All Data", type="primary", use_container_width=True)
            
        if submitted:
            has_error = False
            
            # 1. Project ID & Site ID Required
            if not proj_id or not site_id:
                st.error("⚠️ Project ID aur Site ID dalna compulsory hai!")
                has_error = True
            
            # 2. Dynamic PO No 11 Digit Check
            for p in po_nos:
                if p and (not p.isdigit() or len(p) != 11):
                    st.error(f"⚠️ PO NO. '{p}' strict 11 digit ka number hona chahiye!")
                    has_error = True
                
            # 3. Dynamic WCC No 11 Digit Check
            for w in wcc_nums:
                if w and (not w.isdigit() or len(w) != 11):
                    st.error(f"⚠️ WCC NUMBER '{w}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            
            # 4. Project ID Duplicate Check
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
                    
                    # COMMA SEPARATED JOIN FOR MULTIPLE POs (Safe to save in text column)
                    "PO No.": ", ".join([p for p in po_nos if p]),
                    "PO Date": ", ".join([str(d) for d in po_dates if d]),
                    
                    "PO Status": po_status if po_status != "Select" else "",
                    "RFAI Status": rfai_status if rfai_status != "Select" else "",
                    "WH Material": wh_material if wh_material != "Select" else "",
                    "Team Name": team_name if team_name != "Select" else "",
                    "Team Billing Status": team_billing if team_billing != "Select" else "",
                    "Extra Approval": extra_approval if extra_approval != "Select" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Select" else "",
                    
                    # COMMA SEPARATED JOIN FOR MULTIPLE WCCs
                    "WCC Number": ", ".join([w for w in wcc_nums if w]),
                    "WCC Status": ", ".join([ws if ws != "Select" else "" for ws in wcc_statuses])
                }
                
                try:
                    supabase.table("site_data").insert(insert_data).execute()
                    st.success("✅ Record Successfully Added!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"❌ Error Saving Data: {e}")

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_add, col_upload, col_export = st.columns([4, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🏗️ Site Data Master</h2>", unsafe_allow_html=True)
with col_add:
    if st.button("➕ Add Record", use_container_width=True):
        st.session_state.action = "add"
        st.session_state.po_count = 1 # Popup open hone par hamesha 1 PO dabba dikhega
        add_record_dialog() 
with col_upload:
    if st.button("📤 Bulk Upload (.tsv)", use_container_width=True):
        st.session_state.action = "upload"
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

# Define All Columns exactly as requested
columns_list = [
    "Department", "Operator", "Project Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Site Status", "Work Description", "Product", "PO No.", 
    "PO Date", "PO Status", "RFAI Status", "WH Material", "Team Name", 
    "Team Billing Status", "Extra Approval", "Vision Billing Status", 
    "WCC Number", "WCC Status"
]

if data:
    df = pd.DataFrame(data)
    # Ensure all columns exist even if data is partial
    for col in columns_list:
        if col not in df.columns:
            df[col] = ""
else:
    # Empty Lavish DataFrame
    df = pd.DataFrame(columns=columns_list)

# Pehla column "Action" select ke liye add kar rahe hain
if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)
else:
    df["🎯 Select"] = False

# --- 6. PAGINATION LOGIC (10 lines per page) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

# Bound page limits
if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages
elif st.session_state.current_page < 1:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 7. LAVISH DATA TABLE (Horizonal & Vertical Scroll) ---
st.markdown("##### 🗄️ Live Database Records")
df_page = df.iloc[start_idx:end_idx].copy()

# Data Editor jisme user row select kar sakta hai
edited_df = st.data_editor(
    df_page, 
    use_container_width=True, 
    hide_index=True,
    height=400, # Fixed height for vertical roller
    column_config={
        "🎯 Select": st.column_config.CheckboxColumn("Edit/Del", default=False)
    }
)

# Agar user ne koi row select ki hai, toh Edit/Delete buttons show honge
selected_rows = edited_df[edited_df["🎯 Select"] == True]
if not selected_rows.empty:
    st.markdown("---")
    col_ed1, col_ed2, col_ed3 = st.columns([1, 1, 6])
    with col_ed1:
        st.button("✏️ Edit Selected", type="primary", use_container_width=True)
    with col_ed2:
        st.button("🗑️ Delete Selected", type="primary", use_container_width=True)

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
