import streamlit as st
import pandas as pd
import requests 
import time
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

# --- 4. LAVISH CUSTOM CSS FOR BUTTONS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* BIG, LAVISH CUSTOM BUTTON STYLING */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        border-radius: 15px !important;
        border: 3px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #475569 !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    
    /* Hover effect for all buttons */
    div.stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(0,0,0,0.1) !important;
        border-color: #94a3b8 !important;
    }

    /* ACTIVE BUTTON (PRIMARY) - VERY COLORFUL */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 8px 20px rgba(255, 65, 108, 0.4) !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2) !important;
    }
    
    /* Dataframe and Inputs */
    [data-testid="stDataFrame"] th { background-color: #1E3A8A !important; color: white !important; font-weight: 700 !important; }
    div[data-testid="stTextInput"] div[data-baseweb="input"] { border: 2px solid #cbd5e1 !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

# Helper function
def get_actual_col(df_columns, possible_names):
    for col in df_columns:
        if str(col).strip().lower() in [p.lower() for p in possible_names]:
            return col
    return None

st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 20px;'>🔄 STN Details & Processing</h1>", unsafe_allow_html=True)

# =====================================================================
# 🎛️ TOP NAVIGATION BUTTONS
# =====================================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⏳ 1. STN Pending", type="primary" if st.session_state.active_view == 'Pending' else "secondary"):
        change_view('Pending')
        st.rerun()
        
with col2:
    if st.button("✅ 2. STN Closed", type="primary" if st.session_state.active_view == 'Closed' else "secondary"):
        change_view('Closed')
        st.rerun()
        
with col3:
    if st.button("🔙 3. Material Return", type="primary" if st.session_state.active_view == 'Return' else "secondary"):
        change_view('Return')
        st.rerun()

st.markdown("<hr style='border: 2px solid #cbd5e1; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# =====================================================================
# ⏳ VIEW 1: STN PENDING LOGIC
# =====================================================================
if st.session_state.active_view == 'Pending':
    st.markdown("### ⏳ Pending STN Records")
    search_query = st.text_input("🔍 Search within Pending STN", placeholder="Enter Project ID, Site Name, etc...")
    
    # ADVANCED FETCH WITH ERROR TRACING
    wh_data = []
    error_msg = ""
    
    try:
        # Native Supabase Call
        res = supabase.table("warehouse_data").select("*").execute()
        if res.data:
            wh_data = res.data
    except Exception as e:
        error_msg += f"Supabase Client Error: {e} | "
        # Direct REST API Fallback
        try:
            headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept-Profile": "public"}
            r = requests.get(f"{URL}/rest/v1/warehouse_data?select=*", headers=headers)
            if r.status_code == 200:
                wh_data = r.json()
            else:
                error_msg += f"REST API Error: Code {r.status_code}, Msg: {r.text}"
        except Exception as ex:
            error_msg += f"Fallback Request Error: {ex}"

    if wh_data:
        df = pd.DataFrame(wh_data)
        
        # Checking Columns
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
        id_col = get_actual_col(df.columns, ["id", "uuid", "uid"])
        
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
                
                csv_data = display_df.to_csv(index=False).encode('utf-8')
                c_down.download_button("📥 Download Excel", data=csv_data, file_name="STN_Pending.csv", mime="text/csv", use_container_width=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("⚠️ Data table me hai, par 'Required' aur 'Dispatched' status match hone wala koi record nahi mila.")
        else:
            st.error("⚠️ Data aa gaya hai, par Table me 'STN Status' ya 'Material Status' columns nahi mile. Spelings check karein.")
            st.write("Aapke current table ke columns ye hain:", list(df.columns))
            
    else:
        st.error("❌ Data fetch nahi ho paya. Kripya Supabase SQL Editor me jake `NOTIFY pgrst, 'reload schema';` run karein.")
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
