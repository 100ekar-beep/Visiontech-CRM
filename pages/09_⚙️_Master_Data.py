import streamlit as st
import pandas as pd
import io
import math
import html
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Master Data Settings", page_icon="⚙️", layout="wide")

# --- 2. ✨ LAVISH CUSTOM CSS ---
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

/* Section labels */
.section-head { margin:.45rem 0 .85rem; padding-left:.2rem; }
.section-title { color:var(--ink); font-size:1.22rem; font-weight:800; margin:0; }
.section-sub { color:var(--muted); font-size:.84rem; margin:.2rem 0 0; }

/* ================= KPI CARDS (lavish) ================= */
.lux-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 4px 0 18px; }
.lux-kpi {
    position: relative; background: #ffffff; border-radius: 16px; padding: 18px 20px 16px;
    border: 1px solid #e0e7ff; overflow: hidden;
    box-shadow: 0 12px 28px -14px rgba(79, 70, 229, 0.35);
    transition: transform .25s ease, box-shadow .25s ease;
}
.lux-kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 34px -14px rgba(79, 70, 229, 0.45); }
.lux-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--accent); }
.lux-kpi-icon {
    position: absolute; right: 16px; top: 16px; width: 42px; height: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.3rem; background: var(--soft);
}
.lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; padding-right: 48px; }
.lux-kpi-value { font-size: 1.6rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
.lux-kpi-value.green { color: #059669; }
.lux-kpi-value.red { color: #dc2626; }
.lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

/* Native widgets */
label p, label[data-testid="stWidgetLabel"] p { color:#34405d!important; font-weight:750!important; }
[data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { background:white!important; border-color:#e1e5ef!important; border-radius:11px!important; min-height:44px; }
[data-testid="stForm"] { background:white; border:1px solid #e6e9f2!important; border-radius:20px!important; padding:1.25rem 1.35rem!important; box-shadow:0 10px 30px rgba(35,41,70,.07); }
[data-testid="stFileUploaderDropzone"] { background:#f8f7ff; border:1.5px dashed #a99af5; border-radius:16px; }

/* Buttons: defaults and named action colours */
div.stButton > button, div.stDownloadButton > button, [data-testid="stFormSubmitButton"] button { border:0!important; border-radius:12px!important; min-height:44px; font-weight:800!important; transition:.2s ease; box-shadow:0 7px 18px rgba(50,55,90,.12); }
div.stButton > button:hover, div.stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] button:hover { transform:translateY(-2px); box-shadow:0 11px 24px rgba(50,55,90,.18); }
div.stButton > button { background:linear-gradient(90deg,#6848ef,#885cf7)!important; color:white!important; }
div.stButton > button p { color:white!important; }
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

/* ================= ✨ LAVISH TABLE ================= */
.slux-head-bar {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 16px 22px; border-radius: 18px 18px 0 0;
    background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
}
.slux-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
.slux-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
.slux-badge {
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
    padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
}
.st-key-mst_table_wrap {
    background: #ffffff !important; overflow: auto !important; padding: 0 !important;
    border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important; border-radius: 0 !important;
}
.st-key-mst_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-mst_table_wrap [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important; }
.st-key-mst_table_wrap [data-testid="stColumn"], .st-key-mst_table_wrap [data-testid="column"] {
    padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
}
div[class*="st-key-msthead"] {
    position: sticky !important; top: 0 !important; z-index: 5 !important;
    background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
}
div[class*="st-key-msthead"] [data-testid="stColumn"], div[class*="st-key-msthead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
.slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
.slux-th.c { text-align: center; }
.slux-th.r { text-align: right; }
div[class*="st-key-mstrow_"] {
    padding: 9px 0 !important; background: #ffffff;
    border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
}
div[class*="st-key-mstrow_odd"] { background: #fafaff; }
div[class*="st-key-mstrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
div[class*="st-key-mstrow_"] p { margin: 0 !important; }
div[class*="st-key-mstrow_"].inactive-row { opacity: .6; }

.slux-cell { font-size: .87rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
.slux-strong { font-weight: 800; color: #0f172a; }
.slux-soft { color: #475569; font-weight: 600; }
.slux-muted { color: #cbd5e1; }
.slux-num {
    display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
    align-items: center; justify-content: center;
    background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
    font-weight: 800; font-size: .72rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
}
.slux-chip {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
    padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
}
.slux-chip.item { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }
.slux-pill {
    display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
    background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
    border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .5px; text-transform: uppercase;
}
.mst-amt { text-align: right; font-weight: 900; color: #4f46e5; font-variant-numeric: tabular-nums; }
.mst-pct { display:inline-block; padding: 3px 10px; border-radius: 8px; background: #fffbeb; border: 1px solid #fde68a; color: #b45309; font-weight: 900; font-size: .8rem; }
.status-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 11px; border-radius: 999px; border: 1px solid transparent;
    font-size: .7rem; font-weight: 800; letter-spacing: .4px; white-space: nowrap;
}
.status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
.status-green  { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
.status-red    { background: #fee2e2; color: #b91c1c; border-color: #fecaca; }
.status-yellow { background: #fef9c3; color: #a16207; border-color: #fde68a; }
.status-grey   { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }

/* Single ⚙️ popover button at row start */
div[class*="st-key-mstpop_"] button {
    width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
    padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
    background: rgba(99,102,241,0.14) !important; border: 1px solid rgba(99,102,241,0.3) !important;
    box-shadow: none !important; transition: all .2s ease !important;
}
div[class*="st-key-mstpop_"] button:hover {
    background: #6366f1 !important; border-color: #818cf8 !important;
    transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(99,102,241,.6) !important;
}
div[class*="st-key-mstpop_"] button p, div[class*="st-key-mstpop_"] button span { color: #1e293b !important; }
div[class*="st-key-mstpop_"] button svg { display: none !important; }
/* Red delete buttons */
div[class*="st-key-mst_del_"] button, .st-key-mst_confirm_del button { background: linear-gradient(90deg,#ef4444,#dc2626) !important; }
.st-key-mst_cancel_del button { background: #f1f5f9 !important; box-shadow: none !important; }
.st-key-mst_cancel_del button p { color: #334155 !important; }

.slux-foot {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
    border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
    box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
    font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
}
.slux-foot small { color: #6366f1; font-weight: 700; letter-spacing: .5px; margin-left: 10px; text-transform: none; font-size: .8rem; }
.slux-foot-badge { background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 5px 14px; border-radius: 999px; font-size: .75rem; letter-spacing: .5px; }
.page-count { text-align: center; font-size: 1rem; font-weight: 800; color: #4338ca; margin-top: 10px; }
.slux-empty {
    background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
    text-align: center; color: #64748b; font-weight: 600;
}
.slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }
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

# --- Categories (Vendor Name, Payment From, Payment Type included) ---
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
# 30s cache; kisi bhi insert/update/delete/status-toggle ke baad
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

# --- BULK UPLOAD DIALOG POPUP ---
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

# --- EDIT DIALOG POPUP (WITH DIRECT SUPABASE FETCH) ---
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
                # FIX: galat Rate (jaise "abc") par pehle poora dialog crash ho jaata tha
                try:
                    rate_val = float(raw_rate_ed) if raw_rate_ed.strip() != '' else None
                except ValueError:
                    rate_val = "INVALID"
            
        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if submitted:
            if rate_val == "INVALID":
                st.error("⚠️ Rate must be a valid number.")
            else:
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

# --- DELETE CONFIRMATION DIALOG (pehle ek click me turant delete ho jaata tha) ---
@st.dialog("🗑️ Delete Record")
def delete_record_dialog(row_data):
    st.markdown(
        f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
<div style="font-weight:900;color:#991b1b;font-size:1rem;">{html.escape(str(row_data.get('option_value','') or '-'))}</div>
<div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">Category: {html.escape(str(row_data.get('category','') or '-'))}</div>
</div>
<p style="color:#475569;">Ye option permanently delete ho jayega aur baaki pages ke dropdown me nahi dikhega. Agar sirf chhupana hai to <b>Deactivate</b> karein. Kya aap sure hain?</p>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="mst_cancel_del", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="mst_confirm_del", use_container_width=True):
            try:
                supabase.table(master_table_name).delete().eq("id", row_data['id']).execute()
                clear_master_cache()
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

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


# --- LAVISH CELL HELPERS ---
_MUTED = "<div class='slux-cell'><span class='slux-muted'>—</span></div>"

def _clean(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "null") else s

def _txt(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return _MUTED
    e = html.escape(s)
    return f"<div class='slux-cell {extra_cls}' title='{e}'>{e}</div>"

def _chip(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return _MUTED
    e = html.escape(s)
    return f"<div class='slux-cell' title='{e}'><span class='slux-chip {extra_cls}'>{e}</span></div>"

def _pill(v):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-pill'>{html.escape(s)}</span></div>"

def _badge(text, color):
    return f"<div class='slux-cell'><span class='status-badge status-{color}'>{html.escape(str(text))}</span></div>"

def _active_badge(v):
    return _badge("Active", "green") if bool(v) else _badge("Inactive", "red")

def _stn_badge(v):
    s = _clean(v)
    if not s:
        return _MUTED
    return _badge(s, "yellow" if s.lower() == "required" else "grey")

def _rate(v):
    n = pd.to_numeric(v, errors="coerce")
    if pd.isna(n):
        return _MUTED
    return f"<div class='slux-cell mst-amt'>₹ {float(n):,.2f}</div>"

def _pct(v):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div style='text-align:center;'><span class='mst-pct'>{html.escape(s.rstrip('%'))}%</span></div>"

def _details(row):
    """Compact extra details for the 'View All' table."""
    parts = []
    for label, key in (("📱", "mobile"), ("PAN", "pan"), ("GST", "gst"), ("%", "percentage"), ("", "item_description"), ("STN", "stn_status"), ("Mat", "material_of")):
        val = _clean(row.get(key))
        if val and not (key in ("stn_status", "material_of") and row.get("category") != "Item Code"):
            parts.append(f"{label} {val}".strip())
    rate_n = pd.to_numeric(row.get("rate"), errors="coerce")
    if pd.notna(rate_n):
        parts.append(f"₹ {float(rate_n):,.2f}")
    return " • ".join(parts)


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
active_pct = (active_count / total_count * 100) if total_count else 0

def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

st.markdown(
    '<div class="lux-kpi-grid">'
    + _kpi("🗂️", "Total Records", f"{total_count:,}", "All categories", "linear-gradient(90deg,#7657ff,#b14cff)", "#f3efff")
    + _kpi("✅", "Active Options", f"{active_count:,}", f"{active_pct:.0f}% of all records", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5", "green")
    + _kpi("🏷️", "Categories", f"{category_count:,}", f"of {len(categories)} available", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb")
    + _kpi("🚫", "Inactive Options", f"{inactive_count:,}", "Hidden from dropdowns", "linear-gradient(90deg,#ec4899,#ef4444)", "#fdf2f8", "red" if inactive_count else "")
    + '</div>',
    unsafe_allow_html=True,
)

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
      <div class="section-sub">Filter, search or download — click ⚙️ on any row to edit, activate/deactivate or delete.</div>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.2, 1.5, .9])
    with f1:
        filter_cat = st.selectbox("Category", ["View All"] + categories, key="table_category")
    with f2:
        search_text = st.text_input("Search Records", placeholder="Search option, item, mobile, PAN, GST...", key="table_search")
    with f3:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"], key="table_status")

    # Filter/search badalne par page 1 par wapas
    _sig = f"{filter_cat}|{search_text}|{status_filter}"
    if st.session_state.get("mst_last_sig") != _sig:
        st.session_state.mst_last_sig = _sig
        st.session_state.mst_page = 1
    if "mst_page" not in st.session_state:
        st.session_state.mst_page = 1

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

            # Sort: category, then option value (easy to scan)
            if not df.empty:
                df = df.sort_values(by=["category", "option_value"], key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)

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
                st.markdown(f'<div class="hint" style="margin-top:.1rem">🔎 Showing <b>{result_count:,}</b> matching record(s). Click <b>⚙️</b> on any row for Edit / Activate / Delete.</div>', unsafe_allow_html=True)

            if not df.empty:
                # --- Columns depend on the selected category ---
                if filter_cat == "Team Name":
                    COL_RATIOS = [0.55, 0.5, 2.2, 1.3, 1.3, 1.6, 0.8, 1.0]
                    COL_LABELS = ["⚙️", "#", "TEAM NAME", "MOBILE", "PAN", "GST", "%", "STATUS"]
                    center_idx, right_idx = (0, 1, 6, 7), ()
                elif filter_cat == "Vendor Name":
                    COL_RATIOS = [0.55, 0.5, 2.4, 1.3, 1.3, 1.7, 1.0]
                    COL_LABELS = ["⚙️", "#", "VENDOR NAME", "MOBILE", "PAN", "GST", "STATUS"]
                    center_idx, right_idx = (0, 1, 6), ()
                elif filter_cat == "Item Code":
                    COL_RATIOS = [0.55, 0.5, 1.5, 3.2, 1.0, 1.1, 1.0, 1.0]
                    COL_LABELS = ["⚙️", "#", "ITEM CODE", "ITEM DESCRIPTION", "MATERIAL OF", "STN STATUS", "RATE", "STATUS"]
                    center_idx, right_idx = (0, 1, 7), (6,)
                elif filter_cat == "View All":
                    COL_RATIOS = [0.55, 0.5, 1.4, 2.2, 3.2, 1.0]
                    COL_LABELS = ["⚙️", "#", "CATEGORY", "OPTION VALUE", "DETAILS", "STATUS"]
                    center_idx, right_idx = (0, 1, 5), ()
                else:
                    COL_RATIOS = [0.55, 0.5, 1.6, 4.0, 1.0]
                    COL_LABELS = ["⚙️", "#", "CATEGORY", "OPTION VALUE", "STATUS"]
                    center_idx, right_idx = (0, 1, 4), ()

                min_w = 1150 if filter_cat in ("Item Code", "Team Name", "View All") else 900
                st.markdown(
                    f"<style>.st-key-mst_table_wrap [data-testid='stHorizontalBlock'],"
                    f".st-key-mst_table_wrap div[class*='st-key-msthead'],"
                    f".st-key-mst_table_wrap div[class*='st-key-mstrow_'] {{ min-width: {min_w}px !important; }}</style>",
                    unsafe_allow_html=True,
                )

                # --- Pagination (25 rows / page — Item Code me hazaaron rows ho sakti hain) ---
                rows_per_page = 25
                total_pages = max(1, math.ceil(result_count / rows_per_page))
                st.session_state.mst_page = min(max(1, st.session_state.mst_page), total_pages)
                start_idx = (st.session_state.mst_page - 1) * rows_per_page
                end_idx = start_idx + rows_per_page
                df_page = df.iloc[start_idx:end_idx]

                n_active = int(df["is_active"].fillna(False).astype(bool).sum())
                st.markdown(
                    '<div class="slux-head-bar">'
                    f'<div class="slux-title">🗂️ {html.escape(filter_cat)}<span>sorted by category & name</span></div>'
                    f'<div class="slux-badge">✅ {n_active:,} active / {result_count:,}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                table_kwargs = {"height": 560} if len(df_page) > 10 else {}
                with st.container(key="mst_table_wrap", **table_kwargs):
                    with st.container(key="msthead"):
                        h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
                        for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                            cls = " c" if i in center_idx else (" r" if i in right_idx else "")
                            h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

                    for page_pos, (_, r) in enumerate(df_page.iterrows()):
                        row_to_edit = r.to_dict()
                        rid = row_to_edit.get("id")
                        serial_no = start_idx + page_pos + 1
                        parity = "odd" if serial_no % 2 else "even"
                        is_active = bool(row_to_edit.get("is_active")) if pd.notna(row_to_edit.get("is_active")) else False

                        with st.container(key=f"mstrow_{parity}_{rid}"):
                            rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                            with rcols[0]:
                                with st.container(key=f"mstpop_{rid}"):
                                    with st.popover("⚙️"):
                                        st.markdown(f"**{html.escape(_clean(row_to_edit.get('option_value')) or '-')}**")
                                        if st.button("✏️ Edit Record", key=f"mst_edit_{rid}", use_container_width=True):
                                            edit_dialog(row_to_edit)
                                        status_text = "🚫 Deactivate" if is_active else "✅ Activate"
                                        if st.button(status_text, key=f"mst_toggle_{rid}", use_container_width=True):
                                            try:
                                                supabase.table(master_table_name).update({"is_active": not is_active}).eq("id", rid).execute()
                                                clear_master_cache()
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Status update failed: {e}")
                                        if st.button("🗑️ Delete", key=f"mst_del_{rid}", use_container_width=True):
                                            delete_record_dialog(row_to_edit)

                            rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)

                            if filter_cat == "Team Name":
                                rcols[2].markdown(_txt(f"👷 {_clean(row_to_edit.get('option_value'))}", "slux-strong"), unsafe_allow_html=True)
                                rcols[3].markdown(_chip(row_to_edit.get('mobile')), unsafe_allow_html=True)
                                rcols[4].markdown(_chip(row_to_edit.get('pan')), unsafe_allow_html=True)
                                rcols[5].markdown(_chip(row_to_edit.get('gst')), unsafe_allow_html=True)
                                rcols[6].markdown(_pct(row_to_edit.get('percentage')), unsafe_allow_html=True)
                                rcols[7].markdown(f"<div style='text-align:center;'>{_active_badge(is_active)}</div>", unsafe_allow_html=True)
                            elif filter_cat == "Vendor Name":
                                rcols[2].markdown(_txt(f"🏭 {_clean(row_to_edit.get('option_value'))}", "slux-strong"), unsafe_allow_html=True)
                                rcols[3].markdown(_chip(row_to_edit.get('mobile')), unsafe_allow_html=True)
                                rcols[4].markdown(_chip(row_to_edit.get('pan')), unsafe_allow_html=True)
                                rcols[5].markdown(_chip(row_to_edit.get('gst')), unsafe_allow_html=True)
                                rcols[6].markdown(f"<div style='text-align:center;'>{_active_badge(is_active)}</div>", unsafe_allow_html=True)
                            elif filter_cat == "Item Code":
                                rcols[2].markdown(_chip(row_to_edit.get('option_value'), "item"), unsafe_allow_html=True)
                                rcols[3].markdown(_txt(row_to_edit.get('item_description'), "slux-soft"), unsafe_allow_html=True)
                                rcols[4].markdown(_pill(row_to_edit.get('material_of')), unsafe_allow_html=True)
                                rcols[5].markdown(_stn_badge(row_to_edit.get('stn_status')), unsafe_allow_html=True)
                                rcols[6].markdown(_rate(row_to_edit.get('rate')), unsafe_allow_html=True)
                                rcols[7].markdown(f"<div style='text-align:center;'>{_active_badge(is_active)}</div>", unsafe_allow_html=True)
                            elif filter_cat == "View All":
                                rcols[2].markdown(_pill(row_to_edit.get('category')), unsafe_allow_html=True)
                                rcols[3].markdown(_txt(row_to_edit.get('option_value'), "slux-strong"), unsafe_allow_html=True)
                                rcols[4].markdown(_txt(_details(row_to_edit), "slux-soft"), unsafe_allow_html=True)
                                rcols[5].markdown(f"<div style='text-align:center;'>{_active_badge(is_active)}</div>", unsafe_allow_html=True)
                            else:
                                rcols[2].markdown(_pill(row_to_edit.get('category')), unsafe_allow_html=True)
                                rcols[3].markdown(_txt(row_to_edit.get('option_value'), "slux-strong"), unsafe_allow_html=True)
                                rcols[4].markdown(f"<div style='text-align:center;'>{_active_badge(is_active)}</div>", unsafe_allow_html=True)

                shown_from = start_idx + 1
                shown_to = min(end_idx, result_count)
                st.markdown(
                    '<div class="slux-foot">'
                    f'<div>{result_count:,} record{"s" if result_count != 1 else ""}<small>Showing {shown_from}–{shown_to}</small></div>'
                    f'<div><span class="slux-foot-badge">Page {st.session_state.mst_page} of {total_pages}</span></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if total_pages > 1:
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    p1, p2, p3 = st.columns([1, 2, 1])
                    with p1:
                        if st.button("⬅️ Previous", use_container_width=True, disabled=st.session_state.mst_page == 1, key="mst_prev"):
                            st.session_state.mst_page -= 1
                            st.rerun()
                    with p2:
                        st.markdown(f"<div class='page-count'>Page {st.session_state.mst_page} of {total_pages}</div>", unsafe_allow_html=True)
                    with p3:
                        if st.button("Next ➡️", use_container_width=True, disabled=st.session_state.mst_page == total_pages, key="mst_next"):
                            st.session_state.mst_page += 1
                            st.rerun()
            else:
                st.markdown('<div class="slux-empty"><div>🔎</div>No records match the selected filters.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="slux-empty"><div>🗂️</div>No options registered yet for {html.escape(filter_cat)}.</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"⚠️ Table Error: Please ensure all required columns exist in Supabase. Details: {e}")
