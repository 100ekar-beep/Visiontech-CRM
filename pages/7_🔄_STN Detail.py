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

# --- 4. EXACT STYLING AS REQUESTED ---
st.markdown("""
    <style>
    /* White box, Dark Black Border, Black Bold Text */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        font-weight: 900 !important; /* Extra Bold */
        border-radius: 6px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Hover effect */
    div.stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #000000 !important;
    }

    /* Active Button styling (Slightly thicker border to show it's active) */
    div.stButton > button[kind="primary"] {
        border: 4px solid #000000 !important;
        background-color: #e2e8f0 !important;
    }
    
    /* Dataframe and Inputs */
    [data-testid="stDataFrame"] th { background-color: #000000 !important; color: white !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# Helper function
def get_actual_col(df_columns, possible_names):
    for col in df_columns:
        if str(col).strip().lower() in [p.lower() for p in possible_names]:
            return col
    return None

st.markdown("<h2 style='color: #000000; margin-bottom: 20px;'>🔄 STN Details & Processing</h2>", unsafe_allow_html=True)

# =====================================================================
# 🎛️ TOP NAVIGATION BUTTONS (BAJU-BAJU ALIGNMENT)
# =====================================================================
# Added a 4th empty column taking up remaining space so buttons stay close to each other on the left
col1, col2, col3, empty_space = st.columns([1.5, 1.5, 1.5, 5])

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
    error_msg = ""
    
    # 💡 SMART FETCH: Handling the Supabase Cache Error automatically
    try:
        # Attempt 1: Try the new table name
        res = supabase.table("warehouse_data").select("*").execute()
        wh_data = res.data
    except Exception as e:
        error_msg += f"Attempt 1 Failed: {e} | "
        if "Indus Data" in str(e) or "PGRST205" in str(e):
            try:
                # Attempt 2: Fallback to the cached table name Supabase is asking for
                res = supabase.table("Indus Data").select("*").execute()
                wh_data = res.data
            except Exception as e2:
                error_msg += f"Attempt 2 (Indus Data) Failed: {e2}"

    if wh_data:
        df = pd.DataFrame(wh_data)
        
        stn_status_col = get_actual_col(df.columns, ["stn_status", "stn status", "stnstatus"])
        mat_status_col = get_actual_col(df.columns, ["material_status", "material status", "materialstatus"])
        
        col_map = {
            "Project ID": get_actual_col(df.columns, ["project_id", "project id"]),
            "Site ID": get_actual_col(df.columns, ["site_id", "site id"]),
            "Site Name": get_actual_col(df.columns, ["site_name", "site name"]),
            "Cluster": get_actual_col(df.columns, ["cluster"]),
            "ITEM DESCRIPTION": get_actual_col(df.columns, ["item_description", "item description", "description"]),
            "Qty": get_actual_col(df.columns, ["qty", "quantity"]),
            "Team Name": get_actual_col(df.columns, ["team_name", "team name"])
        }
        
        if stn_status_col and mat_status_col:
            df_filtered = df[
                (df[stn_status_col].astype(str).str.strip().str.lower() == 'required') & 
                (df[mat_status_col].astype(str).str.strip().str.lower() == 'dispatched')
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
                
                # USER CORRECTION APPLIED: Handling .tsv file extension instead of .csv
                tsv_data = display_df.to_csv(index=False, sep='\t').encode('utf-8')
                c_down.download_button("📥 Download TSV File", data=tsv_data, file_name="STN_Pending.tsv", mime="text/tab-separated-values", use_container_width=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("⚠️ Data table me hai, par 'Required' aur 'Dispatched' status match hone wala koi record nahi mila.")
        else:
            st.error("⚠️ Data aa gaya hai, par Table me 'STN Status' ya 'Material Status' columns nahi mile.")
            st.write("Aapke current table ke columns ye hain:", list(df.columns))
            
    else:
        st.error("❌ Data fetch nahi ho paya. Auto-fallback ne bhi kaam nahi kiya.")
        if error_msg:
            st.code(error_msg, language="bash")

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
