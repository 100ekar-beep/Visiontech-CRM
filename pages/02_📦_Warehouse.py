import streamlit as st
import pandas as pd
import math
import io
import html
import requests # <--- NEW: Added requests for WhatsApp API
import smtplib  # <--- NEW: For Email Sending
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from st_keyup import st_keyup  # <--- NEW: For live search-as-you-type (Item Code/Description)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Warehouse Hub", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'wh_mat_count' not in st.session_state:
    st.session_state.wh_mat_count = 1

# --- MOBILE VIEW TOGGLE STATE ---
if 'wh_view_mode' not in st.session_state:
    st.session_state.wh_view_mode = "table"

# --- 2. ✨ LAVISH LIGHT THEME CSS (Quotation / Site Data / Invoice jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Top Action Buttons */
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
    .page-count { text-align: center; font-size: 1rem; font-weight: 800; color: #4338ca; margin-top: 10px; }
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

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
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important; font-weight: 700 !important; -webkit-text-fill-color: #000000 !important;
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
    .lux-kpi-value.red { color: #dc2626; }
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
    .st-key-wh_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-wh_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-wh_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-wh_table_wrap div[class*="st-key-whhead"],
    .st-key-wh_table_wrap div[class*="st-key-whrow_"] { min-width: 3000px !important; }
    .st-key-wh_table_wrap [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-wh_table_wrap [data-testid="stColumn"], .st-key-wh_table_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header */
    div[class*="st-key-whhead"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-whhead"] [data-testid="stColumn"], div[class*="st-key-whhead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-whrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-whrow_odd"] { background: #fafaff; }
    div[class*="st-key-whrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-whrow_"] p { margin: 0 !important; }

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
    .slux-chip.item { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .slux-qty {
        display: inline-block; min-width: 38px; text-align: center; padding: 4px 10px; border-radius: 8px;
        background: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; font-weight: 900; font-size: .85rem;
    }

    /* Status pills */
    .status-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 11px; border-radius: 999px; border: 1px solid transparent;
        font-size: .7rem; font-weight: 800; letter-spacing: .4px; white-space: nowrap;
    }
    .status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
    .status-green  { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
    .status-blue   { background: #dbeafe; color: #1d4ed8; border-color: #bfdbfe; }
    .status-yellow { background: #fef9c3; color: #a16207; border-color: #fde68a; }
    .status-red    { background: #fee2e2; color: #b91c1c; border-color: #fecaca; }
    .status-grey   { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }

    /* Single ⚙️ action button at row start (Site Data jaisa) */
    div[class*="st-key-whpop_"] button {
        width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    div[class*="st-key-whpop_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    div[class*="st-key-whpop_"] button p, div[class*="st-key-whpop_"] button span { color: #1e293b !important; }
    div[class*="st-key-whpop_"] button svg { display: none !important; }
    .st-key-wh_del_yes button { background: linear-gradient(90deg, #ef4444, #dc2626) !important; box-shadow: 0 4px 10px -2px rgba(239,68,68,.5) !important; }
    .st-key-wh_del_no button { background: #f1f5f9 !important; box-shadow: none !important; }
    .st-key-wh_del_no button p { color: #334155 !important; }

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
    .wh-card-title { font-size: 1.05rem; font-weight: 800; color: #312e81; margin-bottom: 2px; }
    .wh-card-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
    .wh-card-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; gap: 10px; }
    .wh-card-row:last-child { border-bottom: none; }
    .wh-card-label { color: #64748b; font-weight: 700; white-space: nowrap; text-transform: uppercase; font-size: .75rem; }
    .wh-card-value { color: #0f172a; font-weight: 600; text-align: right; }

    /* ================= ITEM CODE LIVE-SEARCH MATCH CAPTION ================= */
    .item-match-count { color: #4338ca; font-size: 0.78rem; font-weight: 700; margin: 2px 0 4px 0; }
    .item-no-match { color: #dc2626; font-size: 0.78rem; font-weight: 700; margin: 2px 0 4px 0; }
    .wh-item-label { color: #334155; font-size: 0.85rem; margin-top: 15px; margin-bottom: 5px; font-weight: 800; }
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

# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: CACHED DATA FETCHERS ---
# ⚠️ FIX (isi tarah ka issue jaise Site Data Hub mein tha): pehle
# get_all_dropdowns(), get_site_projects() aur main warehouse_data fetch
# — teeno BINA kisi caching ke the. Streamlit dialog ke andar HAR
# keystroke/click par poora script phir se chalta hai, matlab har type
# karne par, har dropdown select karne par, ye teeno poori tables Supabase
# se dobara download kar rahe the — yahi Cached Egress ko bahut zyada
# kha raha tha. Ab inhe 30s ke liye cache kiya gaya hai, aur kisi bhi
# insert/update/delete se pehle .clear() call karke turant fresh data
# le liya jaata hai.
# -------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

@st.cache_data(ttl=30, show_spinner=False)
def get_site_projects(workspace):
    try:
        res = supabase.table("site_data").select("*").eq("workspace", workspace).execute()
        return res.data if res.data else []
    except Exception as e:
        st.toast(f"Database Error: {e}", icon="❌")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def fetch_warehouse_data_cached(workspace):
    try:
        response = supabase.table("warehouse_data").select("*").eq("workspace", workspace).execute()
        return response.data if response.data else []
    except Exception:
        return []

def clear_warehouse_caches():
    """Call this right before st.rerun() after any insert/update/delete on warehouse_data."""
    fetch_warehouse_data_cached.clear()

# --- NEW: LIVE ITEM MASTER SEARCH (matches Item Code OR Item Description, partial word) ---
# Cached too (short TTL) since the same partial search term is often retyped/reused while
# the user is narrowing down an item — avoids repeated identical queries hitting Supabase.
@st.cache_data(ttl=60, show_spinner=False)
def search_item_master(term, limit=25):
    """
    Search the Item Code master table for any row where item_code OR item_description
    contains the given term (case-insensitive, partial match anywhere in the string).
    Tries both possible table name variants used elsewhere in the app.
    """
    term_clean = str(term).strip()
    if not term_clean:
        return []
    # Escape characters that could break the PostgREST filter mini-language
    safe_term = term_clean.replace(",", " ").replace("(", " ").replace(")", " ")
    for t_name in ["Item Code", "item_code"]:
        try:
            res = (
                supabase.table(t_name)
                .select("*")
                .or_(f"item_code.ilike.*{safe_term}*,item_description.ilike.*{safe_term}*")
                .limit(limit)
                .execute()
            )
            if res.data:
                return res.data
        except Exception:
            continue
    return []

def render_item_code_search(search_key, match_key, stn_status_opts, on_select_keys):
    """
    Shared UI block: live search box + matching-items dropdown (Code — Description).

    Behaviour:
    - If the typed text is an EXACT (100%) match to exactly one item's Item Code,
      that item is auto-selected immediately — no extra dropdown click needed.
    - Otherwise (partial text, multiple matches, or matches only by description),
      a dropdown of "CODE — DESCRIPTION" options is shown so the user can pick.

    `on_select_keys` = dict with keys: 'final_code', 'idesc', 'stn' -> the session_state
    keys that should be updated when an item is selected (auto or manual).
    Returns the currently selected item code (string, may be empty).
    """
    search_val = st_keyup(
        "ITEM CODE * (type code or description to search)",
        placeholder="e.g. 64B9E0 or SMPS...",
        key=search_key,
    )

    if search_val and search_val.strip():
        matches = search_item_master(search_val)
        if matches:
            term_clean = search_val.strip().lower()
            exact_matches = [m for m in matches if str(m.get("item_code", "")).strip().lower() == term_clean]

            if len(exact_matches) == 1:
                # --- 100% EXACT MATCH: auto-select directly, no dropdown needed ---
                m = exact_matches[0]
                sel_code = str(m.get("item_code", "")).strip()
                sel_desc = str(m.get("item_description", "")).strip()
                sel_stn = str(m.get("stn_status", "Required")).strip()
                st.session_state[on_select_keys["final_code"]] = sel_code
                st.session_state[on_select_keys["idesc"]] = sel_desc
                if sel_stn in stn_status_opts:
                    st.session_state[on_select_keys["stn"]] = sel_stn
                st.markdown(
                    f"<div class='item-match-count'>✅ Exact match — auto-selected: <b>{sel_code}</b></div>",
                    unsafe_allow_html=True,
                )
            else:
                # --- Partial / multiple matches: show dropdown to pick manually ---
                match_opts = ["🔍 Select matching item..."]
                match_lookup = {}
                for m in matches:
                    m_code = str(m.get("item_code", "")).strip()
                    m_desc = str(m.get("item_description", "")).strip()
                    m_stn = str(m.get("stn_status", "Required")).strip()
                    label = f"{m_code} — {m_desc}" if m_desc else m_code
                    if label not in match_lookup:
                        match_opts.append(label)
                        match_lookup[label] = (m_code, m_desc, m_stn)

                st.markdown(f"<div class='item-match-count'>📋 {len(match_lookup)} matching item(s) found — select one below</div>", unsafe_allow_html=True)
                chosen = st.selectbox(
                    "Matches", match_opts, key=match_key, label_visibility="collapsed"
                )
                if chosen != "🔍 Select matching item...":
                    sel_code, sel_desc, sel_stn = match_lookup[chosen]
                    st.session_state[on_select_keys["final_code"]] = sel_code
                    st.session_state[on_select_keys["idesc"]] = sel_desc
                    if sel_stn in stn_status_opts:
                        st.session_state[on_select_keys["stn"]] = sel_stn
        else:
            st.markdown("<div class='item-no-match'>⚠️ Koi matching item code/description nahi mila.</div>", unsafe_allow_html=True)

    return st.session_state.get(on_select_keys["final_code"], "")

# --- 3.5 WAREHOUSE MATERIAL ADD DIALOG (POP-UP) ---
@st.dialog("📦 Add New Warehouse Material", width="large")
def add_warehouse_material_dialog():
    st.caption("Manage transaction items and asset movements against Project IDs")
    
    all_dd = get_all_dropdowns()
    site_records = get_site_projects(st.session_state.get('active_workspace', 'VISPL'))
    
    unique_proj_ids = []
    for r in site_records:
        pid, wh_mat = "", ""
        for k, v in r.items():
            k_clean = str(k).strip().lower().replace("_", " ")
            if k_clean == "project id":
                pid = v
            elif k_clean == "wh material":
                wh_mat = v
                
        if str(pid).strip() and str(wh_mat).strip().lower() == "required":
            unique_proj_ids.append(str(pid).strip())
            
    unique_proj_ids = list(set(unique_proj_ids))
    unique_proj_ids.sort()
    
    if not unique_proj_ids:
        st.toast("Koi bhi Project ID 'WH Material = Required' status ke sath nahi mili!", icon="ℹ️")
        
    proj_id_opts = ["Select Project ID"] + unique_proj_ids

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            proj_id = st.selectbox("PROJECT ID *", proj_id_opts)
            
        site_id_val, site_name_val, cluster_val, team_val = "", "", "", ""
        if proj_id != "Select Project ID":
            for r in site_records:
                curr_pid = ""
                for k, v in r.items():
                    if str(k).strip().lower().replace("_", " ") == "project id":
                        curr_pid = str(v).strip()
                        break
                
                if curr_pid == proj_id:
                    for k, v in r.items():
                        k_clean = str(k).strip().lower().replace("_", " ")
                        if k_clean == "site id": site_id_val = str(v)
                        elif k_clean == "site name": site_name_val = str(v)
                        elif k_clean == "cluster": cluster_val = str(v)
                        elif k_clean == "team name" or k_clean == "team": team_val = str(v)
                    break

        with c2:
            st.text_input("SITE ID", value=site_id_val, disabled=True)
        with c3:
            st.text_input("SITE NAME", value=site_name_val, disabled=True)
        with c4:
            st.text_input("CLUSTER", value=cluster_val, disabled=True)
        with c5:
            st.text_input("TEAM", value=team_val, disabled=True)
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, key="w_srn_status")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        w_trans_types, w_boqs, w_item_codes, w_descs, w_qtys = [], [], [], [], []
        w_statuses, w_dates, w_stn_statuses, w_remarks = [], [], [], []
        
        for i in range(st.session_state.wh_mat_count):
            if i > 0:
                st.markdown(f"<p class='wh-item-label'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"w_trans_{i}")
                w_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER *", placeholder="BOQ No", key=f"w_boq_{i}")
                w_boqs.append(boq_no)
            with mc3:
                # --- NEW: LIVE SEARCH (by code OR description, partial match) + SELECT ---
                i_code = render_item_code_search(
                    search_key=f"w_icode_search_{i}",
                    match_key=f"w_icode_match_{i}",
                    stn_status_opts=stn_status_opts,
                    on_select_keys={
                        "final_code": f"w_icode_final_{i}",
                        "idesc": f"w_idesc_{i}",
                        "stn": f"w_stn_{i}",
                    },
                )
                w_item_codes.append(i_code)
                if i_code:
                    st.caption(f"✅ Selected: **{i_code}**")

            with mc4:
                current_desc_val = st.session_state.get(f"w_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"w_idesc_{i}")
                w_descs.append(i_desc)
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"w_iqty_{i}")
                w_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"w_mstat_{i}")
                w_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"w_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                w_dates.append(d_date)
            with mc8:
                default_stn = st.session_state.get(f"w_stn_{i}", "Select")
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"w_stn_{i}")
                w_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"w_rem_{i}")
                w_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_m_add, col_m_rem, _ = st.columns([3, 3, 4])
        with col_m_add:
            if st.button("➕ Add Item", key="btn_add_wh_mat", use_container_width=True):
                st.session_state.wh_mat_count += 1
        with col_m_rem:
            if st.session_state.wh_mat_count > 1:
                if st.button("➖ Remove Item", key="btn_rem_wh_mat", use_container_width=True):
                    st.session_state.wh_mat_count -= 1
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            save_mat = st.button("💾 Save Material", type="primary", use_container_width=True)
            
        if save_mat:
            has_m_err = False
            
            if proj_id == "Select Project ID":
                st.error("⚠️ Project ID select karna compulsory hai!")
                has_m_err = True

            seen_codes = set()
            if not has_m_err:
                for idx, (b, ic) in enumerate(zip(w_boqs, w_item_codes)):
                    if not b:
                        st.error(f"⚠️ Item {idx+1}: BOQ Number dalna compulsory hai!")
                        has_m_err = True
                        break
                    
                    code_str = ic.strip()
                    if not code_str:
                        st.error(f"⚠️ Item {idx+1}: Item Code cannot be empty! (Search karke item select karein)")
                        has_m_err = True
                        break
                    
                    if code_str in seen_codes:
                        st.error(f"⚠️ Item {idx+1}: You entered duplicate Item Code '{code_str}' in this form!")
                        has_m_err = True
                        break
                    seen_codes.add(code_str)

            # --- FIX: DUPLICATE ITEM CODE CHECK — NOW SCOPED TO CURRENT WORKSPACE ONLY ---
            if not has_m_err:
                active_ws_check = st.session_state.get('active_workspace', 'VISPL')
                for ic in w_item_codes:
                    code_str = ic.strip()
                    try:
                        dup_check = supabase.table("warehouse_data").select("Item Code").eq("Project ID", proj_id).eq("Item Code", code_str).eq("workspace", active_ws_check).execute()
                        if dup_check.data and len(dup_check.data) > 0:
                            st.error(f"❌ This item '{code_str}' already exist against this project id '{proj_id}' in '{active_ws_check}' workspace.")
                            has_m_err = True
                            break
                    except Exception as db_err:
                        pass 
                        
            if not has_m_err:
                try:
                    for i in range(len(w_item_codes)):
                        insert_dict = {
                            "workspace": st.session_state.get('active_workspace', 'VISPL'),
                            "Project ID": proj_id,
                            "Site ID": site_id_val,
                            "Site Name": site_name_val,
                            "Cluster": cluster_val,
                            "Team": team_val,
                            "SRN Status": srn_status if srn_status != "Select" else "",
                            "Transaction Type": w_trans_types[i] if w_trans_types[i] != "Select" else "",
                            "BOQ Number": w_boqs[i],
                            "Item Code": w_item_codes[i].strip(),
                            "Item Description": w_descs[i],
                            "Indus Qty": w_qtys[i],
                            "Material Status": w_statuses[i] if w_statuses[i] != "Select" else "",
                            "Dispatch Date": w_dates[i],
                            "STN Status": w_stn_statuses[i] if w_stn_statuses[i] != "Select" else "",
                            "Remark": w_remarks[i]
                        }
                        supabase.table("warehouse_data").insert(insert_dict).execute()
                        
                    st.success("✅ Warehouse Material Successfully Saved!")

                    # --- Clean up search-related session state so next "Add" starts fresh ---
                    for k in list(st.session_state.keys()):
                        if k.startswith("w_icode_final_") or k.startswith("w_idesc_") or k.startswith("w_stn_") \
                           or k.startswith("w_icode_search_") or k.startswith("w_icode_match_"):
                            del st.session_state[k]

                    clear_warehouse_caches()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving Material: {e}")

# --- 3.6 EDIT WAREHOUSE MATERIAL DIALOG FUNCTION ---
@st.dialog("✏️ Edit Warehouse Material", width="large")
def edit_warehouse_material_dialog(row_data):
    st.caption("Update transaction items and asset movements")
    all_dd = get_all_dropdowns()
    rid = row_data.get('id')  # used to scope search-related keys to THIS row only

    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True, key="ed_w_pid")
        with c2:
            st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True, key="ed_w_sid")
        with c3:
            st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True, key="ed_w_sname")
        with c4:
            st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True, key="ed_w_clu")
        with c5:
            st.text_input("TEAM", value=row_data.get('Team', ''), disabled=True, key="ed_w_team")
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, index=get_idx(row_data.get('SRN Status'), srn_opts), key="ed_w_srn")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            t_type = st.selectbox("TRANSACTION TYPE", trans_types, index=get_idx(row_data.get('Transaction Type'), trans_types), key="ed_w_trans")
        with mc2:
            boq_no = st.text_input("BOQ NUMBER *", value=row_data.get('BOQ Number', ''), key="ed_w_boq")
        with mc3:
            # --- NEW: LIVE SEARCH (by code OR description, partial match) + SELECT ---
            # Pre-load the current item's code as the starting point (row-scoped key so
            # switching between different rows never shows a stale selection).
            final_code_key = f"ed_w_icode_final_{rid}"
            idesc_key = f"ed_w_idesc_{rid}"
            stn_key = f"ed_w_stn_{rid}"

            if final_code_key not in st.session_state:
                st.session_state[final_code_key] = row_data.get('Item Code', '')
            if idesc_key not in st.session_state:
                st.session_state[idesc_key] = row_data.get('Item Description', '')
            if stn_key not in st.session_state:
                _cur_stn = row_data.get('STN Status', 'Select')
                st.session_state[stn_key] = _cur_stn if _cur_stn in stn_status_opts else "Select"

            i_code = render_item_code_search(
                search_key=f"ed_w_icode_search_{rid}",
                match_key=f"ed_w_icode_match_{rid}",
                stn_status_opts=stn_status_opts,
                on_select_keys={
                    "final_code": final_code_key,
                    "idesc": idesc_key,
                    "stn": stn_key,
                },
            )
            st.caption(f"✅ Current Code: **{i_code or '—'}**")
        with mc4:
            i_desc = st.text_input("ITEM DESCRIPTION", key=idesc_key)
        with mc5:
            try:
                indus_val = float(row_data.get('Indus Qty', 0))
            except:
                indus_val = 0.0
            i_qty = st.number_input("INDUS QTY", value=indus_val, key="ed_w_iqty")
            
        mc6, mc7, mc8, mc9 = st.columns(4)
        with mc6:
            m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, index=get_idx(row_data.get('Material Status'), mat_status_opts), key="ed_w_mstat")
        with mc7:
            val_date = str(row_data.get('Dispatch Date', ''))
            d_date = st.text_input("DISPATCH DATE (DD/MM/YYYY)", value=val_date if val_date != 'nan' else "", key="ed_w_ddate")
        with mc8:
            stn_stat = st.selectbox("STN STATUS", stn_status_opts, key=stn_key)
        with mc9:
            val_rem = str(row_data.get('Remark', ''))
            rem = st.text_input("REMARKS", value=val_rem if val_rem != 'nan' else "", key="ed_w_rem")

        st.markdown("<br>", unsafe_allow_html=True)
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            update_mat = st.button("💾 Update Material", type="primary", use_container_width=True)
            
        if update_mat:
            if not boq_no:
                st.error("⚠️ BOQ Number dalna compulsory hai!")
            elif not i_code.strip():
                st.error("⚠️ Item Code cannot be empty! (Search karke item select karein)")
            else:
                try:
                    update_dict = {
                        "SRN Status": srn_status if srn_status != "Select" else "",
                        "Transaction Type": t_type if t_type != "Select" else "",
                        "BOQ Number": boq_no,
                        "Item Code": i_code.strip(),
                        "Item Description": i_desc,
                        "Indus Qty": i_qty,
                        "Material Status": m_stat if m_stat != "Select" else "",
                        "Dispatch Date": d_date,
                        "STN Status": stn_stat if stn_stat != "Select" else "",
                        "Remark": rem
                    }
                    supabase.table("warehouse_data").update(update_dict).eq("id", row_data['id']).execute()
                    st.success("✅ Warehouse Material Successfully Updated!")

                    # --- Clean up this row's search-related session state ---
                    for k in [final_code_key, idesc_key, stn_key, f"ed_w_icode_search_{rid}", f"ed_w_icode_match_{rid}"]:
                        if k in st.session_state:
                            del st.session_state[k]

                    clear_warehouse_caches()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Updating Material: {e}")

# --- 3.7 VIEW RECORD DIALOG FUNCTION (READ-ONLY) ---
@st.dialog("👁️ View Warehouse Material", width="large")
def view_record_dialog(row_data):
    st.caption("Read-only preview of transaction items and asset movements")

    st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True)
    with c2: st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True)
    with c3: st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True)
    with c4: st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True)
    with c5: st.text_input("TEAM", value=row_data.get('Team', ''), disabled=True)
    with c6: st.text_input("SRN STATUS", value=row_data.get('SRN Status', ''), disabled=True)

    st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1: st.text_input("TRANSACTION TYPE", value=row_data.get('Transaction Type', ''), disabled=True)
    with mc2: st.text_input("BOQ NUMBER", value=row_data.get('BOQ Number', ''), disabled=True)
    with mc3: st.text_input("ITEM CODE", value=row_data.get('Item Code', ''), disabled=True)
    with mc4: st.text_input("ITEM DESCRIPTION", value=row_data.get('Item Description', ''), disabled=True)
    with mc5: st.text_input("INDUS QTY", value=str(row_data.get('Indus Qty', '')), disabled=True)

    mc6, mc7, mc8, mc9 = st.columns(4)
    with mc6: st.text_input("MATERIAL STATUS", value=row_data.get('Material Status', ''), disabled=True)
    with mc7: st.text_input("DISPATCH DATE", value=row_data.get('Dispatch Date', ''), disabled=True)
    with mc8: st.text_input("STN STATUS", value=row_data.get('STN Status', ''), disabled=True)
    with mc9: st.text_input("REMARKS", value=row_data.get('Remark', ''), disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True):
        st.rerun()

# --- 3.8 DELETE CONFIRMATION DIALOG (replaces the old inline confirm row) ---
@st.dialog("🗑️ Delete Warehouse Material")
def delete_confirm_dialog(row_data):
    rid = row_data.get("id")
    st.markdown(
        f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
<div style="font-weight:900;color:#991b1b;font-size:1rem;">{html.escape(str(row_data.get('Item Code','') or '-'))}</div>
<div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">{html.escape(str(row_data.get('Project ID','') or '-'))} • {html.escape(str(row_data.get('Site Name','') or '-'))}</div>
</div>
<p style="color:#475569;">Ye record permanently delete ho jayega. Kya aap sure hain?</p>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="wh_del_no", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="wh_del_yes", type="primary", use_container_width=True):
            try:
                supabase.table("warehouse_data").delete().eq("id", rid).execute()
                st.success("✅ Record Successfully Deleted!")
                clear_warehouse_caches()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Deleting Record: {e}")

# --- 3.9 EXPORT DIALOG FUNCTION ---
@st.dialog("📥 Export Data", width="large")
def export_dialog(df_export):
    st.caption("Download your live database records as an Excel file.")
    
    export_df = df_export.copy()
    if "🎯 Select" in export_df.columns:
        export_df = export_df.drop(columns=["🎯 Select"])
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Warehouse Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="Warehouse_Data_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_ref, col_add, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>📦 Warehouse Material Hub</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        clear_warehouse_caches()
        get_all_dropdowns.clear()
        get_site_projects.clear()
        st.rerun() 
with col_add:
    if st.button("➕ Add New Material", use_container_width=True):
        st.session_state.wh_mat_count = 1
        # --- Clear any stale item-search selections from a previous "Add" session ---
        for k in list(st.session_state.keys()):
            if k.startswith("w_icode_final_") or k.startswith("w_idesc_") or k.startswith("w_stn_") \
               or k.startswith("w_icode_search_") or k.startswith("w_icode_match_"):
                del st.session_state[k]
        add_warehouse_material_dialog() 
with col_export:
    if st.button("📥 Download", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH & PREPARE DATA FROM WAREHOUSE (cached — see fetch_warehouse_data_cached above) ---
table_name = "warehouse_data"
active_ws = st.session_state.get('active_workspace', 'VISPL')
data = fetch_warehouse_data_cached(active_ws)

columns_list = [
    "id", "Project ID", "Site ID", "Site Name", "Cluster", "Team", 
    "SRN Status", "Transaction Type", "BOQ Number", "Item Code", 
    "Item Description", "Indus Qty", "Material Status", "Dispatch Date", 
    "STN Status", "Remark"
]

if data:
    df_raw = pd.DataFrame(data)
    df = pd.DataFrame()
    for col in columns_list:
        matched = False
        for raw_col in df_raw.columns:
            if str(raw_col).strip().lower().replace("_", " ") == str(col).strip().lower().replace("_", " "):
                df[col] = df_raw[raw_col]
                matched = True
                break
        if not matched:
            df[col] = ""
    # Newest first (highest id on top)
    if "id" in df.columns:
        _idn = pd.to_numeric(df["id"], errors="coerce")
        if _idn.notna().any():
            df = df.assign(_idn=_idn.fillna(-1)).sort_values("_idn", ascending=False).drop(columns=["_idn"]).reset_index(drop=True)
else:
    df = pd.DataFrame(columns=columns_list)

if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)
else:
    df["🎯 Select"] = False

# --- EXPORT LOGIC TRIGGER AFTER DF LOAD ---
if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = "" 

# --- 5.5 SEARCH BOX + VIEW MODE TOGGLE ---
col_table_title, col_search, col_viewtoggle = st.columns([5, 3, 2])
with col_table_title:
    st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Live Warehouse Records</h5>", unsafe_allow_html=True)
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")
with col_viewtoggle:
    toggle_label = "📱 Mobile View" if st.session_state.wh_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="wh_view_mode_toggle"):
        st.session_state.wh_view_mode = "cards" if st.session_state.wh_view_mode == "table" else "table"
        st.rerun()

if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]


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
    return "" if s.lower() in ("nan", "nat", "none", "null", "-") else s

def _num(v):
    try:
        s = _clean(v).replace(",", "")
        return float(s) if s else 0.0
    except (TypeError, ValueError):
        return 0.0

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

def _qty(v):
    s = _clean(v)
    if not s:
        return _MUTED
    n = _num(s)
    shown = str(int(n)) if float(n).is_integer() else f"{n:g}"
    return f"<div class='slux-cell' style='text-align:center;'><span class='slux-qty'>{shown}</span></div>"

def status_badge(val):
    v = _clean(val)
    if not v:
        return _MUTED
    vl = v.lower()
    if "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "received", "delivered", "dispatched"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress", "transit"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<div class='slux-cell'><span class='status-badge {cls}'>{html.escape(v)}</span></div>"


# --- KPI CARDS (search ke hisaab se) ---
k_records = len(df)
k_projects = df["Project ID"].map(_clean).replace("", pd.NA).dropna().nunique() if not df.empty else 0
k_qty = sum(_num(v) for v in df["Indus Qty"]) if not df.empty else 0.0
k_stn_pending = int(df["STN Status"].astype(str).str.lower().str.contains("pending|required", regex=True, na=False).sum()) if not df.empty else 0

def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

k_qty_txt = f"{int(k_qty):,}" if float(k_qty).is_integer() else f"{k_qty:,.2f}"
st.markdown(
    '<div class="lux-kpi-grid">'
    + _kpi("📦", "Material Lines", f"{k_records:,}", "Filtered results" if search_query else "All records", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
    + _kpi("🏗️", "Projects", f"{k_projects:,}", "Unique Project IDs", "linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")
    + _kpi("🔢", "Total Indus Qty", k_qty_txt, "Sum of all lines", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5")
    + _kpi("⏳", "STN Pending / Required", f"{k_stn_pending:,}", "Needs STN action", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb", "red" if k_stn_pending else "")
    + '</div>',
    unsafe_allow_html=True,
)

# --- 6. PAGINATION LOGIC (10 lines per page) ---
if 'wh_current_page' not in st.session_state:
    st.session_state.wh_current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.wh_current_page > total_pages:
    st.session_state.wh_current_page = total_pages
elif st.session_state.wh_current_page < 1:
    st.session_state.wh_current_page = 1

start_idx = (st.session_state.wh_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 7. ✨ LAVISH TABLE (or mobile cards) ---
df_page = df.iloc[start_idx:end_idx].copy()

if df_page.empty:
    st.markdown(
        '<div class="slux-empty"><div>🗂️</div>'
        + ("No records match your search." if search_query else "No warehouse records yet. Click ➕ Add New Material to create one.")
        + '</div>',
        unsafe_allow_html=True,
    )

elif st.session_state.wh_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE-FRIENDLY CARD VIEW - one card per record, no horizontal scroll
    # ---------------------------------------------------------------
    for page_pos, (_, row) in enumerate(df_page.iterrows()):
        row_dict = row.to_dict()
        rid = row_dict.get("id")
        serial_no = start_idx + page_pos + 1

        with st.container(border=True):
            st.markdown(f"""
                <div class="wh-card-title">#{serial_no} — {html.escape(_clean(row_dict.get('Item Code')) or '-')}</div>
                <div class="wh-card-sub">{html.escape(_clean(row_dict.get('Project ID')) or '-')} • {html.escape(_clean(row_dict.get('Site ID')) or '-')}</div>
                <div class="wh-card-row"><span class="wh-card-label">Site Name</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Site Name')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Cluster</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Cluster')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Team</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Team')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">SRN Status</span><span class="wh-card-value">{status_badge(row_dict.get('SRN Status',''))}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Transaction Type</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Transaction Type')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">BOQ Number</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('BOQ Number')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Item Description</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Item Description')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Indus Qty</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Indus Qty')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Material Status</span><span class="wh-card-value">{status_badge(row_dict.get('Material Status',''))}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Dispatch Date</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Dispatch Date')) or '-')}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">STN Status</span><span class="wh-card-value">{status_badge(row_dict.get('STN Status',''))}</span></div>
                <div class="wh-card-row"><span class="wh-card-label">Remark</span><span class="wh-card-value">{html.escape(_clean(row_dict.get('Remark')) or '-')}</span></div>
            """, unsafe_allow_html=True)

            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("👁️ View", key=f"card_view_{rid}", use_container_width=True):
                    view_record_dialog(row_dict)
            with bc2:
                if st.button("✏️ Edit", key=f"card_edit_{rid}", use_container_width=True):
                    edit_warehouse_material_dialog(row_dict)
            with bc3:
                if st.button("🗑️ Delete", key=f"card_del_{rid}", use_container_width=True):
                    delete_confirm_dialog(row_dict)

else:
    # ---------------------------------------------------------------
    # ✨ LAVISH DESKTOP TABLE VIEW — single ⚙️ button at row start
    # ---------------------------------------------------------------
    COL_RATIOS = [
        0.55, 0.5,                   # ⚙️, #
        1.3, 1.1, 1.6, 1.0, 1.1,     # Project ID, Site ID, Site Name, Cluster, Team
        1.1, 1.3, 1.1, 1.3,          # SRN Status, Transaction Type, BOQ Number, Item Code
        2.2, 0.8, 1.3, 1.1,          # Item Description, Indus Qty, Material Status, Dispatch Date
        1.1, 1.6                     # STN Status, Remark
    ]
    COL_LABELS = [
        "⚙️", "#",
        "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "TEAM",
        "SRN STATUS", "TRANSACTION TYPE", "BOQ NUMBER", "ITEM CODE",
        "ITEM DESCRIPTION", "INDUS QTY", "MATERIAL STATUS", "DISPATCH DATE",
        "STN STATUS", "REMARK"
    ]

    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">📦 Warehouse Register<span>newest first • scroll right for more →</span></div>'
        f'<div class="slux-badge">Qty {k_qty_txt}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="wh_table_wrap", height=560):
        # --- HEADER ROW (sticky) ---
        with st.container(key="whhead"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                cls = " c" if i in (0, 1, 12) else ""
                h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

        # --- DATA ROWS ---
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1
            rk = rid if _clean(rid) else f"s{serial_no}"
            parity = "odd" if serial_no % 2 else "even"

            with st.container(key=f"whrow_{parity}_{rk}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                with rcols[0]:
                    with st.container(key=f"whpop_{rk}"):
                        with st.popover("⚙️"):
                            if st.button("👁️ View", key=f"view_{rid}", use_container_width=True):
                                view_record_dialog(row_dict)
                            if st.button("✏️ Edit", key=f"edit_{rid}", use_container_width=True):
                                edit_warehouse_material_dialog(row_dict)
                            if st.button("🗑️ Delete", key=f"del_{rid}", use_container_width=True):
                                delete_confirm_dialog(row_dict)

                rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)
                rcols[2].markdown(_chip(row_dict.get('Project ID'), "proj"), unsafe_allow_html=True)
                rcols[3].markdown(_chip(row_dict.get('Site ID')), unsafe_allow_html=True)
                rcols[4].markdown(_txt(row_dict.get('Site Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[5].markdown(_pill(row_dict.get('Cluster')), unsafe_allow_html=True)
                rcols[6].markdown(_txt(row_dict.get('Team'), "slux-strong"), unsafe_allow_html=True)
                rcols[7].markdown(status_badge(row_dict.get('SRN Status')), unsafe_allow_html=True)
                rcols[8].markdown(_txt(row_dict.get('Transaction Type'), "slux-soft"), unsafe_allow_html=True)
                rcols[9].markdown(_chip(row_dict.get('BOQ Number')), unsafe_allow_html=True)
                rcols[10].markdown(_chip(row_dict.get('Item Code'), "item"), unsafe_allow_html=True)
                rcols[11].markdown(_txt(row_dict.get('Item Description')), unsafe_allow_html=True)
                rcols[12].markdown(_qty(row_dict.get('Indus Qty')), unsafe_allow_html=True)
                rcols[13].markdown(status_badge(row_dict.get('Material Status')), unsafe_allow_html=True)
                rcols[14].markdown(_txt(row_dict.get('Dispatch Date'), "slux-soft"), unsafe_allow_html=True)
                rcols[15].markdown(status_badge(row_dict.get('STN Status')), unsafe_allow_html=True)
                rcols[16].markdown(_txt(row_dict.get('Remark'), "slux-soft"), unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    st.markdown(
        '<div class="slux-foot">'
        f'<div>{total_rows:,} material line{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small></div>'
        f'<div class="slux-foot-amts"><span>Total Qty: <b style="color:#047857;">{k_qty_txt}</b></span>'
        f'<span class="slux-foot-badge">Page {st.session_state.wh_current_page} of {total_pages}</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.wh_current_page == 1)):
        st.session_state.wh_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.wh_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.wh_current_page == total_pages)):
        st.session_state.wh_current_page += 1
        st.rerun()
