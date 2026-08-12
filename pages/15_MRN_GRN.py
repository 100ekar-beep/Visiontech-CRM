import streamlit as st
import pandas as pd
import math
import io
import json
import random
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MRN / GRN Desk", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'mrn_current_page' not in st.session_state:
    st.session_state.mrn_current_page = 1
if 'mrn_action' not in st.session_state:
    st.session_state.mrn_action = ""

# --- 2. LAVISH CUSTOM CSS (Imported from your ecosystem) ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Top Action Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Pagination Text & Button Font Color Fix */
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    div.stButton > button p, div.stButton > button span, div.stButton > button div { color: #ffffff !important; font-weight: 800 !important; }
    
    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #ffffff !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p { color: #e2e8f0 !important; }
    div[data-testid="stDialog"] button[kind="icon"] svg { fill: #ffffff !important; }

    .modal-section-title {
        color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;
        margin-top: 15px; margin-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 5px;
    }
    
    label p, label[data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px; }

    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important; font-weight: 700 !important; -webkit-text-fill-color: #000000 !important; background: #e2e8f0 !important;
    }

    /* Fixed Horizontal Scrolling Table */
    .st-key-site_table_wrap {
        background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px;
        overflow: auto !important; padding: 0px 0 !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1800px !important; align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important; padding: 6px 0 !important; flex-wrap: nowrap !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:hover { background: rgba(255,255,255,0.04); }
    .st-key-site_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; display: flex; align-items: center; justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-site_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-site_table_wrap .tbl-head {
        background: transparent; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px;
        color: #94a3b8; text-transform: uppercase; white-space: nowrap !important;
    }
    .st-key-site_table_wrap .tbl-cell {
        color: #e2e8f0; font-size: 0.86rem; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    
    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"        
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- HELPER FUNCTIONS ---
def fetch_mrn_data():
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("mrn_data").select("*").eq("workspace", ws).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def fetch_project_ids():
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        # ---> FIXED: Added .limit(100000) to fetch ALL project IDs <---
        res = supabase.table("site_data").select("Project ID").eq("workspace", ws).limit(100000).execute()
        if res.data:
            pids = [str(x["Project ID"]).strip() for x in res.data if x.get("Project ID") and str(x.get("Project ID")).strip() != "" and str(x.get("Project ID")).strip().lower() != "nan"]
            return ["Select Project ID"] + list(dict.fromkeys(pids))
    except:
        pass
    return ["Select Project ID"]

def fetch_project_details(proj_id):
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("site_data").select("*").eq("Project ID", proj_id).eq("workspace", ws).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return {}

def fetch_team_percentage(team_name):
    # As per logic: fetch from team_master. Return 100 if not found.
    try:
        if team_name:
            res = supabase.table("team_master").select("percentage").eq("Team Name", team_name).execute()
            if res.data and res.data[0].get("percentage"):
                return float(res.data[0]["percentage"])
    except:
        pass
    return 100.0

def fetch_po_line_items(po_no):
    # Dummy structure logic assuming 'po_items' table exists. 
    # If it doesn't, it returns a blank DF matching the strict columns requested.
    try:
        res = supabase.table("po_items").select("*").eq("po_no", po_no).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except:
        pass
    # Fallback to empty standard structure
    return pd.DataFrame(columns=["PO Line No", "Item Code", "Item Description", "PO Qty", "PO Price"])


# --- 4. MRN ADD DIALOG ---
@st.dialog("📦 Create New MRN / GRN", width="large")
def add_mrn_dialog():
    st.caption("Generate a new Material Receipt Note (GRN) for the selected Project.")
    
    st.markdown('<div class="modal-section-title">🏢 PROJECT & SITE DETAILS</div>', unsafe_allow_html=True)
    
    proj_opts = fetch_project_ids()
    selected_proj = st.selectbox("SEARCH & SELECT PROJECT ID *", proj_opts)
    
    site_name, site_id, cluster, rfai_status, site_status, team_name = "", "", "", "", "", ""
    po_list = []
    team_percent = 100.0
    
    if selected_proj != "Select Project ID":
        proj_data = fetch_project_details(selected_proj)
        site_name = proj_data.get("Site Name", "")
        site_id = proj_data.get("Site ID", "")
        cluster = proj_data.get("Cluster", "")
        rfai_status = proj_data.get("RFAI Status", "")
        site_status = proj_data.get("Site Status", "")
        team_name = proj_data.get("Team Name", "")
        
        # Extract POs safely
        po_str = str(proj_data.get("PO No.", ""))
        if po_str and po_str.lower() != "nan":
            po_list = [p.strip() for p in po_str.split(",") if p.strip()]
            
        team_percent = fetch_team_percentage(team_name)

    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("SITE ID", value=site_id, disabled=True)
    with c2: st.text_input("SITE NAME", value=site_name, disabled=True)
    with c3: st.text_input("CLUSTER", value=cluster, disabled=True)
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("RFAI STATUS", value=rfai_status, disabled=True)
    with c5: st.text_input("SITE STATUS", value=site_status, disabled=True)
    with c6: st.text_input(f"TEAM NAME (Rate: {team_percent}%)", value=team_name, disabled=True)

    st.markdown('<div class="modal-section-title">📑 PO SELECTION & LINE ITEMS</div>', unsafe_allow_html=True)
    
    if not po_list and selected_proj != "Select Project ID":
        st.warning("⚠️ No POs found for this Project ID.")
        
    selected_pos = st.multiselect("SEARCH & SELECT PO(s)", po_list, placeholder="Choose one or multiple POs")
    
    grand_basic_total = 0.0
    all_po_dfs = {}
    
    for po in selected_pos:
        st.markdown(f"<p style='color:#3b82f6; font-weight:700; margin-top:15px;'>🛒 Processing PO: {po}</p>", unsafe_allow_html=True)
        
        df_po = fetch_po_line_items(po)
        
        # If no items found, populate with a blank editable row for demo/manual entry
        if df_po.empty:
            df_po = pd.DataFrame([{
                "PO Line No": "10", 
                "Item Code": "", 
                "Item Description": "", 
                "PO Qty": 1, 
                "PO Price": 0.0
            }])
            
        # Ensure column requirements
        df_display = pd.DataFrame()
        df_display["PO Line No"] = df_po.get("PO Line No", df_po.get("line_no", ["10"]*len(df_po)))
        df_display["Item Code"] = df_po.get("Item Code", df_po.get("item_code", [""]*len(df_po)))
        df_display["Item Description"] = df_po.get("Item Description", df_po.get("description", [""]*len(df_po)))
        df_display["PO Qty"] = pd.to_numeric(df_po.get("PO Qty", df_po.get("qty", [1]*len(df_po))), errors='coerce').fillna(0)
        
        # Add Custom Editable Fields
        df_display["User Qty"] = 0
        
        # Apply Logic: Adjusted Price = PO Price * (Team% / 100)
        original_price = pd.to_numeric(df_po.get("PO Price", df_po.get("price", [0.0]*len(df_po))), errors='coerce').fillna(0)
        df_display["Adjusted Rate"] = original_price * (team_percent / 100.0)
        df_display["Line Total"] = 0.0
        
        editor_key = f"editor_po_{po}"
        
        edited_df = st.data_editor(
            df_display,
            key=editor_key,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PO Line No": st.column_config.TextColumn("LINE NO", disabled=True),
                "Item Code": st.column_config.TextColumn("ITEM CODE", disabled=True),
                "Item Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
                "PO Qty": st.column_config.NumberColumn("PO QTY", disabled=True),
                "User Qty": st.column_config.NumberColumn("USER QTY", min_value=0, required=True),
                "Adjusted Rate": st.column_config.NumberColumn(f"RATE ({team_percent}%)", disabled=True, format="₹ %.2f"),
                "Line Total": st.column_config.NumberColumn("TOTAL", disabled=True, format="₹ %.2f"),
            }
        )
        
        # Calculate totals dynamically based on User Qty
        for idx, r in edited_df.iterrows():
            u_qty = pd.to_numeric(r["User Qty"], errors='coerce')
            u_qty = 0 if pd.isna(u_qty) else int(u_qty)
            rate = float(r["Adjusted Rate"])
            tot = u_qty * rate
            edited_df.at[idx, "Line Total"] = tot
            grand_basic_total += tot
            
        all_po_dfs[po] = edited_df

    st.markdown('<div class="modal-section-title">💳 BILLING SUMMARY</div>', unsafe_allow_html=True)
    
    gst_percent = 18.0
    gst_amount = grand_basic_total * (gst_percent / 100.0)
    final_amount = grand_basic_total + gst_amount
    
    c_b1, c_b2, c_b3 = st.columns(3)
    with c_b1:
        st.markdown(f"<h4 style='color:#94a3b8; font-size:1.1rem;'>Basic Amount:<br><span style='color:#fff;'>₹ {grand_basic_total:,.2f}</span></h4>", unsafe_allow_html=True)
    with c_b2:
        st.markdown(f"<h4 style='color:#94a3b8; font-size:1.1rem;'>GST (18%):<br><span style='color:#ef4444;'>+ ₹ {gst_amount:,.2f}</span></h4>", unsafe_allow_html=True)
    with c_b3:
        st.markdown(f"<h3 style='color:#3b82f6; font-size:1.4rem;'>Grand Total:<br>₹ {final_amount:,.2f}</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_save1, col_save2 = st.columns([8, 2])
    with col_save2:
        if st.button("💾 Generate MRN", type="primary", use_container_width=True):
            if selected_proj == "Select Project ID":
                st.error("⚠️ Please select a Project ID.")
                return
            if not selected_pos:
                st.error("⚠️ Please select at least one PO.")
                return
            if grand_basic_total <= 0:
                st.error("⚠️ User Qty must be greater than 0 to generate MRN.")
                return
                
            # Generate Unique 6 digit MRN
            new_mrn_no = f"MRN-{random.randint(100000, 999999)}"
            
            header_data = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "MRN Number": new_mrn_no,
                "Team Name": team_name,
                "Project ID": selected_proj,
                "Site ID": site_id,
                "Site Name": site_name,
                "Cluster": cluster,
                "Basic Amount": grand_basic_total,
                "GST Amount": gst_amount,
                "Total Amount": final_amount,
                "Date": datetime.date.today().strftime("%Y-%m-%d")
            }
            
            try:
                # Save Header
                supabase.table("mrn_data").insert(header_data).execute()
                
                # Save Items
                items_to_insert = []
                for po, d_df in all_po_dfs.items():
                    for _, row in d_df.iterrows():
                        u_qty = pd.to_numeric(row["User Qty"], errors='coerce')
                        if pd.notna(u_qty) and u_qty > 0:
                            items_to_insert.append({
                                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                                "MRN Number": new_mrn_no,
                                "PO Number": po,
                                "Item Code": str(row["Item Code"]),
                                "Description": str(row["Item Description"]),
                                "User Qty": int(u_qty),
                                "Rate": float(row["Adjusted Rate"]),
                                "Total": float(row["Line Total"])
                            })
                if items_to_insert:
                    try:
                        supabase.table("mrn_items").insert(items_to_insert).execute()
                    except Exception:
                        pass # Ignore if items table doesn't exist yet
                        
                st.success(f"✅ MRN Generated Successfully! ID: {new_mrn_no}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Generating MRN: {e}")

# --- 5. EXPORT DIALOG ---
@st.dialog("📥 Export MRN Data", width="large")
def export_dialog(df_export):
    st.caption("Download your MRN/GRN records as an Excel file.")
    export_df = df_export.copy()
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='MRN Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="MRN_GRN_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 6. TOP ACTION BAR ---
col_title, col_ref, col_add, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>📦 MRN / GRN Desk</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun() 
with col_add:
    if st.button("➕ Add New MRN", type="primary", use_container_width=True):
        add_mrn_dialog() 
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.mrn_action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. FETCH & PREPARE MRN DATA ---
df_mrn = fetch_mrn_data()

columns_list = [
    "id", "MRN Number", "Team Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Basic Amount", "GST Amount", "Total Amount", "Date"
]

if not df_mrn.empty:
    for col in columns_list:
        if col not in df_mrn.columns:
            df_mrn[col] = ""
else:
    df_mrn = pd.DataFrame(columns=columns_list)

# --- EXPORT LOGIC TRIGGER AFTER DF LOAD ---
if st.session_state.get('mrn_action') == "export":
    export_dialog(df_mrn)
    st.session_state.mrn_action = "" 

# --- 8. LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Generated MRN Records")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search MRN records...", label_visibility="collapsed")

if search_query and not df_mrn.empty:
    mask = df_mrn.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df_mrn = df_mrn[mask]

# --- 9. PAGINATION LOGIC (10 lines per page) ---
rows_per_page = 10
total_rows = len(df_mrn)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.mrn_current_page > total_pages:
    st.session_state.mrn_current_page = total_pages
elif st.session_state.mrn_current_page < 1:
    st.session_state.mrn_current_page = 1

start_idx = (st.session_state.mrn_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

df_page = df_mrn.iloc[start_idx:end_idx].copy()

# --- 10. MRN DATA TABLE ---
COL_RATIOS = [0.3, 1.2, 1.5, 1.5, 1.2, 1.5, 1.2, 1.0, 1.0, 1.2, 1.0]
COL_LABELS = ["#", "MRN NUMBER", "TEAM NAME", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC", "GST", "TOTAL", "DATE"]

with st.container(key="site_table_wrap", height=560):
    if df_page.empty:
        st.info("No MRN records found. Click '+ Add New MRN' to create one.")
    else:
        # HEADER ROW
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)

        # DATA ROWS
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            serial_no = start_idx + page_pos + 1

            rcols = st.columns(COL_RATIOS)
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            rcols[1].markdown(f"<div class='tbl-cell' style='color:#3b82f6; font-weight:bold;'>{row_dict.get('MRN Number','') or '-'}</div>", unsafe_allow_html=True)
            rcols[2].markdown(f"<div class='tbl-cell'>{row_dict.get('Team Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            
            # Formatting financial data
            basic = pd.to_numeric(row_dict.get('Basic Amount', 0), errors='coerce')
            gst = pd.to_numeric(row_dict.get('GST Amount', 0), errors='coerce')
            tot = pd.to_numeric(row_dict.get('Total Amount', 0), errors='coerce')
            
            rcols[7].markdown(f"<div class='tbl-cell'>₹ {basic:,.2f}</div>", unsafe_allow_html=True)
            rcols[8].markdown(f"<div class='tbl-cell' style='color:#ef4444;'>₹ {gst:,.2f}</div>", unsafe_allow_html=True)
            rcols[9].markdown(f"<div class='tbl-cell' style='color:#10b981; font-weight:bold;'>₹ {tot:,.2f}</div>", unsafe_allow_html=True)
            rcols[10].markdown(f"<div class='tbl-cell'>{row_dict.get('Date','') or '-'}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 11. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.mrn_current_page == 1)):
        st.session_state.mrn_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.mrn_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.mrn_current_page == total_pages)):
        st.session_state.mrn_current_page += 1
        st.rerun()
