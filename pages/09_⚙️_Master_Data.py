import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Master Data Settings", page_icon="⚙️", layout="wide")

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#17213b; --muted:#68738d; --line:#e7eaf2; --primary:#6c4df6; }
.stApp { background:linear-gradient(135deg,#f7f8ff 0%,#f2fbff 50%,#fff8f2 100%); color:var(--ink); font-family:'Manrope',sans-serif; }
.block-container { padding-top:1.2rem; padding-bottom:3rem; max-width:1500px; }
[data-testid="stHeader"] { background:transparent; }

/* Sidebar */
[data-testid="stSidebar"] { background:linear-gradient(180deg,#17122d,#24194a); border-right:0; }
[data-testid="stSidebarNav"] a { padding:.78rem 1rem!important; margin:.35rem .75rem!important; border-radius:12px!important; color:#ddd8ff!important; font-weight:650!important; }
[data-testid="stSidebarNav"] a:hover { background:rgba(255,255,255,.10)!important; color:white!important; transform:translateX(3px); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:linear-gradient(90deg,#7657ff,#b14cff)!important; color:white!important; box-shadow:0 8px 20px rgba(112,72,255,.35); }
[data-testid="stSidebarNav"] a span { color:inherit!important; }

/* Hero */
.hero { position:relative; overflow:hidden; padding:1.6rem 1.8rem; border-radius:24px; color:white; background:linear-gradient(115deg,#5936e8 0%,#7b4df6 42%,#e34f9c 100%); box-shadow:0 18px 46px rgba(91,55,220,.24); margin-bottom:1.15rem; }
.hero:after { content:''; position:absolute; width:260px; height:260px; right:-70px; top:-100px; border-radius:50%; background:rgba(255,255,255,.13); }
.hero-title { font-size:2rem; line-height:1.15; font-weight:800; margin:0 0 .35rem; }
.hero-sub { font-size:.96rem; color:rgba(255,255,255,.86); margin:0; max-width:760px; }
.eyebrow { display:inline-block; padding:.3rem .7rem; border-radius:20px; background:rgba(255,255,255,.16); font-size:.72rem; font-weight:800; letter-spacing:.8px; margin-bottom:.7rem; }

/* Cards / section labels */
.section-head { margin:.45rem 0 .85rem; padding-left:.2rem; }
.section-title { color:var(--ink); font-size:1.22rem; font-weight:800; margin:0; }
.section-sub { color:var(--muted); font-size:.84rem; margin:.2rem 0 0; }
.metric-card { background:white; border:1px solid rgba(226,230,240,.9); border-radius:18px; padding:1rem 1.1rem; box-shadow:0 8px 25px rgba(35,41,70,.07); min-height:95px; }
.metric-label { color:#737d95; font-size:.78rem; font-weight:700; }
.metric-value { color:#1b2540; font-size:1.65rem; font-weight:800; margin-top:.18rem; }
.metric-purple { border-top:4px solid #7657ff; }.metric-green { border-top:4px solid #20b486; }.metric-orange { border-top:4px solid #ff9f43; }.metric-pink { border-top:4px solid #ef5da8; }

/* Native widgets */
label p, label[data-testid="stWidgetLabel"] p { color:#34405d!important; font-weight:750!important; }
[data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { background:white!important; border-color:#e1e5ef!important; border-radius:11px!important; min-height:44px; }
[data-testid="stForm"] { background:white; border:1px solid #e6e9f2!important; border-radius:20px!important; padding:1.25rem 1.35rem!important; box-shadow:0 10px 30px rgba(35,41,70,.07); }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid #e4e8f0; border-radius:16px; overflow:hidden; box-shadow:0 8px 28px rgba(35,41,70,.07); }
[data-testid="stFileUploaderDropzone"] { background:#f8f7ff; border:1.5px dashed #a99af5; border-radius:16px; }

/* Buttons: defaults and named action colours */
div.stButton > button, div.stDownloadButton > button, [data-testid="stFormSubmitButton"] button { border:0!important; border-radius:12px!important; min-height:44px; font-weight:800!important; transition:.2s ease; box-shadow:0 7px 18px rgba(50,55,90,.12); }
div.stButton > button:hover, div.stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] button:hover { transform:translateY(-2px); box-shadow:0 11px 24px rgba(50,55,90,.18); }
div.stButton > button { background:linear-gradient(90deg,#6848ef,#885cf7)!important; color:white!important; }
div.stDownloadButton > button { background:linear-gradient(90deg,#087fce,#16a6dd)!important; color:white!important; }
[data-testid="stFormSubmitButton"] button { background:linear-gradient(90deg,#12a675,#20c997)!important; color:white!important; }

/* Tabs */
[data-baseweb="tab-list"] { gap:.55rem; background:white; padding:.42rem; border:1px solid #e5e8f1; border-radius:15px; box-shadow:0 7px 22px rgba(35,41,70,.06); }
[data-baseweb="tab"] { height:45px; padding:0 1.2rem; border-radius:11px; font-weight:800; color:#6a748c; }
[aria-selected="true"][data-baseweb="tab"] { background:linear-gradient(90deg,#6b4cf2,#9a55f5); color:white!important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none; }

/* Dialog */
div[data-testid="stDialog"] > div { background:#fbfbff; border-radius:22px; border:1px solid #e5e7f0; }
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 { color:#1d2742!important; font-weight:800!important; }
.hint { background:linear-gradient(90deg,#f0edff,#fff4fa); border-left:4px solid #7958f5; border-radius:10px; padding:.7rem .9rem; color:#59647d; font-size:.83rem; margin-bottom:.9rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
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

master_table_name = "dropdown_master"

# --- NAYI LINE: Added Vendor Name, Payment From, and Payment Type in Categories ---
categories = [
    "Department", "Operator", "Project Name", "Site Status", 
    "Product", "PO Status", "RFAI Status", "WH Material", 
    "Team Name", "Vendor Name", "Payment From", "Payment Type",
    "Team Billing Status", "Extra Approval", 
    "Vision Billing Status", "WCC Status",
    "SRN Status", "Transaction Type", "Item Code", 
    "Item Description", "Material Status", "STN Status"
]

# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: cached dropdown_master fetch ---
# Pehle yeh table BINA caching ke fetch hoti thi har baar jab filter
# category badalte ya row select karte — ab 30s ke liye cache kiya
# gaya hai, aur kisi bhi insert/update/delete/status-toggle ke baad
# .clear() call karke fresh data le liya jaata hai.
# -------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_master_data_cached(filter_cat):
    if filter_cat == "View All":
        response = supabase.table(master_table_name).select("*").execute()
    else:
        response = supabase.table(master_table_name).select("*").eq("category", filter_cat).execute()
    return response.data

def clear_master_cache():
    """Call this right before st.rerun() after any insert/update/delete/toggle on dropdown_master."""
    fetch_master_data_cached.clear()

# --- NEW: BULK UPLOAD DIALOG POPUP ---
@st.dialog("📤 Bulk Upload Item Codes", width="large")
def bulk_upload_item_dialog():
    st.caption("Upload Excel (.xlsx) or .tsv file. Required columns: item_code, item_description, material_of, stn_status, rate")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_item_file")
    
    if uploaded_file:
        if st.button("🚀 Process & Upload Items", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file, sep='\t')
                    
                added_count = 0
                failed_count = 0
                
                for index, row in df_upload.iterrows():
                    val = str(row.get("item_code", row.get("Item Code", row.get("Itemcode", row.get("option_value", ""))) )).strip()
                    if not val or val == "nan":
                        continue
                        
                    desc = str(row.get("item_description", row.get("Item Description", row.get("Description", ""))))
                    if desc == "nan": desc = ""

                    mat = str(row.get("material_of", row.get("Material of", row.get("Material Of", "Indus"))))
                    if mat == "nan" or not mat.strip(): mat = "Indus"

                    stn = str(row.get("stn_status", row.get("STN Status", row.get("Stn Status", "Required"))))
                    if stn == "nan" or not stn.strip(): stn = "Required"

                    raw_rate = row.get("rate", row.get("Rate", None))
                    clean_rate = float(raw_rate) if pd.notna(raw_rate) and str(raw_rate).strip() != "" else None

                    insert_dict = {
                        "category": "Item Code",
                        "option_value": val,
                        "is_active": True,
                        "item_description": desc,
                        "material_of": mat,
                        "stn_status": stn,
                        "rate": clean_rate
                    }
                    try:
                        supabase.table(master_table_name).insert(insert_dict).execute()
                        added_count += 1
                    except Exception as db_e:
                        failed_count += 1
                        st.error(f"❌ DB Error at row {index+1} ({val}): {db_e}")
                        
                if added_count > 0:
                    st.success(f"✅ Bulk Upload Complete! {added_count} Item Codes Added Successfully. (Failed: {failed_count})")
                    if failed_count == 0:
                        clear_master_cache()
                        st.rerun()
                else:
                    st.error(f"⚠️ No records added. Please check Supabase table columns and data format!")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- NEW: EDIT DIALOG POPUP (WITH DIRECT SUPABASE FETCH) ---
@st.dialog("✏️ Edit Record", width="large")
def edit_dialog(row_data):
    # Fetch fresh record directly from Supabase using ID to ensure all columns are loaded
    record_id = row_data.get('id')
    live_data = row_data
    try:
        res = supabase.table(master_table_name).select("*").eq("id", record_id).execute()
        if res.data and len(res.data) > 0:
            live_data = res.data[0]
    except Exception as e:
        pass

    with st.form("edit_form", border=False):
        default_index = categories.index(live_data['category']) if live_data['category'] in categories else 0
        new_cat = st.selectbox("Category", categories, index=default_index)
        
        new_val = st.text_input("Option Value", value=str(live_data.get('option_value', '') or ''))
        
        mob, p_num, g_num, perc, item_desc_val, stn_status_val, mat_of_val, rate_val = "", "", "", "", "", "", "Indus", None
        
        if new_cat == 'Team Name':
            c1, c2 = st.columns(2)
            with c1:
                mob = st.text_input("Mobile Number", value=str(live_data.get('mobile', '') or ''))
                p_num = st.text_input("PAN Number", value=str(live_data.get('pan', '') or ''))
            with c2:
                g_num = st.text_input("GST Number", value=str(live_data.get('gst', '') or ''))
                perc = st.text_input("Percentage", value=str(live_data.get('percentage', '') or ''))
        # --- NAYI LINE: Vendor Name Edit Form Logic ---
        elif new_cat == 'Vendor Name':
            c1, c2 = st.columns(2)
            with c1:
                mob = st.text_input("Mobile Number", value=str(live_data.get('mobile', '') or ''))
                p_num = st.text_input("PAN Number", value=str(live_data.get('pan', '') or ''))
            with c2:
                g_num = st.text_input("GST Number", value=str(live_data.get('gst', '') or ''))
        elif new_cat == 'Item Code':
            c1, c2 = st.columns(2)
            with c1:
                item_desc_val = st.text_input("Item Description", value=str(live_data.get('item_description', '') or ''))
                mat_opts_list = ["Indus", "Visiontech"]
                curr_mat = str(live_data.get('material_of', 'Indus') or 'Indus')
                mat_idx = mat_opts_list.index(curr_mat) if curr_mat in mat_opts_list else 0
                mat_of_val = st.selectbox("Material of", mat_opts_list, index=mat_idx)
            with c2:
                stn_opts_list = ["Required", "Not Required"]
                curr_stn = str(live_data.get('stn_status', 'Required') or 'Required')
                stn_idx = stn_opts_list.index(curr_stn) if curr_stn in stn_opts_list else 0
                stn_status_val = st.selectbox("STN Status", stn_opts_list, index=stn_idx)
                
                existing_rate = live_data.get('rate')
                rate_str = str(existing_rate) if existing_rate is not None else ''
                raw_rate_ed = st.text_input("Rate", value=rate_str)
                rate_val = float(raw_rate_ed) if raw_rate_ed.strip() != '' else None
            
        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if submitted:
            update_data = {
                "category": new_cat,
                "option_value": new_val.strip(),
                "mobile": mob, "pan": p_num, "gst": g_num, "percentage": perc,
                "item_description": item_desc_val, "stn_status": stn_status_val,
                "material_of": mat_of_val, "rate": rate_val
            }
            try:
                supabase.table(master_table_name).update(update_data).eq("id", record_id).execute()
                st.success("✅ Record updated!")
                clear_master_cache()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update Error: {e}")

# --- 4. EXPORT HELPERS ---
def dataframe_to_excel(download_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        download_df.to_excel(writer, index=False, sheet_name="Master Data")
        sheet = writer.sheets["Master Data"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column_cells in sheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 45)
    return output.getvalue()

def item_template_excel():
    template = pd.DataFrame(columns=["item_code", "item_description", "material_of", "stn_status", "rate"])
    return dataframe_to_excel(template)


# --- 5. PREMIUM HEADER ---
st.markdown("""
<div class="hero">
  <div class="eyebrow">MASTER DATA CONTROL CENTER</div>
  <div class="hero-title">⚙️ Dropdown Master Settings</div>
  <p class="hero-sub">Register, search, update and export every dropdown option from one clean control panel.</p>
</div>
""", unsafe_allow_html=True)

# Dashboard counts are intentionally fetched from the same cached source.
try:
    overview_data = fetch_master_data_cached("View All") if supabase else []
except Exception:
    overview_data = []

overview_df = pd.DataFrame(overview_data)
total_count = len(overview_df)
active_count = int(overview_df.get("is_active", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if total_count else 0
inactive_count = total_count - active_count
category_count = int(overview_df["category"].nunique()) if total_count and "category" in overview_df.columns else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card metric-purple"><div class="metric-label">TOTAL RECORDS</div><div class="metric-value">{total_count:,}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card metric-green"><div class="metric-label">ACTIVE OPTIONS</div><div class="metric-value">{active_count:,}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card metric-orange"><div class="metric-label">CATEGORIES</div><div class="metric-value">{category_count:,}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card metric-pink"><div class="metric-label">INACTIVE OPTIONS</div><div class="metric-value">{inactive_count:,}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

# Registration and table are deliberately separated into dedicated tabs.
tab_records, tab_add = st.tabs(["📋  Registered Data", "➕  New Registration"])

with tab_add:
    st.markdown("""
    <div class="section-head">
      <div class="section-title">Create a New Master Option</div>
      <div class="section-sub">Choose a category and fill the relevant details. The new record will be active by default.</div>
    </div>
    """, unsafe_allow_html=True)

    add_left, add_right = st.columns([1.25, 1], gap="large")
    with add_left:
        selected_category = st.selectbox("Select Registration Category", categories, key="add_category")

        with st.form("add_master_form", clear_on_submit=True):
            mobile, pan, gst, percentage = "", "", "", ""
            item_desc, stn_status, material_of = "", "Required", "Indus"
            raw_rate_input = ""

            if selected_category == "Team Name":
                new_option_value = st.text_input("Team Name *", placeholder="Enter complete team name")
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    mobile = st.text_input("Mobile Number", placeholder="10 digit mobile number")
                    pan = st.text_input("PAN Number", placeholder="ABCDE1234F")
                with col_t2:
                    gst = st.text_input("GST Number", placeholder="GSTIN, if applicable")
                    percentage = st.text_input("Percentage (%)", placeholder="e.g. 5")
            elif selected_category == "Vendor Name":
                new_option_value = st.text_input("Vendor Name *", placeholder="Enter vendor/company name")
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    mobile = st.text_input("Mobile Number", placeholder="10 digit mobile number")
                    pan = st.text_input("PAN Number", placeholder="ABCDE1234F")
                with col_v2:
                    gst = st.text_input("GST Number", placeholder="GSTIN, if applicable")
            elif selected_category == "Item Code":
                new_option_value = st.text_input("Item Code *", placeholder="Enter unique item code")
                item_desc = st.text_area("Item Description *", placeholder="Enter complete item description", height=90)
                col_i1, col_i2, col_i3 = st.columns(3)
                with col_i1:
                    material_of = st.selectbox("Material of *", ["Indus", "Visiontech"])
                with col_i2:
                    stn_status = st.selectbox("STN Status *", ["Required", "Not Required"])
                with col_i3:
                    raw_rate_input = st.text_input("Rate", placeholder="0.00")
            else:
                new_option_value = st.text_input("Option Value *", placeholder=f"Enter new {selected_category}")

            submit_btn = st.form_submit_button("➕  ADD NEW RECORD", use_container_width=True)

            if submit_btn:
                clean_value = new_option_value.strip()
                rate = None
                rate_valid = True
                if raw_rate_input.strip():
                    try:
                        rate = float(raw_rate_input.strip())
                    except ValueError:
                        rate_valid = False
                        st.error("⚠️ Rate must be a valid number.")

                if not clean_value:
                    st.error("⚠️ Please enter the required option value.")
                elif selected_category == "Item Code" and not item_desc.strip():
                    st.error("⚠️ Item Description is required for an Item Code.")
                elif rate_valid:
                    insert_data = {
                        "category": selected_category, "option_value": clean_value, "is_active": True,
                        "mobile": mobile.strip(), "pan": pan.strip().upper(), "gst": gst.strip().upper(),
                        "percentage": percentage.strip(), "item_description": item_desc.strip(),
                        "stn_status": stn_status, "material_of": material_of, "rate": rate
                    }
                    try:
                        supabase.table(master_table_name).insert(insert_data).execute()
                        st.success(f"✅ {selected_category} added successfully: {clean_value}")
                        clear_master_cache()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Database Error: {e}")

    with add_right:
        st.markdown("""
        <div class="section-head">
          <div class="section-title">Item Code Bulk Tools</div>
          <div class="section-sub">Use the ready Excel format or upload many item codes at once.</div>
        </div>
        <div class="hint">💡 Required columns: item_code, item_description, material_of, stn_status and rate.</div>
        """, unsafe_allow_html=True)
        st.download_button(
            "⬇️  DOWNLOAD EXCEL TEMPLATE",
            data=item_template_excel(),
            file_name="item_code_upload_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        if st.button("📤  OPEN BULK UPLOAD", use_container_width=True, key="open_bulk_from_add"):
            bulk_upload_item_dialog()

with tab_records:
    st.markdown("""
    <div class="section-head">
      <div class="section-title">Registered Options Database</div>
      <div class="section-sub">Filter, search, download or select one record to edit, activate/deactivate or delete.</div>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.2, 1.5, .9])
    with f1:
        filter_cat = st.selectbox("Category", ["View All"] + categories, key="table_category")
    with f2:
        search_text = st.text_input("Search Records", placeholder="Search option, item, mobile, PAN, GST...", key="table_search")
    with f3:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"], key="table_status")

    try:
        data = fetch_master_data_cached(filter_cat)

        if data:
            df = pd.DataFrame(data)
            expected_columns = ['id', 'category', 'option_value', 'is_active', 'mobile', 'pan', 'gst', 'percentage', 'item_description', 'stn_status', 'material_of', 'rate']
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""

            if status_filter != "All":
                wanted = status_filter == "Active"
                df = df[df["is_active"].fillna(False).astype(bool) == wanted]

            if search_text.strip():
                searchable = df.astype(str).apply(lambda col: col.str.contains(search_text.strip(), case=False, na=False))
                df = df[searchable.any(axis=1)]

            result_count = len(df)
            tool1, tool2, tool3 = st.columns([1, 1, 2.2])
            with tool1:
                st.download_button(
                    "⬇️ DOWNLOAD EXCEL",
                    data=dataframe_to_excel(df.drop(columns=["id"], errors="ignore")),
                    file_name=f"dropdown_master_{filter_cat.replace(' ', '_').lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    disabled=df.empty
                )
            with tool2:
                if st.button("📤 BULK UPLOAD", use_container_width=True, key="open_bulk_from_table"):
                    bulk_upload_item_dialog()
            with tool3:
                st.markdown(f'<div class="hint" style="margin-top:.1rem">🔎 Showing <b>{result_count:,}</b> matching record(s). Select one row below to enable record actions.</div>', unsafe_allow_html=True)

            if not df.empty:
                df.insert(0, "Select", False)
                if filter_cat == "Team Name":
                    display_df = df[['Select', 'id', 'category', 'option_value', 'mobile', 'pan', 'gst', 'percentage', 'is_active']].copy()
                elif filter_cat == "Vendor Name":
                    display_df = df[['Select', 'id', 'category', 'option_value', 'mobile', 'pan', 'gst', 'is_active']].copy()
                elif filter_cat == "Item Code":
                    display_df = df[['Select', 'id', 'category', 'option_value', 'item_description', 'material_of', 'stn_status', 'rate', 'is_active']].copy()
                else:
                    display_df = df[['Select', 'id', 'category', 'option_value', 'is_active']].copy()

                edited_df = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=520,
                    disabled=[c for c in display_df.columns if c != "Select"],
                    column_config={
                        "id": None,
                        "Select": st.column_config.CheckboxColumn("Select", default=False, width="small"),
                        "category": st.column_config.TextColumn("Category", width="medium"),
                        "option_value": st.column_config.TextColumn("Option Value", width="large"),
                        "item_description": st.column_config.TextColumn("Item Description", width="large"),
                        "is_active": st.column_config.CheckboxColumn("Active", disabled=True, width="small"),
                        "rate": st.column_config.NumberColumn("Rate", format="₹ %.2f")
                    },
                    key=f"master_editor_{filter_cat}_{status_filter}"
                )

                selected_rows = edited_df[edited_df["Select"] == True]
                if len(selected_rows) > 1:
                    st.warning("⚠️ Please select only one record at a time for Edit, Status or Delete action.")
                elif len(selected_rows) == 1:
                    row_to_edit = selected_rows.iloc[0].to_dict()
                    st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
                    col_a1, col_a2, col_a3, col_a4 = st.columns([1, 1.2, 1, 2])
                    with col_a1:
                        if st.button("✏️ EDIT RECORD", use_container_width=True):
                            edit_dialog(row_to_edit)
                    with col_a2:
                        status_text = "🚫 DEACTIVATE" if bool(row_to_edit['is_active']) else "✅ ACTIVATE"
                        if st.button(status_text, use_container_width=True):
                            try:
                                supabase.table(master_table_name).update({"is_active": not bool(row_to_edit['is_active'])}).eq("id", row_to_edit['id']).execute()
                                clear_master_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Status update failed: {e}")
                    with col_a3:
                        if st.button("🗑️ DELETE", type="primary", use_container_width=True):
                            try:
                                supabase.table(master_table_name).delete().eq("id", row_to_edit['id']).execute()
                                clear_master_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {e}")
                    with col_a4:
                        st.info(f"Selected: {row_to_edit.get('option_value', '')}")
            else:
                st.info("No records match the selected filters.")
        else:
            st.info(f"ℹ️ No options registered yet for {filter_cat}.")
    except Exception as e:
        st.error(f"⚠️ Table Error: Please ensure all required columns exist in Supabase. Details: {e}")
