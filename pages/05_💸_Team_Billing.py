import streamlit as st
import pandas as pd
import datetime
import io
import os
import math
import html
import requests
from supabase import create_client, Client
from st_keyup import st_keyup
import zipfile

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Team & Vendor Billing", page_icon="💸", layout="wide")

# --- INIT SESSION STATE (nav) ---
if 'billing_active_page' not in st.session_state:
    st.session_state.billing_active_page = "invoice"
if 'billing_view_mode' not in st.session_state:
    st.session_state.billing_view_mode = "table"
if 'invoice_sub_tab' not in st.session_state:
    st.session_state.invoice_sub_tab = "team"

# --- 2. ✨ LAVISH CUSTOM CSS (Quotation / Site Data / Invoice jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Tabs Styling */
    button[data-baseweb="tab"] { font-weight: 700 !important; font-size: 1.1rem !important; }

    /* Buttons (support both old "baseButton-*" and newer "stBaseButton-*" testid naming) */
    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"],
    button[kind="primary"], button[kind="primaryFormSubmit"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
        transition: all .2s ease !important;
    }
    button[kind="primary"] p, button[kind="primaryFormSubmit"] p { color: #ffffff !important; font-weight: 800 !important; }
    /* Secondary = clean white/indigo (pehle poori page par RED tha — ab sirf Delete/Reject red hain) */
    button[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"],
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {
        background: #ffffff !important; color: #334155 !important;
        border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important;
        font-weight: 800 !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
        transition: all .2s ease !important;
    }
    button[kind="secondary"] p { color: #334155 !important; font-weight: 800 !important; }
    button[kind="primary"]:hover, button[kind="secondary"]:hover { transform: translateY(-2px) !important; }

    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }

    /* st.dataframe (ledger tables) polish */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border-radius: 16px !important; overflow: hidden !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12), 0 4px 6px -2px rgba(15, 23, 42, 0.05) !important;
        border: 1px solid #e2e8f0 !important; background: #ffffff !important;
    }
    [data-testid="stElementToolbar"] {
        background: #ffffff !important; border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12) !important; border: 1px solid #e2e8f0 !important;
    }

    /* ================= KPI CARDS ================= */
    .lux-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin: 4px 0 22px; }
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
    .lux-kpi-value { font-size: 1.5rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
    .lux-kpi-value.green { color: #059669; }
    .lux-kpi-value.red { color: #dc2626; }
    .lux-kpi-value.blue { color: #4f46e5; }
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

    /* ================= SCROLLING TABLE BODIES (inv / pay / transfer / mrn) ================= */
    div[class*="st-key-"][class*="_table_wrap"] {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    div[class*="_table_wrap"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
    div[class*="_table_wrap"] [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    div[class*="_table_wrap"] [data-testid="stColumn"], div[class*="_table_wrap"] [data-testid="column"] {
        padding: 0 10px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header rows */
    div[class*="st-key-blhead_"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-blhead_"] [data-testid="stColumn"], div[class*="st-key-blhead_"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-blrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-blrow_odd"] { background: #fafaff; }
    div[class*="st-key-blrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-blrow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .85rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
    .slux-wrap { font-size: .85rem; color: #1e293b; white-space: normal; word-break: break-word; line-height: 1.25; width: 100%; }
    .slux-strong { font-weight: 700; color: #0f172a; }
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
        padding: 3px 8px; border-radius: 6px; font-size: .76rem; font-weight: 700; white-space: nowrap;
    }
    .slux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
    .slux-chip.inv { background: #fdf4ff; border-color: #f5d0fe; color: #a21caf; }
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .bl-team { font-weight: 800; color: #b45309; }
    .bl-vendor { font-weight: 800; color: #0e7490; }
    .bl-amt { text-align: right; font-weight: 700; color: #334155; font-variant-numeric: tabular-nums; }
    .bl-amt.zero { color: #cbd5e1; font-weight: 600; }
    .bl-amt.strong { color: #4f46e5; font-weight: 900; font-size: .9rem; }
    .bl-amt.paid { color: #059669; font-weight: 900; }
    .bl-amt.tds { color: #d97706; }
    .status-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 11px; border-radius: 999px; border: 1px solid transparent;
        font-size: .7rem; font-weight: 800; letter-spacing: .4px; white-space: nowrap;
    }
    .status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
    .status-green  { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
    .status-red    { background: #fee2e2; color: #b91c1c; border-color: #fecaca; }
    .status-blue   { background: #dbeafe; color: #1d4ed8; border-color: #bfdbfe; }
    .status-purple { background: #f3e8ff; color: #7e22ce; border-color: #e9d5ff; }

    /* ---- Row action buttons ---- */
    div[class*="st-key-blpop_"] button, div[class*="st-key-reverse_transfer_"] button, div[class*="st-key-reversed_transfer_"] button,
    div[class*="st-key-mrn_app_"] button, div[class*="st-key-mrn_rej_"] button {
        width: 38px !important; max-width: 38px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    /* Single ⚙️ popover (Site Data jaisa) */
    div[class*="st-key-blpop_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-blpop_"] button:hover { background: #3b82f6 !important; border-color: #60a5fa !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important; }
    div[class*="st-key-blpop_"] button p, div[class*="st-key-blpop_"] button span { color: #1e293b !important; }
    div[class*="st-key-blpop_"] button svg { display: none !important; }
    /* ↩️ Revoke transfer (amber) */
    div[class*="st-key-reverse_transfer_"] button { background: rgba(245,158,11,0.15) !important; border: 1px solid rgba(245,158,11,0.35) !important; }
    div[class*="st-key-reverse_transfer_"] button:hover { background: #f59e0b !important; transform: translateY(-2px) !important; }
    /* ✅ Approve (green) / ❌ Reject (red) */
    div[class*="st-key-mrn_app_"] button { background: rgba(16,185,129,0.15) !important; border: 1px solid rgba(16,185,129,0.35) !important; }
    div[class*="st-key-mrn_app_"] button:hover { background: #10b981 !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(16,185,129,.6) !important; }
    div[class*="st-key-mrn_rej_"] button { background: rgba(239,68,68,0.12) !important; border: 1px solid rgba(239,68,68,0.3) !important; }
    div[class*="st-key-mrn_rej_"] button:hover { background: #ef4444 !important; transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(239,68,68,.6) !important; }
    /* Red "Yes, Delete" inside confirm dialogs + card delete/reject buttons */
    div[class*="st-key-bl_del_yes"] button, div[class*="st-key-invc_del_"] button, div[class*="st-key-payc_del_"] button, div[class*="st-key-mrnc_rej_"] button {
        background: linear-gradient(90deg, #ef4444, #dc2626) !important; border: none !important;
    }
    div[class*="st-key-bl_del_yes"] button p, div[class*="st-key-invc_del_"] button p, div[class*="st-key-payc_del_"] button p, div[class*="st-key-mrnc_rej_"] button p { color: #ffffff !important; }

    /* Footer bar */
    .slux-foot {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45); margin-bottom: 20px;
        font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .slux-foot-amts { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; text-transform: none; letter-spacing: 0; }
    .slux-foot-amts span { font-size: .95rem; }
    .slux-empty {
        background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
        text-align: center; color: #64748b; font-weight: 600;
    }
    .slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }

    /* =========================================================
       MOBILE CARD VIEW (light theme)
       ========================================================= */
    .billing-card-title { font-size: 1.02rem; font-weight: 800; color: #312e81; margin-bottom: 2px; }
    .billing-card-sub { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .billing-card-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; }
    .billing-card-row:last-child { border-bottom: none; }
    .billing-card-label { color: #64748b; font-weight: 700; text-transform: uppercase; font-size: .75rem; }
    .billing-card-value { color: #1e293b; font-weight: 600; text-align: right; }

    /* Dialog/Popup Premium Styling */
    div[data-testid="stDialog"] > div {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2 {
        color: #1e293b !important; font-weight: 800 !important; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px;
    }
    .gst-highlight { color: #10b981; font-weight: 800; font-size: 1.1rem; }
    .total-highlight { color: #3b82f6; font-weight: 900; font-size: 1.8rem; }

    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    div[data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; border-color: transparent !important;
    }
    div[data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* ================= PAGE NAVIGATION BAR ================= */
    .st-key-billing_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-billing_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 16px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important; box-shadow: none !important;
    }
    .st-key-billing_nav_bar button[kind="secondary"] { background: #ffffff !important; color: #475569 !important; border: 1.5px solid #e2e8f0 !important; }
    .st-key-billing_nav_bar button[kind="secondary"]:hover { background: #f1f5f9 !important; color: #0f172a !important; border-color: #cbd5e1 !important; transform: translateY(-2px) !important; }
    .st-key-billing_nav_bar button[kind="secondary"] p,
    .st-key-billing_nav_bar button[kind="secondary"] span,
    .st-key-billing_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; font-size: 1.05rem !important; }
    .st-key-billing_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
    }
    .st-key-billing_nav_bar button[kind="primary"] p,
    .st-key-billing_nav_bar button[kind="primary"] span,
    .st-key-billing_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; font-size: 1.05rem !important; }

    /* ================= INVOICE SUB-TAB BAR ================= */
    .st-key-invoice_sub_tab_bar div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
    .st-key-invoice_sub_tab_bar button {
        font-size: 0.92rem !important; font-weight: 800 !important; padding: 10px 8px !important;
        height: auto !important; border-radius: 10px !important; box-shadow: none !important;
    }
    .st-key-invoice_sub_tab_bar button[kind="secondary"] { background: #ffffff !important; color: #475569 !important; border: 1.5px solid #e2e8f0 !important; }
    .st-key-invoice_sub_tab_bar button[kind="secondary"] p,
    .st-key-invoice_sub_tab_bar button[kind="secondary"] span,
    .st-key-invoice_sub_tab_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-invoice_sub_tab_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35) !important;
    }
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

# --- INTERAKT WHATSAPP API SETUP ---
INTERAKT_API_KEY = "S2pFcE5ETjE2NDhiQ1VIMEFjMVA5a3ZwdHB6X0diYXpRM2I2SWRxbGJWYzo="

def get_mobile_number(category, name):
    try:
        res = supabase.table("dropdown_master").select("mobile").eq("category", category).eq("option_value", name).eq("is_active", True).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("mobile", "")
    except Exception:
        pass
    return ""

def get_pan_number(category, name):
    try:
        res = supabase.table("dropdown_master").select("pan").eq("category", category).eq("option_value", name).eq("is_active", True).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("pan", "")
    except Exception:
        pass
    return ""

def fetch_mrn_items(invoice_no, workspace):
    """Fetch mrn_items rows for a given MRN/Invoice Number, with fallbacks in case
    of workspace mismatches or extra whitespace/case differences in the MRN Number
    (some MRNs were failing to match on an exact + workspace-scoped query)."""
    inv_clean = str(invoice_no or "").strip()
    if not inv_clean:
        return []

    # 1) Exact match, scoped to the current workspace
    try:
        res = supabase.table("mrn_items").select("*").eq("MRN Number", inv_clean).eq("workspace", workspace).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    # 2) Exact match, without the workspace filter (in case workspace was recorded differently)
    try:
        res = supabase.table("mrn_items").select("*").eq("MRN Number", inv_clean).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    # 3) Case-insensitive / whitespace-tolerant match as a last resort
    try:
        res = supabase.table("mrn_items").select("*").ilike("MRN Number", inv_clean).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    return []

def send_interakt_whatsapp(mobile, template_name, params):
    if not mobile or not INTERAKT_API_KEY:
        return
    
    url = "https://api.interakt.ai/v1/public/message/"
    headers = {
        "Authorization": f"Basic {INTERAKT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    mob = str(mobile).replace("+91", "").replace(" ", "").strip()
    if len(mob) < 10: return
    
    clean_params = [str(p).strip() if str(p).strip() else "-" for p in params]
    
    payload = {
        "countryCode": "+91",
        "phoneNumber": mob,
        "type": "Template",
        "template": {
            "name": template_name,
            "languageCode": "hi",
            "bodyValues": clean_params
        }
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=5)
    except Exception:
        pass

# --- AMOUNT TO WORDS CONVERTER (INDIAN SYSTEM) ---
def cell(val):
    """Safely render a table cell value: None / NaN / 'nan' string all become '-'."""
    if val is None:
        return "-"
    try:
        if isinstance(val, float) and pd.isna(val):
            return "-"
    except Exception:
        pass
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none", "nat"):
        return "-"
    return s


def _parse_any_date(val):
    """Dialog default date: ISO (2026-09-05) ya table wala DD/MM/YYYY dono sahi padhta hai.
    FIX: pehle table se aaya '05/09/2026' month-first padha jaata tha (9 May),
    isliye Edit karke Save karne par invoice/payment ki DATE badal jaati thi."""
    s = str(val or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return datetime.date.today()

def number_to_words(n):
    if n is None or pd.isna(n):
        return ""
    n = int(n)
    if n == 0:
        return ""
        
    words = { 1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
        11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', 15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', 19: 'Nineteen',
        20: 'Twenty', 30: 'Thirty', 40: 'Forty', 50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', 90: 'Ninety' }
    
    def num_to_words_below_1000(num):
        if num == 0: return ""
        elif num < 20: return words[num]
        elif num < 100: return words[num - num % 10] + (" " + words[num % 10] if num % 10 != 0 else "")
        else: return words[num // 100] + " Hundred" + (" and " + num_to_words_below_1000(num % 100) if num % 100 != 0 else "")

    res = ""
    if n >= 10000000:
        res += num_to_words_below_1000(n // 10000000) + " Crore "
        n %= 10000000
    if n >= 100000:
        res += num_to_words_below_1000(n // 100000) + " Lakh "
        n %= 100000
    if n >= 1000:
        res += num_to_words_below_1000(n // 1000) + " Thousand "
        n %= 1000
    if n > 0:
        res += num_to_words_below_1000(n)
        
    return res.strip() + " Rupees Only"

# --- VISIONTECH FIXED COMPANY DETAILS (used inside Bill To / Ship To block) ---
VISIONTECH_ADDRESS_LINES = [
    "Near Vikas Mitra Madal Chowk, Survey No 8/9/7, House No 81",
    "Santkrupa Building, Canal Road, Lane Number 2, Karve Nagar,",
    "Pune, Pune, Maharashtra, 411052",
]
VISIONTECH_GSTIN = "27AAICV3205F1ZI"
VISIONTECH_PAN = "AAICV3205F"

# --- INVOICE PDF GENERATOR (fully in-memory — NEVER saved/uploaded to Supabase) ---
def _wrap_text_for_pdf(pdf, text, width_mm):
    """Wrap text within width_mm, including long IDs that contain no spaces."""
    usable_width = max(float(width_mm) - 2.0, 1.0)
    words = str(text).replace("\r", "").split(" ")
    lines = []
    current = ""

    def split_long_word(word):
        """Hard-wrap a single token (Project ID, Site ID, etc.) by width."""
        pieces = []
        piece = ""
        for char in str(word):
            test_piece = piece + char
            if piece and pdf.get_string_width(test_piece) > usable_width:
                pieces.append(piece)
                piece = char
            else:
                piece = test_piece
        if piece or not pieces:
            pieces.append(piece)
        return pieces

    for w in words:
        if "\n" in w:
            parts = w.split("\n")
        else:
            parts = [w]

        expanded_parts = []
        for part in parts:
            expanded_parts.extend(split_long_word(part))

        for part_index, part in enumerate(expanded_parts):
            w = part
            test = (current + " " + w).strip()
            if pdf.get_string_width(test) <= usable_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w

            # Preserve an explicit newline from the source text.
            if len(parts) > 1 and part_index < len(expanded_parts) - 1:
                if current:
                    lines.append(current)
                current = ""
    if current:
        lines.append(current)
    return lines or [""]


def _draw_items_table_header(pdf, widths, continued=False):
    """Draw the item-table heading on the first page and every continuation page."""
    if continued:
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 7, "INVOICE - CONTINUED", align='C', ln=True)
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(37, 60, 122)
    pdf.set_text_color(255, 255, 255)
    headers = ["SR", "ITEM CODE", "ITEM DESCRIPTION", "QTY", "PRICE (Rs.)", "TOTAL (Rs.)"]
    for heading, width in zip(headers, widths):
        pdf.cell(width, 8, heading, border=1, align='C', fill=True)
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)


def _draw_item_row(pdf, sr, item_code, desc, qty, price, total, widths, line_h=4):
    """Draw one item-table row with word-wrapped description; all columns share the row's total height."""
    pdf.set_font("Arial", '', 8)
    desc_lines = _wrap_text_for_pdf(pdf, desc, widths[2])
    row_height = max(1, len(desc_lines)) * line_h

    # Never allow multi_cell() to start a row that cannot fit on the current
    # page. Otherwise FPDF moves only the description to a new page and the
    # remaining cells are drawn using the old page coordinates.
    page_bottom = pdf.h - pdf.b_margin
    if pdf.get_y() + row_height > page_bottom:
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        _draw_items_table_header(pdf, widths, continued=True)

    x0 = pdf.get_x()
    y0 = pdf.get_y()

    pdf.cell(widths[0], row_height, str(sr), border=1, align='C')
    pdf.set_font("Arial", '', 7)
    pdf.cell(widths[1], row_height, str(item_code), border=1, align='C')
    pdf.set_font("Arial", '', 8)

    pdf.set_xy(x0 + widths[0] + widths[1], y0)
    pdf.multi_cell(widths[2], line_h, str(desc), border=1, align='L')

    pdf.set_xy(x0 + widths[0] + widths[1] + widths[2], y0)
    pdf.cell(widths[3], row_height, str(qty), border=1, align='C')
    pdf.cell(widths[4], row_height, f"{price:,.2f}", border=1, align='R')
    pdf.cell(widths[5], row_height, f"{total:,.2f}", border=1, align='R')

    pdf.set_xy(x0, y0 + row_height)


def generate_invoice_pdf(row_dict):
    if FPDF is None:
        raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")

    invoice_type = str(row_dict.get("invoice_type", "") or "").strip()
    if invoice_type == "Vendor" and str(row_dict.get("vendor_name", "") or "").strip():
        entity_name = str(row_dict.get("vendor_name")).strip()
    else:
        entity_name = str(row_dict.get("team_name", "") or "").strip() or "TEAM"

    invoice_no = str(row_dict.get("invoice_no", "") or "-")
    date_raw = row_dict.get("date", "")
    try:
        if not date_raw:
            date_fmt = "-"
        elif isinstance(date_raw, (datetime.date, datetime.datetime, pd.Timestamp)):
            date_fmt = pd.Timestamp(date_raw).strftime("%d-%b-%Y")
        else:
            date_text = str(date_raw).strip()
            parsed_date = None
            for date_pattern in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    parsed_date = datetime.datetime.strptime(date_text[:10], date_pattern)
                    break
                except ValueError:
                    continue
            if parsed_date is None:
                parsed_date = pd.to_datetime(date_text, dayfirst=True, errors="raise")
            date_fmt = parsed_date.strftime("%d-%b-%Y")
    except Exception:
        date_fmt = str(date_raw) or "-"
    project_id = str(row_dict.get("project_id", "") or "-")
    site_id = str(row_dict.get("site_id", "") or "-")
    site_name = str(row_dict.get("site_name", "") or "-")
    cluster = str(row_dict.get("cluster", "") or "-")
    remark = str(row_dict.get("remark", "") or "-")

    try:
        basic_amt = float(row_dict.get("basic_amount") or 0)
    except Exception:
        basic_amt = 0.0
    try:
        total_amt = float(row_dict.get("amount") or basic_amt)
    except Exception:
        total_amt = basic_amt

    # --- Fetch MRN line items (PO Number, Item Code, Description, Qty, Price, Total) ---
    ws_val = row_dict.get("workspace") or st.session_state.get('active_workspace', 'VISPL')
    mrn_items_rows = fetch_mrn_items(invoice_no, ws_val)

    try:
        entity_mobile = get_mobile_number(
            "Vendor Name" if invoice_type == "Vendor" else "Team Name", entity_name
        ) or "-"
    except Exception:
        entity_mobile = "-"

    try:
        entity_pan = get_pan_number(
            "Vendor Name" if invoice_type == "Vendor" else "Team Name", entity_name
        ) or "-"
    except Exception:
        entity_pan = "-"

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- HEADER: Team / Vendor Name (big, blue, centered) ---
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 12, entity_name.upper(), align='C', ln=True)
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
    pdf.ln(6)

    # --- INVOICE title bar ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(190, 9, "INVOICE", border=1, align='C', ln=True)

    # --- Bill To / Ship To (left = Visiontech) + Entity Info (right) box ---
    box_top = pdf.get_y()
    box_height = 50
    pdf.rect(10, box_top, 190, box_height)
    pdf.line(105, box_top, 105, box_top + box_height)

    left_x = 12
    pdf.set_xy(left_x, box_top + 2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(90, 5, "Bill To : Visiontech Infra Solution Pvt. Ltd.", ln=2)
    pdf.set_x(left_x)
    pdf.set_font("Arial", '', 8)
    addr_block = "\n".join(VISIONTECH_ADDRESS_LINES) + f"\nGSTIN/UIN : {VISIONTECH_GSTIN}\nPAN : {VISIONTECH_PAN}"
    pdf.multi_cell(90, 4, addr_block)
    pdf.ln(1)
    pdf.set_x(left_x)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(90, 5, "Ship To : Visiontech Infra Solution Pvt. Ltd.", ln=2)
    pdf.set_x(left_x)
    pdf.set_font("Arial", '', 8)
    pdf.multi_cell(90, 4, "\n".join(VISIONTECH_ADDRESS_LINES) + f"\nGSTIN/UIN : {VISIONTECH_GSTIN}")

    right_x = 107
    pdf.set_xy(right_x, box_top + 2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(90, 5, entity_name, ln=2)
    pdf.set_x(right_x)
    pdf.set_font("Arial", '', 8)
    pdf.multi_cell(90, 4, f"Contact : {entity_name}\nMobile : {entity_mobile}\nPAN : {entity_pan}")

    pdf.set_y(box_top + box_height + 2)

    # --- Invoice detail table ---
    detail_rows = [
        ("Invoice Number", invoice_no, "MRN Date", date_fmt),
        ("Project ID", project_id, "Site ID", site_id),
        ("Site Name", site_name, "Cluster", cluster),
        ("Remark", "Tower Work", "Place of Supply", "Maharashtra, Code : 27"),
    ]
    row_h = 7
    for label1, val1, label2, val2 in detail_rows:
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(35, row_h, label1, border=1, fill=True)
        pdf.set_font("Arial", '', 8)
        pdf.cell(60, row_h, val1, border=1)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(35, row_h, label2, border=1, fill=True)
        pdf.set_font("Arial", '', 8)
        pdf.cell(60, row_h, val2, border=1, ln=True)

    pdf.ln(4)

    # --- Items table: real MRN line items when available, else a single fallback row ---
    widths = [10, 40, 53, 15, 32, 40]
    _draw_items_table_header(pdf, widths)

    if mrn_items_rows:
        gross_value = 0.0
        for idx, it in enumerate(mrn_items_rows, start=1):
            i_code = it.get("Item Code", "-")
            i_desc = it.get("Description", "-")
            try:
                i_qty_raw = float(it.get("User Qty") or 0)
                i_qty = int(i_qty_raw) if i_qty_raw.is_integer() else i_qty_raw
            except Exception:
                i_qty = it.get("User Qty", "-")
            try:
                i_price = float(it.get("Adjusted Price") or 0)
            except Exception:
                i_price = 0.0
            try:
                i_total = float(it.get("Total") or 0)
            except Exception:
                i_total = 0.0
            gross_value += i_total
            _draw_item_row(pdf, idx, i_code, i_desc, i_qty, i_price, i_total, widths)
    else:
        gross_value = basic_amt
        _draw_item_row(pdf, 1, "-", "Tower Work", 1, basic_amt, basic_amt, widths)

    # Keep totals, amount-in-words and signature together instead of leaving
    # a totals fragment at the bottom of an items page.
    if pdf.get_y() + 76 > pdf.h - pdf.b_margin:
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "INVOICE SUMMARY", align='C', ln=True)
        pdf.ln(3)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(150, 8, "Gross Invoice Value", border=1, align='R')
    pdf.cell(40, 8, f"{gross_value:,.2f}", border=1, align='R', ln=True)

    # TDS applies only to Team/work bills. Vendor bills are material supply bills.
    tds_applicable = invoice_type != "Vendor"
    tds_amt = gross_value * 0.01 if tds_applicable else 0.0
    net_payable = gross_value - tds_amt

    if tds_applicable:
        pdf.set_font("Arial", '', 9)
        pdf.cell(150, 8, "Less: TDS 1%", border=1, align='R')
        pdf.cell(40, 8, f"{tds_amt:,.2f}", border=1, align='R', ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"Net Payable : Rs. {net_payable:,.2f}", align='R', ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 6, "Amount In Words :")
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(150, 6, f"INR {number_to_words(net_payable)}")

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, f"for {entity_name}", align='R', ln=True)
    pdf.ln(24)
    pdf.cell(0, 6, "Authorised Signatory", align='R', ln=True)

    raw = pdf.output(dest='S')
    return bytes(raw) if isinstance(raw, (bytearray, bytes)) else raw.encode('latin1')

# --- 4. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=60, show_spinner=False)
def get_dropdown_data(category_name):
    try:
        res = supabase.table("dropdown_master").select("option_value").eq("category", category_name).eq("is_active", True).execute()
        if res.data:
            return [r["option_value"] for r in res.data]
    except Exception as e:
        pass
    return []

team_list = get_dropdown_data("Team Name") or ["No Teams Available"]
vendor_list = get_dropdown_data("Vendor Name") or ["No Vendors Available"]
pay_from_list = get_dropdown_data("Payment From") or ["Bank", "Cash"]
pay_type_list = get_dropdown_data("Payment Type") or ["NEFT", "RTGS", "UPI"]


# --- 5. POPUP DIALOGS FOR INVOICES ---
@st.dialog("📝 Team Invoice Entry", width="large")
def team_invoice_dialog(row_data=None):
    is_new = row_data is None
    
    def_team = row_data.get("team_name", team_list[0]) if not is_new else team_list[0]
    def_inv = row_data.get("invoice_no", "") if not is_new else ""
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = _parse_any_date(def_date_str)
    
    c1, c2, c3 = st.columns(3)
    team_val = c1.selectbox("Team Name *", options=team_list, index=team_list.index(def_team) if def_team in team_list else 0)
    inv_no = c2.text_input("Invoice No *", value=def_inv)
    
    is_duplicate = False
    if inv_no:
        try:
            ws_active = st.session_state.get('active_workspace', 'VISPL')
            dup_res = supabase.table("billing_invoices").select("id").eq("workspace", ws_active).eq("invoice_no", inv_no).execute()
            if dup_res.data:
                if is_new:
                    is_duplicate = True
                else:
                    if any(r['id'] != row_data['id'] for r in dup_res.data):
                        is_duplicate = True
            
            if is_duplicate:
                st.markdown("<span style='color:#ef4444; font-weight:800; font-size:0.9rem;'>⚠️ This invoice number is already exist in CRM.</span>", unsafe_allow_html=True)
        except Exception:
            pass

    inv_date = c3.date_input("Invoice Date", value=def_date, format="DD/MM/YYYY")
    
    c4, c5, c6, c7 = st.columns(4)
    proj_id = c4.text_input("Project ID", value=row_data.get("project_id", "") if not is_new else "")
    site_id = c5.text_input("Site ID", value=row_data.get("site_id", "") if not is_new else "")
    site_name = c6.text_input("Site Name", value=row_data.get("site_name", "") if not is_new else "")
    cluster = c7.text_input("Cluster", value=row_data.get("cluster", "") if not is_new else "")
    
    c8, c9, c10, c11 = st.columns(4)
    remark = c8.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    b_amt = row_data.get("basic_amount") if not is_new else None
    g_amt = row_data.get("gst_amount") if not is_new else None
    
    start_basic = float(b_amt) if b_amt is not None and not math.isnan(b_amt) else None
    
    if start_basic and start_basic > 0 and g_amt is not None and not math.isnan(g_amt):
        start_gst_perc = (float(g_amt) / start_basic) * 100
    else:
        start_gst_perc = None

    basic_amt = c9.number_input("Basic Amount (₹)", min_value=0.0, step=1.0, value=start_basic, placeholder="0")
    safe_basic = basic_amt if basic_amt is not None else 0.0
    
    if safe_basic > 0:
        c9.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_basic)}</div>", unsafe_allow_html=True)

    gst_perc = c10.number_input("GST (%)", min_value=0.0, step=1.0, value=start_gst_perc, placeholder="0")
    safe_gst = gst_perc if gst_perc is not None else 0.0
    
    gst_amt = safe_basic * (safe_gst / 100)
    total_calc = safe_basic + gst_amt

    tds_calc = total_calc * 0.01
    net_payable_calc = total_calc - tds_calc

    c11.markdown(f"**GST Amount:**<br><span class='gst-highlight'>₹ {gst_amt:,.0f}</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:right; margin-top:8px;'><span style='font-weight:700; color:#64748b;'>Less: TDS (1%): </span><span style='color:#f59e0b; font-weight:800; font-size:1.05rem;'>₹ {tds_calc:,.0f}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:right; margin-top:10px; margin-bottom:15px;'><span style='font-size:1.2rem; font-weight:700; color:#64748b;'>Grand Total (After TDS): </span><span class='total-highlight'>₹ {net_payable_calc:,.0f}</span><br><span style='color:#ef4444; font-weight:800; font-size:0.95rem;'>{number_to_words(net_payable_calc)}</span></div>", unsafe_allow_html=True)

    # --- MRN LINE ITEMS (read-only, fetched live from mrn_items by Invoice/MRN Number) ---
    st.markdown("---")
    st.markdown("<div style='color:#4338ca; font-weight:800; font-size:0.85rem; letter-spacing:1px; text-transform:uppercase; margin-bottom:10px;'>📦 MRN Line Items</div>", unsafe_allow_html=True)

    mrn_items_dialog_rows = []
    if inv_no:
        ws_items = st.session_state.get('active_workspace', 'VISPL')
        mrn_items_dialog_rows = fetch_mrn_items(inv_no, ws_items)

    if mrn_items_dialog_rows:
        df_mrn_items = pd.DataFrame(mrn_items_dialog_rows)
        rename_map = {
            "PO Number": "PO Number",
            "Item Code": "Item Code",
            "Description": "Item Description",
            "Adjusted Price": "Price",
            "User Qty": "Qty",
            "Total": "Total",
        }
        show_cols = [c for c in rename_map if c in df_mrn_items.columns]
        df_mrn_show = df_mrn_items[show_cols].rename(columns=rename_map)
        st.dataframe(df_mrn_show, hide_index=True, use_container_width=True)

        gross_items_val = float(df_mrn_items["Total"].sum()) if "Total" in df_mrn_items.columns else 0.0
        tds_items_val = gross_items_val * 0.01
        net_items_val = gross_items_val - tds_items_val

        mi1, mi2, mi3 = st.columns(3)
        mi1.markdown(f"<div style='text-align:center; background:#f8fafc; border:1px solid #e0e7ff; border-radius:12px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>Gross Invoice Value</span><br><span style='font-size:1.15rem; font-weight:800; color:#3b82f6;'>₹ {gross_items_val:,.0f}</span></div>", unsafe_allow_html=True)
        mi2.markdown(f"<div style='text-align:center; background:#f8fafc; border:1px solid #e0e7ff; border-radius:12px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>TDS (1%)</span><br><span style='font-size:1.15rem; font-weight:800; color:#f59e0b;'>₹ {tds_items_val:,.0f}</span></div>", unsafe_allow_html=True)
        mi3.markdown(f"<div style='text-align:center; background:#f8fafc; border:1px solid #e0e7ff; border-radius:12px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>Net Payable</span><br><span style='font-size:1.15rem; font-weight:800; color:#10b981;'>₹ {net_items_val:,.0f}</span></div>", unsafe_allow_html=True)
    else:
        st.caption("No MRN line items found for this Invoice/MRN number.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 Save Team Invoice", type="primary", use_container_width=True):
        if not inv_no:
            st.error("⚠️ Invoice No is required!")
        elif is_duplicate:
            st.error("⚠️ Cannot Save! This invoice number already exists in CRM.")
        else:
            payload = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "invoice_type": "Team",
                "team_name": team_val,
                "amount": total_calc,
                "basic_amount": safe_basic,
                "gst_amount": gst_amt,
                "date": str(inv_date),
                "project_id": proj_id,
                "site_id": site_id,
                "site_name": site_name,
                "invoice_no": inv_no,
                "vendor_name": "",
                "remark": remark,
                "cluster": cluster
            }
            try:
                if is_new:
                    supabase.table("billing_invoices").insert(payload).execute()
                else:
                    supabase.table("billing_invoices").update(payload).eq("id", row_data["id"]).execute()
                
                st.success("✅ Team Invoice Saved Successfully!")
                fetch_billing_invoices_cached.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

@st.dialog("📝 Vendor Invoice Entry", width="large")
def vendor_invoice_dialog(row_data=None):
    is_new = row_data is None
    
    def_vendor = row_data.get("vendor_name", vendor_list[0]) if not is_new else vendor_list[0]
    def_team = row_data.get("team_name", team_list[0]) if not is_new else team_list[0]
    def_inv = row_data.get("invoice_no", "") if not is_new else ""
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = _parse_any_date(def_date_str)
    
    c1, c2, c3 = st.columns(3)
    vendor_val = c1.selectbox("Vendor Name *", options=vendor_list, index=vendor_list.index(def_vendor) if def_vendor in vendor_list else 0)
    inv_no = c2.text_input("Invoice No *", value=def_inv)
    
    is_duplicate = False
    if inv_no:
        try:
            ws_active = st.session_state.get('active_workspace', 'VISPL')
            dup_res = supabase.table("billing_invoices").select("id").eq("workspace", ws_active).eq("invoice_no", inv_no).execute()
            if dup_res.data:
                if is_new:
                    is_duplicate = True
                else:
                    if any(r['id'] != row_data['id'] for r in dup_res.data):
                        is_duplicate = True
            
            if is_duplicate:
                st.markdown("<span style='color:#ef4444; font-weight:800; font-size:0.9rem;'>⚠️ This invoice number is already exist in CRM.</span>", unsafe_allow_html=True)
        except Exception:
            pass

    inv_date = c3.date_input("Invoice Date", value=def_date, format="DD/MM/YYYY")
    
    c4, c5, c6, c7 = st.columns(4)
    team_val = c4.selectbox("Link to Team *", options=team_list, index=team_list.index(def_team) if def_team in team_list else 0)
    remark = c5.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    b_amt = row_data.get("basic_amount") if not is_new else None
    g_amt = row_data.get("gst_amount") if not is_new else None
    
    start_basic = float(b_amt) if b_amt is not None and not math.isnan(b_amt) else None
    
    if start_basic and start_basic > 0 and g_amt is not None and not math.isnan(g_amt):
        start_gst_perc = (float(g_amt) / start_basic) * 100
    else:
        start_gst_perc = None

    basic_amt = c6.number_input("Basic Amount (₹)", min_value=0.0, step=1.0, value=start_basic, placeholder="0")
    safe_basic = basic_amt if basic_amt is not None else 0.0
    
    if safe_basic > 0:
        c6.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_basic)}</div>", unsafe_allow_html=True)

    gst_perc = c7.number_input("GST (%)", min_value=0.0, step=1.0, value=start_gst_perc, placeholder="0")
    
    safe_gst = gst_perc if gst_perc is not None else 0.0
    
    gst_amt = safe_basic * (safe_gst / 100)
    total_calc = safe_basic + gst_amt
    
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg,#f5f3ff,#eef2ff); padding: 15px; border-radius: 12px; margin-top: 10px; margin-bottom: 20px; border: 1px solid #c7d2fe;'>
            <div><span style='font-weight:700; color:#64748b;'>GST Amount:</span> <span class='gst-highlight'>₹ {gst_amt:,.0f}</span></div>
            <div style='text-align:right;'><span style='font-size:1.2rem; font-weight:700; color:#64748b;'>Grand Total: </span><span class='total-highlight'>₹ {total_calc:,.0f}</span><br><span style='color:#ef4444; font-weight:800; font-size:0.95rem;'>{number_to_words(total_calc)}</span></div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("💾 Save Vendor Invoice", type="primary", use_container_width=True):
        if not inv_no:
            st.error("⚠️ Invoice No is required!")
        elif is_duplicate:
            st.error("⚠️ Cannot Save! This invoice number already exists in CRM.")
        else:
            payload = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "invoice_type": "Vendor",
                "team_name": team_val,
                "amount": total_calc,
                "basic_amount": safe_basic,
                "gst_amount": gst_amt,
                "date": str(inv_date),
                "project_id": "", "site_id": "", "site_name": "", "cluster": "",
                "invoice_no": inv_no,
                "vendor_name": vendor_val,
                "remark": remark
            }
            try:
                if is_new:
                    supabase.table("billing_invoices").insert(payload).execute()
                else:
                    supabase.table("billing_invoices").update(payload).eq("id", row_data["id"]).execute()
                
                st.success("✅ Vendor Invoice Saved Successfully!")
                fetch_billing_invoices_cached.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

@st.dialog("💳 Payment Entry", width="large")
def payment_dialog(row_data=None, mode="Team"):
    is_new = row_data is None
    
    def_from = row_data.get("pay_from", pay_from_list[0]) if not is_new else (pay_from_list[0] if pay_from_list else "")
    
    pay_to_opts = team_list if mode == "Team" else vendor_list
    def_to = row_data.get("pay_to", pay_to_opts[0]) if not is_new else (pay_to_opts[0] if pay_to_opts else "")
    
    def_type = row_data.get("pay_type", pay_type_list[0]) if not is_new else (pay_type_list[0] if pay_type_list else "")
    
    def_date_str = row_data.get("date", str(datetime.date.today())) if not is_new else str(datetime.date.today())
    def_date = _parse_any_date(def_date_str)
    
    p1, p2, p3 = st.columns(3)
    pay_from = p1.selectbox("Payment From *", options=pay_from_list, index=pay_from_list.index(def_from) if def_from in pay_from_list else 0)
    pay_to = p2.selectbox("Pay To *", options=pay_to_opts, index=pay_to_opts.index(def_to) if def_to in pay_to_opts else 0)
    pay_type = p3.selectbox("Payment Type *", options=pay_type_list, index=pay_type_list.index(def_type) if def_type in pay_type_list else 0)
    
    p4, p5, p6 = st.columns(3)
    start_amount = float(row_data.get("amount", 0.0)) if not is_new else None
    pay_amt = p4.number_input("Amount (₹)", min_value=0.0, step=1.0, value=start_amount, placeholder="0")
    safe_pay_amt = pay_amt if pay_amt is not None else 0.0
    
    if safe_pay_amt > 0:
        p4.markdown(f"<div style='color:#ef4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>{number_to_words(safe_pay_amt)}</div>", unsafe_allow_html=True)
    
    pay_date = p5.date_input("Payment Date", value=def_date, format="DD/MM/YYYY")
    pay_remark = p6.text_input("Remark", value=row_data.get("remark", "") if not is_new else "")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(f"💾 Save {mode} Payment", type="primary", use_container_width=True):
        if pay_amt is None or pay_amt <= 0:
            st.error("⚠️ Amount must be greater than zero!")
        else:
            try:
                payload = {
                    "workspace": st.session_state.get('active_workspace', 'VISPL'),
                    "pay_from": pay_from,
                    "pay_to": pay_to,
                    "pay_type": pay_type,
                    "amount": pay_amt,
                    "date": str(pay_date),
                    "remark": pay_remark,
                    "mode": mode
                }
                if is_new:
                    supabase.table("billing_payments").insert(payload).execute()
                else:
                    supabase.table("billing_payments").update(payload).eq("id", row_data["id"]).execute()
                
                try:
                    cat = "Team Name" if mode == "Team" else "Vendor Name"
                    mob = get_mobile_number(cat, pay_to)
                    if mob:
                        wa_date_str = pay_date.strftime("%d/%m/%Y")
                        wa_params = [pay_to, pay_from, pay_type, str(int(pay_amt)), wa_date_str]
                        send_interakt_whatsapp(mob, "paymentinfo", wa_params) 
                except:
                    pass

                st.success(f"✅ {mode} Payment Saved Successfully!")
                fetch_billing_payments_cached.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

@st.dialog("🔄 Team Material Transfer", width="large")
def team_material_transfer_dialog():
    c1, c2 = st.columns(2)
    from_team = c1.selectbox("Material Given By (From Team) *", options=team_list, key="mt_from_team")
    to_options = [name for name in team_list if name != from_team]
    to_team = c2.selectbox("Material Received By (To Team) *", options=to_options, key="mt_to_team")

    c3, c4, c5 = st.columns(3)
    transfer_date = c3.date_input("Transfer Date *", value=datetime.date.today(), format="DD/MM/YYYY", key="mt_date")
    reference_no = c4.text_input("Challan / Reference No.", key="mt_reference")
    amount = c5.number_input("Material Value (₹) *", min_value=0.0, step=1.0, value=None, placeholder="0", key="mt_amount")

    c6, c7 = st.columns([2, 1])
    material_description = c6.text_input("Material Description *", placeholder="Example: GI Pole, Battery, Cable...", key="mt_description")
    quantity = c7.text_input("Quantity", placeholder="Example: 5 Nos / 100 Kg", key="mt_quantity")
    remark = st.text_area("Remark", placeholder="Optional note...", key="mt_remark")

    st.info("From Team के ledger में amount जुड़ेगा और To Team के ledger से उतना ही amount घटेगा।")

    if st.button("💾 Save Material Transfer", type="primary", use_container_width=True, key="mt_save"):
        if not to_options:
            st.error("कम-से-कम दो Team होना आवश्यक है।")
        elif from_team == to_team:
            st.error("From Team और To Team अलग होने चाहिए।")
        elif not material_description.strip():
            st.error("Material Description डालें।")
        elif amount is None or amount <= 0:
            st.error("Material Value zero से ज्यादा होना चाहिए।")
        else:
            try:
                supabase.table("team_material_transfers").insert({
                    "workspace": st.session_state.get("active_workspace", "VISPL"),
                    "transfer_date": str(transfer_date),
                    "from_team": from_team,
                    "to_team": to_team,
                    "reference_no": reference_no.strip() or None,
                    "material_description": material_description.strip(),
                    "quantity": quantity.strip() or None,
                    "amount": amount,
                    "remark": remark.strip() or None,
                    "status": "Active",
                }).execute()
                fetch_team_material_transfers_cached.clear()
                fetch_ledger_data_cached.clear()
                st.success("✅ Material Transfer दोनों Team ledgers में दर्ज हो गया।")
                st.rerun()
            except Exception as e:
                st.error(f"Material Transfer save error: {e}")


# --- NEW: DELETE CONFIRMATION DIALOGS (pehle ek click me turant delete ho jaata tha) ---
def _confirm_box(title, sub):
    st.markdown(
        f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
<div style="font-weight:900;color:#991b1b;font-size:1rem;">{html.escape(str(title))}</div>
<div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">{html.escape(str(sub))}</div>
</div>
<p style="color:#475569;">Ye record permanently delete ho jayega. Kya aap sure hain?</p>""",
        unsafe_allow_html=True,
    )

@st.dialog("🗑️ Delete Invoice")
def delete_invoice_dialog(row_dict):
    rid = row_dict.get("id")
    entity = row_dict.get("vendor_name") if str(row_dict.get("invoice_type", "")).strip() == "Vendor" else row_dict.get("team_name")
    amt = pd.to_numeric(row_dict.get("amount"), errors="coerce")
    _confirm_box(
        f"Invoice {cell(row_dict.get('invoice_no'))}",
        f"{cell(entity)} • {cell(row_dict.get('date'))} • ₹ {(0 if pd.isna(amt) else amt):,.0f}",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="bl_del_no_inv", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="bl_del_yes_inv", use_container_width=True):
            try:
                supabase.table("billing_invoices").delete().eq("id", rid).execute()
                st.success("✅ Deleted successfully!")
                fetch_billing_invoices_cached.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {e}")

@st.dialog("🗑️ Delete Payment")
def delete_payment_dialog(row_dict):
    rid = row_dict.get("id")
    amt = pd.to_numeric(row_dict.get("amount"), errors="coerce")
    _confirm_box(
        f"Payment to {cell(row_dict.get('pay_to'))}",
        f"{cell(row_dict.get('date'))} • {cell(row_dict.get('pay_type'))} • ₹ {(0 if pd.isna(amt) else amt):,.0f}",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="bl_del_no_pay", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="bl_del_yes_pay", use_container_width=True):
            try:
                supabase.table("billing_payments").delete().eq("id", rid).execute()
                st.success("✅ Deleted successfully!")
                fetch_billing_payments_cached.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {e}")

# --- 6. MAIN PAGE NAVIGATION (custom buttons, replaces st.tabs for guaranteed styling) ---
st.markdown("<h1 style='color:#0f172a; margin-bottom: 20px;'>💸 Team & Vendor Billing</h1>", unsafe_allow_html=True)

BILLING_NAV_PAGES = [
    ("invoice", "📄 Invoice Entry"),
    ("payment", "💳 Payment Entry"),
    ("transfer", "🔄 Material Transfer"),
    ("ledger", "📊 Ledger Reports"),
    ("mrn", "🕒 Pending MRN Approval"),
]

with st.container(key="billing_nav_bar"):
    nav_cols = st.columns(len(BILLING_NAV_PAGES))
    for nav_col, (page_id, page_label) in zip(nav_cols, BILLING_NAV_PAGES):
        is_active = st.session_state.billing_active_page == page_id
        with nav_col:
            if st.button(page_label, key=f"billing_nav_{page_id}", use_container_width=True, type=("primary" if is_active else "secondary")):
                st.session_state.billing_active_page = page_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

col_viewtoggle_space, col_viewtoggle = st.columns([5, 2])
with col_viewtoggle:
    toggle_label = "📱 Mobile View" if st.session_state.billing_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="billing_view_toggle"):
        st.session_state.billing_view_mode = "cards" if st.session_state.billing_view_mode == "table" else "table"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_billing_invoices_cached(workspace):
    try:
        inv_res = supabase.table("billing_invoices").select("*").eq("workspace", workspace).order("id", desc=True).execute()
        return inv_res.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_billing_payments_cached(workspace):
    try:
        pay_res = supabase.table("billing_payments").select("*").eq("workspace", workspace).order("id", desc=True).execute()
        return pay_res.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_team_material_transfers_cached(workspace):
    try:
        result = supabase.table("team_material_transfers").select("*").eq("workspace", workspace).order("transfer_date", desc=True).order("id", desc=True).execute()
        return result.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_ledger_data_cached(workspace, rep_mode, inv_col, sel_name):
    try:
        res_inv = supabase.table("billing_invoices").select("*").eq("workspace", workspace).eq("invoice_type", rep_mode).eq(inv_col, sel_name).order("id", desc=True).execute()
        inv_rows = res_inv.data or []
    except Exception:
        inv_rows = []
    try:
        res_pay = supabase.table("billing_payments").select("*").eq("workspace", workspace).eq("mode", rep_mode).eq("pay_to", sel_name).order("id", desc=True).execute()
        pay_rows = res_pay.data or []
    except Exception:
        pay_rows = []
    return inv_rows, pay_rows


@st.cache_data(ttl=30, show_spinner=False)
def fetch_pending_mrn_cached(workspace):
    try:
        p_res = supabase.table("pending_billing_invoices").select("*").eq("workspace", workspace).order("id", desc=True).execute()
        return p_res.data or []
    except Exception:
        return []


# ================================================================
# --- ✨ LAVISH TABLE RENDER HELPERS ---
# ================================================================
_MUTED = "<div class='slux-cell'><span class='slux-muted'>—</span></div>"

def _num(v):
    n = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(n) else float(n)

def _txt(v, extra_cls=""):
    s = cell(v)
    if s == "-":
        return _MUTED
    e = html.escape(s)
    return f"<div class='slux-cell {extra_cls}' title='{e}'>{e}</div>"

def _wrap(v, extra_cls=""):
    s = cell(v)
    if s == "-":
        return _MUTED
    return f"<div class='slux-wrap {extra_cls}'>{html.escape(s)}</div>"

def _chip(v, extra_cls=""):
    s = cell(v)
    if s == "-":
        return _MUTED
    e = html.escape(s)
    return f"<div class='slux-cell' title='{e}'><span class='slux-chip {extra_cls}'>{e}</span></div>"

def _pill(v):
    s = cell(v)
    if s == "-":
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-pill'>{html.escape(s)}</span></div>"

def _money(v, style=""):
    n = _num(v)
    if n is None:
        return "<div class='slux-cell bl-amt zero'>—</div>"
    cls = "zero" if n == 0 and not style else style
    return f"<div class='slux-cell bl-amt {cls}'>₹ {n:,.0f}</div>"

def _entity(v, kind="team"):
    s = cell(v)
    if s == "-":
        return _MUTED
    icon = "👷" if kind == "team" else "🏭"
    cls = "bl-team" if kind == "team" else "bl-vendor"
    e = html.escape(s)
    return f"<div class='slux-cell' title='{e}'><span class='{cls}'>{icon} {e}</span></div>"

def _badge(text, color):
    return f"<div class='slux-cell'><span class='status-badge status-{color}'>{html.escape(str(text))}</span></div>"

def _serial(n):
    return f"<div style='text-align:center;'><span class='slux-num'>{n}</span></div>"

def kpi_card(icon, label, value, foot, accent, soft, value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

KPI_INDIGO = ("linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
KPI_GREEN = ("linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5")
KPI_AMBER = ("linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb")
KPI_PINK = ("linear-gradient(90deg,#ec4899,#a855f7)", "#fdf2f8")
KPI_RED = ("linear-gradient(90deg,#ef4444,#f97316)", "#fef2f2")
KPI_BLUE = ("linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")

def kpi_grid(*cards):
    st.markdown('<div class="lux-kpi-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)

def table_title_bar(title, subtitle, badge):
    st.markdown(
        '<div class="slux-head-bar">'
        f'<div class="slux-title">{title}<span>{subtitle}</span></div>'
        f'<div class="slux-badge">{badge}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

def table_min_width_css(wrap_key, min_width):
    st.markdown(
        f"<style>.st-key-{wrap_key} [data-testid='stHorizontalBlock'],"
        f".st-key-{wrap_key} div[class*='st-key-blhead_'],"
        f".st-key-{wrap_key} div[class*='st-key-blrow_'] {{ min-width: {min_width}px !important; }}</style>",
        unsafe_allow_html=True,
    )

def table_header_row(key, ratios, labels, center_idx=(), right_idx=()):
    with st.container(key=key):
        h_cols = st.columns(ratios, vertical_alignment="center")
        for i, (h_col, label) in enumerate(zip(h_cols, labels)):
            cls = " c" if i in center_idx else (" r" if i in right_idx else "")
            h_col.markdown(f"<div class='slux-th{cls}' title='{label}'>{label}</div>", unsafe_allow_html=True)

def table_footer(left_html, right_html=""):
    st.markdown(f'<div class="slux-foot"><div>{left_html}</div><div class="slux-foot-amts">{right_html}</div></div>', unsafe_allow_html=True)

def empty_state(msg):
    st.markdown(f'<div class="slux-empty"><div>🗂️</div>{html.escape(msg)}</div>', unsafe_allow_html=True)

def _sum_col(df, col):
    if df is None or df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


# ==========================================
# PAGE 1: INVOICE ENTRY
# ==========================================
if st.session_state.billing_active_page == "invoice":
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    try:
        inv_data_raw_all = fetch_billing_invoices_cached(active_ws)
    except Exception:
        inv_data_raw_all = []

    # --- Team Invoices / Vendor Invoices sub-tabs ---
    INVOICE_SUB_TABS = [("team", "👥 Team Invoices"), ("vendor", "🏭 Vendor Invoices")]
    with st.container(key="invoice_sub_tab_bar"):
        sub_cols = st.columns(len(INVOICE_SUB_TABS))
        for sub_col, (tab_id, tab_label) in zip(sub_cols, INVOICE_SUB_TABS):
            is_active_sub = st.session_state.invoice_sub_tab == tab_id
            with sub_col:
                if st.button(tab_label, key=f"invoice_sub_{tab_id}", use_container_width=True, type=("primary" if is_active_sub else "secondary")):
                    st.session_state.invoice_sub_tab = tab_id
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    active_invoice_type = "Team" if st.session_state.invoice_sub_tab == "team" else "Vendor"
    inv_data_raw = [r for r in inv_data_raw_all if str(r.get("invoice_type", "")).strip() == active_invoice_type]

    is_vendor_tab = active_invoice_type == "Vendor"
    inv_filter_col = "vendor_name" if is_vendor_tab else "team_name"
    inv_filter_all = "All Vendors" if is_vendor_tab else "All Teams"
    inv_team_opts = [inv_filter_all]
    if inv_data_raw:
        _entities = sorted(set(str(r.get(inv_filter_col, "")).strip() for r in inv_data_raw if str(r.get(inv_filter_col, "")).strip()))
        inv_team_opts += _entities

    col_search, col_teamfilter, col_addbtn, col_dl, col_zip = st.columns([2.6, 1.8, 1.6, 1.4, 1.8])

    with col_search:
        search_inv = st_keyup("Search", placeholder="🔍 Search Invoices...", label_visibility="collapsed", key="search_inv_input")
    with col_teamfilter:
        team_filter_inv = st.selectbox(
            "Vendor Filter" if is_vendor_tab else "Team Filter",
            options=inv_team_opts,
            label_visibility="collapsed",
            key=f"inv_entity_filter_{active_invoice_type.lower()}"
        )
    with col_addbtn:
        if st.session_state.invoice_sub_tab == "team":
            if st.button("➕ Add Team Invoice", type="primary", use_container_width=True):
                team_invoice_dialog()
        else:
            if st.button("➕ Add Vendor Invoice", type="primary", use_container_width=True):
                vendor_invoice_dialog()

    st.markdown("<br>", unsafe_allow_html=True)

    try:
        if inv_data_raw:
            df_inv = pd.DataFrame(inv_data_raw)

            if team_filter_inv and team_filter_inv != inv_filter_all and inv_filter_col in df_inv.columns:
                df_inv = df_inv[df_inv[inv_filter_col].astype(str).str.strip() == team_filter_inv]

            if search_inv:
                mask = df_inv.astype(str).apply(lambda x: x.str.contains(search_inv, case=False, na=False)).any(axis=1)
                df_inv = df_inv[mask]

            with col_dl:
                if is_vendor_tab:
                    vendor_export_columns = {
                        "vendor_name": "Vendor Name",
                        "invoice_no": "Invoice No.",
                        "date": "Invoice Date",
                        "basic_amount": "Basic Amount",
                        "gst_amount": "GST Amount",
                        "amount": "Total Amount",
                        "team_name": "Team Name",
                        "remark": "Remark",
                    }
                    export_df = df_inv.reindex(columns=list(vendor_export_columns)).rename(columns=vendor_export_columns)
                else:
                    export_df = df_inv
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Invoices')
                st.download_button(label="📥 Excel", data=buffer.getvalue(), file_name="Invoices_List.xlsx", use_container_width=True, type="secondary", key="dl_inv_btn")

            with col_zip:
                if team_filter_inv and team_filter_inv != inv_filter_all and not df_inv.empty:
                    try:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            used_names = set()
                            for _, zrow in df_inv.iterrows():
                                zrow_dict = zrow.to_dict()
                                try:
                                    zpdf_bytes = generate_invoice_pdf(zrow_dict)
                                except Exception:
                                    continue
                                base_name = str(zrow_dict.get("invoice_no", "") or "invoice").replace("/", "-").replace(" ", "_")
                                fname = f"Invoice_{base_name}.pdf"
                                n = 1
                                while fname in used_names:
                                    fname = f"Invoice_{base_name}_{n}.pdf"
                                    n += 1
                                used_names.add(fname)
                                zf.writestr(fname, zpdf_bytes)
                        zip_file_label = team_filter_inv.replace(" ", "_")
                        st.download_button(
                            label="📦 All PDFs (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{zip_file_label}_Invoices.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key="dl_inv_zip_btn"
                        )
                    except Exception as e:
                        st.button("📦 All PDFs (ZIP)", disabled=True, use_container_width=True, key="dl_inv_zip_btn_err", help=f"Error: {e}")
                else:
                    st.button("📦 All PDFs (ZIP)", disabled=True, use_container_width=True, key="dl_inv_zip_btn_disabled", help="Select a specific team above to enable bulk PDF download")

            # --- KPI CARDS (filter + search ke hisaab se) ---
            k_count = len(df_inv)
            k_basic = _sum_col(df_inv, "basic_amount")
            k_gst = _sum_col(df_inv, "gst_amount")
            k_total = _sum_col(df_inv, "amount")
            if is_vendor_tab:
                kpi_grid(
                    kpi_card("🏭", "Vendor Invoices", f"{k_count:,}", "Filtered results" if (search_inv or team_filter_inv != inv_filter_all) else "All records", *KPI_INDIGO),
                    kpi_card("📦", "Basic Amount", f"₹ {k_basic:,.0f}", "Before GST", *KPI_BLUE),
                    kpi_card("🏛️", "GST Amount", f"₹ {k_gst:,.0f}", "Total GST", *KPI_PINK),
                    kpi_card("💰", "Total Amount", f"₹ {k_total:,.0f}", "No TDS on vendor bills", *KPI_GREEN, value_cls="green"),
                )
            else:
                k_tds = k_total * 0.01
                kpi_grid(
                    kpi_card("👥", "Team Invoices", f"{k_count:,}", "Filtered results" if (search_inv or team_filter_inv != inv_filter_all) else "All records", *KPI_INDIGO),
                    kpi_card("📦", "Basic Amount", f"₹ {k_basic:,.0f}", f"GST ₹ {k_gst:,.0f}", *KPI_BLUE),
                    kpi_card("✂️", "TDS (1%)", f"₹ {k_tds:,.0f}", "Deducted", *KPI_AMBER),
                    kpi_card("💰", "Net Payable", f"₹ {k_total - k_tds:,.0f}", "After TDS", *KPI_GREEN, value_cls="green"),
                )

            if not df_inv.empty:
                if "date" in df_inv.columns:
                    df_inv["date"] = pd.to_datetime(df_inv["date"], errors="coerce").dt.strftime('%d/%m/%Y')

                df_inv = df_inv.reset_index(drop=True)

                if st.session_state.billing_view_mode == "cards":
                    # ---------------------------------------------------------------
                    # MOBILE CARD VIEW
                    # ---------------------------------------------------------------
                    for pos, (_, row) in enumerate(df_inv.iterrows()):
                        row_dict = row.to_dict()
                        rid = row_dict.get("id")
                        basic_v = row_dict.get('basic_amount')
                        gst_v = row_dict.get('gst_amount')
                        amt_v = row_dict.get('amount')
                        is_vendor_invoice = str(row_dict.get('invoice_type', '')).strip() == 'Vendor'
                        if pd.notna(amt_v):
                            tds_v = 0.0 if is_vendor_invoice else amt_v * 0.01
                            net_v = amt_v - tds_v
                        else:
                            tds_v = None
                            net_v = None

                        with st.container(border=True):
                            st.markdown(f"""
                                <div class="billing-card-title">#{pos + 1} — {html.escape(cell(row_dict.get('vendor_name') if is_vendor_invoice else row_dict.get('team_name')))}</div>
                                <div class="billing-card-sub">{html.escape(cell(row_dict.get('invoice_no')))} • {cell(row_dict.get('date'))}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Project ID</span><span class="billing-card-value">{html.escape(cell(row_dict.get('project_id')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site ID</span><span class="billing-card-value">{html.escape(cell(row_dict.get('site_id')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site Name</span><span class="billing-card-value">{html.escape(cell(row_dict.get('site_name')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Cluster</span><span class="billing-card-value">{html.escape(cell(row_dict.get('cluster')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Basic Amount</span><span class="billing-card-value">{'₹ %s' % format(basic_v, ',.0f') if pd.notna(basic_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">GST Amount</span><span class="billing-card-value">{'₹ %s' % format(gst_v, ',.0f') if pd.notna(gst_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">TDS (1%)</span><span class="billing-card-value">{'Not Applicable' if is_vendor_invoice else ('₹ %s' % format(tds_v, ',.0f') if tds_v is not None else '-')}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Total (Net)</span><span class="billing-card-value" style="color:#4f46e5;font-weight:800;">{'₹ %s' % format(net_v, ',.0f') if net_v is not None else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">{'Team' if is_vendor_invoice else 'Vendor'}</span><span class="billing-card-value">{html.escape(cell(row_dict.get('team_name') if is_vendor_invoice else row_dict.get('vendor_name')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{html.escape(cell(row_dict.get('remark')))}</span></div>
                            """, unsafe_allow_html=True)

                            bc1, bc2, bc3 = st.columns(3)
                            with bc1:
                                if st.button("⚙️ Manage", key=f"invc_mgr_{rid}", use_container_width=True):
                                    if row_dict.get("invoice_type") == "Team":
                                        team_invoice_dialog(row_dict)
                                    else:
                                        vendor_invoice_dialog(row_dict)
                            with bc2:
                                try:
                                    pdf_bytes_card = generate_invoice_pdf(row_dict)
                                    file_no_card = str(row_dict.get("invoice_no", "") or "invoice").replace("/", "-").replace(" ", "_")
                                    st.download_button(
                                        "📥 PDF", data=pdf_bytes_card, file_name=f"Invoice_{file_no_card}.pdf",
                                        mime="application/pdf", key=f"invc_dl_{rid}", use_container_width=True
                                    )
                                except Exception:
                                    st.button("📥 PDF", key=f"invc_dl_{rid}", disabled=True, use_container_width=True)
                            with bc3:
                                if st.button("🗑️ Delete", key=f"invc_del_{rid}", use_container_width=True):
                                    delete_invoice_dialog(row_dict)
                else:
                    # ---------------------------------------------------------------
                    # ✨ LAVISH DESKTOP TABLE VIEW — single ⚙️ button at row start
                    # ---------------------------------------------------------------
                    if is_vendor_tab:
                        INV_COL_RATIOS = [0.55, 0.5, 1.6, 1.3, 1.0, 1.1, 1.0, 1.2, 1.4, 1.8]
                        INV_COL_LABELS = ["⚙️", "#", "VENDOR NAME", "INVOICE NO.", "INVOICE DATE", "BASIC AMOUNT", "GST AMOUNT", "TOTAL AMOUNT", "TEAM NAME", "REMARK"]
                        right_idx = (5, 6, 7)
                        min_w = 1500
                    else:
                        INV_COL_RATIOS = [0.55, 0.5, 1.3, 1.2, 0.95, 1.4, 1.0, 1.3, 1.0, 1.0, 0.95, 0.9, 1.1, 1.1, 1.4]
                        INV_COL_LABELS = ["⚙️", "#", "TEAM", "INVOICE NO.", "DATE", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC AMT", "GST AMT", "TDS", "TOTAL (NET)", "VENDOR", "REMARK"]
                        right_idx = (9, 10, 11, 12)
                        min_w = 2000

                    view_net = k_total if is_vendor_tab else k_total * 0.99
                    table_min_width_css("inv_table_wrap", min_w)
                    table_title_bar(
                        "🏭 Vendor Invoice Register" if is_vendor_tab else "👥 Team Invoice Register",
                        "newest first • scroll right for more →",
                        f"₹ {view_net:,.0f}",
                    )

                    with st.container(key="inv_table_wrap", height=520):
                        table_header_row("blhead_inv", INV_COL_RATIOS, INV_COL_LABELS, center_idx=(0, 1), right_idx=right_idx)

                        for pos, (_, row) in enumerate(df_inv.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            parity = "odd" if (pos + 1) % 2 else "even"

                            with st.container(key=f"blrow_{parity}_inv_{rid}"):
                                rcols = st.columns(INV_COL_RATIOS, vertical_alignment="center")

                                with rcols[0]:
                                    with st.container(key=f"blpop_inv_{rid}"):
                                        with st.popover("⚙️"):
                                            if st.button("✏️ Edit Invoice", key=f"inv_mgr_{rid}", use_container_width=True):
                                                if row_dict.get("invoice_type") == "Team":
                                                    team_invoice_dialog(row_dict)
                                                else:
                                                    vendor_invoice_dialog(row_dict)
                                            try:
                                                pdf_bytes_row = generate_invoice_pdf(row_dict)
                                                file_no_row = str(row_dict.get("invoice_no", "") or "invoice").replace("/", "-").replace(" ", "_")
                                                st.download_button(
                                                    "📥 Download PDF", data=pdf_bytes_row, file_name=f"Invoice_{file_no_row}.pdf",
                                                    mime="application/pdf", key=f"inv_dl_{rid}", use_container_width=True
                                                )
                                            except Exception:
                                                st.button("📥 PDF Error", key=f"inv_dl_{rid}", use_container_width=True, disabled=True)
                                            if st.button("🗑️ Delete Invoice", key=f"inv_del_{rid}", use_container_width=True):
                                                delete_invoice_dialog(row_dict)

                                rcols[1].markdown(_serial(pos + 1), unsafe_allow_html=True)

                                basic_v = row_dict.get('basic_amount')
                                gst_v = row_dict.get('gst_amount')
                                amt_v = row_dict.get('amount')

                                if is_vendor_tab:
                                    rcols[2].markdown(_entity(row_dict.get('vendor_name'), "vendor"), unsafe_allow_html=True)
                                    rcols[3].markdown(_chip(row_dict.get('invoice_no'), "inv"), unsafe_allow_html=True)
                                    rcols[4].markdown(_txt(row_dict.get('date'), "slux-soft"), unsafe_allow_html=True)
                                    rcols[5].markdown(_money(basic_v), unsafe_allow_html=True)
                                    rcols[6].markdown(_money(gst_v), unsafe_allow_html=True)
                                    rcols[7].markdown(_money(amt_v, "strong"), unsafe_allow_html=True)
                                    rcols[8].markdown(_entity(row_dict.get('team_name'), "team"), unsafe_allow_html=True)
                                    rcols[9].markdown(_wrap(row_dict.get('remark'), "slux-soft"), unsafe_allow_html=True)
                                else:
                                    rcols[2].markdown(_entity(row_dict.get('team_name'), "team"), unsafe_allow_html=True)
                                    rcols[3].markdown(_chip(row_dict.get('invoice_no'), "inv"), unsafe_allow_html=True)
                                    rcols[4].markdown(_txt(row_dict.get('date'), "slux-soft"), unsafe_allow_html=True)
                                    rcols[5].markdown(_chip(row_dict.get('project_id'), "proj"), unsafe_allow_html=True)
                                    rcols[6].markdown(_chip(row_dict.get('site_id')), unsafe_allow_html=True)
                                    rcols[7].markdown(_txt(row_dict.get('site_name'), "slux-strong"), unsafe_allow_html=True)
                                    rcols[8].markdown(_pill(row_dict.get('cluster')), unsafe_allow_html=True)
                                    rcols[9].markdown(_money(basic_v), unsafe_allow_html=True)
                                    rcols[10].markdown(_money(gst_v), unsafe_allow_html=True)
                                    amt_n = _num(amt_v)
                                    if amt_n is not None:
                                        rcols[11].markdown(_money(amt_n * 0.01, "tds"), unsafe_allow_html=True)
                                        rcols[12].markdown(_money(amt_n * 0.99, "strong"), unsafe_allow_html=True)
                                    else:
                                        rcols[11].markdown(_money(None), unsafe_allow_html=True)
                                        rcols[12].markdown(_money(None), unsafe_allow_html=True)
                                    rcols[13].markdown(_txt(row_dict.get('vendor_name')), unsafe_allow_html=True)
                                    rcols[14].markdown(_txt(row_dict.get('remark'), "slux-soft"), unsafe_allow_html=True)

                    table_footer(
                        f'{len(df_inv):,} invoice{"s" if len(df_inv) != 1 else ""}',
                        f'<span>Basic: <b style="color:#334155;">₹ {k_basic:,.0f}</b></span>'
                        + ("" if is_vendor_tab else f'<span>TDS: <b style="color:#d97706;">₹ {k_total * 0.01:,.0f}</b></span>')
                        + f'<span>{"Total" if is_vendor_tab else "Net"}: <b style="color:#4f46e5;">₹ {view_net:,.0f}</b></span>',
                    )
            else:
                empty_state("No invoices match your search.")
        else:
            empty_state("No invoices found. Click the buttons above to add one.")
            with col_dl:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_inv_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

# ==========================================
# PAGE 2: PAYMENT ENTRY
# ==========================================
elif st.session_state.billing_active_page == "payment":
    col_search_p, col_tpbtn, col_vpbtn, col_dl_p = st.columns([4, 2, 2, 2])
    with col_search_p:
        search_pay = st_keyup("Search", placeholder="🔍 Search Payments...", label_visibility="collapsed", key="search_pay_input")
    with col_tpbtn:
        if st.button("➕ Add Team Payment", type="primary", use_container_width=True):
            payment_dialog(mode="Team")
    with col_vpbtn:
        if st.button("➕ Add Vendor Payment", type="primary", use_container_width=True):
            payment_dialog(mode="Vendor")
            
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        pay_data_raw = fetch_billing_payments_cached(active_ws)
        if pay_data_raw:
            df_pay = pd.DataFrame(pay_data_raw)
            
            if search_pay:
                mask_p = df_pay.astype(str).apply(lambda x: x.str.contains(search_pay, case=False, na=False)).any(axis=1)
                df_pay = df_pay[mask_p]

            with col_dl_p:
                buffer_p = io.BytesIO()
                with pd.ExcelWriter(buffer_p, engine='openpyxl') as writer:
                    df_pay.to_excel(writer, index=False, sheet_name='Payments')
                st.download_button(label="📥 Download Excel", data=buffer_p.getvalue(), file_name="Payments_List.xlsx", use_container_width=True, type="secondary", key="dl_pay_btn")

            # --- KPI CARDS ---
            k_count = len(df_pay)
            k_total = _sum_col(df_pay, "amount")
            _mode = df_pay["mode"].astype(str) if "mode" in df_pay.columns else pd.Series([""] * len(df_pay))
            k_team = _sum_col(df_pay[_mode.values == "Team"], "amount") if k_count else 0.0
            k_vendor = _sum_col(df_pay[_mode.values == "Vendor"], "amount") if k_count else 0.0
            kpi_grid(
                kpi_card("💳", "Payments", f"{k_count:,}", "Filtered results" if search_pay else "All records", *KPI_INDIGO),
                kpi_card("💰", "Total Paid", f"₹ {k_total:,.0f}", "Team + Vendor", *KPI_GREEN, value_cls="green"),
                kpi_card("👷", "Team Payments", f"₹ {k_team:,.0f}", "Mode = Team", *KPI_AMBER),
                kpi_card("🏭", "Vendor Payments", f"₹ {k_vendor:,.0f}", "Mode = Vendor", *KPI_BLUE),
            )

            if not df_pay.empty:
                if "date" in df_pay.columns:
                    df_pay["date"] = pd.to_datetime(df_pay["date"], errors="coerce").dt.strftime('%d/%m/%Y')

                df_pay = df_pay.reset_index(drop=True)

                if st.session_state.billing_view_mode == "cards":
                    # ---------------------------------------------------------------
                    # MOBILE CARD VIEW
                    # ---------------------------------------------------------------
                    for pos, (_, row) in enumerate(df_pay.iterrows()):
                        row_dict = row.to_dict()
                        rid = row_dict.get("id")
                        amt_v = row_dict.get('amount')

                        with st.container(border=True):
                            st.markdown(f"""
                                <div class="billing-card-title">#{pos + 1} — {html.escape(cell(row_dict.get('pay_to')))}</div>
                                <div class="billing-card-sub">{cell(row_dict.get('date'))} • {html.escape(cell(row_dict.get('pay_type')))} • {html.escape(cell(row_dict.get('mode')))}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Pay From</span><span class="billing-card-value">{html.escape(cell(row_dict.get('pay_from')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Amount</span><span class="billing-card-value" style="color:#059669;font-weight:800;">{'₹ %s' % format(amt_v, ',.0f') if pd.notna(amt_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{html.escape(cell(row_dict.get('remark')))}</span></div>
                            """, unsafe_allow_html=True)

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.button("⚙️ Manage", key=f"payc_mgr_{rid}", use_container_width=True):
                                    payment_dialog(row_data=row_dict, mode=row_dict.get("mode", "Team"))
                            with bc2:
                                if st.button("🗑️ Delete", key=f"payc_del_{rid}", use_container_width=True):
                                    delete_payment_dialog(row_dict)
                else:
                    # ---------------------------------------------------------------
                    # ✨ LAVISH DESKTOP TABLE VIEW — single ⚙️ button at row start
                    # ---------------------------------------------------------------
                    PAY_COL_RATIOS = [0.55, 0.5, 1.1, 1.6, 1.0, 1.1, 1.0, 1.8, 0.9]
                    PAY_COL_LABELS = ["⚙️", "#", "PAY FROM", "PAY TO", "PAY TYPE", "AMOUNT", "DATE", "REMARK", "MODE"]

                    table_min_width_css("pay_table_wrap", 1300)
                    table_title_bar("💳 Payment Register", "newest first", f"₹ {k_total:,.0f}")

                    with st.container(key="pay_table_wrap", height=520):
                        table_header_row("blhead_pay", PAY_COL_RATIOS, PAY_COL_LABELS, center_idx=(0, 1, 8), right_idx=(5,))

                        for pos, (_, row) in enumerate(df_pay.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            parity = "odd" if (pos + 1) % 2 else "even"
                            is_team_mode = str(row_dict.get("mode", "")).strip() != "Vendor"

                            with st.container(key=f"blrow_{parity}_pay_{rid}"):
                                rcols = st.columns(PAY_COL_RATIOS, vertical_alignment="center")

                                with rcols[0]:
                                    with st.container(key=f"blpop_pay_{rid}"):
                                        with st.popover("⚙️"):
                                            if st.button("✏️ Edit Payment", key=f"pay_mgr_{rid}", use_container_width=True):
                                                payment_dialog(row_data=row_dict, mode=row_dict.get("mode", "Team"))
                                            if st.button("🗑️ Delete Payment", key=f"pay_del_{rid}", use_container_width=True):
                                                delete_payment_dialog(row_dict)

                                rcols[1].markdown(_serial(pos + 1), unsafe_allow_html=True)
                                rcols[2].markdown(_pill(row_dict.get('pay_from')), unsafe_allow_html=True)
                                rcols[3].markdown(_entity(row_dict.get('pay_to'), "team" if is_team_mode else "vendor"), unsafe_allow_html=True)
                                rcols[4].markdown(_chip(row_dict.get('pay_type')), unsafe_allow_html=True)
                                rcols[5].markdown(_money(row_dict.get('amount'), "paid"), unsafe_allow_html=True)
                                rcols[6].markdown(_txt(row_dict.get('date'), "slux-soft"), unsafe_allow_html=True)
                                rcols[7].markdown(_txt(row_dict.get('remark'), "slux-soft"), unsafe_allow_html=True)
                                rcols[8].markdown(
                                    f"<div style='text-align:center;'>{_badge(cell(row_dict.get('mode')), 'blue' if is_team_mode else 'purple')}</div>",
                                    unsafe_allow_html=True,
                                )

                    table_footer(
                        f'{len(df_pay):,} payment{"s" if len(df_pay) != 1 else ""}',
                        f'<span>Team: <b style="color:#b45309;">₹ {k_team:,.0f}</b></span>'
                        f'<span>Vendor: <b style="color:#0e7490;">₹ {k_vendor:,.0f}</b></span>'
                        f'<span>Total: <b style="color:#059669;">₹ {k_total:,.0f}</b></span>',
                    )
            else:
                empty_state("No payments match your search.")
        else:
            empty_state("No payments found. Click the buttons above to add one.")
            with col_dl_p:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_p_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

# ==========================================
# PAGE 3: TEAM MATERIAL TRANSFER
# ==========================================
elif st.session_state.billing_active_page == "transfer":
    active_ws = st.session_state.get("active_workspace", "VISPL")
    c_add, c_search, c_download = st.columns([1.7, 4.5, 1.8])
    with c_add:
        if st.button("➕ New Transfer", type="primary", use_container_width=True, key="add_material_transfer"):
            team_material_transfer_dialog()
    with c_search:
        transfer_search = st_keyup("Search Transfer", placeholder="🔍 Search team, material, reference...", label_visibility="collapsed", key="transfer_search")

    transfer_rows = fetch_team_material_transfers_cached(active_ws)
    df_transfer = pd.DataFrame(transfer_rows)
    if not df_transfer.empty:
        if transfer_search:
            transfer_mask = df_transfer.astype(str).apply(lambda col: col.str.contains(transfer_search, case=False, na=False)).any(axis=1)
            df_transfer = df_transfer[transfer_mask]

        with c_download:
            transfer_buffer = io.BytesIO()
            export_cols = ["transfer_date", "from_team", "to_team", "reference_no", "material_description", "quantity", "amount", "remark", "status"]
            transfer_export = df_transfer.reindex(columns=export_cols).rename(columns={
                "transfer_date": "Date", "from_team": "From Team", "to_team": "To Team",
                "reference_no": "Reference No.", "material_description": "Material",
                "quantity": "Quantity", "amount": "Amount", "remark": "Remark", "status": "Status"
            })
            with pd.ExcelWriter(transfer_buffer, engine="openpyxl") as writer:
                transfer_export.to_excel(writer, index=False, sheet_name="Material Transfers")
            st.download_button("📥 Download Excel", transfer_buffer.getvalue(), "Team_Material_Transfers.xlsx", use_container_width=True, key="transfer_excel")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- KPI CARDS ---
        _status = df_transfer["status"].astype(str) if "status" in df_transfer.columns else pd.Series([""] * len(df_transfer))
        _active_df = df_transfer[_status.values == "Active"]
        k_active = len(_active_df)
        k_reversed = int((_status == "Reversed").sum())
        k_value = _sum_col(_active_df, "amount")
        kpi_grid(
            kpi_card("🔄", "Transfers", f"{len(df_transfer):,}", "Filtered results" if transfer_search else "All records", *KPI_INDIGO),
            kpi_card("✅", "Active", f"{k_active:,}", "Counted in ledgers", *KPI_GREEN, value_cls="green"),
            kpi_card("↩️", "Reversed", f"{k_reversed:,}", "Not counted", *KPI_RED, value_cls="red" if k_reversed else ""),
            kpi_card("💰", "Active Material Value", f"₹ {k_value:,.0f}", "Given ↔ Received", *KPI_AMBER),
        )

        ratios = [0.55, 0.5, 1.0, 1.4, 1.4, 1.9, 0.8, 1.1, 1.7, 1.0]
        labels = ["↩️", "#", "DATE", "FROM TEAM", "TO TEAM", "MATERIAL", "QTY", "AMOUNT", "REMARK / REF.", "STATUS"]

        table_min_width_css("transfer_table_wrap", 1500)
        table_title_bar("🔄 Material Transfer Register", "↩️ = revoke an active transfer", f"₹ {k_value:,.0f}")

        with st.container(height=520, key="transfer_table_wrap"):
            table_header_row("blhead_transfer", ratios, labels, center_idx=(0, 1, 6, 9), right_idx=(7,))
            for pos, (_, transfer) in enumerate(df_transfer.reset_index(drop=True).iterrows()):
                row = transfer.to_dict()
                rid = row.get("id")
                parity = "odd" if (pos + 1) % 2 else "even"
                with st.container(key=f"blrow_{parity}_tr_{rid}"):
                    row_cols = st.columns(ratios, vertical_alignment="center")
                    with row_cols[0]:
                        if row.get("status") == "Active":
                            if st.button("↩️", key=f"reverse_transfer_{rid}", help="Revoke Transfer"):
                                try:
                                    supabase.table("team_material_transfers").update({
                                        "status": "Reversed",
                                        "reversed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                                    }).eq("id", rid).execute()
                                    fetch_team_material_transfers_cached.clear()
                                    fetch_ledger_data_cached.clear()
                                    st.success("✅ Transfer revoked. दोनों ledgers से adjustment हट गया।")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Revoke error: {e}")
                        else:
                            st.button("↩️", key=f"reversed_transfer_{rid}", disabled=True)
                    transfer_date_display = pd.to_datetime(row.get("transfer_date"), errors="coerce")
                    transfer_date_display = transfer_date_display.strftime("%d/%m/%Y") if pd.notna(transfer_date_display) else "-"
                    row_cols[1].markdown(_serial(pos + 1), unsafe_allow_html=True)
                    row_cols[2].markdown(_txt(transfer_date_display, "slux-soft"), unsafe_allow_html=True)
                    row_cols[3].markdown(_entity(row.get('from_team'), "team"), unsafe_allow_html=True)
                    row_cols[4].markdown(_entity(row.get('to_team'), "team"), unsafe_allow_html=True)
                    row_cols[5].markdown(_wrap(row.get('material_description'), "slux-strong"), unsafe_allow_html=True)
                    row_cols[6].markdown(f"<div style='text-align:center;'>{_txt(row.get('quantity'))}</div>", unsafe_allow_html=True)
                    row_cols[7].markdown(_money(row.get("amount"), "strong"), unsafe_allow_html=True)
                    ref_remark = " | ".join(v for v in [str(row.get("reference_no") or "").strip(), str(row.get("remark") or "").strip()] if v)
                    row_cols[8].markdown(_wrap(ref_remark, "slux-soft"), unsafe_allow_html=True)
                    is_active_tr = row.get("status") == "Active"
                    row_cols[9].markdown(
                        f"<div style='text-align:center;'>{_badge(cell(row.get('status')), 'green' if is_active_tr else 'red')}</div>",
                        unsafe_allow_html=True,
                    )

        table_footer(
            f'{len(df_transfer):,} transfer{"s" if len(df_transfer) != 1 else ""}',
            f'<span>Active Value: <b style="color:#4f46e5;">₹ {k_value:,.0f}</b></span>',
        )
    else:
        with c_download:
            st.button("📥 Download Excel", disabled=True, use_container_width=True, key="transfer_excel_disabled")
        empty_state("अभी कोई Team Material Transfer नहीं है। New Transfer से पहली entry जोड़ें।")

# ==========================================
# PAGE 4: REPORTS & LEDGER
# ==========================================
elif st.session_state.billing_active_page == "ledger":
    col_rmode, col_rname, _ = st.columns([3, 4, 3])
    with col_rmode:
        rep_mode = st.radio("Ledger Type:", ["Team", "Vendor"], horizontal=True, key="rep_mode")
    with col_rname:
        rep_opts = team_list if rep_mode == "Team" else vendor_list
        sel_name = st.selectbox("Select Name", options=["-- Select --"] + rep_opts)

    st.markdown("---")

    if sel_name and sel_name != "-- Select --":
        tot_inv = 0.0
        tot_pay = 0.0
        tot_material_given = 0.0
        tot_material_received = 0.0
        df_inv_rep, df_pay_rep, df_transfer_rep = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        try:
            active_ws = st.session_state.get('active_workspace', 'VISPL')
            inv_col = "team_name" if rep_mode == "Team" else "vendor_name"
            inv_rows, pay_rows = fetch_ledger_data_cached(active_ws, rep_mode, inv_col, sel_name)
            if inv_rows:
                df_inv_rep = pd.DataFrame(inv_rows)
                tot_inv = df_inv_rep["amount"].sum()
                
                req_cols = ["invoice_no", "date", "project_id", "site_id", "site_name", "basic_amount", "amount"]
                for c in req_cols:
                    if c not in df_inv_rep.columns:
                        df_inv_rep[c] = ""
                df_inv_rep = df_inv_rep[req_cols]

                df_inv_rep["amount"] = pd.to_numeric(df_inv_rep["amount"], errors="coerce").fillna(0.0)
                df_inv_rep["tds_amount"] = 0.0 if rep_mode == "Vendor" else df_inv_rep["amount"] * 0.01
                df_inv_rep["net_payable"] = df_inv_rep["amount"] - df_inv_rep["tds_amount"]
                df_inv_rep = df_inv_rep.drop(columns=["amount"])

                df_inv_rep.rename(columns={
                    "invoice_no": "Invoice No.",
                    "date": "Invoice Date",
                    "project_id": "Project ID",
                    "site_id": "Site ID",
                    "site_name": "Site Name",
                    "basic_amount": "Basic Amt",
                    "tds_amount": "TDS (1%)",
                    "net_payable": "Net Payable"
                }, inplace=True)
                
                if "Invoice Date" in df_inv_rep.columns:
                    df_inv_rep["Invoice Date"] = pd.to_datetime(df_inv_rep["Invoice Date"], errors="coerce").dt.strftime('%d/%m/%Y')

            if pay_rows:
                df_pay_rep = pd.DataFrame(pay_rows)
                tot_pay = df_pay_rep["amount"].sum()
                df_pay_rep = df_pay_rep[["date", "pay_from", "pay_type", "amount", "remark"]]
                
                if "date" in df_pay_rep.columns:
                    df_pay_rep["date"] = pd.to_datetime(df_pay_rep["date"], errors="coerce").dt.strftime('%d/%m/%Y')

            if rep_mode == "Team":
                all_transfers = fetch_team_material_transfers_cached(active_ws)
                team_transfers = [
                    row for row in all_transfers
                    if row.get("status") == "Active"
                    and (row.get("from_team") == sel_name or row.get("to_team") == sel_name)
                ]
                if team_transfers:
                    raw_transfer_df = pd.DataFrame(team_transfers)
                    raw_transfer_df["amount"] = pd.to_numeric(raw_transfer_df["amount"], errors="coerce").fillna(0.0)
                    tot_material_given = raw_transfer_df.loc[raw_transfer_df["from_team"] == sel_name, "amount"].sum()
                    tot_material_received = raw_transfer_df.loc[raw_transfer_df["to_team"] == sel_name, "amount"].sum()

                    transfer_report_rows = []
                    for _, transfer_row in raw_transfer_df.iterrows():
                        is_given = transfer_row.get("from_team") == sel_name
                        transfer_report_rows.append({
                            "Date": pd.to_datetime(transfer_row.get("transfer_date"), errors="coerce").strftime("%d/%m/%Y"),
                            "Direction": "Material Given (+)" if is_given else "Material Received (-)",
                            "Other Team": transfer_row.get("to_team") if is_given else transfer_row.get("from_team"),
                            "Material": transfer_row.get("material_description"),
                            "Quantity": transfer_row.get("quantity"),
                            "Reference No.": transfer_row.get("reference_no"),
                            "Amount": transfer_row.get("amount"),
                            "Remark": transfer_row.get("remark"),
                        })
                    df_transfer_rep = pd.DataFrame(transfer_report_rows)
                    
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        bal = tot_inv - tot_pay + tot_material_given - tot_material_received

        # --- ✨ LAVISH KPI CARDS ---
        _cards = [
            kpi_card("🧾", "Total Billed", f"₹ {tot_inv:,.0f}", f"{len(df_inv_rep):,} invoice(s)", *KPI_BLUE, value_cls="blue"),
            kpi_card("💰", "Total Paid", f"₹ {tot_pay:,.0f}", f"{len(df_pay_rep):,} payment(s)", *KPI_GREEN, value_cls="green"),
        ]
        if rep_mode == "Team":
            _cards += [
                kpi_card("📤", "Material Given", f"₹ {tot_material_given:,.0f}", "Added to balance (+)", *KPI_INDIGO, value_cls="blue"),
                kpi_card("📥", "Material Received", f"₹ {tot_material_received:,.0f}", "Less from balance (−)", *KPI_PINK, value_cls="red"),
            ]
        _cards.append(
            kpi_card("⚖️", "Net Balance", f"₹ {bal:,.0f}", "Payable" if bal > 0 else "Settled / Advance",
                     *(KPI_RED if bal > 0 else KPI_GREEN), value_cls="red" if bal > 0 else "green")
        )
        kpi_grid(*_cards)

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("<h4 style='color:#0f172a;'>📚 Invoices</h4>", unsafe_allow_html=True)
            st.dataframe(df_inv_rep, use_container_width=True, hide_index=True)
        with t2:
            st.markdown("<h4 style='color:#0f172a;'>💸 Payments</h4>", unsafe_allow_html=True)
            st.dataframe(df_pay_rep, use_container_width=True, hide_index=True)

        if rep_mode == "Team":
            st.markdown("<h4 style='color:#0f172a;'>🔄 Material Transfers</h4>", unsafe_allow_html=True)
            st.dataframe(df_transfer_rep, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        col_down1, col_down2, _ = st.columns([2, 2, 6])
        
        with col_down1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if not df_inv_rep.empty: df_inv_rep.to_excel(writer, index=False, sheet_name='Invoices')
                if not df_pay_rep.empty: df_pay_rep.to_excel(writer, index=False, sheet_name='Payments')
                if not df_transfer_rep.empty: df_transfer_rep.to_excel(writer, index=False, sheet_name='Material Transfers')
                summary_df = pd.DataFrame({
                    "Name": [sel_name], "Total Billed": [tot_inv], "Total Paid": [tot_pay],
                    "Material Given": [tot_material_given], "Material Received": [tot_material_received],
                    "Balance": [bal]
                })
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
            
            st.download_button(label="📊 Download Excel", data=buffer.getvalue(), file_name=f"{sel_name}_Ledger.xlsx", type="primary", use_container_width=True)

        with col_down2:
            def generate_pdf():
                if FPDF is None:
                    raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                
                if os.path.exists("logo (1).png"):
                    pdf.image("logo (1).png", x=75, y=10, w=60)
                    pdf.ln(28) 
                
                primary_color = (15, 23, 42) 
                secondary_color = (59, 130, 246) 
                green_color = (16, 185, 129) 
                red_color = (239, 68, 68) 
                
                pdf.set_text_color(*primary_color)
                pdf.set_font("Arial", 'B', 18)
                pdf.cell(190, 10, "VISIONTECH INFRA SOLUTION PVT. LTD.", ln=True, align='C')
                
                pdf.set_text_color(*secondary_color)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(190, 8, "LEDGER & BALANCE SHEET", ln=True, align='C')
                
                pdf.set_text_color(100, 116, 139) 
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(190, 8, f"Statement For: {sel_name}", ln=True, align='C')
                pdf.ln(5)
                
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(10, pdf.get_y(), 190, 34, 'FD')
                
                pdf.set_y(pdf.get_y() + 5)
                pdf.set_font("Arial", 'B', 11)
                
                pdf.set_text_color(*secondary_color)
                pdf.cell(63, 8, f"Total Billed: Rs. {tot_inv:,.0f}", ln=False, align='C')
                
                pdf.set_text_color(*green_color)
                pdf.cell(63, 8, f"Total Paid: Rs. {tot_pay:,.0f}", ln=False, align='C')
                
                bal_color = red_color if bal > 0 else green_color
                pdf.set_text_color(*bal_color)
                pdf.cell(64, 8, f"Net Balance: Rs. {bal:,.0f}", ln=True, align='C')

                if rep_mode == "Team":
                    pdf.set_text_color(71, 85, 105)
                    pdf.set_font("Arial", 'B', 9)
                    pdf.cell(95, 8, f"Material Given (+): Rs. {tot_material_given:,.0f}", ln=False, align='C')
                    pdf.cell(95, 8, f"Material Received (-): Rs. {tot_material_received:,.0f}", ln=True, align='C')
                
                pdf.ln(12)
                
                def create_table(title, df, header_color):
                    if not df.empty:
                        cols = df.columns.tolist()

                        if len(cols) == 8:
                            # Total = 190 mm. Widths remain fixed; long values wrap.
                            col_widths = [18, 18, 22, 24, 36, 24, 20, 28]
                        else:
                            col_widths = [190 / len(cols)] * len(cols)

                        # Project/Site values and remarks can be long. Every value stays
                        # inside its original fixed-width cell and increases row height.
                        wrap_cols = {
                            "invoice no.", "project id", "site id", "site name",
                            "remark", "description", "pay from", "pay type"
                        }

                        line_h = 4.0
                        header_h = 8.0
                        page_bottom = pdf.h - pdf.b_margin

                        def draw_table_heading(continued=False):
                            heading = f"{title} - CONTINUED" if continued else title
                            pdf.set_font("Arial", 'B', 12)
                            pdf.set_text_color(*header_color)
                            pdf.cell(190, 8, heading, ln=True, align='L')

                            pdf.set_fill_color(*header_color)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Arial", 'B', 7)
                            for i, col in enumerate(cols):
                                pdf.cell(
                                    col_widths[i], header_h,
                                    str(col).upper().replace('_', ' '),
                                    border=1, align='C', fill=True
                                )
                            pdf.ln(header_h)
                            pdf.set_text_color(0, 0, 0)

                        # Never start a table where only its heading can fit.
                        if pdf.get_y() + 20 > page_bottom:
                            pdf.add_page()
                        draw_table_heading()

                        fill = False
                        for _, row in df.iterrows():
                            if fill:
                                pdf.set_fill_color(241, 245, 249)
                            else:
                                pdf.set_fill_color(255, 255, 255)

                            # First pass: wrap every required value and calculate one common
                            # height for the complete row.
                            row_vals = []
                            max_lines = 1
                            for i, col in enumerate(cols):
                                val = row[col]
                                col_lower = str(col).lower()

                                if 'tds' in col_lower or 'payable' in col_lower or 'amt' in col_lower or 'total' in col_lower or 'gst' in col_lower or 'basic' in col_lower or 'amount' in col_lower:
                                    try:
                                        if pd.notna(val) and str(val).strip() != "":
                                            val_str = f"Rs. {float(val):,.0f}"
                                        else:
                                            val_str = "-"
                                    except:
                                        val_str = str(val)
                                    align = 'R'
                                else:
                                    val_str = str(val) if pd.notna(val) and str(val).strip() != "" else "-"
                                    align = 'L' if col_lower in wrap_cols else 'C'

                                pdf.set_font("Arial", '', 7.5)
                                lines = _wrap_text_for_pdf(pdf, val_str, col_widths[i])
                                if col_lower not in wrap_cols and len(lines) > 1:
                                    # Safety: even an unexpected long value must not enter
                                    # the next column.
                                    align = 'C'

                                row_vals.append((lines, align, col_widths[i]))
                                max_lines = max(max_lines, len(lines))

                            row_height = max(6.0, max_lines * line_h + 2.0)

                            # A complete row moves to the next page. This is the main fix
                            # for PDFs that were splitting/cutting cells between pages.
                            if pdf.get_y() + row_height > page_bottom:
                                pdf.add_page()
                                draw_table_heading(continued=True)

                            # Second pass: draw a full-height rectangle for every cell, then
                            # place wrapped text line-by-line within that same rectangle.
                            x0 = pdf.get_x()
                            y0 = pdf.get_y()
                            x_cursor = x0
                            for lines, align, w in row_vals:
                                pdf.set_xy(x_cursor, y0)
                                pdf.rect(x_cursor, y0, w, row_height, 'DF' if fill else 'D')
                                text_y = y0 + 1.0
                                pdf.set_font("Arial", '', 7.5)
                                for text_line in lines:
                                    pdf.set_xy(x_cursor + 1.0, text_y)
                                    pdf.cell(w - 2.0, line_h, text_line, border=0, align=align)
                                    text_y += line_h
                                x_cursor += w
                            pdf.set_xy(x0, y0 + row_height)
                            fill = not fill
                        pdf.ln(5)
                
                create_table("INVOICES (BILLED)", df_inv_rep, secondary_color)
                create_table("PAYMENTS (PAID)", df_pay_rep, green_color)
                if rep_mode == "Team":
                    create_table("TEAM MATERIAL TRANSFERS", df_transfer_rep, (139, 92, 246))
                
                raw = pdf.output(dest='S')
                return bytes(raw) if isinstance(raw, (bytearray, bytes)) else raw.encode('latin1')

            try:
                pdf_bytes = generate_pdf()
                st.download_button(label="📄 Download PDF", data=pdf_bytes, file_name=f"{sel_name}_Report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(str(e))

# ==========================================
# PAGE 5: PENDING MRN APPROVAL
# ==========================================
elif st.session_state.billing_active_page == "mrn":
    st.markdown("<h3 style='color:#0f172a;'>🔒 MRN Approval Gate</h3>", unsafe_allow_html=True)
    st.markdown("Enter your security password to view and approve MRNs generated from the desk.")
    
    pwd = st.text_input("Security Password", type="password", placeholder="Enter Password...", key="mrn_approval_pwd")
    
    if pwd == "Indus@123":
        st.success("Access Granted! Welcome to MRN Approvals.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        try:
            active_ws = st.session_state.get('active_workspace', 'VISPL')
            # Latest pending records appear at the top
            pending_rows = fetch_pending_mrn_cached(active_ws)
            if pending_rows:
                df_pending = pd.DataFrame(pending_rows).reset_index(drop=True)

                display_dates = (
                    pd.to_datetime(df_pending["date"], errors="coerce").dt.strftime('%d/%m/%Y')
                    if "date" in df_pending.columns else pd.Series([""] * len(df_pending))
                )

                # --- KPI CARDS ---
                k_pending = len(df_pending)
                k_pending_amt = _sum_col(df_pending, "amount")
                k_pending_teams = df_pending["team_name"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA}).dropna().nunique() if "team_name" in df_pending.columns else 0
                kpi_grid(
                    kpi_card("🕒", "Pending MRNs", f"{k_pending:,}", "Waiting for approval", *KPI_AMBER),
                    kpi_card("💰", "Pending Amount", f"₹ {k_pending_amt:,.0f}", "Will move to billing on approve", *KPI_INDIGO, value_cls="blue"),
                    kpi_card("👷", "Teams", f"{k_pending_teams:,}", "With pending MRNs", *KPI_PINK),
                )

                if st.session_state.billing_view_mode == "cards":
                    # ---------------------------------------------------------------
                    # MOBILE CARD VIEW
                    # ---------------------------------------------------------------
                    for pos, (_, row) in enumerate(df_pending.iterrows()):
                        row_dict = row.to_dict()
                        rid = row_dict.get("id")
                        basic_v = row_dict.get('basic_amount')
                        amt_v = row_dict.get('amount')

                        with st.container(border=True):
                            st.markdown(f"""
                                <div class="billing-card-title">#{pos + 1} — {html.escape(cell(row_dict.get('team_name')))}</div>
                                <div class="billing-card-sub">{html.escape(cell(row_dict.get('invoice_no')))} • {cell(display_dates.iloc[pos])}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Project ID</span><span class="billing-card-value">{html.escape(cell(row_dict.get('project_id')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site ID</span><span class="billing-card-value">{html.escape(cell(row_dict.get('site_id')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site Name</span><span class="billing-card-value">{html.escape(cell(row_dict.get('site_name')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Cluster</span><span class="billing-card-value">{html.escape(cell(row_dict.get('cluster')))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Basic Amount</span><span class="billing-card-value">{'₹ %s' % format(basic_v, ',.0f') if pd.notna(basic_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Total</span><span class="billing-card-value" style="color:#4f46e5;font-weight:800;">{'₹ %s' % format(amt_v, ',.0f') if pd.notna(amt_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{html.escape(cell(row_dict.get('remark')))}</span></div>
                            """, unsafe_allow_html=True)

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.button("✅ Approve", key=f"mrnc_app_{rid}", type="primary", use_container_width=True):
                                    try:
                                        full_row = dict(row_dict)
                                        full_row.pop("id", None)
                                        supabase.table("billing_invoices").insert(full_row).execute()
                                        supabase.table("pending_billing_invoices").delete().eq("id", rid).execute()
                                        st.success("✅ MRN Approved and Moved to Main Billing Ledger!")
                                        fetch_billing_invoices_cached.clear()
                                        fetch_pending_mrn_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error approving: {e}")
                            with bc2:
                                if st.button("❌ Reject", key=f"mrnc_rej_{rid}", use_container_width=True):
                                    try:
                                        supabase.table("pending_billing_invoices").delete().eq("id", rid).execute()
                                        st.error("❌ Pending MRN Rejected and Deleted from Queue!")
                                        fetch_pending_mrn_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error rejecting: {e}")
                else:
                    # ---------------------------------------------------------------
                    # ✨ LAVISH DESKTOP TABLE VIEW — ✅ / ❌ at row start
                    # ---------------------------------------------------------------
                    MRN_COL_RATIOS = [0.5, 0.5, 0.5, 1.3, 1.2, 0.95, 1.4, 1.0, 1.3, 1.0, 1.05, 1.1, 1.4]
                    MRN_COL_LABELS = ["✅", "❌", "#", "TEAM", "MRN NO.", "DATE", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC AMT", "TOTAL", "REMARK"]

                    table_min_width_css("mrn_table_wrap", 1800)
                    table_title_bar("🕒 Pending MRN Queue", "✅ approve → moves to Invoice Entry • ❌ reject → removed", f"₹ {k_pending_amt:,.0f}")

                    with st.container(key="mrn_table_wrap", height=460):
                        table_header_row("blhead_mrn", MRN_COL_RATIOS, MRN_COL_LABELS, center_idx=(0, 1, 2), right_idx=(10, 11))

                        for pos, (_, row) in enumerate(df_pending.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            parity = "odd" if (pos + 1) % 2 else "even"

                            with st.container(key=f"blrow_{parity}_mrn_{rid}"):
                                rcols = st.columns(MRN_COL_RATIOS, vertical_alignment="center")

                                with rcols[0]:
                                    if st.button("✅", key=f"mrn_app_{rid}", help="Approve MRN"):
                                        try:
                                            full_row = dict(row_dict)
                                            full_row.pop("id", None)
                                            supabase.table("billing_invoices").insert(full_row).execute()
                                            supabase.table("pending_billing_invoices").delete().eq("id", rid).execute()
                                            st.success("✅ MRN Approved and Moved to Main Billing Ledger!")
                                            fetch_billing_invoices_cached.clear()
                                            fetch_pending_mrn_cached.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error approving: {e}")
                                with rcols[1]:
                                    if st.button("❌", key=f"mrn_rej_{rid}", help="Reject MRN"):
                                        try:
                                            supabase.table("pending_billing_invoices").delete().eq("id", rid).execute()
                                            st.error("❌ Pending MRN Rejected and Deleted from Queue!")
                                            fetch_pending_mrn_cached.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error rejecting: {e}")

                                rcols[2].markdown(_serial(pos + 1), unsafe_allow_html=True)
                                rcols[3].markdown(_entity(row_dict.get('team_name'), "team"), unsafe_allow_html=True)
                                rcols[4].markdown(_chip(row_dict.get('invoice_no'), "inv"), unsafe_allow_html=True)
                                rcols[5].markdown(_txt(display_dates.iloc[pos], "slux-soft"), unsafe_allow_html=True)
                                rcols[6].markdown(_chip(row_dict.get('project_id'), "proj"), unsafe_allow_html=True)
                                rcols[7].markdown(_chip(row_dict.get('site_id')), unsafe_allow_html=True)
                                rcols[8].markdown(_txt(row_dict.get('site_name'), "slux-strong"), unsafe_allow_html=True)
                                rcols[9].markdown(_pill(row_dict.get('cluster')), unsafe_allow_html=True)
                                rcols[10].markdown(_money(row_dict.get('basic_amount')), unsafe_allow_html=True)
                                rcols[11].markdown(_money(row_dict.get('amount'), "strong"), unsafe_allow_html=True)
                                rcols[12].markdown(_txt(row_dict.get('remark'), "slux-soft"), unsafe_allow_html=True)

                    table_footer(
                        f'{k_pending:,} pending MRN{"s" if k_pending != 1 else ""}',
                        f'<span>Pending Total: <b style="color:#4f46e5;">₹ {k_pending_amt:,.0f}</b></span>',
                    )
            else:
                empty_state("No pending MRNs waiting for approval.")
        except Exception as e:
            st.error(f"Database error: {e}")
    elif pwd != "":
        st.error("❌ Incorrect Password!")
