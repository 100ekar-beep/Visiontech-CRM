import streamlit as st
import pandas as pd
import math
import io
import json
import re
import html
import time
from supabase import create_client, Client
from st_keyup import st_keyup
from datetime import datetime, date

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

# =========================================================================
# 🏢 COMPANY CONFIG — Visiontech & Bhagyashree
# Dono companies SAME Supabase tables use karti hain — data "workspace"
# column se alag hota hai (VISIONTECH / BHAGYASHREE).
# Ek baar run karein: add_workspace_column.sql
# =========================================================================
COMPANIES = {
    "vis": {
        "label": "🏢 VISIONTECH",
        "workspace": "VISIONTECH",
        "invoice_table": "invoice_management",
        "ers_table": "ERSprocess",
        "invdata_table": "Invoicedata",
        # ERS Checklist PDF header details
        "partner_name": "Visiontech Infra Solutions",
        "user_name": "Pramodkumar Jaju",
        "department": "Deployment",
        "email": "vispltower@gmail.com",
        "contact": "9552273181",
    },
    "bhg": {
        "label": "🏭 BHAGYASHREE",
        "workspace": "BHAGYASHREE",
        "invoice_table": "invoice_management",
        "ers_table": "ERSprocess",
        "invdata_table": "Invoicedata",
        "partner_name": "Bhagyashree Enterprises",
        "user_name": "Mr. Varpe",
        "department": "Deployment",
        "email": "project@bhagyshrienterprises.com",
        "contact": "9975522431",
    },
}

# --- INITIALIZE SESSION STATES ---
for _page_key in ["vis_inv_page", "bhg_inv_page", "ers_page", "invdata_page", "bhagya_page",
                  "saitele_page", "bhg_ers_page", "bhg_invdata_page"]:
    if _page_key not in st.session_state:
        st.session_state[_page_key] = 1

# --- 2. ✨ LAVISH LIGHT THEME CSS (Quotation / Site Data / Solar jaisa) ---
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

    /* ================= COMPANY BAR (VISIONTECH / BHAGYASHREE) ================= */
    .st-key-company_bar div[data-testid="stHorizontalBlock"] { gap: 16px !important; }
    .st-key-company_bar button {
        font-size: 1.3rem !important; font-weight: 900 !important; padding: 18px 10px !important;
        height: auto !important; border-radius: 14px !important; letter-spacing: 2px !important;
        transition: all 0.25s ease !important;
    }
    .st-key-company_bar button[kind="secondary"] {
        background: #ffffff !important; border: 2px solid rgba(0,0,0,0.10) !important;
        box-shadow: 0 2px 6px rgba(15,23,42,0.06) !important;
    }
    .st-key-company_bar button[kind="secondary"] p,
    .st-key-company_bar button[kind="secondary"] span,
    .st-key-company_bar button[kind="secondary"] div { color: #64748b !important; font-size: 1.3rem !important; font-weight: 900 !important; }
    .st-key-company_bar button[kind="secondary"]:hover { background: #f1f5f9 !important; transform: translateY(-2px) !important; }
    .st-key-company_bar button[kind="primary"] {
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%) !important; border: none !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4) !important;
    }
    .st-key-company_bar button[kind="primary"] p,
    .st-key-company_bar button[kind="primary"] span,
    .st-key-company_bar button[kind="primary"] div { color: #ffffff !important; font-size: 1.3rem !important; font-weight: 900 !important; }

    /* ================= SUB-TAB NAV BAR ================= */
    .st-key-nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 16px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-nav_bar button[kind="secondary"] {
        background: #ffffff !important; border: 1.5px solid rgba(0,0,0,0.12) !important;
        box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-nav_bar button[kind="secondary"]:hover { background: #eef2ff !important; border-color: #c7d2fe !important; transform: translateY(-2px) !important; }
    .st-key-nav_bar button[kind="secondary"] p,
    .st-key-nav_bar button[kind="secondary"] span,
    .st-key-nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; font-size: 1.05rem !important; }
    .st-key-nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; border: none !important;
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.45) !important;
    }
    .st-key-nav_bar button[kind="primary"] p,
    .st-key-nav_bar button[kind="primary"] span,
    .st-key-nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; font-size: 1.05rem !important; }

    /* ================= DIALOGS (light glass) ================= */
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

    /* Generic table-cell fallback (for small tables inside dialogs) */
    .tbl-cell { color: #1e293b; font-size: 0.86rem; }
    .tbl-head { color: #4338ca; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; }

    /* Read-only "display box" */
    .display-box-label { color: #64748b; font-size: 0.78rem; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 4px; text-transform: uppercase; }
    .display-box-value {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px;
        color: #0f172a !important; font-weight: 800 !important; font-size: 0.95rem; min-height: 20px;
    }
    div[data-testid="stTextInput"] input:disabled,
    div[data-testid="stTextInput"] input[disabled] {
        color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; opacity: 1 !important;
        font-weight: 800 !important; background-color: #f1f5f9 !important; border: 1px solid rgba(0,0,0,0.08) !important;
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

    /* ================= SCROLLING TABLE BODIES (every key ending in _table_wrap) ================= */
    div[class*="_table_wrap"] {
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
    div[class*="st-key-ilhead_"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-ilhead_"] [data-testid="stColumn"], div[class*="st-key-ilhead_"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-ilrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-ilrow_odd"] { background: #fafaff; }
    div[class*="st-key-ilrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-ilrow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .84rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
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
    .sol-amt { text-align: right; font-weight: 700; color: #334155; font-variant-numeric: tabular-nums; }
    .sol-amt.zero { color: #cbd5e1; font-weight: 600; }
    .sol-amt.strong { color: #4f46e5; font-weight: 900; font-size: .9rem; }
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

    /* Single ⚙️ popover button at row start (Site Data jaisa) */
    div[class*="st-key-ilpop_"] button {
        width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    div[class*="st-key-ilpop_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    div[class*="st-key-ilpop_"] button p, div[class*="st-key-ilpop_"] button span { color: #1e293b !important; }
    div[class*="st-key-ilpop_"] button svg { display: none !important; }

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

    /* Dialog mini-table + totals box (Bhagyashree invoice dialogs) */
    .dlg-head { color: #4338ca; font-size: 0.74rem; font-weight: 800; letter-spacing: .6px; text-transform: uppercase; }
    .dlg-cell { color: #0f172a; font-size: 0.86rem; }
    .dlg-sum {
        background: linear-gradient(90deg, #f5f3ff, #eef2ff); border: 1px solid #c7d2fe;
        padding: 14px 20px; border-radius: 12px; margin-top: 15px;
    }
    .dlg-sum-row { display: flex; justify-content: space-between; padding: 3px 0; }
    .dlg-sum-row .l { color: #475569; font-weight: 700; }
    .dlg-sum-row .v { color: #0f172a; font-weight: 800; }
    .dlg-sum-row.disc .l, .dlg-sum-row.disc .v { color: #d97706; }
    .dlg-sum-row.sep { border-top: 1px dashed #c7d2fe; margin-top: 4px; padding-top: 6px; }
    .dlg-sum-row.final { border-top: 2px solid #c7d2fe; margin-top: 6px; padding-top: 8px; }
    .dlg-sum-row.final .l, .dlg-sum-row.final .v { color: #4f46e5; font-weight: 900; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    # Must not catch its own exceptions — a failure should not be cached.
    url: str = str(st.secrets["supabase"]["url"]).strip().strip('"').strip("'")
    url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    key: str = str(st.secrets["supabase"]["key"]).strip().strip('"').strip("'")
    if not url or not key:
        raise ValueError("Supabase 'url' or 'key' is empty in secrets.toml")
    return create_client(url, key)


try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"🚨 Supabase connection error: {e}")
    st.info(
        "Ye aksar TEMPORARY hota hai (Supabase free-tier project 'sleep' me chala jaata hai, "
        "ya network ka thoda glitch). Neeche 'Retry Connection' dabao. Agar baar baar aaye "
        "to secrets.toml format check karo:\n\n"
        "[supabase]\n"
        "url = \"https://YOUR-PROJECT-REF.supabase.co\"\n"
        "key = \"YOUR-ANON-OR-SERVICE-KEY\"\n\n"
        "(url ke aage 'https://' zaroor hona chahiye, aur '/rest/v1' ya trailing slash nahi hona chahiye.)"
    )
    if st.button("🔄 Retry Connection"):
        init_connection.clear()
        st.rerun()
    st.stop()


def display_box(label, value):
    """Bold, clearly-legible read-only value box."""
    safe_val = "" if value is None else str(value)
    if safe_val.strip() == "" or safe_val.lower() == "nan":
        safe_val = "-"
    return f"""
        <div>
            <div class="display-box-label">{label}</div>
            <div class="display-box-value">{safe_val}</div>
        </div>
    """

# =========================================================================
# ERS PROCESS — "Indus Towers Invoice Submission Checklist" PDF
# Sirf ON-DEMAND download — Supabase me kabhi save nahi hota.
# Partner Name / User Name / E-Mail / Contact ab COMPANIES config se aate hain.
# =========================================================================

ERS_CHECKLIST_PART1 = [
    ("1", "Original Invoice", ["v", "v", "v", "v", "v"]),
    ("a", "Printed Invoice/Digital Invoice. No Manual correction on Printed Invoice. Manual Correction, if any, should be only PO / WCC/WCR No, which needs to be duly signed and stamped by auth. Person", ["v", "v", "v", "v", "v"]),
    ("b", 'Invoice No. should not exceed 16 characters, containing alphabets or numerals or special characters hyphen or dash and slash symbolised as "-" , "\\" and "/" respectively', ["v", "v", "v", "v", "v"]),
    ("c", "In case of debit / credit note, Number and date of the corresponding original tax invoice", ["v", "v", "v", "v", "v"]),
    ("d", "Name, Addresss & GSTIN of Partner & Indus Towers Limited on Invoice to be matched with PO", ["v", "v", "v", "v", "v"]),
    ("e", "Ship TO & Bill TO need to mention on invoices", ["v", "x", "x", "x", "x"]),
    ("f", "HSN/SAC code present on Invoice to be matched with PO/WCR", ["v", "v", "v", "v", "v"]),
    ("g", "Description of Goods/ services", ["v", "v", "v", "v", "v"]),
    ("h", "Quantity in case of goods and Unit/ Unique Quantity Code (UQC) of the same", ["v", "v", "v", "v", "v"]),
    ("i", "Taxes applied (IGST/CGST+SGST) in invoices to be matched with GRN/WCR", ["v", "v", "v", "v", "v"]),
    ("j", "Rate & Quantity should match with GRN/WCR", ["v", "v", "v", "v", "v"]),
    ("k", "In case of Agreement based invoices, rates should match with valid contract summary/valid agreement.", ["x", "x", "x", "x", "v"]),
    ("l", "Rates which are not part of PO/GBPA need to be verify through BOQ & for NON BOQ Rates circle SCM Head approval is required", ["x", "v", "v", "v", "x"]),
    ("m", "Total value of supply of goods or services should match with GRN / WCR", ["v", "v", "v", "v", "v"]),
    ("n", "Place of supply and name of State in case of inter-State Supply", ["v", "v", "v", "v", "v"]),
    ("o", "Stamp & Signature on printed invoice or digital signature on a digital invoice", ["v", "v", "v", "v", "v"]),
    ("p", "PO No & WCC/WCR No to be mentioned on Invoice. PO Date should be before Invoice Date", ["v", "v", "v", "v", "v"]),
]

ERS_CHECKLIST_PART2 = [
    ("2", "E-Waybill /LR copy", ["v", "x", "x", "x", "x"]),
    ("3", "Delivery Challans (in case multiple supply below 50K and consolidated bill above 50K is raised)", ["x", "x", "v", "x", "x"]),
    ("4", "In case of Direct Tower Supply, PDI copy is required", ["v", "x", "x", "x", "x"]),
    ("5", "Measurement sheet / Annexure sheet", ["x", "v", "x", "x", "x"]),
    ("6", "PF/ESIC/Wages Register/Returns proof attached (in case labour charges are mentioned)", ["x", "v", "v", "x", "x"]),
    ("7", "Receipt copy in cases of New connections / Load Up gradation / Transfer Installation", ["x", "x", "x", "v", "x"]),
    ("8", "Original Receipt required in EB Reimbursement bills with security & other Expense bifurcation", ["x", "x", "x", "v", "x"]),
    ("9", "Increase of HT EB Liaisoning Electricity Board approval letter required", ["x", "x", "x", "v", "x"]),
    ("10", "STN (Stock Transfer note) / MRN / SRN", ["x", "v", "x", "x", "x"]),
    ("11", "Photocopy of NOC from Gram panchayat in case of Municipal service charges", [None, None, None, None, None]),
    ("12", "Photocopy Pollution control certificate copy in case of PUC Service Depart.", [None, None, None, None, None]),
]


def _ers_draw_check(pdf, cx, cy, size=3.2):
    pdf.set_draw_color(20, 110, 20)
    pdf.set_line_width(0.45)
    x0, y0 = cx - size * 0.5, cy
    x1, y1 = cx - size * 0.12, cy + size * 0.42
    x2, y2 = cx + size * 0.55, cy - size * 0.5
    pdf.line(x0, y0, x1, y1)
    pdf.line(x1, y1, x2, y2)


def _ers_draw_cross(pdf, cx, cy, size=2.6):
    pdf.set_draw_color(160, 30, 30)
    pdf.set_line_width(0.45)
    half = size * 0.5
    pdf.line(cx - half, cy - half, cx + half, cy + half)
    pdf.line(cx - half, cy + half, cx + half, cy - half)


def _ers_wrap_text(pdf, text, max_width):
    words = text.replace("\n", " ").split(" ")
    lines = []
    current = ""
    for w in words:
        trial = (current + " " + w).strip()
        if pdf.get_string_width(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines if lines else [""]


def _wrap_code_text(pdf, text, max_width):
    """Wraps hyphen-separated codes (e.g. '12-C00000-0-01-ZZ-ZZ-013'),
    allowing a line break after each hyphen."""
    tokens = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in (" ", "-"):
            tokens.append(buf)
            buf = ""
    if buf:
        tokens.append(buf)

    lines = []
    current = ""
    for tok in tokens:
        trial = current + tok
        if pdf.get_string_width(trial.strip()) <= max_width:
            current = trial
        else:
            if current.strip():
                lines.append(current.strip())
            current = tok
    if current.strip():
        lines.append(current.strip())
    return lines if lines else [""]


def _ers_find_field(row_dict, candidates):
    """Case/space-insensitive lookup of a column value from a generic row dict."""
    if not row_dict:
        return ""
    cleaned_map = {str(k).strip().lower().replace("_", " "): k for k in row_dict.keys()}
    for cand in candidates:
        c = cand.strip().lower().replace("_", " ")
        if c in cleaned_map:
            val = row_dict.get(cleaned_map[c], "")
            if val not in (None, "", "nan"):
                return str(val)
    for cand in candidates:
        c = cand.strip().lower().replace("_", " ")
        for cleaned_key, orig_key in cleaned_map.items():
            if c in cleaned_key:
                val = row_dict.get(orig_key, "")
                if val not in (None, "", "nan"):
                    return str(val)
    return ""


def generate_ers_checklist_pdf(invoice_no, po_no, inv_date, company_key="vis"):
    """Builds the fixed Indus Towers invoice-submission-checklist PDF in memory.
    Partner/user/contact details come from COMPANIES[company_key]."""
    if FPDF is None:
        raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")

    comp = COMPANIES.get(company_key, COMPANIES["vis"])

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(8, 8, 8)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    PAGE_W = 194

    # ---------------- TITLE BAR ----------------
    pdf.set_fill_color(191, 191, 191)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(PAGE_W, 7, "Indus Towers Limited (Invoice submission checklist)", border=1, align="C", fill=True, ln=1)

    # ---------------- HEADER INFO TABLE ----------------
    label_w = 30
    value_w = 67
    row_h = 6.2

    header_rows = [
        ("Inward\nNumber-", invoice_no, "Inward Date-", inv_date),
        ("Partner\nName : -", comp.get("partner_name", ""), "Invoice No.", invoice_no),
        ("PO NO:", po_no, "Invoice Date", inv_date),
        ("User Name :-", comp.get("user_name", ""), "Depart.", comp.get("department", "")),
        ("E-Mail ID : -", comp.get("email", ""), "Contact No-", comp.get("contact", "")),
    ]

    for lbl1, val1, lbl2, val2 in header_rows:
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        pdf.set_font("Arial", "B", 8)
        pdf.multi_cell(label_w, row_h / 2 if "\n" in lbl1 else row_h, lbl1, border=1, align="L")
        pdf.set_xy(x_start + label_w, y_start)
        pdf.set_font("Arial", "", 8.5)
        pdf.cell(value_w, row_h, " " + str(val1), border=1, align="L")
        pdf.set_font("Arial", "B", 8)
        pdf.cell(label_w, row_h, lbl2, border=1, align="L")
        pdf.set_font("Arial", "", 8.5)
        pdf.cell(value_w, row_h, " " + str(val2), border=1, align="L", ln=1)
        pdf.set_xy(x_start, y_start + row_h)

    # ---------------- CHECKLIST TABLE ----------------
    col_widths = [10, 68, 16, 24, 24, 22, 30]
    headers_row2 = ["S.No.", "Particulars", "Supply\n(Y/N)", "TSP\n(Electrical/\nCivil & others)", "IME/OME/SMS/\nSME", "EB/Liasio\nning", "Others Services\n(Legal/Rent etc.)"]

    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(sum(col_widths[:3]), 4.3, "", border=1)
    pdf.cell(sum(col_widths[3:]), 4.3, "Services", border=1, align="C")
    pdf.ln(4.3)

    pdf.set_font("Arial", "B", 7)
    y_h = pdf.get_y()
    x_h = pdf.get_x()
    max_lines = max(len(h.split("\n")) for h in headers_row2)
    hdr_line_h = 2.9
    hdr_h = hdr_line_h * max_lines
    for w, h in zip(col_widths, headers_row2):
        xx = pdf.get_x()
        pdf.multi_cell(w, hdr_line_h, h, border=1, align="C")
        pdf.set_xy(xx + w, y_h)
    pdf.set_xy(x_h, y_h + hdr_h)

    def render_row(no_label, particulars, marks):
        pdf.set_font("Arial", "", 7)
        lines = _ers_wrap_text(pdf, particulars, col_widths[1] - 2)
        line_h = 3.05
        row_height = max(line_h * len(lines), 4.8)

        x_row = pdf.get_x()
        y_row = pdf.get_y()

        pdf.multi_cell(col_widths[0], row_height, no_label, border=1, align="C")
        pdf.set_xy(x_row + col_widths[0], y_row)
        pdf.multi_cell(col_widths[1], line_h, particulars, border=1, align="L")
        cur_y = pdf.get_y()
        if cur_y < y_row + row_height:
            pdf.rect(x_row + col_widths[0], cur_y, col_widths[1], (y_row + row_height) - cur_y)

        cx = x_row + col_widths[0] + col_widths[1]
        for i, w in enumerate(col_widths[2:]):
            pdf.rect(cx, y_row, w, row_height)
            mark = marks[i] if i < len(marks) else None
            if mark == "v":
                _ers_draw_check(pdf, cx + w / 2, y_row + row_height / 2)
            elif mark == "x":
                _ers_draw_cross(pdf, cx + w / 2, y_row + row_height / 2)
            cx += w

        pdf.set_xy(x_row, y_row + row_height)

    for no_label, particulars, marks in ERS_CHECKLIST_PART1:
        if pdf.get_y() + 6 > 290:
            pdf.add_page()
        render_row(no_label, particulars, marks)

    if pdf.get_y() + 6 > 290:
        pdf.add_page()
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_fill_color(235, 235, 235)
    pdf.cell(sum(col_widths), 4.5, "  Mandatory Documents", border=1, align="L", fill=True, ln=1)

    for no_label, particulars, marks in ERS_CHECKLIST_PART2:
        if pdf.get_y() + 6 > 290:
            pdf.add_page()
        render_row(no_label, particulars, marks)

    if pdf.get_y() + 14 > 290:
        pdf.add_page()
    pdf.ln(2)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(PAGE_W, 5, "PHD USE ONLY", border=1, ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(PAGE_W, 7, "  PHD Inward No.(Mandatory)", border=1, ln=1)

    out = pdf.output(dest='S')
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return out.encode('latin1')


def _ers_pdf_filename(invoice_no):
    inv_no_for_name = invoice_no or "ERS"
    slashes_replaced = str(inv_no_for_name).replace("/", "-").replace("\\", "-")
    safe_name = "".join(c for c in slashes_replaced if c.isalnum() or c in ("-", "_")) or "ERS_Checklist"
    return f"DOC_{safe_name}.pdf"


# --- SAFE DATE PARSER HELPER ---
def parse_date_safely(val):
    if not val or str(val).strip() in ['', '-', 'nan', 'None']:
        return None
    val_str = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None

# =========================================================================
# GENERIC HELPERS (used by ERS Process & Invoice Data tabs)
# =========================================================================

@st.cache_data(ttl=30, show_spinner=False)
def _fetch_table_data(table_name, workspace=None):
    """Fetch table data with retries. Failures are raised (never cached).
    workspace diya ho to sirf usi workspace ki rows aati hain."""
    last_error = None
    for attempt in range(3):
        try:
            query = supabase.table(table_name).select("*")
            if workspace:
                query = query.eq("workspace", workspace)
            response = query.execute()
            return response.data or []
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(2)

    raise RuntimeError(
        f"Could not load table '{table_name}' after 3 attempts: {last_error}"
    )


def get_table_df(table_name, workspace=None):
    """Fetch a Supabase table into a DataFrame, newest (highest id) first."""
    try:
        data = _fetch_table_data(table_name, workspace)
    except Exception as e:
        st.error(f"⚠️ Could not load table '{table_name}': {e}")
        data = []

    if data:
        df = pd.DataFrame(data)
        if 'id' in df.columns:
            id_numeric = pd.to_numeric(df['id'], errors='coerce')
            if id_numeric.notna().any():
                df['id_num'] = id_numeric.fillna(-1)
                df = df.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
            else:
                df = df.iloc[::-1].reset_index(drop=True)
    else:
        df = pd.DataFrame()
    return df


get_table_df.clear = _fetch_table_data.clear


def field_widget(col_name, value, key, container):
    """Renders the right input widget for a column based on its name, returns the value to save."""
    cl = col_name.lower()
    if 'date' in cl:
        parsed = parse_date_safely(value) if value not in (None, '') else None
        raw = container.date_input(col_name.replace("_", " ").title(), value=parsed, key=key)
        return raw.strftime("%Y-%m-%d") if raw else None
    elif any(k in cl for k in ['amount', 'gst', 'total', 'balance', 'percentage', 'price', 'rate']) and 'number' not in cl:
        try:
            fv = float(value) if value not in (None, '', 'nan') else 0.0
        except (ValueError, TypeError):
            fv = 0.0
        return container.number_input(col_name.replace("_", " ").title(), value=fv, format="%.2f", key=key)
    else:
        sv = "" if value is None else str(value)
        if sv.lower() == 'nan':
            sv = ""
        return container.text_input(col_name.replace("_", " ").title(), value=sv, key=key)


@st.dialog("➕ Add Record", width="large")
def generic_add_dialog(table_name, columns, prefix, workspace=None):
    st.caption(f"Add a new record to {table_name}")
    values = {}

    if not columns:
        st.info("Table has no records yet, so columns can't be auto-detected. Define fields below (name + value), then save.")
        editor_df = pd.DataFrame({"Field": [""], "Value": [""]})
        edited = st.data_editor(editor_df, num_rows="dynamic", use_container_width=True, key=f"{prefix}_add_kv_editor")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Record", type="primary", use_container_width=True, key=f"{prefix}_add_kv_save"):
            insert_data = {}
            for _, r in edited.iterrows():
                f = str(r.get("Field", "")).strip()
                v = str(r.get("Value", "")).strip()
                if f:
                    insert_data[f] = v
            if insert_data:
                if workspace:
                    insert_data["workspace"] = workspace
                try:
                    supabase.table(table_name).insert(insert_data).execute()
                    st.success("✅ Record Added!")
                    get_table_df.clear()
                    st.session_state[f"{prefix}_page"] = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving: {e}")
            else:
                st.warning("Please define at least one field.")
        return

    chunks = [columns[i:i + 4] for i in range(0, len(columns), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            values[col_name] = field_widget(col_name, "", f"{prefix}_add_{col_name}", c)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Record", type="primary", use_container_width=True, key=f"{prefix}_add_save"):
        if workspace:
            values["workspace"] = workspace
        try:
            supabase.table(table_name).insert(values).execute()
            st.success("✅ Record Added!")
            get_table_df.clear()
            st.session_state[f"{prefix}_page"] = 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error Saving: {e}")


@st.dialog("✏️ Edit Record", width="large")
def generic_edit_dialog(table_name, row_data, columns, prefix):
    st.caption("Update record")
    rid = row_data.get('id')
    values = {}
    data_cols = [c for c in columns if c != 'id']

    chunks = [data_cols[i:i + 4] for i in range(0, len(data_cols), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            values[col_name] = field_widget(col_name, row_data.get(col_name, ""), f"{prefix}_edit_{col_name}_{rid}", c)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Update Record", type="primary", use_container_width=True, key=f"{prefix}_edit_save_{rid}"):
        try:
            supabase.table(table_name).update(values).eq("id", rid).execute()
            st.success("✅ Updated Successfully!")
            get_table_df.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error Updating: {e}")


@st.dialog("👁️ View Record", width="large")
def generic_view_dialog(row_data, columns, prefix):
    st.caption("Read-only preview")
    rid = row_data.get('id')
    data_cols = [c for c in columns if c != 'id']

    chunks = [data_cols[i:i + 4] for i in range(0, len(data_cols), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            val = row_data.get(col_name, "")
            c.text_input(col_name.replace("_", " ").title(), value="" if val is None else str(val), disabled=True, key=f"{prefix}_view_{col_name}_{rid}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True, key=f"{prefix}_view_close_{rid}"):
        st.rerun()


@st.dialog("🗑️ Confirm Deletion", width="small")
def generic_delete_dialog(table_name, rid, label, prefix):
    st.warning(f"Delete record '{label}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True, key=f"{prefix}_del_cancel_{rid}"):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True, key=f"{prefix}_del_confirm_{rid}"):
            try:
                supabase.table(table_name).delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


# =========================================================================
# ✨ LAVISH TABLE RENDER HELPERS (shared by all tables on this page)
# =========================================================================
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


def _money(v, style=""):
    if not _clean(v):
        return "<div class='slux-cell sol-amt zero'>—</div>"
    val = _num(v)
    cls = "zero" if val == 0 and not style else style
    shown = f"{val:,.2f}".rstrip('0').rstrip('.')
    return f"<div class='slux-cell sol-amt {cls}'>₹ {shown}</div>"


def _date_cell(v):
    s = _clean(v)
    if not s:
        return _MUTED
    d = parse_date_safely(s[:10])
    shown = d.strftime("%d %b %Y") if d else s
    return f"<div class='slux-cell slux-soft' title='{html.escape(s)}'>{html.escape(shown)}</div>"


def status_badge(val):
    v = _clean(val)
    if not v:
        return _MUTED
    vl = v.lower()
    if vl == "not required":
        cls = "status-grey"
    elif "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "available", "paid", "received", "cleared"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress", "submitted", "process"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<div class='slux-cell'><span class='status-badge {cls}'>{html.escape(v)}</span></div>"


def _auto_cell(col_name, val):
    """Picks a lavish style automatically from the column name (for generic tables)."""
    cl = str(col_name).lower()
    if 'date' in cl:
        return _date_cell(val)
    if 'status' in cl:
        return status_badge(val)
    if any(k in cl for k in ['amount', 'gst', 'total', 'balance', 'price', 'rate', 'value']) and 'number' not in cl and ' no' not in cl:
        return _money(val, "strong" if 'total' in cl else "")
    if 'invoice' in cl and any(k in cl for k in ['number', 'no', 'num']):
        return _chip(val, "inv")
    if 'project' in cl and 'name' not in cl:
        return _chip(val, "proj")
    if any(k in cl for k in ['number', ' no', '_no', 'site id', 'site_id', 'code']):
        return _chip(val)
    if 'circle' in cl or 'cluster' in cl:
        return _pill(val)
    if 'name' in cl:
        return _txt(val, "slux-strong")
    return _txt(val)


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
            h_col.markdown(f"<div class='slux-th{cls}' title='{html.escape(str(label))}'>{html.escape(str(label))}</div>", unsafe_allow_html=True)


def table_min_width_css(wrap_key, min_width):
    st.markdown(
        f"<style>"
        f".st-key-{wrap_key} [data-testid='stHorizontalBlock'],"
        f".st-key-{wrap_key} div[class*='st-key-ilhead_'],"
        f".st-key-{wrap_key} div[class*='st-key-ilrow_'] {{ min-width: {min_width}px !important; }}"
        f"</style>",
        unsafe_allow_html=True,
    )


def table_footer(left_html, right_html=""):
    st.markdown(f'<div class="slux-foot"><div>{left_html}</div><div class="slux-foot-amts">{right_html}</div></div>', unsafe_allow_html=True)


def empty_state(msg):
    st.markdown(f'<div class="slux-empty"><div>🗂️</div>{html.escape(msg)}</div>', unsafe_allow_html=True)


def serial_cell(n):
    return f"<div style='text-align:center;'><span class='slux-num'>{n}</span></div>"


def row_key_for(rid, fallback):
    return rid if (rid is not None and str(rid).strip() not in ("", "nan", "None")) else fallback


def pager(page_state_key, total_pages, total_rows, key_prefix, label="Total Records"):
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state[page_state_key] == 1), key=f"{key_prefix}_prev"):
            st.session_state[page_state_key] -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state[page_state_key]} of {total_pages} ({label}: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state[page_state_key] == total_pages), key=f"{key_prefix}_next"):
            st.session_state[page_state_key] += 1
            st.rerun()


def render_generic_tab(table_name, prefix, tab_title, icon, pdf_button=False, company_key="vis", workspace=None):
    """Full CRUD tab for any Supabase table. pdf_button=True adds the ERS
    checklist PDF download (company details taken from COMPANIES[company_key])."""

    if f"{prefix}_page" not in st.session_state:
        st.session_state[f"{prefix}_page"] = 1

    col_title, col_ref, col_add, col_export = st.columns([3, 1, 1.5, 1.5])
    with col_title:
        st.markdown(f"<h2 style='margin:0; color:#0f172a;'>{icon} {tab_title}</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key=f"{prefix}_refresh"):
            get_table_df.clear()
            st.rerun()

    df = get_table_df(table_name, workspace)
    # 'workspace' column user ko dikhana/edit karna nahi — code khud set karta hai
    if workspace and 'workspace' in df.columns:
        df = df.drop(columns=['workspace'])
    known_cols = [c for c in df.columns if c != 'id'] if not df.empty else st.session_state.get(f"{prefix}_columns", [])
    if not df.empty:
        st.session_state[f"{prefix}_columns"] = known_cols

    with col_add:
        if st.button("➕ Add Record", use_container_width=True, key=f"{prefix}_add_btn"):
            generic_add_dialog(table_name, known_cols, prefix, workspace)
    with col_export:
        if st.button("📥 Export Data", use_container_width=True, key=f"{prefix}_export_btn"):
            st.session_state[f"{prefix}_action"] = "export"

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get(f"{prefix}_action") == "export":
        export_df = df.copy()
        if "id" in export_df.columns:
            export_df = export_df.drop(columns=["id"])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name=tab_title[:31])
        st.download_button(
            f"📊 Download {tab_title} Excel",
            data=buffer.getvalue(),
            file_name=f"{table_name}_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key=f"{prefix}_dl_btn"
        )
        st.session_state[f"{prefix}_action"] = ""

    if df.empty:
        empty_state(f"No records found in '{table_name}'. Click ➕ Add Record to create the first one.")
        return

    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown(f"<h5 style='margin:0; color:#0f172a;'>🗄️ {tab_title} Records</h5>", unsafe_allow_html=True)
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search...", label_visibility="collapsed", key=f"{prefix}_search")

    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    rows_per_page = 10
    total_rows = len(df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state[f"{prefix}_page"] > total_pages:
        st.session_state[f"{prefix}_page"] = total_pages
    elif st.session_state[f"{prefix}_page"] < 1:
        st.session_state[f"{prefix}_page"] = 1

    start_idx = (st.session_state[f"{prefix}_page"] - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df.iloc[start_idx:end_idx].copy()

    data_cols = [c for c in df.columns if c != 'id']
    col_ratios = [0.55, 0.5] + [1.2] * len(data_cols)
    col_labels = ["⚙️", "#"] + [c.replace("_", " ").title() for c in data_cols]

    wrap_key = f"{prefix}_table_wrap"
    min_width = max(1000, 140 + len(data_cols) * 150)
    table_min_width_css(wrap_key, min_width)

    table_title_bar(f"{icon} {tab_title}", "newest first • scroll right for more →" if len(data_cols) > 6 else "newest first", f"{total_rows:,} records")

    with st.container(key=wrap_key, height=560):
        if df_page.empty:
            empty_state("No records found.")
        else:
            table_header_row(f"ilhead_{prefix}", col_ratios, col_labels, center_idx=(0, 1))

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                serial_no = start_idx + page_pos + 1
                rk = row_key_for(rid, f"s{serial_no}")
                parity = "odd" if serial_no % 2 else "even"

                with st.container(key=f"ilrow_{parity}_{prefix}_{rk}"):
                    rcols = st.columns(col_ratios, vertical_alignment="center")

                    with rcols[0]:
                        label_val = str(row_dict.get(data_cols[0], rid)) if data_cols else str(rid)
                        with st.container(key=f"ilpop_{prefix}_{rk}"):
                            with st.popover("⚙️"):
                                if st.button("👁️ Open", key=f"{prefix}_view_{rid}", use_container_width=True):
                                    generic_view_dialog(row_dict, df.columns.tolist(), prefix)
                                if st.button("✏️ Edit", key=f"{prefix}_editbtn_{rid}", use_container_width=True):
                                    generic_edit_dialog(table_name, row_dict, df.columns.tolist(), prefix)
                                if st.button("🗑️ Delete", key=f"{prefix}_delbtn_{rid}", use_container_width=True):
                                    generic_delete_dialog(table_name, rid, label_val, prefix)
                                if pdf_button:
                                    guess_inv = _ers_find_field(row_dict, [
                                        "tally invoice number", "tally invoice no", "tally_invoice_number", "tally invoice",
                                        "invoice_number", "invoice no", "invoiceno", "invoice num", "invoice_no",
                                        "inv number", "inv no", "invno", "inv_no", "bill number", "bill no",
                                        "invoice", "ers number", "ers no", "ers_number"
                                    ])
                                    guess_po = _ers_find_field(row_dict, ["po_number", "po no", "ponumber", "po", "po num"])
                                    guess_date = _ers_find_field(row_dict, ["date", "invoice_date", "invoice date"])
                                    try:
                                        pdf_bytes = generate_ers_checklist_pdf(guess_inv, guess_po, guess_date, company_key)
                                        st.download_button(
                                            "📥 Download PDF", data=pdf_bytes,
                                            file_name=_ers_pdf_filename(guess_inv), mime="application/pdf",
                                            key=f"{prefix}_pdfdl_{rid}", use_container_width=True
                                        )
                                    except Exception as e:
                                        st.button("⚠️ PDF Error", key=f"{prefix}_pdferr_{rid}", help=str(e), use_container_width=True, disabled=True)

                    rcols[1].markdown(serial_cell(serial_no), unsafe_allow_html=True)
                    for idx, k in enumerate(data_cols, start=2):
                        rcols[idx].markdown(_auto_cell(k, row_dict.get(k, '')), unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    table_footer(
        f'{total_rows:,} record{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small>',
        f'<span class="slux-foot-badge">Page {st.session_state[f"{prefix}_page"]} of {total_pages}</span>',
    )

    st.markdown("<br>", unsafe_allow_html=True)
    pager(f"{prefix}_page", total_pages, total_rows, prefix)

# =========================================================================
# BHAGYASHREE INVOICE (Visiontech ke andar) — Custom PO-based invoice builder
# (Pramodkumar / Radhika Jaju -> Bhagyashree Enterprises)
# =========================================================================

BHAGYA_WORKSPACE = "BHAGYASHREE"
BHAGYA_TABLE = "bhagyashree_invoices"

HSN_TABLE = "HSN"


@st.cache_data(ttl=60, show_spinner=False)
def get_hsn_map():
    """Item Code -> HSN dict (cached 60s)."""
    try:
        res = supabase.table(HSN_TABLE).select("item_code, hsn").execute()
        rows = res.data if res.data else []
    except Exception:
        rows = []
    return {str(r.get("item_code", "")).strip(): str(r.get("hsn", "")).strip() for r in rows if r.get("item_code")}


WORKSPACE_DISCOUNT_PCT = {
    "BHAGYASHREE": 2.0,
    "SAITELE": 5.0,
}

BILL_FROM_DETAILS = {
    "Pramodkumar Jaju": {
        "letterhead_name": "Pramodkumar Jaju",
        "full_name": "Pramodkumar B. Jaju",
        "address": "Near Vikas Mitra Madal Chowk, Survey No 8/9/7, House No 81, Santkrupa Building, Canal Road, Lane Number 2, Karve Nagar, Pune, Pune, Maharashtra, 411052",
        "pan": "AJBPJ0233E",
        "contact_person": "Pramodkumar Jaju",
        "mobile": "9552273181",
        "state": "Maharashtra, Code : 27",
        "invoice_prefix": "PRAMO",
    },
    "Radhika Jaju": {
        "letterhead_name": "Radhika Jaju",
        "full_name": "Radhika P. Jaju",
        "address": "Near Vikas Mitra Madal Chowk, Survey No 8/9/7, House No 81, Santkrupa Building, Canal Road, Lane Number 2, Karve Nagar, Pune, Pune, Maharashtra, 411052",
        "pan": "CCOPR9903F",
        "contact_person": "Radhika Jaju",
        "mobile": "9742514121",
        "state": "Maharashtra, Code : 27",
        "invoice_prefix": "RADH",
    },
}


def bhagya_next_invoice_number(bill_from):
    """Return the next seller-wise invoice number, e.g. PRAMO-001/RADH-001."""
    prefix = BILL_FROM_DETAILS.get(bill_from, {}).get("invoice_prefix", "INV")
    highest = 0
    try:
        result = supabase.table(BHAGYA_TABLE).select("invoice_no").execute()
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$", re.IGNORECASE)
        for record in (result.data or []):
            match = pattern.match(str(record.get("invoice_no", "")).strip())
            if match:
                highest = max(highest, int(match.group(1)))
    except Exception:
        pass
    return f"{prefix}-{highest + 1:03d}"


BILL_TO_DETAILS = {
    BHAGYA_WORKSPACE: {
        "full_name": "Bhagyashree Enterprises",
        "address": "S. No. 66, Sai Pritam Nagar Rahtani, BLD - A Flat - 7 Pune Pune,Maharashtra-411017,India.",
        "gstin": "27ABWPV2922M1ZQ",
        "state": "Maharashtra, Code : 27",
    },
}


def _po_field(po_dict, candidates):
    """Case/space-insensitive lookup of a value from a PO-line dict."""
    if not po_dict:
        return ""
    low_map = {str(k).strip().lower().replace("_", " "): k for k in po_dict.keys()}
    for cand in candidates:
        c = cand.strip().lower().replace("_", " ")
        if c in low_map:
            val = po_dict.get(low_map[c], "")
            if val not in (None, "", "nan"):
                return str(val)
    return ""


_NUM_WORDS_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                   "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                   "Seventeen", "Eighteen", "Nineteen"]
_NUM_WORDS_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two_digit_words(n):
    if n < 20:
        return _NUM_WORDS_ONES[n]
    tens, ones = divmod(n, 10)
    return (_NUM_WORDS_TENS[tens] + (" " + _NUM_WORDS_ONES[ones] if ones else "")).strip()


def _three_digit_words(n):
    parts = []
    if n >= 100:
        parts.append(_NUM_WORDS_ONES[n // 100] + " Hundred")
        n %= 100
    if n:
        parts.append(_two_digit_words(n))
    return " ".join(parts)


def number_to_words_indian(num):
    """Indian-numbering-system words (Crore/Lakh/Thousand)."""
    num = int(round(num))
    if num == 0:
        return "Zero"
    crore, num = divmod(num, 10000000)
    lakh, num = divmod(num, 100000)
    thousand, hundred = divmod(num, 1000)
    parts = []
    if crore:
        parts.append(_three_digit_words(crore) + " Crore")
    if lakh:
        parts.append(_three_digit_words(lakh) + " Lakh")
    if thousand:
        parts.append(_three_digit_words(thousand) + " Thousand")
    if hundred:
        parts.append(_three_digit_words(hundred))
    return " ".join(parts).strip()


def amount_in_words_inr(amount):
    return f"INR {number_to_words_indian(amount)} Only"


@st.cache_data(ttl=30, show_spinner=False)
def bhagya_get_site_options():
    """Sites where workspace = BHAGYASHREE, minus project_ids already invoiced."""
    try:
        site_res = supabase.table("site_data").select("*").eq("workspace", BHAGYA_WORKSPACE).execute()
        sites = site_res.data if site_res.data else []
    except Exception as e:
        st.error(f"❌ Error fetching sites: {e}")
        sites = []

    try:
        inv_res = supabase.table(BHAGYA_TABLE).select("project_id").eq("workspace", BHAGYA_WORKSPACE).execute()
        already_invoiced = set(r.get("project_id") for r in (inv_res.data or []) if r.get("project_id"))
    except Exception:
        already_invoiced = set()

    site_map = {}
    for s in sites:
        pid = str(s.get("Project ID", "")).strip()
        if pid and pid not in already_invoiced and pid not in site_map:
            site_map[pid] = s
    return site_map


@st.cache_data(ttl=30, show_spinner=False)
def bhagya_get_po_lines(site_id):
    try:
        res = supabase.table("po_working").select("*") \
            .eq("workspace", BHAGYA_WORKSPACE).eq("Site ID", site_id).execute()
        rows = res.data if res.data else []
        rows.sort(key=lambda r: (r.get("Line Number") is None, r.get("Line Number")))
        return rows
    except Exception:
        return []


def bhagya_generate_pdf(row_data):
    """Bhagyashree tax-invoice PDF, built in memory for download only."""
    if FPDF is None:
        raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")

    bill_from = row_data.get("bill_from", "")
    bf_details = BILL_FROM_DETAILS.get(bill_from, {"full_name": bill_from, "address": "", "gstin": ""})
    bt_details = BILL_TO_DETAILS.get(BHAGYA_WORKSPACE, {"full_name": "Bhagyashree Enterprises", "address": "", "gstin": ""})

    line_items = row_data.get("line_items", [])
    if isinstance(line_items, str):
        try:
            line_items = json.loads(line_items)
        except Exception:
            line_items = []

    discount_pct = row_data.get("discount_pct", WORKSPACE_DISCOUNT_PCT.get(BHAGYA_WORKSPACE, 0.0)) or 0.0
    discount_factor = 1 - (discount_pct / 100.0)

    subtotal_v = row_data.get("subtotal", 0) or 0
    taxable_amount_v = row_data.get("taxable_amount", subtotal_v * discount_factor) or 0
    cgst_v = row_data.get("cgst", 0) or 0
    sgst_v = row_data.get("sgst", 0) or 0
    total_v = row_data.get("total", 0) or 0

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(8, 8, 8)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    PAGE_W = 194

    # ---------------- LETTERHEAD ----------------
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(15, 40, 110)
    pdf.cell(PAGE_W, 8, str(bf_details.get("letterhead_name", bill_from)), align="C", ln=1)
    pdf.set_draw_color(15, 40, 110)
    pdf.set_line_width(0.6)
    pdf.line(8, pdf.get_y() + 1, 8 + PAGE_W, pdf.get_y() + 1)
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)

    # ---------------- TITLE BAR ----------------
    pdf.set_fill_color(230, 230, 230)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(PAGE_W, 8, "INVOICE", border=1, align="C", fill=True, ln=1)

    # ---------------- BILL TO / SHIP TO (left) | SELLER (right) ----------------
    col_w = PAGE_W / 2.0
    line_h = 4.2
    pdf.set_font("Arial", "", 8.5)

    left_lines = []
    left_lines.append(("B", f"Bill To : {bt_details.get('full_name', '')}"))
    for ln in _ers_wrap_text(pdf, bt_details.get("address", ""), col_w - 4):
        left_lines.append(("", ln))
    left_lines.append(("", f"GSTIN No : {bt_details.get('gstin', '')}"))
    left_lines.append(("", ""))
    left_lines.append(("B", f"Ship To : {bt_details.get('full_name', '')}"))
    for ln in _ers_wrap_text(pdf, bt_details.get("address", ""), col_w - 4):
        left_lines.append(("", ln))
    left_lines.append(("", f"GSTIN No : {bt_details.get('gstin', '')}"))

    right_lines = []
    right_lines.append(("B", str(bf_details.get("full_name", ""))))
    for ln in _ers_wrap_text(pdf, bf_details.get("address", ""), col_w - 4):
        right_lines.append(("", ln))
    if bf_details.get("state"):
        right_lines.append(("", f"State Name : {bf_details.get('state', '')}"))
    if bf_details.get("gstin"):
        right_lines.append(("", f"GSTIN/UIN : {bf_details.get('gstin', '')}"))
    if bf_details.get("pan"):
        right_lines.append(("", f"PAN : {bf_details.get('pan', '')}"))
    if bf_details.get("contact_person"):
        right_lines.append(("", f"Contact : {bf_details.get('contact_person', '')}  Mobile : {bf_details.get('mobile', '')}"))
    if bf_details.get("email"):
        right_lines.append(("", f"E-Mail : {bf_details.get('email', '')}"))

    max_lines = max(len(left_lines), len(right_lines))
    box_x = pdf.get_x()
    box_top_y = pdf.get_y()
    for i in range(max_lines):
        y = box_top_y + i * line_h
        if i < len(left_lines):
            style, txt = left_lines[i]
            pdf.set_xy(box_x, y)
            pdf.set_font("Arial", style, 9 if style == "B" else 8.3)
            pdf.cell(col_w, line_h, " " + txt if txt else "", border="LR")
        else:
            pdf.set_xy(box_x, y)
            pdf.cell(col_w, line_h, "", border="LR")
        if i < len(right_lines):
            style, txt = right_lines[i]
            pdf.set_xy(box_x + col_w, y)
            pdf.set_font("Arial", style, 10 if style == "B" else 8.3)
            pdf.cell(col_w, line_h, " " + txt if txt else "", border="LR")
        else:
            pdf.set_xy(box_x + col_w, y)
            pdf.cell(col_w, line_h, "", border="LR")

    box_bottom_y = box_top_y + max_lines * line_h
    pdf.line(box_x, box_top_y, box_x + PAGE_W, box_top_y)
    pdf.line(box_x, box_bottom_y, box_x + PAGE_W, box_bottom_y)
    pdf.line(box_x + col_w, box_top_y, box_x + col_w, box_bottom_y)
    pdf.set_xy(box_x, box_bottom_y)

    # ---------------- INVOICE DETAILS GRID ----------------
    label_w = 32
    value_w = PAGE_W / 2.0 - label_w
    row_h = 6
    detail_rows = [
        ("Invoice Number", row_data.get("invoice_no", ""), "Invoice Date", str(row_data.get("invoice_date", ""))),
        ("Project ID", row_data.get("project_id", ""), "Site ID", row_data.get("site_id", "")),
        ("Site Name", row_data.get("site_name", ""), "Cluster", row_data.get("cluster", "")),
        ("Project Name", row_data.get("project_name", ""), "Place of Supply", bt_details.get("state", "Maharashtra")),
    ]
    for lbl1, val1, lbl2, val2 in detail_rows:
        pdf.set_font("Arial", "B", 8)
        pdf.cell(label_w, row_h, lbl1, border=1)
        pdf.set_font("Arial", "", 8.3)
        pdf.cell(value_w, row_h, " " + str(val1), border=1)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(label_w, row_h, lbl2, border=1)
        pdf.set_font("Arial", "", 8.3)
        pdf.cell(value_w, row_h, " " + str(val2), border=1, ln=1)

    pdf.ln(2)

    # ---------------- LINE ITEMS TABLE ----------------
    widths = [8, 13, 27, 39, 10, 16, 20, 18, 18, 25]
    headers_row = ["Line", "HSN", "Item\nCode", "Description", "Qty", "Price",
                   "Basic\nAmount", "CGST\nAmount", "SGST\nAmount", "Total\nAmount"]

    pdf.set_font("Arial", "B", 7.2)
    pdf.set_fill_color(59, 130, 246)
    pdf.set_text_color(255, 255, 255)
    y_h = pdf.get_y()
    x_h = pdf.get_x()
    hdr_line_h = 3.0
    max_hdr_lines = max(len(h.split("\n")) for h in headers_row)
    hdr_h = hdr_line_h * max_hdr_lines
    for w, h in zip(widths, headers_row):
        xx = pdf.get_x()
        pdf.multi_cell(w, hdr_line_h, h, border=1, align="C", fill=True)
        pdf.set_xy(xx + w, y_h)
    pdf.set_xy(x_h, y_h + hdr_h)

    pdf.set_text_color(0, 0, 0)
    fill = False
    line_h2 = 3.1
    hsn_map = get_hsn_map()
    for li in line_items:
        qty = li.get("claim_qty", 0) or 0
        raw_price = li.get("price", 0) or 0
        disc_rate = raw_price * discount_factor
        disc_basic = qty * disc_rate
        disc_cgst = disc_basic * 0.09
        disc_sgst = disc_basic * 0.09
        disc_total = disc_basic + disc_cgst + disc_sgst
        hsn = hsn_map.get(str(li.get("item_code", "")).strip()) or li.get("hsn") or "-"
        description = str(li.get("description", ""))

        pdf.set_font("Arial", "", 7.2)
        desc_lines = _ers_wrap_text(pdf, description, widths[3] - 2)
        code_lines = _wrap_code_text(pdf, str(li.get("item_code", "")), widths[2] - 2)
        row_h2 = max(line_h2 * len(desc_lines), line_h2 * len(code_lines), 6) + 1.5

        x_row = pdf.get_x()
        y_row = pdf.get_y()
        pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)

        pdf.cell(widths[0], row_h2, str(li.get("line_number", "")), border=1, align="C", fill=fill)
        pdf.cell(widths[1], row_h2, str(hsn), border=1, align="C", fill=fill)

        fill_style = "DF" if fill else "D"

        x_code = pdf.get_x()
        pdf.rect(x_code, y_row, widths[2], row_h2, style=fill_style)
        for i, ln in enumerate(code_lines):
            pdf.set_xy(x_code, y_row + 1 + i * line_h2)
            pdf.cell(widths[2], line_h2, ln, align="C")
        pdf.set_xy(x_code + widths[2], y_row)

        x_desc = pdf.get_x()
        pdf.rect(x_desc, y_row, widths[3], row_h2, style=fill_style)
        for i, ln in enumerate(desc_lines):
            pdf.set_xy(x_desc + 1, y_row + 1 + i * line_h2)
            pdf.cell(widths[3] - 2, line_h2, ln, align="L")
        pdf.set_xy(x_desc + widths[3], y_row)

        cx = x_desc + widths[3]
        numeric_vals = [str(qty), f"{disc_rate:,.2f}", f"{disc_basic:,.2f}", f"{disc_cgst:,.2f}", f"{disc_sgst:,.2f}", f"{disc_total:,.2f}"]
        for w, v in zip(widths[4:], numeric_vals):
            pdf.rect(cx, y_row, w, row_h2)
            pdf.set_xy(cx, y_row + max((row_h2 - 3.2) / 2, 0))
            pdf.cell(w - 1, 3.2, v, align="R")
            cx += w

        pdf.set_xy(x_row, y_row + row_h2)
        fill = not fill

    # ---------------- TOTAL ROW ----------------
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_fill_color(235, 235, 235)
    lead_w = sum(widths[:6])
    pdf.cell(lead_w, 6, "  TOTAL", border=1, align="L", fill=True)
    pdf.cell(widths[6], 6, f"{taxable_amount_v:,.2f}", border=1, align="R", fill=True)
    pdf.cell(widths[7], 6, f"{cgst_v:,.2f}", border=1, align="R", fill=True)
    pdf.cell(widths[8], 6, f"{sgst_v:,.2f}", border=1, align="R", fill=True)
    pdf.cell(widths[9], 6, f"{total_v:,.2f}", border=1, align="R", fill=True, ln=1)

    pdf.ln(3)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(PAGE_W, 7, f"Total Amount : {total_v:,.2f}", border=0, align="R", ln=1)

    pdf.ln(2)
    pdf.set_font("Arial", "B", 8.5)
    pdf.cell(30, 5, "Amount In Words :", border=0)
    pdf.set_font("Arial", "", 8.5)
    pdf.multi_cell(PAGE_W - 30, 5, amount_in_words_inr(total_v))

    pdf.ln(1)
    pdf.set_font("Arial", "", 7.5)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(PAGE_W, 4, f"(Price & Basic Amount above are already net of the {discount_pct:.0f}% discount before GST.)", ln=1)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(PAGE_W, 5, f"for {bf_details.get('full_name', '')}", align="R", ln=1)
    pdf.ln(10)
    pdf.set_font("Arial", "", 9)
    pdf.cell(PAGE_W, 5, "Authorised Signatory", align="R", ln=1)

    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, (bytes, bytearray)):
        return bytes(pdf_output)
    return pdf_output.encode('latin1')

def _bhagya_summary_html(subtotal, discount_pct, discount_amount, taxable_amount, cgst, sgst, total):
    """Light-theme totals box used by the Bhagyashree add/edit dialogs."""
    return f"""
        <div class="dlg-sum">
            <div class="dlg-sum-row"><span class="l">Subtotal</span><span class="v">₹ {subtotal:,.0f}</span></div>
            <div class="dlg-sum-row disc"><span class="l">Discount ({discount_pct:.0f}%)</span><span class="v">- ₹ {discount_amount:,.0f}</span></div>
            <div class="dlg-sum-row sep"><span class="l">Taxable Amount</span><span class="v">₹ {taxable_amount:,.0f}</span></div>
            <div class="dlg-sum-row"><span class="l">CGST (9%)</span><span class="v">₹ {cgst:,.0f}</span></div>
            <div class="dlg-sum-row"><span class="l">SGST (9%)</span><span class="v">₹ {sgst:,.0f}</span></div>
            <div class="dlg-sum-row final"><span class="l">Final Amount</span><span class="v">₹ {total:,.0f}</span></div>
        </div>
    """


def _dlg_cell(v, color=None, bold=False):
    style = ""
    if color:
        style += f"color:{color};"
    if bold:
        style += "font-weight:800;"
    return f"<div class='dlg-cell' style='{style}'>{html.escape(str(v))}</div>"


@st.dialog("➕ Add New Invoice (Bhagyashree)", width="large")
def bhagya_add_invoice_dialog():
    st.caption("PO Working ke saamne wale Claim Qty bharke invoice banayein")

    bf1, bf2 = st.columns(2)
    with bf1:
        bill_from = st.selectbox("Bill From *", options=list(BILL_FROM_DETAILS.keys()), key="bhagya_bill_from")
    with bf2:
        invoice_no = bhagya_next_invoice_number(bill_from)
        st.text_input("Invoice No (Auto Generated)", value=invoice_no, disabled=True, key=f"bhagya_inv_no_{bill_from}")

    site_map = bhagya_get_site_options()
    project_options = ["Select"] + sorted(site_map.keys())

    pc1, pc2 = st.columns(2)
    with pc1:
        selected_pid = st.selectbox("Project ID *", options=project_options, key="bhagya_project_id")
    with pc2:
        invoice_date = st.date_input("Invoice Date", value=date.today(), format="DD/MM/YYYY", key="bhagya_inv_date")

    if selected_pid == "Select":
        st.info("Pehle ek Project ID select karein.")
        return

    site_row = site_map.get(selected_pid, {})
    site_id = site_row.get("Site ID", "")

    st.markdown('<div class="modal-section-title">📍 SITE DETAILS</div>', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    with d1: st.markdown(display_box("Site ID", site_row.get("Site ID", "")), unsafe_allow_html=True)
    with d2: st.markdown(display_box("Site Name", site_row.get("Site Name", "")), unsafe_allow_html=True)
    with d3: st.markdown(display_box("Cluster", site_row.get("Cluster", "")), unsafe_allow_html=True)
    with d4: st.markdown(display_box("Project Name", site_row.get("Project Name", "")), unsafe_allow_html=True)

    st.markdown('<div class="modal-section-title">📦 PO LINE ITEMS — Enter Claim Qty</div>', unsafe_allow_html=True)
    po_lines = bhagya_get_po_lines(site_id)

    if not po_lines:
        st.warning("Is Project ID ke liye PO Working me koi line nahi mili.")
        return

    h_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
    for c, label in zip(h_cols, ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]):
        c.markdown(f"<span class='dlg-head'>{label}</span>", unsafe_allow_html=True)

    line_items = []
    subtotal = 0.0
    hsn_map = get_hsn_map()
    for po in po_lines:
        r_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
        line_no = po.get("Line Number", "")
        item_code = po.get("Item Num", "")
        description = po.get("Description", "")
        po_qty = po.get("PO Qty", 0) or 0
        price = po.get("Price", 0) or 0

        r_cols[0].markdown(_dlg_cell(line_no), unsafe_allow_html=True)
        r_cols[1].markdown(_dlg_cell(item_code), unsafe_allow_html=True)
        r_cols[2].markdown(_dlg_cell(description), unsafe_allow_html=True)
        r_cols[3].markdown(_dlg_cell(po_qty), unsafe_allow_html=True)
        r_cols[4].markdown(_dlg_cell(f"{price:,.0f}"), unsafe_allow_html=True)

        claim_qty = r_cols[5].number_input(
            "Claim Qty", min_value=0, max_value=int(po_qty) if po_qty else 0, step=1, value=0,
            key=f"bhagya_claim_{line_no}_{item_code}", label_visibility="collapsed"
        )
        amount = claim_qty * price
        r_cols[6].markdown(_dlg_cell(f"{amount:,.0f}", "#4f46e5", True), unsafe_allow_html=True)

        subtotal += amount
        line_items.append({
            "line_number": line_no,
            "item_code": item_code,
            "description": description,
            "po_qty": po_qty,
            "price": price,
            "claim_qty": claim_qty,
            "amount": amount,
            "hsn": hsn_map.get(str(item_code).strip()) or _po_field(po, ["hsn", "hsn code", "hsn/sac"]),
        })

    discount_pct = WORKSPACE_DISCOUNT_PCT.get(BHAGYA_WORKSPACE, 0.0)
    discount_amount = subtotal * (discount_pct / 100.0)
    taxable_amount = subtotal - discount_amount

    cgst = taxable_amount * 0.09
    sgst = taxable_amount * 0.09
    total = taxable_amount + cgst + sgst

    st.markdown(_bhagya_summary_html(subtotal, discount_pct, discount_amount, taxable_amount, cgst, sgst, total), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Invoice", type="primary", use_container_width=True, key="bhagya_save_btn"):
        if subtotal <= 0:
            st.error("⚠️ Kam se kam ek line me Claim Qty > 0 dalein!")
        else:
            invoice_no = bhagya_next_invoice_number(bill_from)
            payload = {
                "workspace": BHAGYA_WORKSPACE,
                "invoice_no": invoice_no.strip(),
                "invoice_date": str(invoice_date),
                "bill_from": bill_from,
                "project_id": selected_pid,
                "site_id": site_row.get("Site ID", ""),
                "site_name": site_row.get("Site Name", ""),
                "cluster": site_row.get("Cluster", ""),
                "project_name": site_row.get("Project Name", ""),
                "line_items": line_items,
                "subtotal": subtotal,
                "discount_pct": discount_pct,
                "discount_amount": discount_amount,
                "taxable_amount": taxable_amount,
                "cgst": cgst,
                "sgst": sgst,
                "total": total,
            }
            try:
                supabase.table(BHAGYA_TABLE).insert(payload).execute()
                st.success("✅ Invoice Saved! Neeche table me ⚙️ button se PDF download kar sakte hain.")
                get_table_df.clear()
                bhagya_get_site_options.clear()
                st.session_state.bhagya_page = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving invoice: {e}")


@st.dialog("🧾 Invoice Detail & Download", width="large")
def bhagya_view_invoice_dialog(row_data):
    st.caption(f"Invoice No: {row_data.get('invoice_no','')}")

    d1, d2, d3, d4 = st.columns(4)
    with d1: st.markdown(display_box("Bill From", row_data.get("bill_from", "")), unsafe_allow_html=True)
    with d2: st.markdown(display_box("Project ID", row_data.get("project_id", "")), unsafe_allow_html=True)
    with d3: st.markdown(display_box("Site ID", row_data.get("site_id", "")), unsafe_allow_html=True)
    with d4: st.markdown(display_box("Invoice Date", str(row_data.get("invoice_date", ""))), unsafe_allow_html=True)

    st.markdown(display_box(
        "Site Name / Cluster / Project Name",
        f"{row_data.get('site_name','')} | {row_data.get('cluster','')} | {row_data.get('project_name','')}"
    ), unsafe_allow_html=True)

    line_items = row_data.get("line_items", [])
    if isinstance(line_items, str):
        try:
            line_items = json.loads(line_items)
        except Exception:
            line_items = []

    st.markdown('<div class="modal-section-title">📦 LINE ITEMS</div>', unsafe_allow_html=True)
    h_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
    for c, label in zip(h_cols, ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]):
        c.markdown(f"<span class='dlg-head'>{label}</span>", unsafe_allow_html=True)
    for li in line_items:
        r_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
        r_cols[0].markdown(_dlg_cell(li.get('line_number','')), unsafe_allow_html=True)
        r_cols[1].markdown(_dlg_cell(li.get('item_code','')), unsafe_allow_html=True)
        r_cols[2].markdown(_dlg_cell(li.get('description','')), unsafe_allow_html=True)
        r_cols[3].markdown(_dlg_cell(li.get('po_qty','')), unsafe_allow_html=True)
        r_cols[4].markdown(_dlg_cell(f"{li.get('price',0):,.0f}"), unsafe_allow_html=True)
        r_cols[5].markdown(_dlg_cell(li.get('claim_qty','')), unsafe_allow_html=True)
        r_cols[6].markdown(_dlg_cell(f"{li.get('amount',0):,.0f}", "#059669", True), unsafe_allow_html=True)

    subtotal_v = row_data.get('subtotal', 0) or 0
    discount_pct_v = row_data.get('discount_pct', 0) or 0
    discount_amount_v = row_data.get('discount_amount', 0) or 0
    taxable_amount_v = row_data.get('taxable_amount', subtotal_v - discount_amount_v) or 0
    gst_v = (row_data.get('cgst', 0) or 0) + (row_data.get('sgst', 0) or 0)
    total_v = row_data.get('total', 0) or 0

    st.markdown(f"""
        <div class="dlg-sum">
            <div class="dlg-sum-row"><span class="l">Subtotal</span><span class="v">₹ {subtotal_v:,.0f}</span></div>
            <div class="dlg-sum-row disc"><span class="l">Discount ({discount_pct_v:.0f}%)</span><span class="v">- ₹ {discount_amount_v:,.0f}</span></div>
            <div class="dlg-sum-row sep"><span class="l">Taxable Amount</span><span class="v">₹ {taxable_amount_v:,.0f}</span></div>
            <div class="dlg-sum-row"><span class="l">CGST + SGST</span><span class="v" style="color:#d97706;">₹ {gst_v:,.0f}</span></div>
            <div class="dlg-sum-row final"><span class="l">Final Amount</span><span class="v" style="color:#059669;">₹ {total_v:,.0f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_dl, col_close = st.columns(2)
    with col_dl:
        try:
            pdf_bytes = bhagya_generate_pdf(row_data)
            st.download_button(
                "📄 Download PDF", data=pdf_bytes,
                file_name=f"{row_data.get('invoice_no','invoice')}.pdf", mime="application/pdf",
                use_container_width=True, type="primary"
            )
        except Exception as e:
            st.error(str(e))
    with col_close:
        if st.button("Close", use_container_width=True):
            st.rerun()


@st.dialog("✏️ Edit Invoice (Bhagyashree)", width="large")
def bhagya_edit_invoice_dialog(row_data):
    """Edit Bill From / Invoice No / Date and Claim Qty. Project/Site stay fixed."""
    rid = row_data.get("id")
    st.caption(f"Editing Invoice No: {row_data.get('invoice_no','')}")

    existing_line_items = row_data.get("line_items", [])
    if isinstance(existing_line_items, str):
        try:
            existing_line_items = json.loads(existing_line_items)
        except Exception:
            existing_line_items = []
    existing_qty_map = {
        (li.get("line_number"), li.get("item_code")): li.get("claim_qty", 0)
        for li in existing_line_items
    }

    bf1, bf2 = st.columns(2)
    with bf1:
        bf_options = list(BILL_FROM_DETAILS.keys())
        current_bf = row_data.get("bill_from", bf_options[0] if bf_options else "")
        bf_index = bf_options.index(current_bf) if current_bf in bf_options else 0
        bill_from = st.selectbox("Bill From *", options=bf_options, index=bf_index, key=f"bhagya_edit_bf_{rid}")
    with bf2:
        invoice_no = st.text_input("Invoice No *", value=row_data.get("invoice_no", ""), key=f"bhagya_edit_no_{rid}")

    dc1, dc2 = st.columns(2)
    with dc1:
        parsed_date = parse_date_safely(row_data.get("invoice_date", "")) or date.today()
        invoice_date = st.date_input("Invoice Date", value=parsed_date, format="DD/MM/YYYY", key=f"bhagya_edit_date_{rid}")
    with dc2:
        st.markdown(display_box("Project ID", row_data.get("project_id", "")), unsafe_allow_html=True)

    site_id = row_data.get("site_id", "")

    st.markdown('<div class="modal-section-title">📍 SITE DETAILS</div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1: st.markdown(display_box("Site ID", site_id), unsafe_allow_html=True)
    with d2: st.markdown(display_box("Site Name", row_data.get("site_name", "")), unsafe_allow_html=True)
    with d3: st.markdown(display_box("Cluster", row_data.get("cluster", "")), unsafe_allow_html=True)

    st.markdown('<div class="modal-section-title">📦 PO LINE ITEMS — Update Claim Qty</div>', unsafe_allow_html=True)
    po_lines = bhagya_get_po_lines(site_id)
    if not po_lines:
        st.warning("Is site ke liye PO Working me koi line nahi mili.")
        return

    h_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
    for c, label in zip(h_cols, ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]):
        c.markdown(f"<span class='dlg-head'>{label}</span>", unsafe_allow_html=True)

    line_items = []
    subtotal = 0.0
    hsn_map = get_hsn_map()
    for po in po_lines:
        r_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
        line_no = po.get("Line Number", "")
        item_code = po.get("Item Num", "")
        description = po.get("Description", "")
        po_qty = po.get("PO Qty", 0) or 0
        price = po.get("Price", 0) or 0

        r_cols[0].markdown(_dlg_cell(line_no), unsafe_allow_html=True)
        r_cols[1].markdown(_dlg_cell(item_code), unsafe_allow_html=True)
        r_cols[2].markdown(_dlg_cell(description), unsafe_allow_html=True)
        r_cols[3].markdown(_dlg_cell(po_qty), unsafe_allow_html=True)
        r_cols[4].markdown(_dlg_cell(f"{price:,.0f}"), unsafe_allow_html=True)

        default_qty = int(existing_qty_map.get((line_no, item_code), 0) or 0)
        max_qty = int(po_qty) if po_qty else 0
        claim_qty = r_cols[5].number_input(
            "Claim Qty", min_value=0, max_value=max_qty, step=1, value=min(default_qty, max_qty),
            key=f"bhagya_edit_claim_{rid}_{line_no}_{item_code}", label_visibility="collapsed"
        )
        amount = claim_qty * price
        r_cols[6].markdown(_dlg_cell(f"{amount:,.0f}", "#4f46e5", True), unsafe_allow_html=True)

        subtotal += amount
        line_items.append({
            "line_number": line_no,
            "item_code": item_code,
            "description": description,
            "po_qty": po_qty,
            "price": price,
            "claim_qty": claim_qty,
            "amount": amount,
            "hsn": hsn_map.get(str(item_code).strip()) or _po_field(po, ["hsn", "hsn code", "hsn/sac"]),
        })

    discount_pct = WORKSPACE_DISCOUNT_PCT.get(BHAGYA_WORKSPACE, 0.0)
    discount_amount = subtotal * (discount_pct / 100.0)
    taxable_amount = subtotal - discount_amount
    cgst = taxable_amount * 0.09
    sgst = taxable_amount * 0.09
    total = taxable_amount + cgst + sgst

    st.markdown(_bhagya_summary_html(subtotal, discount_pct, discount_amount, taxable_amount, cgst, sgst, total), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Update Invoice", type="primary", use_container_width=True, key=f"bhagya_edit_save_{rid}"):
        if not invoice_no.strip():
            st.error("⚠️ Invoice No is required!")
        elif subtotal <= 0:
            st.error("⚠️ Kam se kam ek line me Claim Qty > 0 dalein!")
        else:
            payload = {
                "invoice_no": invoice_no.strip(),
                "invoice_date": str(invoice_date),
                "bill_from": bill_from,
                "line_items": line_items,
                "subtotal": subtotal,
                "discount_pct": discount_pct,
                "discount_amount": discount_amount,
                "taxable_amount": taxable_amount,
                "cgst": cgst,
                "sgst": sgst,
                "total": total,
            }
            try:
                supabase.table(BHAGYA_TABLE).update(payload).eq("id", rid).execute()
                st.success("✅ Invoice Updated Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating invoice: {e}")


@st.dialog("🗑️ Confirm Deletion", width="small")
def bhagya_delete_dialog(rid, invoice_no):
    st.warning(f"Delete invoice '{invoice_no}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True, key=f"bhagya_del_cancel_{rid}"):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True, key=f"bhagya_del_confirm_{rid}"):
            try:
                supabase.table(BHAGYA_TABLE).delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                get_table_df.clear()
                bhagya_get_site_options.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


@st.dialog("📤 Bulk Update HSN (from Tally Export)", width="large")
def bhagya_bulk_hsn_dialog():
    st.caption(
        "Tally ke GST Rate Setup / HSN export ki Excel/CSV file yahan upload karo. Isme "
        "'Item Code' aur 'HSN' naam ke (ya milte-julte) do columns hone chahiye. Ye seedha "
        "dedicated 'HSN' table me save hoga (Item Code -> HSN) — invoice PDF wahi se HSN uthata hai."
    )
    uploaded_file = st.file_uploader("Choose Excel/CSV File", type=["xlsx", "xls", "csv"], key="bhagya_hsn_file")

    if uploaded_file and st.button("🚀 Process & Update HSN", type="primary", use_container_width=True, key="bhagya_hsn_process"):
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            cols_lower = {str(c).strip().lower(): c for c in df_upload.columns}

            code_col = None
            for cand in ["item code", "item num", "item number", "code", "stock item", "item name", "particulars"]:
                if cand in cols_lower:
                    code_col = cols_lower[cand]
                    break

            hsn_col = None
            for cand in ["hsn", "hsn code", "hsn/sac", "hsn sac", "sac", "hsn/sac code", "hsn code/sac code"]:
                if cand in cols_lower:
                    hsn_col = cols_lower[cand]
                    break

            if not code_col or not hsn_col:
                st.error(
                    f"❌ Item Code / HSN column nahi mil paaya. File me ye columns hain: "
                    f"{list(df_upload.columns)}. Column ka naam 'Item Code' aur 'HSN' (ya 'HSN/SAC') jaisa rakho."
                )
            else:
                upserted = 0
                skipped = 0
                errors = []
                for _, row in df_upload.iterrows():
                    item_code = str(row.get(code_col, "")).strip()
                    hsn_val = str(row.get(hsn_col, "")).strip()
                    if not item_code or not hsn_val or item_code.lower() == "nan" or hsn_val.lower() == "nan":
                        skipped += 1
                        continue
                    try:
                        supabase.table(HSN_TABLE).upsert(
                            {"item_code": item_code, "hsn": hsn_val}, on_conflict="item_code"
                        ).execute()
                        upserted += 1
                    except Exception as e:
                        errors.append(f"{item_code}: {e}")

                st.success(f"✅ Done! {upserted} item codes saved/updated in the HSN table.")
                if skipped:
                    st.info(f"ℹ️ {skipped} rows skipped (blank Item Code or HSN value).")
                if errors:
                    st.warning(f"⚠️ {len(errors)} error(s). First few: {errors[:5]}")
                    if any("HSN" in str(e) or "does not exist" in str(e) for e in errors):
                        st.error(
                            "Lagta hai 'HSN' table Supabase me abhi bana hi nahi hai. Pehle "
                            "create_and_populate_hsn_table.sql script Supabase SQL Editor me run karo."
                        )
                get_hsn_map.clear()
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")


def render_bhagyashree_tab():
    col_title, col_ref, col_hsn, col_add = st.columns([3, 1, 1.6, 1.5])
    with col_title:
        st.markdown("<h2 style='margin:0; color:#0f172a;'>🏢 Bhagyashree Invoice</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key="bhagya_refresh"):
            get_table_df.clear()
            bhagya_get_site_options.clear()
            st.rerun()
    with col_hsn:
        if st.button("📤 Bulk Update HSN", use_container_width=True, key="bhagya_hsn_btn"):
            bhagya_bulk_hsn_dialog()
    with col_add:
        if st.button("➕ Add New Invoice", use_container_width=True, key="bhagya_add_btn"):
            bhagya_add_invoice_dialog()

    st.markdown("<br>", unsafe_allow_html=True)

    df = get_table_df(BHAGYA_TABLE)

    # ---- KPI cards ----
    if not df.empty:
        k_taxable = sum(_num(v) for v in df["taxable_amount"]) if "taxable_amount" in df.columns else 0.0
        k_gst = (sum(_num(v) for v in df["cgst"]) if "cgst" in df.columns else 0.0) + (sum(_num(v) for v in df["sgst"]) if "sgst" in df.columns else 0.0)
        k_total = sum(_num(v) for v in df["total"]) if "total" in df.columns else 0.0
        st.markdown(
            '<div class="lux-kpi-grid">'
            + kpi_card("🧾", "Total Invoices", f"{len(df):,}", "Pramodkumar + Radhika", *KPI_INDIGO)
            + kpi_card("📦", "Taxable Amount", f"₹ {k_taxable:,.0f}", "After discount", *KPI_AMBER)
            + kpi_card("🏛️", "GST (CGST + SGST)", f"₹ {k_gst:,.0f}", "18% total", *KPI_PINK)
            + kpi_card("💰", "Grand Total", f"₹ {k_total:,.0f}", "All invoices", *KPI_GREEN, value_cls="green")
            + '</div>',
            unsafe_allow_html=True,
        )

    if not df.empty:
        buffer = io.BytesIO()
        export_df = df.drop(columns=[c for c in ["line_items"] if c in df.columns])
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Bhagyashree Invoices')
        st.download_button(
            "📥 Download Excel", data=buffer.getvalue(),
            file_name="Bhagyashree_Invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="bhagya_dl_btn"
        )

    if 'bhagya_page' not in st.session_state:
        st.session_state.bhagya_page = 1

    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Bhagyashree Invoices</h5>", unsafe_allow_html=True)
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search...", label_visibility="collapsed", key="bhagya_search")

    if df.empty:
        empty_state("Abhi tak koi invoice nahi bani. ➕ Add New Invoice se shuru karein.")
        return

    view_df = df.copy()
    if search_query:
        mask = view_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        view_df = view_df[mask]

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    rows_per_page = 10
    total_rows = len(view_df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
    if st.session_state.bhagya_page > total_pages: st.session_state.bhagya_page = total_pages
    elif st.session_state.bhagya_page < 1: st.session_state.bhagya_page = 1
    start_idx = (st.session_state.bhagya_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    page_df = view_df.iloc[start_idx:end_idx]

    b_cols = ["⚙️", "#", "Invoice No", "Date", "Bill From", "Project ID", "Site ID", "Site Name", "Basic", "GST", "Total"]
    b_ratios = [0.55, 0.5, 1.2, 1.0, 1.3, 1.3, 1.1, 1.6, 1.0, 1.0, 1.1]

    view_total = sum(_num(v) for v in view_df["total"]) if "total" in view_df.columns else 0.0
    table_min_width_css("bhagya_table_wrap", 1450)
    table_title_bar("🏢 Bhagyashree Invoices", "newest first", f"₹ {view_total:,.0f}")

    with st.container(key="bhagya_table_wrap", height=520):
        table_header_row("ilhead_bhagya", b_ratios, b_cols, center_idx=(0, 1), right_idx=(8, 9, 10))

        for pos, (_, row) in enumerate(page_df.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + pos + 1
            rk = row_key_for(rid, f"s{serial_no}")
            parity = "odd" if serial_no % 2 else "even"

            with st.container(key=f"ilrow_{parity}_bhagya_{rk}"):
                r_cols = st.columns(b_ratios, vertical_alignment="center")
                with r_cols[0]:
                    with st.container(key=f"ilpop_bhagya_{rk}"):
                        with st.popover("⚙️"):
                            if st.button("👁️ Open", key=f"bhagya_view_{rid}", use_container_width=True):
                                bhagya_view_invoice_dialog(row_dict)
                            if st.button("✏️ Edit", key=f"bhagya_editbtn_{rid}", use_container_width=True):
                                bhagya_edit_invoice_dialog(row_dict)
                            if st.button("🗑️ Delete", key=f"bhagya_delbtn_{rid}", use_container_width=True):
                                bhagya_delete_dialog(rid, row_dict.get('invoice_no', ''))
                r_cols[1].markdown(serial_cell(serial_no), unsafe_allow_html=True)
                r_cols[2].markdown(_chip(row_dict.get('invoice_no'), "inv"), unsafe_allow_html=True)
                r_cols[3].markdown(_date_cell(row_dict.get('invoice_date')), unsafe_allow_html=True)
                r_cols[4].markdown(_txt(row_dict.get('bill_from'), "slux-strong"), unsafe_allow_html=True)
                r_cols[5].markdown(_chip(row_dict.get('project_id'), "proj"), unsafe_allow_html=True)
                r_cols[6].markdown(_chip(row_dict.get('site_id')), unsafe_allow_html=True)
                r_cols[7].markdown(_txt(row_dict.get('site_name'), "slux-strong"), unsafe_allow_html=True)
                subtotal_v = row_dict.get('subtotal', 0) or 0
                basic_v = row_dict.get('taxable_amount', subtotal_v - (row_dict.get('discount_amount', 0) or 0))
                r_cols[8].markdown(_money(basic_v), unsafe_allow_html=True)
                gst_total = (row_dict.get('cgst', 0) or 0) + (row_dict.get('sgst', 0) or 0)
                r_cols[9].markdown(_money(gst_total), unsafe_allow_html=True)
                r_cols[10].markdown(_money(row_dict.get('total', 0), "paid"), unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    table_footer(
        f'{total_rows:,} invoice{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small>',
        f'<span>Total: <b style="color:#059669;">₹ {view_total:,.0f}</b></span>'
        f'<span class="slux-foot-badge">Page {st.session_state.bhagya_page} of {total_pages}</span>',
    )

    st.markdown("<br>", unsafe_allow_html=True)
    pager("bhagya_page", total_pages, total_rows, "bhagya", label="Total")

# =========================================================================
# INVOICE MASTER — DIALOGS (ab table_name parameter lete hain, taaki
# Visiontech aur Bhagyashree dono ke liye same dialog kaam kare)
# =========================================================================

columns_list = [
    "id", "circle", "invoice_number", "invoice_date", "basic_amount", "cgst", "sgst", "igst", "Total",
    "project_id", "site_id", "site_name", "po_number", "wcc_number", "receipt_number", "percentage_amount",
    "Sub_status",
    "payment_1_amount", "payment_1_date", "payment_2_amount", "payment_2_date", "payment_3_amount", "payment_3_date",
    "balance", "remark"
]


@st.dialog("📄 Add Invoice Record", width="large")
def add_invoice_dialog(table_name, prefix, workspace=None):
    st.caption("Configure invoice details, taxation, and milestone payments")

    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", placeholder="Circle name")
        with c2: invoice_number = st.text_input("Invoice_number", placeholder="Inv Number")
        with c3:
            raw_inv_date = st.date_input("Invoice_date", value=None)
            invoice_date = raw_inv_date.strftime("%Y-%m-%d") if raw_inv_date else None
        with c4: project_id = st.text_input("Project_id", placeholder="Project ID")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", placeholder="Site ID")
        with c6: site_name = st.text_input("Site_name", placeholder="Site Name")
        with c7: po_number = st.text_input("Po_number", placeholder="PO Number")
        with c8: wcc_number = st.text_input("Wcc_number", placeholder="WCC Number")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION (Basic + CGST + SGST + IGST = Total)</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=0.0, format="%.2f")
        with c10: cgst = st.number_input("CGST", value=0.0, format="%.2f")
        with c11: sgst = st.number_input("SGST", value=0.0, format="%.2f")
        with c12: igst = st.number_input("IGST", value=0.0, format="%.2f")

        total = basic_amount + cgst + sgst + igst
        with c13:
            st.markdown(f"<p style='color:#4f46e5; font-weight:900; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", placeholder="Receipt No")
        with c15: percentage_amount = st.number_input("%Amount", value=0.0, format="%.2f")

        sub_status = st.text_input("Sub_status", placeholder="Sub Status")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=0.0, format="%.2f")
        with p2:
            raw_p1_date = st.date_input("Payment_1_date", value=None)
            payment_1_date = raw_p1_date.strftime("%Y-%m-%d") if raw_p1_date else None
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=0.0, format="%.2f")
        with p4:
            raw_p2_date = st.date_input("Payment_2_date", value=None)
            payment_2_date = raw_p2_date.strftime("%Y-%m-%d") if raw_p2_date else None
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=0.0, format="%.2f")
        with p6:
            raw_p3_date = st.date_input("Payment_3_date", value=None)
            payment_3_date = raw_p3_date.strftime("%Y-%m-%d") if raw_p3_date else None

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=0.0, format="%.2f")
        with b2: remark = st.text_input("Remark", placeholder="Enter remarks...")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            insert_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "Total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "Sub_status": sub_status,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            if workspace:
                insert_data["workspace"] = workspace
            try:
                supabase.table(table_name).insert(insert_data).execute()
                st.success("✅ Invoice Added Successfully!")
                get_table_df.clear()
                st.session_state[f"{prefix}_inv_page"] = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Saving: {e}")


@st.dialog("✏️ Edit Invoice Record", width="large")
def edit_invoice_dialog(row_data, table_name):
    st.caption("Update invoice parameters")

    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", value=str(row_data.get('circle', '')), key="ed_circle")
        with c2: invoice_number = st.text_input("Invoice_number", value=str(row_data.get('invoice_number', '')), key="ed_inv_num")
        with c3:
            parsed_date = parse_date_safely(row_data.get('invoice_date', ''))
            raw_inv_date = st.date_input("Invoice_date", value=parsed_date, key="ed_inv_date")
            invoice_date = raw_inv_date.strftime("%Y-%m-%d") if raw_inv_date else None
        with c4: project_id = st.text_input("Project_id", value=str(row_data.get('project_id', '')), key="ed_proj_id")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", value=str(row_data.get('site_id', '')), key="ed_site_id")
        with c6: site_name = st.text_input("Site_name", value=str(row_data.get('site_name', '')), key="ed_site_name")
        with c7: po_number = st.text_input("Po_number", value=str(row_data.get('po_number', '')), key="ed_po_num")
        with c8: wcc_number = st.text_input("Wcc_number", value=str(row_data.get('wcc_number', '')), key="ed_wcc_num")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=float(row_data.get('basic_amount', 0.0) or 0.0), format="%.2f", key="ed_basic")
        with c10: cgst = st.number_input("CGST", value=float(row_data.get('cgst', 0.0) or 0.0), format="%.2f", key="ed_cgst")
        with c11: sgst = st.number_input("SGST", value=float(row_data.get('sgst', 0.0) or 0.0), format="%.2f", key="ed_sgst")
        with c12: igst = st.number_input("IGST", value=float(row_data.get('igst', 0.0) or 0.0), format="%.2f", key="ed_igst")

        total = basic_amount + cgst + sgst + igst
        with c13:
            st.markdown(f"<p style='color:#4f46e5; font-weight:900; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", value=str(row_data.get('receipt_number', '')), key="ed_receipt")
        with c15: percentage_amount = st.number_input("%Amount", value=float(row_data.get('percentage_amount', 0.0) or 0.0), format="%.2f", key="ed_pct")

        sub_status = st.text_input("Sub_status", value=str(row_data.get('Sub_status', '')), key="ed_substatus")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=float(row_data.get('payment_1_amount', 0.0) or 0.0), format="%.2f", key="ed_p1_amt")
        with p2:
            p1_d = parse_date_safely(row_data.get('payment_1_date', ''))
            raw_p1 = st.date_input("Payment_1_date", value=p1_d, key="ed_p1_date")
            payment_1_date = raw_p1.strftime("%Y-%m-%d") if raw_p1 else None
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=float(row_data.get('payment_2_amount', 0.0) or 0.0), format="%.2f", key="ed_p2_amt")
        with p4:
            p2_d = parse_date_safely(row_data.get('payment_2_date', ''))
            raw_p2 = st.date_input("Payment_2_date", value=p2_d, key="ed_p2_date")
            payment_2_date = raw_p2.strftime("%Y-%m-%d") if raw_p2 else None
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=float(row_data.get('payment_3_amount', 0.0) or 0.0), format="%.2f", key="ed_p3_amt")
        with p6:
            p3_d = parse_date_safely(row_data.get('payment_3_date', ''))
            raw_p3 = st.date_input("Payment_3_date", value=p3_d, key="ed_p3_date")
            payment_3_date = raw_p3.strftime("%Y-%m-%d") if raw_p3 else None

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=float(row_data.get('balance', 0.0) or 0.0), format="%.2f", key="ed_bal")
        with b2: remark = st.text_input("Remark", value=str(row_data.get('remark', '')), key="ed_rem")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Update Invoice", type="primary", use_container_width=True):
            update_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "Total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "Sub_status": sub_status,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            try:
                supabase.table(table_name).update(update_data).eq("id", row_data['id']).execute()
                st.success("✅ Invoice Updated Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating: {e}")


@st.dialog("👁️ View Invoice Record", width="large")
def view_invoice_dialog(row_data):
    st.caption("Read-only preview")
    st.markdown('<div class="modal-section-title">🧾 GENERAL DETAILS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("Circle", value=row_data.get('circle', ''), disabled=True)
    with c2: st.text_input("Invoice Number", value=row_data.get('invoice_number', ''), disabled=True)
    with c3: st.text_input("Invoice Date", value=row_data.get('invoice_date', ''), disabled=True)
    with c4: st.text_input("Project ID", value=row_data.get('project_id', ''), disabled=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5: st.text_input("Site ID", value=row_data.get('site_id', ''), disabled=True)
    with c6: st.text_input("Site Name", value=row_data.get('site_name', ''), disabled=True)
    with c7: st.text_input("PO Number", value=row_data.get('po_number', ''), disabled=True)
    with c8: st.text_input("WCC Number", value=row_data.get('wcc_number', ''), disabled=True)

    st.markdown('<div class="modal-section-title">💰 AMOUNTS & TOTAL</div>', unsafe_allow_html=True)
    c9, c10, c11, c12, c13, c14 = st.columns(6)

    b_amt = float(row_data.get('basic_amount', 0) or 0)
    c_amt = float(row_data.get('cgst', 0) or 0)
    s_amt = float(row_data.get('sgst', 0) or 0)
    i_amt = float(row_data.get('igst', 0) or 0)
    t_amt = row_data.get('Total')
    if not t_amt or str(t_amt).lower() in ['nan', 'none', '']:
        t_amt = b_amt + c_amt + s_amt + i_amt

    with c9: st.text_input("Basic Amount", value=str(b_amt), disabled=True)
    with c10: st.text_input("CGST", value=str(c_amt), disabled=True)
    with c11: st.text_input("SGST", value=str(s_amt), disabled=True)
    with c12: st.text_input("IGST", value=str(i_amt), disabled=True)
    with c13: st.text_input("Total", value=str(t_amt), disabled=True)
    with c14: st.text_input("% Amount", value=str(row_data.get('percentage_amount', '')), disabled=True)

    st.text_input("Sub Status", value=row_data.get('Sub_status', ''), disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True):
        st.rerun()


@st.dialog("🗑️ Confirm Deletion", width="small")
def delete_invoice_dialog(rid, inv_num, table_name):
    st.warning(f"Delete invoice '{inv_num}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                supabase.table(table_name).delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


@st.dialog("📤 Bulk Upload Invoices", width="large")
def bulk_upload_dialog(table_name, prefix, workspace=None):
    st.caption("Upload an Excel file to bulk import invoice records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key=f"{prefix}_bulk_inv_file")

    if uploaded_file and st.button("🚀 Process & Upload", type="primary", use_container_width=True):
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df_upload = pd.read_excel(uploaded_file)
            else:
                df_upload = pd.read_csv(uploaded_file, sep='\t')

            added = 0
            for _, row in df_upload.iterrows():
                p_id = str(row.get("project_id", row.get("Project ID", ""))).strip()
                if not p_id or p_id.lower() == "nan": continue

                insert_dict = {}
                for col in columns_list:
                    if col != "id" and col != "🎯 Select":
                        val = row.get(col, row.get(col.lower(), ""))
                        insert_dict[col] = str(val).strip() if pd.notna(val) and str(val).lower() != 'nan' else ""

                try:
                    b = float(insert_dict.get('basic_amount', 0) or 0)
                    c = float(insert_dict.get('cgst', 0) or 0)
                    s = float(insert_dict.get('sgst', 0) or 0)
                    i = float(insert_dict.get('igst', 0) or 0)
                    insert_dict['Total'] = b + c + s + i
                except:
                    pass

                if workspace:
                    insert_dict["workspace"] = workspace

                try:
                    supabase.table(table_name).insert(insert_dict).execute()
                    added += 1
                except:
                    pass
            st.success(f"✅ Bulk Upload Complete! {added} records added.")
            get_table_df.clear()
            st.session_state[f"{prefix}_inv_page"] = 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

def _invoice_total(row_dict):
    """'Total' column value, or Basic + CGST + SGST + IGST if Total is blank."""
    t = row_dict.get('Total')
    if _clean(t):
        return _num(t)
    return sum(_num(row_dict.get(k)) for k in ('basic_amount', 'cgst', 'sgst', 'igst'))


def render_invoice_master_tab(company_key, prefix, title):
    """Invoice Master table (VIS Invoice jaisa) — kisi bhi company ke liye.
    company_key -> COMPANIES se table name leta hai; prefix -> widget keys/page state."""
    table_name = COMPANIES[company_key]["invoice_table"]
    workspace = COMPANIES[company_key]["workspace"]
    page_key = f"{prefix}_inv_page"
    action_key = f"{prefix}_inv_action"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # --- TOP ACTION BAR ---
    col_title, col_ref, col_add, col_upload, col_export = st.columns([3, 1, 1.5, 1.5, 1.5])
    with col_title:
        st.markdown(f"<h2 style='margin:0; color:#0f172a;'>{title}</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key=f"{prefix}_inv_refresh"):
            get_table_df.clear()
            st.rerun()
    with col_add:
        if st.button("➕ Add Invoice", use_container_width=True, key=f"{prefix}_inv_add"):
            add_invoice_dialog(table_name, prefix, workspace)
    with col_upload:
        if st.button("📤 Bulk Upload", use_container_width=True, key=f"{prefix}_inv_bulk"):
            bulk_upload_dialog(table_name, prefix, workspace)
    with col_export:
        if st.button("📥 Export Data", use_container_width=True, key=f"{prefix}_inv_export"):
            st.session_state[action_key] = "export"

    st.markdown("<br>", unsafe_allow_html=True)

    df = get_table_df(table_name, workspace).copy()
    if not df.empty:
        for col in columns_list:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=columns_list)

    if "🎯 Select" not in df.columns:
        df.insert(0, "🎯 Select", False)

    # Export Trigger
    if st.session_state.get(action_key) == "export":
        export_df = df.copy()
        if "🎯 Select" in export_df.columns: export_df = export_df.drop(columns=["🎯 Select"])
        if "id" in export_df.columns: export_df = export_df.drop(columns=["id"])

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Invoices')
        st.download_button("📊 Download Excel File", data=buffer.getvalue(), file_name=f"{workspace}_{table_name}_Export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary", key=f"{prefix}_inv_dl")
        st.session_state[action_key] = ""

    # --- LIVE SEARCH BOX ---
    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Database Records</h5>", unsafe_allow_html=True)
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search invoices...", label_visibility="collapsed", key=f"{prefix}_inv_search")

    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    # --- KPI CARDS (search ke hisaab se) ---
    rows_as_dicts = df.to_dict("records")
    k_count = len(rows_as_dicts)
    k_billed = sum(_invoice_total(r) for r in rows_as_dicts)
    k_received = sum(_num(r.get(c)) for r in rows_as_dicts for c in ("payment_1_amount", "payment_2_amount", "payment_3_amount"))
    k_balance = sum(_num(r.get("balance")) for r in rows_as_dicts)
    st.markdown(
        '<div class="lux-kpi-grid">'
        + kpi_card("🧾", "Total Invoices", f"{k_count:,}", "Filtered results" if search_query else "All records", *KPI_INDIGO)
        + kpi_card("💼", "Total Billed", f"₹ {k_billed:,.0f}", "Basic + GST", *KPI_AMBER)
        + kpi_card("💰", "Payments Received", f"₹ {k_received:,.0f}", "Pay 1 + Pay 2 + Pay 3", *KPI_GREEN, value_cls="green")
        + kpi_card("⏳", "Balance", f"₹ {k_balance:,.0f}", "Pending collection", *KPI_RED, value_cls="red")
        + '</div>',
        unsafe_allow_html=True,
    )

    # --- PAGINATION LOGIC ---
    rows_per_page = 10
    total_rows = len(df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state[page_key] > total_pages: st.session_state[page_key] = total_pages
    elif st.session_state[page_key] < 1: st.session_state[page_key] = 1

    start_idx = (st.session_state[page_key] - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df.iloc[start_idx:end_idx].copy()

    keys_seq = [
        'circle', 'invoice_number', 'invoice_date', 'basic_amount', 'cgst', 'sgst', 'igst', 'Total',
        'project_id', 'site_id', 'site_name', 'po_number', 'wcc_number', 'receipt_number', 'percentage_amount',
        'Sub_status',
        'payment_1_amount', 'payment_1_date', 'payment_2_amount', 'payment_2_date', 'payment_3_amount', 'payment_3_date',
        'balance', 'remark'
    ]

    COL_RATIOS = [
        0.55, 0.5, 1.0, 1.4, 1.1, 1.1, 0.9, 0.9, 0.9, 1.15,
        1.4, 1.15, 1.5, 1.35, 1.25, 1.2, 1.0, 1.15,
        1.05, 1.05, 1.05, 1.05, 1.05, 1.05, 1.1, 1.6
    ]
    COL_LABELS = [
        "⚙️", "#",
        "Circle", "Invoice No", "Invoice Date", "Basic Amount", "CGST", "SGST", "IGST", "Total",
        "Project ID", "Site ID", "Site Name", "PO Number", "WCC Number", "Receipt No", "% Amount",
        "Sub Status",
        "Pay 1 Amt", "Pay 1 Date", "Pay 2 Amt", "Pay 2 Date", "Pay 3 Amt", "Pay 3 Date", "Balance", "Remark"
    ]
    RIGHT_IDX = tuple(i for i, lbl in enumerate(COL_LABELS) if lbl in (
        "Basic Amount", "CGST", "SGST", "IGST", "Total", "% Amount", "Pay 1 Amt", "Pay 2 Amt", "Pay 3 Amt", "Balance"))

    wrap_key = f"{prefix}_invoice_table_wrap"
    table_min_width_css(wrap_key, 3700)
    table_title_bar(f"🧾 {html.escape(title)}", "newest first • scroll right for payments →", f"₹ {k_billed:,.0f}")

    with st.container(key=wrap_key, height=560):
        if df_page.empty:
            empty_state("No invoice records found.")
        else:
            table_header_row(f"ilhead_inv_{prefix}", COL_RATIOS, COL_LABELS, center_idx=(0, 1), right_idx=RIGHT_IDX)

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                serial_no = start_idx + page_pos + 1
                rk = row_key_for(rid, f"s{serial_no}")
                parity = "odd" if serial_no % 2 else "even"

                with st.container(key=f"ilrow_{parity}_inv_{prefix}_{rk}"):
                    rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                    with rcols[0]:
                        with st.container(key=f"ilpop_inv_{prefix}_{rk}"):
                            with st.popover("⚙️"):
                                if st.button("👁️ Open", key=f"{prefix}_view_inv_{rid}", use_container_width=True):
                                    view_invoice_dialog(row_dict)
                                if st.button("✏️ Edit", key=f"{prefix}_edit_inv_{rid}", use_container_width=True):
                                    edit_invoice_dialog(row_dict, table_name)
                                if st.button("🗑️ Delete", key=f"{prefix}_del_inv_{rid}", use_container_width=True):
                                    delete_invoice_dialog(rid, row_dict.get('invoice_number', ''), table_name)
                    rcols[1].markdown(serial_cell(serial_no), unsafe_allow_html=True)

                    bal = _num(row_dict.get('balance'))
                    cells = {
                        'circle': _pill(row_dict.get('circle')),
                        'invoice_number': _chip(row_dict.get('invoice_number'), "inv"),
                        'invoice_date': _date_cell(row_dict.get('invoice_date')),
                        'basic_amount': _money(row_dict.get('basic_amount')),
                        'cgst': _money(row_dict.get('cgst')),
                        'sgst': _money(row_dict.get('sgst')),
                        'igst': _money(row_dict.get('igst')),
                        'Total': _money(_invoice_total(row_dict), "strong"),
                        'project_id': _chip(row_dict.get('project_id'), "proj"),
                        'site_id': _chip(row_dict.get('site_id')),
                        'site_name': _txt(row_dict.get('site_name'), "slux-strong"),
                        'po_number': _chip(row_dict.get('po_number')),
                        'wcc_number': _chip(row_dict.get('wcc_number')),
                        'receipt_number': _chip(row_dict.get('receipt_number')),
                        'percentage_amount': _money(row_dict.get('percentage_amount')),
                        'Sub_status': status_badge(row_dict.get('Sub_status')),
                        'payment_1_amount': _money(row_dict.get('payment_1_amount'), "paid" if _num(row_dict.get('payment_1_amount')) else ""),
                        'payment_1_date': _date_cell(row_dict.get('payment_1_date')),
                        'payment_2_amount': _money(row_dict.get('payment_2_amount'), "paid" if _num(row_dict.get('payment_2_amount')) else ""),
                        'payment_2_date': _date_cell(row_dict.get('payment_2_date')),
                        'payment_3_amount': _money(row_dict.get('payment_3_amount'), "paid" if _num(row_dict.get('payment_3_amount')) else ""),
                        'payment_3_date': _date_cell(row_dict.get('payment_3_date')),
                        'balance': _money(row_dict.get('balance'), "due" if bal > 0 else ("paid" if _clean(row_dict.get('balance')) else "")),
                        'remark': _txt(row_dict.get('remark'), "slux-soft"),
                    }
                    for idx, k in enumerate(keys_seq, start=2):
                        rcols[idx].markdown(cells[k], unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    table_footer(
        f'{total_rows:,} invoice{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small>',
        f'<span>Billed: <b style="color:#4f46e5;">₹ {k_billed:,.0f}</b></span>'
        f'<span>Received: <b style="color:#059669;">₹ {k_received:,.0f}</b></span>'
        f'<span>Balance: <b style="color:#dc2626;">₹ {k_balance:,.0f}</b></span>',
    )

    st.markdown("<br>", unsafe_allow_html=True)
    pager(page_key, total_pages, total_rows, f"{prefix}_inv")


# =========================================================================
# TOP BANNER
# =========================================================================
st.markdown("""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🧾 Invoice Management Hub
        </h1>
    </div>
""", unsafe_allow_html=True)

# =========================================================================
# NAVIGATION — Level 1: Company (VISIONTECH / BHAGYASHREE)
#              Level 2: Us company ke tabs
# =========================================================================
NAV_PAGES_BY_COMPANY = {
    "vis": [
        ("vis", "📋 VIS Invoice"),
        ("ers", "⚙️ ERS Process"),
        ("invdata", "📁 Invoice Data"),
        ("bhagya", "🏢 Bhagyashree Invoice"),
        ("saitele", "📡 Sai Tele Invoice"),
    ],
    "bhg": [
        ("bhg_inv", "📋 BE Invoice"),
        ("bhg_ers", "⚙️ ERS Process"),
        ("bhg_invdata", "📁 Invoice Data"),
    ],
}

if 'active_company' not in st.session_state:
    st.session_state.active_company = "vis"
if 'active_pages' not in st.session_state:
    st.session_state.active_pages = {k: v[0][0] for k, v in NAV_PAGES_BY_COMPANY.items()}

with st.container(key="company_bar"):
    comp_cols = st.columns(len(COMPANIES))
    for comp_col, (comp_key, comp_cfg) in zip(comp_cols, COMPANIES.items()):
        is_active = st.session_state.active_company == comp_key
        with comp_col:
            if st.button(comp_cfg["label"], key=f"company_{comp_key}", use_container_width=True,
                         type=("primary" if is_active else "secondary")):
                st.session_state.active_company = comp_key
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

active_company = st.session_state.active_company
company_pages = NAV_PAGES_BY_COMPANY[active_company]

with st.container(key="nav_bar"):
    nav_cols = st.columns(len(company_pages))
    for nav_col, (page_id, page_label) in zip(nav_cols, company_pages):
        is_active = st.session_state.active_pages.get(active_company) == page_id
        with nav_col:
            if st.button(page_label, key=f"nav_{page_id}", use_container_width=True, type=("primary" if is_active else "secondary")):
                st.session_state.active_pages[active_company] = page_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

active_page = st.session_state.active_pages.get(active_company, company_pages[0][0])

# =========================================================================
# 🏢 VISIONTECH (bilkul pehle jaisa)
# =========================================================================
if active_company == "vis":
    if active_page == "vis":
        render_invoice_master_tab("vis", "vis", "📊 Live Invoices Master")
    elif active_page == "ers":
        render_generic_tab(table_name=COMPANIES["vis"]["ers_table"], prefix="ers", tab_title="ERS Process",
                           icon="⚙️", pdf_button=True, company_key="vis", workspace=COMPANIES["vis"]["workspace"])
    elif active_page == "invdata":
        render_generic_tab(table_name=COMPANIES["vis"]["invdata_table"], prefix="invdata", tab_title="Invoice Data", icon="📁",
                           workspace=COMPANIES["vis"]["workspace"])
    elif active_page == "bhagya":
        render_bhagyashree_tab()
    elif active_page == "saitele":
        render_generic_tab(table_name="SaiTeleInvoice", prefix="saitele", tab_title="Sai Tele Invoice", icon="📡")

# =========================================================================
# 🏭 BHAGYASHREE (Visiontech jaisa hi — same tables, workspace = BHAGYASHREE)
# =========================================================================
elif active_company == "bhg":
    if active_page == "bhg_inv":
        render_invoice_master_tab("bhg", "bhg", "📊 Bhagyashree Invoices Master")
    elif active_page == "bhg_ers":
        render_generic_tab(table_name=COMPANIES["bhg"]["ers_table"], prefix="bhg_ers", tab_title="ERS Process",
                           icon="⚙️", pdf_button=True, company_key="bhg", workspace=COMPANIES["bhg"]["workspace"])
    elif active_page == "bhg_invdata":
        render_generic_tab(table_name=COMPANIES["bhg"]["invdata_table"], prefix="bhg_invdata", tab_title="Invoice Data", icon="📁",
                           workspace=COMPANIES["bhg"]["workspace"])
