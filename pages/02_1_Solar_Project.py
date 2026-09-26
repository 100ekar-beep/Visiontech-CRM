import streamlit as st
import pandas as pd
import math
import io
import datetime
import os
from html import escape
from collections import defaultdict
from supabase import create_client, Client
from st_keyup import st_keyup

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Solar Project Hub", page_icon="☀️", layout="wide")

# --- INIT SESSION STATE ---
if 'solar_current_page' not in st.session_state:
    st.session_state.solar_current_page = 1

if 'solar_active_page' not in st.session_state:
    st.session_state.solar_active_page = "sites"

# --- MOBILE VIEW TOGGLE STATES (one per tab, independent of each other) ---
if 'solar_sites_view' not in st.session_state:
    st.session_state.solar_sites_view = "table"
if 'solar_ledger_view' not in st.session_state:
    st.session_state.solar_ledger_view = "table"
if 'solar_payments_view' not in st.session_state:
    st.session_state.solar_payments_view = "table"

# --- 2. CSS (✨ LAVISH LIGHT THEME — Quotation / Site Data jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%);
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
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important; font-weight: 800 !important;
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
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p {
        color: #1e293b !important;
    }
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
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%) !important;
        color: #ffffff !important; border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* ================= PAGE NAVIGATION BAR (Sites / Ledger / Payments) ================= */
    .st-key-solar_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-solar_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 16px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-solar_nav_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-solar_nav_bar button[kind="secondary"]:hover {
        background: #fff7ed !important; border-color: #fdba74 !important; transform: translateY(-2px) !important;
    }
    .st-key-solar_nav_bar button[kind="secondary"] p,
    .st-key-solar_nav_bar button[kind="secondary"] span,
    .st-key-solar_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; font-size: 1.05rem !important; }
    .st-key-solar_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 18px rgba(245, 158, 11, 0.45) !important;
    }
    .st-key-solar_nav_bar button[kind="primary"] p,
    .st-key-solar_nav_bar button[kind="primary"] span,
    .st-key-solar_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; font-size: 1.05rem !important; }

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

    /* ================= SCROLLING TABLE BODIES (all 4 tables) ================= */
    .st-key-solar_table_wrap, .st-key-ledger_table_wrap, .st-key-payments_table_wrap, .st-key-site_ledger_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-solar_table_wrap [data-testid="stVerticalBlock"],
    .st-key-ledger_table_wrap [data-testid="stVerticalBlock"],
    .st-key-payments_table_wrap [data-testid="stVerticalBlock"],
    .st-key-site_ledger_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-solar_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-ledger_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-payments_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-site_ledger_table_wrap [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-solar_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-solar_table_wrap div[class*="st-key-solhead_"], .st-key-solar_table_wrap div[class*="st-key-solrow_"],
    .st-key-site_ledger_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-site_ledger_table_wrap div[class*="st-key-solhead_"], .st-key-site_ledger_table_wrap div[class*="st-key-solrow_"] { min-width: 1900px !important; }
    .st-key-ledger_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-ledger_table_wrap div[class*="st-key-solhead_"], .st-key-ledger_table_wrap div[class*="st-key-solrow_"] { min-width: 1100px !important; }
    .st-key-payments_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-payments_table_wrap div[class*="st-key-solhead_"], .st-key-payments_table_wrap div[class*="st-key-solrow_"] { min-width: 1000px !important; }

    .st-key-solar_table_wrap [data-testid="stColumn"], .st-key-solar_table_wrap [data-testid="column"],
    .st-key-ledger_table_wrap [data-testid="stColumn"], .st-key-ledger_table_wrap [data-testid="column"],
    .st-key-payments_table_wrap [data-testid="stColumn"], .st-key-payments_table_wrap [data-testid="column"],
    .st-key-site_ledger_table_wrap [data-testid="stColumn"], .st-key-site_ledger_table_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header rows */
    div[class*="st-key-solhead_"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-solhead_"] [data-testid="stColumn"], div[class*="st-key-solhead_"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-solrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-solrow_odd"] { background: #fafaff; }
    div[class*="st-key-solrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-solrow_"] p { margin: 0 !important; }

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
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .sol-team { font-weight: 800; color: #b45309; }
    .sol-mini {
        display: inline-block; margin-left: 6px; padding: 2px 8px; border-radius: 999px;
        font-size: .64rem; font-weight: 800; letter-spacing: .4px; vertical-align: middle;
    }
    .sol-mini.done { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .sol-mini.pend { background: #fef9c3; color: #a16207; border: 1px solid #fde68a; }
    .sol-amt { text-align: right; font-weight: 700; color: #334155; font-variant-numeric: tabular-nums; }
    .sol-amt.zero { color: #cbd5e1; font-weight: 600; }
    .sol-amt.strong { color: #4f46e5; font-weight: 900; font-size: .92rem; }
    .sol-amt.amber { color: #d97706; font-weight: 900; font-size: .92rem; }
    .sol-amt.paid { color: #059669; font-weight: 900; }
    .sol-amt.due { color: #dc2626; font-weight: 900; }

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

    /* Inline row buttons */
    div[class*="st-key-solar_mgr_"] button, div[class*="st-key-ledger_view_"] button, div[class*="st-key-delpay_"] button {
        width: 38px !important; max-width: 38px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        box-shadow: none !important; font-size: 1rem !important; transition: all .2s ease !important;
    }
    div[class*="st-key-solar_mgr_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-solar_mgr_"] button:hover { background: #3b82f6 !important; border-color: #60a5fa !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important; }
    div[class*="st-key-ledger_view_"] button { background: rgba(99,102,241,0.15) !important; border: 1px solid rgba(99,102,241,0.3) !important; }
    div[class*="st-key-ledger_view_"] button:hover { background: #6366f1 !important; border-color: #818cf8 !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(99,102,241,.6) !important; }
    div[class*="st-key-delpay_"] button { background: rgba(239,68,68,0.12) !important; border: 1px solid rgba(239,68,68,0.3) !important; }
    div[class*="st-key-delpay_"] button:hover { background: #ef4444 !important; border-color: #f87171 !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(239,68,68,.6) !important; }

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
    .solar-mcard-title { font-size: 1.05rem; font-weight: 800; color: #312e81; margin-bottom: 2px; }
    .solar-mcard-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
    .solar-mcard-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; gap: 10px; }
    .solar-mcard-row:last-child { border-bottom: none; }
    .solar-mcard-label { color: #64748b; font-weight: 700; white-space: nowrap; text-transform: uppercase; font-size: .75rem; }
    .solar-mcard-value { color: #0f172a; font-weight: 600; text-align: right; }
    .solar-mcard-value.paid { color: #059669; font-weight: 800; }
    .solar-mcard-value.pending { color: #dc2626; font-weight: 800; }
    .solar-mcard-value.amber { color: #d97706; font-weight: 800; }

    /* Detail dialog mini tables */
    .sol-dlg-head { color: #4338ca; font-size: .72rem; font-weight: 800; letter-spacing: .8px; text-transform: uppercase; }
    .sol-dlg-cell { color: #1e293b; font-size: .88rem; }
    .sol-dlg-muted { color: #64748b; font-size: .85rem; }
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

def get_simple_opts(category, all_data, fallback):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return opts if opts else fallback

def num(v):
    try:
        return float(v) if v not in (None, "", "None") else 0.0
    except Exception:
        return 0.0

# --- SMALL HELPER TO RENDER THE "TABLE / MOBILE" TOGGLE BUTTON ---
def render_view_toggle(state_key, button_key):
    toggle_label = "📱 Mobile View" if st.session_state[state_key] == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key=button_key):
        st.session_state[state_key] = "cards" if st.session_state[state_key] == "table" else "table"
        st.rerun()

# ================================================================
# --- ✨ LAVISH TABLE RENDER HELPERS ---
# ================================================================
_MUTED = "<div class='slux-cell'><span class='slux-muted'>—</span></div>"

def _clean(v):
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("nan", "none", "null", "-") else s

def _txt(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div class='slux-cell {extra_cls}' title='{escape(s)}'>{escape(s)}</div>"

def _chip(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-chip {extra_cls}'>{escape(s)}</span></div>"

def _pill(v):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-pill'>{escape(s)}</span></div>"

def _money(v, style=""):
    val = num(v)
    cls = "zero" if val == 0 and not style else style
    return f"<div class='slux-cell sol-amt {cls}'>₹ {val:,.0f}</div>"

def _team_cell(name, status):
    n = _clean(name)
    if not n:
        return _MUTED
    mini = "<span class='sol-mini done'>✓ DONE</span>" if status == "Completed" else "<span class='sol-mini pend'>⏳ PENDING</span>"
    return f"<div class='slux-cell' title='{escape(n)}'><span class='sol-team'>{escape(n)}</span>{mini}</div>"

def status_badge(val):
    v = _clean(val)
    if not v:
        return _MUTED
    vl = v.lower()
    if vl == "not required":
        cls = "status-grey"
    elif "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "available"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<div class='slux-cell'><span class='status-badge {cls}'>{escape(v)}</span></div>"

def kpi_card(icon, label, value, foot="", accent="linear-gradient(90deg,#6366f1,#8b5cf6)", soft="#eef2ff", value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

KPI_INDIGO = ("linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
KPI_GREEN = ("linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5")
KPI_AMBER = ("linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb")
KPI_PINK = ("linear-gradient(90deg,#ec4899,#a855f7)", "#fdf2f8")
KPI_BLUE = ("linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")
KPI_RED = ("linear-gradient(90deg,#ef4444,#f97316)", "#fef2f2")

def table_title_bar(title, subtitle, badge):
    st.markdown(
        '<div class="slux-head-bar">'
        f'<div class="slux-title">{title}<span>{subtitle}</span></div>'
        f'<div class="slux-badge">{badge}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

def table_header_row(key, ratios, labels, center_idx=(), right_idx=()):
    with st.container(key=key):
        h_cols = st.columns(ratios, vertical_alignment="center")
        for i, (h_col, label) in enumerate(zip(h_cols, labels)):
            cls = " c" if i in center_idx else (" r" if i in right_idx else "")
            h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

def empty_state(msg):
    st.markdown(f'<div class="slux-empty"><div>🗂️</div>{escape(msg)}</div>', unsafe_allow_html=True)

# --- 4. MANAGE TEAMS DIALOG (amount-only, no payment status) ---
@st.dialog("⚙️ Manage Solar Teams & Charges", width="large")
def manage_solar_teams_dialog(site_row, alloc_row):
    st.caption("Civil / Electrical / Transporter teams ke charges yahan manage karein")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("PROJECT ID", value=site_row.get("Project ID", ""), disabled=True)
    with c2: st.text_input("SITE ID", value=site_row.get("Site ID", ""), disabled=True)
    with c3: st.text_input("SITE NAME", value=site_row.get("Site Name", ""), disabled=True)
    with c4: st.text_input("CLUSTER", value=site_row.get("Cluster", ""), disabled=True)

    all_dd = get_all_dropdowns()
    team_opts = get_opts("Team Name", all_dd)

    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    def team_section(label, key_prefix, alloc):
        st.markdown(f'<div class="modal-section-title">👷 {label} TEAM</div>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_name = st.selectbox(
                f"{label} TEAM NAME", team_opts,
                index=get_idx(alloc.get(f"{key_prefix}_team_name", ""), team_opts),
                key=f"solar_{key_prefix}_team"
            )
        with tc2:
            status_opts = ["Pending", "Completed"]
            t_status = st.selectbox(
                f"{label} STATUS", status_opts,
                index=(1 if alloc.get(f"{key_prefix}_status") == "Completed" else 0),
                key=f"solar_{key_prefix}_status"
            )
        with tc3:
            t_charge = st.number_input(
                f"{label} CHARGE AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_charge_amount", 0)),
                key=f"solar_{key_prefix}_charge"
            )
        tc4, tc5 = st.columns([1, 2])
        with tc4:
            t_appr_amt = st.number_input(
                f"{label} EXTRA APPROVAL AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_extra_approval_amount", 0)),
                key=f"solar_{key_prefix}_apprvamt"
            )
        with tc5:
            t_appr_remark = st.text_input(
                f"{label} EXTRA APPROVAL REMARK (kis baat ka approval hai)",
                value=alloc.get(f"{key_prefix}_extra_approval_remark", ""),
                placeholder="Amount > 0 hai to yeh likhna compulsory hai",
                key=f"solar_{key_prefix}_apprvremark"
            )
        return {
            f"{key_prefix}_team_name": t_name if t_name != "Select" else "",
            f"{key_prefix}_status": t_status,
            f"{key_prefix}_charge_amount": t_charge,
            f"{key_prefix}_extra_approval_amount": t_appr_amt,
            f"{key_prefix}_extra_approval_remark": t_appr_remark,
        }

    civil_data = team_section("CIVIL", "civil", alloc_row)
    electrical_data = team_section("ELECTRICAL", "electrical", alloc_row)
    transport_data = team_section("TRANSPORTER", "transport", alloc_row)

    st.markdown('<div class="modal-section-title">📝 REMARKS</div>', unsafe_allow_html=True)
    remarks = st.text_area("REMARKS", value=alloc_row.get("remarks", ""), key="solar_remarks", height=80)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        save_clicked = st.button("💾 Save Allocation", type="primary", use_container_width=True)

    if save_clicked:
        has_error = False
        for label, data, key_prefix in [("CIVIL", civil_data, "civil"), ("ELECTRICAL", electrical_data, "electrical"), ("TRANSPORTER", transport_data, "transport")]:
            amt = num(data.get(f"{key_prefix}_extra_approval_amount", 0))
            rmk = str(data.get(f"{key_prefix}_extra_approval_remark", "")).strip()
            if amt > 0 and not rmk:
                st.error(f"⚠️ {label} Extra Approval Amount ₹{amt:,.0f} diya hai, iske liye Remark likhna compulsory hai (kis baat ka approval hai)!")
                has_error = True

        if has_error:
            st.stop()

        payload = {
            "workspace": st.session_state.get('active_workspace', 'VISPL'),
            "Project ID": site_row.get("Project ID", ""),
            "Site ID": site_row.get("Site ID", ""),
            "Site Name": site_row.get("Site Name", ""),
            "Cluster": site_row.get("Cluster", ""),
            "remarks": remarks,
        }
        payload.update(civil_data)
        payload.update(electrical_data)
        payload.update(transport_data)

        try:
            existing = supabase.table("solar_team_allocation") \
                .select("id") \
                .eq("workspace", payload["workspace"]) \
                .eq("Project ID", payload["Project ID"]) \
                .execute()
            if existing.data:
                supabase.table("solar_team_allocation").update(payload).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("solar_team_allocation").insert(payload).execute()
            st.success("✅ Solar Team Allocation Saved!")
            fetch_solar_data_cached.clear()
            st.rerun()
        except Exception as e:
            err_str = str(e)
            if "schema cache" in err_str.lower() or "PGRST204" in err_str:
                st.error("❌ Database mein zaroori columns nahi mile. Kripya 'solar_setup.sql' script Supabase SQL Editor mein (dobara) run karein, phir 30 second wait karke retry karein.")
            else:
                st.error(f"❌ Error saving allocation: {e}")

# --- 5. VIEW TEAM SITE DETAILS DIALOG (Ledger tab) ---
@st.dialog("🧾 Team Site-wise & Payment Detail", width="large")
def view_team_detail_dialog(team_name, entries, payments):
    st.caption(f"Team '{team_name}' ke saare Solar sites aur payments ka detailed hisaab")

    st.markdown('<div class="modal-section-title">🏗️ WORK DONE (SITE-WISE)</div>', unsafe_allow_html=True)
    h1, h2, h3, h4, h5, h6, h7 = st.columns([1.3, 1.3, 0.9, 0.9, 1.0, 1.0, 2.0])
    for c, label in zip([h1, h2, h3, h4, h5, h6, h7],
                         ["SITE ID", "PROJECT ID", "ROLE", "STATUS", "CHARGE (₹)", "APPROVAL (₹)", "APPROVAL REMARK"]):
        c.markdown(f"<span class='sol-dlg-head'>{label}</span>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none; border-top:2px solid #e0e7ff; margin:6px 0;'>", unsafe_allow_html=True)
    for e in entries:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.3, 1.3, 0.9, 0.9, 1.0, 1.0, 2.0])
        c1.markdown(f"<span class='slux-chip'>{escape(str(e['site_id']))}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span class='slux-chip proj'>{escape(str(e['project_id']))}</span>", unsafe_allow_html=True)
        c3.markdown(f"<span class='sol-dlg-cell'>{e['role']}</span>", unsafe_allow_html=True)
        status_cls = "status-green" if e.get('status') == "Completed" else "status-yellow"
        c4.markdown(f"<span class='status-badge {status_cls}'>{e.get('status','Pending')}</span>", unsafe_allow_html=True)
        c5.markdown(f"<span class='sol-dlg-cell'>{e['charge']:,.0f}</span>", unsafe_allow_html=True)
        c6.markdown(f"<span class='sol-dlg-cell'>{e['approval']:,.0f}</span>", unsafe_allow_html=True)
        c7.markdown(f"<span class='sol-dlg-muted'>{escape(str(e['approval_remark'] or '-'))}</span>", unsafe_allow_html=True)
    st.caption("💡 Sirf 'Completed' status wale kaam ka amount Total Billed / Balance mein count hota hai.")

    st.markdown('<div class="modal-section-title">💰 PAYMENTS RECEIVED</div>', unsafe_allow_html=True)
    if payments:
        p1, p2, p3, p4, p5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.2])
        for c, label in zip([p1, p2, p3, p4, p5], ["DATE", "PAID FROM", "TYPE", "AMOUNT (₹)", "REMARK"]):
            c.markdown(f"<span class='sol-dlg-head'>{label}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:2px solid #e0e7ff; margin:6px 0;'>", unsafe_allow_html=True)
        for p in payments:
            p1, p2, p3, p4, p5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.2])
            p1.markdown(f"<span class='sol-dlg-cell'>{escape(str(p.get('pay_date','')))}</span>", unsafe_allow_html=True)
            p2.markdown(f"<span class='sol-dlg-cell'>{escape(str(p.get('pay_from','')))}</span>", unsafe_allow_html=True)
            p3.markdown(f"<span class='sol-dlg-cell'>{escape(str(p.get('pay_type','')))}</span>", unsafe_allow_html=True)
            p4.markdown(f"<span style='color:#059669; font-weight:800;'>{num(p.get('amount')):,.0f}</span>", unsafe_allow_html=True)
            p5.markdown(f"<span class='sol-dlg-muted'>{escape(str(p.get('remark','') or '-'))}</span>", unsafe_allow_html=True)
    else:
        st.info("Is team ko abhi tak koi payment nahi kiya gaya.")

    completed_entries = [e for e in entries if e.get("status") == "Completed"]
    total_billed = sum(e['charge'] + e['approval'] for e in completed_entries)
    total_paid = sum(num(p.get('amount')) for p in payments)
    balance = total_billed - total_paid
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #f5f3ff, #eef2ff); border: 1px solid #c7d2fe; padding: 14px 20px; border-radius: 12px; margin-top:15px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px;">
            <div style="color:#312e81; font-weight:800;">Total Billed: <span style="color:#4f46e5;">₹ {total_billed:,.0f}</span></div>
            <div style="color:#312e81; font-weight:800;">Total Paid: <span style="color:#059669;">₹ {total_paid:,.0f}</span></div>
            <div style="color:#312e81; font-weight:800;">Balance: <span style="color:{'#dc2626' if balance>0 else '#059669'};">₹ {balance:,.0f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    def generate_team_pdf():
        if FPDF is None:
            raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()

        if os.path.exists("logo (1).png"):
            pdf.image("logo (1).png", x=75, y=10, w=60)
            pdf.ln(28)

        primary_color = (15, 23, 42)
        secondary_color = (245, 158, 11)
        green_color = (16, 185, 129)
        red_color = (239, 68, 68)

        pdf.set_text_color(*primary_color)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(190, 10, "VISIONTECH INFRA SOLUTION PVT. LTD.", ln=True, align='C')

        pdf.set_text_color(*secondary_color)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 8, "SOLAR PROJECT - TEAM LEDGER", ln=True, align='C')

        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, f"Team: {team_name}", ln=True, align='C')
        pdf.ln(4)

        def draw_table(title, cols, col_widths, rows, header_color):
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(*header_color)
            pdf.cell(190, 8, title, ln=True, align='L')

            pdf.set_fill_color(*header_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 8)
            for i, col in enumerate(cols):
                pdf.cell(col_widths[i], 8, col, border=1, align='C', fill=True)
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 8)
            fill = False
            for row in rows:
                pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
                for i, val in enumerate(row):
                    pdf.cell(col_widths[i], 7, str(val), border=1, align='L', fill=fill)
                pdf.ln()
                fill = not fill
            pdf.ln(6)

        # --- SITE-WISE WORK TABLE ---
        site_rows_pdf = [
            [e['site_id'], e['project_id'], e['site_name'], e.get('status', 'Pending'),
             f"Rs. {e['charge']:,.0f}", f"Rs. {e['approval']:,.0f}",
             f"Rs. {(e['charge'] + e['approval']):,.0f}" if e.get('status') == "Completed" else "-"]
            for e in entries
        ]
        draw_table("SITE-WISE WORK DONE", ["Site ID", "Project ID", "Site Name", "Status", "Charge Amt", "Extra Approval", "Total"],
                   [20, 22, 42, 22, 26, 28, 30], site_rows_pdf, secondary_color)

        # --- PAYMENTS TABLE ---
        payment_rows_pdf = [
            [p.get('pay_date', ''), p.get('pay_from', ''), f"Rs. {num(p.get('amount')):,.0f}"]
            for p in payments
        ]
        if payment_rows_pdf:
            draw_table("PAYMENTS RECEIVED", ["Payment Date", "Paid From", "Amount"],
                       [45, 55, 90], payment_rows_pdf, green_color)

        # --- TOTALS ---
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(10, pdf.get_y(), 190, 28, 'FD')
        pdf.set_y(pdf.get_y() + 5)

        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(*secondary_color)
        pdf.cell(190, 8, f"Total Site Amount: Rs. {total_billed:,.0f}", ln=True, align='L')

        pdf.set_text_color(*green_color)
        pdf.cell(190, 8, f"Total Paid Amount: Rs. {total_paid:,.0f}", ln=True, align='L')

        bal_color = red_color if balance > 0 else green_color
        pdf.set_text_color(*bal_color)
        pdf.cell(190, 8, f"Total Balance: Rs. {balance:,.0f}", ln=True, align='L')

        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, (bytes, bytearray)):
            return bytes(pdf_output)
        return pdf_output.encode('latin1')

    col_dl, col_close = st.columns(2)
    with col_dl:
        try:
            pdf_bytes = generate_team_pdf()
            st.download_button(
                "📄 Download PDF", data=pdf_bytes,
                file_name=f"{team_name}_Solar_Ledger.pdf", mime="application/pdf",
                use_container_width=True, type="primary"
            )
        except Exception as e:
            st.error(str(e))
    with col_close:
        if st.button("Close", use_container_width=True):
            st.rerun()

# --- TOP BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #f59e0b 0%, #ec4899 50%, #8b5cf6 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            ☀️ SOLAR PROJECT — {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 6. FETCH SOLAR SITES (Project Name = Solar) FROM site_data ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_solar_data_cached(workspace):
    """Bundles the 3 core Solar Project queries into one cached call.
    Previously these ran unconditionally on EVERY rerun (every search
    keystroke, every tab switch, every dialog interaction) — now they're
    reused for 30s. Call fetch_solar_data_cached.clear() before st.rerun()
    after saving/deleting a team allocation or a payment."""
    try:
        site_res = supabase.table("site_data").select("*").eq("workspace", workspace).ilike("Project Name", "%solar%").execute()
        site_data_ = site_res.data if site_res.data else []
        site_data_ = [r for r in site_data_ if str(r.get("Project Name", "")).strip().lower() == "solar"]
    except Exception:
        site_data_ = []

    try:
        alloc_res = supabase.table("solar_team_allocation").select("*").eq("workspace", workspace).execute()
        alloc_data_ = alloc_res.data if alloc_res.data else []
    except Exception:
        alloc_data_ = []

    try:
        pay_res = supabase.table("solar_payments").select("*").eq("workspace", workspace).order("id", desc=True).execute()
        solar_payments_data_ = pay_res.data if pay_res.data else []
    except Exception:
        solar_payments_data_ = []

    return site_data_, alloc_data_, solar_payments_data_


active_ws = st.session_state.get('active_workspace', 'VISPL')
site_data, alloc_data, solar_payments_data = fetch_solar_data_cached(active_ws)

if not site_data:
    try:
        all_ws_res = supabase.table("site_data").select("Project Name").eq("workspace", active_ws).execute()
        distinct_pn = sorted(set(str(r.get("Project Name", "")).strip() for r in (all_ws_res.data or []) if str(r.get("Project Name", "")).strip()))
        if distinct_pn:
            st.info(f"ℹ️ Koi 'Solar' site nahi mili. Aapke workspace mein 'Project Name' column ki actual values hain: {', '.join(distinct_pn)}")
    except Exception:
        pass

alloc_map = {row.get("Project ID", ""): row for row in alloc_data}

df = pd.DataFrame(site_data) if site_data else pd.DataFrame(
    columns=["id", "Project ID", "Site ID", "Site Name", "Cluster", "Site Status"]
)

if 'created_at' in df.columns and not df.empty:
    df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.sort_values(by='created_at_dt', ascending=False).drop(columns=['created_at_dt']).reset_index(drop=True)
elif not df.empty:
    df = df.iloc[::-1].reset_index(drop=True)

# --- Build team_entries (used by Ledger + Payments tabs) ---
team_entries = defaultdict(list)
for a in alloc_data:
    for role, role_label in [("civil", "Civil"), ("electrical", "Electrical"), ("transport", "Transporter")]:
        t_name = str(a.get(f"{role}_team_name", "")).strip()
        if not t_name:
            continue
        team_entries[t_name].append({
            "site_id": a.get("Site ID", ""),
            "project_id": a.get("Project ID", ""),
            "site_name": a.get("Site Name", ""),
            "role": role_label,
            "status": a.get(f"{role}_status", "Pending"),
            "charge": num(a.get(f"{role}_charge_amount")),
            "approval": num(a.get(f"{role}_extra_approval_amount")),
            "approval_remark": a.get(f"{role}_extra_approval_remark", ""),
        })

payments_by_team = defaultdict(list)
for p in solar_payments_data:
    payments_by_team[str(p.get("team_name", "")).strip()].append(p)

solar_team_names = sorted(set(team_entries.keys()) | set(payments_by_team.keys()))

# ================================================================
# --- NAVIGATION BAR: SOLAR SITES | TEAM LEDGER | PAYMENTS ---
# (custom buttons, replaces st.tabs for guaranteed styling)
# ================================================================
SOLAR_NAV_PAGES = [
    ("sites", "📍 Solar Sites"),
    ("ledger", "🧾 Team Ledger"),
    ("payments", "💳 Payments"),
]

with st.container(key="solar_nav_bar"):
    nav_cols = st.columns(len(SOLAR_NAV_PAGES))
    for nav_col, (page_id, page_label) in zip(nav_cols, SOLAR_NAV_PAGES):
        is_active = st.session_state.solar_active_page == page_id
        with nav_col:
            if st.button(page_label, key=f"solar_nav_{page_id}", use_container_width=True, type=("primary" if is_active else "secondary")):
                st.session_state.solar_active_page = page_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ================================================================
# PAGE 1: SOLAR SITES
# ================================================================
if st.session_state.solar_active_page == "sites":
    total_sites = len(df)
    civil_total = sum(num(a.get("civil_charge_amount")) for a in alloc_data)
    electrical_total = sum(num(a.get("electrical_charge_amount")) for a in alloc_data)
    transport_total = sum(num(a.get("transport_charge_amount")) for a in alloc_data)
    approval_total = sum(
        num(a.get("civil_extra_approval_amount")) + num(a.get("electrical_extra_approval_amount")) + num(a.get("transport_extra_approval_amount"))
        for a in alloc_data
    )

    st.markdown(
        '<div class="lux-kpi-grid">'
        + kpi_card("☀️", "Total Solar Sites", f"{total_sites:,}", "Project Name = Solar", *KPI_INDIGO)
        + kpi_card("🧱", "Civil Charges", f"₹ {civil_total:,.0f}", "All civil teams", *KPI_AMBER)
        + kpi_card("⚡", "Electrical Charges", f"₹ {electrical_total:,.0f}", "All electrical teams", *KPI_BLUE)
        + kpi_card("🚚", "Transport Charges", f"₹ {transport_total:,.0f}", "All transporters", *KPI_GREEN)
        + kpi_card("📝", "Total Extra Approval", f"₹ {approval_total:,.0f}", "Across all teams", *KPI_PINK)
        + '</div>',
        unsafe_allow_html=True,
    )

    col_title, col_search, col_export, col_toggle = st.columns([4, 2.5, 1.3, 1.5])
    with col_title:
        st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Solar Project Sites</h5>", unsafe_allow_html=True)
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search solar sites...", label_visibility="collapsed", key="solar_search")
    with col_export:
        export_clicked = st.button("📥 Export", use_container_width=True, key="solar_export_btn")
    with col_toggle:
        render_view_toggle("solar_sites_view", "solar_sites_view_toggle")

    df_view = df.copy()
    if search_query and not df_view.empty:
        mask = df_view.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_view = df_view[mask]

    if export_clicked and not df_view.empty:
        rows = []
        for _, r in df_view.iterrows():
            a = alloc_map.get(r.get("Project ID", ""), {})
            rows.append({
                "Project ID": r.get("Project ID", ""),
                "Site ID": r.get("Site ID", ""),
                "Site Name": r.get("Site Name", ""),
                "Cluster": r.get("Cluster", ""),
                "Site Status": r.get("Site Status", ""),
                "Civil Team": a.get("civil_team_name", ""),
                "Civil Status": a.get("civil_status", "Pending"),
                "Civil Charge": num(a.get("civil_charge_amount")),
                "Civil Extra Approval": num(a.get("civil_extra_approval_amount")),
                "Civil Approval Remark": a.get("civil_extra_approval_remark", ""),
                "Electrical Team": a.get("electrical_team_name", ""),
                "Electrical Status": a.get("electrical_status", "Pending"),
                "Electrical Charge": num(a.get("electrical_charge_amount")),
                "Electrical Extra Approval": num(a.get("electrical_extra_approval_amount")),
                "Electrical Approval Remark": a.get("electrical_extra_approval_remark", ""),
                "Transport Team": a.get("transport_team_name", ""),
                "Transport Status": a.get("transport_status", "Pending"),
                "Transport Charge": num(a.get("transport_charge_amount")),
                "Transport Extra Approval": num(a.get("transport_extra_approval_amount")),
                "Transport Approval Remark": a.get("transport_extra_approval_remark", ""),
                "Remarks": a.get("remarks", ""),
            })
        export_df = pd.DataFrame(rows)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Solar Project')
        st.download_button(
            label="📊 Download Solar_Project_Export.xlsx",
            data=buffer.getvalue(),
            file_name="Solar_Project_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="solar_export_dl"
        )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    rows_per_page = 10
    total_rows = len(df_view)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state.solar_current_page > total_pages:
        st.session_state.solar_current_page = total_pages
    elif st.session_state.solar_current_page < 1:
        st.session_state.solar_current_page = 1

    start_idx = (st.session_state.solar_current_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df_view.iloc[start_idx:end_idx].copy()

    if df_page.empty:
        empty_state("Koi Solar site nahi mili. Site Data Hub mein 'Project Name' = Solar select karke site add karein.")

    elif st.session_state.solar_sites_view == "cards":
        # ---------------------------------------------------------------
        # MOBILE CARD VIEW - Solar Sites
        # ---------------------------------------------------------------
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            proj_id = str(row_dict.get("Project ID", ""))
            alloc = alloc_map.get(proj_id, {})
            serial_no = start_idx + page_pos + 1

            civil_charge = num(alloc.get("civil_charge_amount"))
            electrical_charge = num(alloc.get("electrical_charge_amount"))
            transport_charge = num(alloc.get("transport_charge_amount"))
            total_charge = civil_charge + electrical_charge + transport_charge
            total_approval = (
                num(alloc.get("civil_extra_approval_amount")) +
                num(alloc.get("electrical_extra_approval_amount")) +
                num(alloc.get("transport_extra_approval_amount"))
            )

            def status_tag(prefix):
                s = alloc.get(f"{prefix}_status", "Pending")
                return " ✅" if s == "Completed" else (" ⏳" if alloc.get(f"{prefix}_team_name") else "")

            with st.container(border=True):
                st.markdown(f"""
                    <div class="solar-mcard-title">#{serial_no} — {row_dict.get('Site ID','') or '-'} | {row_dict.get('Site Name','') or '-'}</div>
                    <div class="solar-mcard-sub">{proj_id or '-'} • {row_dict.get('Cluster','') or '-'}</div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Site Status</span><span class="solar-mcard-value">{row_dict.get('Site Status','') or '-'}</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Civil Team</span><span class="solar-mcard-value">{(alloc.get('civil_team_name','') or '-')}{status_tag('civil')} (₹{civil_charge:,.0f})</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Electrical Team</span><span class="solar-mcard-value">{(alloc.get('electrical_team_name','') or '-')}{status_tag('electrical')} (₹{electrical_charge:,.0f})</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Transport Team</span><span class="solar-mcard-value">{(alloc.get('transport_team_name','') or '-')}{status_tag('transport')} (₹{transport_charge:,.0f})</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Total Charge</span><span class="solar-mcard-value amber">₹ {total_charge:,.0f}</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Total Approval</span><span class="solar-mcard-value">₹ {total_approval:,.0f}</span></div>
                """, unsafe_allow_html=True)
                if st.button("⚙️ Manage Teams", key=f"card_solar_mgr_{row_dict.get('id')}", use_container_width=True):
                    manage_solar_teams_dialog(row_dict, alloc)

    else:
        # ---------------------------------------------------------------
        # ✨ LAVISH DESKTOP TABLE VIEW
        # ---------------------------------------------------------------
        COL_RATIOS = [0.5, 0.45, 1.1, 1.5, 1.0, 1.2, 1.0,
                      1.6, 0.9, 1.6, 0.9, 1.6, 0.9,
                      1.1, 1.1]
        COL_LABELS = ["⚙️", "#", "SITE ID", "SITE NAME", "CLUSTER", "PROJECT ID", "STATUS",
                      "CIVIL TEAM", "AMT (₹)", "ELECTRICAL TEAM", "AMT (₹)", "TRANSPORT TEAM", "AMT (₹)",
                      "TOTAL CHARGE", "TOTAL APPROVAL"]

        # Total charge of ALL filtered sites (for badge + footer)
        view_total_charge = 0.0
        for _pid in df_view["Project ID"].astype(str) if "Project ID" in df_view.columns else []:
            _a = alloc_map.get(_pid, {})
            view_total_charge += num(_a.get("civil_charge_amount")) + num(_a.get("electrical_charge_amount")) + num(_a.get("transport_charge_amount"))

        table_title_bar("☀️ Solar Site Register", "newest first • scroll right for more →", f"₹ {view_total_charge:,.0f}")

        with st.container(key="solar_table_wrap", height=560):
            table_header_row("solhead_sites", COL_RATIOS, COL_LABELS, center_idx=(0, 1), right_idx=(8, 10, 12, 13, 14))

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                proj_id = str(row_dict.get("Project ID", ""))
                alloc = alloc_map.get(proj_id, {})
                serial_no = start_idx + page_pos + 1
                rid = row_dict.get("id")
                row_key = rid if (rid is not None and str(rid).strip() not in ("", "nan", "None")) else f"s{serial_no}"

                civil_charge = num(alloc.get("civil_charge_amount"))
                electrical_charge = num(alloc.get("electrical_charge_amount"))
                transport_charge = num(alloc.get("transport_charge_amount"))
                total_charge = civil_charge + electrical_charge + transport_charge

                total_approval = (
                    num(alloc.get("civil_extra_approval_amount")) +
                    num(alloc.get("electrical_extra_approval_amount")) +
                    num(alloc.get("transport_extra_approval_amount"))
                )

                parity = "odd" if serial_no % 2 else "even"
                with st.container(key=f"solrow_{parity}_site_{row_key}"):
                    rcols = st.columns(COL_RATIOS, vertical_alignment="center")
                    with rcols[0]:
                        if st.button("⚙️", key=f"solar_mgr_{row_key}", help="Manage Teams"):
                            manage_solar_teams_dialog(row_dict, alloc)
                    rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)
                    rcols[2].markdown(_chip(row_dict.get('Site ID')), unsafe_allow_html=True)
                    rcols[3].markdown(_txt(row_dict.get('Site Name'), "slux-strong"), unsafe_allow_html=True)
                    rcols[4].markdown(_pill(row_dict.get('Cluster')), unsafe_allow_html=True)
                    rcols[5].markdown(_chip(proj_id, "proj"), unsafe_allow_html=True)
                    rcols[6].markdown(status_badge(row_dict.get('Site Status')), unsafe_allow_html=True)
                    rcols[7].markdown(_team_cell(alloc.get('civil_team_name'), alloc.get('civil_status', 'Pending')), unsafe_allow_html=True)
                    rcols[8].markdown(_money(civil_charge), unsafe_allow_html=True)
                    rcols[9].markdown(_team_cell(alloc.get('electrical_team_name'), alloc.get('electrical_status', 'Pending')), unsafe_allow_html=True)
                    rcols[10].markdown(_money(electrical_charge), unsafe_allow_html=True)
                    rcols[11].markdown(_team_cell(alloc.get('transport_team_name'), alloc.get('transport_status', 'Pending')), unsafe_allow_html=True)
                    rcols[12].markdown(_money(transport_charge), unsafe_allow_html=True)
                    rcols[13].markdown(_money(total_charge, "strong"), unsafe_allow_html=True)
                    rcols[14].markdown(_money(total_approval), unsafe_allow_html=True)

        shown_from = start_idx + 1 if total_rows else 0
        shown_to = min(end_idx, total_rows)
        st.markdown(
            '<div class="slux-foot">'
            f'<div>Total {total_rows:,} solar site{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small></div>'
            f'<div class="slux-foot-amts"><span>Total Charge: <b style="color:#4f46e5;">₹ {view_total_charge:,.0f}</b></span>'
            f'<span class="slux-foot-badge">Page {st.session_state.solar_current_page} of {total_pages}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.solar_current_page == 1), key="solar_prev"):
            st.session_state.solar_current_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state.solar_current_page} of {total_pages} (Total Solar Sites: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.solar_current_page == total_pages), key="solar_next"):
            st.session_state.solar_current_page += 1
            st.rerun()

# ================================================================
# PAGE 2: TEAM LEDGER (Team-wise + Site-wise toggle)
# ================================================================
elif st.session_state.solar_active_page == "ledger":
    ledger_view_mode = st.radio("Ledger View:", ["👷 Team Wise", "📍 Site Wise"], horizontal=True, key="ledger_view_mode")
    st.markdown("<br>", unsafe_allow_html=True)

    if ledger_view_mode == "👷 Team Wise":
        ledger_rows = []
        for t_name in solar_team_names:
            entries = team_entries.get(t_name, [])
            completed_entries = [e for e in entries if e.get("status") == "Completed"]
            payments = payments_by_team.get(t_name, [])
            site_ids = set(e["project_id"] for e in completed_entries)
            total_charge = sum(e["charge"] for e in completed_entries)
            total_approval = sum(e["approval"] for e in completed_entries)
            total_billed = total_charge + total_approval
            total_paid = sum(num(p.get("amount")) for p in payments)
            balance = total_billed - total_paid
            ledger_rows.append({
                "Team Name": t_name,
                "Sites Worked": len(site_ids),
                "Total Charge (₹)": total_charge,
                "Total Approval (₹)": total_approval,
                "Total Billed (₹)": total_billed,
                "Total Paid (₹)": total_paid,
                "Balance (₹)": balance,
                "_entries": entries,
                "_payments": payments,
            })

        ledger_rows.sort(key=lambda r: r["Balance (₹)"], reverse=True)

        grand_billed = sum(r["Total Billed (₹)"] for r in ledger_rows)
        grand_paid = sum(r["Total Paid (₹)"] for r in ledger_rows)
        grand_balance = sum(r["Balance (₹)"] for r in ledger_rows)

        st.markdown(
            '<div class="lux-kpi-grid">'
            + kpi_card("👷", "Total Teams", f"{len(ledger_rows):,}", "Civil + Electrical + Transport", *KPI_INDIGO)
            + kpi_card("🧾", "Total Billed", f"₹ {grand_billed:,.0f}", "Completed work only", *KPI_AMBER)
            + kpi_card("💰", "Total Paid", f"₹ {grand_paid:,.0f}", "All payments", *KPI_GREEN, value_cls="green")
            + kpi_card("⏳", "Total Balance", f"₹ {grand_balance:,.0f}", "Billed − Paid", *KPI_RED, value_cls="red")
            + '</div>',
            unsafe_allow_html=True,
        )

        col_title, col_search, col_toggle = st.columns([4.5, 3, 1.5])
        with col_title:
            st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Team-wise Hisaab (Civil + Electrical + Transporter combined)</h5>", unsafe_allow_html=True)
        with col_search:
            ledger_search = st_keyup("Search", placeholder="🔍 Search team...", label_visibility="collapsed", key="ledger_search")
        with col_toggle:
            render_view_toggle("solar_ledger_view", "solar_ledger_view_toggle_team")

        display_rows = ledger_rows
        if ledger_search:
            display_rows = [r for r in ledger_rows if ledger_search.lower() in r["Team Name"].lower()]

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if not display_rows:
            empty_state("Abhi tak kisi bhi team ko Solar site allocate nahi hui. 'Solar Sites' tab se ⚙️ Manage Teams se allocation karein.")

        elif st.session_state.solar_ledger_view == "cards":
            # ---------------------------------------------------------------
            # MOBILE CARD VIEW - Team Ledger (Team Wise)
            # ---------------------------------------------------------------
            for r in display_rows:
                with st.container(border=True):
                    st.markdown(f"""
                        <div class="solar-mcard-title">👷 {r['Team Name']}</div>
                        <div class="solar-mcard-sub">{r['Sites Worked']} site(s) worked</div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Charge</span><span class="solar-mcard-value">₹ {r['Total Charge (₹)']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Approval</span><span class="solar-mcard-value">₹ {r['Total Approval (₹)']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Total Billed</span><span class="solar-mcard-value amber">₹ {r['Total Billed (₹)']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Paid</span><span class="solar-mcard-value paid">₹ {r['Total Paid (₹)']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Balance</span><span class="solar-mcard-value pending">₹ {r['Balance (₹)']:,.0f}</span></div>
                    """, unsafe_allow_html=True)
                    if st.button("👁️ View Detail", key=f"card_ledger_view_{r['Team Name']}", use_container_width=True):
                        view_team_detail_dialog(r["Team Name"], r["_entries"], r["_payments"])

        else:
            LCOL_RATIOS = [0.55, 0.5, 2.0, 0.8, 1.2, 1.2, 1.3, 1.2, 1.3]
            LCOL_LABELS = ["👁️", "#", "TEAM NAME", "SITES", "CHARGE", "APPROVAL", "TOTAL BILLED", "PAID", "BALANCE"]

            table_title_bar("🧾 Team Ledger", "highest balance first", f"Balance ₹ {grand_balance:,.0f}")

            with st.container(key="ledger_table_wrap", height=520):
                table_header_row("solhead_ledger", LCOL_RATIOS, LCOL_LABELS, center_idx=(0, 1, 3), right_idx=(4, 5, 6, 7, 8))

                for idx, r in enumerate(display_rows, start=1):
                    parity = "odd" if idx % 2 else "even"
                    with st.container(key=f"solrow_{parity}_ledger_{idx}"):
                        rcols = st.columns(LCOL_RATIOS, vertical_alignment="center")
                        with rcols[0]:
                            if st.button("👁️", key=f"ledger_view_{r['Team Name']}", help="View Detail"):
                                view_team_detail_dialog(r["Team Name"], r["_entries"], r["_payments"])
                        rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{idx}</span></div>", unsafe_allow_html=True)
                        rcols[2].markdown(f"<div class='slux-cell'><span class='sol-team'>👷 {escape(r['Team Name'])}</span></div>", unsafe_allow_html=True)
                        rcols[3].markdown(f"<div style='text-align:center;'><span class='slux-pill'>{r['Sites Worked']}</span></div>", unsafe_allow_html=True)
                        rcols[4].markdown(_money(r['Total Charge (₹)']), unsafe_allow_html=True)
                        rcols[5].markdown(_money(r['Total Approval (₹)']), unsafe_allow_html=True)
                        rcols[6].markdown(_money(r['Total Billed (₹)'], "strong"), unsafe_allow_html=True)
                        rcols[7].markdown(_money(r['Total Paid (₹)'], "paid"), unsafe_allow_html=True)
                        rcols[8].markdown(_money(r['Balance (₹)'], "due" if r['Balance (₹)'] > 0 else "paid"), unsafe_allow_html=True)

            st.markdown(
                '<div class="slux-foot">'
                f'<div>{len(display_rows):,} team{"s" if len(display_rows) != 1 else ""}</div>'
                '<div class="slux-foot-amts">'
                f'<span>Billed: <b style="color:#4f46e5;">₹ {grand_billed:,.0f}</b></span>'
                f'<span>Paid: <b style="color:#059669;">₹ {grand_paid:,.0f}</b></span>'
                f'<span>Balance: <b style="color:#dc2626;">₹ {grand_balance:,.0f}</b></span>'
                '</div></div>',
                unsafe_allow_html=True,
            )

    else:
        # ---- SITE WISE VIEW ----
        col_title2, col_search2, col_toggle2 = st.columns([4.5, 3, 1.5])
        with col_title2:
            st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Site-wise Hisaab (Kis site pe kaunsi team, kitna amount)</h5>", unsafe_allow_html=True)
        with col_search2:
            site_search = st_keyup("Search", placeholder="🔍 Search site...", label_visibility="collapsed", key="site_ledger_search")
        with col_toggle2:
            render_view_toggle("solar_ledger_view", "solar_ledger_view_toggle_site")

        site_rows = []
        for _, r in df.iterrows():
            proj_id = str(r.get("Project ID", ""))
            a = alloc_map.get(proj_id, {})
            civil_status = a.get("civil_status", "Pending")
            electrical_status = a.get("electrical_status", "Pending")
            transport_status = a.get("transport_status", "Pending")

            civil_charge = num(a.get("civil_charge_amount")) if civil_status == "Completed" else 0.0
            electrical_charge = num(a.get("electrical_charge_amount")) if electrical_status == "Completed" else 0.0
            transport_charge = num(a.get("transport_charge_amount")) if transport_status == "Completed" else 0.0
            total_approval = (
                (num(a.get("civil_extra_approval_amount")) if civil_status == "Completed" else 0.0) +
                (num(a.get("electrical_extra_approval_amount")) if electrical_status == "Completed" else 0.0) +
                (num(a.get("transport_extra_approval_amount")) if transport_status == "Completed" else 0.0)
            )
            total_charge = civil_charge + electrical_charge + transport_charge

            def tag(name, status):
                if not name or name == "-":
                    return "-"
                return f"{name} ✅" if status == "Completed" else f"{name} ⏳"

            site_rows.append({
                "Site ID": r.get("Site ID", "") or "-",
                "Site Name": r.get("Site Name", "") or "-",
                "Cluster": r.get("Cluster", "") or "-",
                "Project ID": proj_id or "-",
                "Civil Team": tag(a.get("civil_team_name", ""), civil_status),
                "Civil Amt": civil_charge,
                "Electrical Team": tag(a.get("electrical_team_name", ""), electrical_status),
                "Electrical Amt": electrical_charge,
                "Transport Team": tag(a.get("transport_team_name", ""), transport_status),
                "Transport Amt": transport_charge,
                "Total Charge": total_charge,
                "Total Approval": total_approval,
                "Grand Total": total_charge + total_approval,
                "_civil": (a.get("civil_team_name", ""), civil_status),
                "_electrical": (a.get("electrical_team_name", ""), electrical_status),
                "_transport": (a.get("transport_team_name", ""), transport_status),
            })

        st.caption("💡 Sirf ✅ Completed status wale kaam ka amount yahan count hota hai. ⏳ = Pending (abhi count nahi hoga).")

        if site_search:
            site_rows = [
                sr for sr in site_rows
                if site_search.lower() in " ".join(str(v) for k, v in sr.items() if not k.startswith("_")).lower()
            ]

        if not site_rows:
            empty_state("Koi Solar site data nahi mila.")

        elif st.session_state.solar_ledger_view == "cards":
            # ---------------------------------------------------------------
            # MOBILE CARD VIEW - Team Ledger (Site Wise)
            # ---------------------------------------------------------------
            for idx, sr in enumerate(site_rows, start=1):
                with st.container(border=True):
                    st.markdown(f"""
                        <div class="solar-mcard-title">#{idx} — {sr['Site ID']} | {sr['Site Name']}</div>
                        <div class="solar-mcard-sub">{sr['Project ID']} • {sr['Cluster']}</div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Civil Team</span><span class="solar-mcard-value">{sr['Civil Team']} (₹{sr['Civil Amt']:,.0f})</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Electrical Team</span><span class="solar-mcard-value">{sr['Electrical Team']} (₹{sr['Electrical Amt']:,.0f})</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Transport Team</span><span class="solar-mcard-value">{sr['Transport Team']} (₹{sr['Transport Amt']:,.0f})</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Total Charge</span><span class="solar-mcard-value">₹ {sr['Total Charge']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Total Approval</span><span class="solar-mcard-value">₹ {sr['Total Approval']:,.0f}</span></div>
                        <div class="solar-mcard-row"><span class="solar-mcard-label">Grand Total</span><span class="solar-mcard-value amber">₹ {sr['Grand Total']:,.0f}</span></div>
                    """, unsafe_allow_html=True)

        else:
            SCOL_RATIOS = [0.45, 1.1, 1.5, 1.0, 1.2, 1.6, 0.9, 1.6, 0.9, 1.6, 0.9, 1.1, 1.1, 1.1]
            SCOL_LABELS = ["#", "SITE ID", "SITE NAME", "CLUSTER", "PROJECT ID",
                           "CIVIL TEAM", "AMT (₹)", "ELECTRICAL TEAM", "AMT (₹)", "TRANSPORT TEAM", "AMT (₹)",
                           "TOTAL CHARGE", "TOTAL APPROVAL", "GRAND TOTAL"]

            site_grand_total = sum(sr["Grand Total"] for sr in site_rows)
            table_title_bar("📍 Site-wise Ledger", "completed work only • scroll right →", f"₹ {site_grand_total:,.0f}")

            with st.container(key="site_ledger_table_wrap", height=560):
                table_header_row("solhead_siteledger", SCOL_RATIOS, SCOL_LABELS, center_idx=(0,), right_idx=(6, 8, 10, 11, 12, 13))

                for idx, sr in enumerate(site_rows, start=1):
                    parity = "odd" if idx % 2 else "even"
                    with st.container(key=f"solrow_{parity}_siteledger_{idx}"):
                        rcols = st.columns(SCOL_RATIOS, vertical_alignment="center")
                        rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{idx}</span></div>", unsafe_allow_html=True)
                        rcols[1].markdown(_chip(sr['Site ID']), unsafe_allow_html=True)
                        rcols[2].markdown(_txt(sr['Site Name'], "slux-strong"), unsafe_allow_html=True)
                        rcols[3].markdown(_pill(sr['Cluster']), unsafe_allow_html=True)
                        rcols[4].markdown(_chip(sr['Project ID'], "proj"), unsafe_allow_html=True)
                        rcols[5].markdown(_team_cell(*sr['_civil']), unsafe_allow_html=True)
                        rcols[6].markdown(_money(sr['Civil Amt']), unsafe_allow_html=True)
                        rcols[7].markdown(_team_cell(*sr['_electrical']), unsafe_allow_html=True)
                        rcols[8].markdown(_money(sr['Electrical Amt']), unsafe_allow_html=True)
                        rcols[9].markdown(_team_cell(*sr['_transport']), unsafe_allow_html=True)
                        rcols[10].markdown(_money(sr['Transport Amt']), unsafe_allow_html=True)
                        rcols[11].markdown(_money(sr['Total Charge']), unsafe_allow_html=True)
                        rcols[12].markdown(_money(sr['Total Approval']), unsafe_allow_html=True)
                        rcols[13].markdown(_money(sr['Grand Total'], "amber"), unsafe_allow_html=True)

            st.markdown(
                '<div class="slux-foot">'
                f'<div>{len(site_rows):,} solar site{"s" if len(site_rows) != 1 else ""}</div>'
                f'<div class="slux-foot-amts"><span>Grand Total: <b style="color:#d97706;">₹ {site_grand_total:,.0f}</b></span></div>'
                '</div>',
                unsafe_allow_html=True,
            )

# ================================================================
# PAGE 3: PAYMENTS
# ================================================================
elif st.session_state.solar_active_page == "payments":
    st.markdown("<h5 style='margin:0 0 10px 0; color:#0f172a;'>💳 Solar Team Payment Entry</h5>", unsafe_allow_html=True)

    if not solar_team_names:
        st.info("Abhi tak koi team Solar site pe allocate nahi hui. Pehle 'Solar Sites' tab se ⚙️ Manage Teams se team allocate karein, phir yahan payment kar sakte ho.")
    else:
        all_dd = get_all_dropdowns()
        pay_from_opts = get_simple_opts("Payment From", all_dd, ["Bank", "Cash"])
        pay_type_opts = get_simple_opts("Payment Type", all_dd, ["NEFT", "RTGS", "UPI"])

        with st.form("solar_payment_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                pay_team = st.selectbox("Pay To (Solar Team) *", solar_team_names)
            with f2:
                pay_from = st.selectbox("Payment From *", pay_from_opts)
            with f3:
                pay_type = st.selectbox("Payment Type *", pay_type_opts)

            f4, f5, f6 = st.columns(3)
            with f4:
                pay_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, value=0.0)
            with f5:
                pay_date = st.date_input("Payment Date", value=datetime.date.today(), format="DD/MM/YYYY")
            with f6:
                pay_remark = st.text_input("Remark", placeholder="e.g. Civil work advance")

            submitted = st.form_submit_button("💾 Save Payment", type="primary", use_container_width=True)

            if submitted:
                if pay_amount <= 0:
                    st.error("⚠️ Amount 0 se zyada hona chahiye!")
                else:
                    try:
                        ws = st.session_state.get('active_workspace', 'VISPL')

                        # 1. Mirror into main Team & Vendor Billing (billing_payments) so it shows there too
                        billing_payload = {
                            "workspace": ws,
                            "pay_from": pay_from,
                            "pay_to": pay_team,
                            "pay_type": pay_type,
                            "amount": pay_amount,
                            "date": str(pay_date),
                            "remark": f"[Solar] {pay_remark}".strip(),
                            "mode": "Team",
                        }
                        billing_res = supabase.table("billing_payments").insert(billing_payload).execute()
                        billing_id = billing_res.data[0].get("id") if (hasattr(billing_res, 'data') and billing_res.data) else None

                        # 2. Save into solar_payments (for Solar Ledger reporting)
                        solar_payload = {
                            "workspace": ws,
                            "team_name": pay_team,
                            "pay_from": pay_from,
                            "pay_type": pay_type,
                            "amount": pay_amount,
                            "pay_date": str(pay_date),
                            "remark": pay_remark,
                            "billing_payment_id": billing_id,
                        }
                        supabase.table("solar_payments").insert(solar_payload).execute()

                        st.success(f"✅ Payment Saved! Yeh Team Billing page ke Payment Entry mein bhi save ho gaya hai.")
                        fetch_solar_data_cached.clear()
                        st.rerun()
                    except Exception as e:
                        err_str = str(e)
                        if "schema cache" in err_str.lower() or "PGRST204" in err_str or "does not exist" in err_str.lower():
                            st.error("❌ 'solar_payments' table nahi mila. Kripya 'solar_setup.sql' script Supabase mein run karein.")
                        else:
                            st.error(f"❌ Error saving payment: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h5 style='margin:0 0 10px 0; color:#0f172a;'>🗄️ Solar Payment History</h5>", unsafe_allow_html=True)

    pcol_search, pcol_export, pcol_toggle = st.columns([5.5, 2, 2])
    with pcol_search:
        payment_search = st_keyup("Search", placeholder="🔍 Search payments...", label_visibility="collapsed", key="solar_payment_search")
    with pcol_export:
        payment_export_clicked = st.button("📥 Export", use_container_width=True, key="solar_payment_export_btn")
    with pcol_toggle:
        render_view_toggle("solar_payments_view", "solar_payments_view_toggle")

    pdf_view = pd.DataFrame(solar_payments_data) if solar_payments_data else pd.DataFrame(
        columns=["id", "team_name", "pay_from", "pay_type", "amount", "pay_date", "remark"]
    )
    if payment_search and not pdf_view.empty:
        mask = pdf_view.astype(str).apply(lambda x: x.str.contains(payment_search, case=False, na=False)).any(axis=1)
        pdf_view = pdf_view[mask]

    if payment_export_clicked and not pdf_view.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            pdf_view.drop(columns=[c for c in ["id", "billing_payment_id", "created_at"] if c in pdf_view.columns]).to_excel(writer, index=False, sheet_name='Solar Payments')
        st.download_button(
            label="📊 Download Solar_Payments.xlsx",
            data=buffer.getvalue(),
            file_name="Solar_Payments.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="solar_payment_export_dl"
        )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if pdf_view.empty:
        empty_state("Abhi tak koi Solar payment record nahi hai.")

    elif st.session_state.solar_payments_view == "cards":
        # ---------------------------------------------------------------
        # MOBILE CARD VIEW - Payment History
        # ---------------------------------------------------------------
        for _, prow in pdf_view.iterrows():
            pd_dict = prow.to_dict()
            with st.container(border=True):
                st.markdown(f"""
                    <div class="solar-mcard-title">{pd_dict.get('team_name','') or '-'}</div>
                    <div class="solar-mcard-sub">{pd_dict.get('pay_date','') or '-'}</div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Paid From</span><span class="solar-mcard-value">{pd_dict.get('pay_from','') or '-'}</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Type</span><span class="solar-mcard-value">{pd_dict.get('pay_type','') or '-'}</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Amount</span><span class="solar-mcard-value paid">₹ {num(pd_dict.get('amount')):,.0f}</span></div>
                    <div class="solar-mcard-row"><span class="solar-mcard-label">Remark</span><span class="solar-mcard-value">{pd_dict.get('remark','') or '-'}</span></div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"card_delpay_{pd_dict.get('id')}", use_container_width=True):
                    try:
                        supabase.table("solar_payments").delete().eq("id", pd_dict["id"]).execute()
                        b_id = pd_dict.get("billing_payment_id")
                        if b_id:
                            supabase.table("billing_payments").delete().eq("id", b_id).execute()
                        st.success("✅ Payment Deleted!")
                        fetch_solar_data_cached.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting: {e}")

    else:
        PCOL_RATIOS = [0.55, 0.5, 1.7, 1.2, 1.1, 1.0, 1.2, 2.4]
        PCOL_LABELS = ["🗑️", "#", "TEAM NAME", "DATE", "PAID FROM", "TYPE", "AMOUNT", "REMARK"]

        pay_total = sum(num(v) for v in pdf_view["amount"]) if "amount" in pdf_view.columns else 0.0
        table_title_bar("💳 Payment History", "newest first", f"₹ {pay_total:,.0f}")

        with st.container(key="payments_table_wrap", height=420):
            table_header_row("solhead_payments", PCOL_RATIOS, PCOL_LABELS, center_idx=(0, 1), right_idx=(6,))

            for idx, (_, prow) in enumerate(pdf_view.iterrows(), start=1):
                pd_dict = prow.to_dict()
                pid = pd_dict.get("id")
                row_key = pid if (pid is not None and str(pid).strip() not in ("", "nan", "None")) else f"p{idx}"
                parity = "odd" if idx % 2 else "even"
                with st.container(key=f"solrow_{parity}_pay_{row_key}"):
                    rcols = st.columns(PCOL_RATIOS, vertical_alignment="center")
                    with rcols[0]:
                        if st.button("🗑️", key=f"delpay_{row_key}", help="Delete"):
                            try:
                                supabase.table("solar_payments").delete().eq("id", pd_dict["id"]).execute()
                                b_id = pd_dict.get("billing_payment_id")
                                if b_id:
                                    supabase.table("billing_payments").delete().eq("id", b_id).execute()
                                st.success("✅ Payment Deleted!")
                                fetch_solar_data_cached.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting: {e}")
                    rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{idx}</span></div>", unsafe_allow_html=True)
                    team_nm = _clean(pd_dict.get('team_name'))
                    rcols[2].markdown(f"<div class='slux-cell'><span class='sol-team'>👷 {escape(team_nm)}</span></div>" if team_nm else _MUTED, unsafe_allow_html=True)
                    rcols[3].markdown(_txt(pd_dict.get('pay_date'), "slux-soft"), unsafe_allow_html=True)
                    rcols[4].markdown(_pill(pd_dict.get('pay_from')), unsafe_allow_html=True)
                    rcols[5].markdown(_chip(pd_dict.get('pay_type')), unsafe_allow_html=True)
                    rcols[6].markdown(_money(pd_dict.get('amount'), "paid"), unsafe_allow_html=True)
                    rcols[7].markdown(_txt(pd_dict.get('remark'), "slux-soft"), unsafe_allow_html=True)

        st.markdown(
            '<div class="slux-foot">'
            f'<div>{len(pdf_view):,} payment{"s" if len(pdf_view) != 1 else ""}</div>'
            f'<div class="slux-foot-amts"><span>Total Paid: <b style="color:#059669;">₹ {pay_total:,.0f}</b></span></div>'
            '</div>',
            unsafe_allow_html=True,
        )
