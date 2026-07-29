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
    
    /* Dialog Styling */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #ffffff !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] p { color: #e2e8f0 !important; }
    div[data-testid="stDialog"] button[kind="icon"] svg { fill: #ffffff !important; }
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

categories = [
    "Department", "Operator", "Project Name", "Site Status", 
    "Product", "PO Status", "RFAI Status", "WH Material", 
    "Team Name", "Team Billing Status", "Extra Approval", 
    "Vision Billing Status", "WCC Status"
]

# --- NEW: EDIT DIALOG POPUP ---
@st.dialog("✏️ Edit Record", width="large")
def edit_dialog(row_data):
    with st.form("edit_form", border=False):
        # FIX: Category ko editable dropdown bana diya gaya hai
        default_index = categories.index(row_data['category']) if row_data['category'] in categories else 0
        new_cat = st.selectbox("Category", categories, index=default_index)
        
        new_val = st.text_input("Option Value", value=row_data.get('option_value', ''))
        
        # Agar category Team Name hai, tabhi extra fields dikhao
        if row_data['category'] == 'Team Name':
            c1, c2 = st.columns(2)
            with c1:
                mob = st.text_input("Mobile Number", value=row_data.get('mobile', ''))
                p_num = st.text_input("PAN Number", value=row_data.get('pan', ''))
            with c2:
                g_num = st.text_input("GST Number", value=row_data.get('gst', ''))
                perc = st.text_input("Percentage", value=row_data.get('percentage', ''))
        else:
            mob, p_num, g_num, perc = "", "", "", ""
            
        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if submitted:
            update_data = {
                "category": new_cat, # NEW: Update category in database
                "option_value": new_val.strip(),
                "mobile": mob, "pan": p_num, "gst": g_num, "percentage": perc
            }
            try:
                supabase.table(master_table_name).update(update_data).eq("id", row_data['id']).execute()
                st.success("✅ Record updated!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update Error: {e}")

# --- 4. HEADER ---
st.markdown('<div class="page-header">⚙️ Master Dropdown Settings</div>', unsafe_allow_html=True)
st.caption("Centralized hub to register and manage all your form dropdown values dynamically.")
st.markdown("<br>", unsafe_allow_html=True)

# --- 5. UI LAYOUT ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">➕ REGISTER NEW DROPDOWN OPTION</div>', unsafe_allow_html=True)
    
    # NEW: Dropdown outside the form to make the UI dynamic
    selected_category = st.selectbox("Select Dropdown Category", categories)
    
    with st.form("add_master_form", clear_on_submit=True):
        # NEW: Custom UI based on Selection
        if selected_category == "Team Name":
            new_option_value = st.text_input("Team Name *", placeholder="Enter Team Name")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                mobile = st.text_input("Mobile Number")
                pan = st.text_input("PAN Number")
            with col_t2:
                gst = st.text_input("GST Number")
                percentage = st.text_input("Percentage (%)")
        else:
            new_option_value = st.text_input("Enter New Option Value *", placeholder="e.g. Civil, Pending, etc.")
            mobile, pan, gst, percentage = "", "", "", ""
        
        submit_btn = st.form_submit_button("🚀 Add to Database", use_container_width=True)
        
        if submit_btn:
            if new_option_value.strip() == "":
                st.error("⚠️ Please enter a valid option value!")
            else:
                insert_data = {
                    "category": selected_category,
                    "option_value": new_option_value.strip(),
                    "is_active": True, # Active by default
                    "mobile": mobile,
                    "pan": pan,
                    "gst": gst,
                    "percentage": percentage
                }
                try:
                    supabase.table(master_table_name).insert(insert_data).execute()
                    st.success(f"✅ '{new_option_value}' has been successfully added to {selected_category}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Database Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 REGISTERED OPTIONS DATABASE</div>', unsafe_allow_html=True)
    
    filter_cat = st.selectbox("Filter Database by Category", ["View All"] + categories)
    
    try:
        if filter_cat == "View All":
            response = supabase.table(master_table_name).select("*").execute()
        else:
            response = supabase.table(master_table_name).select("*").eq("category", filter_cat).execute()
            
        data = response.data
        
        if data:
            df = pd.DataFrame(data)
            
            # Ensure columns exist to prevent errors
            for col in ['id', 'category', 'option_value', 'is_active', 'mobile', 'pan', 'gst', 'percentage']:
                if col not in df.columns:
                    df[col] = ""
            
            # Setup Display Dataframe
            if "🎯 Select" not in df.columns:
                df.insert(0, "🎯 Select", False)
            
            # Formatting Display Columns based on category
            if filter_cat == "Team Name":
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'mobile', 'pan', 'gst', 'percentage', 'is_active']].copy()
            else:
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'is_active']].copy()
            
            # Interactive Data Editor
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=350,
                column_config={
                    "id": None, # Hide ID from UI
                    "is_active": st.column_config.CheckboxColumn("Active?", disabled=True),
                    "🎯 Select": st.column_config.CheckboxColumn("Action", default=False)
                }
            )
            
            # NEW: EDIT, DEACTIVATE & DELETE LOGIC
            selected_rows = edited_df[edited_df["🎯 Select"] == True]
            if not selected_rows.empty:
                st.markdown("---")
                col_a1, col_a2, col_a3 = st.columns(3)
                row_to_edit = selected_rows.iloc[0].to_dict()
                
                with col_a1:
                    if st.button("✏️ Edit", use_container_width=True):
                        edit_dialog(row_to_edit)
                        
                with col_a2:
                    status_text = "🚫 Deactivate" if row_to_edit['is_active'] else "✅ Activate"
                    if st.button(status_text, use_container_width=True):
                        new_status = not row_to_edit['is_active']
                        try:
                            supabase.table(master_table_name).update({"is_active": new_status}).eq("id", row_to_edit['id']).execute()
                            st.rerun()
                        except Exception as e:
                            st.error("Error updating status.")
                            
                with col_a3:
                    if st.button("🗑️ Delete", type="primary", use_container_width=True):
                        try:
                            supabase.table(master_table_name).delete().eq("id", row_to_edit['id']).execute()
                            st.rerun()
                        except Exception as e:
                            st.error("Error deleting record.")
        else:
            st.info(f"ℹ️ No options registered yet for {filter_cat}.")
            
    except Exception as e:
        st.error(f"⚠️ Table Error: Please ensure all columns are created in Supabase. Details: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
