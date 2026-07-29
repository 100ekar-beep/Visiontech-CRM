import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Master Data Settings", page_icon="⚙️", layout="wide")

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

# Database Table Name for Dropdowns
master_table_name = "dropdown_master"

# --- 4. HEADER ---
st.markdown('<div class="page-header">⚙️ Master Dropdown Settings</div>', unsafe_allow_html=True)
st.caption("Centralized hub to register and manage all your form dropdown values dynamically.")
st.markdown("<br>", unsafe_allow_html=True)

# Define all the categories user requested
categories = [
    "Department", "Operator", "Project Name", "Site Status", 
    "Product", "PO Status", "RFAI Status", "WH Material", 
    "Team Name", "Team Billing Status", "Extra Approval", 
    "Vision Billing Status", "WCC Status"
]

# --- 5. UI LAYOUT ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">➕ REGISTER NEW DROPDOWN OPTION</div>', unsafe_allow_html=True)
    
    with st.form("add_master_form", clear_on_submit=True):
        selected_category = st.selectbox("Select Dropdown Category", categories)
        new_option_value = st.text_input("Enter New Option Value", placeholder="e.g. Civil, Pending, etc.")
        
        submit_btn = st.form_submit_button("🚀 Add to Database", use_container_width=True)
        
        if submit_btn:
            if new_option_value.strip() == "":
                st.error("⚠️ Please enter a valid option value!")
            else:
                insert_data = {
                    "category": selected_category,
                    "option_value": new_option_value.strip()
                }
                try:
                    supabase.table(master_table_name).insert(insert_data).execute()
                    st.success(f"✅ '{new_option_value}' has been successfully added to {selected_category}!")
                    st.rerun()
                except Exception as e:
                    # FIX: Yahan ab Supabase ka actual exact error dikhega
                    st.error(f"❌ Database Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 REGISTERED OPTIONS DATABASE</div>', unsafe_allow_html=True)
    
    filter_cat = st.selectbox("Filter Database by Category", ["View All"] + categories)
    
    try:
        # Fetching data from Supabase
        if filter_cat == "View All":
            response = supabase.table(master_table_name).select("*").execute()
        else:
            response = supabase.table(master_table_name).select("*").eq("category", filter_cat).execute()
            
        data = response.data
        
        if data:
            df = pd.DataFrame(data)
            # Reorder columns for beautiful display
            display_df = df[['category', 'option_value']]
            display_df.columns = ["Dropdown Category", "Registered Value"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=250)
        else:
            st.info(f"ℹ️ No options registered yet for {filter_cat}.")
            
    except Exception as e:
        st.error(f"⚠️ Table Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
