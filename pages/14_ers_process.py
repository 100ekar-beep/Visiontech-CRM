import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client
from st_keyup import st_keyup

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="ERS Process Data", page_icon="🧾", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'action' not in st.session_state:
    st.session_state.action = ""

# --- 2. LAVISH CUSTOM CSS (Same as your Master Page) ---
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
    
    div.stButton > button p, 
    div.stButton > button span, 
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    
    /* FIX FOR DIALOG TITLE AND CAPTION COLOR */
    div[data-testid="stDialog"] h1, 
    div[data-testid="stDialog"] h2, 
    div[data-testid="stDialog"] h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
    div[data-testid="stDialog"] p {
        color: #e2e8f0 !important; 
    }
    div[data-testid="stDialog"] button[kind="icon"] svg {
        fill: #ffffff !important; 
    }

    .modal-section-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
    }
    
    /* FIX FOR FIELD LABELS COLOR */
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* Fixed Force Scrolling Table */
    .st-key-ers_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important; 
        padding: 0px 0 !important;
    }
    .st-key-ers_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1200px !important; 
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 8px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-ers_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    .st-key-ers_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; 
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-ers_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    
    .st-key-ers_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    .st-key-ers_table_wrap .tbl-cell {
        color: #e2e8f0;
        font-size: 0.9rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-ers_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') != 'VISPL':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye page exclusively **VISPL** workspace ke liye available hai.")
    st.stop()

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"] 

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- DIALOGS (POP-UPS) ---

@st.dialog("📄 Add ERS Record", width="large")
def add_ers_dialog():
    st.caption("Add a single ERS Process data entry")
    
    with st.container():
        st.markdown('<div class="modal-section-title">ERS INFORMATION</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("Date")
        with c2:
            ers_num = st.text_input("ERS Number *", placeholder="Enter ERS Number")
            
        c3, c4 = st.columns(2)
        with c3:
            po_num = st.text_input("PO Number", placeholder="Enter PO Number")
        with c4:
            tally_inv = st.text_input("Tally Invoice Number", placeholder="Enter Tally Invoice No.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Record", type="primary", use_container_width=True):
            if not ers_num:
                st.error("⚠️ ERS Number dalna compulsory hai!")
            else:
                insert_data = {
                    "date": date_val.strftime("%d-%m-%Y") if date_val else "",
                    "ers_number": ers_num.strip(),
                    "po_number": po_num.strip(),
                    "tally_invoice_number": tally_inv.strip()
                }
                try:
                    supabase.table("ERSprocess").insert(insert_data).execute()
                    st.success("✅ Record Successfully Added!")
                    st.session_state.current_page = 1 
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving Data: {e}")

@st.dialog("📤 Bulk Upload ERS Data", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel (.xlsx) file to bulk import ERS records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "csv"], key="bulk_ers_file")
    
    if uploaded_file:
        if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file)
                
                # Standardizing column names for matching
                df_upload.columns = [str(c).strip() for c in df_upload.columns]
                
                bulk_data = []
                for index, row in df_upload.iterrows():
                    ers_no = str(row.get("ERS Number", row.get("ers_number", ""))).strip()
                    if not ers_no or ers_no.lower() == "nan":
                        continue
                        
                    po_no = str(row.get("PO Number", row.get("po_number", ""))).strip()
                    if po_no.endswith(".0"): po_no = po_no[:-2]
                    
                    bulk_data.append({
                        "date": str(row.get("Date", row.get("date", ""))).strip(),
                        "ers_number": ers_no,
                        "po_number": po_no,
                        "tally_invoice_number": str(row.get("Tally Invoice Number", row.get("tally_invoice_number", ""))).strip()
                    })
                
                if bulk_data:
                    # Using UPSERT so duplicates update instead of crashing
                    supabase.table('ERSprocess').upsert(bulk_data).execute()
                    st.success(f"✅ Bulk Upload Complete! {len(bulk_data)} records added/updated successfully.")
                    st.session_state.current_page = 1
                    st.rerun()
                else:
                    st.warning("⚠️ No valid data found in the file.")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

@st.dialog("📥 Export Data", width="large")
def export_dialog(df_export):
    st.caption("Download your live ERS database records as an Excel file.")
    export_df = df_export.copy()
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    # Standardize column names for export
    export_df.rename(columns={
        "date": "Date", 
        "ers_number": "ERS Number", 
        "po_number": "PO Number", 
        "tally_invoice_number": "Tally Invoice Number"
    }, inplace=True)
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='ERS Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="ERS_Process_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- TOP BANNER ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #10b981 0%, #3b82f6 50%, #6366f1 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🧾 ERS PROCESS HUB
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 4. TOP ACTION BAR ---
col_title, col_ref, col_add, col_upload, col_export = st.columns([3.5, 1.5, 1.5, 1.5, 2])
with col_title:
    pass # Empty space for alignment
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun() 
with col_add:
    if st.button("➕ Add ERS", use_container_width=True):
        add_ers_dialog() 
with col_upload:
    if st.button("📤 Bulk Upload", use_container_width=True):
        bulk_upload_dialog() 
with col_export:
    if st.button("📥 Export Database", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH DATA ---
try:
    response = supabase.table("ERSprocess").select("*").order('id', desc=True).execute()
    data = response.data
except Exception:
    data = []

columns_list = ["id", "date", "ers_number", "po_number", "tally_invoice_number"]

if data:
    df = pd.DataFrame(data)
    for col in columns_list:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=columns_list)

# --- EXPORT LOGIC TRIGGER ---
if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 5.5 LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ ERS Database Records")
with col_search:
    search_query = st_keyup("Search", placeholder="🔍 Search records...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- 6. PAGINATION LOGIC ---
rows_per_page = 15
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages
elif st.session_state.current_page < 1:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page
df_page = df.iloc[start_idx:end_idx].copy()

# --- 7. PROPER BORDERED TABLE ---
COL_RATIOS = [0.5, 1.5, 2.5, 2.0, 2.5]
COL_LABELS = ["#", "DATE", "ERS NUMBER", "PO NUMBER", "TALLY INVOICE NUMBER"]

with st.container(key="ers_table_wrap", height=600):
    if df_page.empty:
        st.info("No ERS records found.")
    else:
        # Header
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)

        # Rows
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            serial_no = start_idx + page_pos + 1
            rcols = st.columns(COL_RATIOS)

            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            rcols[1].markdown(f"<div class='tbl-cell'>{row.get('date','') or '-'}</div>", unsafe_allow_html=True)
            rcols[2].markdown(f"<div class='tbl-cell' style='color:#60a5fa; font-weight:bold;'>{row.get('ers_number','') or '-'}</div>", unsafe_allow_html=True)
            rcols[3].markdown(f"<div class='tbl-cell'>{row.get('po_number','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell' style='color:#4ade80;'>{row.get('tally_invoice_number','') or '-'}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 1)):
        st.session_state.current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages)):
        st.session_state.current_page += 1
        st.rerun()
