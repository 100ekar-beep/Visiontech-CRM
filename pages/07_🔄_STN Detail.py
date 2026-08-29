import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="STN Details", page_icon="🔄", layout="wide")

# --- 2. SUPABASE CONNECTION ---
# FIX: Ab hardcoded URL/Key ki jagah st.secrets se liya jaa raha hai — isse
# ek hi jagah (Streamlit Cloud Secrets) update karke sabhi pages naye
# Supabase project se automatically connect ho jaate hain.
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase connection error: {e}")
        return None

supabase: Client = init_connection()

# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: cached warehouse_data fetch ---
# ⚠️ BADI WAJAH: pehle teeno tabs (Pending / Closed / Return) apni
# apni ALAG, BINA CACHING wali query chalate the — aur Streamlit ke
# rerun-on-every-interaction model ki wajah se yeh har keystroke
# (search box), har dialog open/close, har button click par poori
# 'warehouse_data' table dobara Supabase se download kar rahe the.
# Ab ek hi cached fetch (30s) sabhi teeno tabs ke liye reuse hota hai,
# aur Closed/Return tabs bhi isi cached data ko locally Python me
# filter karte hain instead of alag query chalane ke.
# -------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_warehouse_data_cached(workspace):
    try:
        response = supabase.table("warehouse_data").select("*").eq("workspace", workspace).execute()
        return response.data if response.data else []
    except Exception:
        return []

def clear_stn_cache():
    """Call this right before st.rerun() after any insert/update/delete on warehouse_data."""
    fetch_warehouse_data_cached.clear()

# --- 3. SESSION STATE FOR TAB NAVIGATION ---
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Pending'
if 'stn_current_page' not in st.session_state:
    st.session_state.stn_current_page = 1

def change_view(view_name):
    st.session_state.active_view = view_name
    st.session_state.stn_current_page = 1

# --- 4. STYLING ---
st.markdown("""
    <style>
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
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* Top 3 Tab Buttons */
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

    /* Table wrapper */
    .st-key-stn_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,0,0,0.15);
        border-radius: 10px;
        overflow: auto !important;
        padding: 0px 0 !important;
    }
    .st-key-stn_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1400px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(0,0,0,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-stn_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(59,130,246,0.06);
    }
    .st-key-stn_table_wrap div[data-testid="column"] {
        padding: 0 15px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(0,0,0,0.06);
    }
    .st-key-stn_table_wrap div[data-testid="column"]:last-child { border-right: none; }

    .st-key-stn_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #334155;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    .st-key-stn_table_wrap .tbl-cell {
        color: #0f172a;
        font-size: 0.88rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-stn_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    .st-key-stn_table_wrap button {
        height: 32px !important;
        width: 100% !important;
        max-width: 34px !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        margin: 0 auto !important;
    }
    div[class*="st-key-svbtn_"] button { background: rgba(34,197,94,0.15) !important; border: 1px solid rgba(34,197,94,0.3) !important; }
    div[class*="st-key-sebtn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-sdbtn_"] button { background: rgba(239,68,68,0.15) !important; border: 1px solid rgba(239,68,68,0.3) !important; }

    .page-count { text-align: center; font-size: 1.05rem; font-weight: 600; color: #334155; margin-top: 10px; }
    [data-testid="stDataFrame"] th { background-color: #000000 !important; color: white !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 5. HELPERS ---
def get_actual_col(df_columns, possible_names):
    cleaned_cols = {str(col).strip().lower().replace("_", " "): col for col in df_columns}
    for p in possible_names:
        p_clean = p.strip().lower().replace("_", " ")
        if p_clean in cleaned_cols:
            return cleaned_cols[p_clean]
    return None

@st.dialog("👁️ View STN Record", width="large")
def view_stn_dialog(row_data):
    st.caption("Read-only preview of this record")
    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True)
    with c2: st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True)
    with c3: st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True)

    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True)
    with c5: st.text_input("TEAM NAME", value=row_data.get('Team', ''), disabled=True)
    with c6: st.text_input("QTY", value=str(row_data.get('Indus Qty', '')), disabled=True)

    st.text_input("ITEM DESCRIPTION", value=row_data.get('Item Description', ''), disabled=True)

    c7, c8 = st.columns(2)
    with c7: st.text_input("STN STATUS", value=row_data.get('STN Status', ''), disabled=True)
    with c8: st.text_input("MATERIAL STATUS", value=row_data.get('Material Status', ''), disabled=True)

    if st.button("Close", use_container_width=True):
        st.rerun()

# --- EDIT DIALOG WITH NEW SHIFTING DROPDOWN ---
@st.dialog("✏️ Edit STN Record", width="large")
def edit_stn_dialog(row_data):
    st.caption("Update this warehouse/STN record")

    c1, c2, c3 = st.columns(3)
    with c1: proj_id = st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True)
    with c2: site_id = st.text_input("SITE ID", value=row_data.get('Site ID', ''))
    with c3: site_name = st.text_input("SITE NAME", value=row_data.get('Site Name', ''))

    c4, c5, c6 = st.columns(3)
    with c4: cluster = st.text_input("CLUSTER", value=row_data.get('Cluster', ''))
    with c5: team = st.text_input("TEAM NAME", value=row_data.get('Team', ''))
    with c6: qty = st.number_input("QTY", value=int(row_data.get('Indus Qty') or 0), min_value=0)

    item_desc = st.text_input("ITEM DESCRIPTION", value=row_data.get('Item Description', ''))

    c7, c8 = st.columns(2)
    with c7:
        stn_status = st.selectbox("STN STATUS", ["Required", "Not Required", "Closed"],
                                   index=["Required", "Not Required", "Closed"].index(row_data.get('STN Status')) if row_data.get('STN Status') in ["Required", "Not Required", "Closed"] else 0)
    with c8:
        material_status = st.selectbox("MATERIAL STATUS", ["Dispatched", "Pending", "Received"],
                                        index=["Dispatched", "Pending", "Received"].index(row_data.get('Material Status')) if row_data.get('Material Status') in ["Dispatched", "Pending", "Received"] else 0)

    # 🌟 NEW DROPDOWN REQUIREMENT ADDED HERE
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700; color:#0f172a; margin-bottom:5px;'>🔄 SHIFT / ACTION STATUS</p>", unsafe_allow_html=True)
    
    action_options = ["-- Select Action --", "STN Closed", "Fresh Material return to WH"]
    selected_action = st.selectbox("Select action to shift record", action_options, label_visibility="collapsed")

    if st.button("💾 Update Record", type="primary", use_container_width=True):
        try:
            update_dict = {
                "Site ID": site_id,
                "Site Name": site_name,
                "Cluster": cluster,
                "Team": team,
                "Indus Qty": qty,
                "Item Description": item_desc,
                "STN Status": stn_status,
                "Material Status": material_status
            }

            # If user selected an action, automatically adjust fields to shift tabs
            if selected_action == "STN Closed":
                update_dict["STN Status"] = "Closed"
            elif selected_action == "Fresh Material return to WH":
                update_dict["Material Status"] = "Returned" # Or adjust according to your table schema if needed

            supabase.table("warehouse_data").update(update_dict).eq("id", row_data['id']).execute()
            st.success("✅ Record Updated and Shifted Successfully!")
            clear_stn_cache()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error updating record: {e}")

@st.dialog("📥 Export STN Data", width="large")
def export_stn_dialog(export_df):
    st.caption("Download filtered STN Pending records as Excel file.")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='STN Pending')
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="STN_Pending_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 6. HEADER ---
st.markdown("<h2 style='color:#000000; margin-bottom:20px;'>🔄 STN Details & Processing</h2>", unsafe_allow_html=True)

# --- 7. TOP NAVIGATION TABS ---
col1, col2, col3, empty_space = st.columns([1, 1, 1, 4])
with col1:
    if st.button("1. STN Pending", type="primary" if st.session_state.active_view == 'Pending' else "secondary", use_container_width=True):
        change_view('Pending'); st.rerun()
with col2:
    if st.button("2. STN Closed", type="primary" if st.session_state.active_view == 'Closed' else "secondary", use_container_width=True):
        change_view('Closed'); st.rerun()
with col3:
    if st.button("3. Material Return", type="primary" if st.session_state.active_view == 'Return' else "secondary", use_container_width=True):
        change_view('Return'); st.rerun()

st.markdown("<hr style='border: 1px solid #cbd5e1; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- SHARED CACHED FETCH — used by all 3 tabs below (see fetch_warehouse_data_cached above) ---
active_ws = st.session_state.get('active_workspace', 'VISPL')
wh_data = fetch_warehouse_data_cached(active_ws)

# =====================================================================
# ⏳ VIEW 1: STN PENDING
# =====================================================================
if st.session_state.active_view == 'Pending':

    if wh_data:
        df_raw = pd.DataFrame(wh_data)

        stn_col = get_actual_col(df_raw.columns, ["STN Status", "stn_status"])
        mat_col = get_actual_col(df_raw.columns, ["Material Status", "material_status"])

        if stn_col and mat_col:
            # PENDING TAB: STN Status = Required AND Material Status = Dispatched
            df = df_raw[
                (df_raw[stn_col].astype(str).str.strip().str.lower() == 'required') &
                (df_raw[mat_col].astype(str).str.strip().str.lower() == 'dispatched')
            ].copy()
        else:
            st.error("⚠️ 'STN Status' ya 'Material Status' column table me nahi mila.")
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()
        st.warning("⚠️ 'warehouse_data' table se koi record nahi mila.")

    # --- Search box + Export button ---
    col_search, col_export = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("🔍 Search within Pending STN", placeholder="Enter Project ID, Site Name, etc...", label_visibility="collapsed")
    with col_export:
        export_clicked = st.button("📥 Export to Excel", use_container_width=True)

    if not df.empty and search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    st.markdown(f"<p style='color:#334155; font-weight:600; margin-top:10px;'>Showing {len(df)} Pending STN Record(s)</p>", unsafe_allow_html=True)

    if export_clicked:
        if not df.empty:
            export_stn_dialog(df)
        else:
            st.warning("⚠️ Export karne ke liye koi data nahi hai.")

    # --- Pagination ---
    rows_per_page = 10
    total_rows = len(df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
    if st.session_state.stn_current_page > total_pages:
        st.session_state.stn_current_page = total_pages
    elif st.session_state.stn_current_page < 1:
        st.session_state.stn_current_page = 1

    start_idx = (st.session_state.stn_current_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df.iloc[start_idx:end_idx].copy() if not df.empty else df

    COL_RATIOS = [0.3, 0.35, 0.35, 0.35, 1.2, 1.0, 1.5, 1.2, 2.2, 0.7, 1.2]
    COL_LABELS = ["#", "👁️", "✏️", "🗑️", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "ITEM DESCRIPTION", "QTY", "TEAM NAME"]

    with st.container(key="stn_table_wrap", height=560):
        if df_page.empty:
            st.info("⚠️ Koi Pending STN record nahi mila (STN Status = Required aur Material Status = Dispatched wali koi row nahi).")
        else:
            h_cols = st.columns(COL_RATIOS)
            for h_col, label in zip(h_cols, COL_LABELS):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                serial_no = start_idx + page_pos + 1

                rcols = st.columns(COL_RATIOS)
                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)

                with rcols[1]:
                    if st.button("👁️", key=f"svbtn_{rid}", help="View", use_container_width=True):
                        view_stn_dialog(row_dict)
                with rcols[2]:
                    if st.button("✏️", key=f"sebtn_{rid}", help="Edit", use_container_width=True):
                        edit_stn_dialog(row_dict)
                with rcols[3]:
                    if st.button("🗑️", key=f"sdbtn_{rid}", help="Delete", use_container_width=True):
                        st.session_state[f"stn_confirm_del_{rid}"] = True

                rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
                rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
                rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
                rcols[7].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
                rcols[8].markdown(f"<div class='tbl-cell'>{row_dict.get('Item Description','') or '-'}</div>", unsafe_allow_html=True)
                rcols[9].markdown(f"<div class='tbl-cell'>{row_dict.get('Indus Qty','') or '-'}</div>", unsafe_allow_html=True)
                rcols[10].markdown(f"<div class='tbl-cell'>{row_dict.get('Team','') or '-'}</div>", unsafe_allow_html=True)

                if st.session_state.get(f"stn_confirm_del_{rid}"):
                    wc1, wc2, wc3 = st.columns([6, 1, 1])
                    with wc1:
                        st.warning(f"Delete record for Site ID '{row_dict.get('Site ID','')}' / Item '{row_dict.get('Item Description','')}'? This cannot be undone.")
                    with wc2:
                        if st.button("✅ Confirm", key=f"stn_confirm_yes_{rid}", use_container_width=True):
                            try:
                                supabase.table("warehouse_data").delete().eq("id", rid).execute()
                                st.session_state[f"stn_confirm_del_{rid}"] = False
                                st.success("✅ Record Deleted!")
                                clear_stn_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting record: {e}")
                    with wc3:
                        if st.button("❌ Cancel", key=f"stn_confirm_no_{rid}", use_container_width=True):
                            st.session_state[f"stn_confirm_del_{rid}"] = False
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.stn_current_page == 1)):
            st.session_state.stn_current_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state.stn_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.stn_current_page == total_pages)):
            st.session_state.stn_current_page += 1
            st.rerun()

# =====================================================================
# ✅ VIEW 2: STN CLOSED (Filters records where STN Status = Closed)
# =====================================================================
elif st.session_state.active_view == 'Closed':
    st.markdown("### ✅ Closed STN Records")

    # FIX: pehle yahan alag se ek uncached query chalti thi. Ab shared
    # cached 'wh_data' (upar fetch hua) ko hi locally filter kar rahe hain.
    if wh_data:
        df_all = pd.DataFrame(wh_data)
        stn_col = get_actual_col(df_all.columns, ["STN Status", "stn_status"])
        if stn_col:
            df_closed = df_all[df_all[stn_col].astype(str).str.strip().str.lower() == 'closed'].copy()
        else:
            df_closed = pd.DataFrame()
    else:
        df_closed = pd.DataFrame()

    if not df_closed.empty:
        st.dataframe(df_closed, use_container_width=True, hide_index=True)
    else:
        st.info("No closed STN records found.")

# =====================================================================
# 🔙 VIEW 3: MATERIAL RETURN (Filters records where Material Status = Returned)
# =====================================================================
elif st.session_state.active_view == 'Return':
    st.markdown("### 🔙 Fresh Material Return to WH Records")

    # FIX: pehle yahan alag se ek uncached query chalti thi. Ab shared
    # cached 'wh_data' (upar fetch hua) ko hi locally filter kar rahe hain.
    if wh_data:
        df_all = pd.DataFrame(wh_data)
        mat_col = get_actual_col(df_all.columns, ["Material Status", "material_status"])
        if mat_col:
            df_ret = df_all[df_all[mat_col].astype(str).str.strip().str.lower() == 'returned'].copy()
        else:
            df_ret = pd.DataFrame()
    else:
        df_ret = pd.DataFrame()

    if not df_ret.empty:
        st.dataframe(df_ret, use_container_width=True, hide_index=True)
    else:
        st.info("No material return records found.")
