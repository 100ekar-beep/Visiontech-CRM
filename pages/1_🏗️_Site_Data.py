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
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_add, col_upload, col_export = st.columns([4, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🏗️ Site Data Master</h2>", unsafe_allow_html=True)
with col_add:
    if st.button("➕ Add Record", use_container_width=True):
        st.session_state.action = "add"
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
df.insert(0, "🎯 Select", False)

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
