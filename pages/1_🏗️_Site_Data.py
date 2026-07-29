import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Site Data Management", page_icon="🏢", layout="wide")

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Premium Glassmorphism Container */
    .glass-container {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Gradient Buttons */
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

    /* Fix for Labels to be bright white */
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }
    
    /* Headers */
    .page-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
    }
    .section-title {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
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

master_table_name = "dropdown_master"
site_table_name = "site_data"  # Example site table name, keeping existing names intact

# --- HELPER: FETCH MASTER OPTIONS ---
def get_master_options(category_name):
    try:
        res = supabase.table(master_table_name).select("*").eq("category", category_name).eq("is_active", True).execute()
        if res.data:
            return [str(item.get("option_value", "")) for item in res.data]
    except Exception as e:
        pass
    return []

# --- HELPER: FETCH ITEM MASTER DETAILS FOR AUTO-FILL ---
def get_item_master_details():
    try:
        res = supabase.table(master_table_name).select("*").eq("category", "Item Code").eq("is_active", True).execute()
        if res.data:
            mapping = {}
            for item in res.data:
                code = str(item.get("option_value", "")).strip()
                if code:
                    mapping[code] = {
                        "description": str(item.get("item_description", "") or ""),
                        "stn_status": str(item.get("stn_status", "Required") or "Required"),
                        "material_of": str(item.get("material_of", "Indus") or "Indus"),
                        "rate": item.get("rate")
                    }
            return mapping
    except Exception as e:
        pass
    return {}

# --- 4. HEADER ---
st.markdown('<div class="page-header">🏢 Site Data & Material Tracking</div>', unsafe_allow_html=True)
st.caption("Manage site operations, warehouse material movements, and automated tracking.")
st.markdown("<br>", unsafe_allow_html=True)

# --- 5. WAREHOUSE MATERIAL TRACKING FORM SECTION ---
st.markdown('<div class="glass-container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📦 WAREHOUSE MATERIAL TRACKING FORM</div>', unsafe_allow_html=True)

# Fetch dynamic item details dictionary
item_master_dict = get_item_master_details()
item_codes_list = list(item_master_dict.keys())

# Site Info Row (Mock / Existing structure)
c_p1, c_p2, c_p3, c_p4, c_p5, c_p6 = st.columns(6)
with c_p1:
    st.text_input("PROJECT ID", value="OM-RELIBB-3433331", disabled=True)
with c_p2:
    st.text_input("SITE ID", value="IN-1086244", disabled=True)
with c_p3:
    st.text_input("SITE NAME", value="Ghatnandra", disabled=True)
with c_p4:
    st.text_input("CLUSTER", value="Buldhana", disabled=True)
with c_p5:
    st.text_input("TEAM", value="Pramodkumar Jaju", disabled=True)
with c_p6:
    srn_status_opts = get_master_options("SRN Status")
    st.selectbox("SRN STATUS *", ["Select"] + srn_status_opts)

st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

# Transaction & Asset Items Row
col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)

with col_t1:
    trans_opts = get_master_options("Transaction Type")
    transaction_type = st.selectbox("TRANSACTION TYPE", ["Select"] + trans_opts)

with col_t2:
    boq_number = st.text_input("BOQ NUMBER *", placeholder="BOQ No")

with col_t3:
    # UPDATED: Item Code as searchable selectbox / input to enable auto-fill
    item_code_options = ["Select Item Code"] + item_codes_list
    selected_item_code = st.selectbox("ITEM CODE *", item_code_options)

# Get auto-filled values based on selected item code
auto_description = ""
auto_stn_status = "Select"

if selected_item_code != "Select Item Code" and selected_item_code in item_master_dict:
    auto_description = item_master_dict[selected_item_code]["description"]
    auto_stn_status_val = item_master_dict[selected_item_code]["stn_status"]
    stn_opts = get_master_options("STN Status")
    if auto_stn_status_val in stn_opts:
        auto_stn_status = auto_stn_status_val

with col_t4:
    # UPDATED: Automatic Item Description populated from master data
    item_description = st.text_input("ITEM DESCRIPTION", value=auto_description, placeholder="Description")

with col_t5:
    indus_qty = st.number_input("INDUS QTY", min_value=0, value=0)

# Second row of items
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    mat_status_opts = get_master_options("Material Status")
    material_status = st.selectbox("MATERIAL STATUS", ["Select"] + mat_status_opts)

with col_m2:
    dispatch_date = st.date_input("DISPATCH DATE", value=None)

with col_m3:
    # UPDATED: Automatic STN Status populated from master data
    stn_status_opts = get_master_options("STN Status")
    stn_status_dropdown_list = ["Select"] + stn_status_opts
    
    default_stn_idx = 0
    if auto_stn_status in stn_status_dropdown_list:
        default_stn_idx = stn_status_dropdown_list.index(auto_stn_status)
        
    stn_status = st.selectbox("STN STATUS", stn_status_dropdown_list, index=default_stn_idx)

with col_m4:
    remarks = st.text_input("REMARKS", placeholder="Remarks notes")

st.markdown("<br>", unsafe_allow_html=True)
col_b1, col_b2 = st.columns([1, 4])
with col_b1:
    st.button("➕ Add Item", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.button("💾 Save Material", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
