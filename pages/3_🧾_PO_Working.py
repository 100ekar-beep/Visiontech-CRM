import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="PO Working", page_icon="🧾", layout="wide")

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Primary Action Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Secondary Action Buttons (Like Cancel) */
    button[data-testid="baseButton-secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }

    button[data-testid="baseButton-primary"]:hover, 
    button[data-testid="baseButton-secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }

    /* Pagination Text & Button Font Color Fix */
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    
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

    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
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

    /* KPI PILLS FOR POPUP HEADER */
    .kpi-pill-container {
        display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;
    }
    .kpi-pill {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #cbd5e1;
        display: flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kpi-pill span {
        color: #60a5fa;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    /* =========================================================
       FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING (PO WORKING)
       ========================================================= */
    .st-key-po_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important; /* Enables both Horizontal & Vertical Scroll */
        padding: 0px 0 !important;
    }
    /* Force inner rows to be wide so they NEVER squish */
    .st-key-po_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1800px !important; /* Horizontal Scroll fix */
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-po_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    /* Cell padding and border */
    .st-key-po_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; 
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-po_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    
    .st-key-po_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    /* Strict nowrap with ellipsis to prevent column bleeding */
    .st-key-po_table_wrap .tbl-cell {
        color: #e2e8f0;
        font-size: 0.86rem;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.4;
        width: 100%;
    }
    .st-key-po_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    /* Fixed native Action Buttons strictly constrained to their columns */
    .st-key-po_table_wrap button {
        height: 32px !important;
        width: 100% !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important;
        pointer-events: auto !important; 
        cursor: pointer !important;
    }
    .st-key-po_table_wrap button:hover {
        background: #3b82f6 !important;
        border-color: #60a5fa !important;
        transform: translateY(-2px) !important;
    }

    /* ACTION COLUMNS MERGING & ALIGNMENT */
    .st-key-po_table_wrap div[data-testid="column"]:nth-child(1) {
        padding: 0 10px 0 15px !important;
    }
    .st-key-po_table_wrap div[data-testid="column"]:nth-child(2) .tbl-head,
    .st-key-po_table_wrap div[data-testid="column"]:nth-child(3) .tbl-head {
        color: #94a3b8; 
    }
    .st-key-po_table_wrap div[data-testid="column"]:nth-child(2) {
        padding: 4px 4px !important;
        border-right: none !important;
    }
    .st-key-po_table_wrap div[data-testid="column"]:nth-child(3) {
        padding: 4px 15px 4px 4px !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* Round, color-coded, compact action icon buttons */
    .st-key-po_table_wrap div[class*="st-key-vbtn_"] button,
    .st-key-po_table_wrap div[class*="st-key-dbtn_"] button {
        width: 100% !important; 
        max-width: 34px !important;
        height: 32px !important;
        padding: 0 !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
        margin: 0 auto !important;
    }
    div[class*="st-key-vbtn_"] button { background: rgba(34,197,94,0.15) !important; border: 1px solid rgba(34,197,94,0.3) !important; }
    div[class*="st-key-dbtn_"] button { background: rgba(239,68,68,0.15) !important; border: 1px solid rgba(239,68,68,0.3) !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2.5 SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- INITIALIZE SESSION STATE DIRECTLY FROM SUPABASE ---
if 'po_working_df' not in st.session_state:
    try:
        res = supabase.table("po_working").select("*").execute()
        if res.data and len(res.data) > 0:
            df_fetched = pd.DataFrame(res.data)
            num_cols = ['Line Number', 'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount']
            for col in num_cols:
                if col in df_fetched.columns:
                    df_fetched[col] = df_fetched[col].astype(str).str.replace(',', '', regex=True)
                    df_fetched[col] = pd.to_numeric(df_fetched[col], errors='coerce').fillna(0).astype(int)
            st.session_state.po_working_df = df_fetched
        else:
            st.session_state.po_working_df = pd.DataFrame(columns=[
                'id', 'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
                'Item Num', 'Description', 'UOM', 'PO Qty', 
                'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
            ])
    except Exception:
        st.session_state.po_working_df = pd.DataFrame(columns=[
            'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
            'Item Num', 'Description', 'UOM', 'PO Qty', 
            'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
        ])

if 'id' not in st.session_state.po_working_df.columns:
    st.session_state.po_working_df['id'] = None

# --- 3. UPLOAD ORACLE PO DIALOG FUNCTION ---
@st.dialog("📄 Upload PO (Notepad)")
def po_upload_dialog():
    st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#cbd5e1; margin-bottom:5px; margin-top:5px;'>PO NUMBER <span style='color:#ef4444;'>*</span></p>", unsafe_allow_html=True)
    po_number_input = st.text_input("PO NUMBER", label_visibility="collapsed", placeholder="Enter PO Number...")
    
    st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#cbd5e1; margin-bottom:5px; margin-top:15px;'>PO DOCUMENT (TXT/CSV/TSV/EXCEL) <span style='color:#ef4444;'>*</span></p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("PO DOCUMENT", label_visibility="collapsed", type=["tsv", "csv", "txt", "xlsx"], key="po_upload_file")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_cancel, col_submit = st.columns(2)
    with col_cancel:
        cancel_btn = st.button("Cancel", use_container_width=True)
    with col_submit:
        submit_btn = st.button("💾 Submit", type="primary", use_container_width=True)
        
    if cancel_btn:
        st.rerun()
        
    if submit_btn:
        if not po_number_input.strip():
            st.error("⚠️ PO Number dalna compulsory hai!")
        elif not uploaded_file:
            st.error("⚠️ File upload karna compulsory hai!")
        else:
            try:
                df_raw = pd.read_csv(uploaded_file, sep='\t', encoding='cp1252', skiprows=8)
                
                cols_to_drop = [
                    'Type', 'Type.1', 'Item/Job', 'Supplier Item', 'Type.2', 
                    'Advance Amount', 'Advance Billed', 'Maximum Retainage Amount', 
                    'Retainage Rate (%)', 'Status', 'Reason', 'Site Address'
                ]
                df_proc = df_raw.drop(columns=[c for c in cols_to_drop if c in df_raw.columns], errors='ignore')
                df_proc = df_proc.dropna(subset=['Qty'])
                
                if 'Project Name' in df_proc.columns:
                    proj_idx = df_proc.columns.get_loc('Project Name')
                    df_proc = df_proc.iloc[:, :proj_idx+1]
                    
                df_proc = df_proc.rename(columns={'Line': 'Line Number', 'Qty': 'PO Qty'})
                po_no = po_number_input.strip()
                
                df_proc['PO Number'] = po_no
                df_proc['User Qty'] = 0
                df_proc['VIS Qty'] = 0
                df_proc['Diff'] = 0
                df_proc['Claim Qty'] = 0
                df_proc['Receipt Qty'] = 0
                if 'Amount' not in df_proc.columns: df_proc['Amount'] = 0
                if 'Price' not in df_proc.columns: df_proc['Price'] = 0
                
                final_cols = [
                    'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
                    'Item Num', 'Description', 'UOM', 'PO Qty', 
                    'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
                ]
                
                for col in final_cols:
                    if col not in df_proc.columns:
                        df_proc[col] = ""
                        
                df_proc = df_proc[final_cols]
                
                num_columns_to_int = ['Line Number', 'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount']
                for col in num_columns_to_int:
                    if col in df_proc.columns:
                        df_proc[col] = df_proc[col].astype(str).str.replace(',', '', regex=True)
                        df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce').fillna(0).astype(int)
                
                df_proc['Diff'] = df_proc['PO Qty'] - df_proc['VIS Qty']
                df_proc['Amount'] = df_proc['VIS Qty'] * df_proc['Price']
                
                existing_df = st.session_state.po_working_df
                new_rows_to_add = []
                
                for idx, new_row in df_proc.iterrows():
                    match_mask = (existing_df['PO Number'] == po_no) & (existing_df['Item Num'] == new_row['Item Num'])
                    
                    if match_mask.any():
                        match_idx = existing_df[match_mask].index[0]
                        row_id = existing_df.at[match_idx, 'id'] if 'id' in existing_df.columns else None
                        
                        curr_vis = int(existing_df.at[match_idx, 'VIS Qty']) if pd.notna(existing_df.at[match_idx, 'VIS Qty']) else 0
                        new_po = int(new_row['PO Qty'])
                        new_price = int(new_row['Price'])
                        
                        new_diff = new_po - curr_vis
                        new_amount = curr_vis * new_price
                        
                        if pd.notna(row_id):
                            try:
                                supabase.table("po_working").update({
                                    'PO Qty': new_po,
                                    'Price': new_price,
                                    'UOM': str(new_row['UOM']),
                                    'Description': str(new_row['Description']),
                                    'Diff': new_diff,
                                    'Amount': new_amount
                                }).eq("id", row_id).execute()
                            except Exception:
                                pass
                    else:
                        new_rows_to_add.append(new_row.to_dict())
                
                if new_rows_to_add:
                    records_to_insert = []
                    for rec in new_rows_to_add:
                        clean_rec = {}
                        for k, v in rec.items():
                            if k in num_columns_to_int:
                                clean_rec[k] = int(v)
                            else:
                                clean_rec[k] = str(v).strip() if pd.notna(v) and str(v) != 'nan' else ""
                        records_to_insert.append(clean_rec)
                    
                    try:
                        res = supabase.table("po_working").insert(records_to_insert).execute()
                    except Exception as e:
                        st.error(f"❌ DB Insert Error: Please verify Supabase columns match exactly. Details: {e}")
                        return
                
                if 'po_working_df' in st.session_state:
                    del st.session_state['po_working_df']
                st.success(f"✅ PO {po_number_input} Processed and Saved to Database!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

# --- 4. EXPORT DIALOG FUNCTION ---
@st.dialog("📥 Export PO Working Data", width="large")
def export_dialog(df_export):
    st.caption("Download your processed working list as an Excel file.")
    
    export_df = df_export.copy()
    if "🎯 Select" in export_df.columns:
        export_df = export_df.drop(columns=["🎯 Select"])
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='PO Working Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="PO_Working_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 4.5 DETAILED PO VIEW DIALOG FUNCTION ---
@st.dialog("👁️ PO Detailed Working View", width="large")
def view_po_details_dialog(row_data):
    po_no = row_data['PO Number']
    site_id = row_data['Site ID']
    site_name = row_data['Site Name']
    proj_name = row_data['Project Name']
    
    cluster_val, rfai_val, srn_val, km_val = "-", "-", "-", "-"
    if site_id:
        try:
            res_site = supabase.table("site_data").select("Cluster, RFAI Status").eq("Site ID", site_id).execute()
            if res_site.data:
                cluster_val = res_site.data[0].get("Cluster", "-")
                rfai_val = res_site.data[0].get("RFAI Status", "-")
            
            res_exc = supabase.table("Excalation Matrix").select("KM").eq("Site ID", site_id).execute()
            if res_exc.data:
                km_val = res_exc.data[0].get("KM", "-")
        except:
            pass

    display_cols = [
        'id', 'Line Number', 'PO Number', 'Item Num', 'Description', 'UOM', 
        'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
    ]
    
    editor_key = f"po_editor_{po_no}_{proj_name}"
    
    df_full = st.session_state.po_working_df
    po_specific_mask = (df_full['PO Number'] == po_no) & (df_full['Project Name'] == proj_name)
    real_indices = df_full[po_specific_mask].index.tolist()
    
    if editor_key in st.session_state:
        edits = st.session_state[editor_key].get("edited_rows", {})
        if edits:
            for str_idx, changes in edits.items():
                pos_idx = int(str_idx)
                if pos_idx < len(real_indices):
                    real_idx = real_indices[pos_idx] 
                    for col, val in changes.items():
                        st.session_state.po_working_df.loc[real_idx, col] = val

    df_temp = st.session_state.po_working_df[po_specific_mask].copy()
    
    df_temp['PO Qty'] = df_temp['PO Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['PO Qty'] = pd.to_numeric(df_temp['PO Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['VIS Qty'] = df_temp['VIS Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['VIS Qty'] = pd.to_numeric(df_temp['VIS Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Price'] = df_temp['Price'].astype(str).str.replace(',', '', regex=True)
    df_temp['Price'] = pd.to_numeric(df_temp['Price'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Diff'] = df_temp['PO Qty'] - df_temp['VIS Qty']
    df_temp['Amount'] = df_temp['VIS Qty'] * df_temp['Price']
    
    df_temp['User Qty'] = df_temp['User Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['User Qty'] = pd.to_numeric(df_temp['User Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Claim Qty'] = df_temp['Claim Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['Claim Qty'] = pd.to_numeric(df_temp['Claim Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Receipt Qty'] = df_temp['Receipt Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['Receipt Qty'] = pd.to_numeric(df_temp['Receipt Qty'], errors='coerce').fillna(0).astype(int)
    
    st.session_state.po_working_df.update(df_temp)
    
    # --- FIX: Calculate Total Project Amount as (PO Qty * Price) ---
    project_total_amount = (df_temp['PO Qty'] * df_temp['Price']).sum()
    
    st.markdown(f"""
        <div class="kpi-pill-container">
            <div class="kpi-pill">SITE ID: <span>{site_id}</span></div>
            <div class="kpi-pill">SITE NAME: <span>{site_name}</span></div>
            <div class="kpi-pill">PROJECT ID: <span>{proj_name}</span></div>
            <div class="kpi-pill">CLUSTER: <span>{cluster_val}</span></div>
            <div class="kpi-pill">RFAI: <span>{rfai_val}</span></div>
            <div class="kpi-pill">SRN: <span>{srn_val}</span></div>
            <div class="kpi-pill" style="border-color: #ef4444;">KM: <span style="color: #ef4444;">{km_val}</span></div>
            <div class="kpi-pill" style="background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);">
                <span style="color: #0f172a !important; font-weight: 900; letter-spacing: 1px; font-size: 0.95rem;">PROJECT AMOUNT : ₹ {project_total_amount:,}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    active_cols = [c for c in display_cols if c in st.session_state.po_working_df.columns]
    po_specific_df = st.session_state.po_working_df[po_specific_mask][active_cols].copy()

    st.markdown('<div class="modal-section-title">📋 PO LINE ITEMS</div>', unsafe_allow_html=True)
    
    edited_po_df = st.data_editor(
        po_specific_df, 
        key=editor_key,
        use_container_width=True, 
        hide_index=True,
        height=400, 
        column_config={
            "id": None, "Site ID": None, "Site Name": None, "Project Name": None,
            "Line Number": st.column_config.NumberColumn("Line", width="small", alignment="center", format="%d"),
            "PO Number": st.column_config.TextColumn("PO Number", alignment="center"),
            "PO Qty": st.column_config.NumberColumn("PO Qty", disabled=True, alignment="center", format="%d"),
            "User Qty": st.column_config.NumberColumn("USER QTY", alignment="center", format="%d", step=1),
            "VIS Qty": st.column_config.NumberColumn("VIS QTY", alignment="center", format="%d", step=1),
            "Diff": st.column_config.NumberColumn("Diff", disabled=True, alignment="center", format="%d"),
            "Claim Qty": st.column_config.NumberColumn("CLAIM QTY", alignment="center", format="%d", step=1),
            "Receipt Qty": st.column_config.NumberColumn("RECEIPT QTY", alignment="center", format="%d", step=1),
            "Price": st.column_config.NumberColumn("Price", alignment="center", format="%d"),
            "Amount": st.column_config.NumberColumn("Amount", disabled=True, alignment="center", format="%d")
        }
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_v1, col_v2 = st.columns([8, 2])
    with col_v2:
        if st.button("💾 Submit", type="primary", use_container_width=True):
            for idx, row in edited_po_df.iterrows():
                try:
                    if pd.notna(row.get('id')):
                        update_payload = {
                            "User Qty": int(row['User Qty']),
                            "VIS Qty": int(row['VIS Qty']),
                            "Diff": int(row['Diff']),
                            "Claim Qty": int(row['Claim Qty']),
                            "Receipt Qty": int(row['Receipt Qty']),
                            "Amount": int(row['Amount'])
                        }
                        supabase.table("po_working").update(update_payload).eq("id", row['id']).execute()
                except Exception:
                    pass
            
            if editor_key in st.session_state:
                del st.session_state[editor_key]
                
            if 'po_working_df' in st.session_state:
                del st.session_state['po_working_df']
                
            st.success("✅ PO Lines Submitted Successfully to DB!")
            st.rerun()

# --- 5. TOP ACTION BAR ---
col_title, col_ref, col_upload, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🧾 PO Working Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        if 'po_working_df' in st.session_state:
            del st.session_state['po_working_df']
        st.rerun() 
with col_upload:
    if st.button("📤 PO Upload Notepad", type="primary", use_container_width=True):
        po_upload_dialog() 
with col_export:
    if st.button("📥 Export", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- FETCH DATA FROM SESSION ---
df = st.session_state.po_working_df.copy()

if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 6. LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Uploaded PO Summary")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search PO, Project, Site...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- CREATE UNIQUE PO SUMMARY LIST ---
if not df.empty:
    summary_df = df[['Project Name', 'Site ID', 'Site Name', 'PO Number']].drop_duplicates().reset_index(drop=True)
else:
    summary_df = pd.DataFrame(columns=["Project Name", "Site ID", "Site Name", "PO Number"])

# --- 7. PAGINATION LOGIC ---
if 'po_current_page' not in st.session_state:
    st.session_state.po_current_page = 1

rows_per_page = 10
total_rows = len(summary_df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.po_current_page > total_pages:
    st.session_state.po_current_page = total_pages
elif st.session_state.po_current_page < 1:
    st.session_state.po_current_page = 1

start_idx = (st.session_state.po_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 8. SUMMARY DATA TABLE ---
df_page = summary_df.iloc[start_idx:end_idx].copy()

# Total 7 cols (Sr No + 2 Buttons + 4 Data)
COL_RATIOS = [0.3, 0.35, 0.35, 1.8, 1.2, 1.8, 1.2] 
COL_LABELS = ["#", "👁️", "🗑️", "PROJECT NAME", "SITE ID", "SITE NAME", "PO NUMBER"]

with st.container(key="po_table_wrap", height=560):
    if df_page.empty:
        st.info("No PO records found.")
    else:
        # Header
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)
        
        # Rows
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            po_num = str(row_dict.get('PO Number', '')).strip()
            safe_po_key = urllib.parse.quote(po_num) # safe key for widgets
            serial_no = start_idx + page_pos + 1
            
            rcols = st.columns(COL_RATIOS)
            
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            
            with rcols[1]:
                with st.container(key=f"vbtn_{safe_po_key}"):
                    if st.button("👁️", key=f"view_{safe_po_key}", help="View Details", use_container_width=True):
                        view_po_details_dialog(row_dict)
            with rcols[2]:
                with st.container(key=f"dbtn_{safe_po_key}"):
                    if st.button("🗑️", key=f"del_{safe_po_key}", help="Delete", use_container_width=True):
                        st.session_state[f"confirm_del_{safe_po_key}"] = True
                        
            rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Project Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('PO Number','') or '-'}</div>", unsafe_allow_html=True)

            # Inline delete confirmation
            if st.session_state.get(f"confirm_del_{safe_po_key}"):
                wc1, wc2, wc3 = st.columns([6, 1, 1])
                with wc1:
                    st.warning(f"Delete PO '{po_num}'? This will remove all associated items.")
                with wc2:
                    if st.button("✅ Confirm", key=f"confirm_yes_{safe_po_key}", use_container_width=True):
                        try:
                            supabase.table("po_working").delete().eq("PO Number", po_num).execute()
                            if 'po_working_df' in st.session_state:
                                del st.session_state['po_working_df']
                            st.session_state[f"confirm_del_{safe_po_key}"] = False
                            st.success(f"✅ PO {po_num} Deleted Successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error Deleting Record: {e}")
                with wc3:
                    if st.button("❌ Cancel", key=f"confirm_no_{safe_po_key}", use_container_width=True):
                        st.session_state[f"confirm_del_{safe_po_key}"] = False
                        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- 9. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.po_current_page == 1)):
        st.session_state.po_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.po_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.po_current_page == total_pages)):
        st.session_state.po_current_page += 1
        st.rerun()
