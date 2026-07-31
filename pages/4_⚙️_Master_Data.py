import streamlit as st
import pandas as pd
import io
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

    /* =========================================================
       NEW: PREMIUM SIDEBAR NAVIGATION BUTTONS
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

# --- NAYI LINE: Added Vendor Name, Payment From, and Payment Type in Categories ---
categories = [
    "Department", "Operator", "Project Name", "Site Status", 
    "Product", "PO Status", "RFAI Status", "WH Material", 
    "Team Name", "Vendor Name", "Payment From", "Payment Type",
    "Team Billing Status", "Extra Approval", 
    "Vision Billing Status", "WCC Status",
    "SRN Status", "Transaction Type", "Item Code", 
    "Item Description", "Material Status", "STN Status"
]

# --- NEW: BULK UPLOAD DIALOG POPUP ---
@st.dialog("📤 Bulk Upload Item Codes", width="large")
def bulk_upload_item_dialog():
    st.caption("Upload Excel (.xlsx) or .tsv file. Required columns: item_code, item_description, material_of, stn_status, rate")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_item_file")
    
    if uploaded_file:
        if st.button("🚀 Process & Upload Items", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file, sep='\t')
                    
                added_count = 0
                failed_count = 0
                
                for index, row in df_upload.iterrows():
                    val = str(row.get("item_code", row.get("Item Code", row.get("Itemcode", row.get("option_value", ""))) )).strip()
                    if not val or val == "nan":
                        continue
                        
                    desc = str(row.get("item_description", row.get("Item Description", row.get("Description", ""))))
                    if desc == "nan": desc = ""

                    mat = str(row.get("material_of", row.get("Material of", row.get("Material Of", "Indus"))))
                    if mat == "nan" or not mat.strip(): mat = "Indus"

                    stn = str(row.get("stn_status", row.get("STN Status", row.get("Stn Status", "Required"))))
                    if stn == "nan" or not stn.strip(): stn = "Required"

                    raw_rate = row.get("rate", row.get("Rate", None))
                    clean_rate = float(raw_rate) if pd.notna(raw_rate) and str(raw_rate).strip() != "" else None

                    insert_dict = {
                        "category": "Item Code",
                        "option_value": val,
                        "is_active": True,
                        "item_description": desc,
                        "material_of": mat,
                        "stn_status": stn,
                        "rate": clean_rate
                    }
                    try:
                        supabase.table(master_table_name).insert(insert_dict).execute()
                        added_count += 1
                    except Exception as db_e:
                        failed_count += 1
                        st.error(f"❌ DB Error at row {index+1} ({val}): {db_e}")
                        
                if added_count > 0:
                    st.success(f"✅ Bulk Upload Complete! {added_count} Item Codes Added Successfully. (Failed: {failed_count})")
                    if failed_count == 0:
                        st.rerun()
                else:
                    st.error(f"⚠️ No records added. Please check Supabase table columns and data format!")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- NEW: EDIT DIALOG POPUP (WITH DIRECT SUPABASE FETCH) ---
@st.dialog("✏️ Edit Record", width="large")
def edit_dialog(row_data):
    # Fetch fresh record directly from Supabase using ID to ensure all columns are loaded
    record_id = row_data.get('id')
    live_data = row_data
    try:
        res = supabase.table(master_table_name).select("*").eq("id", record_id).execute()
        if res.data and len(res.data) > 0:
            live_data = res.data[0]
    except Exception as e:
        pass

    with st.form("edit_form", border=False):
        default_index = categories.index(live_data['category']) if live_data['category'] in categories else 0
        new_cat = st.selectbox("Category", categories, index=default_index)
        
        new_val = st.text_input("Option Value", value=str(live_data.get('option_value', '') or ''))
        
        mob, p_num, g_num, perc, item_desc_val, stn_status_val, mat_of_val, rate_val = "", "", "", "", "", "", "Indus", None
        
        if new_cat == 'Team Name':
            c1, c2 = st.columns(2)
            with c1:
                mob = st.text_input("Mobile Number", value=str(live_data.get('mobile', '') or ''))
                p_num = st.text_input("PAN Number", value=str(live_data.get('pan', '') or ''))
            with c2:
                g_num = st.text_input("GST Number", value=str(live_data.get('gst', '') or ''))
                perc = st.text_input("Percentage", value=str(live_data.get('percentage', '') or ''))
        # --- NAYI LINE: Vendor Name Edit Form Logic ---
        elif new_cat == 'Vendor Name':
            c1, c2 = st.columns(2)
            with c1:
                mob = st.text_input("Mobile Number", value=str(live_data.get('mobile', '') or ''))
                p_num = st.text_input("PAN Number", value=str(live_data.get('pan', '') or ''))
            with c2:
                g_num = st.text_input("GST Number", value=str(live_data.get('gst', '') or ''))
        elif new_cat == 'Item Code':
            c1, c2 = st.columns(2)
            with c1:
                item_desc_val = st.text_input("Item Description", value=str(live_data.get('item_description', '') or ''))
                mat_opts_list = ["Indus", "Visiontech"]
                curr_mat = str(live_data.get('material_of', 'Indus') or 'Indus')
                mat_idx = mat_opts_list.index(curr_mat) if curr_mat in mat_opts_list else 0
                mat_of_val = st.selectbox("Material of", mat_opts_list, index=mat_idx)
            with c2:
                stn_opts_list = ["Required", "Not Required"]
                curr_stn = str(live_data.get('stn_status', 'Required') or 'Required')
                stn_idx = stn_opts_list.index(curr_stn) if curr_stn in stn_opts_list else 0
                stn_status_val = st.selectbox("STN Status", stn_opts_list, index=stn_idx)
                
                existing_rate = live_data.get('rate')
                rate_str = str(existing_rate) if existing_rate is not None else ''
                raw_rate_ed = st.text_input("Rate", value=rate_str)
                rate_val = float(raw_rate_ed) if raw_rate_ed.strip() != '' else None
            
        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if submitted:
            update_data = {
                "category": new_cat,
                "option_value": new_val.strip(),
                "mobile": mob, "pan": p_num, "gst": g_num, "percentage": perc,
                "item_description": item_desc_val, "stn_status": stn_status_val,
                "material_of": mat_of_val, "rate": rate_val
            }
            try:
                supabase.table(master_table_name).update(update_data).eq("id", record_id).execute()
                st.success("✅ Record updated!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update Error: {e}")

# --- 4. HEADER ---
col_head1, col_head2 = st.columns([7, 3])
with col_head1:
    st.markdown('<div class="page-header">⚙️ Master Dropdown Settings</div>', unsafe_allow_html=True)
    st.caption("Centralized hub to register and manage all your form dropdown values dynamically.")
with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📤 Bulk Upload Item Codes", use_container_width=True):
        bulk_upload_item_dialog()

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. UI LAYOUT ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">➕ REGISTER NEW DROPDOWN OPTION</div>', unsafe_allow_html=True)
    
    selected_category = st.selectbox("Select Dropdown Category", categories)
    
    with st.form("add_master_form", clear_on_submit=True):
        mobile, pan, gst, percentage, item_desc, stn_status, material_of, rate = "", "", "", "", "", "Required", "Indus", None
        
        if selected_category == "Team Name":
            new_option_value = st.text_input("Team Name *", placeholder="Enter Team Name")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                mobile = st.text_input("Mobile Number")
                pan = st.text_input("PAN Number")
            with col_t2:
                gst = st.text_input("GST Number")
                percentage = st.text_input("Percentage (%)")
        # --- NAYI LINE: Vendor Name Add Form Logic ---
        elif selected_category == "Vendor Name":
            new_option_value = st.text_input("Vendor Name *", placeholder="Enter Vendor Name")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                mobile = st.text_input("Mobile Number")
                pan = st.text_input("PAN Number")
            with col_v2:
                gst = st.text_input("GST Number")
        elif selected_category == "Item Code":
            new_option_value = st.text_input("Item Code *", placeholder="Enter Item Code")
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                item_desc = st.text_input("Item Description *", placeholder="Enter Item Description")
                material_of = st.selectbox("Material of *", ["Indus", "Visiontech"])
            with col_i2:
                stn_status = st.selectbox("STN Status *", ["Required", "Not Required"])
                raw_rate_input = st.text_input("Rate *", placeholder="Enter Rate")
                rate = float(raw_rate_input) if raw_rate_input.strip() != "" else None
        else:
            # Payment From and Payment Type will perfectly use this default block
            new_option_value = st.text_input("Enter New Option Value *", placeholder="e.g. Civil, Pending, etc.")
        
        submit_btn = st.form_submit_button("🚀 Add to Database", use_container_width=True)
        
        if submit_btn:
            if new_option_value.strip() == "":
                st.error("⚠️ Please enter a valid option value!")
            else:
                insert_data = {
                    "category": selected_category,
                    "option_value": new_option_value.strip(),
                    "is_active": True,
                    "mobile": mobile,
                    "pan": pan,
                    "gst": gst,
                    "percentage": percentage,
                    "item_description": item_desc,
                    "stn_status": stn_status,
                    "material_of": material_of,
                    "rate": rate
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
            
            for col in ['id', 'category', 'option_value', 'is_active', 'mobile', 'pan', 'gst', 'percentage', 'item_description', 'stn_status', 'material_of', 'rate']:
                if col not in df.columns:
                    df[col] = ""
            
            if "🎯 Select" not in df.columns:
                df.insert(0, "🎯 Select", False)
            
            if filter_cat == "Team Name":
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'mobile', 'pan', 'gst', 'percentage', 'is_active']].copy()
            # --- NAYI LINE: Vendor Name Table View Display Logic ---
            elif filter_cat == "Vendor Name":
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'mobile', 'pan', 'gst', 'is_active']].copy()
            elif filter_cat == "Item Code":
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'item_description', 'material_of', 'stn_status', 'rate', 'is_active']].copy()
            else:
                display_df = df[['🎯 Select', 'id', 'category', 'option_value', 'is_active']].copy()
            
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=350,
                column_config={
                    "id": None,
                    "is_active": st.column_config.CheckboxColumn("Active?", disabled=True),
                    "🎯 Select": st.column_config.CheckboxColumn("Action", default=False)
                }
            )
            
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
