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

# --- 3. CLEAN & SAFE CSS (Sidebar ko disturb nahi karegi) ---
st.markdown("""
    <style>
    /* Sirf Dataframe header ko style karenge */
    [data-testid="stDataFrame"] th { background-color: #000000 !important; color: white !important; font-weight: 700 !important; }
    
    /* Tabs ki formatting ko bold aur black karenge (Standard Style) */
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 17px !important;
        color: #000000 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom-color: #000000 !important;
        background-color: #f8fafc !important;
    }
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
# 🗂️ STANDARD TABS NAVIGATION
# =====================================================================
tab1, tab2, tab3 = st.tabs(["1. STN Pending", "2. STN Closed", "3. Material Return"])

# =====================================================================
# ⏳ TAB 1: STN PENDING LOGIC
# =====================================================================
with tab1:
    search_query = st.text_input("🔍 Search within Pending STN", placeholder="Enter Project ID, Site Name, etc...")
    
    wh_data = []
    error_msg = ""
    
    # 💡 SMART FETCH: Handling the Supabase Cache Error automatically
    try:
        res = supabase.table("warehouse_data").select("*").execute()
        wh_data = res.data
    except Exception as e:
        error_msg += f"Attempt 1 Failed: {e} | "
        if "Indus Data" in str(e) or "PGRST205" in str(e):
            try:
                # Cache Bypass: Purane table naam se uthayega
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
                
                # Downloading in strictly .tsv format as previously requested
                tsv_data = display_df.to_csv(index=False, sep='\t').encode('utf-8')
                c_down.download_button("📥 Download TSV File", data=tsv_data, file_name="STN_Pending.tsv", mime="text/tab-separated-values", use_container_width=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("⚠️ Data table me hai, par 'Required' aur 'Dispatched' status match hone wala koi record nahi mila.")
        else:
            st.error("⚠️ Data aa gaya hai, par Table me 'STN Status' ya 'Material Status' columns nahi mile.")
            st.write("Current columns:", list(df.columns))
            
    else:
        st.error("❌ Data fetch nahi ho paya. Auto-fallback ne bhi kaam nahi kiya.")
        if error_msg:
            st.code(error_msg, language="bash")

# =====================================================================
# ✅ TAB 2: STN CLOSED LOGIC
# =====================================================================
with tab2:
    st.info("🚀 STN Closed - Data yahan dikhega.")

# =====================================================================
# 🔙 TAB 3: MATERIAL RETURN LOGIC
# =====================================================================
with tab3:
    st.info("🔙 Fresh Material Return - Data yahan dikhega.")
