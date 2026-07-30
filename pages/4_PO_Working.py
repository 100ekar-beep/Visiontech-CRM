import streamlit as st
import pandas as pd
import math
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="PO Working", page_icon="🧾", layout="wide")

# --- INITIALIZE SESSION STATE FOR TABLE DATA ---
if 'po_working_df' not in st.session_state:
    st.session_state.po_working_df = pd.DataFrame(columns=[
        'Site ID', 'Site Name', 'Project Name', 'Line Number', 
        'Item Num', 'Description', 'UOM', 'PO Qty', 
        'User Qty', 'VIS Qty', 'Price', 'Amount'
    ])

# --- 2. LAVISH CUSTOM CSS ---
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
    </style>
""", unsafe_allow_html=True)

# --- 3. UPLOAD ORACLE PO DIALOG FUNCTION ---
@st.dialog("📤 Upload Oracle PO File", width="large")
def po_upload_dialog():
    st.caption("Upload the Oracle exported .tsv file. Background cleaning rules will apply automatically.")
    
    # Strictly configured for .tsv files
    uploaded_file = st.file_uploader("Choose Oracle .tsv File", type=["tsv"], key="po_upload_file")
    
    if uploaded_file:
        if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
            try:
                # Read TSV with cp1252 encoding and skipping first 8 messy rows from Oracle
                df_raw = pd.read_csv(uploaded_file, sep='\t', encoding='cp1252', skiprows=8)
                
                # Rule 1-5 & 7-13: Dropping all unnecessary Oracle columns
                cols_to_drop = [
                    'Type', 'Type.1', 'Item/Job', 'Supplier Item', 'Type.2', 
                    'Advance Amount', 'Advance Billed', 'Maximum Retainage Amount', 
                    'Retainage Rate (%)', 'Status', 'Reason', 'Site Address'
                ]
                df_proc = df_raw.drop(columns=[c for c in cols_to_drop if c in df_raw.columns], errors='ignore')
                
                # Rule 6: Drop rows where 'Qty' is completely blank
                df_proc = df_proc.dropna(subset=['Qty'])
                
                # Rule 14: Delete everything after 'Project Name'
                if 'Project Name' in df_proc.columns:
                    proj_idx = df_proc.columns.get_loc('Project Name')
                    df_proc = df_proc.iloc[:, :proj_idx+1]
                    
                # Mapping existing Oracle columns to your requested format
                df_proc = df_proc.rename(columns={'Line': 'Line Number', 'Qty': 'PO Qty'})
                
                # Adding the new manual input columns
                df_proc['User Qty'] = 0.0
                df_proc['VIS Qty'] = 0.0
                
                # Formatting to strictly match the requested sequence
                final_cols = [
                    'Site ID', 'Site Name', 'Project Name', 'Line Number', 
                    'Item Num', 'Description', 'UOM', 'PO Qty', 
                    'User Qty', 'VIS Qty', 'Price', 'Amount'
                ]
                
                # Ensure all columns exist before restructuring to prevent errors
                for col in final_cols:
                    if col not in df_proc.columns:
                        df_proc[col] = ""
                        
                df_proc = df_proc[final_cols]
                
                # Pushing clean data to session state for live table rendering
                st.session_state.po_working_df = df_proc
                st.success("✅ Oracle TSV Processed and Cleaned Successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing file: Make sure it's the exact Oracle .tsv export. Details: {e}")

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

# --- 5. TOP ACTION BAR ---
col_title, col_ref, col_upload, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🧾 PO Working Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun() 
with col_upload:
    if st.button("📤 PO Upload", use_container_width=True):
        po_upload_dialog() 
with col_export:
    if st.button("📥 Export", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- FETCH DATA FROM SESSION ---
df = st.session_state.po_working_df.copy()

if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)

# --- EXPORT LOGIC TRIGGER AFTER DF LOAD ---
if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 6. LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Working Line Items")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- 7. PAGINATION LOGIC (10 lines per page) ---
if 'po_current_page' not in st.session_state:
    st.session_state.po_current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.po_current_page > total_pages:
    st.session_state.po_current_page = total_pages
elif st.session_state.po_current_page < 1:
    st.session_state.po_current_page = 1

start_idx = (st.session_state.po_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 8. ORIGINAL LAVISH DATA TABLE (st.data_editor) ---
df_page = df.iloc[start_idx:end_idx].copy()

# Render Data Editor - User Qty and VIS Qty are left editable to match "Working" concept
edited_df = st.data_editor(
    df_page, 
    use_container_width=True, 
    hide_index=True,
    height=400, 
    column_config={
        "🎯 Select": st.column_config.CheckboxColumn("Select", default=False),
        "User Qty": st.column_config.NumberColumn("User Qty", format="%.2f"),
        "VIS Qty": st.column_config.NumberColumn("VIS Qty", format="%.2f")
    }
)

# Update Session State if user manually edits User Qty or VIS Qty in the table
if not edited_df.equals(df_page):
    for idx, row in edited_df.iterrows():
        original_idx = df.index[(df['Line Number'] == row['Line Number']) & (df['Item Num'] == row['Item Num'])]
        if not original_idx.empty:
            real_index = original_idx[0]
            st.session_state.po_working_df.at[real_index, 'User Qty'] = row['User Qty']
            st.session_state.po_working_df.at[real_index, 'VIS Qty'] = row['VIS Qty']

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
