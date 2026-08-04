import streamlit as st
import pandas as pd
import urllib.parse
import requests # API Call ke liye
import time # For page refresh
from supabase import create_client, Client
from datetime import datetime

# --- 1. SUPABASE CONNECTION ---
URL = "https://sckyflvukpmdqmdzjzhs.supabase.co"
KEY = "sb_publishable_rAiegSkKYvM0Z9n7sUAI1w_WTgm1S4I" 
supabase: Client = create_client(URL, KEY)

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="STN Details", page_icon="🔄", layout="wide")

# --- 3. LAVISH CUSTOM CSS (EXACTLY SAME AS PREVIOUS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Primary Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4) !important;
    }

    /* PERFECT SOLID BORDERS FOR TEXT INPUT BOXES */
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stNumberInput"] div[data-baseweb="input"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        border: 2px solid #cbd5e1 !important; 
        border-radius: 8px !important;
        background-color: #ffffff !important;
    }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
        border-color: #3b82f6 !important; 
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
        color: #0f172a !important;
        font-weight: 600 !important;
        padding: 10px !important;
    }
    
    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #475569 !important; font-weight: 700 !important; font-size: 0.9rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #1E3A8A !important; color: white !important; font-weight: 700 !important; }

    /* Expanders */
    [data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }
    
    /* Custom Info Cards WITH SOLID BORDER FIX */
    .info-card {
        background: #ffffff; 
        border-radius: 12px; 
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
        border: 2px solid #94a3b8 !important; 
        margin-bottom: 15px;
    }
    
    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
    section[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important; 
    }
    div[data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    div[data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; border-color: transparent !important;
    }
    div[data-testid="stSidebarNav"] a span { color: inherit !important; }
    </style>
""", unsafe_allow_html=True)


# Helper function to dynamically find actual column names in database
def get_actual_col(df_columns, possible_names):
    for col in df_columns:
        if str(col).strip().lower() in [p.lower() for p in possible_names]:
            return col
    return None

# =====================================================================
# 🔄 STN PAGE HEADER & TABS
# =====================================================================

st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 30px;'>🔄 STN Details & Processing</h1>", unsafe_allow_html=True)

# 3 Requested Tabs
tab1, tab2, tab3 = st.tabs(["⏳ 1. STN Pending", "✅ 2. STN Closed", "🔙 3. Fresh Material Return to WH"])

# =====================================================================
# TAB 1: STN PENDING LOGIC
# =====================================================================
with tab1:
    st.markdown("### ⏳ Pending STN Records")
    
    # Upper Search Box
    search_query = st.text_input("🔍 Search within Pending STN", placeholder="Enter Project ID, Site Name, Item Description etc...")
    
    try:
        # Fetching data from Warehouse table (Double bypass fetch for reliability)
        wh_data = []
        res = supabase.table("warehouse_data").select("*").execute()
        if res.data:
            wh_data = res.data
        else:
            headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
            r = requests.get(f"{URL}/rest/v1/warehouse_data?select=*", headers=headers)
            if r.status_code == 200:
                wh_data = r.json()

        if wh_data:
            df = pd.DataFrame(wh_data)
            
            # Smart Column Detection (Case Insensitive)
            stn_status_col = get_actual_col(df.columns, ["stn_status", "stn status", "stnstatus"])
            mat_status_col = get_actual_col(df.columns, ["material_status", "material status", "materialstatus"])
            
            # Mapping strictly required columns
            col_map = {
                "Project ID": get_actual_col(df.columns, ["project_id", "project id"]),
                "Site ID": get_actual_col(df.columns, ["site_id", "site id"]),
                "Site Name": get_actual_col(df.columns, ["site_name", "site name"]),
                "Cluster": get_actual_col(df.columns, ["cluster"]),
                "ITEM DESCRIPTION": get_actual_col(df.columns, ["item_description", "item description", "description"]),
                "Qty": get_actual_col(df.columns, ["qty", "quantity"]),
                "Team Name": get_actual_col(df.columns, ["team_name", "team name"])
            }
            
            id_col = get_actual_col(df.columns, ["id", "uuid", "uid"]) # Used for Edit/Delete
            
            if stn_status_col and mat_status_col:
                # APPLYING MANDATORY LOGIC 1 & 2
                df_filtered = df[
                    (df[stn_status_col].astype(str).str.strip().str.lower() == 'required') & 
                    (df[mat_status_col].astype(str).str.strip().str.lower() == 'dispatched')
                ].copy()
                
                if not df_filtered.empty:
                    # Global Search Logic
                    if search_query:
                        search_mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                        df_filtered = df_filtered[search_mask]
                    
                    # Formatting Display Dataframe
                    display_df = pd.DataFrame()
                    for display_name, actual_col in col_map.items():
                        if actual_col:
                            display_df[display_name] = df_filtered[actual_col]
                        else:
                            display_df[display_name] = "N/A" # Fallback if column missing in DB
                            
                    # Injecting hidden ID for mapping
                    if id_col:
                        display_df['_ID'] = df_filtered[id_col].values 
                        
                    # 📥 Top Action Bar (Count + Excel Download)
                    c_stats, c_down = st.columns([3, 1])
                    c_stats.success(f"✅ Showing {len(display_df)} Pending STN Record(s)")
                    
                    # Convert to CSV for Excel Download
                    csv_data = display_df.drop(columns=['_ID'], errors='ignore').to_csv(index=False).encode('utf-8')
                    c_down.download_button("📥 Download Excel File", data=csv_data, file_name="STN_Pending.csv", mime="text/csv", use_container_width=True)
                    
                    # 📊 Display Data Table
                    st.dataframe(display_df.drop(columns=['_ID'], errors='ignore'), use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # 🛠️ VIEW, EDIT & DELETE SECTION
                    st.markdown("### 🛠️ Manage Selected Record (View / Edit / Delete)")
                    
                    if id_col:
                        # Generating Dropdown Options mapped to IDs
                        site_col_name = col_map["Site ID"] if col_map["Site ID"] else id_col
                        record_options = df_filtered[id_col].astype(str) + " | Site: " + df_filtered[site_col_name].astype(str)
                        record_dict = dict(zip(record_options, df_filtered[id_col].values))
                        
                        sel_rec = st.selectbox("📌 Select a record to Edit or Delete", ["-- Select Record --"] + list(record_dict.keys()))
                        
                        if sel_rec != "-- Select Record --":
                            sel_id = record_dict[sel_rec]
                            record_data = df_filtered[df_filtered[id_col] == sel_id].iloc[0]
                            
                            st.markdown("<div class='info-card'>", unsafe_allow_html=True)
                            with st.form(f"edit_form_{sel_id}"):
                                st.markdown("#### ✏️ Update Record Details")
                                ec1, ec2, ec3 = st.columns(3)
                                
                                # Populating Input fields automatically based on required columns
                                edit_vals = {}
                                cols_to_edit = [k for k,v in col_map.items() if v is not None]
                                
                                for i, col_title in enumerate(cols_to_edit):
                                    act_col = col_map[col_title]
                                    col_container = [ec1, ec2, ec3][i % 3]
                                    with col_container:
                                        edit_vals[act_col] = st.text_input(f"{col_title}", value=str(record_data[act_col]) if pd.notna(record_data[act_col]) else "")
                                        
                                st.write("")
                                btn_c1, btn_c2 = st.columns(2)
                                with btn_c1:
                                    update_btn = st.form_submit_button("💾 Update Database", type="primary", use_container_width=True)
                                with btn_c2:
                                    delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                                    
                                if update_btn:
                                    try:
                                        supabase.table("warehouse_data").update(edit_vals).eq(id_col, sel_id).execute()
                                        st.success("✅ Record updated successfully!")
                                        time.sleep(1) # Delay for smooth UI refresh
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error updating: {e}")
                                        
                                if delete_btn:
                                    try:
                                        supabase.table("warehouse_data").delete().eq(id_col, sel_id).execute()
                                        st.success("🗑️ Record deleted successfully!")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error deleting: {e}")
                                        
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ No Primary Key ('id') column found in table to perform Edit/Delete operations.")

                else:
                    st.info("⚠️ Currently, there are no records where STN Status is 'Required' AND Material Status is 'Dispatched'.")
            else:
                st.error("⚠️ System error: 'STN Status' ya 'Material Status' columns database table me nahi mile. Spelings check karein.")
        else:
            st.info("⚠️ Table 'warehouse_data' me abhi koi data nahi hai.")
            
    except Exception as e:
        st.error(f"Database Fetch Error: {e}")

# =====================================================================
# TAB 2: STN CLOSED LOGIC
# =====================================================================
with tab2:
    st.info("🚀 STN Closed - Logic to be updated as per your instruction.")

# =====================================================================
# TAB 3: FRESH MATERIAL RETURN LOGIC
# =====================================================================
with tab3:
    st.info("🔙 Fresh Material Return - Logic to be updated as per your instruction.")
