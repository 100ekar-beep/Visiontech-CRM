import streamlit as st
import pandas as pd
import datetime
import io
import json
import html
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Quotation List", page_icon="📄", layout="wide")

# ================================================================
# --- 📌 STICKY HEADER + BOLD HEADER COLOR + 100 ROWS (all tables) ---
# ================================================================
def rows_per_page_picker(key, page_state_key=None, default=100):
    """Chhota 'Rows per page' dropdown (default 100). Badalne par page 1 par wapas."""
    if key not in st.session_state:
        st.session_state[key] = default
    def _reset_page():
        if page_state_key:
            st.session_state[page_state_key] = 1
    _rpp_space, _rpp_col = st.columns([6, 1.3])
    with _rpp_col:
        st.selectbox("Rows per page", [25, 50, 100, 200], key=key, on_change=_reset_page,
                     help="Ek page par kitni lines dikhni chahiye (default 100).")
    return int(st.session_state[key])


st.markdown("""
<style>
.stApp .st-key-lux_tbody { max-height: 78vh !important; overflow: auto !important; }
/* Header: alag gehra color + bold safed text + amber underline (header body ke upar fixed rehta hai) */
.stApp .st-key-lux_thead {
    background: linear-gradient(90deg, #312e81 0%, #4338ca 45%, #6d28d9 100%) !important;
    border-bottom: 3px solid #f59e0b !important;
    box-shadow: 0 8px 14px -8px rgba(30, 27, 75, .55) !important;
    padding: 14px !important; position: sticky !important; top: 0 !important; z-index: 20 !important;
}
.stApp .st-key-lux_thead p {
    color: #ffffff !important; font-size: .76rem !important; font-weight: 900 !important;
    letter-spacing: 1.2px !important; text-shadow: 0 1px 2px rgba(0,0,0,.25);
}
</style>
""", unsafe_allow_html=True)

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
        rows = []
        offset = 0
        page_size = 500
        while True:
            res = (supabase.table("site_data")
                   .select('id,"Operator","Project ID","Site ID","Site Name","Cluster","Project Name"')
                   .eq("workspace", workspace_name)
                   .ilike("Operator", "%uotat%")
                   .order("id")
                   .range(offset, offset + page_size - 1).execute())
            chunk = res.data or []
            if not chunk:
                break
            rows.extend(chunk)
            offset += len(chunk)
        if rows:
            return pd.DataFrame(rows)
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
                    df.attrs["master_table"] = t
                    df.attrs["master_columns"] = {normalized: original for original, normalized in col_map.items()}
                    return df
        except Exception:
            continue
    return pd.DataFrame(columns=["Item Code", "Description", "Price"])

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_templates_cached(active_ws):
    """Show saved templates across VISPL/Bhagyshree workspaces.
    Templates are reusable; quotation records remain workspace-specific.
    """
    try:
        all_rows = []
        offset = 0
        while True:
            response = (supabase.table("quotation_templates")
                        .select("*")
                        .range(offset, offset + 499).execute())
            batch = response.data or []
            all_rows.extend(batch)
            if len(batch) < 500:
                break
            offset += 500
        if all_rows:
            return pd.DataFrame(all_rows)
    except Exception as e:
        st.warning(f"Quotation templates could not be loaded: {e}")
    return pd.DataFrame(columns=["id", "Template Name", "Items Data", "workspace"])

def fetch_templates():
    return _fetch_templates_cached(st.session_state.get('active_workspace', 'VISPL'))
fetch_templates.clear = _fetch_templates_cached.clear


def fetch_quotation_templates():
    return fetch_templates().to_dict("records")

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
# Workspace label avoids collisions when different companies have same template name.
template_lookup = {}
for i, template in enumerate(templates_data):
    name = str(template.get("Template Name") or "").strip()
    if not name:
        continue
    ws = str(template.get("workspace") or "Shared").strip()
    label = f"{name} ({ws})"
    if label in template_lookup:
        label = f"{label} [#{template.get('id', i)}]"
    template_lookup[label] = template
template_names = list(template_lookup.keys())

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
    
    bulk_mode = is_new and st.checkbox("Multiple projects - same template", key="quo_bulk_mode")
    selected_projects = []
    if bulk_mode:
        selected_projects = st.multiselect(
            "SELECT PROJECT IDs *", options=available_opts, key="quo_bulk_projects",
            help="One separate quotation will be created for each selected project using the same items and quantities."
        )
        if selected_projects:
            st.caption(f"{len(selected_projects)} projects selected. Site details below preview the first project.")
            st.dataframe(
                df_projects[df_projects["Project ID"].isin(selected_projects)][
                    ["Project ID", "Site ID", "Site Name", "Cluster", "Project Name"]
                ], hide_index=True, use_container_width=True
            )

    # Top Section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        quo_name = st.text_input("QUOTATION *", value=default_name)
    with col2:
        quo_date = st.date_input("QUOTATION DATE *", value=default_date)
    with col3:
        sel_idx = dynamic_options.index(default_proj) if default_proj in dynamic_options else 0
        if bulk_mode:
            sel_proj = selected_projects[0] if selected_projects else ""
            st.text_input("FIRST PROJECT (PREVIEW)", value=str(sel_proj), disabled=True)
        else:
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
            if t is template_lookup.get(selected_template):
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
        save_label = f"Generate {len(selected_projects)} Quotations" if bulk_mode else "💾 Save Quotation"
        if st.button(save_label, type="primary", use_container_width=True):
            if bulk_mode:
                if not selected_projects:
                    st.error("Select at least one Project ID.")
                    return
                if selected_template == "-- Select Template --":
                    st.error("Select a quotation template.")
                    return
                if not quo_name.strip():
                    st.error("Quotation name is required.")
                    return
                import uuid
                active_ws = st.session_state.get('active_workspace', 'VISPL')
                bulk_items = []
                for _, r in edited_items_df.iterrows():
                    if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip():
                        qty = int(r["Qty"]) if pd.notna(r["Qty"]) else 0
                        price = int(r["Price"]) if pd.notna(r["Price"]) else 0
                        bulk_items.append({
                            "workspace": active_ws,
                            "Item Code": str(r["Item Code"]).split(" | ")[0].strip(),
                            "Description": str(r["Description"]),
                            "Qty": qty, "Price": price, "Total": qty * price
                        })
                if not bulk_items:
                    st.error("Template must contain at least one material item.")
                    return
                bulk_results = []
                progress = st.progress(0)
                for position, project_id in enumerate(selected_projects):
                    bulk_name = ""
                    try:
                        existing = (supabase.table("quotations").select('id')
                                    .eq("workspace", active_ws).eq("Project ID", project_id)
                                    .limit(1).execute())
                        if existing.data:
                            bulk_results.append({"Project ID": project_id, "Quotation": "", "Result": "Skipped - quotation already exists"})
                            continue
                        project_rows = df_projects[df_projects["Project ID"] == project_id]
                        if project_rows.empty:
                            raise ValueError("Project details not found")
                        project_row = project_rows.iloc[0]
                        bulk_name = f"{quo_name.strip()} - {project_id} - {uuid.uuid4().hex}"
                        bulk_header = {
                            "workspace": active_ws,
                            "Quotation Name": bulk_name, "Date": str(quo_date),
                            "Project ID": project_id,
                            "Site ID": str(project_row.get("Site ID", "")),
                            "Site Name": str(project_row.get("Site Name", "")),
                            "Project Name": str(project_row.get("Project Name", "")),
                            "Quotation Amount": sum(item["Total"] for item in bulk_items),
                            "Status": "Manual"
                        }
                        supabase.table("quotations").insert(bulk_header).execute()
                        try:
                            supabase.table("quotation_items").insert([
                                dict(item, **{"Quotation Name": bulk_name}) for item in bulk_items
                            ]).execute()
                        except Exception:
                            supabase.table("quotation_items").delete().eq("workspace", active_ws).eq("Quotation Name", bulk_name).execute()
                            supabase.table("quotations").delete().eq("workspace", active_ws).eq("Quotation Name", bulk_name).execute()
                            raise
                        bulk_results.append({"Project ID": project_id, "Quotation": bulk_name, "Result": "Saved"})
                    except Exception as e:
                        bulk_results.append({"Project ID": project_id, "Quotation": bulk_name, "Result": f"Failed - {e}"})
                    finally:
                        progress.progress((position + 1) / len(selected_projects))
                fetch_quotations_cached.clear()
                st.session_state.quotations_df = fetch_quotations()
                st.session_state["quo_bulk_results"] = bulk_results
                st.rerun()
                return
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


def render_quotation_templates():
    st.markdown('<style>\n/* FIX: table box khud scroll karta hai (78% screen height) — header isi box ke top par chipka rahe */\n.stApp div[class*="_table_wrap"] { max-height: 78vh !important; overflow: auto !important; }\n.stApp div[class*="_table_wrap"] > div[class*="st-key-tplhead"],\n.stApp div[class*="_table_wrap"] > div:has(div[class*="st-key-tplhead"]) {\nposition: sticky !important; top: 0 !important; z-index: 20 !important;\n}\n/* Header: alag gehra color + bold safed text + amber underline */\n.stApp div[class*="st-key-tplhead"] {\nbackground: linear-gradient(90deg, #312e81 0%, #4338ca 45%, #6d28d9 100%) !important;\nborder-bottom: 3px solid #f59e0b !important;\nbox-shadow: 0 8px 14px -8px rgba(30, 27, 75, .55) !important;\npadding: 14px 0 !important;\n}\n.stApp div[class*="st-key-tplhead"] [data-testid="stColumn"], .stApp div[class*="st-key-tplhead"] [data-testid="column"] { border-right: 1px solid rgba(255,255,255,.18) !important; }\n.stApp div[class*="st-key-tplhead"] .slux-th, .stApp div[class*="st-key-tplhead"] p {\ncolor: #ffffff !important; font-size: .76rem !important; font-weight: 900 !important;\nletter-spacing: 1.2px !important; text-shadow: 0 1px 2px rgba(0,0,0,.25);\n}\n\n</style>\n\n\n<style>\n.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: \'Inter\', sans-serif; }\nbutton[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"], button[kind="primary"] {\nbackground: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;\ncolor: white !important; border: none !important; border-radius: 8px !important;\nfont-weight: 800 !important; padding: 0.6rem 1.2rem !important;\nbox-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important; transition: all .2s ease !important;\n}\nbutton[kind="primary"] p { color: #ffffff !important; font-weight: 800 !important; }\nbutton[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"], button[kind="secondary"] {\nbackground: #ffffff !important; color: #334155 !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important;\nfont-weight: 800 !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important; transition: all .2s ease !important;\n}\nbutton[kind="secondary"] p { color: #334155 !important; font-weight: 800 !important; }\nbutton[kind="primary"]:hover, button[kind="secondary"]:hover { transform: translateY(-2px) !important; }\n\ndiv[data-testid="stDialog"] > div { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }\n.modal-section-title { color: #4338ca; font-size: 1rem; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #e0e7ff; padding-bottom: 8px; }\nlabel p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }\n[data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }\n\n/* PREMIUM SIDEBAR */\n[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); border-right: 1px solid rgba(255, 255, 255, 0.05); }\n[data-testid="stSidebarNav"] a {\npadding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;\nbackground: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;\ndisplay: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;\n}\n[data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }\n[data-testid="stSidebarNav"] a[aria-current="page"] {\nbackground: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;\n}\n[data-testid="stSidebarNav"] a span { color: inherit !important; }\n\n/* ================= KPI CARDS ================= */\n.lux-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 4px 0 22px; }\n.lux-kpi {\nposition: relative; background: #ffffff; border-radius: 16px; padding: 18px 20px 16px;\nborder: 1px solid #e0e7ff; overflow: hidden;\nbox-shadow: 0 12px 28px -14px rgba(79, 70, 229, 0.35);\ntransition: transform .25s ease, box-shadow .25s ease;\n}\n.lux-kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 34px -14px rgba(79, 70, 229, 0.45); }\n.lux-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--accent); }\n.lux-kpi-icon {\nposition: absolute; right: 16px; top: 16px; width: 42px; height: 42px; border-radius: 12px;\ndisplay: flex; align-items: center; justify-content: center; font-size: 1.3rem; background: var(--soft);\n}\n.lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; padding-right: 48px; }\n.lux-kpi-value { font-size: 1.55rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n.lux-kpi-value.small { font-size: 1.1rem; }\n.lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }\n\n/* ================= TABLE ================= */\n.slux-head-bar {\ndisplay: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;\npadding: 16px 22px; border-radius: 18px 18px 0 0;\nbackground: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);\n}\n.slux-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }\n.slux-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }\n.slux-badge {\nbackground: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;\npadding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;\n}\n.st-key-tpl_table_wrap {\nbackground: #ffffff !important; overflow: auto !important; padding: 0 !important;\nborder: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important; border-radius: 0 !important;\n}\n.st-key-tpl_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }\n.st-key-tpl_table_wrap [data-testid="stHorizontalBlock"],\n.st-key-tpl_table_wrap div[class*="st-key-tplhead"],\n.st-key-tpl_table_wrap div[class*="st-key-tplrow_"] { min-width: 900px !important; }\n.st-key-tpl_table_wrap [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important; }\n.st-key-tpl_table_wrap [data-testid="stColumn"], .st-key-tpl_table_wrap [data-testid="column"] {\npadding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;\n}\ndiv[class*="st-key-tplhead"] {\nposition: sticky !important; top: 0 !important; z-index: 5 !important;\nbackground: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;\n}\ndiv[class*="st-key-tplhead"] [data-testid="stColumn"], div[class*="st-key-tplhead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }\n.slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }\n.slux-th.c { text-align: center; }\n.slux-th.r { text-align: right; }\ndiv[class*="st-key-tplrow_"] {\npadding: 10px 0 !important; background: #ffffff;\nborder-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;\n}\ndiv[class*="st-key-tplrow_odd"] { background: #fafaff; }\ndiv[class*="st-key-tplrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }\ndiv[class*="st-key-tplrow_"] p { margin: 0 !important; }\n\n.slux-cell { font-size: .88rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }\n.slux-num {\ndisplay: inline-flex; width: 30px; height: 30px; border-radius: 50%;\nalign-items: center; justify-content: center;\nbackground: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;\nfont-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);\n}\n.tpl-name { font-weight: 800; color: #312e81; font-size: .95rem; }\n.tpl-preview { color: #64748b; font-size: .78rem; font-weight: 600; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n.tpl-count {\ndisplay: inline-block; min-width: 34px; text-align: center; padding: 4px 10px; border-radius: 8px;\nbackground: #eef2ff; border: 1px solid #c7d2fe; color: #4338ca; font-weight: 900; font-size: .82rem;\n}\n.tpl-qty {\ndisplay: inline-block; min-width: 34px; text-align: center; padding: 4px 10px; border-radius: 8px;\nbackground: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; font-weight: 900; font-size: .82rem;\n}\n.tpl-amt { text-align: right; font-weight: 900; color: #4f46e5; font-size: .95rem; font-variant-numeric: tabular-nums; }\n\n/* Single ⚙️ popover button at row start */\ndiv[class*="st-key-tplpop_"] button {\nwidth: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;\npadding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;\nbackground: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;\nbox-shadow: none !important; transition: all .2s ease !important;\n}\ndiv[class*="st-key-tplpop_"] button:hover {\nbackground: #3b82f6 !important; border-color: #60a5fa !important;\ntransform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;\n}\ndiv[class*="st-key-tplpop_"] button p, div[class*="st-key-tplpop_"] button span { color: #1e293b !important; }\ndiv[class*="st-key-tplpop_"] button svg { display: none !important; }\n.st-key-tpl_del_yes button { background: linear-gradient(90deg, #ef4444, #dc2626) !important; border: none !important; }\n.st-key-tpl_del_yes button p { color: #ffffff !important; }\n\n.slux-foot {\ndisplay: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;\npadding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);\nborder: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;\nbox-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);\nfont-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;\n}\n.slux-foot span { text-transform: none; letter-spacing: 0; font-size: .95rem; }\n.slux-empty {\nbackground: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;\ntext-align: center; color: #64748b; font-weight: 600;\n}\n.slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }\n</style>', unsafe_allow_html=True)
    df_items = fetch_item_master()
    if not df_items.empty:
        df_items["Description"] = df_items["Description"].fillna("")
        # --- Description first, Code inside brackets for dropdown search view ---
        df_items["Display"] = df_items["Description"].astype(str) + "  [" + df_items["Item Code"].astype(str) + "]"
    
        item_display_list = df_items["Display"].tolist()
        item_code_list = df_items["Item Code"].astype(str).tolist()
        combined_item_options = item_display_list + item_code_list 
    
        display_to_code = dict(zip(df_items["Display"], df_items["Item Code"]))
        display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))
        display_to_price = dict(zip(df_items["Display"], df_items["Price"]))
        code_to_display = dict(zip(df_items["Item Code"], df_items["Display"]))
    else:
        combined_item_options = []
        display_to_code = {}
        display_to_desc = {}
        display_to_price = {}
        code_to_display = {}

    @st.dialog("📋 Quotation Template Builder", width="large")
    def template_dialog(template_data=None):
        st.caption("Configure items for this quotation template")
        is_new = template_data is None
    
        def_name = "" if is_new else template_data.get("Template Name", "")
        t_name = st.text_input("QUOTATION TEMPLATE NAME *", value=def_name)
    
        st.markdown("<br>", unsafe_allow_html=True)
        col_t1, col_t2 = st.columns([8, 2])
        with col_t1:
            st.markdown('<div class="modal-section-title" style="margin-top:0;">📚 Template Items</div>', unsafe_allow_html=True)

        t_key = f"t_items_{def_name if not is_new else 'new'}"
        widget_t_key = f"widget_{t_key}"

        if t_key not in st.session_state:
            if is_new:
                st.session_state[t_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price"])
            else:
                try:
                    raw_data = template_data.get("Items Data", "[]")
                    items_list = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    temp_df = pd.DataFrame(items_list)
                
                    # Qty Handle karna agar purane template mein na ho
                    if "Qty" not in temp_df.columns:
                        temp_df.insert(2, "Qty", 1)
                    
                    # Map code back to Display format for dropdown
                    if "Item Code" in temp_df.columns:
                        temp_df["Item Code"] = temp_df["Item Code"].map(code_to_display).fillna(temp_df["Item Code"])
                    st.session_state[t_key] = temp_df
                except:
                    st.session_state[t_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price"])

        # --- FAILSAFE: Agar purana Session State without 'Qty' ho, toh zabardasti column dalo ---
        if "Qty" not in st.session_state[t_key].columns:
            st.session_state[t_key].insert(2, "Qty", 1)

        # --- Stable State Editor Engine (Prevents Popup Close Bug) ---
        if widget_t_key in st.session_state:
            w_state = st.session_state[widget_t_key]
            edits = w_state.get("edited_rows", {})
            adds = w_state.get("added_rows", [])
            dels = w_state.get("deleted_rows", [])
        
            if edits or adds or dels:
                curr_df = st.session_state[t_key].copy()
                if dels: curr_df = curr_df.drop(dels).reset_index(drop=True)
                if edits:
                    for str_idx, changes in edits.items():
                        idx = int(str_idx)
                        if idx < len(curr_df):
                            for col, val in changes.items():
                                curr_df.at[idx, col] = val
                            if "Item Code" in changes:
                                disp = str(changes["Item Code"])
                                if " | " in disp or "[" in disp:
                                    # Extract pure code
                                    code_only = display_to_code.get(disp, disp.split("[")[-1].replace("]", "").strip() if "[" in disp else disp)
                                    curr_df.at[idx, "Item Code"] = code_only
                                    if disp in display_to_desc:
                                        curr_df.at[idx, "Description"] = display_to_desc[disp]
                                        curr_df.at[idx, "Price"] = display_to_price[disp]
                                else:
                                    match = df_items[df_items["Item Code"] == disp]
                                    if not match.empty:
                                        curr_df.at[idx, "Description"] = match.iloc[0]["Description"]
                                        curr_df.at[idx, "Price"] = match.iloc[0]["Price"]
                if adds:
                    for row in adds:
                        new_row = {"Item Code": row.get("Item Code"), "Description": "", "Qty": 1, "Price": 0}
                        if "Item Code" in row and pd.notna(row["Item Code"]):
                            disp = str(row["Item Code"])
                            if "[" in disp or " | " in disp:
                                code_only = display_to_code.get(disp, disp.split("[")[-1].replace("]", "").strip() if "[" in disp else disp)
                                new_row["Item Code"] = code_only
                                if disp in display_to_desc:
                                    new_row["Description"] = display_to_desc[disp]
                                    new_row["Price"] = display_to_price[disp]
                        curr_df = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state[t_key] = curr_df
                del st.session_state[widget_t_key]

        edited_t_df = st.data_editor(
            st.session_state[t_key],
            key=widget_t_key,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            height=300,
            column_config={
                "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=combined_item_options, required=True, width="medium"),
                "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
                "Qty": st.column_config.NumberColumn("QTY", min_value=1, default=1, alignment="center", width="small"),
                "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d", alignment="center", width="small")
            }
        )

        # --- CALCULATE AND DISPLAY GRAND TOTAL FOR TEMPLATE ---
        try:
            qty_series = pd.to_numeric(edited_t_df["Qty"], errors='coerce').fillna(0)
            price_series = pd.to_numeric(edited_t_df["Price"], errors='coerce').fillna(0)
            grand_total = (qty_series * price_series).sum()
        except Exception:
            grand_total = 0

        st.markdown(f"""
            <div style="display:flex; justify-content:flex-end; margin: 10px 0 20px 0;">
                <div style="background:linear-gradient(90deg,#f5f3ff,#eef2ff); border:1px solid #c7d2fe; border-radius:14px; padding:12px 22px; text-align:right;">
                    <div style="color:#64748b; font-weight:800; font-size:.72rem; letter-spacing:1px; text-transform:uppercase;">Grand Total</div>
                    <div style="color:#4f46e5; font-weight:900; font-size:1.6rem;">₹ {grand_total:,.0f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Save Template", type="primary", use_container_width=True):
            if not t_name.strip():
                st.error("⚠️ Template Name is required!")
                return
        
            clean_items = []
            for _, r in edited_t_df.iterrows():
                if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip() != "":
                    disp_val = str(r["Item Code"])
                    c_code = display_to_code.get(disp_val, disp_val.split("[")[-1].replace("]", "").strip() if "[" in disp_val else disp_val)
                    clean_items.append({
                        "Item Code": c_code,
                        "Description": str(r["Description"]),
                        "Qty": int(r["Qty"]) if "Qty" in r and pd.notna(r["Qty"]) else 1,
                        "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0
                    })
        
            payload = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "Template Name": t_name.strip(),
                "Items Data": json.dumps(clean_items)
            }
        
            try:
                if not is_new and "id" in template_data and pd.notna(template_data["id"]):
                    supabase.table("quotation_templates").update(payload).eq("id", template_data["id"]).execute()
                else:
                    supabase.table("quotation_templates").insert(payload).execute()
            
                fetch_templates.clear()
                st.success("✅ Template Saved Successfully!")
                st.rerun()
            except Exception as e:
                # FIX: Fallback if workspace column is completely missing in database schema
                error_str = str(e)
                if 'PGRST204' in error_str or 'workspace' in error_str:
                    payload_fallback = {k: v for k, v in payload.items() if k != "workspace"}
                    try:
                        if not is_new and "id" in template_data and pd.notna(template_data["id"]):
                            supabase.table("quotation_templates").update(payload_fallback).eq("id", template_data["id"]).execute()
                        else:
                            supabase.table("quotation_templates").insert(payload_fallback).execute()
                    
                        fetch_templates.clear()
                        st.success("✅ Template Saved! (⚠️ DB me 'workspace' column nahi hai isliye use skip kiya gaya)")
                        st.rerun()
                    except Exception as fallback_e:
                        st.error(f"Error saving template: {fallback_e}")
                else:
                    st.error(f"Error saving template: {e}")


    @st.dialog("🗑️ Delete Template")
    def delete_template_dialog(row_dict, items_count, value):
        st.markdown(
            f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
    <div style="font-weight:900;color:#991b1b;font-size:1rem;">{html.escape(str(row_dict.get('Template Name','') or '-'))}</div>
    <div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">{items_count} item(s) • ₹ {value:,.0f}</div>
    </div>
    <p style="color:#475569;">Ye template permanently delete ho jayega. Kya aap sure hain?</p>""",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancel", key="tpl_del_no", use_container_width=True):
                st.rerun()
        with c2:
            if st.button("Yes, Delete", key="tpl_del_yes", use_container_width=True):
                try:
                    supabase.table("quotation_templates").delete().eq("id", row_dict["id"]).execute()
                    fetch_templates.clear()
                    st.success("✅ Template Deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


    def _parse_items(raw):
        try:
            items = json.loads(raw) if isinstance(raw, str) else (raw or [])
            return items if isinstance(items, list) else []
        except Exception:
            return []

    def _num(v, default=0.0):
        n = pd.to_numeric(v, errors="coerce")
        return default if pd.isna(n) else float(n)


    # --- TOP HEADER ---
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1:
        st.markdown("<h1 style='margin:0; color:#0f172a;'>📋 Quotation Templates</h1>", unsafe_allow_html=True)
    with col_h2:
        if st.button("➕ Add Template", type="primary", use_container_width=True):
            # Clear all state parameters related to template form
            for key in list(st.session_state.keys()):
                if key.startswith("t_items_") or key.startswith("widget_t_items_"):
                    del st.session_state[key]
            template_dialog()

    st.markdown("<br>", unsafe_allow_html=True)

    df_templates = fetch_templates().copy().reset_index(drop=True)

    # --- Per-template summary (items, qty, value) ---
    summaries = []
    for _, r in df_templates.iterrows():
        items = _parse_items(r.get("Items Data", "[]"))
        qty_total = sum(_num(it.get("Qty", 1), 1) for it in items)
        value = sum(_num(it.get("Qty", 1), 1) * _num(it.get("Price", 0)) for it in items)
        preview = ", ".join(str(it.get("Description") or it.get("Item Code") or "").strip() for it in items[:3] if (it.get("Description") or it.get("Item Code")))
        if len(items) > 3:
            preview += f" +{len(items) - 3} more"
        summaries.append({"items": len(items), "qty": qty_total, "value": value, "preview": preview})

    if not df_templates.empty:
        # --- KPI CARDS ---
        k_count = len(df_templates)
        k_items = sum(s["items"] for s in summaries)
        k_avg = (sum(s["value"] for s in summaries) / k_count) if k_count else 0.0
        top_idx = max(range(k_count), key=lambda i: summaries[i]["value"]) if k_count else None
        top_name = str(df_templates.iloc[top_idx].get("Template Name", "-")) if top_idx is not None else "-"
        top_value = summaries[top_idx]["value"] if top_idx is not None else 0.0

        def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
            return (
                f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
                f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
                f'<div class="lux-kpi-value {value_cls}" title="{html.escape(str(value))}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
            )

        st.markdown(
            '<div class="lux-kpi-grid">'
            + _kpi("📋", "Templates", f"{k_count:,}", "In this workspace", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
            + _kpi("📦", "Total Line Items", f"{k_items:,}", "Across all templates", "linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")
            + _kpi("💰", "Avg Template Value", f"₹ {k_avg:,.0f}", "Qty × Price", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5")
            + _kpi("🏆", "Highest Value", html.escape(top_name), f"₹ {top_value:,.0f}", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb", "small")
            + '</div>',
            unsafe_allow_html=True,
        )

        # --- ✨ LAVISH TABLE — single ⚙️ button at row start ---
        COL_RATIOS = [0.55, 0.5, 4.2, 1.0, 1.0, 1.5]
        COL_LABELS = ["⚙️", "#", "TEMPLATE NAME", "ITEMS", "TOTAL QTY", "TEMPLATE VALUE"]

        st.markdown(
            '<div class="slux-head-bar">'
            '<div class="slux-title">📋 Template Library<span>click ⚙️ to edit or delete</span></div>'
            f'<div class="slux-badge">{k_count} template{"s" if k_count != 1 else ""}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        table_kwargs = {"height": 520} if k_count > 8 else {}
        with st.container(key="tpl_table_wrap"):
            with st.container(key="tplhead"):
                h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
                for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                    cls = " c" if i in (0, 1, 3, 4) else (" r" if i == 5 else "")
                    h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

            for pos, (_, r) in enumerate(df_templates.iterrows()):
                row_dict = r.to_dict()
                rid = row_dict.get("id")
                rk = rid if rid is not None and str(rid).strip() not in ("", "nan", "None") else f"s{pos}"
                s = summaries[pos]
                parity = "odd" if (pos + 1) % 2 else "even"
                name = str(row_dict.get("Template Name", "") or "-")

                with st.container(key=f"tplrow_{parity}_{rk}"):
                    rcols = st.columns(COL_RATIOS, vertical_alignment="center")
                    with rcols[0]:
                        with st.container(key=f"tplpop_{rk}"):
                            with st.popover("⚙️"):
                                if st.button("✏️ Edit Template", key=f"tpl_edit_{rk}", use_container_width=True):
                                    for state_key in list(st.session_state.keys()):
                                        if state_key.startswith("t_items_") or state_key.startswith("widget_t_items_"):
                                            del st.session_state[state_key]
                                    template_dialog(row_dict)
                                if st.button("🗑️ Delete Template", key=f"tpl_del_{rk}", use_container_width=True):
                                    delete_template_dialog(row_dict, s["items"], s["value"])
                    rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos + 1}</span></div>", unsafe_allow_html=True)
                    rcols[2].markdown(
                        f"<div class='slux-cell'><div class='tpl-name' title='{html.escape(name)}'>📋 {html.escape(name)}</div>"
                        f"<div class='tpl-preview' title='{html.escape(s['preview'])}'>{html.escape(s['preview']) or '—'}</div></div>",
                        unsafe_allow_html=True,
                    )
                    rcols[3].markdown(f"<div style='text-align:center;'><span class='tpl-count'>{s['items']}</span></div>", unsafe_allow_html=True)
                    qty_txt = str(int(s["qty"])) if float(s["qty"]).is_integer() else f"{s['qty']:g}"
                    rcols[4].markdown(f"<div style='text-align:center;'><span class='tpl-qty'>{qty_txt}</span></div>", unsafe_allow_html=True)
                    rcols[5].markdown(f"<div class='slux-cell tpl-amt'>₹ {s['value']:,.0f}</div>", unsafe_allow_html=True)

        st.markdown(
            f'<div class="slux-foot"><div>{k_count:,} template{"s" if k_count != 1 else ""}</div>'
            f'<div><span>Total Items: <b style="color:#4338ca;">{k_items:,}</b></span></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="slux-empty"><div>📋</div>No Templates found. Click ➕ Add Template to create one.</div>',
            unsafe_allow_html=True,
        )


def save_new_master_item(item_code, description, price, master_data):
    item_code = item_code.strip()
    description = description.strip()
    if not item_code or not description:
        raise ValueError("Item Code and Description are required.")
    if price < 0:
        raise ValueError("Price cannot be negative.")
    table_name = master_data.attrs.get("master_table")
    columns = master_data.attrs.get("master_columns", {})
    if not table_name or not all(field in columns for field in ("Item Code", "Description", "Price")):
        raise ValueError("Item Master table/columns could not be detected. Check Item Master access first.")
    existing = (supabase.table(table_name).select(columns["Item Code"])
                .eq(columns["Item Code"], item_code).limit(1).execute())
    if existing.data:
        raise ValueError("This Item Code already exists. Use the existing item from the dropdown.")
    payload = {columns["Item Code"]: item_code, columns["Description"]: description,
               columns["Price"]: int(price)}
    supabase.table(table_name).insert(payload).execute()
    fetch_item_master.clear()


@st.dialog("➕ Add New Item to Item Master", width="large")
def add_master_item_dialog():
    st.caption("Save a new material item for use in quotation templates and quotations.")
    with st.form("quotation_new_master_item_form", clear_on_submit=False):
        new_item_code = st.text_input("ITEM CODE *")
        new_item_description = st.text_area("DESCRIPTION *")
        new_item_price = st.number_input("PRICE *", min_value=0, value=0, step=1)
        submitted = st.form_submit_button("💾 Save New Item", type="primary", use_container_width=True)
    if submitted:
        try:
            save_new_master_item(new_item_code, new_item_description, new_item_price, df_items)
        except Exception as e:
            st.error(f"Item could not be saved: {e}")
            return
        st.session_state["quotation_item_saved"] = new_item_code.strip()
        st.rerun()

# --- Integrated page navigation ---
if st.session_state.get("quotation_item_saved"):
    st.success(f"Item {st.session_state.pop('quotation_item_saved')} saved. Available in template and quotation dropdowns.")
if st.button("➕ Add New Item", key="quotation_add_master_item"):
    add_master_item_dialog()

quotation_section = st.radio(
    "Quotation Setup", ["📄 Quotation List", "📋 Quotation Templates"],
    horizontal=True, key="quotation_setup_section", label_visibility="collapsed"
)
if quotation_section == "📋 Quotation Templates":
    render_quotation_templates()
    st.stop()

# --- 7. TOP HEADER & FILTERS ---
if st.session_state.get("quo_bulk_results"):
    bulk_result_df = pd.DataFrame(st.session_state["quo_bulk_results"])
    saved_count = int((bulk_result_df["Result"] == "Saved").sum())
    failed_count = int(bulk_result_df["Result"].str.startswith("Failed").sum())
    bulk_summary = f"Bulk generation complete: {saved_count} quotations saved out of {len(bulk_result_df)} selected projects."
    if failed_count:
        st.error(f"{bulk_summary} {failed_count} failed. See results below.")
    elif saved_count:
        st.success(bulk_summary)
    else:
        st.warning(bulk_summary)
    with st.expander("Bulk quotation results", expanded=True):
        st.dataframe(bulk_result_df, hide_index=True, use_container_width=True)
        st.download_button("Download Results CSV", bulk_result_df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="bulk_quotation_results.csv", mime="text/csv")
        if st.button("Clear Bulk Results"):
            del st.session_state["quo_bulk_results"]
            st.rerun()

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
    PAGE_SIZE = rows_per_page_picker("quo_rows_per_page", "quo_page")

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
    body_kwargs = {}  # height ab CSS (78vh) se aati hai
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
