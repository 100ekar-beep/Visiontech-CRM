import streamlit as st
import pandas as pd
import requests 
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
URL = "https://sckyflvukpmdqmdzjzhs.supabase.co"
KEY = "sb_publishable_rAiegSkKYvM0Z9n7sUAI1w_WTgm1S4I" 
supabase: Client = create_client(URL, KEY)

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="STN Details", page_icon="🔄", layout="wide")

# --- 3. SESSION STATE FOR BUTTON NAVIGATION ---
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Pending'

def change_view(view_name):
    st.session_state.active_view = view_name

# --- 4. EXACT SIDEBAR & TOP BUTTON STYLING ---
st.markdown("""
    <style>
    /* Premium Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
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
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* Top 3 Navigation Buttons */
    div[data-testid="stMainBlockContainer"] div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        font-weight: 900 !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    div[data-testid="stMainBlockContainer"] div.stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #000000 !important;
    }
    div[data-testid="stMainBlockContainer"] div.stButton > button[kind="primary"] {
        border: 4px solid #000000 !important;
        background-color: #e2e8f0 !important;
    }
    
    [data-testid="stDataFrame"] th { background-color: #000000 !important; color: white !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# Smart Column Matcher
def get_actual_col(df_columns, possible_names):
    cleaned_cols = {str(col).strip().lower().replace("_", " "): col for col in df_columns}
    for p in possible_names:
        p_clean = p.strip().lower().replace("_", " ")
        if p_clean in cleaned_cols:
            return cleaned_cols[p_clean]
    return None

st.markdown("<h2 style='color: #000000; margin-bottom: 20px;'>🔄 STN Details & Processing</h2>", unsafe_allow_html=True)

# =====================================================================
# 🎛️ TOP NAVIGATION BUTTONS
# =====================================================================
col1, col2, col3, empty_space = st.columns([1, 1, 1, 4])

with col1:
    if st.button("1. STN Pending", type="primary" if st.session_state.active_view == 'Pending' else "secondary", use_container_width=True):
        change_view('Pending')
        st.rerun()
        
with col2:
    if st.button("2. STN Closed", type="primary" if st.session_state.active_view == 'Closed' else "secondary", use_container_width=True):
        change_view('Closed')
        st.rerun()
        
with col3:
    if st.button("3. Material Return", type="primary" if st.session_state.active_view == 'Return' else "secondary", use_container_width=True):
        change_view('Return')
        st.rerun()

st.markdown("<hr style='border: 1px solid #cbd5e1; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# =====================================================================
# ⏳ VIEW 1: STN PENDING LOGIC
# =====================================================================
if st.session_state.active_view == 'Pending':
    search_query = st.text_input("🔍 Search within Pending STN", placeholder="Enter Project ID, Site Name, etc...")
    
    wh_data = []
    try:
        res = supabase.table("warehouse_data").select("*").execute()
        if res.data:
            wh_data = res.data
    except Exception:
        try:
            headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
            r = requests.get(f"{URL}/rest/v1/warehouse_data?select=*", headers=headers)
            if r.status_code == 200:
                wh_data = r.json()
        except Exception as e:
            st.error(f"Fetch Error: {e}")

    if wh_data:
        df = pd.DataFrame(wh_data)
        
        stn_status_col = get_actual_col(df.columns, ["stn_status", "stn status", "STN Status"])
        mat_status_col = get_actual_col(df.columns, ["material_status", "material status", "Material Status"])
        
        col_map = {
            "Project ID": get_actual_col(df.columns, ["project_id", "project id", "Project ID"]),
            "Site ID": get_actual_col(df.columns, ["site_id", "site id", "Site ID"]),
            "Site Name": get_actual_col(df.columns, ["site_name", "site name", "Site Name"]),
            "Cluster": get_actual_col(df.columns, ["cluster", "Cluster"]),
            "ITEM DESCRIPTION": get_actual_col(df.columns, ["item_description", "item description", "description", "Item Description"]),
            "Qty": get_actual_col(df.columns, ["qty", "quantity", "indus qty", "indus_qty", "Indus Qty"]),
            "Team Name": get_actual_col(df.columns, ["team_name", "team name", "team", "Team"])
        }
        
        if stn_status_col and mat_status_col:
            # EXACT FILTERING: Material Status = Dispatched AND STN Status = Required
            df_filtered = df[
                (df[mat_status_col].astype(str).str.strip().str.lower() == 'dispatched') & 
                (df[stn_status_col].astype(str).str.strip().str.lower() == 'required')
            ].copy()
            
            if not df_filtered.empty:
                if search_query:
                    search_mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                    df_filtered = df_filtered[search_mask]
                
                display_df = pd.DataFrame()
                for display_name, actual_col in col_map.items():
                    display_df[display_name] = df_filtered[actual_col] if actual_col else "N/A"
                        
                c_stats, c_down = st.columns([3, 1])
                c_stats.success(f"✅ Showing {len(display_df)} Pending STN Record(s)")
                
                tsv_data = display_df.to_csv(index=False, sep='\t').encode('utf-8')
                c_down.download_button("📥 Download TSV File", data=tsv_data, file_name="STN_Pending.tsv", mime="text/tab-separated-values", use_container_width=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("⚠️ Aisi koi row nahi mili jiska Material Status 'Dispatched' aur STN Status 'Required' dono ho.")
        else:
            st.error("⚠️ Table me 'STN Status' ya 'Material Status' columns nahi mile.")
            st.write(list(df.columns))
            
    else:
        st.warning("⚠️ Table 'warehouse_data' me abhi koi data nahi mila.")

# =====================================================================
# ✅ VIEW 2: STN CLOSED LOGIC
# =====================================================================
elif st.session_state.active_view == 'Closed':
    st.info("🚀 STN Closed - Yahan aage ka logic aayega.")

# =====================================================================
# 🔙 VIEW 3: MATERIAL RETURN LOGIC
# =====================================================================
elif st.session_state.active_view == 'Return':
    st.info("🔙 Fresh Material Return - Yahan aage ka logic aayega.")
