import streamlit as st
import pandas as pd
import datetime
import io
import json
import html
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Quotation List", page_icon="📄", layout="wide")

# --- NEW: MOBILE VIEW TOGGLE STATE ---
if 'quo_view_mode' not in st.session_state:
    st.session_state.quo_view_mode = "table"

# --- 2. LAVISH CUSTOM CSS (Matches Screenshots & Sidebar) ---
st.markdown("""
    <style>
    /* Dark Premium Theme & Backgrounds */
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Primary Action Buttons */
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
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
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

    input:disabled, div[data-baseweb="input"] input:disabled, textarea:disabled {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
        opacity: 1 !important;
    }

    /* Data Editor Table Header */
    [data-testid="stDataFrame"] th {
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
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

    /* =========================================================
       NEW: MOBILE-FRIENDLY CARD VIEW (light theme, matches this page)
       ========================================================= */
    .quo-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
    }
    .quo-card-title { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; }
    .quo-card-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
    .quo-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; gap: 10px; }
    .quo-card-row:last-child { border-bottom: none; }
    .quo-card-label { color: #64748b; font-weight: 700; white-space: nowrap; text-transform: uppercase; font-size: 0.75rem; }
    .quo-card-value { color: #0f172a; font-weight: 600; text-align: right; }
    .quo-card-value.amount { color: #4f46e5; font-weight: 800; font-size: 0.95rem; }

    /* ================= LAVISH KPI STRIP ================= */
    .lux-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 4px 0 22px; }
    @media (max-width: 900px) { .lux-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
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
        display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
        background: var(--soft);
    }
    .lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; }
    .lux-kpi-value { font-size: 1.65rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

    /* ================= LAVISH TABLE ================= */
    .lux-table-wrap {
        background: #ffffff; border-radius: 18px; border: 1px solid #e0e7ff; overflow: hidden;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
    }
    .lux-table-head {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 16px 22px;
        background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
    }
    .lux-table-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
    .lux-table-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
    .lux-table-badge {
        background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
        padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
    }
    .lux-scroll { max-height: 560px; overflow: auto; }
    table.lux-table { width: 100%; min-width: 980px; border-collapse: separate; border-spacing: 0; font-size: .88rem; }
    .lux-table thead th {
        position: sticky; top: 0; z-index: 2;
        background: #eef2ff; color: #3730a3;
        font-size: .7rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase;
        padding: 13px 14px; text-align: left; white-space: nowrap;
        border-bottom: 2px solid #c7d2fe;
    }
    .lux-table thead th.r, .lux-table td.r { text-align: right; }
    .lux-table thead th.c, .lux-table td.c { text-align: center; }
    .lux-table tbody td {
        padding: 12px 14px; color: #1e293b; vertical-align: middle;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease;
    }
    .lux-table tbody tr:nth-child(even) td { background: #fafaff; }
    .lux-table tbody tr:hover td { background: #eef2ff; }
    .lux-table tbody tr:hover td:first-child { box-shadow: inset 4px 0 0 #6366f1; }

    .lux-num {
        display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
        align-items: center; justify-content: center;
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
        font-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
    }
    .lux-date { font-weight: 800; color: #0f172a; white-space: nowrap; }
    .lux-date small { display: block; color: #94a3b8; font-weight: 600; font-size: .7rem; letter-spacing: .5px; }
    .lux-chip {
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
        padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
    }
    .lux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
    .lux-site { font-weight: 700; color: #0f172a; }
    .lux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .lux-proj { color: #475569; font-weight: 600; }
    .lux-amt { font-weight: 900; color: #4f46e5; white-space: nowrap; font-size: .95rem; }
    .lux-muted { color: #cbd5e1; }

    .lux-table tfoot td {
        position: sticky; bottom: 0; z-index: 2;
        background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border-top: 2px solid #c7d2fe; padding: 14px; font-weight: 900; color: #312e81;
        text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .lux-table tfoot td.r { font-size: 1.05rem; color: #4f46e5; letter-spacing: 0; }

    .lux-empty { padding: 48px 20px; text-align: center; color: #64748b; font-weight: 600; }
    .lux-empty div { font-size: 2.4rem; margin-bottom: 8px; }

    /* ================= ACTION BAR ================= */
    .lux-action-title {
        margin: 22px 0 8px; font-size: .78rem; font-weight: 800; letter-spacing: 1.2px;
        text-transform: uppercase; color: #4338ca; display: flex; align-items: center; gap: 8px;
    }
    .lux-action-title::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, #c7d2fe, transparent); }
    /* ================= ROW-WISE TABLE (inline Edit / Delete) ================= */
    .st-key-lux_thead {
        background: #eef2ff; border-left: 1px solid #e0e7ff; border-right: 1px solid #e0e7ff;
        border-bottom: 2px solid #c7d2fe; padding: 12px 14px;
    }
    .st-key-lux_thead p {
        margin: 0 !important; color: #3730a3; font-size: .7rem !important; font-weight: 800;
        letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap;
    }
    .st-key-lux_tbody {
        background: #ffffff; border-left: 1px solid #e0e7ff; border-right: 1px solid #e0e7ff;
    }
    .st-key-lux_tbody [data-testid="stVerticalBlock"] { gap: 0 !important; }
    div[class*="st-key-luxrow_"] {
        padding: 8px 14px; border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-luxrow_odd"] { background: #fafaff; }
    div[class*="st-key-luxrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-luxrow_"] p { margin: 0 !important; font-size: .88rem; color: #1e293b; }
    div[class*="st-key-luxrow_"] [data-testid="stHorizontalBlock"] { gap: .6rem !important; }

    /* Single inline Manage button (same idea as Site Data ⚙️ button) */
    div[class*="st-key-qmgr_"] button {
        width: 38px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; font-size: 1rem !important; transition: all .2s ease !important;
    }
    div[class*="st-key-qmgr_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    /* Danger-zone delete button inside the Manage dialog */
    div[class*="st-key-quo_del_now_"] button {
        background: linear-gradient(90deg, #ef4444, #dc2626) !important;
        box-shadow: 0 4px 10px -2px rgba(239,68,68,.5) !important;
    }

    /* Table footer */
    .lux-tfoot {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
        font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .lux-tfoot small { color: #6366f1; font-weight: 700; letter-spacing: .5px; margin-left: 10px; text-transform: none; font-size: .78rem; }
    .lux-tfoot .lux-tfoot-amt { font-size: 1.1rem; color: #4f46e5; letter-spacing: 0; }
    .lux-table-head { border-radius: 18px 18px 0 0; }

    /* Pager + delete dialog */
    .lux-pager-info { text-align: center; font-weight: 800; color: #4338ca; font-size: .85rem; padding-top: 8px; }
    .st-key-del_yes button { background: linear-gradient(90deg, #ef4444, #dc2626) !important; box-shadow: 0 4px 10px -2px rgba(239,68,68,.5) !important; }
    .st-key-del_cancel button { background: #f1f5f9 !important; color: #334155 !important; box-shadow: none !important; }
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

# --- 4. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_quotation_projects(workspace_name):
    try:
        res = supabase.table("site_data").select("*").eq("workspace", workspace_name).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if "Operator" in df.columns:
                mask = df["Operator"].astype(str).str.contains("uotat", case=False, na=False)
                return df[mask]
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["Project ID", "Site ID", "Site Name", "Cluster", "KM", "Project Name"])

@st.cache_data(ttl=60)
def fetch_item_master():
    tables_to_try = ["Item Code", "item_master", "items", "Item_Code"]
    for t in tables_to_try:
        try:
            res = supabase.table(t).select("*").limit(10000).execute()
            if res.data and len(res.data) > 0:
                df = pd.DataFrame(res.data)
                col_map = {}
                for c in df.columns:
                    cl = str(c).strip().lower()
                    if cl in ['item code', 'item_code', 'itemcode', 'code', 'material item']: col_map[c] = 'Item Code'
                    if cl in ['description', 'desc', 'item description', 'item_description']: col_map[c] = 'Description'
                    if cl in ['price', 'rate', 'amount', 'unit price']: col_map[c] = 'Price'
                df = df.rename(columns=col_map)
                if 'Item Code' in df.columns:
                    return df
        except Exception:
            continue
    return pd.DataFrame(columns=["Item Code", "Description", "Price"])

@st.cache_data(ttl=30)
def fetch_quotation_templates():
    try:
        res = supabase.table("quotation_templates").select("*").execute()
        if res.data:
            return res.data
    except:
        pass
    return []

# --- NEW: EGRESS OPTIMIZATION — cached KM lookup used inside the quotation
# dialog. Previously this ran on EVERY rerun while the dialog was open
# (every data-editor cell edit re-triggers the whole script) — now cached
# for 60s per Site ID.
@st.cache_data(ttl=60, show_spinner=False)
def fetch_site_km_cached(site_id):
    if not site_id:
        return ""
    try:
        res_exc = supabase.table("Excalation Matrix").select("KM").eq("Site ID", site_id).execute()
        if res_exc.data and len(res_exc.data) > 0:
            km_val = res_exc.data[0].get("KM", "")
            return "" if pd.isna(km_val) else str(km_val)
    except Exception:
        pass
    return ""

# Load Master Data First so cluster mapping is ready
df_projects = fetch_quotation_projects(st.session_state.get('active_workspace', 'VISPL'))
project_list = df_projects["Project ID"].dropna().unique().tolist() if not df_projects.empty else []

@st.cache_data(ttl=30, show_spinner=False)
def fetch_quotations_cached(active_ws, cluster_map_items):
    """cluster_map_items is a hashable tuple version of the Project ID -> Cluster map,
    passed in so caching stays correct even if site_data changes."""
    try:
        # STRICT WORKSPACE FILTERING (No cross-contamination)
        res = supabase.table("quotations").select("*").eq("workspace", active_ws).execute()

        if res.data:
            df = pd.DataFrame(res.data)
            # --- Robust Cluster mapping from site_data using Project ID ---
            if not df.empty and "Project ID" in df.columns and cluster_map_items:
                proj_cluster_map = dict(cluster_map_items)
                df["Cluster"] = df["Project ID"].map(proj_cluster_map).fillna("")
            else:
                df["Cluster"] = ""
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "Quotation Name", "Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project Name", "Quotation Amount", "Status"])


def fetch_quotations():
    """Thin wrapper kept so existing call sites (incl. after inserts/updates/deletes) don't need changes."""
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    if not df_projects.empty and "Project ID" in df_projects.columns and "Cluster" in df_projects.columns:
        cluster_map_items = tuple(zip(df_projects["Project ID"], df_projects["Cluster"]))
    else:
        cluster_map_items = tuple()
    return fetch_quotations_cached(active_ws, cluster_map_items)

df_items = fetch_item_master()
if not df_items.empty:
    df_items["Description"] = df_items["Description"].fillna("")
    df_items["Display"] = df_items["Item Code"].astype(str) + " | " + df_items["Description"].astype(str)
    
    item_display_list = df_items["Display"].tolist()
    item_code_list = df_items["Item Code"].astype(str).tolist()
    combined_item_options = item_display_list + item_code_list 
    
    display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))
    display_to_price = dict(zip(df_items["Display"], df_items["Price"]))
else:
    combined_item_options = []
    display_to_desc = {}
    display_to_price = {}

templates_data = fetch_quotation_templates()
template_names = [t["Template Name"] for t in templates_data]

# --- 5. INITIALIZE SESSION STATE ---
st.session_state.quotations_df = fetch_quotations()

# --- 6. DIALOG FOR ADD/VIEW QUOTATION ---
@st.dialog("⚙️ Manage Quotation (View / Edit / Delete)", width="large")
def quotation_dialog(quotation_data=None):
    st.caption("Details and items for project estimation")
    
    is_new = quotation_data is None
    
    quo_id = None
    default_name = f"Quotation {len(st.session_state.quotations_df) + 100}" if is_new else quotation_data.get("Quotation Name", "")
    default_date = datetime.date.today() if is_new else pd.to_datetime(quotation_data.get("Date", datetime.date.today())).date()
    
    # --- MODIFIED LOGIC: Default blank for new, filter out already used Project IDs ---
    default_proj = quotation_data.get("Project ID", "") if quotation_data else ""
    
    used_projs = []
    if not st.session_state.quotations_df.empty and "Project ID" in st.session_state.quotations_df.columns:
        used_projs = st.session_state.quotations_df["Project ID"].dropna().unique().tolist()
        
    available_opts = [p for p in project_list if p not in used_projs]
    if not is_new and default_proj and default_proj not in available_opts:
        available_opts.append(default_proj)
        
    dynamic_options = [""] + available_opts
    
    # Top Section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        quo_name = st.text_input("QUOTATION *", value=default_name)
    with col2:
        quo_date = st.date_input("QUOTATION DATE *", value=default_date)
    with col3:
        sel_idx = dynamic_options.index(default_proj) if default_proj in dynamic_options else 0
        sel_proj = st.selectbox("PROJECT ID *", options=dynamic_options, index=sel_idx)
    
    auto_site_id = ""
    auto_site_name = ""
    auto_cluster = ""
    auto_km = "" 
    auto_proj_name = ""
    if sel_proj:
        proj_row = df_projects[df_projects["Project ID"] == sel_proj]
        if not proj_row.empty:
            auto_site_id = str(proj_row.iloc[0].get("Site ID", ""))
            auto_site_name = str(proj_row.iloc[0].get("Site Name", ""))
            auto_cluster = str(proj_row.iloc[0].get("Cluster", ""))

            if auto_site_id:
                auto_km = fetch_site_km_cached(auto_site_id)
            auto_proj_name = str(proj_row.iloc[0].get("Project Name", ""))
            
    with col4:
        st.text_input("SITE ID *", value=auto_site_id, disabled=True)
        
    col5, col6, col_km, col7, col8 = st.columns(5)
    with col5:
        st.text_input("SITE NAME", value=auto_site_name, disabled=True)
    with col6:
        st.text_input("CLUSTER", value=auto_cluster, disabled=True)
    with col_km:
        st.text_input("KM", value=auto_km, disabled=True) 
    with col7:
        st.text_input("PROJECT NAME", value=auto_proj_name, disabled=True)
    with col8:
        selected_template = st.selectbox("QUOTATION TEMPLATE", options=["-- Select Template --"] + template_names)
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_list_title, col_add_btn = st.columns([8, 2])
    with col_list_title:
        st.markdown('<div class="modal-section-title" style="margin-top:0;">📚 Listing Premium Items <span style="font-size:0.8rem; color:#64748b; font-weight:500;">(Use plus (+) icon below to add lines)</span></div>', unsafe_allow_html=True)
    
    editor_key = f"quo_items_{quo_name}_{sel_proj}"
    widget_key = f"widget_{editor_key}"
    
    saved_proj = quotation_data.get("Project ID", "") if quotation_data else ""
    
    if editor_key not in st.session_state:
        if is_new or sel_proj != saved_proj:
            st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])
        else:
            try:
                res_items = supabase.table("quotation_items").select("*").eq("Quotation Name", quo_name).execute()
                if res_items.data and len(res_items.data) > 0:
                    temp_df = pd.DataFrame(res_items.data)[["Item Code", "Description", "Qty", "Price", "Total"]]
                    st.session_state[editor_key] = temp_df
                else:
                    st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])
            except:
                st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])

    if selected_template and selected_template != "-- Select Template --":
        for t in templates_data:
            if t["Template Name"] == selected_template:
                try:
                    raw_items = json.loads(t["Items Data"]) if isinstance(t["Items Data"], str) else t["Items Data"]
                    loaded_rows = []
                    for ri in raw_items:
                        qty_val = int(ri.get("Qty", 1))
                        price_val = int(ri.get("Price", 0))
                        loaded_rows.append({
                            "Item Code": ri.get("Item Code", ""),
                            "Description": ri.get("Description", ""),
                            "Qty": qty_val,
                            "Price": price_val,
                            "Total": price_val * qty_val
                        })
                    if loaded_rows:
                        st.session_state[editor_key] = pd.DataFrame(loaded_rows)
                except:
                    pass

    with col_add_btn:
        if st.button("➕ Add New Row", use_container_width=True):
            new_item = pd.DataFrame([{"Item Code": None, "Description": "", "Qty": 1, "Price": 0, "Total": 0}])
            st.session_state[editor_key] = pd.concat([st.session_state[editor_key], new_item], ignore_index=True)

    if widget_key in st.session_state:
        w_state = st.session_state[widget_key]
        edits = w_state.get("edited_rows", {})
        adds = w_state.get("added_rows", [])
        dels = w_state.get("deleted_rows", [])
        
        if edits or adds or dels:
            curr_df = st.session_state[editor_key].copy()
            if dels: curr_df = curr_df.drop(dels).reset_index(drop=True)
            if edits:
                for str_idx, changes in edits.items():
                    idx = int(str_idx)
                    if idx < len(curr_df):
                        for col, val in changes.items():
                            curr_df.at[idx, col] = val
                        if "Item Code" in changes:
                            disp = str(changes["Item Code"])
                            if " | " in disp:
                                code_only = disp.split(" | ")[0].strip()
                                curr_df.at[idx, "Item Code"] = code_only
                                if disp in display_to_desc:
                                    curr_df.at[idx, "Description"] = display_to_desc[disp]
                                    curr_df.at[idx, "Price"] = display_to_price[disp]
                            else:
                                match = df_items[df_items["Item Code"] == disp]
                                if not match.empty:
                                    curr_df.at[idx, "Description"] = match.iloc[0]["Description"]
                                    curr_df.at[idx, "Price"] = match.iloc[0]["Price"]
                        qty = pd.to_numeric(curr_df.at[idx, "Qty"], errors='coerce')
                        price = pd.to_numeric(curr_df.at[idx, "Price"], errors='coerce')
                        curr_df.at[idx, "Total"] = (0 if pd.isna(qty) else int(qty)) * (0 if pd.isna(price) else int(price))
            if adds:
                for row in adds:
                    new_row = {"Item Code": row.get("Item Code"), "Description": "", "Qty": 1, "Price": 0, "Total": 0}
                    if "Item Code" in row and pd.notna(row["Item Code"]):
                        disp = str(row["Item Code"])
                        if " | " in disp:
                            code_only = disp.split(" | ")[0].strip()
                            new_row["Item Code"] = code_only
                            if disp in display_to_desc:
                                new_row["Description"] = display_to_desc[disp]
                                new_row["Price"] = display_to_price[disp]
                                new_row["Total"] = display_to_price[disp] * 1
                    curr_df = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state[editor_key] = curr_df
            del st.session_state[widget_key]

    edited_items_df = st.data_editor(
        st.session_state[editor_key],
        key=widget_key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=300,
        column_config={
            "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=combined_item_options, required=True, width="medium"),
            "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
            "Qty": st.column_config.NumberColumn("QTY", min_value=0, default=1, format="%d", alignment="center", width="small"),
            "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d", alignment="center", width="small"),
            "Total": st.column_config.NumberColumn("TOTAL", disabled=True, format="₹ %d", alignment="center", width="medium")
        }
    )

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
                
            header_data = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
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
                if not is_new and "id" in quotation_data and pd.notna(quotation_data["id"]):
                    supabase.table("quotations").update(header_data).eq("id", quotation_data["id"]).execute()
                else:
                    supabase.table("quotations").insert(header_data).execute()
                
                supabase.table("quotation_items").delete().eq("Quotation Name", quo_name).execute()
                
                if not edited_items_df.empty:
                    items_to_insert = []
                    for _, r in edited_items_df.iterrows():
                        if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip() != "":
                            clean_code = str(r["Item Code"]).split(" | ")[0].strip()
                            items_to_insert.append({
                                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                                "Quotation Name": quo_name,
                                "Item Code": clean_code,
                                "Description": str(r["Description"]),
                                "Qty": int(r["Qty"]) if pd.notna(r["Qty"]) else 0,
                                "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0,
                                "Total": int(r["Total"]) if pd.notna(r["Total"]) else 0
                            })
                    if items_to_insert:
                        supabase.table("quotation_items").insert(items_to_insert).execute()
                
                fetch_quotations_cached.clear()
                st.session_state.quotations_df = fetch_quotations()
                st.success("✅ Quotation Saved Successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Database Error: {e}")

    # ---------------------------------------------------------------
    # --- DANGER ZONE: DELETE THIS QUOTATION (only for existing records)
    # ---------------------------------------------------------------
    if not is_new:
        del_name = quotation_data.get("Quotation Name", "")
        del_key = quotation_data.get("id", del_name)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="border-top: 1px dashed rgba(239,68,68,0.4); margin-top: 10px; padding-top: 15px;">
                <div style="color:#dc2626; font-weight:800; font-size:0.85rem; letter-spacing:1px; text-transform:uppercase;">⚠️ Danger Zone</div>
            </div>
        """, unsafe_allow_html=True)
        confirm_del = st.checkbox(
            "Main is quotation ko permanently DELETE karna chahta hoon (is action ko undo nahi kiya ja sakta)",
            key=f"quo_del_confirm_{del_key}"
        )
        if confirm_del:
            if st.button("🗑️ Delete This Quotation Permanently", key=f"quo_del_now_{del_key}", use_container_width=True):
                try:
                    supabase.table("quotations").delete().eq("Quotation Name", del_name).execute()
                    supabase.table("quotation_items").delete().eq("Quotation Name", del_name).execute()
                    fetch_quotations_cached.clear()
                    st.session_state.quotations_df = fetch_quotations()
                    st.toast(f"✅ Deleted {del_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Deleting Quotation: {e}")

# --- 7. TOP HEADER & FILTERS ---
col_head1, col_head2, col_head3, col_head4, col_head5 = st.columns([3.5, 1.8, 1.6, 1.6, 1.6])
with col_head1:
    st.markdown("<h1 style='margin:0; color:#0f172a;'>Quotation List</h1>", unsafe_allow_html=True)
with col_head2:
    search_q = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")
with col_head3:
    if st.button("➕ Add Record", type="primary", use_container_width=True):
        quotation_dialog()
with col_head4:
    # --- NEW: MOBILE / TABLE VIEW TOGGLE ---
    toggle_label = "📱 Mobile View" if st.session_state.quo_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="quo_view_mode_toggle"):
        st.session_state.quo_view_mode = "cards" if st.session_state.quo_view_mode == "table" else "table"
        st.rerun()
with col_head5:
    with st.popover("📥 Download Options", use_container_width=True):
        st.markdown("##### Filter by Date Range")
        d_from = st.date_input("From Date", value=datetime.date.today() - datetime.timedelta(days=30))
        d_to = st.date_input("To Date", value=datetime.date.today())
        
        if st.button("📊 Generate Excel", type="primary", use_container_width=True):
            try:
                df_base = st.session_state.quotations_df.copy()
                if search_q:
                    mask = df_base.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
                    df_base = df_base[mask]
                
                df_base['Date_Parsed'] = pd.to_datetime(df_base['Date'], errors='coerce').dt.date
                df_filtered = df_base[(df_base['Date_Parsed'] >= d_from) & (df_base['Date_Parsed'] <= d_to)]
                
                if df_filtered.empty:
                    df_filtered = df_base
                
                sheet1_df = df_filtered[["Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project Name", "Quotation Amount"]].copy()
                sheet1_df.columns = ["Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project", "Grand Total"]
                
                line_rows = []
                quotation_names = df_filtered["Quotation Name"].tolist()
                
                if quotation_names:
                    res_items = supabase.table("quotation_items").select("*").in_("Quotation Name", quotation_names).execute()
                    if res_items.data:
                        items_df = pd.DataFrame(res_items.data)
                        merged_df = pd.merge(items_df, df_filtered, on="Quotation Name", how="inner")
                        
                        for _, row in merged_df.iterrows():
                            p_id = row.get("Project ID", "")
                            clust = row.get("Cluster", "")
                            if not clust and not df_projects.empty:
                                match_proj = df_projects[df_projects["Project ID"] == p_id]
                                if not match_proj.empty:
                                    clust = match_proj.iloc[0].get("Cluster", "")

                            line_rows.append({
                                "Project ID": p_id,
                                "Site ID": row.get("Site ID", ""),
                                "Site Name": row.get("Site Name", ""),
                                "Cluster": clust,
                                "Project": row.get("Project Name", ""),
                                "Item Code": row.get("Item Code", ""),
                                "Item Description": row.get("Description", ""),
                                "Qty": row.get("Qty", 0),
                                "Price": row.get("Price", 0),
                                "Total": row.get("Total", 0)
                            })
                
                sheet2_df = pd.DataFrame(line_rows)
                if sheet2_df.empty:
                    sheet2_df = pd.DataFrame(columns=["Project ID", "Site ID", "Site Name", "Cluster", "Project", "Item Code", "Item Description", "Qty", "Price", "Total"])
                else:
                    sheet2_df = sheet2_df[["Project ID", "Site ID", "Site Name", "Cluster", "Project", "Item Code", "Item Description", "Qty", "Price", "Total"]]
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    sheet1_df.to_excel(writer, index=False, sheet_name='Site Details')
                    sheet2_df.to_excel(writer, index=False, sheet_name='Line Wise Items')
                
                st.download_button(
                    label="⬇️ Click Here to Download",
                    data=buffer.getvalue(),
                    file_name=f"Quotation_Export_{d_from}_to_{d_to}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Export Error: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. MAIN SCREEN QUOTATION LIST (lavish table or mobile cards) ---
df_display = st.session_state.quotations_df.copy()

# Newest quotations sabse upar
if not df_display.empty:
    if "id" in df_display.columns:
        df_display = df_display.sort_values(by="id", ascending=False).reset_index(drop=True)
    else:
        df_display = df_display.iloc[::-1].reset_index(drop=True)

if not df_display.empty and search_q:
    mask = df_display.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
    # FIX: reset_index zaroori hai, warna search ke baad galat row select/delete hoti thi
    df_display = df_display[mask].reset_index(drop=True)

disp_cols = ["Date", "Project ID", "Site ID", "Site Name", "Cluster", "Project Name", "Quotation Amount"]
for c in disp_cols + ["Quotation Name"]:
    if c not in df_display.columns:
        df_display[c] = ""


def _esc(v):
    """HTML-safe text; blank / NaN ko '—' dikhata hai."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan", "None"):
        return '<span class="lux-muted">—</span>'
    return html.escape(str(v))


def _amt(v):
    try:
        return f"₹ {int(float(v)):,}"
    except Exception:
        return "₹ 0"


def _delete_quotation(q_name):
    try:
        supabase.table("quotations").delete().eq("Quotation Name", q_name).execute()
        supabase.table("quotation_items").delete().eq("Quotation Name", q_name).execute()
        fetch_quotations_cached.clear()
        st.session_state.quotations_df = fetch_quotations()
        st.toast(f"✅ Deleted {q_name}")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting: {e}")



# ---------------- KPI STRIP (dono views me dikhega) ----------------
amounts = pd.to_numeric(df_display["Quotation Amount"], errors="coerce").fillna(0)
dates = pd.to_datetime(df_display["Date"], errors="coerce")
today = pd.Timestamp(datetime.date.today())
this_month = int(((dates.dt.year == today.year) & (dates.dt.month == today.month)).sum())
total_count = len(df_display)
total_value = int(amounts.sum())
avg_value = int(amounts.mean()) if total_count else 0
cluster_count = df_display["Cluster"].replace("", pd.NA).dropna().nunique()

st.markdown(
    '<div class="lux-kpi-grid">'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#6366f1,#8b5cf6);--soft:#eef2ff;">'
    f'<div class="lux-kpi-icon">📄</div><div class="lux-kpi-label">Total Quotations</div>'
    f'<div class="lux-kpi-value">{total_count:,}</div><div class="lux-kpi-foot">{"Filtered results" if search_q else "All records"}</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#10b981,#14b8a6);--soft:#ecfdf5;">'
    f'<div class="lux-kpi-icon">💰</div><div class="lux-kpi-label">Total Value</div>'
    f'<div class="lux-kpi-value">₹ {total_value:,}</div><div class="lux-kpi-foot">Sum of grand totals</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#f59e0b,#f97316);--soft:#fffbeb;">'
    f'<div class="lux-kpi-icon">📊</div><div class="lux-kpi-label">Average Quotation</div>'
    f'<div class="lux-kpi-value">₹ {avg_value:,}</div><div class="lux-kpi-foot">Per quotation</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#ec4899,#a855f7);--soft:#fdf2f8;">'
    f'<div class="lux-kpi-icon">🗓️</div><div class="lux-kpi-label">This Month</div>'
    f'<div class="lux-kpi-value">{this_month:,}</div><div class="lux-kpi-foot">{cluster_count} active clusters</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

if st.session_state.quo_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE CARD VIEW (same as before)
    # ---------------------------------------------------------------
    if df_display.empty:
        st.info("No quotation records found.")
    else:
        for pos, (_, row) in enumerate(df_display.iterrows(), start=1):
            row_dict = row.to_dict()
            q_name = row_dict.get("Quotation Name", "")
            with st.container(border=True):
                st.markdown(
                    f'<div class="quo-card-title">#{pos} — {_esc(q_name)}</div>'
                    f'<div class="quo-card-sub">{_esc(row_dict.get("Date"))} • {_esc(row_dict.get("Project ID"))}</div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Site ID</span><span class="quo-card-value">{_esc(row_dict.get("Site ID"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Site Name</span><span class="quo-card-value">{_esc(row_dict.get("Site Name"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Cluster</span><span class="quo-card-value">{_esc(row_dict.get("Cluster"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Project</span><span class="quo-card-value">{_esc(row_dict.get("Project Name"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Grand Total</span><span class="quo-card-value amount">{_amt(row_dict.get("Quotation Amount"))}</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button("⚙️ Manage", key=f"card_quo_mgr_{q_name}_{pos}", use_container_width=True):
                    quotation_dialog(row_dict)

else:
    # ---------------------------------------------------------------
    # LAVISH DESKTOP TABLE VIEW — inline ✏️ Edit / 🗑️ Delete per row
    # ---------------------------------------------------------------
    PAGE_SIZE = 25

    # Search badalne par page 1 par wapas jao
    if st.session_state.get("quo_last_search") != search_q:
        st.session_state.quo_last_search = search_q
        st.session_state.quo_page = 1
    total_pages = max(1, -(-len(df_display) // PAGE_SIZE))
    page = min(max(1, st.session_state.get("quo_page", 1)), total_pages)
    start = (page - 1) * PAGE_SIZE
    df_page = df_display.iloc[start:start + PAGE_SIZE]

    # Column ratios: Manage | # | Date | Project ID | Site Code | Site Name | Cluster | Project | Grand Total
    COLS = [0.6, 0.6, 1.3, 1.7, 1.4, 2.3, 1.3, 1.5, 1.3]

    # ---- Table title bar ----
    st.markdown(
        '<div class="lux-table-head">'
        '<div class="lux-table-title">📑 Quotation Register<span>newest first</span></div>'
        f'<div class="lux-table-badge">₹ {total_value:,}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Column headers ----
    with st.container(key="lux_thead"):
        hc = st.columns(COLS, vertical_alignment="center")
        for col, label in zip(hc, ["⚙️", "#", "Date", "Project ID", "Site Code",
                                    "Site Name", "Cluster", "Project", "Grand Total"]):
            align = "right" if label == "Grand Total" else ("center" if label in ("⚙️", "#") else "left")
            col.markdown(f'<p style="text-align:{align};">{label}</p>', unsafe_allow_html=True)

    # ---- Rows ----
    body_kwargs = {"height": 560} if len(df_page) > 8 else {}
    with st.container(key="lux_tbody", border=False, **body_kwargs):
        if df_page.empty:
            st.markdown(
                '<div class="lux-empty"><div>🗂️</div>'
                f'{"No quotations match your search." if search_q else "No quotation records yet. Click ➕ Add Record to create one."}'
                "</div>",
                unsafe_allow_html=True,
            )
        for pos, (_, r) in enumerate(df_page.iterrows(), start=start + 1):
            row_dict = r.to_dict()
            rid = row_dict.get("id")
            rid = pos if rid is None or (isinstance(rid, float) and pd.isna(rid)) else rid
            q_name = row_dict.get("Quotation Name", "")

            d = pd.to_datetime(row_dict.get("Date"), errors="coerce")
            date_html = (
                f'<div class="lux-date">{d.strftime("%d %b %Y")}<small>{d.strftime("%A")}</small></div>'
                if pd.notna(d) else _esc(row_dict.get("Date"))
            )
            pid = str(row_dict.get("Project ID") or "").strip()
            sid = str(row_dict.get("Site ID") or "").strip()
            clu = str(row_dict.get("Cluster") or "").strip()
            pid_html = f'<span class="lux-chip proj">{html.escape(pid)}</span>' if pid and pid != "nan" else _esc("")
            sid_html = f'<span class="lux-chip">{html.escape(sid)}</span>' if sid and sid != "nan" else _esc("")
            clu_html = f'<span class="lux-pill">{html.escape(clu)}</span>' if clu and clu != "nan" else _esc("")

            parity = "odd" if pos % 2 else "even"
            with st.container(key=f"luxrow_{parity}_{rid}"):
                c = st.columns(COLS, vertical_alignment="center")
                with c[0]:
                    if st.button("⚙️", key=f"qmgr_{rid}", help="Manage (View / Edit / Delete)"):
                        quotation_dialog(row_dict)
                c[1].markdown(f'<p style="text-align:center;"><span class="lux-num">{pos}</span></p>', unsafe_allow_html=True)
                c[2].markdown(date_html, unsafe_allow_html=True)
                c[3].markdown(f"<p>{pid_html}</p>", unsafe_allow_html=True)
                c[4].markdown(f"<p>{sid_html}</p>", unsafe_allow_html=True)
                c[5].markdown(f'<p class="lux-site">{_esc(row_dict.get("Site Name"))}</p>', unsafe_allow_html=True)
                c[6].markdown(f"<p>{clu_html}</p>", unsafe_allow_html=True)
                c[7].markdown(f'<p class="lux-proj">{_esc(row_dict.get("Project Name"))}</p>', unsafe_allow_html=True)
                c[8].markdown(f'<p class="lux-amt" style="text-align:right;">{_amt(row_dict.get("Quotation Amount"))}</p>', unsafe_allow_html=True)

    # ---- Footer ----
    shown_to = min(start + PAGE_SIZE, len(df_display))
    st.markdown(
        '<div class="lux-tfoot">'
        f'<div>Grand Total of {total_count:,} quotation{"s" if total_count != 1 else ""}'
        f'<small>Showing {start + 1 if total_count else 0}–{shown_to} of {total_count}</small></div>'
        f'<div class="lux-tfoot-amt">₹ {total_value:,}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Pager ----
    if total_pages > 1:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        _, p_prev, p_info, p_next, _ = st.columns([4, 1.2, 1.6, 1.2, 4], vertical_alignment="center")
        with p_prev:
            if st.button("◀ Prev", key="quo_prev", use_container_width=True, disabled=page <= 1):
                st.session_state.quo_page = page - 1
                st.rerun()
        with p_info:
            st.markdown(f'<div class="lux-pager-info">Page {page} of {total_pages}</div>', unsafe_allow_html=True)
        with p_next:
            if st.button("Next ▶", key="quo_next", use_container_width=True, disabled=page >= total_pages):
                st.session_state.quo_page = page + 1
                st.rerun()
