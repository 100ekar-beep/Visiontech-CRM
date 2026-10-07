import streamlit as st
import pandas as pd
import math
import io
import json
import html
import inspect
from datetime import datetime
from uuid import uuid4
from supabase import create_client, Client
from st_keyup import st_keyup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="JMS - Joint Measurement Sheet", page_icon="🧾", layout="wide")

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
/* FIX: table box khud scroll karta hai (78% screen height) — header isi box ke top par chipka rahe */
.stApp div[class*="_table_wrap"] { max-height: 78vh !important; overflow: auto !important; }
.stApp div[class*="_table_wrap"] > div[class*="st-key-jmshead"],
.stApp div[class*="_table_wrap"] > div:has(div[class*="st-key-jmshead"]) {
    position: sticky !important; top: 0 !important; z-index: 20 !important;
}
/* Header: alag gehra color + bold safed text + amber underline */
.stApp div[class*="st-key-jmshead"] {
    background: linear-gradient(90deg, #312e81 0%, #4338ca 45%, #6d28d9 100%) !important;
    border-bottom: 3px solid #f59e0b !important;
    box-shadow: 0 8px 14px -8px rgba(30, 27, 75, .55) !important;
    padding: 14px 0 !important;
}
.stApp div[class*="st-key-jmshead"] [data-testid="stColumn"], .stApp div[class*="st-key-jmshead"] [data-testid="column"] { border-right: 1px solid rgba(255,255,255,.18) !important; }
.stApp div[class*="st-key-jmshead"] .slux-th, .stApp div[class*="st-key-jmshead"] p {
    color: #ffffff !important; font-size: .76rem !important; font-weight: 900 !important;
    letter-spacing: 1.2px !important; text-shadow: 0 1px 2px rgba(0,0,0,.25);
}

</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'jmspage_open_row' not in st.session_state:
    st.session_state.jmspage_open_row = None
if 'jmspage_loaded_key' not in st.session_state:
    st.session_state.jmspage_loaded_key = None
if 'jmspage_lines' not in st.session_state:
    st.session_state.jmspage_lines = []
if 'jmspage_last_pdf' not in st.session_state:
    st.session_state.jmspage_last_pdf = None
if 'jmspage_add_gen' not in st.session_state:
    st.session_state.jmspage_add_gen = 0
if 'jmspage_current_page' not in st.session_state:
    st.session_state.jmspage_current_page = 1

# --- GUARD AGAINST STALE DIALOG STATE AFTER PAGE NAVIGATION ---
# session_state is shared across every page in the app, so if a JMS dialog was left
# open (user navigated away without clicking "Close"), jmspage_open_row would still
# be set on the next visit and the dialog would auto-pop-up. We tie "the dialog is
# genuinely open on THIS page visit" to a URL marker instead: it only survives
# reruns caused by interacting with widgets inside this same page (typing, editing,
# clicking Save/Add/Reload — none of which change the URL), but a fresh sidebar
# navigation to this page does NOT carry it over, so we know to reset stale state.
if st.query_params.get("jms_ctx") != "open":
    st.session_state.jmspage_open_row = None
    st.session_state.jmspage_loaded_key = None
    st.session_state.jmspage_last_pdf = None

# --- MULTI-COMPANY TAB SETUP (same as Site Data page) ---
SITE_COMPANIES = [
    ("VISPL", "VISPL"),
    ("Bhagyashree", "Bhagyashree"),
    ("Sai Tele", "Sai Tele"),
]
SITE_COMPANY_WORKSPACE_MAP = {
    "VISPL": "VISPL",
    "Bhagyashree": "BHAGYASHREE",
    "Sai Tele": "SAI TELE SERVICES",
}
if 'site_active_company' not in st.session_state:
    st.session_state.site_active_company = "VISPL"
st.session_state['active_workspace'] = SITE_COMPANY_WORKSPACE_MAP.get(st.session_state.site_active_company, "VISPL")

# --- 2. CSS (✨ LAVISH — Quotation / Site Data / Solar / Invoice jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.25);
    }
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

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
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p {
        color: #1e293b !important;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #0f172a !important; font-weight: 700 !important; letter-spacing: 0.5px;
    }

    .page-count { text-align: center; font-size: 1rem; font-weight: 800; color: #4338ca; margin-top: 10px; }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION (same theme as Site Data page,
       so switching pages doesn't flip the sidebar's look)
       ========================================================= */
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
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* Company Nav Bar */
    .st-key-jms_company_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-jms_company_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important; color: #0f172a !important;
        border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"] p,
    .st-key-jms_company_nav_bar button[kind="secondary"] span,
    .st-key-jms_company_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover p,
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover span,
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover div { color: #0f172a !important; }
    .st-key-jms_company_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    .st-key-jms_company_nav_bar button[kind="primary"] p,
    .st-key-jms_company_nav_bar button[kind="primary"] span,
    .st-key-jms_company_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; }

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
    .lux-kpi-value.red { color: #dc2626; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }
    .lux-progress { height: 6px; background: #e2e8f0; border-radius: 999px; margin-top: 8px; overflow: hidden; }
    .lux-progress > div { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #10b981, #3b82f6); }

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
    .st-key-jms_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-jms_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-jms_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-jms_table_wrap div[class*="st-key-jmshead"],
    .st-key-jms_table_wrap div[class*="st-key-jmsrow_"] { min-width: 1250px !important; }
    .st-key-jms_table_wrap [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-jms_table_wrap [data-testid="stColumn"], .st-key-jms_table_wrap [data-testid="column"] {
        padding: 0 10px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header */
    div[class*="st-key-jmshead"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-jmshead"] [data-testid="stColumn"], div[class*="st-key-jmshead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }

    /* Data rows */
    div[class*="st-key-jmsrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-jmsrow_odd"] { background: #fafaff; }
    div[class*="st-key-jmsrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-jmsrow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .86rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
    .slux-strong { font-weight: 700; color: #0f172a; }
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
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }

    /* Status pills */
    .status-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 11px; border-radius: 999px; border: 1px solid transparent;
        font-size: .7rem; font-weight: 800; letter-spacing: .4px; white-space: nowrap;
    }
    .status-green { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
    .status-grey  { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }

    /* Inline row buttons: 🧾 Create (green) / ✏️ Edit (blue) / ⬇️ PDF (purple) */
    div[class*="st-key-jmscreate_"] button, div[class*="st-key-jmsedit_"] button, div[class*="st-key-jmsrowdl_"] button {
        width: 38px !important; max-width: 38px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        box-shadow: none !important; font-size: 1rem !important; transition: all .2s ease !important;
    }
    div[class*="st-key-jmscreate_"] button { background: rgba(16,185,129,0.15) !important; border: 1px solid rgba(16,185,129,0.35) !important; }
    div[class*="st-key-jmscreate_"] button:hover { background: #10b981 !important; border-color: #34d399 !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(16,185,129,.6) !important; }
    div[class*="st-key-jmsedit_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-jmsedit_"] button:hover { background: #3b82f6 !important; border-color: #60a5fa !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important; }
    div[class*="st-key-jmsrowdl_"] button { background: rgba(168,85,247,0.15) !important; border: 1px solid rgba(168,85,247,0.3) !important; }
    div[class*="st-key-jmsrowdl_"] button:hover { background: #a855f7 !important; border-color: #c084fc !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(168,85,247,.6) !important; }
    div[class*="st-key-jmsrowdl_"] button p, div[class*="st-key-jmsrowdl_"] button span { color: #1e293b !important; }

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
    .slux-foot-badge {
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 5px 14px;
        border-radius: 999px; font-size: .75rem; letter-spacing: .5px;
    }
    .slux-empty {
        background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
        text-align: center; color: #64748b; font-weight: 600;
    }
    .slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- MULTI-COMPANY NAV BAR ---
with st.container(key="jms_company_nav_bar"):
    nav_cols = st.columns(len(SITE_COMPANIES))
    for nav_col, (company_id, company_label) in zip(nav_cols, SITE_COMPANIES):
        is_active = st.session_state.site_active_company == company_id
        with nav_col:
            if st.button(
                company_label, key=f"jms_nav_{company_id}",
                use_container_width=True, type=("primary" if is_active else "secondary")
            ):
                st.session_state.site_active_company = company_id
                st.session_state.active_workspace = SITE_COMPANY_WORKSPACE_MAP[company_id]
                st.session_state.jmspage_current_page = 1
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
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

# --- CACHED FETCHERS ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_site_data_cached(workspace):
    try:
        response = supabase.table("site_data").select("*").eq("workspace", workspace).execute()
        return response.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_jms_drafts_cached(workspace):
    """Returns {site_data_id: draft_row} for every JMS already saved in this workspace."""
    result = {}
    try:
        res = supabase.table("jms_drafts").select("*").eq("workspace", workspace).execute()
        for row in (res.data or []):
            sid = str(row.get("site_data_id", ""))
            if sid:
                result[sid] = row
    except Exception:
        pass
    return result


@st.cache_data(ttl=30, show_spinner=False)
def fetch_jms_templates_cached(workspace):
    """Load saved JMS templates and ALL their items reliably."""
    try:
        heads = (
            supabase.table("ground_template")
            .select("id,template_name")
            .order("template_name")
            .execute().data or []
        )
        if not heads:
            return []

        ids = [row["id"] for row in heads]

        # IMPORTANT:
        # Some existing ground_template_items tables do not have item_description.
        # Selecting that column makes the whole query fail and template appears as 0 items.
        # Fetch * so old + new schemas both work.
        items = (
            supabase.table("ground_template_items")
            .select("*")
            .in_("template_id", ids)
            .order("sort_order")
            .execute().data or []
        )

        # Normalize IDs because Supabase can return bigint as int/string depending on data/client.
        grouped = {str(tid): [] for tid in ids}

        master = get_item_master_details()
        by_code = {
            _clean_text(code).casefold(): data
            for code, data in master.items()
            if _clean_text(code)
        }

        for item in items:
            tid = str(item.get("template_id", ""))
            item_code = _clean_text(item.get("item_code"))

            # Description priority:
            # 1) Full description from Item Code master
            # 2) Description saved in template item (if that column exists)
            master_desc = _clean_text(
                by_code.get(item_code.casefold(), {}).get("description", "")
            )
            saved_desc = _clean_text(
                item.get("item_description")
                or item.get("description")
                or item.get("Item Description")
            )
            description = master_desc if len(master_desc) >= len(saved_desc) else saved_desc

            grouped.setdefault(tid, []).append({
                "id": item.get("id"),
                "template_id": item.get("template_id"),
                "item_code": item_code,
                "item_description": description,
                "default_qty": item.get("default_qty"),
                "sort_order": item.get("sort_order"),
            })

        return [
            {
                "id": row["id"],
                "name": row["template_name"],
                "line_items": grouped.get(str(row["id"]), []),
            }
            for row in heads
        ]

    except Exception as exc:
        st.error(f"Templates load nahi hue: {exc}")
        return []


def _template_lines(lines):
    # Qty and remarks are entered separately for each JMS, never inherited from a template.
    return [{"item_code": _clean_text(line.get("item_code")),
             "item_description": _clean_text(line.get("item_description")),
             "qty": None, "qty_manual": True, "remarks": ""}
            for line in lines if _clean_text(line.get("item_code")) or _clean_text(line.get("item_description"))]


def save_jms_template(name, lines, template_id=None):
    # Preserve template-manager Qty while cleaning code/description.
    clean_lines = []
    for line in lines:
        item_code = _clean_text(line.get("item_code"))
        item_description = _clean_text(line.get("item_description"))
        if item_code or item_description:
            clean_lines.append({
                "item_code": item_code,
                "item_description": item_description,
                "qty": line.get("qty"),
                "qty_manual": True,
                "remarks": "",
            })

    def _payload_for(tid, include_description=True):
        payload = []
        for pos, row in enumerate(clean_lines, 1):
            item = {
                "template_id": tid,
                "item_code": row["item_code"],
                "default_qty": row.get("qty") if row.get("qty") not in (None, "") else 0,
                "sort_order": pos,
            }
            if include_description:
                item["item_description"] = row["item_description"]
            payload.append(item)
        return payload

    def _insert_template_items(tid):
        payload = _payload_for(tid, include_description=True)
        if not payload:
            return []
        try:
            inserted = supabase.table("ground_template_items").insert(payload).execute()
            return inserted.data or []
        except Exception as first_exc:
            # Backward compatibility: older table may not have item_description.
            try:
                payload = _payload_for(tid, include_description=False)
                inserted = supabase.table("ground_template_items").insert(payload).execute()
                return inserted.data or []
            except Exception:
                raise first_exc

    if template_id:
        tid = int(template_id)
        old = (
            supabase.table("ground_template_items")
            .select("id")
            .eq("template_id", tid)
            .execute().data or []
        )

        # Insert replacement rows first, so failed insert leaves old items intact.
        inserted_rows = _insert_template_items(tid)
        new_ids = [row["id"] for row in inserted_rows if row.get("id") is not None]

        try:
            supabase.table("ground_template").update(
                {"template_name": name.strip()}
            ).eq("id", tid).execute()

            if old:
                old_ids = [x["id"] for x in old if x.get("id") not in new_ids]
                if old_ids:
                    supabase.table("ground_template_items").delete().in_("id", old_ids).execute()
        except Exception:
            if new_ids:
                supabase.table("ground_template_items").delete().in_("id", new_ids).execute()
            raise
    else:
        parent = supabase.table("ground_template").insert(
            {"template_name": name.strip()}
        ).execute()
        tid = parent.data[0]["id"]
        try:
            _insert_template_items(tid)
        except Exception:
            supabase.table("ground_template").delete().eq("id", tid).execute()
            raise

    fetch_jms_templates_cached.clear()
    return tid


def clear_jms_cache():
    fetch_site_data_cached.clear()
    fetch_jms_drafts_cached.clear()


# --- 3.1 DROPDOWN / ITEM MASTER HELPERS (needed by "Add New Item" inside JMS form) ---
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts


def get_item_master_details():
    mapping = {}
    # Keep the original JMS item list from "Item Code". Later tables may only
    # supply a longer description for an already listed code.
    primary_loaded = False
    for t_name in ("Item Code", "item_code", "item_master"):
        try:
            rows = supabase.table(t_name).select("*").execute().data or []
            for item in rows:
                code = _clean_text(item.get("item_code"))
                if not code or (primary_loaded and code not in mapping):
                    continue
                candidates = [_clean_text(item.get(column)) for column in
                              ("item_description", "Item Description", "description", "Description")]
                description = max(candidates, key=len, default="")[:80]
                if code not in mapping:
                    mapping[code] = {
                        "description": description,
                        "stn_status": str(item.get("stn_status", "Required") or "Required"),
                        "material_of": str(item.get("material_of", "Indus") or "Indus"),
                        "rate": item.get("rate"),
                    }
                elif len(description) > len(mapping[code]["description"]):
                    mapping[code]["description"] = description
            if mapping:
                primary_loaded = True
        except Exception:
            continue
    return mapping


# --- TEAM MASTER HELPERS ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_team_names_cached():
    try:
        rows = (supabase.table("dropdown_master")
                .select("option_value")
                .eq("category", "Team Name")
                .eq("is_active", True)
                .order("option_value")
                .execute().data or [])
        return [_clean_text(r.get("option_value")) for r in rows if _clean_text(r.get("option_value"))]
    except Exception:
        # Some older dropdown_master tables do not have is_active.
        try:
            rows = (supabase.table("dropdown_master")
                    .select("option_value")
                    .eq("category", "Team Name")
                    .order("option_value")
                    .execute().data or [])
            return [_clean_text(r.get("option_value")) for r in rows if _clean_text(r.get("option_value"))]
        except Exception:
            return []


def _internal_signature_text(team_name):
    """Internal-use signature text only; this is intentionally not a real signature."""
    name = _clean_text(team_name) or "TEAM"
    return f"{name} / Internal"


# =============================================================
# JMS BUILDER (identical logic to the Site Data page's JMS module)
# =============================================================
JMS_COMPANY_NAMES = {
    "VISPL": "Visiontech Infra Solutions",
    "BHAGYASHREE": "Bhagyashree Enterprises",
    "SAI TELE SERVICES": "Sai Tele Services",
}

def _clean_text(value):
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.lower() in ("nan", "none", "null") else value


def _readonly_detail_box(label, value):
    safe_label = html.escape(_clean_text(label))
    safe_value = html.escape(_clean_text(value) or "-")
    st.markdown(
        f"""
        <div style="margin-bottom:12px;">
            <div style="font-size:0.82rem;font-weight:900;color:#111827;letter-spacing:0.4px;margin-bottom:6px;">
                {safe_label}
            </div>
            <div style="background:#f1f5f9;border:1px solid #cbd5e1;border-radius:9px;
                        padding:12px 14px;min-height:46px;color:#000000;font-size:1rem;
                        font-weight:900;display:flex;align-items:center;box-sizing:border-box;">
                {safe_value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _lookup_blank_jms_site(site_id):
    """Fetch Site Name and Cluster from Excalation Matrix for Blank JMS."""
    clean_site_id = _clean_text(site_id)
    if not clean_site_id:
        return "", ""

    for table_name in ("Excalation Matrix", "Escalation Matrix"):
        try:
            result = (supabase.table(table_name).select("*")
                      .eq("Site ID", clean_site_id).limit(1).execute())
            if result.data:
                site_row = result.data[0]
                return (
                    _first_value(site_row, ["Site Name", "SITE NAME", "site_name"]),
                    _first_value(site_row, ["Cluster", "CLUSTER", "cluster"]),
                )
        except Exception:
            continue
    return "", ""

def _first_value(row, names, default=""):
    for name in names:
        value = _clean_text(row.get(name))
        if value:
            return value
    return default

def _normalized_po_value(row, aliases, default=""):
    normalized = {
        "".join(ch for ch in str(key).lower() if ch.isalnum()): value
        for key, value in row.items()
    }
    for alias in aliases:
        value = _clean_text(normalized.get("".join(ch for ch in alias.lower() if ch.isalnum())))
        if value:
            return value
    return default

def _detect_po_item_code(row):
    value = _normalized_po_value(row, [
        "Item Num", "Item Code", "ItemCode", "Item Number", "ItemNumber", "Item No",
        "ItemNo", "Oracle Item Code", "Material Code", "MaterialCode", "Item"
    ])
    if value:
        return value
    for key, raw in row.items():
        nk = "".join(ch for ch in str(key).lower() if ch.isalnum())
        if (("item" in nk and ("code" in nk or "number" in nk or nk.endswith("no")))
                or ("material" in nk and "code" in nk)):
            value = _clean_text(raw)
            if value:
                return value
    return ""

def _detect_po_qty(row):
    value = _normalized_po_value(row, [
        "PO Qty", "PO Quantity", "PO Ordered Qty", "Ordered Qty", "Order Qty",
        "Item Qty", "Quantity", "Qty", "VIS Qty", "User Qty"
    ], "")
    if value != "":
        return _number_value(value)
    for key, raw in row.items():
        nk = "".join(ch for ch in str(key).lower() if ch.isalnum())
        if (("po" in nk and ("qty" in nk or "quantity" in nk))
                or nk in ("orderedquantity", "orderedqty", "itemquantity", "itemqty")):
            value = _clean_text(raw)
            if value != "":
                return _number_value(value)
    return 0.0

@st.cache_data(ttl=300, show_spinner=False)
def _jms_item_description_code_map():
    return {
        " ".join(_clean_text(details.get("description")).lower().split()): code
        for code, details in get_item_master_details().items()
        if _clean_text(details.get("description"))
    }

def _code_from_item_master(description):
    wanted = " ".join(_clean_text(description).lower().split())
    if not wanted:
        return ""
    return _jms_item_description_code_map().get(wanted, "")

def _number_value(value):
    try:
        number = float(value)
        return 0.0 if math.isnan(number) else number
    except (TypeError, ValueError):
        return 0.0

def _split_list_field(raw):
    items = []
    normalized = str(raw if raw is not None else "").replace("|", ",")
    for x in normalized.split(","):
        x = x.strip()
        if x and x.lower() not in ("nan", "none", "null"):
            items.append(x)
    return items

def _jms_row_key(row_data):
    return f"{st.session_state.get('active_workspace', 'VISPL')}::{row_data.get('id')}"

def _fetch_po_lines_for_site(row_data):
    workspace = st.session_state.get("active_workspace", "VISPL")
    project_id = _clean_text(row_data.get("Project ID"))
    site_id = _clean_text(row_data.get("Site ID"))
    po_numbers = set(_split_list_field(row_data.get("PO No.", "")))
    candidates = []

    for field_name, field_value in (("Project Name", project_id), ("Site ID", site_id)):
        if not field_value:
            continue
        try:
            result = (supabase.table("po_working").select("*")
                      .eq("workspace", workspace).eq(field_name, field_value).execute())
            candidates.extend(result.data or [])
        except Exception:
            pass

    unique_rows, seen = [], set()
    for po_row in candidates:
        identity = po_row.get("id")
        if identity is None:
            identity = repr(sorted(po_row.items()))
        identity = str(identity)
        if identity not in seen:
            seen.add(identity)
            unique_rows.append(po_row)

    unique_rows.sort(key=lambda r: (
        _number_value(_normalized_po_value(r, ["Line Number", "Line Num", "Line No"], 999999)),
        _clean_text(r.get("id"))
    ))

    if po_numbers:
        matched = [r for r in unique_rows if _first_value(r, ["PO Number", "PO No.", "PO No", "po_number"]) in po_numbers]
        if matched:
            unique_rows = matched

    lines = []
    for po_row in unique_rows:
        item_code = _detect_po_item_code(po_row)
        description = _normalized_po_value(po_row, [
            "Item Description", "ItemDescription", "Description", "PO Item Description"
        ])
        qty = _detect_po_qty(po_row)
        if not item_code and description:
            item_code = _code_from_item_master(description)
        if item_code or description:
            lines.append({
                "item_code": item_code,
                "item_description": description,
                "qty": qty,
                "qty_manual": False,
                "remarks": "",
            })
    return lines

def _merge_saved_lines_with_po(saved_lines, po_lines):
    if not saved_lines:
        return po_lines
    po_by_desc = {_clean_text(x.get("item_description")).lower(): x for x in po_lines}
    po_by_code = {_clean_text(x.get("item_code")).lower(): x for x in po_lines if _clean_text(x.get("item_code"))}
    merged = []
    used_codes = set()
    for saved in saved_lines:
        row = dict(saved)
        code = _clean_text(row.get("item_code"))
        desc = _clean_text(row.get("item_description"))
        source = po_by_code.get(code.lower()) if code else None
        if source is None and desc:
            source = po_by_desc.get(desc.lower())
        if source:
            if not code:
                row["item_code"] = source.get("item_code", "")
            if not desc:
                row["item_description"] = source.get("item_description", "")
            if (not row.get("qty_manual") and _number_value(row.get("qty")) == 0
                    and _number_value(source.get("qty")) != 0):
                row["qty"] = source.get("qty", 0)
            used_codes.add(_clean_text(source.get("item_code")).lower())
        if not _clean_text(row.get("item_code")) and _clean_text(row.get("item_description")):
            row["item_code"] = _code_from_item_master(row.get("item_description"))
        merged.append(row)
    for po_line in po_lines:
        po_code = _clean_text(po_line.get("item_code")).lower()
        po_desc = _clean_text(po_line.get("item_description")).lower()
        already_present = po_code in used_codes if po_code else any(
            _clean_text(x.get("item_description")).lower() == po_desc for x in merged
        )
        if not already_present:
            merged.append(po_line)
    return merged

def _load_saved_jms(row_data):
    workspace = st.session_state.get("active_workspace", "VISPL")
    try:
        result = (supabase.table("jms_drafts").select("*")
                  .eq("workspace", workspace).eq("site_data_id", str(row_data.get("id")))
                  .limit(1).execute())
        return (result.data or [None])[0]
    except Exception:
        return None

def _save_jms_draft(row_data, circle, lines):
    workspace = st.session_state.get("active_workspace", "VISPL")
    payload = {
        "workspace": workspace,
        "site_data_id": str(row_data.get("id")),
        "project_id": _clean_text(row_data.get("Project ID")),
        "site_id": _clean_text(row_data.get("Site ID")),
        "site_name": _clean_text(row_data.get("Site Name")),
        "company_name": JMS_COMPANY_NAMES.get(workspace, workspace),
        "circle": circle,
        "cluster": _clean_text(row_data.get("Cluster")),
        "team_name": _clean_text(row_data.get("Team Name")),
        "line_items": lines,
        "updated_at": datetime.utcnow().isoformat(),
    }
    return supabase.table("jms_drafts").upsert(
        payload, on_conflict="workspace,site_data_id"
    ).execute()

def _build_jms_pdf(row_data, circle, lines):
    buffer = io.BytesIO()
    workspace = st.session_state.get("active_workspace", "VISPL")
    company = JMS_COMPANY_NAMES.get(workspace, workspace)
    page_w, page_h = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"JMS {_clean_text(row_data.get('Site ID'))}")

    def first_80_chars(value):
        return _clean_text(value)[:80]

    def fit_lines(text, max_width, font="Helvetica", size=4.2, max_lines=4):
        words = str(text).split()
        output, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            if stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                if current:
                    output.append(current)
                current = word
                if len(output) >= max_lines:
                    break
        if current and len(output) < max_lines:
            output.append(current)
        if len(output) == max_lines and len(" ".join(output).split()) < len(words):
            output[-1] = output[-1].rstrip(".") + "..."
        return output

    def draw_cell_text(text, x, y_top, width, height, size=4.2, bold=False, center=False, max_lines=4):
        font = "Helvetica-Bold" if bold else "Helvetica"
        rows = fit_lines(text, width - 4, font, size, max_lines)
        leading = size + 0.9
        total = len(rows) * leading
        y = y_top - (height - total) / 2 - size
        pdf.setFont(font, size)
        for line in rows:
            tx = x + width / 2 if center else x + 2
            if center:
                pdf.drawCentredString(tx, y, line)
            else:
                pdf.drawString(tx, y, line)
            y -= leading

    source_lines = list(lines)
    chunks = [source_lines[i:i + 30] for i in range(0, len(source_lines), 30)] or [[]]
    for page_no, chunk in enumerate(chunks, 1):
        margin = 10 * mm
        pdf.setLineWidth(0.8)
        pdf.rect(margin, margin, page_w - 2*margin, page_h - 2*margin)

        pdf.setFillColor(colors.HexColor("#3730a3"))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(page_w/2, page_h - 20*mm, company.upper())
        pdf.setFillColor(colors.HexColor("#334155"))
        pdf.setFont("Helvetica", 8.5)
        pdf_subtitle = "Joint Measurement Sheet - Circle: M&G" if row_data.get("_blank_jms") else "Joint Measurement Sheet"
        pdf.drawCentredString(page_w/2, page_h - 27*mm, pdf_subtitle)
        pdf.line(margin, page_h - 32*mm, page_w-margin, page_h - 32*mm)

        ix, iy, iw, ih = 16*mm, page_h - 52*mm, page_w - 32*mm, 14*mm
        pdf.setStrokeColor(colors.black); pdf.setLineWidth(0.55)
        pdf.rect(ix, iy, iw, ih); pdf.line(ix + iw/2, iy, ix + iw/2, iy + ih); pdf.line(ix, iy + ih/2, ix + iw, iy + ih/2)
        if row_data.get("_blank_jms"):
            info = [
                ("Project ID :-", _clean_text(row_data.get("Project ID")), ix, iy + ih, iw/2, ih/2),
                ("Site ID :-", _clean_text(row_data.get("Site ID")), ix+iw/2, iy+ih, iw/2, ih/2),
                ("Site Name :-", _clean_text(row_data.get("Site Name")), ix, iy+ih/2, iw/2, ih/2),
                ("Cluster :-", _clean_text(row_data.get("Cluster")), ix+iw/2, iy+ih/2, iw/2, ih/2),
            ]
        else:
            info = [
                ("Circle :-", circle or "Maharashtra", ix, iy + ih, iw/2, ih/2),
                ("Site ID :-", _clean_text(row_data.get("Site ID")), ix+iw/2, iy+ih, iw/2, ih/2),
                ("Site Name :-", _clean_text(row_data.get("Site Name")), ix, iy+ih/2, iw/2, ih/2),
                ("Project ID :-", _clean_text(row_data.get("Project ID")), ix+iw/2, iy+ih/2, iw/2, ih/2),
            ]
        for label, value, x, top, width, height in info:
            pdf.setFont("Helvetica-Bold", 6.2); pdf.drawString(x+3, top-height/2-2, label)
            pdf.setFont("Helvetica", 6.2); pdf.drawString(x+25*mm, top-height/2-2, value[:55])

        tx, table_top = 16*mm, iy - 4*mm
        widths = [10*mm, 33*mm, 91*mm, 18*mm, 26*mm]
        header_h, row_h = 8*mm, 5.8*mm
        headers = ["S.No.", "Item Code", "Item Description", "Qty as per site", "Remarks"]
        x = tx
        pdf.setFillColor(colors.HexColor("#e5e7eb")); pdf.rect(tx, table_top-header_h, sum(widths), header_h, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        for label, width in zip(headers, widths):
            pdf.rect(x, table_top-header_h, width, header_h, fill=0, stroke=1)
            draw_cell_text(label, x, table_top, width, header_h, size=5.4, bold=True, center=(label in ("S.No.", "Qty as per site")), max_lines=2)
            x += width

        for row_pos in range(30):
            y_top = table_top - header_h - row_pos*row_h
            line = chunk[row_pos] if row_pos < len(chunk) else {}
            global_no = (page_no - 1)*30 + row_pos + 1 if row_pos < len(chunk) else ""
            qty = _number_value(line.get("qty")) if line else 0
            qty_text = (str(int(qty)) if float(qty).is_integer() else f"{qty:g}") if line and qty != 0 else ""
            values = [global_no, _clean_text(line.get("item_code")), first_80_chars(line.get("item_description")), qty_text, _clean_text(line.get("remarks"))]
            x = tx
            for col_no, (value, width) in enumerate(zip(values, widths)):
                pdf.rect(x, y_top-row_h, width, row_h, fill=0, stroke=1)
                draw_cell_text(value, x, y_top, width, row_h,
                               size=5.65 if col_no in (1,2) else 5.25,
                               bold=col_no in (1,2), center=col_no in (0,3), max_lines=2)
                x += width

        sig_y, sig_h, gap = 12*mm, 27*mm, 6*mm
        sig_w = (iw-gap)/2
        pdf.rect(ix, sig_y, sig_w, sig_h); pdf.rect(ix+sig_w+gap, sig_y, sig_w, sig_h)

        # LEFT BOX: selected Team Name + clearly marked internal-use signature.
        team_name = _clean_text(row_data.get("Team Name"))
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawString(ix+5*mm, sig_y+19*mm, "Team Name :")
        pdf.setFont("Helvetica-Bold", 7.2)
        pdf.drawString(ix+5*mm, sig_y+15*mm, (team_name or "-")[:42])
        if team_name:
            pdf.setFillColor(colors.HexColor("#334155"))
            pdf.setFont("Helvetica-Oblique", 11)
            pdf.drawString(ix+5*mm, sig_y+8*mm, _internal_signature_text(team_name)[:38])
            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica", 5.2)
            pdf.drawString(ix+5*mm, sig_y+4*mm, "Internal use signature - not original signature")
            pdf.setFillColor(colors.black)

        # RIGHT BOX: existing auditor area unchanged.
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawString(ix+sig_w+gap+5*mm, sig_y+12*mm, "Auditor Name :-")
        pdf.drawString(ix+sig_w+gap+5*mm, sig_y+6*mm, "Audit Agency :-")
        pdf.showPage()

    pdf.save()
    return buffer.getvalue()

@st.cache_data(ttl=600, show_spinner=False)
def _cached_jms_pdf_bytes(workspace, site_data_id, updated_at, row_json, circle, lines_json):
    """Builds the JMS PDF straight from a saved draft, without opening the dialog.
    Cached on (workspace, site_data_id, updated_at) so it's instant after the first
    build and only regenerates when the draft is actually saved/changed again."""
    row_data = json.loads(row_json)
    lines = json.loads(lines_json)
    return _build_jms_pdf(row_data, circle, lines)


def _clear_jms_dialog():
    st.session_state.jmspage_open_row = None
    st.session_state.jmspage_loaded_key = None
    st.session_state.jmspage_last_pdf = None
    st.query_params.pop("jms_ctx", None)


# On newer Streamlit, the dismissal callback also handles X, Esc and outside click.
# Older versions that support dismissible=False must use the Close button.
_dialog_options = {"width": "large"}
_dialog_parameters = inspect.signature(st.dialog).parameters

# Keep Streamlit's normal top-right X / Esc / outside-click close behavior.
# We intentionally do NOT use on_dismiss because some Streamlit versions
# call it during widget reruns (e.g. template select), which used to close
# the popup unexpectedly.


@st.dialog("🧾 Create / Edit JMS", **_dialog_options)
def jms_dialog(row_data):
    active_key = _jms_row_key(row_data)
    is_blank_jms = bool(row_data.get("_blank_jms"))
    if st.session_state.jmspage_loaded_key != active_key:
        saved = None if is_blank_jms else _load_saved_jms(row_data)
        saved_lines = saved.get("line_items") if saved else None
        po_lines = [] if is_blank_jms else _fetch_po_lines_for_site(row_data)
        st.session_state.jmspage_lines = _merge_saved_lines_with_po(saved_lines, po_lines) if isinstance(saved_lines, list) else po_lines
        st.session_state.jmspage_loaded_key = active_key
        st.session_state.jmspage_last_pdf = None
        st.session_state.jmspage_add_gen += 1
        st.session_state[f"jmspage_circle_{active_key}"] = (
            "M&G" if is_blank_jms else (_clean_text(saved.get("circle")) if saved else "Maharashtra")
        )
        if is_blank_jms:
            st.session_state[f"jmspage_blank_project_{active_key}"] = _clean_text(row_data.get("Project ID"))
            st.session_state[f"jmspage_blank_site_id_{active_key}"] = _clean_text(row_data.get("Site ID"))
            st.session_state[f"jmspage_blank_team_{active_key}"] = _clean_text(row_data.get("Team Name"))

    workspace = st.session_state.get("active_workspace", "VISPL")
    company = JMS_COMPANY_NAMES.get(workspace, workspace)
    st.markdown(f"### {company}")
    if is_blank_jms:
        st.caption("Blank JMS — Project ID aur Site ID bhariye. Site Name aur Cluster auto aa jayenge.")
        detail_top1, detail_top2 = st.columns(2)
        with detail_top1:
            blank_project_id = st.text_input(
                "PROJECT ID",
                key=f"jmspage_blank_project_{active_key}",
                placeholder="Project ID enter karein"
            )
        with detail_top2:
            blank_site_id = st.text_input(
                "SITE ID",
                key=f"jmspage_blank_site_id_{active_key}",
                placeholder="Site ID enter karke Enter dabayein"
            )

        blank_site_name, blank_cluster = _lookup_blank_jms_site(blank_site_id)
        detail_bottom1, detail_bottom2 = st.columns(2)
        with detail_bottom1:
            _readonly_detail_box("SITE NAME", blank_site_name)
        with detail_bottom2:
            _readonly_detail_box("CLUSTER", blank_cluster)

        # Compact controls: Team Name + Template side-by-side
        team_names = fetch_team_names_cached()
        current_team = _clean_text(st.session_state.get(f"jmspage_blank_team_{active_key}"))
        team_options = [""] + team_names
        if current_team and current_team not in team_options:
            team_options.append(current_team)

        templates = fetch_jms_templates_cached(workspace)
        template_ids = {str(t["id"]): t for t in templates}
        template_choice_key = f"jmspage_template_choice_{active_key}"

        def _auto_load_selected_template():
            selected_template_id = st.session_state.get(template_choice_key, "")
            if selected_template_id and selected_template_id in template_ids:
                st.session_state.jmspage_lines = _template_lines(
                    template_ids[selected_template_id].get("line_items") or []
                )
                st.session_state.jmspage_last_pdf = None
                st.session_state.jmspage_add_gen += 1
            st.session_state.jmspage_open_row = row_data
            st.query_params["jms_ctx"] = "open"

        team_col, template_col = st.columns(2)
        with team_col:
            blank_team_name = st.selectbox(
                "TEAM NAME",
                team_options,
                index=team_options.index(current_team) if current_team in team_options else 0,
                format_func=lambda value: "-- Team Name --" if not value else value,
                key=f"jmspage_blank_team_{active_key}",
            )
        with template_col:
            chosen_id = st.selectbox(
                "TEMPLATE",
                [""] + list(template_ids),
                format_func=lambda tid: "-- Template --" if not tid else template_ids[tid]["name"],
                key=template_choice_key,
                on_change=_auto_load_selected_template,
            )

        if not team_names:
            st.warning("Team Name master me active teams nahi mile. dropdown_master check karein.")
        if chosen_id and not (template_ids[chosen_id].get("line_items") or []):
            st.warning(f"{template_ids[chosen_id]['name']} template me koi saved item nahi mila.")

        if _clean_text(blank_site_id):
            if blank_site_name or blank_cluster:
                st.success("✅ Site Name aur Cluster Excalation Matrix se mil gaye.")
            else:
                st.warning("Is Site ID ka data Excalation Matrix me nahi mila.")

        row_data["Project ID"] = _clean_text(blank_project_id)
        row_data["Site ID"] = _clean_text(blank_site_id)
        row_data["Site Name"] = _clean_text(blank_site_name)
        row_data["Cluster"] = _clean_text(blank_cluster)
        row_data["Team Name"] = _clean_text(blank_team_name)
        st.session_state.jmspage_open_row = row_data
    else:
        st.caption(f"Site: {_clean_text(row_data.get('Site ID'))} | Project: {_clean_text(row_data.get('Project ID'))} | PO: {_clean_text(row_data.get('PO No.')) or '-'}")
    if is_blank_jms:
        circle = "M&G"
        _readonly_detail_box("CIRCLE", circle)
    else:
        circle = st.text_input("Circle", key=f"jmspage_circle_{active_key}")

    if not is_blank_jms:
        if st.button("🔄 Reload Item Code & Qty from PO", use_container_width=True, key=f"jmspage_reload_po_{active_key}"):
            fresh_po_lines = _fetch_po_lines_for_site(row_data)
            if fresh_po_lines:
                st.session_state.jmspage_lines = _merge_saved_lines_with_po(st.session_state.jmspage_lines, fresh_po_lines)
                st.session_state.jmspage_last_pdf = None
                st.success("PO se Item Code aur Qty reload ho gaye.")
                st.rerun()
            else:
                st.warning("Is Project ID / Site ID ke against po_working me koi line nahi mili.")

    st.markdown("#### Manual JMS Line Items" if is_blank_jms else "#### PO / Saved JMS Line Items")
    if st.session_state.jmspage_lines:
        editor_df = pd.DataFrame(st.session_state.jmspage_lines)
        for col, default in (("item_code", ""), ("item_description", ""), ("qty", 0.0), ("remarks", "")):
            if col not in editor_df.columns:
                editor_df[col] = default
        editor_df["qty"] = editor_df["qty"].apply(
            lambda value: "" if _number_value(value) == 0 else (
                str(int(_number_value(value))) if _number_value(value).is_integer()
                else f"{_number_value(value):g}"
            )
        )
        edited = st.data_editor(
            editor_df[["item_code", "item_description", "qty", "remarks"]],
            hide_index=True, use_container_width=True, num_rows="dynamic",
            disabled=[],
            column_config={
                "item_code": st.column_config.TextColumn("Item Code"),
                "item_description": st.column_config.TextColumn("Item Description", width="large"),
                "qty": st.column_config.TextColumn("Qty", help="Qty editable hai; 0 ya blank dono blank rahenge."),
                "remarks": st.column_config.TextColumn("Remarks", width="medium"),
            }, key=f"jmspage_editor_{active_key}_{st.session_state.jmspage_add_gen}")
        edited_records = edited.to_dict("records")
        for item in edited_records:
            raw_qty = _clean_text(item.get("qty"))
            if raw_qty:
                try:
                    parsed_qty = float(raw_qty.replace(",", ""))
                    item["qty"] = None if parsed_qty == 0 else parsed_qty
                except ValueError:
                    item["qty"] = None
            else:
                item["qty"] = None
            item["qty_manual"] = True
        st.session_state.jmspage_lines = edited_records
    else:
        if is_blank_jms:
            st.info("Template select karein ya neeche item add karein. Qty baad me bhar sakte hain.")
        else:
            st.info("Is site ke PO me item lines nahi mili. Neeche se new item add kijiye.")

    # Template selection for Blank JMS is already shown compactly beside Team Name.
    # For normal JMS keep a simple compact template dropdown here.
    if not is_blank_jms:
        templates = fetch_jms_templates_cached(workspace)
        template_ids = {str(t["id"]): t for t in templates}
        template_choice_key = f"jmspage_template_choice_{active_key}"

        def _auto_load_selected_template_normal():
            selected_template_id = st.session_state.get(template_choice_key, "")
            if selected_template_id and selected_template_id in template_ids:
                st.session_state.jmspage_lines = _template_lines(
                    template_ids[selected_template_id].get("line_items") or []
                )
                st.session_state.jmspage_last_pdf = None
                st.session_state.jmspage_add_gen += 1
            st.session_state.jmspage_open_row = row_data
            st.query_params["jms_ctx"] = "open"

        chosen_id = st.selectbox(
            "TEMPLATE",
            [""] + list(template_ids),
            format_func=lambda tid: "-- Template --" if not tid else template_ids[tid]["name"],
            key=template_choice_key,
            on_change=_auto_load_selected_template_normal,
        )



    st.markdown("#### Add New Item")
    master = get_item_master_details()
    gen = st.session_state.jmspage_add_gen
    add_code = st.selectbox(
        "Item Code", [""] + sorted(master.keys()),
        format_func=lambda code: "-- Select item --" if not code else f"{code} — {master[code]['description']}",
        key=f"jmspage_add_code_{active_key}_{gen}") if master else st.text_input("Item Code", key=f"jmspage_add_code_{active_key}_{gen}")
    add_desc = master.get(add_code, {}).get("description", "") if master else st.text_input("Item Description", key=f"jmspage_add_desc_{active_key}_{gen}")
    if master and add_code:
        st.caption(add_desc)
    add_qty_raw = st.text_input("Qty", value="", placeholder="Blank = 0", key=f"jmspage_add_qty_{active_key}_{gen}")
    if st.button("➕ Add New Item", use_container_width=True, key=f"jmspage_add_btn_{active_key}", disabled=not _clean_text(add_code)):
        add_qty = _number_value(add_qty_raw.replace(",", "")) if _clean_text(add_qty_raw) else None
        st.session_state.jmspage_lines.append({"item_code": add_code, "item_description": add_desc, "qty": None if add_qty == 0 else add_qty, "qty_manual": True, "remarks": ""})
        st.session_state.jmspage_add_gen += 1
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save JMS", type="primary", use_container_width=True, key=f"jmspage_save_{active_key}"):
            clean_lines = [x for x in st.session_state.jmspage_lines if _clean_text(x.get("item_code")) or _clean_text(x.get("item_description"))]
            if not clean_lines:
                st.error("Kam se kam ek item line required hai.")
            elif is_blank_jms and not _clean_text(row_data.get("Team Name")):
                st.error("Blank JMS ke liye Team Name select karein.")
            else:
                try:
                    _save_jms_draft(row_data, circle, clean_lines)
                    st.session_state.jmspage_lines = clean_lines
                    st.session_state.jmspage_last_pdf = _build_jms_pdf(row_data, circle, clean_lines)
                    clear_jms_cache()
                    st.success("JMS save ho gayi. Ab PDF download kar sakte hain.")
                except Exception as exc:
                    st.error(f"JMS save nahi hui: {exc}")
    with c2:
        if st.button("✖ Close", use_container_width=True, key=f"jmspage_close_{active_key}"):
            _clear_jms_dialog()
            st.rerun()

    if st.session_state.get("jmspage_last_pdf"):
        safe_site = _clean_text(row_data.get("Site ID")) or "Site"
        st.download_button("⬇️ Download JMS PDF", st.session_state.jmspage_last_pdf,
                           file_name=f"JMS_{safe_site}.pdf", mime="application/pdf",
                           use_container_width=True, key=f"jmspage_download_{active_key}")


# --- TOP BANNER ---
active_ws_display = st.session_state.get('site_active_company', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #f59e0b 0%, #ef4444 50%, #d946ef 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.2rem; text-transform: uppercase;">
            🧾 JMS — {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

@st.dialog("🧩 JMS Template Manager", width="large")
def template_manager_dialog():
    workspace = st.session_state.get("active_workspace", "VISPL")
    templates = fetch_jms_templates_cached(workspace)
    by_id = {str(t["id"]): t for t in templates}

    st.markdown("""
    <div style="padding:14px 18px;border-radius:14px;
                background:linear-gradient(135deg,#eef2ff,#f5f3ff);
                border:1px solid #c7d2fe;margin-bottom:14px;">
        <div style="font-size:1.15rem;font-weight:900;color:#312e81;">Create / Update JMS Template</div>
        <div style="font-size:.85rem;color:#64748b;margin-top:3px;">
            Template select karein, Item Code add karein aur Save / Update karein.
        </div>
    </div>
    """, unsafe_allow_html=True)

    selection = st.selectbox(
        "SELECT TEMPLATE",
        ["NEW"] + list(by_id),
        format_func=lambda tid: "➕ Create New Template" if tid == "NEW" else by_id[tid]["name"],
        key=f"jmspage_popup_choice_{workspace}",
    )

    identity = (workspace, selection)
    if st.session_state.get("jmspage_popup_loaded") != identity:
        selected = by_id.get(selection, {})
        st.session_state["jmspage_popup_name"] = selected.get("name", "")
        rows = []
        for item in (selected.get("line_items") or []):
            qty = item.get("default_qty")
            if qty in (None, 0, 0.0, "0", "0.0"):
                qty = ""
            rows.append({
                "item_code": _clean_text(item.get("item_code")),
                "item_description": _clean_text(item.get("item_description")),
                "qty": qty,
            })
        st.session_state["jmspage_popup_items"] = rows
        st.session_state["jmspage_popup_loaded"] = identity
        st.session_state["jmspage_popup_gen"] = st.session_state.get("jmspage_popup_gen", 0) + 1

    template_name = st.text_input(
        "TEMPLATE NAME",
        key="jmspage_popup_name",
        placeholder="Example: Battery Bank",
    )

    item_master = get_item_master_details()
    current_rows = st.session_state.get("jmspage_popup_items", [])
    gen = st.session_state.get("jmspage_popup_gen", 0)

    st.markdown("##### 📦 Template Items")
    frame = pd.DataFrame(current_rows, columns=["item_code", "item_description", "qty"]).fillna("")
    code_options = sorted(set(item_master.keys()) | {
        _clean_text(r.get("item_code")) for r in current_rows if _clean_text(r.get("item_code"))
    })

    changed = st.data_editor(
        frame,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "item_code": st.column_config.SelectboxColumn(
                "Item Code", options=code_options, width="medium"
            ),
            "item_description": st.column_config.TextColumn("Description", width="large"),
            "qty": st.column_config.TextColumn("Qty", width="small"),
        },
        key=f"jmspage_popup_editor_{workspace}_{selection}_{gen}",
    )

    changed_rows = changed.to_dict("records")
    master_by_code = {c.casefold(): d for c, d in item_master.items()}
    for row in changed_rows:
        code_value = _clean_text(row.get("item_code"))
        if code_value:
            match = master_by_code.get(code_value.casefold())
            if match and not _clean_text(row.get("item_description")):
                row["item_description"] = _clean_text(match.get("description"))

    st.session_state["jmspage_popup_items"] = changed_rows

    add1, add2 = st.columns([4, 1])
    with add1:
        chosen_code = st.selectbox(
            "ADD ITEM FROM MASTER",
            [""] + sorted(item_master.keys()),
            format_func=lambda c: "-- Item Code select karein --" if not c
            else f"{c} — {item_master[c]['description']}",
            key=f"jmspage_popup_add_code_{workspace}_{selection}_{gen}",
        )
    with add2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        add_clicked = st.button(
            "➕ Add Item", type="primary", use_container_width=True,
            disabled=not chosen_code,
            key=f"jmspage_popup_add_btn_{workspace}_{selection}_{gen}",
        )

    if add_clicked:
        rows = changed.to_dict("records")
        present = {_clean_text(r.get("item_code")).casefold() for r in rows}
        if chosen_code.casefold() in present:
            st.warning("Ye Item Code template me already hai.")
        else:
            rows.append({
                "item_code": chosen_code,
                "item_description": item_master[chosen_code]["description"],
                "qty": "",
            })
            st.session_state["jmspage_popup_items"] = rows
            st.session_state["jmspage_popup_gen"] = gen + 1
            st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        save_new = st.button(
            "💾 Save New Template", type="primary", use_container_width=True,
            key=f"jmspage_popup_save_new_{workspace}",
        )
    with c2:
        update_existing = st.button(
            "🔄 Update Template", use_container_width=True,
            disabled=(selection == "NEW"),
            key=f"jmspage_popup_update_{workspace}",
        )
    with c3:
        close_popup = st.button(
            "✖ Close", use_container_width=True,
            key=f"jmspage_popup_close_{workspace}",
        )

    if close_popup:
        st.session_state["jmspage_template_popup_open"] = False
        st.rerun()

    if save_new or update_existing:
        clean_name = _clean_text(template_name)
        clean_rows = []
        for row in changed.to_dict("records"):
            item_code = _clean_text(row.get("item_code"))
            item_description = _clean_text(row.get("item_description"))
            raw_qty = _clean_text(row.get("qty"))
            qty = None
            if raw_qty:
                try:
                    qty = float(raw_qty.replace(",", ""))
                except ValueError:
                    st.error(f"Qty valid number hona chahiye: {raw_qty}")
                    return
            if item_code or item_description:
                clean_rows.append({
                    "item_code": item_code,
                    "item_description": item_description,
                    "qty": qty,
                    "qty_manual": True,
                    "remarks": "",
                })

        if not clean_name:
            st.error("Template Name bhariye.")
            return
        if not clean_rows:
            st.error("Kam se kam ek item add karein.")
            return

        try:
            if save_new:
                duplicate = any(
                    t["name"].strip().casefold() == clean_name.casefold()
                    for t in templates
                )
                if duplicate:
                    st.error("Is naam ka template already hai. Use select karke Update Template karein.")
                    return
                save_jms_template(clean_name, clean_rows)
                st.success(f"✅ {clean_name} template save ho gaya.")
            else:
                save_jms_template(clean_name, clean_rows, int(selection))
                st.success(f"✅ {clean_name} template update ho gaya.")

            fetch_jms_templates_cached.clear()
            st.session_state["jmspage_popup_loaded"] = None
            st.rerun()
        except Exception as exc:
            st.error(f"Template save/update nahi hua: {exc}")




col_title, col_blank, col_template, col_ref = st.columns([3.6, 1.15, 1.15, 1])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>Joint Measurement Sheets</h2>", unsafe_allow_html=True)
with col_blank:
    if st.button("➕ Blank JMS", type="primary", use_container_width=True):
        blank_id = f"blank-{uuid4().hex}"
        st.session_state.jmspage_open_row = {
            "id": blank_id,
            "_blank_jms": True,
            "Site Name": "",
            "Project ID": "",
            "Site ID": "",
            "Cluster": "",
            "PO No.": "",
            "Team Name": "",
        }
        st.session_state.jmspage_loaded_key = None
        st.session_state.jmspage_last_pdf = None
        st.query_params["jms_ctx"] = "open"
        st.rerun()
with col_template:
    if st.button("🧩 Template", type="primary", use_container_width=True):
        st.session_state["jmspage_template_popup_open"] = True
        st.rerun()
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        clear_jms_cache()
        st.rerun()

if st.session_state.get("jmspage_template_popup_open", False):
    template_manager_dialog()

# --- TEMPLATE MANAGER POPUP ---
st.markdown("<br>", unsafe_allow_html=True)

# --- GENERATED JMS HISTORY / DOWNLOAD ---
active_ws = st.session_state.get('active_workspace', 'VISPL')
jms_drafts_map = fetch_jms_drafts_cached(active_ws)

# Keep the JMS dialog open across reruns while editing/saving.
if st.session_state.get("jmspage_open_row") is not None:
    jms_dialog(st.session_state.jmspage_open_row)

history_rows = list(jms_drafts_map.values())
if history_rows:
    history_df = pd.DataFrame(history_rows)
    for col in ("site_data_id", "project_id", "site_id", "site_name", "cluster", "team_name", "circle", "updated_at", "line_items"):
        if col not in history_df.columns:
            history_df[col] = "" if col != "line_items" else [[] for _ in range(len(history_df))]
    history_df["updated_at_dt"] = pd.to_datetime(history_df["updated_at"], errors="coerce")
    history_df = history_df.sort_values("updated_at_dt", ascending=False).drop(columns=["updated_at_dt"]).reset_index(drop=True)
else:
    history_df = pd.DataFrame(columns=["site_data_id", "project_id", "site_id", "site_name", "cluster", "team_name", "circle", "updated_at", "line_items"])

# KPI is now intentionally about GENERATED JMS only; old site-data register is removed.
kpi_created = len(history_df)
kpi_blank = int(history_df["site_data_id"].astype(str).str.startswith("blank-").sum()) if not history_df.empty else 0
kpi_normal = max(kpi_created - kpi_blank, 0)
kpi_teams = history_df["team_name"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA}).dropna().nunique() if not history_df.empty else 0

def _kpi(icon, label, value, foot, accent, soft, value_cls="", extra=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div>{extra}</div>'
    )

st.markdown(
    '<div class="lux-kpi-grid">'
    + _kpi("🧾", "Generated JMS", f"{kpi_created:,}", "Saved JMS in this company", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
    + _kpi("📝", "Blank JMS", f"{kpi_blank:,}", "Created from Blank JMS", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb")
    + _kpi("🏗️", "Site JMS", f"{kpi_normal:,}", "Created from site records", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5", "green")
    + _kpi("👷", "Teams", f"{kpi_teams:,}", "Teams used in saved JMS", "linear-gradient(90deg,#ec4899,#a855f7)", "#fdf2f8")
    + '</div>',
    unsafe_allow_html=True,
)

# Search only the JMS already generated/saved.
search_query = st_keyup(
    "Search Generated JMS",
    placeholder="🔍 Search Generated JMS by Project ID / Site ID / Site Name / Cluster / Team Name...",
    label_visibility="collapsed",
    key="jms_history_search",
)
if search_query and not history_df.empty:
    search_cols = [c for c in ["project_id", "site_id", "site_name", "cluster", "team_name", "circle"] if c in history_df.columns]
    mask = history_df[search_cols].astype(str).apply(
        lambda x: x.str.contains(search_query, case=False, na=False)
    ).any(axis=1)
    history_df = history_df[mask].reset_index(drop=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

_MUTED = "<div class='slux-cell'><span class='slux-muted'>—</span></div>"

def _txt(v, extra_cls=""):
    value = _clean_text(v)
    if not value:
        return _MUTED
    escaped = html.escape(value)
    return f"<div class='slux-cell {extra_cls}' title='{escaped}'>{escaped}</div>"

def _chip(v, extra_cls=""):
    value = _clean_text(v)
    if not value:
        return _MUTED
    escaped = html.escape(value)
    return f"<div class='slux-cell' title='{escaped}'><span class='slux-chip {extra_cls}'>{escaped}</span></div>"

def _pill(v):
    value = _clean_text(v)
    if not value:
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-pill'>{html.escape(value)}</span></div>"

def _history_date(value):
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        return "-" if pd.isna(parsed) else parsed.strftime("%d/%m/%Y %I:%M %p")
    except Exception:
        return _clean_text(value) or "-"

# No old site_data table here. Only saved/generated JMS detail + direct PDF download.
COL_RATIOS = [0.5, 0.55, 1.15, 1.1, 1.55, 1.0, 1.25, 1.15, 1.2]
COL_LABELS = ["#", "PDF", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "TEAM NAME", "CIRCLE", "UPDATED"]

if history_df.empty:
    st.markdown(
        '<div class="slux-empty"><div>🧾</div>'
        + ("No generated JMS matches your search." if search_query else "Abhi tak koi JMS save nahi hui.")
        + '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">🧾 Generated JMS History<span>saved JMS detail + direct download</span></div>'
        f'<div class="slux-badge">{len(history_df):,} JMS</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="jms_table_wrap"):
        with st.container(key="jmshead"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                h_col.markdown(f"<div class='slux-th{' c' if i < 2 else ''}'>{label}</div>", unsafe_allow_html=True)

        for pos, (_, draft_row) in enumerate(history_df.iterrows(), 1):
            draft = draft_row.to_dict()
            draft_id = _clean_text(draft.get("site_data_id")) or f"draft-{pos}"
            safe_key = "".join(ch if ch.isalnum() else "_" for ch in draft_id)
            parity = "odd" if pos % 2 else "even"

            with st.container(key=f"jmsrow_{parity}_history_{safe_key}_{pos}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")
                rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos}</span></div>", unsafe_allow_html=True)

                # Rebuild exactly from the saved JMS draft, including Blank JMS Team Name/Cluster.
                pdf_row = {
                    "id": draft_id,
                    "_blank_jms": str(draft_id).startswith("blank-"),
                    "Project ID": _clean_text(draft.get("project_id")),
                    "Site ID": _clean_text(draft.get("site_id")),
                    "Site Name": _clean_text(draft.get("site_name")),
                    "Cluster": _clean_text(draft.get("cluster")),
                    "Team Name": _clean_text(draft.get("team_name")),
                    "PO No.": "",
                }
                draft_circle = _clean_text(draft.get("circle")) or ("M&G" if pdf_row["_blank_jms"] else "Maharashtra")
                draft_lines = draft.get("line_items") if isinstance(draft.get("line_items"), list) else []
                updated_at = _clean_text(draft.get("updated_at"))

                with rcols[1]:
                    try:
                        pdf_bytes = _cached_jms_pdf_bytes(
                            active_ws, draft_id, updated_at,
                            json.dumps(pdf_row, default=str), draft_circle,
                            json.dumps(draft_lines, default=str),
                        )
                        safe_site = _clean_text(draft.get("site_id")) or "Site"
                        st.download_button(
                            "⬇️", data=pdf_bytes, file_name=f"JMS_{safe_site}.pdf",
                            mime="application/pdf", key=f"jmshistorydl_{safe_key}_{pos}",
                            help="Download JMS PDF",
                        )
                    except Exception as exc:
                        st.caption("PDF error")

                rcols[2].markdown(_chip(draft.get("project_id"), "proj"), unsafe_allow_html=True)
                rcols[3].markdown(_chip(draft.get("site_id")), unsafe_allow_html=True)
                rcols[4].markdown(_txt(draft.get("site_name"), "slux-strong"), unsafe_allow_html=True)
                rcols[5].markdown(_pill(draft.get("cluster")), unsafe_allow_html=True)
                rcols[6].markdown(_txt(draft.get("team_name"), "slux-strong"), unsafe_allow_html=True)
                rcols[7].markdown(_pill(draft_circle), unsafe_allow_html=True)
                rcols[8].markdown(_txt(_history_date(updated_at)), unsafe_allow_html=True)

    st.markdown(
        '<div class="slux-foot">'
        f'<div>{len(history_df):,} generated JMS<small>Newest saved JMS first</small></div>'
        '<div class="slux-foot-amts"><span class="slux-foot-badge">Direct PDF Download</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
