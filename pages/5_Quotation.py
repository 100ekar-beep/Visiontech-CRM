import streamlit as st
import pandas as pd
import datetime
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Quotation List", page_icon="📄", layout="wide")

# --- 2. LAVISH CUSTOM CSS (Matches Screenshots) ---
st.markdown("""
    <style>
    /* Dark Premium Theme & Backgrounds */
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Top Action Buttons (Add Record, File) */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
    }
    button[data-testid="baseButton-secondary"] {
        background: #10b981 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4) !important;
    }
    button[data-testid="baseButton-primary"]:hover, 
    button[data-testid="baseButton-secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2) !important;
    }

    /* Dialog/Popup Glassmorphism for Quotation View */
    div[data-testid="stDialog"] > div {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, 
    div[data-testid="stDialog"] h2, 
    div[data-testid="stDialog"] h3 {
        color: #1e293b !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] p {
        color: #475569 !important; 
    }
    div[data-testid="stDialog"] button[kind="icon"] svg {
        fill: #64748b !important; 
    }

    /* Modal Section Title */
    .modal-section-title {
        color: #3b82f6;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Input Labels */
    label p, label[data-testid="stWidgetLabel"] p {
        color: #64748b !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Data Editor Table Header */
    [data-testid="stDataFrame"] th {
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 4. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_quotation_projects():
    # Only fetch projects where Operator is 'Quotation'
    try:
        res = supabase.table("site_data").select("Project ID, Site ID, Site Name, Cluster, KM, Project Name").eq("Operator", "Quotation").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    # Fallback dummy data if DB fails
    return pd.DataFrame(columns=["Project ID", "Site ID", "Site Name", "Cluster", "KM", "Project Name"])

@st.cache_data(ttl=60)
def fetch_item_master():
    try:
        res = supabase.table("item_master").select("Item Code, Description, Price").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    # Fallback dummy data
    return pd.DataFrame({
        "Item Code": ["25-100000-0-00", "21-510000-0-00", "29-400000-0-00"],
        "Description": ["Supply & Filling with Murram soil", "De-installation, Diesel Generator", "Hydra hiring for monopole"],
        "Price": [450, 2500, 7000]
    })

def fetch_quotations():
    try:
        res = supabase.table("quotations").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "Quotation Name", "Date", "Project ID", "Site ID", "Site Name", "Project Name", "Quotation Amount", "Status"])

# Load Master Data
df_projects = fetch_quotation_projects()
project_list = df_projects["Project ID"].dropna().unique().tolist() if not df_projects.empty else []

df_items = fetch_item_master()
item_code_list = df_items["Item Code"].dropna().unique().tolist() if not df_items.empty else []

# --- 5. INITIALIZE SESSION STATE ---
if 'quotations_df' not in st.session_state:
    st.session_state.quotations_df = fetch_quotations()

# --- 6. DIALOG FOR ADD/VIEW QUOTATION ---
@st.dialog("📄 Update Quotation", width="large")
def quotation_dialog(quotation_data=None):
    st.caption("Details and items for project estimation")
    
    is_new = quotation_data is None
    
    # Init variables
    quo_id = None
    default_name = f"Quotation {len(st.session_state.quotations_df) + 100}" if is_new else quotation_data.get("Quotation Name", "")
    default_date = datetime.date.today() if is_new else pd.to_datetime(quotation_data.get("Date", datetime.date.today())).date()
    default_proj = project_list[0] if project_list and is_new else quotation_data.get("Project ID", "")
    
    # Top Section: 4 Columns layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        quo_name = st.text_input("QUOTATION *", value=default_name)
    with col2:
        quo_date = st.date_input("QUOTATION DATE *", value=default_date)
    with col3:
        # User selects Project ID
        sel_proj = st.selectbox("PROJECT ID *", options=[""] + project_list, index=project_list.index(default_proj)+1 if default_proj in project_list else 0)
    
    # Auto-fetch Site Details based on selected Project ID
    auto_site_id = ""
    auto_site_name = ""
    auto_cluster = ""
    auto_proj_name = ""
    if sel_proj:
        proj_row = df_projects[df_projects["Project ID"] == sel_proj]
        if not proj_row.empty:
            auto_site_id = str(proj_row.iloc[0].get("Site ID", ""))
            auto_site_name = str(proj_row.iloc[0].get("Site Name", ""))
            auto_cluster = str(proj_row.iloc[0].get("Cluster", ""))
            auto_proj_name = str(proj_row.iloc[0].get("Project Name", ""))
            
    with col4:
        st.text_input("SITE ID *", value=auto_site_id, disabled=True)
        
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.text_input("SITE NAME", value=auto_site_name, disabled=True)
    with col6:
        st.text_input("CLUSTER", value=auto_cluster, disabled=True)
    with col7:
        st.text_input("PROJECT NAME", value=auto_proj_name, disabled=True)
    with col8:
        st.selectbox("QUOTATION TEMPLATE", options=["Standard Template", "Capex Template", "Opex Template"])
        
    st.markdown('<div class="modal-section-title">📚 Listing Premium Items</div>', unsafe_allow_html=True)
    
    # Line Items Session State management for this specific dialog
    editor_key = f"quo_items_{quo_name}"
    
    if editor_key not in st.session_state:
        if is_new:
            st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])
        else:
            # Fetch existing items from DB (Mocked logic, replace with actual DB fetch for items)
            try:
                res_items = supabase.table("quotation_items").select("*").eq("Quotation Name", quo_name).execute()
                if res_items.data:
                    st.session_state[editor_key] = pd.DataFrame(res_items.data)[["Item Code", "Description", "Qty", "Price", "Total"]]
                else:
                    st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])
            except:
                st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])

    # Render Dynamic Data Editor
    # num_rows="dynamic" enables the built-in + icon and Trash/Delete icon per row
    edited_items_df = st.data_editor(
        st.session_state[editor_key],
        key=f"editor_{editor_key}",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=300,
        column_config={
            "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=item_code_list, required=True, width="large"),
            "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
            "Qty": st.column_config.NumberColumn("QTY", min_value=0, default=1, format="%d"),
            "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d"),
            "Total": st.column_config.NumberColumn("TOTAL", disabled=True, format="₹ %d")
        }
    )
    
    # Auto-fill logic and Instant Calculation
    changes_made = False
    for idx, row in edited_items_df.iterrows():
        i_code = row.get("Item Code")
        if pd.notna(i_code) and i_code != "":
            # Auto-fill Description and Price if missing
            master_match = df_items[df_items["Item Code"] == i_code]
            if not master_match.empty:
                exp_desc = master_match.iloc[0]["Description"]
                exp_price = master_match.iloc[0]["Price"]
                
                if pd.isna(row.get("Description")) or row.get("Description") == "":
                    edited_items_df.at[idx, "Description"] = exp_desc
                    changed_made = True
                
                if pd.isna(row.get("Price")) or row.get("Price") == 0:
                    edited_items_df.at[idx, "Price"] = exp_price
                    changed_made = True
                    
        # Calculate Total dynamically
        qty = pd.to_numeric(row.get("Qty"), errors='coerce')
        price = pd.to_numeric(row.get("Price"), errors='coerce')
        qty = 0 if pd.isna(qty) else int(qty)
        price = 0 if pd.isna(price) else int(price)
        
        calc_total = qty * price
        if row.get("Total") != calc_total:
            edited_items_df.at[idx, "Total"] = calc_total
            changed_made = True

    # Update session state if calculated
    st.session_state[editor_key] = edited_items_df

    grand_total = edited_items_df["Total"].sum() if not edited_items_df.empty else 0
    
    st.markdown(f"<h4 style='text-align: right; color: #4f46e5;'>Grand Total: ₹ {grand_total:,}</h4>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_dl, _, col_save = st.columns([2, 6, 2])
    
    with col_dl:
        st.button("📥 Download PDF", use_container_width=True)
        
    with col_save:
        if st.button("💾 Save Quotation", type="primary", use_container_width=True):
            if not sel_proj:
                st.error("⚠️ Project ID is required!")
                return
                
            # Create header record
            header_data = {
                "Quotation Name": quo_name,
                "Date": str(quo_date),
                "Project ID": sel_proj,
                "Site ID": auto_site_id,
                "Site Name": auto_site_name,
                "Project Name": auto_proj_name,
                "Quotation Amount": int(grand_total),
                "Status": "Manual"
            }
            
            try:
                # Upsert Header to Supabase
                if not is_new and "id" in quotation_data and pd.notna(quotation_data["id"]):
                    supabase.table("quotations").update(header_data).eq("id", quotation_data["id"]).execute()
                else:
                    supabase.table("quotations").insert(header_data).execute()
                
                # Delete old items and insert new ones
                supabase.table("quotation_items").delete().eq("Quotation Name", quo_name).execute()
                
                if not edited_items_df.empty:
                    items_to_insert = []
                    for _, r in edited_items_df.iterrows():
                        if pd.notna(r["Item Code"]) and r["Item Code"] != "":
                            items_to_insert.append({
                                "Quotation Name": quo_name,
                                "Item Code": str(r["Item Code"]),
                                "Description": str(r["Description"]),
                                "Qty": int(r["Qty"]) if pd.notna(r["Qty"]) else 0,
                                "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0,
                                "Total": int(r["Total"]) if pd.notna(r["Total"]) else 0
                            })
                    if items_to_insert:
                        supabase.table("quotation_items").insert(items_to_insert).execute()
                
                # Refresh local cache
                st.session_state.quotations_df = fetch_quotations()
                st.success("✅ Quotation Saved Successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Database Error: {e}")

# --- 7. TOP HEADER & FILTERS ---
col_head1, col_head2, col_head3, col_head4 = st.columns([4, 2, 2, 2])
with col_head1:
    st.markdown("<h1 style='margin:0; color:#0f172a;'>Quotation List</h1>", unsafe_allow_html=True)
with col_head2:
    search_q = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")
with col_head3:
    if st.button("➕ Add Record", type="primary", use_container_width=True):
        quotation_dialog()
with col_head4:
    st.button("📄 File ▼", type="secondary", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. MAIN SCREEN QUOTATION LIST ---
df_display = st.session_state.quotations_df.copy()

if not df_display.empty and search_q:
    mask = df_display.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
    df_display = df_display[mask]

if not df_display.empty:
    # Prepare display dataframe matching the requirement
    disp_cols = ["Quotation Name", "Date", "Site ID", "Site Name", "Project ID", "Project Name", "Quotation Amount"]
    
    # Ensure columns exist
    for c in disp_cols:
        if c not in df_display.columns:
            df_display[c] = ""
            
    df_list = df_display[disp_cols].copy()
    df_list.insert(0, "Action", False)
    df_list.insert(0, "#", range(1, len(df_list) + 1))
    
    edited_list = st.data_editor(
        df_list,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Action": st.column_config.CheckboxColumn("SELECT", width="small", default=False),
            "#": st.column_config.NumberColumn("#", width="small", alignment="center"),
            "Quotation Amount": st.column_config.NumberColumn("GRAND TOTAL", format="₹ %d"),
            "Project Name": st.column_config.TextColumn("PROJECT"),
            "Site ID": st.column_config.TextColumn("SITE CODE")
        }
    )
    
    # Action Buttons Trigger
    selected_rows = edited_list[edited_list["Action"] == True]
    if not selected_rows.empty:
        st.markdown("---")
        col_act1, col_act2, _ = st.columns([2, 2, 8])
        
        selected_index = selected_rows.index[0]
        actual_data = df_display.iloc[selected_index].to_dict()
        
        with col_act1:
            if st.button("👁️ View / Edit", type="primary", use_container_width=True):
                quotation_dialog(actual_data)
                
        with col_act2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                try:
                    q_name = actual_data["Quotation Name"]
                    supabase.table("quotations").delete().eq("Quotation Name", q_name).execute()
                    supabase.table("quotation_items").delete().eq("Quotation Name", q_name).execute()
                    st.session_state.quotations_df = fetch_quotations()
                    st.success(f"✅ Deleted {q_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
else:
    st.info("No Quotations found. Click '+ Add Record' to create one.")
