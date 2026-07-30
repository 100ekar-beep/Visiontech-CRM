import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="PO Working", page_icon="🧾", layout="wide")

# --- INITIALIZE SESSION STATE FOR TABLE DATA ---
if 'po_working_df' not in st.session_state:
    st.session_state.po_working_df = pd.DataFrame(columns=[
        'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
        'Item Num', 'Description', 'UOM', 'PO Qty', 
        'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
    ])

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
    </style>
""", unsafe_allow_html=True)

# --- 2.5 SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 3. UPLOAD ORACLE PO DIALOG FUNCTION (COMPACT UI) ---
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
                
                df_proc['PO Number'] = po_number_input.strip()
                df_proc['User Qty'] = 0
                df_proc['VIS Qty'] = 0
                df_proc['Diff'] = 0
                df_proc['Claim Qty'] = 0
                df_proc['Receipt Qty'] = 0
                
                # --- NEW FIX: Removed .0 by casting to integers ---
                num_columns_to_int = ['Line Number', 'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount']
                for col in num_columns_to_int:
                    if col in df_proc.columns:
                        df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce').fillna(0).astype(int)
                
                final_cols = [
                    'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
                    'Item Num', 'Description', 'UOM', 'PO Qty', 
                    'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
                ]
                
                for col in final_cols:
                    if col not in df_proc.columns:
                        df_proc[col] = ""
                        
                df_proc = df_proc[final_cols]
                
                st.session_state.po_working_df = pd.concat([st.session_state.po_working_df, df_proc], ignore_index=True)
                st.success(f"✅ PO {po_number_input} Processed and Added Successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing file: Make sure it's the exact Oracle .tsv export format. Details: {e}")

# --- 4. EXPORT DIALOG FUNCTION ---
@st.dialog("📥 Export PO Working Data", width="large")
def export_dialog(df_export):
    st.caption("Download your processed working list as an Excel file.")
    
    export_df = df_export.copy()
    if "🎯 Select" in export_df.columns:
        export_df = export_df.drop(columns=["🎯 Select"])
        
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

    st.markdown(f"""
        <div class="kpi-pill-container">
            <div class="kpi-pill">SITE ID: <span>{site_id}</span></div>
            <div class="kpi-pill">SITE NAME: <span>{site_name}</span></div>
            <div class="kpi-pill">PROJECT ID: <span>{proj_name}</span></div>
            <div class="kpi-pill">CLUSTER: <span>{cluster_val}</span></div>
            <div class="kpi-pill">RFAI: <span>{rfai_val}</span></div>
            <div class="kpi-pill">SRN: <span>{srn_val}</span></div>
            <div class="kpi-pill" style="border-color: #ef4444;">KM: <span style="color: #ef4444;">{km_val}</span></div>
        </div>
    """, unsafe_allow_html=True)
    
    df_full = st.session_state.po_working_df
    
    # --- NEW FIX: Reordered Columns as Requested ---
    display_cols = [
        'Line Number', 'PO Number', 'Item Num', 'Description', 'UOM', 
        'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
    ]
    po_specific_df = df_full[df_full['PO Number'] == po_no][display_cols].copy()
    
    st.markdown('<div class="modal-section-title">📋 PO LINE ITEMS</div>', unsafe_allow_html=True)
    
    # --- NEW FIX: Centered Numbers, Removed .0, Fixed Diff & Amount ---
    edited_po_df = st.data_editor(
        po_specific_df, 
        use_container_width=True, 
        hide_index=True,
        height=400, 
        column_config={
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
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            # --- NEW FIX: Automatically Calculate Diff and Amount on Save ---
            for idx, row in edited_po_df.iterrows():
                try:
                    vis_val = int(row['VIS Qty'])
                    po_val = int(row['PO Qty'])
                    price_val = int(row['Price'])
                    
                    edited_po_df.at[idx, 'Diff'] = po_val - vis_val
                    edited_po_df.at[idx, 'Amount'] = vis_val * price_val
                except:
                    pass
            
            st.session_state.po_working_df.update(edited_po_df)
            st.success("✅ PO Lines & Formulas Updated Successfully!")
            st.rerun()

# --- 5. TOP ACTION BAR ---
col_title, col_ref, col_upload, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🧾 PO Working Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
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
    summary_df.insert(0, "SR NO", range(1, len(summary_df) + 1))
    summary_df.insert(0, "🎯 Select", False)
else:
    summary_df = pd.DataFrame(columns=["🎯 Select", "SR NO", "Project Name", "Site ID", "Site Name", "PO Number"])

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

# --- NEW FIX: Small width for Action and SR NO columns in Summary View ---
edited_summary = st.data_editor(
    df_page, 
    use_container_width=True, 
    hide_index=True,
    height=400, 
    column_config={
        "🎯 Select": st.column_config.CheckboxColumn("Action", width="small", default=False),
        "SR NO": st.column_config.NumberColumn("SR NO", width="small", alignment="center", format="%d")
    }
)

# --- ROW ACTION BUTTONS (VIEW & DELETE) ---
selected_rows = edited_summary[edited_summary["🎯 Select"] == True]
if not selected_rows.empty:
    st.markdown("---")
    col_act1, col_act2, _ = st.columns([1.5, 1.5, 7])
    
    row_to_action = selected_rows.iloc[0].to_dict()
    selected_po = row_to_action['PO Number']
    
    with col_act1:
        if st.button("👁️ View Details", type="primary", use_container_width=True):
            view_po_details_dialog(row_to_action)
            
    with col_act2:
        if st.button("🗑️ Delete PO", type="primary", use_container_width=True):
            st.session_state.po_working_df = st.session_state.po_working_df[st.session_state.po_working_df['PO Number'] != selected_po]
            st.success(f"✅ PO {selected_po} Deleted Successfully!")
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
