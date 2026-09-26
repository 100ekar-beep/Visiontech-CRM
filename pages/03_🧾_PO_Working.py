import streamlit as st
import pandas as pd
import math
import io
import html
import requests
import urllib.parse
from supabase import create_client, Client

# Attempt to load st_keyup for real-time auto-search
try:
    from st_keyup import st_keyup
    HAS_KEYUP = True
except ImportError:
    HAS_KEYUP = False

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="PO Working", page_icon="🧾", layout="wide")

# --- MOBILE VIEW TOGGLE STATE ---
if 'po_view_mode' not in st.session_state:
    st.session_state.po_view_mode = "table"

# --- MULTI-COMPANY TAB SETUP (single login — switch company inside this page) ---
PO_COMPANIES = [
    ("VISPL", "VISPL"),
    ("Bhagyashree", "Bhagyashree"),
    ("Sai Tele", "Sai Tele"),
]
PO_COMPANY_WORKSPACE_MAP = {
    "VISPL": "VISPL",
    "Bhagyashree": "BHAGYASHREE",
    "Sai Tele": "SAI TELE SERVICES",
}
if 'po_active_company' not in st.session_state:
    st.session_state.po_active_company = "VISPL"
# Derive the actual workspace used by every query in this file from the active tab,
# so switching tabs is the only thing needed — no separate per-company login required.
st.session_state['active_workspace'] = PO_COMPANY_WORKSPACE_MAP.get(st.session_state.po_active_company, "VISPL")

# --- 2. ✨ LAVISH LIGHT THEME CSS (Quotation / Site Data / Invoice jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Primary Action Buttons */
    div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"],
    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15) !important;
    }
    div.stButton > button[kind="primary"] p, div.stDownloadButton > button[kind="primary"] p { color: #ffffff !important; font-weight: 800 !important; }

    /* Secondary Action Buttons (Refresh / Export / Cancel etc.) */
    div.stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"] {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    div.stButton > button[kind="secondary"] p { color: #334155 !important; font-weight: 800 !important; }
    div.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.18) !important; }

    .page-count { text-align: center; font-size: 1rem; font-weight: 800; color: #4338ca; margin-top: 10px; }

    /* Dialogs — light glass */
    div[data-testid="stDialog"] > div {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #0f172a !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
    div[data-testid="stDialog"] p { color: #1e293b !important; }
    div[data-testid="stDialog"] button[kind="icon"] svg { fill: #0f172a !important; }

    .modal-section-title {
        color: #4338ca; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px;
        margin-top: 15px; margin-bottom: 10px;
        border-bottom: 2px solid #e0e7ff; padding-bottom: 6px;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #0f172a !important; font-weight: 700 !important; letter-spacing: 0.5px;
    }

    /* Sidebar (kept dark, same as other pages) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important;
        font-weight: 600 !important; font-size: 1.05rem !important; transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; display: flex !important;
        align-items: center !important; gap: 12px !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important; transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important; color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important; border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* KPI PILLS FOR POPUP HEADER (light) */
    .kpi-pill-container { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
    .kpi-pill {
        background: #f8fafc; border: 1px solid #e2e8f0;
        padding: 8px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 700; color: #64748b;
        display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(15,23,42,0.05);
    }
    .kpi-pill span { color: #4338ca; font-weight: 900; letter-spacing: 0.5px; }

    /* ================= KPI CARDS ================= */
    .lux-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 4px 0 22px; }
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
    .lux-kpi-value { font-size: 1.55rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
    .lux-kpi-value.green { color: #059669; }
    .lux-kpi-value.red { color: #d97706; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

    /* ================= TABLE TITLE BAR ================= */
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

    /* ================= SCROLLING TABLE BODY ================= */
    .st-key-po_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-po_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-po_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-po_table_wrap div[class*="st-key-pohead"],
    .st-key-po_table_wrap div[class*="st-key-porow_"] { min-width: 1260px !important; }
    .st-key-po_table_wrap [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-po_table_wrap [data-testid="stColumn"], .st-key-po_table_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header */
    div[class*="st-key-pohead"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-pohead"] [data-testid="stColumn"], div[class*="st-key-pohead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-porow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-porow_odd"] { background: #fafaff; }
    div[class*="st-key-porow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-porow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .86rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
    .slux-strong { font-weight: 700; color: #0f172a; }
    .slux-soft { color: #475569; font-weight: 600; }
    .slux-muted { color: #cbd5e1; }
    .slux-num {
        display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
        align-items: center; justify-content: center;
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
        font-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
    }
    .slux-chip {
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
        padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
    }
    .slux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
    .slux-chip.po { background: #fdf4ff; border-color: #f5d0fe; color: #a21caf; }
    .po-amt { text-align: right; font-weight: 900; color: #4f46e5; font-variant-numeric: tabular-nums; }
    .po-lines { display: inline-block; min-width: 30px; text-align: center; padding: 3px 10px; border-radius: 8px;
                background: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; font-weight: 900; font-size: .82rem; }

    /* STATUS BADGES FOR SITE AVAILABILITY */
    .status-badge-green, .status-badge-orange {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 11px; border-radius: 999px; border: 1px solid transparent;
        font-size: .7rem; font-weight: 800; letter-spacing: .4px; white-space: nowrap;
    }
    .status-badge-green { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
    .status-badge-orange { background: #ffedd5; color: #c2410c; border-color: #fed7aa; }

    /* Single ⚙️ action button at row start (Site Data jaisa) */
    div[class*="st-key-popop_"] button {
        width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    div[class*="st-key-popop_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    div[class*="st-key-popop_"] button p, div[class*="st-key-popop_"] button span { color: #1e293b !important; }
    div[class*="st-key-popop_"] button svg { display: none !important; }
    .st-key-po_del_yes button { background: linear-gradient(90deg, #ef4444, #dc2626) !important; border: none !important; }
    .st-key-po_del_yes button p { color: #ffffff !important; }

    /* Footer bar */
    .slux-foot {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
        font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .slux-foot small { color: #6366f1; font-weight: 700; letter-spacing: .5px; margin-left: 10px; text-transform: none; font-size: .8rem; }
    .slux-foot-amts { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; text-transform: none; letter-spacing: 0; }
    .slux-foot-amts span { font-size: .95rem; }
    .slux-foot-badge {
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 5px 14px;
        border-radius: 999px; font-size: .75rem; letter-spacing: .5px;
    }
    .slux-empty {
        background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
        text-align: center; color: #64748b; font-weight: 600;
    }
    .slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }

    /* ================= MOBILE CARD VIEW (light) ================= */
    .po-card-title { font-size: 1.05rem; font-weight: 800; color: #312e81; margin-bottom: 2px; }
    .po-card-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
    .po-card-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; gap: 10px; }
    .po-card-row:last-child { border-bottom: none; }
    .po-card-label { color: #64748b; font-weight: 700; white-space: nowrap; text-transform: uppercase; font-size: .75rem; }
    .po-card-value { color: #0f172a; font-weight: 600; text-align: right; }

    /* ================= MULTI-COMPANY NAV BAR (VISPL / Bhagyashree / Sai Tele) ================= */
    .st-key-po_company_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-po_company_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-po_company_nav_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-po_company_nav_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important; color: #0f172a !important;
        border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
    }
    .st-key-po_company_nav_bar button[kind="secondary"] p,
    .st-key-po_company_nav_bar button[kind="secondary"] span,
    .st-key-po_company_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-po_company_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    .st-key-po_company_nav_bar button[kind="primary"] p,
    .st-key-po_company_nav_bar button[kind="primary"] span,
    .st-key-po_company_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; }
    </style>
""", unsafe_allow_html=True)

# --- MULTI-COMPANY NAV BAR (single login, switch company right here) ---
with st.container(key="po_company_nav_bar"):
    nav_cols = st.columns(len(PO_COMPANIES))
    for nav_col, (company_id, company_label) in zip(nav_cols, PO_COMPANIES):
        is_active = st.session_state.po_active_company == company_id
        with nav_col:
            if st.button(
                company_label, key=f"po_nav_{company_id}",
                use_container_width=True, type=("primary" if is_active else "secondary")
            ):
                st.session_state.po_active_company = company_id
                st.session_state.active_workspace = PO_COMPANY_WORKSPACE_MAP[company_id]
                # Force a fresh fetch for the newly selected company instead of
                # reusing whatever was already loaded for the previous one.
                if 'po_working_df' in st.session_state:
                    del st.session_state['po_working_df']
                st.session_state.po_current_page = 1
                st.session_state.po_last_search = ""
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('po_active_company', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 2.5 SUPABASE CONNECTION ---
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

def fetch_all_rows(query_builder, page_size: int = 1000):
    """
    Supabase/PostgREST by default returns max 1000 rows per request.
    Ye helper .range() ke through baar baar fetch karke SAARI rows laata hai,
    chahe table me 1000 se zyada rows kyun na ho.
    'query_builder' ek function hai jo (start, end) leke supabase query chalata hai.
    """
    all_rows = []
    start = 0
    while True:
        end = start + page_size - 1
        res = query_builder(start, end)
        batch = res.data or []
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return all_rows


# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: cached site_data lookup ---
# Used only to check "does this Site ID / Project ID already exist in
# site_data" while rendering the PO table. Previously this ran up to 4
# separate Supabase queries (including a full-table fallback fetch) on
# EVERY rerun (every search keystroke, every pagination click). Now it's
# fetched once and cached for 30s, then matched locally in Python.
# -------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_site_data_lookup_cached(workspace):
    try:
        return fetch_all_rows(
            lambda start, end: supabase.table("site_data").select("*").eq("workspace", workspace).range(start, end).execute()
        )
    except Exception:
        return []


def add_site_details_to_excel(export_df, site_rows):
    """Har exported PO line par Site Name, Site ID aur Project ID ensure kare."""
    result = export_df.copy()

    site_by_id = {}
    site_by_project = {}
    for item in site_rows or []:
        site_id = str(item.get("Site ID", "") or "").strip()
        site_name = str(item.get("Site Name", "") or "").strip()
        project_id = str(item.get("Project ID", "") or "").strip()
        project_name = str(item.get("Project Name", "") or "").strip()
        details = {
            "Site ID": site_id,
            "Site Name": site_name,
            "Project ID": project_id or project_name,
        }
        if site_id:
            site_by_id[site_id.upper()] = details
        for project_key in (project_id, project_name):
            if project_key:
                site_by_project[project_key.upper()] = details

    def resolve_details(row):
        row_site_id = str(row.get("Site ID", "") or "").strip()
        # po_working ka "Project Name" column asal mein Project ID store karta hai.
        row_project_id = str(
            row.get("Project ID", "") or row.get("Project Name", "") or ""
        ).strip()
        matched = (
            site_by_id.get(row_site_id.upper())
            or site_by_project.get(row_project_id.upper())
            or {}
        )
        return pd.Series({
            "Site Name": str(row.get("Site Name", "") or "").strip() or matched.get("Site Name", ""),
            "Site ID": row_site_id or matched.get("Site ID", ""),
            "Project ID": row_project_id or matched.get("Project ID", ""),
        })

    details_df = result.apply(resolve_details, axis=1)
    for column in ["Site Name", "Site ID", "Project ID"]:
        result[column] = details_df[column]

    # Internal/misleading field ko Excel mein exact requested name se dikhayein.
    if "Project Name" in result.columns:
        result = result.drop(columns=["Project Name"])

    detail_columns = ["Site Name", "Site ID", "Project ID"]
    other_columns = [c for c in result.columns if c not in detail_columns]
    insert_at = other_columns.index("PO Number") + 1 if "PO Number" in other_columns else 0
    ordered_columns = other_columns[:insert_at] + detail_columns + other_columns[insert_at:]
    return result[ordered_columns]

# --- NEW: EGRESS OPTIMIZATION — cached per-site lookup used inside the
# "Edit PO Detailed Working" dialog. Previously these 2 small queries
# (site_data + Excalation/Escalation Matrix, both filtered by Site ID) ran
# on EVERY rerun while the dialog was open — every cell edit in the data
# editor re-triggers the whole script, so every keystroke was hitting
# Supabase twice more. Now cached for 30s per Site ID.
@st.cache_data(ttl=30, show_spinner=False)
def fetch_po_detail_site_info_cached(site_id, workspace):
    cluster_val, rfai_val, srn_val, km_val = "-", "-", "-", "-"
    if not site_id:
        return cluster_val, rfai_val, srn_val, km_val
    try:
        res_site = supabase.table("site_data").select("*").eq("Site ID", str(site_id).strip()).eq("workspace", workspace).execute()
        if res_site.data:
            cluster_val = res_site.data[0].get("Cluster", "-")
            rfai_val = res_site.data[0].get("RFAI Status", "-")
            srn_val = res_site.data[0].get("SRN", "-")
    except Exception:
        pass
    try:
        res_exc = supabase.table("Excalation Matrix").select("*").eq("Site ID", str(site_id).strip()).execute()
        if res_exc.data:
            km_val = res_exc.data[0].get("KM", "-")
    except Exception:
        try:
            res_exc = supabase.table("Escalation Matrix").select("*").eq("Site ID", str(site_id).strip()).execute()
            if res_exc.data:
                km_val = res_exc.data[0].get("KM", "-")
        except Exception:
            pass
    return cluster_val, rfai_val, srn_val, km_val


@st.cache_data(ttl=300, show_spinner=False)
def fetch_po_item_master_cached():
    """Quotation page jaisa searchable item master PO popup ke liye."""
    tables_to_try = ["Item Code", "item_master", "items", "Item_Code"]
    for table_name in tables_to_try:
        try:
            rows = fetch_all_rows(
                lambda start, end, t=table_name: supabase.table(t).select("*").range(start, end).execute()
            )
            if not rows:
                continue
            items_df = pd.DataFrame(rows)
            rename_map = {}
            for col in items_df.columns:
                clean_col = str(col).strip().lower()
                if clean_col in ["item code", "item_code", "itemcode", "code", "material item"]:
                    rename_map[col] = "Item Code"
                elif clean_col in ["description", "desc", "item description", "item_description"]:
                    rename_map[col] = "Description"
                elif clean_col in ["price", "rate", "amount", "unit price"]:
                    rename_map[col] = "Price"
                elif clean_col in ["uom", "unit", "unit of measure", "unit_of_measure"]:
                    rename_map[col] = "UOM"
            items_df = items_df.rename(columns=rename_map)
            if "Item Code" not in items_df.columns:
                continue
            for required_col, default_value in {"Description": "", "Price": 0, "UOM": ""}.items():
                if required_col not in items_df.columns:
                    items_df[required_col] = default_value
            items_df = items_df[["Item Code", "Description", "UOM", "Price"]].copy()
            items_df["Item Code"] = items_df["Item Code"].fillna("").astype(str).str.strip()
            items_df["Description"] = items_df["Description"].fillna("").astype(str).str.strip()
            items_df["UOM"] = items_df["UOM"].fillna("").astype(str).str.strip()
            items_df["Price"] = pd.to_numeric(items_df["Price"], errors="coerce").fillna(0).astype(int)
            items_df = items_df[items_df["Item Code"] != ""].drop_duplicates("Item Code", keep="first")
            items_df["Display"] = items_df["Item Code"] + " | " + items_df["Description"]
            return items_df.reset_index(drop=True)
        except Exception:
            continue
    return pd.DataFrame(columns=["Item Code", "Description", "UOM", "Price", "Display"])


# --- INITIALIZE SESSION STATE DIRECTLY FROM SUPABASE WITH WORKSPACE FILTER ---
# NOTE: iska already accha pattern hai — poori po_working table sirf EK BAAR
# session_state me load hoti hai (jab tak explicitly delete na ho, jaise
# upload/edit/delete/company-switch ke baad), baar baar Supabase se re-fetch nahi hoti.
if 'po_working_df' not in st.session_state:
    try:
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        all_data = fetch_all_rows(
            lambda start, end: supabase.table("po_working").select("*").eq("workspace", active_ws).range(start, end).execute()
        )
        if all_data and len(all_data) > 0:
            df_fetched = pd.DataFrame(all_data)
            num_cols = ['Line Number', 'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'wcc_qty', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount']
            for col in num_cols:
                if col in df_fetched.columns:
                    df_fetched[col] = df_fetched[col].astype(str).str.replace(',', '', regex=True)
                    df_fetched[col] = pd.to_numeric(df_fetched[col], errors='coerce').fillna(0).astype(int)
            st.session_state.po_working_df = df_fetched
        else:
            st.session_state.po_working_df = pd.DataFrame(columns=[
                'id', 'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
                'Item Num', 'Description', 'UOM', 'PO Qty', 
                'User Qty', 'VIS Qty', 'Diff', 'wcc_qty', 'wcc_status', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
            ])
    except Exception:
        st.session_state.po_working_df = pd.DataFrame(columns=[
            'PO Number', 'Site ID', 'Site Name', 'Project Name', 'Line Number', 
            'Item Num', 'Description', 'UOM', 'PO Qty', 
            'User Qty', 'VIS Qty', 'Diff', 'wcc_qty', 'wcc_status', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
        ])

if 'id' not in st.session_state.po_working_df.columns:
    st.session_state.po_working_df['id'] = None

# --- 3. UPLOAD ORACLE PO DIALOG FUNCTION ---
@st.dialog("📄 Upload PO (Notepad)")
def po_upload_dialog():
    st.markdown("<p style='font-size:0.85rem; font-weight:800; color:#334155; margin-bottom:5px; margin-top:5px;'>PO NUMBER <span style='color:#ef4444;'>*</span></p>", unsafe_allow_html=True)
    po_number_input = st.text_input("PO NUMBER", label_visibility="collapsed", placeholder="Enter PO Number...")
    
    st.markdown("<p style='font-size:0.85rem; font-weight:800; color:#334155; margin-bottom:5px; margin-top:15px;'>PO DOCUMENT (TXT/CSV/TSV/EXCEL) <span style='color:#ef4444;'>*</span></p>", unsafe_allow_html=True)
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
                updated_count = 0
                skipped_count = 0
                update_errors = []
                
                # --- MATCHING RULE ---
                # Har line ki uniqueness ab "Project Name" (Project ID) + "Item Num" (Item Code) se decide hoti hai,
                # PO Number/Line Number se nahi. Isse same project ke andar same item code baar baar upload
                # karne par duplicate nahi banta, sirf jab Qty change ho tabhi update hota hai.
                for idx, new_row in df_proc.iterrows():
                    proj_val = str(new_row.get('Project Name', '')).strip()
                    item_val = str(new_row.get('Item Num', '')).strip()
                    
                    match_mask = (
                        existing_df['Project Name'].astype(str).str.strip() == proj_val
                    ) & (
                        existing_df['Item Num'].astype(str).str.strip() == item_val
                    )
                    
                    if match_mask.any():
                        match_idx = existing_df[match_mask].index[0]
                        row_id = existing_df.at[match_idx, 'id'] if 'id' in existing_df.columns else None
                        
                        curr_po = int(existing_df.at[match_idx, 'PO Qty']) if pd.notna(existing_df.at[match_idx, 'PO Qty']) else 0
                        curr_vis = int(existing_df.at[match_idx, 'VIS Qty']) if pd.notna(existing_df.at[match_idx, 'VIS Qty']) else 0
                        new_po = int(new_row['PO Qty'])
                        new_price = int(new_row['Price'])
                        
                        new_diff = new_po - curr_vis
                        new_amount = curr_vis * new_price
                        
                        if pd.notna(row_id):
                            try:
                                supabase.table("po_working").update({
                                    'PO Number': po_no,
                                    'Line Number': int(new_row['Line Number']),
                                    'PO Qty': new_po,
                                    'Price': new_price,
                                    'UOM': str(new_row['UOM']),
                                    'Description': str(new_row['Description']),
                                    'Diff': new_diff,
                                    'Amount': new_amount
                                }).eq("id", row_id).execute()
                                updated_count += 1
                            except Exception as e:
                                # FIX: pehle ye error silently swallow ho jaata tha - ab dikhega
                                update_errors.append(f"Item {item_val}: {e}")
                        else:
                            update_errors.append(f"Item {item_val}: matched row me 'id' nahi mila, update skip ho gaya.")
                    else:
                        # Is Project ke liye ye Item Code pehli baar aa raha hai -> naya row add hoga
                        new_rows_to_add.append(new_row.to_dict())
                
                inserted_count = 0
                if new_rows_to_add:
                    records_to_insert = []
                    for rec in new_rows_to_add:
                        clean_rec = {}
                        clean_rec["workspace"] = st.session_state.get('active_workspace', 'VISPL')
                        for k, v in rec.items():
                            if k in num_columns_to_int:
                                clean_rec[k] = int(v)
                            else:
                                clean_rec[k] = str(v).strip() if pd.notna(v) and str(v) != 'nan' else ""
                        records_to_insert.append(clean_rec)
                    
                    try:
                        res = supabase.table("po_working").insert(records_to_insert).execute()
                        inserted_count = len(res.data) if res.data else 0
                        if inserted_count == 0:
                            # Supabase ne error nahi diya lekin kuch bhi return nahi kiya - isko bhi flag karo
                            update_errors.append("Insert call ne 0 rows return ki - RLS policy ya column mismatch check karo.")
                    except Exception as e:
                        st.error(f"❌ DB Insert Error: Please verify Supabase columns match exactly. Details: {e}")
                        return
                
                if 'po_working_df' in st.session_state:
                    del st.session_state['po_working_df']

                fetch_site_data_lookup_cached.clear()
                fetch_po_detail_site_info_cached.clear()
                
                st.session_state['po_upload_success_msg'] = po_number_input
                st.session_state['po_upload_summary'] = {
                    'added': inserted_count,
                    'updated': updated_count,
                    'skipped': skipped_count,
                    'errors': update_errors,
                }
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
        
    # --- ADDING SITE STATUS TO EXCEL ---
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    available_sites = set()
    available_projects = set()

    # Reuses the same 30s-cached lookup instead of a fresh full-table fetch —
    # export is an occasional action, but no reason to hit Supabase again if
    # the page-level lookup already has fresh-enough data.
    site_rows = fetch_site_data_lookup_cached(active_ws)
    for item in site_rows:
        s_id = str(item.get("Site ID", "")).strip()
        p_id = str(item.get("Project ID", "")).strip()
        p_name = str(item.get("Project Name", "")).strip()
        
        if s_id: available_sites.add(s_id)
        if p_id: available_projects.add(p_id)
        if p_name: available_projects.add(p_name)

    # Har PO line ke aage exact Site Name, Site ID aur Project ID add/fill karein.
    export_df = add_site_details_to_excel(export_df, site_rows)

    def get_site_status(row):
        sid = str(row.get("Site ID", "")).strip()
        pname = str(row.get("Project Name", "")).strip()

        is_site_avail = sid and sid in available_sites
        is_proj_avail = pname and (pname in available_projects or pname in available_sites)

        if is_site_avail or is_proj_avail:
            return "Available"
        return "Not Available"

    if 'Project ID' in export_df.columns:
        loc = export_df.columns.get_loc('Project ID') + 1
        export_df.insert(loc, 'SITE STATUS', export_df.apply(get_site_status, axis=1))
    else:
        export_df['SITE STATUS'] = export_df.apply(get_site_status, axis=1)
    # -----------------------------------

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
@st.dialog("✏️ Edit PO Detailed Working", width="large")
def view_po_details_dialog(row_data):
    po_no = row_data['PO Number']
    site_id = row_data['Site ID']
    site_name = row_data['Site Name']
    proj_name = row_data['Project Name']

    active_ws = st.session_state.get('active_workspace', 'VISPL')
    # FIX (egress optimization): ye 2 chhoti si single-row lookups (site_data +
    # Excalation/Escalation Matrix) pehle BINA caching ke thi — dialog ke andar
    # har interaction (jaise data editor me cell edit) par poora script phir
    # se chalta hai, matlab har baar dono queries dobara Supabase ko hit karti
    # thi. Ab 30s ke liye cache kiya gaya hai.
    cluster_val, rfai_val, srn_val, km_val = fetch_po_detail_site_info_cached(site_id, active_ws)

    display_cols = [
        'id', 'Line Number', 'PO Number', 'Item Num', 'Description', 'UOM', 
        'PO Qty', 'User Qty', 'VIS Qty', 'Diff', 'wcc_qty', 'wcc_status', 'Claim Qty', 'Receipt Qty', 'Price', 'Amount'
    ]
    
    # Versioned key clears the old data-editor schema where PO Qty was locked.
    editor_key = f"po_editor_v3_{po_no}_{proj_name}"
    
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

    # 🟢 WCC Qty / WCC Status — pushed here by the WCC Upload automation.
    # Display-only in this dialog (not editable, not recalculated).
    if 'wcc_qty' in df_temp.columns:
        df_temp['wcc_qty'] = df_temp['wcc_qty'].astype(str).str.replace(',', '', regex=True)
        df_temp['wcc_qty'] = pd.to_numeric(df_temp['wcc_qty'], errors='coerce').fillna(0).astype(int)
    else:
        df_temp['wcc_qty'] = 0

    if 'wcc_status' in df_temp.columns:
        df_temp['wcc_status'] = df_temp['wcc_status'].fillna('').astype(str)
        df_temp['wcc_status'] = df_temp['wcc_status'].replace('nan', '')
    else:
        df_temp['wcc_status'] = ''
    
    df_temp['User Qty'] = df_temp['User Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['User Qty'] = pd.to_numeric(df_temp['User Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Claim Qty'] = df_temp['Claim Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['Claim Qty'] = pd.to_numeric(df_temp['Claim Qty'], errors='coerce').fillna(0).astype(int)
    
    df_temp['Receipt Qty'] = df_temp['Receipt Qty'].astype(str).str.replace(',', '', regex=True)
    df_temp['Receipt Qty'] = pd.to_numeric(df_temp['Receipt Qty'], errors='coerce').fillna(0).astype(int)
    
    st.session_state.po_working_df.update(df_temp)
    
    project_total_amount = (df_temp['PO Qty'] * df_temp['Price']).sum()
    
    st.markdown(f"""
        <div class="kpi-pill-container">
            <div class="kpi-pill">SITE ID: <span>{site_id}</span></div>
            <div class="kpi-pill">SITE NAME: <span>{site_name}</span></div>
            <div class="kpi-pill">PROJECT ID: <span>{proj_name}</span></div>
            <div class="kpi-pill">CLUSTER: <span>{cluster_val}</span></div>
            <div class="kpi-pill">RFAI: <span>{rfai_val}</span></div>
            <div class="kpi-pill">SRN: <span>{srn_val}</span></div>
            <div class="kpi-pill" style="border-color: #fecaca; background:#fef2f2;">KM: <span style="color: #dc2626;">{km_val}</span></div>
            <div class="kpi-pill" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); border: none; box-shadow: 0 6px 14px -4px rgba(99,102,241,.6);">
                <span style="color: #ffffff !important; font-weight: 900; letter-spacing: 1px; font-size: 0.95rem;">PROJECT AMOUNT : ₹ {project_total_amount:,}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Download only this popup's complete PO/Project line details.
    popup_export_cols = ['Site ID', 'Site Name', 'Project Name'] + display_cols
    popup_export_df = df_temp[[c for c in popup_export_cols if c in df_temp.columns]].copy()
    if "id" in popup_export_df.columns:
        popup_export_df = popup_export_df.drop(columns=["id"])
    popup_export_df = add_site_details_to_excel(
        popup_export_df,
        fetch_site_data_lookup_cached(active_ws),
    )
    popup_excel = io.BytesIO()
    with pd.ExcelWriter(popup_excel, engine="openpyxl") as writer:
        popup_export_df.to_excel(writer, index=False, sheet_name="PO Line Details")
    safe_po_file = "".join(ch for ch in str(po_no) if ch.isalnum() or ch in ("-", "_")) or "PO"
    st.download_button(
        "📥 Download This PO Excel",
        data=popup_excel.getvalue(),
        file_name=f"PO_{safe_po_file}_Line_Details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"popup_excel_{safe_po_file}_{proj_name}",
        use_container_width=True,
        type="primary"
    )

    # Search item from master and save immediately against same PO + Project ID.
    item_master_df = fetch_po_item_master_cached()
    with st.expander("➕ Add New PO Line", expanded=False):
        if item_master_df.empty:
            st.warning("Item master me koi item nahi mila. Item Code/item_master table check karein.")
        else:
            item_options = [""] + item_master_df["Display"].tolist()
            add_form_version_key = f"po_add_form_version_{safe_po_file}_{proj_name}"
            if add_form_version_key not in st.session_state:
                st.session_state[add_form_version_key] = 0
            add_form_version = st.session_state[add_form_version_key]
            add_col1, add_col2, add_col3, add_col4, add_col5 = st.columns([5, 1.5, 1.5, 1.5, 1.5])
            with add_col1:
                selected_item_display = st.selectbox(
                    "SEARCH ITEM CODE / DESCRIPTION", item_options,
                    key=f"po_add_item_{safe_po_file}_{proj_name}_{add_form_version}"
                )
            selected_master_row = None
            default_price = 0
            default_uom = ""
            if selected_item_display:
                selected_rows = item_master_df[item_master_df["Display"] == selected_item_display]
                if not selected_rows.empty:
                    selected_master_row = selected_rows.iloc[0]
                    default_price = int(selected_master_row.get("Price", 0) or 0)
                    default_uom = str(selected_master_row.get("UOM", "") or "")
            selected_item_key = "".join(
                ch for ch in str(selected_item_display) if ch.isalnum()
            )[:40] or "blank"
            with add_col2:
                new_po_qty = st.number_input(
                    "PO QTY", min_value=0, value=0, step=1,
                    key=f"po_add_qty_{safe_po_file}_{proj_name}_{add_form_version}"
                )
            with add_col3:
                new_user_qty = st.number_input(
                    "USER QTY", min_value=0, value=0, step=1,
                    key=f"po_add_user_qty_{safe_po_file}_{proj_name}_{add_form_version}"
                )
            with add_col4:
                new_vis_qty = st.number_input(
                    "VIS QTY", min_value=0, value=0, step=1,
                    key=f"po_add_vis_qty_{safe_po_file}_{proj_name}_{add_form_version}"
                )
            with add_col5:
                new_price = st.number_input(
                    "PRICE", min_value=0, value=default_price, step=1,
                    key=f"po_add_price_{safe_po_file}_{proj_name}_{selected_item_key}_{add_form_version}"
                )
            next_line_preview = int(pd.to_numeric(df_temp["Line Number"], errors="coerce").fillna(0).max()) + 1
            if selected_master_row is not None:
                st.caption(
                    f"Description: {selected_master_row.get('Description', '')} | "
                    f"UOM: {default_uom or '-'} | अगली Line: {next_line_preview}"
                )
            if st.button(
                "➕ Add & Save Line", type="primary", use_container_width=True,
                key=f"po_add_save_{safe_po_file}_{proj_name}_{add_form_version}"
            ):
                if selected_master_row is None:
                    st.error("पहले Item Code select करें।")
                else:
                    new_item_code = str(selected_master_row.get("Item Code", "")).strip()
                    duplicate_mask = df_temp["Item Num"].astype(str).str.strip() == new_item_code
                    if duplicate_mask.any():
                        st.error("यह Item Code इस PO और Project ID में पहले से मौजूद है। Existing line edit करें।")
                    else:
                        insert_payload = {
                            "workspace": active_ws,
                            "PO Number": str(po_no).strip(),
                            "Site ID": str(site_id).strip(),
                            "Site Name": str(site_name).strip(),
                            "Project Name": str(proj_name).strip(),
                            "Line Number": next_line_preview,
                            "Item Num": new_item_code,
                            "Description": str(selected_master_row.get("Description", "") or "").strip(),
                            "UOM": default_uom,
                            "PO Qty": int(new_po_qty),
                            "User Qty": int(new_user_qty),
                            "VIS Qty": int(new_vis_qty),
                            "Diff": int(new_po_qty) - int(new_vis_qty),
                            "wcc_qty": 0, "wcc_status": "",
                            "Claim Qty": 0, "Receipt Qty": 0,
                            "Price": int(new_price),
                            "Amount": int(new_vis_qty) * int(new_price)
                        }
                        try:
                            insert_result = supabase.table("po_working").insert(insert_payload).execute()
                            saved_row = insert_result.data[0] if insert_result.data else insert_payload
                            st.session_state.po_working_df = pd.concat(
                                [st.session_state.po_working_df, pd.DataFrame([saved_row])],
                                ignore_index=True
                            )
                            if editor_key in st.session_state:
                                del st.session_state[editor_key]
                            # Next manual-entry form starts fresh; PO Qty is always 0 by default.
                            st.session_state[add_form_version_key] += 1
                            st.success(f"✅ Line {next_line_preview} Supabase में save हो गई।")
                            try:
                                st.rerun(scope="fragment")
                            except TypeError:
                                st.rerun()
                        except Exception as add_error:
                            st.error(f"❌ नई PO line save नहीं हुई: {add_error}")
    
    active_cols = [c for c in display_cols if c in st.session_state.po_working_df.columns]
    po_specific_df = st.session_state.po_working_df[po_specific_mask][active_cols].copy()

    st.markdown('<div class="modal-section-title">📋 PO LINE ITEMS</div>', unsafe_allow_html=True)
    
    edited_po_df = st.data_editor(
        po_specific_df, 
        key=editor_key,
        use_container_width=True, 
        hide_index=True,
        height=400, 
        disabled=["Line Number", "PO Number", "Item Num", "Description", "UOM", "Diff", "wcc_qty", "wcc_status", "Amount"],
        column_config={
            "id": None, "Site ID": None, "Site Name": None, "Project Name": None,
            "Line Number": st.column_config.NumberColumn("Line", width="small", alignment="center", format="%d"),
            "PO Number": st.column_config.TextColumn("PO Number", alignment="center"),
            "PO Qty": st.column_config.NumberColumn("PO Qty", min_value=0, alignment="center", format="%d", step=1),
            "User Qty": st.column_config.NumberColumn("USER QTY", alignment="center", format="%d", step=1),
            "VIS Qty": st.column_config.NumberColumn("VIS QTY", alignment="center", format="%d", step=1),
            "Diff": st.column_config.NumberColumn("Diff", disabled=True, alignment="center", format="%d"),
            "wcc_qty": st.column_config.NumberColumn("WCC QTY", disabled=True, alignment="center", format="%d"),
            "wcc_status": st.column_config.TextColumn("WCC STATUS", disabled=True, alignment="center"),
            "Claim Qty": st.column_config.NumberColumn("CLAIM QTY", alignment="center", format="%d", step=1),
            "Receipt Qty": st.column_config.NumberColumn("RECEIPT QTY", alignment="center", format="%d", step=1),
            "Price": st.column_config.NumberColumn("Price", alignment="center", format="%d"),
            "Amount": st.column_config.NumberColumn("Amount", disabled=True, alignment="center", format="%d")
        }
    )

    # Delete one selected PO line from both Supabase and the popup table.
    st.markdown('<div class="modal-section-title">🗑️ DELETE PO LINE</div>', unsafe_allow_html=True)
    delete_options = []
    delete_row_map = {}
    for _, delete_row in po_specific_df.iterrows():
        delete_id = delete_row.get("id")
        delete_label = (
            f"Line {delete_row.get('Line Number', '-')} | "
            f"{delete_row.get('Item Num', '')} | {delete_row.get('Description', '')}"
        )
        delete_options.append(delete_label)
        delete_row_map[delete_label] = delete_id

    del_col1, del_col2 = st.columns([8, 2])
    with del_col1:
        selected_delete_line = st.selectbox(
            "SELECT LINE TO DELETE",
            options=[""] + delete_options,
            key=f"po_delete_select_{safe_po_file}_{proj_name}"
        )
    with del_col2:
        st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
        delete_clicked = st.button(
            "🗑️ Delete Line",
            use_container_width=True,
            key=f"po_delete_btn_{safe_po_file}_{proj_name}"
        )

    if delete_clicked:
        if not selected_delete_line:
            st.error("पहले delete करने वाली line select करें।")
        else:
            selected_delete_id = delete_row_map.get(selected_delete_line)
            if pd.isna(selected_delete_id):
                st.error("इस line की database ID नहीं मिली, इसलिए delete नहीं की गई।")
            else:
                try:
                    supabase.table("po_working").delete().eq("id", selected_delete_id).execute()
                    current_df = st.session_state.po_working_df
                    st.session_state.po_working_df = current_df[current_df["id"] != selected_delete_id].reset_index(drop=True)
                    if editor_key in st.session_state:
                        del st.session_state[editor_key]
                    st.success("✅ Selected PO line delete हो गई।")
                    try:
                        st.rerun(scope="fragment")
                    except TypeError:
                        st.rerun()
                except Exception as delete_error:
                    st.error(f"❌ Line delete नहीं हुई: {delete_error}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_v1, col_v2 = st.columns([8, 2])
    with col_v2:
        if st.button("💾 Submit", type="primary", use_container_width=True):
            save_errors = []
            def safe_int(value):
                parsed_value = pd.to_numeric(value, errors="coerce")
                return 0 if pd.isna(parsed_value) else int(parsed_value)

            for idx, row in edited_po_df.iterrows():
                try:
                    if pd.notna(row.get('id')):
                        po_qty_val = safe_int(row.get('PO Qty', 0))
                        user_qty_val = safe_int(row.get('User Qty', 0))
                        vis_qty_val = safe_int(row.get('VIS Qty', 0))
                        claim_qty_val = safe_int(row.get('Claim Qty', 0))
                        receipt_qty_val = safe_int(row.get('Receipt Qty', 0))
                        price_val = safe_int(row.get('Price', 0))
                        diff_val = po_qty_val - vis_qty_val
                        amount_val = vis_qty_val * price_val
                        update_payload = {
                            "PO Qty": po_qty_val,
                            "User Qty": user_qty_val,
                            "VIS Qty": vis_qty_val,
                            "Diff": diff_val,
                            "Claim Qty": claim_qty_val,
                            "Receipt Qty": receipt_qty_val,
                            "Price": price_val,
                            "Amount": amount_val
                        }
                        supabase.table("po_working").update(update_payload).eq("id", row['id']).execute()
                except Exception as save_error:
                    save_errors.append(f"Line {row.get('Line Number', idx + 1)}: {save_error}")

            if save_errors:
                st.error("❌ कुछ lines save नहीं हुई:\n" + "\n".join(save_errors))
                return
            
            if editor_key in st.session_state:
                del st.session_state[editor_key]
                
            if 'po_working_df' in st.session_state:
                del st.session_state['po_working_df']
                
            st.success("✅ PO Lines Submitted Successfully to DB!")
            st.rerun()


# --- 4.6 DELETE PO CONFIRMATION DIALOG (replaces the old inline confirm row) ---
@st.dialog("🗑️ Delete PO")
def delete_po_dialog(row_data):
    po_num = str(row_data.get("PO Number", "")).strip()
    proj_val = str(row_data.get("Project Name", "")).strip()
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    line_count = 0
    try:
        _dfw = st.session_state.po_working_df
        line_count = int(((_dfw['PO Number'].astype(str).str.strip() == po_num) &
                          (_dfw['Project Name'].astype(str).str.strip() == proj_val)).sum())
    except Exception:
        pass

    st.markdown(
        f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
<div style="font-weight:900;color:#991b1b;font-size:1rem;">PO {html.escape(po_num or '-')}</div>
<div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">Project ID: {html.escape(proj_val or '-')} • Site: {html.escape(str(row_data.get('Site ID','') or '-'))} • {line_count} line(s)</div>
</div>
<p style="color:#475569;">Is PO + Project ID ki saari line items permanently delete ho jayengi. Kya aap sure hain?</p>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="po_del_no", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="po_del_yes", type="primary", use_container_width=True):
            try:
                # FIX: pehle sirf "PO Number" se delete hota tha — isse same PO Number wali
                # DOOSRI company (workspace) aur doosre Project IDs ki lines bhi delete ho jaati thi.
                # Ab sirf isi workspace + isi PO + isi Project ID ki lines delete hoti hain.
                q = supabase.table("po_working").delete().eq("PO Number", po_num).eq("workspace", active_ws)
                if proj_val:
                    q = q.eq("Project Name", proj_val)
                q.execute()
                if 'po_working_df' in st.session_state:
                    del st.session_state['po_working_df']
                st.success(f"✅ PO {po_num} Deleted Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Deleting Record: {e}")

# --- 5. TOP ACTION BAR ---
col_title, col_ref, col_upload, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>🧾 PO Working Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        if 'po_working_df' in st.session_state:
            del st.session_state['po_working_df']
        fetch_site_data_lookup_cached.clear()
        fetch_po_detail_site_info_cached.clear()
        st.rerun() 
with col_upload:
    if st.button("📤 PO Upload Notepad", type="primary", use_container_width=True):
        po_upload_dialog() 
with col_export:
    if st.button("📥 Export", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- CELEBRATION BLOCK AFTER UPLOAD ---
if st.session_state.get('po_upload_success_msg'):
    summary = st.session_state.get('po_upload_summary', {})
    added = summary.get('added', 0)
    updated = summary.get('updated', 0)
    skipped = summary.get('skipped', 0)
    errors = summary.get('errors', [])

    if added > 0 or updated > 0:
        st.balloons()
        st.toast(f"🎉 BINGO! PO {st.session_state['po_upload_success_msg']} Processed!", icon="🎈")

    st.success(
        f"🎊 PO **{st.session_state['po_upload_success_msg']}** processed — "
        f"🆕 {added} naye items add hue, ✏️ {updated} items update hue, "
        f"⏭️ {skipped} items same the (no change)."
    )
    if errors:
        st.error("⚠️ Kuch items save nahi ho paaye:\n\n" + "\n".join(f"- {e}" for e in errors))

    del st.session_state['po_upload_success_msg']
    if 'po_upload_summary' in st.session_state:
        del st.session_state['po_upload_summary']

# --- FETCH DATA FROM SESSION ---
df = st.session_state.po_working_df.copy()

if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 6. SEARCH BOX + VIEW MODE TOGGLE ---
col_table_title, col_search, col_viewtoggle = st.columns([5, 3, 2])
with col_table_title:
    st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Uploaded PO Summary</h5>", unsafe_allow_html=True)
with col_search:
    if HAS_KEYUP:
        search_query = st_keyup("Search", placeholder="🔍 Search PO, Project, Site...", label_visibility="collapsed", debounce=300)
    else:
        search_query = st.text_input("Search", placeholder="🔍 Search PO, Project, Site...", label_visibility="collapsed")
        st.caption("Auto-search requires `streamlit-keyup`. Run: `pip install streamlit-keyup`")
with col_viewtoggle:
    toggle_label = "📱 Mobile View" if st.session_state.po_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="po_view_mode_toggle"):
        st.session_state.po_view_mode = "cards" if st.session_state.po_view_mode == "table" else "table"
        st.rerun()

if 'po_last_search' not in st.session_state:
    st.session_state.po_last_search = ""

# Jab bhi search text change ho, page ko 1 par reset kar do - warna filtered
# results kam hone par purane page number ki wajah se list khali dikhti hai.
if search_query != st.session_state.po_last_search:
    st.session_state.po_current_page = 1
    st.session_state.po_last_search = search_query

if search_query:
    # fillna('') taaki blank/None values 'nan' text na ban jayein,
    # regex=False taaki PO/Item text me mojood special characters (jaise ( ) + . /)
    # se koi match error ya galat filtering na ho.
    search_df = df.fillna('').astype(str)
    mask = search_df.apply(lambda x: x.str.contains(search_query, case=False, na=False, regex=False)).any(axis=1)
    df = df[mask]

# --- CREATE UNIQUE PO SUMMARY LIST (+ line count & PO value per PO/Project) ---
SUMMARY_KEYS = ['Project Name', 'Site ID', 'Site Name', 'PO Number']
if not df.empty:
    _calc = df.copy()
    for _c in SUMMARY_KEYS:
        if _c not in _calc.columns:
            _calc[_c] = ""
        _calc[_c] = _calc[_c].fillna("").astype(str)
    _calc['_value'] = (pd.to_numeric(_calc.get('PO Qty', 0), errors='coerce').fillna(0)
                       * pd.to_numeric(_calc.get('Price', 0), errors='coerce').fillna(0))
    summary_df = (_calc.groupby(SUMMARY_KEYS, sort=False)
                  .agg(_lines=('_value', 'size'), _po_value=('_value', 'sum'))
                  .reset_index())
    summary_df = summary_df.iloc[::-1].reset_index(drop=True)
else:
    summary_df = pd.DataFrame(columns=SUMMARY_KEYS + ['_lines', '_po_value'])

# --- SITE AVAILABILITY LOOKUP (cached) ---
active_ws = st.session_state.get('active_workspace', 'VISPL')
available_sites = set()
available_projects = set()
project_name_lookup = {}   # Project ID -> actual Project Name (from site_data)
for item in fetch_site_data_lookup_cached(active_ws):
    sid_val = str(item.get("Site ID", "")).strip()
    pid_val = str(item.get("Project ID", "")).strip()
    pname_val = str(item.get("Project Name", "")).strip()
    if sid_val:
        available_sites.add(sid_val)
    if pid_val:
        available_projects.add(pid_val)
        if pname_val:
            project_name_lookup[pid_val] = pname_val
            project_name_lookup[pid_val.upper()] = pname_val
    if pname_val:
        available_projects.add(pname_val)

def _is_available(site_id_val, proj_name_val):
    return bool((site_id_val and site_id_val in available_sites) or (proj_name_val and proj_name_val in available_projects))

if not summary_df.empty:
    summary_df['_avail'] = [
        _is_available(str(s).strip(), str(p).strip())
        for s, p in zip(summary_df['Site ID'], summary_df['Project Name'])
    ]
else:
    summary_df['_avail'] = []

# --- KPI CARDS (search ke hisaab se) ---
k_entries = len(summary_df)
k_unique_po = summary_df['PO Number'].replace("", pd.NA).dropna().nunique() if k_entries else 0
k_avail = int(summary_df['_avail'].sum()) if k_entries else 0
k_not_avail = k_entries - k_avail
k_value = float(summary_df['_po_value'].sum()) if k_entries else 0.0

def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

st.markdown(
    '<div class="lux-kpi-grid">'
    + _kpi("🧾", "PO Entries", f"{k_entries:,}", f"{k_unique_po:,} unique PO numbers", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
    + _kpi("💰", "Total PO Value", f"₹ {k_value:,.0f}", "PO Qty × Price", "linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")
    + _kpi("🟢", "Site Available", f"{k_avail:,}", "Found in Site Data", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5", "green")
    + _kpi("🟠", "Site Not Available", f"{k_not_avail:,}", "Add these in Site Data", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb", "red" if k_not_avail else "")
    + '</div>',
    unsafe_allow_html=True,
)

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

# --- 8. ✨ LAVISH SUMMARY TABLE (or mobile cards) ---
df_page = summary_df.iloc[start_idx:end_idx].copy()

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
    return "" if s.lower() in ("nan", "none", "null", "-") else s

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

def _status_html(avail):
    return ("<span class='status-badge-green'>🟢 Available</span>" if avail
            else "<span class='status-badge-orange'>🟠 Not Available</span>")

if df_page.empty:
    st.markdown(
        '<div class="slux-empty"><div>🗂️</div>'
        + ("No PO records match your search." if search_query else "No PO records found. Click 📤 PO Upload Notepad to add one.")
        + '</div>',
        unsafe_allow_html=True,
    )

elif st.session_state.po_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE-FRIENDLY CARD VIEW - one card per PO record
    # ---------------------------------------------------------------
    for page_pos, (_, row) in enumerate(df_page.iterrows()):
        row_dict = row.to_dict()
        po_num = str(row_dict.get('PO Number', '')).strip()
        proj_name_val = str(row_dict.get('Project Name', '')).strip()
        serial_no = start_idx + page_pos + 1
        safe_po_key = f"{urllib.parse.quote(po_num)}_{serial_no}"
        resolved_proj_name = project_name_lookup.get(proj_name_val) or project_name_lookup.get(proj_name_val.upper(), "-")

        with st.container(border=True):
            st.markdown(f"""
                <div class="po-card-title">#{serial_no} — PO {html.escape(po_num or '-')}</div>
                <div class="po-card-sub">{html.escape(proj_name_val or '-')}</div>
                <div class="po-card-row"><span class="po-card-label">Project Name</span><span class="po-card-value">{html.escape(resolved_proj_name)}</span></div>
                <div class="po-card-row"><span class="po-card-label">Site Status</span><span class="po-card-value">{_status_html(row_dict.get('_avail'))}</span></div>
                <div class="po-card-row"><span class="po-card-label">Site ID</span><span class="po-card-value">{html.escape(_clean(row_dict.get('Site ID')) or '-')}</span></div>
                <div class="po-card-row"><span class="po-card-label">Site Name</span><span class="po-card-value">{html.escape(_clean(row_dict.get('Site Name')) or '-')}</span></div>
                <div class="po-card-row"><span class="po-card-label">Lines</span><span class="po-card-value">{int(row_dict.get('_lines') or 0)}</span></div>
                <div class="po-card-row"><span class="po-card-label">PO Value</span><span class="po-card-value" style="color:#4f46e5;font-weight:900;">₹ {float(row_dict.get('_po_value') or 0):,.0f}</span></div>
            """, unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✏️ Edit", key=f"card_edit_{safe_po_key}", use_container_width=True):
                    view_po_details_dialog(row_dict)
            with bc2:
                if st.button("🗑️ Delete", key=f"card_del_{safe_po_key}", use_container_width=True):
                    delete_po_dialog(row_dict)

else:
    # ---------------------------------------------------------------
    # ✨ LAVISH DESKTOP TABLE VIEW — single ⚙️ button at row start
    # ---------------------------------------------------------------
    COL_RATIOS = [0.55, 0.5, 1.5, 1.5, 1.3, 1.1, 1.8, 1.3, 0.7, 1.2]
    COL_LABELS = ["⚙️", "#", "PROJECT ID", "PROJECT NAME", "SITE STATUS", "SITE ID", "SITE NAME", "PO NUMBER", "LINES", "PO VALUE"]

    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">🧾 PO Register<span>newest first</span></div>'
        f'<div class="slux-badge">₹ {k_value:,.0f}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="po_table_wrap", height=560):
        # Header (sticky)
        with st.container(key="pohead"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                cls = " c" if i in (0, 1, 8) else (" r" if i == 9 else "")
                h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

        # Rows
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            po_num = str(row_dict.get('PO Number', '')).strip()
            proj_name_val = str(row_dict.get('Project Name', '')).strip()
            resolved_proj_name = project_name_lookup.get(proj_name_val) or project_name_lookup.get(proj_name_val.upper(), "")

            serial_no = start_idx + page_pos + 1
            safe_po_key = f"{urllib.parse.quote(po_num)}_{serial_no}"
            row_css_key = "".join(ch for ch in safe_po_key if ch.isalnum() or ch in "_-") or f"r{serial_no}"
            parity = "odd" if serial_no % 2 else "even"

            with st.container(key=f"porow_{parity}_{row_css_key}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                with rcols[0]:
                    with st.container(key=f"popop_{row_css_key}"):
                        with st.popover("⚙️"):
                            if st.button("✏️ Edit Details", key=f"edit_{safe_po_key}", use_container_width=True):
                                view_po_details_dialog(row_dict)
                            if st.button("🗑️ Delete PO", key=f"del_{safe_po_key}", use_container_width=True):
                                delete_po_dialog(row_dict)

                rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)
                rcols[2].markdown(_chip(proj_name_val, "proj"), unsafe_allow_html=True)
                rcols[3].markdown(_txt(resolved_proj_name, "slux-strong"), unsafe_allow_html=True)
                rcols[4].markdown(_status_html(row_dict.get('_avail')), unsafe_allow_html=True)
                rcols[5].markdown(_chip(row_dict.get('Site ID')), unsafe_allow_html=True)
                rcols[6].markdown(_txt(row_dict.get('Site Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[7].markdown(_chip(po_num, "po"), unsafe_allow_html=True)
                rcols[8].markdown(f"<div style='text-align:center;'><span class='po-lines'>{int(row_dict.get('_lines') or 0)}</span></div>", unsafe_allow_html=True)
                rcols[9].markdown(f"<div class='slux-cell po-amt'>₹ {float(row_dict.get('_po_value') or 0):,.0f}</div>", unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    st.markdown(
        '<div class="slux-foot">'
        f'<div>{total_rows:,} PO entr{"ies" if total_rows != 1 else "y"}<small>Showing {shown_from}–{shown_to}</small></div>'
        f'<div class="slux-foot-amts"><span>Total PO Value: <b style="color:#4f46e5;">₹ {k_value:,.0f}</b></span>'
        f'<span class="slux-foot-badge">Page {st.session_state.po_current_page} of {total_pages}</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

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
