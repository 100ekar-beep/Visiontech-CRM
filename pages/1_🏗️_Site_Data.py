import streamlit as st
import pandas as pd
import math
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Site Data Hub", page_icon="🏗️", layout="wide")

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
    
    /* NEW: FIX FOR FIELD LABELS COLOR (Make them bright white) */
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

# --- 3.5 ADD RECORD DIALOG FUNCTION (POP-UP) ---
@st.dialog("📄 Add Site Data", width="large")
def add_record_dialog():
    st.caption("Configure comprehensive site metrics and procurement status")
    
    with st.form("add_new_site_form", border=False):
        st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
        
        # Row 1
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dept = st.selectbox("DEPARTMENT", ["Select Dept", "Civil", "Electrical", "Telecom", "Acquisition"])
        with c2:
            operator = st.selectbox("OPERATOR", ["Select Op", "Airtel", "Jio", "VIL", "BSNL"])
        with c3:
            proj_name = st.text_input("PROJECT NAME", placeholder="Enter Project Name")
        with c4:
            proj_id = st.text_input("PROJECT ID * (REQUIRED)", placeholder="Project ID")
            
        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            site_id = st.text_input("Site ID * (REQUIRED)", placeholder="Enter Site ID")
        with c6:
            site_name = st.text_input("SITE NAME", placeholder="Enter Site Name")
        with c7:
            cluster = st.text_input("CLUSTER", placeholder="Enter Cluster")
        with c8:
            site_status = st.selectbox("SITE STATUS", ["Status", "WIP", "Completed", "On Hold"])
            
        st.markdown('<div class="modal-section-title">📦 MATERIAL, PO & RFAI DETAILS</div>', unsafe_allow_html=True)
        
        # Row 3
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            product = st.selectbox("PRODUCT", ["Product", "Tower", "Pole", "Rooftop", "Tenancy"])
        with c10:
            po_no = st.text_input("PO NO.", placeholder="11 digits")
        with c11:
            po_date = st.date_input("PO DATE", value=None)
        with c12:
            po_status = st.selectbox("PO STATUS", ["Status", "Released", "Pending", "Cancelled"])
            
        # Row 4
        c13, c14, c15, c16 = st.columns(4)
        with c13:
            rfai_status = st.selectbox("RFAI STATUS", ["RFAI", "Declared", "Pending"])
        with c14:
            wh_material = st.selectbox("WH MATERIAL *", ["Not Required", "Requested", "Delivered"])
        with c15:
            team_name = st.selectbox("TEAM NAME", ["Select Team", "Team Alpha", "Team Beta", "Vendor A"])
        with c16:
            extra_approval = st.selectbox("EXTRA APPROVAL", ["Not Available", "Required", "Approved"])

        st.markdown('<div class="modal-section-title">💰 BILLING & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        # Row 5
        c17, c18, c19, c20 = st.columns(4)
        with c17:
            team_billing = st.selectbox("TEAM BILLING STATUS", ["Pending", "In Process", "Billed", "Paid"])
        with c18:
            vision_billing = st.selectbox("VISION BILLING STATUS", ["Status", "Pending", "Submitted", "Cleared"])
        with c19:
            wcc_num = st.text_input("WCC NUMBER", placeholder="Enter WCC No.")
        with c20:
            wcc_status = st.selectbox("WCC STATUS", ["Status", "Pending", "Approved", "Rejected"])
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Form Submit Buttons
        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.form_submit_button("➕ Add Data", use_container_width=True)
            
        if submitted:
            if not proj_id or not site_id:
                st.error("⚠️ Project ID aur Site ID dalna compulsory hai!")
            else:
                # Prepare data dictionary exactly matching the columns
                insert_data = {
                    "Department": dept if dept != "Select Dept" else "",
                    "Operator": operator if operator != "Select Op" else "",
                    "Project Name": proj_name,
                    "Project ID": proj_id,
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Cluster": cluster,
                    "Site Status": site_status if site_status != "Status" else "",
                    "Product": product if product != "Product" else "",
                    "PO No.": po_no,
                    "PO Date": str(po_date) if po_date else "",
                    "PO Status": po_status if po_status != "Status" else "",
                    "RFAI Status": rfai_status if rfai_status != "RFAI" else "",
                    "WH Material": wh_material if wh_material != "Not Required" else "",
                    "Team Name": team_name if team_name != "Select Team" else "",
                    "Team Billing Status": team_billing if team_billing != "Pending" else "",
                    "Extra Approval": extra_approval if extra_approval != "Not Available" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Status" else "",
                    "WCC Number": wcc_num,
                    "WCC Status": wcc_status if wcc_status != "Status" else ""
                }
                
                try:
                    supabase.table("site_data").insert(insert_data).execute()
                    st.success("✅ Record Successfully Added!")
                    st.rerun() # Refresh to show new data in table
                except Exception as e:
                    st.error(f"❌ Error Saving Data: {e}")

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_add, col_upload, col_export = st.columns([4, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🏗️ Site Data Master</h2>", unsafe_allow_html=True)
with col_add:
    if st.button("➕ Add Record", use_container_width=True):
        st.session_state.action = "add"
        add_record_dialog() # Calling the pop-up function here
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
    "Site Name", "Cluster", "Site Status", "Product", "PO No.", 
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
