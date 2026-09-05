import streamlit as st
import pandas as pd
import datetime
import io
import os
import math
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

# --- 2. LAVISH CUSTOM CSS ---
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
    }
    button[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"],
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {
        background: #ef4444 !important; color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }
    
    /* KPI Cards for Reports */
    .kpi-card {
        background: white; border-radius: 12px; padding: 20px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;
    }
    .kpi-title { font-size: 1rem; color: #64748b; font-weight: 700; text-transform: uppercase; }
    .kpi-value-red { font-size: 2rem; color: #ef4444; font-weight: 900; }
    .kpi-value-green { font-size: 2rem; color: #10b981; font-weight: 900; }
    .kpi-value-blue { font-size: 2rem; color: #3b82f6; font-weight: 900; }

    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }

    /* =========================================================
       LAVISH TABLE STYLING (st.dataframe + st.data_editor)
       ========================================================= */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12), 0 4px 6px -2px rgba(15, 23, 42, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        background: #ffffff !important;
    }
    [data-testid="stDataFrame"] > div, [data-testid="stDataEditor"] > div {
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    /* Header row */
    [data-testid="stDataFrame"] th, [data-testid="stDataEditor"] th,
    [data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataEditor"] [role="columnheader"] {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.4px !important;
        text-transform: uppercase !important;
        border: none !important;
        border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
    }
    /* Body cells */
    [data-testid="stDataFrame"] td, [data-testid="stDataEditor"] td,
    [data-testid="stDataFrame"] [role="gridcell"], [data-testid="stDataEditor"] [role="gridcell"] {
        font-size: 0.88rem !important;
        color: #1e293b !important;
        border-bottom: 1px solid #f1f5f9 !important;
        border-right: 1px solid #f8fafc !important;
    }
    /* Zebra striping */
    [data-testid="stDataFrame"] tr:nth-child(even) td,
    [data-testid="stDataEditor"] tr:nth-child(even) td {
        background-color: #f8fafc !important;
    }
    /* Row hover highlight */
    [data-testid="stDataFrame"] tr:hover td,
    [data-testid="stDataEditor"] tr:hover td {
        background-color: #eef2ff !important;
        transition: background-color 0.15s ease-in-out !important;
    }
    /* Canvas-based grid (glide-data-grid) rounding + shadow wrapper fallback */
    [data-testid="stDataFrame"] canvas, [data-testid="stDataEditor"] canvas {
        border-radius: 0 0 16px 16px !important;
    }
    /* Scrollbar polish inside tables */
    [data-testid="stDataFrame"] ::-webkit-scrollbar, [data-testid="stDataEditor"] ::-webkit-scrollbar {
        height: 10px !important; width: 10px !important;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb, [data-testid="stDataEditor"] ::-webkit-scrollbar-thumb {
        background: #c7d2fe !important; border-radius: 8px !important;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-track, [data-testid="stDataEditor"] ::-webkit-scrollbar-track {
        background: #f1f5f9 !important;
    }
    /* Toolbar (search/download icons) that appears on dataframe hover */
    [data-testid="stElementToolbar"] {
        background: #ffffff !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12) !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* =========================================================
       CUSTOM ROW-BASED TABLE (Site Data Hub style) — used on
       Invoice Entry / Payment Entry / Pending MRN Approval tabs,
       with round gear/trash/tick/cross icon action buttons.
       Header and body are SEPARATE containers (not :first-child)
       so the gradient only ever applies to the actual header row.
       ========================================================= */
    .st-key-inv_table_header, .st-key-pay_table_header, .st-key-mrn_table_header {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        border-radius: 14px 14px 0 0 !important;
        overflow: hidden auto !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10) !important;
    }
    .st-key-inv_table_header div[data-testid="stHorizontalBlock"],
    .st-key-pay_table_header div[data-testid="stHorizontalBlock"],
    .st-key-mrn_table_header div[data-testid="stHorizontalBlock"] {
        min-width: 1700px !important;
        align-items: center !important;
        flex-wrap: nowrap !important;
        padding: 10px 0 !important;
    }
    .st-key-inv_table_wrap, .st-key-pay_table_wrap, .st-key-mrn_table_wrap {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        overflow: auto !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        padding: 4px 0 !important;
        margin-bottom: 20px !important;
    }
    .st-key-inv_table_wrap div[data-testid="stHorizontalBlock"],
    .st-key-pay_table_wrap div[data-testid="stHorizontalBlock"],
    .st-key-mrn_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1700px !important;
        align-items: center !important;
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 7px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-inv_table_wrap div[data-testid="stHorizontalBlock"]:hover,
    .st-key-pay_table_wrap div[data-testid="stHorizontalBlock"]:hover,
    .st-key-mrn_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: #eef2ff !important;
    }
    .st-key-inv_table_header div[data-testid="column"],
    .st-key-pay_table_header div[data-testid="column"],
    .st-key-mrn_table_header div[data-testid="column"] {
        padding: 0 12px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255, 255, 255, 0.15);
    }
    .st-key-inv_table_wrap div[data-testid="column"],
    .st-key-pay_table_wrap div[data-testid="column"],
    .st-key-mrn_table_wrap div[data-testid="column"] {
        padding: 0 12px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid #f8fafc;
    }
    .st-key-inv_table_header div[data-testid="column"]:last-child,
    .st-key-pay_table_header div[data-testid="column"]:last-child,
    .st-key-mrn_table_header div[data-testid="column"]:last-child,
    .st-key-inv_table_wrap div[data-testid="column"]:last-child,
    .st-key-pay_table_wrap div[data-testid="column"]:last-child,
    .st-key-mrn_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    .st-key-inv_table_header .tbl-head,
    .st-key-pay_table_header .tbl-head,
    .st-key-mrn_table_header .tbl-head {
        color: #ffffff !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.6px !important;
        text-transform: uppercase !important;
        white-space: nowrap !important;
        padding: 4px 0 !important;
    }
    .st-key-inv_table_wrap .tbl-cell,
    .st-key-pay_table_wrap .tbl-cell,
    .st-key-mrn_table_wrap .tbl-cell {
        color: #1e293b !important;
        font-size: 0.85rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-inv_table_wrap .tbl-serial,
    .st-key-pay_table_wrap .tbl-serial,
    .st-key-mrn_table_wrap .tbl-serial {
        color: #94a3b8 !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
    }
    /* Round icon action buttons */
    .st-key-inv_table_wrap button, .st-key-pay_table_wrap button, .st-key-mrn_table_wrap button {
        height: 32px !important;
        width: 100% !important;
        max-width: 34px !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 8px !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        font-size: 0.95rem !important;
    }
    div[class*="st-key-inv_mgr_"] button, div[class*="st-key-pay_mgr_"] button {
        background: rgba(99, 102, 241, 0.14) !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
    }
    div[class*="st-key-inv_mgr_"] button:hover, div[class*="st-key-pay_mgr_"] button:hover {
        background: #6366f1 !important;
        transform: translateY(-2px) !important;
    }
    div[class*="st-key-inv_dl_"] button {
        background: rgba(59, 130, 246, 0.14) !important;
        border: 1px solid rgba(59, 130, 246, 0.35) !important;
    }
    div[class*="st-key-inv_dl_"] button:hover {
        background: #3b82f6 !important;
        transform: translateY(-2px) !important;
    }
    div[class*="st-key-inv_del_"] button, div[class*="st-key-pay_del_"] button, div[class*="st-key-mrn_rej_"] button {
        background: rgba(239, 68, 68, 0.14) !important;
        border: 1px solid rgba(239, 68, 68, 0.35) !important;
    }
    div[class*="st-key-inv_del_"] button:hover, div[class*="st-key-pay_del_"] button:hover, div[class*="st-key-mrn_rej_"] button:hover {
        background: #ef4444 !important;
        transform: translateY(-2px) !important;
    }
    div[class*="st-key-mrn_app_"] button {
        background: rgba(16, 185, 129, 0.14) !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
    }
    div[class*="st-key-mrn_app_"] button:hover {
        background: #10b981 !important;
        transform: translateY(-2px) !important;
    }

    /* =========================================================
       MOBILE CARD VIEW (light theme) — used when the Mobile View
       toggle is on, instead of the wide horizontal-scroll tables.
       ========================================================= */
    .billing-card-title { font-size: 1.02rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; }
    .billing-card-sub { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .billing-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; }
    .billing-card-row:last-child { border-bottom: none; }
    .billing-card-label { color: #64748b; font-weight: 600; }
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

    /* =========================================================
       CUSTOM PAGE NAVIGATION BAR (replaces st.tabs — fully reliable styling)
       Scoped to .st-key-billing_nav_bar so it doesn't clash with the
       red "secondary" (delete) button styling used elsewhere on this page.
       ========================================================= */
    .st-key-billing_nav_bar div[data-testid="stHorizontalBlock"] {
        gap: 12px !important;
        flex-wrap: wrap !important;
    }
    .st-key-billing_nav_bar button {
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        padding: 16px 10px !important;
        height: auto !important;
        border-radius: 12px !important;
        transition: all 0.25s ease !important;
        white-space: nowrap !important;
        box-shadow: none !important;
    }
    .st-key-billing_nav_bar button[kind="secondary"] {
        background: #ffffff !important;
        color: #475569 !important;
        border: 1.5px solid #e2e8f0 !important;
    }
    .st-key-billing_nav_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
        transform: translateY(-2px) !important;
    }
    .st-key-billing_nav_bar button[kind="secondary"] p,
    .st-key-billing_nav_bar button[kind="secondary"] span,
    .st-key-billing_nav_bar button[kind="secondary"] div {
        color: #475569 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }
    .st-key-billing_nav_bar button[kind="secondary"]:hover p,
    .st-key-billing_nav_bar button[kind="secondary"]:hover span,
    .st-key-billing_nav_bar button[kind="secondary"]:hover div {
        color: #0f172a !important;
    }
    .st-key-billing_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
    }
    .st-key-billing_nav_bar button[kind="primary"] p,
    .st-key-billing_nav_bar button[kind="primary"] span,
    .st-key-billing_nav_bar button[kind="primary"] div {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }

    /* =========================================================
       INVOICE SUB-TAB BAR (Team Invoices / Vendor Invoices)
       Reuses the same look as the main nav bar, just smaller.
       ========================================================= */
    .st-key-invoice_sub_tab_bar div[data-testid="stHorizontalBlock"] {
        gap: 10px !important;
    }
    .st-key-invoice_sub_tab_bar button {
        font-size: 0.92rem !important;
        font-weight: 800 !important;
        padding: 10px 8px !important;
        height: auto !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }
    .st-key-invoice_sub_tab_bar button[kind="secondary"] {
        background: #ffffff !important;
        color: #475569 !important;
        border: 1.5px solid #e2e8f0 !important;
    }
    .st-key-invoice_sub_tab_bar button[kind="secondary"] p,
    .st-key-invoice_sub_tab_bar button[kind="secondary"] span,
    .st-key-invoice_sub_tab_bar button[kind="secondary"] div {
        color: #475569 !important;
        font-weight: 800 !important;
    }
    .st-key-invoice_sub_tab_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35) !important;
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
    """Word-wrap text to fit within width_mm using the PDF's currently set font."""
    words = str(text).split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if pdf.get_string_width(test) <= width_mm - 2:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def _draw_item_row(pdf, sr, item_code, desc, qty, price, total, widths, line_h=4):
    """Draw one item-table row with word-wrapped description; all columns share the row's total height."""
    pdf.set_font("Arial", '', 8)
    desc_lines = _wrap_text_for_pdf(pdf, desc, widths[2])
    row_height = max(1, len(desc_lines)) * line_h

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
        date_fmt = pd.to_datetime(date_raw).strftime("%d-%b-%Y") if date_raw else "-"
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
    mrn_items_rows = []
    try:
        ws_val = row_dict.get("workspace") or st.session_state.get('active_workspace', 'VISPL')
        res_items = (
            supabase.table("mrn_items")
            .select("*")
            .eq("MRN Number", invoice_no)
            .eq("workspace", ws_val)
            .execute()
        )
        mrn_items_rows = res_items.data or []
    except Exception:
        mrn_items_rows = []

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
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(37, 60, 122)
    pdf.set_text_color(255, 255, 255)
    headers = ["SR", "ITEM CODE", "ITEM DESCRIPTION", "QTY", "PRICE (Rs.)", "TOTAL (Rs.)"]
    widths = [10, 40, 53, 15, 32, 40]
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)

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

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(150, 8, "Gross Invoice Value", border=1, align='R')
    pdf.cell(40, 8, f"{gross_value:,.2f}", border=1, align='R', ln=True)

    tds_amt = gross_value * 0.01
    net_payable = gross_value - tds_amt

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
    def_date = pd.to_datetime(def_date_str).date()
    
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
    st.markdown("<div style='color:#64748b; font-weight:800; font-size:0.85rem; letter-spacing:1px; text-transform:uppercase; margin-bottom:10px;'>📦 MRN Line Items</div>", unsafe_allow_html=True)

    mrn_items_dialog_rows = []
    if inv_no:
        try:
            ws_items = st.session_state.get('active_workspace', 'VISPL')
            mrn_items_res = supabase.table("mrn_items").select("*").eq("MRN Number", inv_no).eq("workspace", ws_items).execute()
            mrn_items_dialog_rows = mrn_items_res.data or []
        except Exception:
            mrn_items_dialog_rows = []

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
        mi1.markdown(f"<div style='text-align:center; background:#f8fafc; border-radius:10px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>Gross Invoice Value</span><br><span style='font-size:1.15rem; font-weight:800; color:#3b82f6;'>₹ {gross_items_val:,.0f}</span></div>", unsafe_allow_html=True)
        mi2.markdown(f"<div style='text-align:center; background:#f8fafc; border-radius:10px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>TDS (1%)</span><br><span style='font-size:1.15rem; font-weight:800; color:#f59e0b;'>₹ {tds_items_val:,.0f}</span></div>", unsafe_allow_html=True)
        mi3.markdown(f"<div style='text-align:center; background:#f8fafc; border-radius:10px; padding:10px;'><span style='color:#64748b; font-weight:700; font-size:0.8rem; text-transform:uppercase;'>Net Payable</span><br><span style='font-size:1.15rem; font-weight:800; color:#10b981;'>₹ {net_items_val:,.0f}</span></div>", unsafe_allow_html=True)
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
    def_date = pd.to_datetime(def_date_str).date()
    
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
        <div style='display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 15px; border-radius: 12px; margin-top: 10px; margin-bottom: 20px; border: 1px solid #e2e8f0;'>
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
    def_date = pd.to_datetime(def_date_str).date()
    
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

# --- 6. MAIN PAGE NAVIGATION (custom buttons, replaces st.tabs for guaranteed styling) ---
st.markdown("<h1 style='color:#0f172a; margin-bottom: 20px;'>💸 Team & Vendor Billing</h1>", unsafe_allow_html=True)

BILLING_NAV_PAGES = [
    ("invoice", "📄 Invoice Entry"),
    ("payment", "💳 Payment Entry"),
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

    inv_team_opts = ["All Teams"]
    if inv_data_raw:
        _teams = sorted(set(str(r.get("team_name", "")).strip() for r in inv_data_raw if str(r.get("team_name", "")).strip()))
        inv_team_opts += _teams

    col_search, col_teamfilter, col_addbtn, col_dl, col_zip = st.columns([2.6, 1.8, 1.6, 1.4, 1.8])

    with col_search:
        search_inv = st_keyup("Search", placeholder="🔍 Search Invoices...", label_visibility="collapsed", key="search_inv_input")
    with col_teamfilter:
        team_filter_inv = st.selectbox("Team Filter", options=inv_team_opts, label_visibility="collapsed", key="inv_team_filter")
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

            if team_filter_inv and team_filter_inv != "All Teams" and "team_name" in df_inv.columns:
                df_inv = df_inv[df_inv["team_name"].astype(str).str.strip() == team_filter_inv]

            if search_inv:
                mask = df_inv.astype(str).apply(lambda x: x.str.contains(search_inv, case=False, na=False)).any(axis=1)
                df_inv = df_inv[mask]

            with col_dl:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_inv.to_excel(writer, index=False, sheet_name='Invoices')
                st.download_button(label="📥 Excel", data=buffer.getvalue(), file_name="Invoices_List.xlsx", use_container_width=True, type="secondary", key="dl_inv_btn")

            with col_zip:
                if team_filter_inv and team_filter_inv != "All Teams" and not df_inv.empty:
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
                        if pd.notna(amt_v):
                            tds_v = amt_v * 0.01
                            net_v = amt_v - tds_v
                        else:
                            tds_v = None
                            net_v = None

                        with st.container(border=True):
                            st.markdown(f"""
                                <div class="billing-card-title">#{pos + 1} — {cell(row_dict.get('team_name'))}</div>
                                <div class="billing-card-sub">{cell(row_dict.get('invoice_no'))} • {cell(row_dict.get('date'))}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Project ID</span><span class="billing-card-value">{cell(row_dict.get('project_id'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site ID</span><span class="billing-card-value">{cell(row_dict.get('site_id'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site Name</span><span class="billing-card-value">{cell(row_dict.get('site_name'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Cluster</span><span class="billing-card-value">{cell(row_dict.get('cluster'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Basic Amount</span><span class="billing-card-value">{'₹ %s' % format(basic_v, ',.0f') if pd.notna(basic_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">GST Amount</span><span class="billing-card-value">{'₹ %s' % format(gst_v, ',.0f') if pd.notna(gst_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">TDS (1%)</span><span class="billing-card-value">{'₹ %s' % format(tds_v, ',.0f') if tds_v is not None else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Total (Net)</span><span class="billing-card-value" style="color:#4f46e5;font-weight:800;">{'₹ %s' % format(net_v, ',.0f') if net_v is not None else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Vendor</span><span class="billing-card-value">{cell(row_dict.get('vendor_name'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{cell(row_dict.get('remark'))}</span></div>
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
                                    try:
                                        supabase.table("billing_invoices").delete().eq("id", rid).execute()
                                        st.success("✅ Deleted successfully!")
                                        fetch_billing_invoices_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
                else:
                    # ---------------------------------------------------------------
                    # DESKTOP WIDE TABLE VIEW
                    # ---------------------------------------------------------------
                    INV_COL_RATIOS = [0.35, 0.35, 0.35, 0.35, 1.1, 1.1, 0.9, 0.9, 0.9, 1.1, 0.9, 1.0, 1.0, 0.9, 1.0, 1.1, 1.3]
                    INV_COL_LABELS = ["#", "⚙️", "📥", "🗑️", "TEAM", "INVOICE NO.", "DATE", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC AMT", "GST AMT", "TDS", "TOTAL (NET)", "VENDOR", "REMARK"]

                    with st.container(key="inv_table_header"):
                        h_cols = st.columns(INV_COL_RATIOS)
                        for h_col, label in zip(h_cols, INV_COL_LABELS):
                            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

                    with st.container(key="inv_table_wrap", height=500):
                        for pos, (_, row) in enumerate(df_inv.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            rcols = st.columns(INV_COL_RATIOS)

                            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)

                            with rcols[1]:
                                if st.button("⚙️", key=f"inv_mgr_{rid}", help="Edit Invoice", use_container_width=True):
                                    if row_dict.get("invoice_type") == "Team":
                                        team_invoice_dialog(row_dict)
                                    else:
                                        vendor_invoice_dialog(row_dict)
                            with rcols[2]:
                                try:
                                    pdf_bytes_row = generate_invoice_pdf(row_dict)
                                    file_no_row = str(row_dict.get("invoice_no", "") or "invoice").replace("/", "-").replace(" ", "_")
                                    st.download_button(
                                        "📥", data=pdf_bytes_row, file_name=f"Invoice_{file_no_row}.pdf",
                                        mime="application/pdf", key=f"inv_dl_{rid}", help="Download Invoice PDF",
                                        use_container_width=True
                                    )
                                except Exception:
                                    st.button("📥", key=f"inv_dl_{rid}", help="PDF generation error", use_container_width=True, disabled=True)
                            with rcols[3]:
                                if st.button("🗑️", key=f"inv_del_{rid}", help="Delete Invoice", use_container_width=True):
                                    try:
                                        supabase.table("billing_invoices").delete().eq("id", rid).execute()
                                        st.success("✅ Deleted successfully!")
                                        fetch_billing_invoices_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")

                            rcols[4].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('team_name'))}</div>", unsafe_allow_html=True)
                            rcols[5].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('invoice_no'))}</div>", unsafe_allow_html=True)
                            rcols[6].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('date'))}</div>", unsafe_allow_html=True)
                            rcols[7].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('project_id'))}</div>", unsafe_allow_html=True)
                            rcols[8].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_id'))}</div>", unsafe_allow_html=True)
                            rcols[9].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_name'))}</div>", unsafe_allow_html=True)
                            rcols[10].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('cluster'))}</div>", unsafe_allow_html=True)

                            basic_v = row_dict.get('basic_amount')
                            rcols[11].markdown(f"<div class='tbl-cell'>₹ {basic_v:,.0f}</div>" if pd.notna(basic_v) else "<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                            gst_v = row_dict.get('gst_amount')
                            rcols[12].markdown(f"<div class='tbl-cell'>₹ {gst_v:,.0f}</div>" if pd.notna(gst_v) else "<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                            amt_v = row_dict.get('amount')
                            if pd.notna(amt_v):
                                tds_v = amt_v * 0.01
                                net_v = amt_v - tds_v
                                rcols[13].markdown(f"<div class='tbl-cell' style='color:#f59e0b;'>₹ {tds_v:,.0f}</div>", unsafe_allow_html=True)
                                rcols[14].markdown(f"<div class='tbl-cell' style='font-weight:800;color:#4f46e5;'>₹ {net_v:,.0f}</div>", unsafe_allow_html=True)
                            else:
                                rcols[13].markdown("<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                                rcols[14].markdown("<div class='tbl-cell'>-</div>", unsafe_allow_html=True)

                            rcols[15].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('vendor_name'))}</div>", unsafe_allow_html=True)
                            rcols[16].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('remark'))}</div>", unsafe_allow_html=True)
            else:
                st.info("No invoices match your search.")
        else:
            st.info("No invoices found. Click the buttons above to add one.")
            with col_dl:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_inv_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

# ==========================================
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
                                <div class="billing-card-title">#{pos + 1} — {cell(row_dict.get('pay_to'))}</div>
                                <div class="billing-card-sub">{cell(row_dict.get('date'))} • {cell(row_dict.get('pay_type'))} • {cell(row_dict.get('mode'))}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Pay From</span><span class="billing-card-value">{cell(row_dict.get('pay_from'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Amount</span><span class="billing-card-value" style="color:#4f46e5;font-weight:800;">{'₹ %s' % format(amt_v, ',.0f') if pd.notna(amt_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{cell(row_dict.get('remark'))}</span></div>
                            """, unsafe_allow_html=True)

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.button("⚙️ Manage", key=f"payc_mgr_{rid}", use_container_width=True):
                                    payment_dialog(row_data=row_dict, mode=row_dict.get("mode", "Team"))
                            with bc2:
                                if st.button("🗑️ Delete", key=f"payc_del_{rid}", use_container_width=True):
                                    try:
                                        supabase.table("billing_payments").delete().eq("id", rid).execute()
                                        st.success("✅ Deleted successfully!")
                                        fetch_billing_payments_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
                else:
                    # ---------------------------------------------------------------
                    # DESKTOP WIDE TABLE VIEW
                    # ---------------------------------------------------------------
                    PAY_COL_RATIOS = [0.35, 0.35, 0.35, 1.0, 1.0, 1.0, 1.0, 0.9, 1.4, 0.8]
                    PAY_COL_LABELS = ["#", "⚙️", "🗑️", "PAY FROM", "PAY TO", "PAY TYPE", "AMOUNT", "DATE", "REMARK", "MODE"]

                    with st.container(key="pay_table_header"):
                        h_cols = st.columns(PAY_COL_RATIOS)
                        for h_col, label in zip(h_cols, PAY_COL_LABELS):
                            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

                    with st.container(key="pay_table_wrap", height=500):
                        for pos, (_, row) in enumerate(df_pay.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            rcols = st.columns(PAY_COL_RATIOS)

                            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)

                            with rcols[1]:
                                if st.button("⚙️", key=f"pay_mgr_{rid}", help="Edit Payment", use_container_width=True):
                                    payment_dialog(row_data=row_dict, mode=row_dict.get("mode", "Team"))
                            with rcols[2]:
                                if st.button("🗑️", key=f"pay_del_{rid}", help="Delete Payment", use_container_width=True):
                                    try:
                                        supabase.table("billing_payments").delete().eq("id", rid).execute()
                                        st.success("✅ Deleted successfully!")
                                        fetch_billing_payments_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")

                            rcols[3].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('pay_from'))}</div>", unsafe_allow_html=True)
                            rcols[4].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('pay_to'))}</div>", unsafe_allow_html=True)
                            rcols[5].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('pay_type'))}</div>", unsafe_allow_html=True)
                            amt_v = row_dict.get('amount')
                            rcols[6].markdown(f"<div class='tbl-cell' style='font-weight:800;color:#4f46e5;'>₹ {amt_v:,.0f}</div>" if pd.notna(amt_v) else "<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                            rcols[7].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('date'))}</div>", unsafe_allow_html=True)
                            rcols[8].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('remark'))}</div>", unsafe_allow_html=True)
                            rcols[9].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('mode'))}</div>", unsafe_allow_html=True)
            else:
                st.info("No payments match your search.")
        else:
            st.info("No payments found. Click the buttons above to add one.")
            with col_dl_p:
                st.button("📥 Download Excel", disabled=True, use_container_width=True, key="dl_p_btn_disabled")
    except Exception as e:
        st.error(f"Database error: {e}")

# ==========================================
# PAGE 3: REPORTS & LEDGER
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
        df_inv_rep, df_pay_rep = pd.DataFrame(), pd.DataFrame()
        
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
                df_inv_rep["tds_amount"] = df_inv_rep["amount"] * 0.01
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
                    
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        bal = tot_inv - tot_pay
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Billed</div><div class='kpi-value-blue'>₹ {tot_inv:,.0f}</div></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Paid</div><div class='kpi-value-green'>₹ {tot_pay:,.0f}</div></div>", unsafe_allow_html=True)
        with k3:
            bal_color = "kpi-value-red" if bal > 0 else "kpi-value-green"
            st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Net Balance</div><div class='{bal_color}'>₹ {bal:,.0f}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### 📚 Invoices")
            st.dataframe(df_inv_rep, use_container_width=True, hide_index=True)
        with t2:
            st.markdown("#### 💸 Payments")
            st.dataframe(df_pay_rep, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        col_down1, col_down2, _ = st.columns([2, 2, 6])
        
        with col_down1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if not df_inv_rep.empty: df_inv_rep.to_excel(writer, index=False, sheet_name='Invoices')
                if not df_pay_rep.empty: df_pay_rep.to_excel(writer, index=False, sheet_name='Payments')
                summary_df = pd.DataFrame({"Name": [sel_name], "Total Billed": [tot_inv], "Total Paid": [tot_pay], "Balance": [bal]})
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
                pdf.rect(10, pdf.get_y(), 190, 25, 'FD')
                
                pdf.set_y(pdf.get_y() + 5)
                pdf.set_font("Arial", 'B', 11)
                
                pdf.set_text_color(*secondary_color)
                pdf.cell(63, 8, f"Total Billed: Rs. {tot_inv:,.0f}", ln=False, align='C')
                
                pdf.set_text_color(*green_color)
                pdf.cell(63, 8, f"Total Paid: Rs. {tot_pay:,.0f}", ln=False, align='C')
                
                bal_color = red_color if bal > 0 else green_color
                pdf.set_text_color(*bal_color)
                pdf.cell(64, 8, f"Net Balance: Rs. {bal:,.0f}", ln=True, align='C')
                
                pdf.ln(12)
                
                def create_table(title, df, header_color):
                    if not df.empty:
                        pdf.set_font("Arial", 'B', 12)
                        pdf.set_text_color(*header_color)
                        pdf.cell(190, 8, title, ln=True, align='L')
                        
                        pdf.set_fill_color(*header_color)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_font("Arial", 'B', 7)
                        
                        cols = df.columns.tolist()
                        
                        if len(cols) == 8:
                            col_widths = [18, 18, 22, 24, 36, 24, 20, 28]
                        else:
                            col_widths = [190 / len(cols)] * len(cols)

                        # Columns whose text should word-wrap inside its own box instead of
                        # overflowing into the next column (e.g. long Site Names).
                        wrap_cols = {"site name", "remark", "description"}
                            
                        for i, col in enumerate(cols):
                            pdf.cell(col_widths[i], 8, str(col).upper().replace('_', ' '), border=1, align='C', fill=True)
                        pdf.ln()
                        
                        pdf.set_text_color(0, 0, 0)
                        
                        fill = False
                        line_h = 4
                        for _, row in df.iterrows():
                            if fill:
                                pdf.set_fill_color(241, 245, 249)
                            else:
                                pdf.set_fill_color(255, 255, 255)

                            # First pass: compute the row's shared height from any wrapped column
                            row_vals = []
                            row_height = line_h
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
                                        val_str = str(val)[:30]
                                    is_wrap = False
                                else:
                                    val_str = str(val) if pd.notna(val) and str(val).strip() != "" else "-"
                                    is_wrap = col_lower in wrap_cols

                                row_vals.append((val_str, is_wrap, col_widths[i]))

                                if is_wrap:
                                    pdf.set_font("Arial", '', 7.5)
                                    n_lines = max(1, len(_wrap_text_for_pdf(pdf, val_str, col_widths[i])))
                                    row_height = max(row_height, n_lines * line_h)

                            # Second pass: draw all cells at the shared row height
                            x0 = pdf.get_x()
                            y0 = pdf.get_y()
                            x_cursor = x0
                            for val_str, is_wrap, w in row_vals:
                                if is_wrap:
                                    pdf.set_font("Arial", '', 7.5)
                                    pdf.set_xy(x_cursor, y0)
                                    y_before = pdf.get_y()
                                    pdf.multi_cell(w, line_h, val_str, border=1, align='L', fill=fill)
                                    used_h = pdf.get_y() - y_before
                                    if used_h < row_height:
                                        pdf.rect(x_cursor, pdf.get_y(), w, row_height - used_h, 'DF' if fill else 'D')
                                else:
                                    pdf.set_xy(x_cursor, y0)
                                    pdf.set_font("Arial", '', 7.5)
                                    pdf.cell(w, row_height, val_str, border=1, align='C', fill=fill)
                                x_cursor += w
                            pdf.set_xy(x0, y0 + row_height)
                            fill = not fill
                        pdf.ln(5)
                
                create_table("INVOICES (BILLED)", df_inv_rep, secondary_color)
                create_table("PAYMENTS (PAID)", df_pay_rep, green_color)
                
                raw = pdf.output(dest='S')
                return bytes(raw) if isinstance(raw, (bytearray, bytes)) else raw.encode('latin1')

            try:
                pdf_bytes = generate_pdf()
                st.download_button(label="📄 Download PDF", data=pdf_bytes, file_name=f"{sel_name}_Report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(str(e))

# ==========================================
# PAGE 4: PENDING MRN APPROVAL
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
            # ---> UPDATED: Added .order("id", desc=True) so latest pending records appear at the top
            pending_rows = fetch_pending_mrn_cached(active_ws)
            if pending_rows:
                df_pending = pd.DataFrame(pending_rows).reset_index(drop=True)

                display_dates = (
                    pd.to_datetime(df_pending["date"], errors="coerce").dt.strftime('%d/%m/%Y')
                    if "date" in df_pending.columns else pd.Series([""] * len(df_pending))
                )

                st.markdown("##### 🕒 Pending MRNs")

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
                                <div class="billing-card-title">#{pos + 1} — {cell(row_dict.get('team_name'))}</div>
                                <div class="billing-card-sub">{cell(row_dict.get('invoice_no'))} • {cell(display_dates.iloc[pos])}</div>
                                <div class="billing-card-row"><span class="billing-card-label">Project ID</span><span class="billing-card-value">{cell(row_dict.get('project_id'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site ID</span><span class="billing-card-value">{cell(row_dict.get('site_id'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Site Name</span><span class="billing-card-value">{cell(row_dict.get('site_name'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Cluster</span><span class="billing-card-value">{cell(row_dict.get('cluster'))}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Basic Amount</span><span class="billing-card-value">{'₹ %s' % format(basic_v, ',.0f') if pd.notna(basic_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label" style="font-weight:800;">Total</span><span class="billing-card-value" style="color:#4f46e5;font-weight:800;">{'₹ %s' % format(amt_v, ',.0f') if pd.notna(amt_v) else '-'}</span></div>
                                <div class="billing-card-row"><span class="billing-card-label">Remark</span><span class="billing-card-value">{cell(row_dict.get('remark'))}</span></div>
                            """, unsafe_allow_html=True)

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.button("✅ Approve", key=f"mrnc_app_{rid}", use_container_width=True):
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
                    # DESKTOP WIDE TABLE VIEW
                    # ---------------------------------------------------------------
                    MRN_COL_RATIOS = [0.35, 0.35, 0.35, 1.1, 1.1, 0.9, 0.9, 0.9, 1.1, 0.9, 1.0, 1.0, 1.3]
                    MRN_COL_LABELS = ["#", "✅", "❌", "TEAM", "MRN NO.", "DATE", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC AMT", "TOTAL", "REMARK"]

                    with st.container(key="mrn_table_header"):
                        h_cols = st.columns(MRN_COL_RATIOS)
                        for h_col, label in zip(h_cols, MRN_COL_LABELS):
                            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

                    with st.container(key="mrn_table_wrap", height=440):
                        for pos, (_, row) in enumerate(df_pending.iterrows()):
                            row_dict = row.to_dict()
                            rid = row_dict.get("id")
                            rcols = st.columns(MRN_COL_RATIOS)

                            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)

                            with rcols[1]:
                                if st.button("✅", key=f"mrn_app_{rid}", help="Approve MRN", use_container_width=True):
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
                            with rcols[2]:
                                if st.button("❌", key=f"mrn_rej_{rid}", help="Reject MRN", use_container_width=True):
                                    try:
                                        supabase.table("pending_billing_invoices").delete().eq("id", rid).execute()
                                        st.error("❌ Pending MRN Rejected and Deleted from Queue!")
                                        fetch_pending_mrn_cached.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error rejecting: {e}")

                            rcols[3].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('team_name'))}</div>", unsafe_allow_html=True)
                            rcols[4].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('invoice_no'))}</div>", unsafe_allow_html=True)
                            rcols[5].markdown(f"<div class='tbl-cell'>{cell(display_dates.iloc[pos])}</div>", unsafe_allow_html=True)
                            rcols[6].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('project_id'))}</div>", unsafe_allow_html=True)
                            rcols[7].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_id'))}</div>", unsafe_allow_html=True)
                            rcols[8].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_name'))}</div>", unsafe_allow_html=True)
                            rcols[9].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('cluster'))}</div>", unsafe_allow_html=True)

                            basic_v = row_dict.get('basic_amount')
                            rcols[10].markdown(f"<div class='tbl-cell'>₹ {basic_v:,.0f}</div>" if pd.notna(basic_v) else "<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                            amt_v = row_dict.get('amount')
                            rcols[11].markdown(f"<div class='tbl-cell' style='font-weight:800;color:#4f46e5;'>₹ {amt_v:,.0f}</div>" if pd.notna(amt_v) else "<div class='tbl-cell'>-</div>", unsafe_allow_html=True)
                            rcols[12].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('remark'))}</div>", unsafe_allow_html=True)
            else:
                st.info("No pending MRNs waiting for approval.")
        except Exception as e:
            st.error(f"Database error: {e}")
    elif pwd != "":
        st.error("❌ Incorrect Password!")
