import streamlit as st
import pandas as pd
import math
import io
import html
import datetime
import random
from supabase import create_client, Client
# ---> Enables the MRN search box to filter results on every keystroke,
# instead of Streamlit's default behavior of waiting for Enter or for the
# box to lose focus. Requires: pip install streamlit-keyup <---
from st_keyup import st_keyup

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MRN / GRN Desk", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'mrn_current_page' not in st.session_state:
    st.session_state.mrn_current_page = 1
if 'mrn_action' not in st.session_state:
    st.session_state.mrn_action = ""
if 'mrn_items_error_banner' not in st.session_state:
    st.session_state.mrn_items_error_banner = None

# --- 2. ✨ LAVISH LIGHT THEME CSS (Quotation / Site Data / Invoice jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Primary Action Buttons */
    div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15) !important;
    }
    div.stButton > button[kind="primary"] p, div.stDownloadButton > button[kind="primary"] p,
    div[data-testid="stFormSubmitButton"] > button p { color: #ffffff !important; font-weight: 800 !important; }

    /* Secondary Action Buttons */
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
    label p, label[data-testid="stWidgetLabel"] p { color: #0f172a !important; font-weight: 700 !important; letter-spacing: 0.5px; }

    /* Read-only inputs: black & bold on light grey */
    div[data-testid="stTextInput"] input:disabled, div[data-testid="stTextArea"] textarea:disabled {
        color: #000000 !important; font-weight: 800 !important; -webkit-text-fill-color: #000000 !important; background: #f1f5f9 !important;
    }

    /* Sidebar (kept dark, same as other pages) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        font-size: 1.05rem !important; transition: all 0.3s ease !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; transform: translateX(4px) !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* 🟢 MRN "Add New MRN" dialog: each PO line item card (shared key PREFIX) */
    div[class*="st-key-mrn_rowcard_"] {
        border: 1.5px solid #c7d2fe !important;
        border-radius: 10px !important;
        background: #fafaff !important;
    }
    .mrn-dlg-head { color: #4338ca; font-weight: 800; font-size: 0.72rem; letter-spacing: 0.6px; text-transform: uppercase; }
    .mrn-po-title { color: #4f46e5; font-weight: 800; margin-top: 15px; }

    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; text-transform: uppercase !important; font-size: 0.8rem !important; }

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
    .st-key-site_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-site_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-site_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-site_table_wrap div[class*="st-key-mrnhead"],
    .st-key-site_table_wrap div[class*="st-key-mrnrow_"] { min-width: 2000px !important; }
    .st-key-site_table_wrap [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-site_table_wrap [data-testid="stColumn"], .st-key-site_table_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header */
    div[class*="st-key-mrnhead"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-mrnhead"] [data-testid="stColumn"], div[class*="st-key-mrnhead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }

    /* Data rows */
    div[class*="st-key-mrnrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-mrnrow_odd"] { background: #fafaff; }
    div[class*="st-key-mrnrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-mrnrow_"] p { margin: 0 !important; }

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
    .slux-chip.mrn { background: #ecfeff; border-color: #a5f3fc; color: #0e7490; }
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .mrn-amt { text-align: right; font-weight: 700; color: #334155; font-variant-numeric: tabular-nums; }
    .mrn-amt.total { color: #059669; font-weight: 900; font-size: .92rem; }
    .mrn-rate { display: inline-block; padding: 3px 10px; border-radius: 8px; background: #fffbeb; border: 1px solid #fde68a; color: #b45309; font-weight: 900; font-size: .8rem; }
    .mrn-team { font-weight: 800; color: #b45309; }

    /* Single ⚙️ action button at row start (Site Data jaisa) */
    div[class*="st-key-mrnpop_"] button {
        width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    div[class*="st-key-mrnpop_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    div[class*="st-key-mrnpop_"] button p, div[class*="st-key-mrnpop_"] button span { color: #1e293b !important; }
    div[class*="st-key-mrnpop_"] button svg { display: none !important; }

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
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

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

# --- HELPER FUNCTIONS ---
# FIX: pehle ye cached functions workspace ko ANDAR se padhte the, isliye cache
# har workspace ke liye ek hi hota tha — workspace badalne par 30-60 sec tak
# PURANI company ka data dikh sakta tha. Ab workspace cache key ka hissa hai.
@st.cache_data(ttl=30, show_spinner=False)
def _fetch_mrn_data_cached(ws):
    try:
        res = supabase.table("mrn_data").select("*").eq("workspace", ws).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def fetch_mrn_data():
    return _fetch_mrn_data_cached(st.session_state.get('active_workspace', 'VISPL'))
fetch_mrn_data.clear = _fetch_mrn_data_cached.clear

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_project_ids_cached(ws):
    try:
        res = supabase.table("site_data").select("*").eq("workspace", ws).limit(100000).execute()
        if res.data:
            pids = [str(x["Project ID"]).strip() for x in res.data if x.get("Project ID") and str(x.get("Project ID")).strip() != "" and str(x.get("Project ID")).strip().lower() != "nan"]
            return ["Select Project ID"] + list(dict.fromkeys(pids))
    except Exception as e:
        st.error(f"Error fetching Project IDs: {e}")
    return ["Select Project ID"]

def fetch_project_ids():
    return _fetch_project_ids_cached(st.session_state.get('active_workspace', 'VISPL'))
fetch_project_ids.clear = _fetch_project_ids_cached.clear

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_project_details_cached(proj_id, ws):
    try:
        res = supabase.table("site_data").select("*").eq("Project ID", proj_id).eq("workspace", ws).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return {}

def fetch_project_details(proj_id):
    return _fetch_project_details_cached(proj_id, st.session_state.get('active_workspace', 'VISPL'))

@st.cache_data(ttl=60, show_spinner=False)
def fetch_team_percentage(team_name):
    try:
        if team_name and team_name != "Select":
            tables_to_check = [
                ("team_master", "Team Name"),
                ("Team Master", "Team Name"),
                ("team_registration", "Team Name"),
                ("dropdown_master", "option_value")
            ]
            
            for t_name, c_name in tables_to_check:
                try:
                    res = supabase.table(t_name).select("*").eq(c_name, team_name).execute()
                    if res.data and len(res.data) > 0:
                        row = res.data[0]
                        for key, val in row.items():
                            if val is not None:
                                k_lower = str(key).lower()
                                if "percent" in k_lower or "rate" in k_lower or "%" in k_lower or "margin" in k_lower:
                                    clean_val = str(val).replace('%', '').strip()
                                    if clean_val.replace('.', '', 1).isdigit():
                                        fetched_pct = float(clean_val)
                                        if fetched_pct > 0:
                                            return fetched_pct
                except Exception:
                    continue
    except Exception:
        pass
    return 100.0

# ---> UNLIMITED PAGINATED DATA FETCHER (BYPASSES SUPABASE 1000 ROW LIMIT) <---
@st.cache_data(ttl=300, show_spinner=False)
def get_unlimited_po_working(ws):
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        try:
            res = supabase.table("po_working").select("*").eq("workspace", ws).range(offset, offset + limit - 1).execute()
            if not res.data:
                break
            all_rows.extend(res.data)
            if len(res.data) < limit:
                break
            offset += limit
        except Exception:
            break
    return all_rows


@st.cache_data(ttl=300, show_spinner=False)
def fetch_item_lookup(ws):
    """Create an item-code lookup from all PO Working rows in this workspace."""
    lookup = {}
    for row in get_unlimited_po_working(ws):
        code = _clean_code_for_db(
            row.get("Item Num") or row.get("Item Code") or row.get("item_code") or ""
        )
        if not code or str(code).lower() in ("nan", "none"):
            continue
        key = str(code).strip().lower()
        description = str(
            row.get("Description")
            or row.get("Item Description")
            or row.get("Item Desc")
            or row.get("description")
            or ""
        ).strip()
        price = pd.to_numeric(
            row.get("Price") or row.get("Unit Price") or row.get("Rate") or 0,
            errors="coerce"
        )
        price = 0.0 if pd.isna(price) else float(price)
        if key not in lookup:
            lookup[key] = {"code": str(code), "description": description, "price": price}
        else:
            if not lookup[key]["description"] and description:
                lookup[key]["description"] = description
            if lookup[key]["price"] <= 0 and price > 0:
                lookup[key]["price"] = price
    return lookup


# ---> HELPER: find a column regardless of case / leading-trailing spaces <---
def _find_col(df, target_name):
    target_clean = target_name.strip().lower()
    for c in df.columns:
        if str(c).strip().lower() == target_clean:
            return c
    return None


# ---> HELPER: normalize any numeric-looking value into a clean digit string <---
def _clean_number(val):
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none"):
        return ""
    s_no_comma = s.replace(",", "")
    try:
        f = float(s_no_comma)
        if f.is_integer():
            return str(int(f))
        return s_no_comma
    except (ValueError, TypeError):
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits if digits else s.strip().lower()


# ---> 🔴 FIX for "invalid input syntax for type integer: 10.0": some Item
# Codes in po_working are purely numeric (e.g. 10, 12) and pandas stores
# them as float64 once the column has any NaN mixed in, so they arrive
# here as 10.0 / "10.0". The mrn_items."Item Code" column is an integer
# type in the DB, and Postgres refuses to cast a string with a decimal
# point to integer — even "10.0" — causing the WHOLE items insert to fail
# silently (all rows rejected together, since it's a single batch insert).
# This only strips a trailing ".0" off purely-numeric values; alphanumeric
# codes like "21-800000-0-00-ZZ-ZZ-057" are returned completely unchanged,
# since float() raises on them and we fall straight through to `return s`. <---
def _clean_code_for_db(val):
    s = str(val).strip()
    if s.endswith(".0"):
        try:
            f = float(s)
            if f.is_integer():
                return str(int(f))
        except ValueError:
            pass
    return s


@st.cache_data(ttl=30, show_spinner=False)
def fetch_mrn_used_qty_map(po_no, workspace, project_id):
    used_map = {}
    try:
        res_used = (
            supabase.table("mrn_items")
            .select('"Item Code","User Qty"')
            .eq("PO Number", po_no)
            .eq("workspace", workspace)
            .eq("Project ID", project_id)
            .execute()
        )
        if res_used.data:
            for r in res_used.data:
                ic = str(r.get("Item Code", "")).replace(".0", "").strip().lower()
                uq = float(r.get("User Qty", 0) or 0)
                used_map[ic] = used_map.get(ic, 0) + uq
    except Exception:
        pass
    return used_map


def fetch_po_line_items(po_no, site_id, proj_id):
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        
        all_data = get_unlimited_po_working(ws)
        if not all_data:
            st.warning("⚠️ 'po_working' table is empty for this workspace (or fetch failed).")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)

        po_col = _find_col(df, "PO Number")
        site_col = _find_col(df, "Site ID")
        proj_col = _find_col(df, "Project Name")
        item_col = _find_col(df, "Item Num")

        if not po_col:
            st.error(f"⚠️ Couldn't find a 'PO Number' column in po_working. "
                     f"Actual columns found: {list(df.columns)}")
            return pd.DataFrame()

        po_target = _clean_number(po_no)
        df['clean_po'] = df[po_col].apply(_clean_number)
        df_filtered = df[df['clean_po'] == po_target].copy()

        if df_filtered.empty:
            sample_vals = df['clean_po'].unique()[:15].tolist()
            st.warning(
                f"No rows matched PO Number '{po_no}' (normalized as '{po_target}') "
                f"in column '{po_col}'. Sample PO values present in table: {sample_vals}"
            )
            return pd.DataFrame()

        s_target = _clean_number(site_id) if str(site_id).strip() != "" else str(site_id).strip().lower()
        p_target = str(proj_id).strip().lower()

        mask = pd.Series([False] * len(df_filtered), index=df_filtered.index)
        filter_applied = False

        if site_col and str(site_id).strip() != "":
            df_filtered['clean_site'] = df_filtered[site_col].apply(_clean_number)
            mask = mask | (df_filtered['clean_site'] == s_target)
            filter_applied = True

        if proj_col and p_target != "":
            df_filtered['clean_proj'] = df_filtered[proj_col].astype(str).str.strip().str.lower()
            df_filtered['clean_proj'] = df_filtered['clean_proj'].str.replace(r'\.0$', '', regex=True)
            mask = mask | (df_filtered['clean_proj'] == p_target)
            filter_applied = True

        if filter_applied:
            final_df = df_filtered[mask].copy()
            if final_df.empty:
                final_df = df_filtered.copy()
        else:
            final_df = df_filtered.copy()

        used_map = fetch_mrn_used_qty_map(po_no, ws, proj_id)

        if item_col:
            final_df["Used Qty"] = final_df[item_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower().map(used_map).fillna(0)
        else:
            final_df["Used Qty"] = 0

        return final_df
    except Exception as e:
        st.error(f"❌ Error in fetch_po_line_items: {e}")
    return pd.DataFrame()


def _derive_wcc_defaults(po_dfs_dict):
    wcc_number_default, wcc_status_default = "", ""
    for _po, df_po in po_dfs_dict.items():
        if df_po is None or df_po.empty:
            continue
        if "wcc_number" in df_po.columns and not wcc_number_default:
            vals = [str(v).strip() for v in df_po["wcc_number"].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
            if vals:
                wcc_number_default = vals[0]
        if "wcc_status" in df_po.columns and not wcc_status_default:
            vals = [str(v).strip() for v in df_po["wcc_status"].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
            if vals:
                wcc_status_default = vals[0]
        if wcc_number_default and wcc_status_default:
            break
    return wcc_number_default, wcc_status_default

# --- 4. DIALOG FUNCTIONS (ADD, EDIT, DELETE) ---

@st.dialog("🗑️ Confirm Deletion", width="small")
def delete_mrn_dialog(rid, mrn_no):
    st.warning(f"Delete MRN '{mrn_no}'? This will also remove its Pending Auto-Bill and Line Items. This cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    wc1, wc2 = st.columns(2)
    with wc1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
    with wc2:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                supabase.table("mrn_data").delete().eq("id", rid).execute()
                supabase.table("mrn_items").delete().eq("MRN Number", mrn_no).execute()
                supabase.table("pending_billing_invoices").delete().eq("invoice_no", mrn_no).execute()
                supabase.table("billing_invoices").delete().eq("invoice_no", mrn_no).execute()
                
                st.success("✅ MRN & Auto-Bill Deleted Successfully!")
                fetch_mrn_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Deleting Record: {e}")

@st.dialog("✏️ Edit MRN Details", width="large")
def edit_mrn_dialog(row_data):
    mrn_no = row_data.get("MRN Number", "")
    st.caption(f"Editing MRN: {mrn_no} (Amounts & Items are auto-linked with Billing and cannot be changed here)")
    
    st.markdown('<div class="modal-section-title">🏢 MRN HEADER</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("MRN NUMBER", value=mrn_no, disabled=True)
    with c2: st.text_input("PROJECT ID", value=row_data.get("Project ID", ""), disabled=True)
    with c3: st.text_input("SITE ID", value=row_data.get("Site ID", ""), disabled=True)
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("TEAM NAME", value=row_data.get("Team Name", ""), disabled=True)
    with c5:
        _basic_v = pd.to_numeric(row_data.get('Basic Amount', 0), errors='coerce')
        st.text_input("BASIC AMOUNT", value=f"₹ {(0 if pd.isna(_basic_v) else _basic_v):,.2f}", disabled=True)
    with c6:
        st.text_input("TEAM RATE %", value=f"{row_data.get('Team Percent', 100)} %", disabled=True)

    c_date, c_desc = st.columns([1, 2])
    with c_date:
        def_date_str = row_data.get("Date", str(datetime.date.today().strftime("%d-%m-%Y")))
        try:
            def_date = pd.to_datetime(def_date_str, format="%d-%m-%Y").date()
        except:
            def_date = datetime.date.today()
        new_date = st.date_input("DATE", value=def_date, format="DD/MM/YYYY")
    with c_desc:
        st.text_area("DESCRIPTION / REMARKS", value=row_data.get("Description", ""), disabled=True, height=68)
        
    st.markdown('<div class="modal-section-title">📦 MRN LINE ITEMS (READ-ONLY)</div>', unsafe_allow_html=True)
    try:
        res = supabase.table("mrn_items").select("*").eq("MRN Number", mrn_no).execute()
        if res.data:
            items_df = pd.DataFrame(res.data)
            display_cols = []
            for col in ['PO Number', 'Item Code', 'Description', 'User Qty', 'Adjusted Price', 'Total']:
                if col in items_df.columns:
                    display_cols.append(col)
            st.dataframe(items_df[display_cols], hide_index=True, use_container_width=True)
        else:
            st.info("No line items found for this MRN.")
    except Exception:
        st.info("Could not fetch line items.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_save1, col_save2 = st.columns([8, 2])
    with col_save2:
        if st.button("💾 Update MRN", type="primary", use_container_width=True):
            new_date_str = new_date.strftime("%d-%m-%Y")
            new_bill_date_str = str(new_date)
            try:
                supabase.table("mrn_data").update({"Date": new_date_str}).eq("id", row_data["id"]).execute()
                supabase.table("pending_billing_invoices").update({"date": new_bill_date_str}).eq("invoice_no", mrn_no).execute()
                supabase.table("billing_invoices").update({"date": new_bill_date_str}).eq("invoice_no", mrn_no).execute()
                
                st.success("✅ MRN Date Updated Successfully!")
                fetch_mrn_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating MRN: {e}")

@st.dialog("📦 Create New MRN / GRN", width="large")
def add_mrn_dialog():
    st.caption("Generate Material Receipt Note and adjust pricing based on Team Registration %")
    
    st.markdown('<div class="modal-section-title">🏢 PROJECT & SITE DETAILS</div>', unsafe_allow_html=True)
    
    proj_opts = fetch_project_ids()
    selected_proj = st.selectbox("SEARCH & SELECT PROJECT ID *", proj_opts)
    
    if selected_proj != "Select Project ID":
        try:
            ex_res = supabase.table("mrn_data").select('"MRN Number","Team Name"').eq("Project ID", selected_proj).execute()
            if ex_res.data:
                ex_text = " | ".join([f"{r['MRN Number']} ({r['Team Name']})" for r in ex_res.data])
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 12px; border-radius: 8px; border: 2px solid #10b981; margin-top: 5px; margin-bottom: 15px;'>
                    <span style='color: #0f172a; font-weight: 800; font-size: 0.95rem;'>📌 EXISTING MRNs FOUND FOR THIS PROJECT:</span><br>
                    <span style='color: #ef4444; font-weight: 700; font-size: 0.9rem;'>{ex_text}</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            pass
    
    site_name, site_id, cluster, rfai_status, site_status, team_name = "", "", "", "", "", ""
    po_list = []
    team_percent = 100.0
    
    if selected_proj != "Select Project ID":
        proj_data = fetch_project_details(selected_proj)
        site_name = proj_data.get("Site Name", "")
        site_id = proj_data.get("Site ID", "")
        cluster = proj_data.get("Cluster", "")
        rfai_status = proj_data.get("RFAI Status", "")
        site_status = proj_data.get("Site Status", "")
        team_name = proj_data.get("Team Name", "")
        
        po_str = str(proj_data.get("PO No.", ""))
        if po_str and po_str.lower() != "nan":
            po_list = [p.strip() for p in po_str.split(",") if p.strip()]
            
        ws_act = st.session_state.get('active_workspace', 'VISPL')
        try:
            all_po_data = get_unlimited_po_working(ws_act)
            p_target = str(selected_proj).strip().lower()
            s_target = str(site_id).strip().lower()
            
            for row in all_po_data:
                match = False
                
                pn_val = str(row.get("Project Name", "")).strip().lower()
                if pn_val.endswith(".0"): pn_val = pn_val[:-2]
                if pn_val == p_target: match = True
                
                sid_val = str(row.get("Site ID", "")).strip().lower()
                if sid_val.endswith(".0"): sid_val = sid_val[:-2]
                if s_target and sid_val == s_target: match = True
                
                if match:
                    pn = str(row.get("PO Number", "")).strip()
                    if pn.endswith(".0"): pn = pn[:-2]
                    if pn and pn.lower() != "nan" and pn not in po_list:
                        po_list.append(pn)
        except Exception as e:
            pass
        
        team_percent = fetch_team_percentage(team_name)

    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("SITE ID", value=site_id, disabled=True)
    with c2: st.text_input("SITE NAME", value=site_name, disabled=True)
    with c3: st.text_input("CLUSTER", value=cluster, disabled=True)
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("RFAI STATUS", value=rfai_status, disabled=True)
    with c5: st.text_input("SITE STATUS", value=site_status, disabled=True)
    with c6: st.text_input("TEAM NAME *", value=team_name, disabled=True)

    PO_MULTISELECT_KEY = "mrn_po_multiselect"
    preview_selected_pos = [p for p in st.session_state.get(PO_MULTISELECT_KEY, []) if p in po_list]

    preview_po_dfs = {}
    for _po in preview_selected_pos:
        _df = fetch_po_line_items(_po, site_id, selected_proj)
        if not _df.empty:
            preview_po_dfs[_po] = _df

    default_wcc_number, default_wcc_status = _derive_wcc_defaults(preview_po_dfs)

    fetched_team_percent = team_percent
    c_rate, c_desc = st.columns([1, 2])
    with c_rate:
        team_percent = st.number_input(
            "TEAM RATE % (Editable for this MRN)",
            min_value=0.0, max_value=100.0,
            value=float(team_percent),
            step=0.5,
            help="Auto-fetched from Team Master. Change it here to override the rate only for this MRN — Adjusted Price will use this %."
        )
        st.caption(
            f"📌 Auto Rate: **{fetched_team_percent:g}%** "
            f"(Team Cut: **{100 - fetched_team_percent:g}%**) → "
            f"Currently Applying: **{team_percent:g}%** of PO Price"
        )
    with c_desc:
        mrn_description = st.text_area(
            "DESCRIPTION / REMARKS",
            placeholder="Enter any description / remarks for this MRN...",
            height=68
        )

    c_wcc1, c_wcc2 = st.columns(2)
    with c_wcc1:
        wcc_number_display = st.text_input(
            "WCC NUMBER (reference only)",
            value=default_wcc_number,
            help="Auto-filled from the selected PO's WCC data. Editable here for reference only — not saved with the MRN."
        )
    with c_wcc2:
        wcc_status_display = st.text_input(
            "WCC STATUS (reference only)",
            value=default_wcc_status,
            help="Auto-filled from the selected PO's WCC data. Editable here for reference only — not saved with the MRN."
        )
    st.caption("ℹ️ WCC Number / WCC Status shown above are for reference only and are **not** saved when this MRN is generated.")

    st.markdown('<div class="modal-section-title">📑 PO SELECTION & LINE ITEMS</div>', unsafe_allow_html=True)
    
    if not po_list and selected_proj != "Select Project ID":
        st.warning("⚠️ No POs found for this Project ID in Site Data.")
        
    selected_pos = st.multiselect("SEARCH & SELECT PO(s)", po_list, placeholder="Choose one or multiple POs", key=PO_MULTISELECT_KEY)
    
    grand_basic_total = 0.0
    all_po_dfs = {}
    
    # ---> 🟢 Manual per-row rendering instead of st.data_editor (dialog stability +
    # per-row highlight). Each Qty box is a normal st.number_input with a stable key. <---
    ROW_RATIOS = [0.6, 1.1, 2.6, 0.7, 0.7, 0.9, 0.9, 1.0, 1.0]
    ROW_LABELS = ["LINE", "ITEM CODE", "DESCRIPTION", "PO QTY", "WCC QTY", "AVAIL QTY", "USER QTY", "PRICE", "TOTAL"]

    # ---> 🟢 All Qty inputs are inside one st.form, so the page reruns only once
    # when "Apply Quantities" is clicked (not on every keystroke). <---
    with st.form(key="mrn_qty_form", border=False):
        for po in selected_pos:
            st.markdown(f"<p class='mrn-po-title'>🛒 Processing PO: {po}</p>", unsafe_allow_html=True)
            
            df_po = preview_po_dfs.get(po)
            if df_po is None:
                df_po = fetch_po_line_items(po, site_id, selected_proj)
            
            if df_po.empty:
                st.info(f"No line items found in PO Working for PO: {po}")
                continue
                
            df_display = pd.DataFrame()
            df_display["PO Line No"] = df_po.get("Line Number", [""]*len(df_po))
            df_display["Item Code"] = df_po.get("Item Num", [""]*len(df_po))
            df_display["Item Description"] = df_po.get("Description", [""]*len(df_po))
            
            raw_po_qty = pd.to_numeric(df_po.get("PO Qty", [0]*len(df_po)), errors='coerce').fillna(0)
            raw_used_qty = pd.to_numeric(df_po.get("Used Qty", [0]*len(df_po)), errors='coerce').fillna(0)
            
            df_display["PO Qty"] = raw_po_qty

            raw_wcc_qty = pd.to_numeric(df_po.get("wcc_qty", [0]*len(df_po)), errors='coerce').fillna(0)
            df_display["WCC Qty"] = raw_wcc_qty

            df_display["Available Qty"] = raw_po_qty - raw_used_qty
            
            original_price = pd.to_numeric(df_po.get("Price", [0]*len(df_po)), errors='coerce').fillna(0)
            df_display["Adjusted Price"] = original_price * (team_percent / 100.0)
            
            df_display = df_display.reset_index(drop=True)

            h_cols = st.columns(ROW_RATIOS)
            for h_col, label in zip(h_cols, ROW_LABELS):
                h_col.markdown(f"<div class='mrn-dlg-head'>{label}</div>", unsafe_allow_html=True)

            row_qtys = []
            for idx, item_row in df_display.iterrows():
                qty_key = f"mrn_row_qty_{po}_{idx}"
                qty_box_key = f"mrn_qtybox_{po}_{idx}"

                # Read the value from the LAST form submission to decide the highlight.
                pre_qty = float(st.session_state.get(qty_key, 0.0) or 0.0)
                is_filled = pre_qty > 0

                if is_filled:
                    st.markdown(f"""
                        <style>
                        .st-key-{qty_box_key} input {{
                            background-color: rgba(34, 197, 94, 0.15) !important;
                            border: 1.5px solid #22c55e !important;
                            color: #000000 !important;
                            font-weight: 800 !important;
                            text-align: center !important;
                        }}
                        </style>
                    """, unsafe_allow_html=True)

                # Each item sits inside its OWN bordered card (clear row boundary).
                row_card_key = f"mrn_rowcard_{po}_{idx}"
                with st.container(border=True, key=row_card_key):
                    rcols = st.columns(ROW_RATIOS)

                    with rcols[6]:
                        with st.container(key=qty_box_key):
                            current_qty = st.number_input(
                                "Qty", min_value=0.0, step=0.01, format="%.2f",
                                key=qty_key, label_visibility="collapsed"
                            )
                    row_qtys.append(float(current_qty))

                    # Bold + green as soon as a Qty is entered for this row.
                    is_filled = current_qty > 0
                    color_style = "color:#15803d; font-weight:800;" if is_filled else "color:#1e293b; font-weight:500;"
                    single_line_style = "white-space:nowrap; overflow:hidden; text-overflow:ellipsis; display:block; max-width:100%; " + color_style
                    wrap_style = (
                        "display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; "
                        "overflow:hidden; white-space:normal; overflow-wrap:break-word; word-break:break-word; "
                        + color_style
                    )

                    line_total = float(current_qty) * float(item_row["Adjusted Price"])

                    full_desc = str(item_row["Item Description"])
                    desc_display = full_desc[:80] + ("…" if len(full_desc) > 80 else "")

                    rcols[0].markdown(f"<div style='{single_line_style}'>{item_row['PO Line No']}</div>", unsafe_allow_html=True)
                    rcols[1].markdown(f"<div style='{single_line_style}'>{item_row['Item Code']}</div>", unsafe_allow_html=True)
                    rcols[2].markdown(f"<div style='{wrap_style}' title=\"{html.escape(full_desc)}\">{html.escape(desc_display)}</div>", unsafe_allow_html=True)
                    rcols[3].markdown(f"<div style='{single_line_style}'>{item_row['PO Qty']:.2f}</div>", unsafe_allow_html=True)
                    rcols[4].markdown(f"<div style='{single_line_style}'>{item_row['WCC Qty']:.2f}</div>", unsafe_allow_html=True)
                    rcols[5].markdown(f"<div style='{single_line_style}'>{item_row['Available Qty']:.2f}</div>", unsafe_allow_html=True)
                    rcols[7].markdown(f"<div style='{single_line_style}'>₹ {item_row['Adjusted Price']:.2f}</div>", unsafe_allow_html=True)
                    rcols[8].markdown(f"<div style='{single_line_style}'>₹ {line_total:,.2f}</div>", unsafe_allow_html=True)

            df_display["User Qty"] = row_qtys
            df_display["Line Total"] = df_display["User Qty"] * df_display["Adjusted Price"]

            grand_basic_total += float(df_display["Line Total"].sum())
            all_po_dfs[po] = df_display

        if selected_pos:
            st.form_submit_button(
                "✅ Apply Quantities (Recalculate Totals)",
                use_container_width=True, type="primary"
            )
            st.caption("Sab items ka Qty daalne ke baad ye button dabao — page sirf ek hi baar refresh hoga, har box par nahi.")

    # Extra payable items which are not part of this site's selected PO(s).
    st.markdown('<div class="modal-section-title">➕ ADD ITEM NOT AVAILABLE IN PO</div>', unsafe_allow_html=True)
    st.caption("Item Code type karein. Description PO Working se automatic aayega; Qty aur Price editable hain.")

    extra_rows_key = f"mrn_extra_rows_{selected_proj}"
    if extra_rows_key not in st.session_state:
        st.session_state[extra_rows_key] = []

    def add_extra_row():
        next_id = max(st.session_state[extra_rows_key], default=0) + 1
        st.session_state[extra_rows_key].append(next_id)

    def remove_extra_row(row_id):
        st.session_state[extra_rows_key] = [
            x for x in st.session_state[extra_rows_key] if x != row_id
        ]

    add_col, _ = st.columns([2, 8])
    with add_col:
        st.button(
            "➕ Add Extra Item",
            key=f"add_extra_item_{selected_proj}",
            use_container_width=True,
            on_click=add_extra_row
        )

    item_lookup = fetch_item_lookup(st.session_state.get('active_workspace', 'VISPL'))
    searchable_item_codes = [x["code"] for x in item_lookup.values()]
    searchable_item_codes = sorted(
        list(dict.fromkeys(searchable_item_codes)),
        key=lambda x: str(x).lower()
    )
    extra_items_to_save = []

    for row_id in st.session_state[extra_rows_key]:
        code_key = f"extra_item_code_{selected_proj}_{row_id}"
        ec1, ec2, ec3, ec4, ec5 = st.columns([1.6, 3.8, 1.2, 1.4, 0.55])
        with ec1:
            entered_code = st.selectbox(
                "Item Code *",
                options=[None] + searchable_item_codes,
                index=0,
                key=code_key,
                placeholder="Type to search Item Code...",
                format_func=lambda x: "" if x is None else str(x),
                help="Box par click karke Item Code ke starting numbers type karein. Matching codes turant filter honge."
            )
            entered_code = "" if entered_code is None else str(entered_code).strip()
        clean_entered_code = _clean_code_for_db(entered_code)
        master_item = item_lookup.get(str(clean_entered_code).strip().lower(), {})
        auto_description = master_item.get("description", "")
        default_adjusted_price = float(master_item.get("price", 0) or 0) * (team_percent / 100.0)

        with ec2:
            st.text_input(
                "Description (Auto)", value=auto_description,
                disabled=True,
                key=f"extra_desc_{selected_proj}_{row_id}_{str(clean_entered_code).lower()}"
            )
        with ec3:
            extra_qty = st.number_input(
                "Qty", min_value=0.0, step=0.01, value=0.0,
                key=f"extra_qty_{selected_proj}_{row_id}"
            )
        with ec4:
            extra_price = st.number_input(
                "Price", min_value=0.0, step=0.01,
                value=default_adjusted_price,
                key=f"extra_price_{selected_proj}_{row_id}_{str(clean_entered_code).lower()}"
            )
        with ec5:
            st.write("")
            st.button(
                "🗑️",
                key=f"remove_extra_{selected_proj}_{row_id}",
                help="Remove this item",
                on_click=remove_extra_row,
                args=(row_id,)
            )

        extra_total = float(extra_qty) * float(extra_price)
        if entered_code:
            st.caption(f"Extra Item Total: ₹ {extra_total:,.2f}")
        grand_basic_total += extra_total
        extra_items_to_save.append({
            "Item Code": clean_entered_code,
            "Description": auto_description,
            "User Qty": float(extra_qty),
            "Adjusted Price": float(extra_price),
            "Total": extra_total,
        })

    st.markdown('<div class="modal-section-title">💳 BILLING SUMMARY</div>', unsafe_allow_html=True)
    
    final_amount = grand_basic_total
    
    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;
                    background:linear-gradient(90deg,#f5f3ff,#eef2ff); border:1px solid #c7d2fe; border-radius:14px; padding:16px 22px;">
            <div>
                <div style="color:#64748b; font-weight:800; font-size:.75rem; letter-spacing:1px; text-transform:uppercase;">Basic Amount</div>
                <div style="color:#0f172a; font-weight:900; font-size:1.3rem;">₹ {grand_basic_total:,.2f}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b; font-weight:800; font-size:.75rem; letter-spacing:1px; text-transform:uppercase;">Grand Total</div>
                <div style="color:#4f46e5; font-weight:900; font-size:1.6rem;">₹ {final_amount:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_save1, col_save2 = st.columns([7, 3])
    with col_save2:
        if st.button("💾 Generate MRN (Send for Approval)", type="primary", use_container_width=True):
            if selected_proj == "Select Project ID":
                st.error("⚠️ Please select a Project ID.")
                return
            
            if not team_name or str(team_name).strip() in ["", "nan", "None", "Select"]:
                st.error("⚠️ Team Name is required! Please assign a team to this project in Site Data before generating MRN.")
                return
                
            valid_extra_items = [x for x in extra_items_to_save if x["Item Code"] and x["User Qty"] > 0]
            if not selected_pos and not valid_extra_items:
                st.error("⚠️ Please select at least one PO or add one Extra Item with Qty greater than 0.")
                return
            if grand_basic_total <= 0:
                st.error("⚠️ User Qty must be greater than 0 to generate MRN.")
                return
            
            for po, edf in all_po_dfs.items():
                for idx, r in edf.iterrows():
                    u_qty = pd.to_numeric(r["User Qty"], errors='coerce')
                    a_qty = pd.to_numeric(r["Available Qty"], errors='coerce')
                    u_qty = 0.0 if pd.isna(u_qty) else round(float(u_qty), 3)
                    a_qty = 0.0 if pd.isna(a_qty) else round(float(a_qty), 3)
                    if u_qty > a_qty + 1e-6:
                        st.error(f"❌ Error in PO {po}: User Qty ({u_qty:g}) cannot be greater than Available Qty ({a_qty:g}) for Item '{r['Item Code']}'.")
                        return

            for item in valid_extra_items:
                if not item["Description"]:
                    st.error(f"❌ Item Code '{item['Item Code']}' PO Working me nahi mila. Sahi Item Code enter karein.")
                    return
                if item["Adjusted Price"] <= 0:
                    st.error(f"❌ Extra Item '{item['Item Code']}' ka Price 0 se greater hona chahiye.")
                    return

            while True:
                new_mrn_no = f"MRN-{random.randint(100000, 999999)}"
                try:
                    check_res = supabase.table("mrn_data").select('"MRN Number"').eq("MRN Number", new_mrn_no).execute()
                    if not check_res.data:
                        break 
                except Exception:
                    break 
            
            header_data = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "MRN Number": new_mrn_no,
                "Team Name": team_name,
                "Project ID": selected_proj,
                "Site ID": site_id,
                "Site Name": site_name,
                "Cluster": cluster,
                "Basic Amount": grand_basic_total,
                "Total Amount": final_amount,
                "Team Percent": float(team_percent),
                "Description": mrn_description.strip() if mrn_description else "",
                "Date": datetime.date.today().strftime("%d-%m-%Y")
            }
            
            try:
                # Save Header
                supabase.table("mrn_data").insert(header_data).execute()
                
                items_to_insert = []
                for po, d_df in all_po_dfs.items():
                    for _, row in d_df.iterrows():
                        u_qty = pd.to_numeric(row["User Qty"], errors='coerce')
                        if pd.notna(u_qty) and u_qty > 0:
                            items_to_insert.append({
                                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                                "MRN Number": new_mrn_no,
                                "PO Number": _clean_code_for_db(po),
                                "Project ID": selected_proj,
                                "Item Code": _clean_code_for_db(row["Item Code"]),
                                "Description": str(row["Item Description"]),
                                "User Qty": round(float(u_qty), 3),
                                "Adjusted Price": float(row["Adjusted Price"]),
                                "Total": float(row["Line Total"])
                            })

                for item in valid_extra_items:
                    items_to_insert.append({
                        "workspace": st.session_state.get('active_workspace', 'VISPL'),
                        "MRN Number": new_mrn_no,
                        "PO Number": "NON-PO",
                        "Project ID": selected_proj,
                        "Item Code": _clean_code_for_db(item["Item Code"]),
                        "Description": str(item["Description"]),
                        "User Qty": round(float(item["User Qty"]), 3),
                        "Adjusted Price": float(item["Adjusted Price"]),
                        "Total": float(item["Total"])
                    })

                items_saved_count = 0
                if items_to_insert:
                    try:
                        supabase.table("mrn_items").insert(items_to_insert).execute()
                        items_saved_count = len(items_to_insert)
                        st.session_state.mrn_items_error_banner = None
                    except Exception as batch_err:
                        row_failures = []
                        for item in items_to_insert:
                            try:
                                supabase.table("mrn_items").insert(item).execute()
                                items_saved_count += 1
                            except Exception as row_err:
                                row_failures.append({
                                    "item_code": item.get("Item Code", "?"),
                                    "error": str(row_err),
                                })
                        if row_failures:
                            st.session_state.mrn_items_error_banner = {
                                "mrn_no": new_mrn_no,
                                "error": f"Batch insert failed ({batch_err}). Row-by-row retry: "
                                         f"{items_saved_count} saved, {len(row_failures)} failed — "
                                         + "; ".join(f"Item Code '{f['item_code']}': {f['error']}" for f in row_failures),
                                "attempted_count": len(items_to_insert),
                            }
                        else:
                            st.session_state.mrn_items_error_banner = None
                else:
                    st.session_state.mrn_items_error_banner = {
                        "mrn_no": new_mrn_no,
                        "error": "No line items had a User Qty > 0 at save time, even though Basic Amount was non-zero. The typed quantities did not carry through to the save step.",
                        "attempted_count": 0,
                    }

                billing_payload = {
                    "workspace": st.session_state.get('active_workspace', 'VISPL'),
                    "invoice_type": "Team",
                    "team_name": team_name,
                    "amount": float(grand_basic_total),
                    "basic_amount": float(grand_basic_total),
                    "gst_amount": 0.0,
                    "date": str(datetime.date.today()), 
                    "project_id": selected_proj,
                    "site_id": site_id,
                    "site_name": site_name,
                    "invoice_no": new_mrn_no,
                    "vendor_name": "",
                    "remark": "Data Taken by MRN",
                    "cluster": cluster
                }
                try:
                    supabase.table("pending_billing_invoices").insert(billing_payload).execute()
                    if items_saved_count == len(items_to_insert) and items_to_insert:
                        st.success(f"✅ MRN Generated Successfully! ID: {new_mrn_no} ({items_saved_count} line item(s) saved, sent for Approval in Team Billing)")
                    else:
                        st.warning(f"⚠️ MRN '{new_mrn_no}' was generated and sent for approval, but its line items did NOT save correctly — see the banner at the top of the page for details.")
                except Exception as e:
                    st.warning(
                        f"⚠️ MRN '{new_mrn_no}' saved, but sending it to Pending Team Billing FAILED: {e}\n\n"
                        f"Payload attempted: {billing_payload}"
                    )
                st.session_state.mrn_current_page = 1
                fetch_mrn_data.clear()
                # ---> Clean up the row-level Qty widget state for these POs
                # so a future MRN on the same PO starts fresh (0 everywhere). <---
                for _po in selected_pos:
                    for _key in list(st.session_state.keys()):
                        if _key.startswith(f"mrn_row_qty_{_po}_"):
                            st.session_state.pop(_key, None)
                st.session_state.pop(extra_rows_key, None)
                for _key in list(st.session_state.keys()):
                    if _key.startswith((
                        f"extra_item_code_{selected_proj}_", f"extra_code_show_{selected_proj}_",
                        f"extra_desc_{selected_proj}_", f"extra_qty_{selected_proj}_",
                        f"extra_price_{selected_proj}_", f"remove_extra_{selected_proj}_"
                    )):
                        st.session_state.pop(_key, None)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Generating MRN: {e}")

# --- 5. EXPORT DIALOG ---
@st.dialog("📥 Export MRN Data", width="large")
def export_dialog(df_export):
    st.caption("Download your MRN/GRN records as an Excel file.")
    export_df = df_export.copy()
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='MRN Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="MRN_GRN_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

if st.session_state.get('mrn_items_error_banner'):
    _err = st.session_state.mrn_items_error_banner
    st.error(
        f"❌ **MRN '{_err['mrn_no']}' line items failed to save to `mrn_items`!**\n\n"
        f"Attempted to save **{_err['attempted_count']}** item(s).\n\n"
        f"**Reason:** {_err['error']}\n\n"
        f"The MRN header and its Team Billing entry were still created, but this MRN's item breakdown "
        f"(and its invoice PDF) will be incomplete until this is fixed."
    )
    if st.button("✖️ Dismiss this warning", key="dismiss_mrn_items_err"):
        st.session_state.mrn_items_error_banner = None
        st.rerun()

# --- 6. TOP ACTION BAR ---
col_title, col_ref, col_add, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>📦 MRN / GRN Desk</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        get_unlimited_po_working.clear()
        fetch_mrn_data.clear()
        fetch_project_ids.clear()
        fetch_mrn_used_qty_map.clear()
        st.rerun() 
with col_add:
    if st.button("➕ Add New MRN", type="primary", use_container_width=True):
        add_mrn_dialog() 
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.mrn_action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. FETCH & PREPARE MRN DATA ---
df_mrn = fetch_mrn_data()

columns_list = [
    "id", "MRN Number", "Team Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Basic Amount", "Total Amount", "Team Percent", "Description", "Date"
]

if not df_mrn.empty:
    df_mrn = df_mrn.copy()
    if 'id' in df_mrn.columns:
        df_mrn['id_num'] = pd.to_numeric(df_mrn['id'], errors='coerce')
        df_mrn = df_mrn.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
    for col in columns_list:
        if col not in df_mrn.columns:
            df_mrn[col] = ""
else:
    df_mrn = pd.DataFrame(columns=columns_list)

# --- EXPORT LOGIC TRIGGER ---
if st.session_state.get('mrn_action') == "export":
    export_dialog(df_mrn)
    st.session_state.mrn_action = "" 

# --- 8. SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("<h5 style='margin:0; color:#0f172a;'>🗄️ Generated MRN Records</h5>", unsafe_allow_html=True)
with col_search:
    search_query = st_keyup(
        "Search",
        placeholder="🔍 Search MRN records...",
        label_visibility="collapsed",
        debounce=300,
        key="mrn_search_keyup",
    )

if search_query and not df_mrn.empty:
    mask = df_mrn.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df_mrn = df_mrn[mask]

# Search badalne par page 1 par wapas
if st.session_state.get("mrn_last_search") != search_query:
    st.session_state.mrn_last_search = search_query
    st.session_state.mrn_current_page = 1

# --- KPI CARDS (search ke hisaab se) ---
def _num(v):
    n = pd.to_numeric(v, errors='coerce')
    return 0.0 if pd.isna(n) else float(n)

k_count = len(df_mrn)
k_total = sum(_num(v) for v in df_mrn["Total Amount"]) if k_count else 0.0
k_teams = df_mrn["Team Name"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA}).dropna().nunique() if k_count else 0
_today = datetime.date.today()
_dates = pd.to_datetime(df_mrn["Date"], format="%d-%m-%Y", errors="coerce") if k_count else pd.Series([], dtype="datetime64[ns]")
_this_month_mask = (_dates.dt.year == _today.year) & (_dates.dt.month == _today.month) if k_count else pd.Series([], dtype=bool)
k_month_count = int(_this_month_mask.sum()) if k_count else 0
k_month_amt = sum(_num(v) for v in df_mrn.loc[_this_month_mask.values, "Total Amount"]) if k_count else 0.0

def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
    return (
        f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
        f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
        f'<div class="lux-kpi-value {value_cls}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
    )

st.markdown(
    '<div class="lux-kpi-grid">'
    + _kpi("📦", "Total MRNs", f"{k_count:,}", "Filtered results" if search_query else "All records", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
    + _kpi("💰", "Total MRN Amount", f"₹ {k_total:,.0f}", "Sent to Team Billing", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5", "green")
    + _kpi("👷", "Teams", f"{k_teams:,}", "Unique teams", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb")
    + _kpi("🗓️", "This Month", f"{k_month_count:,}", f"₹ {k_month_amt:,.0f}", "linear-gradient(90deg,#ec4899,#a855f7)", "#fdf2f8")
    + '</div>',
    unsafe_allow_html=True,
)

# --- 9. PAGINATION LOGIC (10 lines per page) ---
rows_per_page = 10
total_rows = len(df_mrn)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.mrn_current_page > total_pages:
    st.session_state.mrn_current_page = total_pages
elif st.session_state.mrn_current_page < 1:
    st.session_state.mrn_current_page = 1

start_idx = (st.session_state.mrn_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

df_page = df_mrn.iloc[start_idx:end_idx].copy()

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

def _pill(v):
    s = _clean(v)
    if not s:
        return _MUTED
    return f"<div class='slux-cell'><span class='slux-pill'>{html.escape(s)}</span></div>"

def _date_cell(v):
    s = _clean(v)
    if not s:
        return _MUTED
    d = pd.to_datetime(s, format="%d-%m-%Y", errors="coerce")
    shown = d.strftime("%d %b %Y") if pd.notna(d) else s
    return f"<div class='slux-cell slux-soft' title='{html.escape(s)}'>{html.escape(shown)}</div>"

# --- 10. ✨ LAVISH MRN TABLE — single ⚙️ button at row start ---
COL_RATIOS = [0.55, 0.5, 1.3, 1.5, 1.3, 1.1, 1.6, 1.0, 1.1, 1.1, 0.8, 1.9, 1.1]
COL_LABELS = ["⚙️", "#", "MRN NUMBER", "TEAM NAME", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC", "TOTAL", "RATE %", "DESCRIPTION", "DATE"]

if df_page.empty:
    st.markdown(
        '<div class="slux-empty"><div>🗂️</div>'
        + ("No MRN records match your search." if search_query else "No MRN records found. Click ➕ Add New MRN to create one.")
        + '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">📦 MRN Register<span>newest first • scroll right for more →</span></div>'
        f'<div class="slux-badge">₹ {k_total:,.0f}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="site_table_wrap", height=560):
        with st.container(key="mrnhead"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                cls = " c" if i in (0, 1, 10) else (" r" if i in (8, 9) else "")
                h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            serial_no = start_idx + page_pos + 1
            rid = row_dict.get("id")
            mrn_no = row_dict.get('MRN Number', '')
            rk = rid if _clean(rid) else f"s{serial_no}"
            parity = "odd" if serial_no % 2 else "even"

            with st.container(key=f"mrnrow_{parity}_{rk}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                with rcols[0]:
                    with st.container(key=f"mrnpop_{rk}"):
                        with st.popover("⚙️"):
                            if st.button("✏️ Edit Date / View Items", key=f"edit_{rid}", use_container_width=True):
                                edit_mrn_dialog(row_dict)
                            if st.button("🗑️ Delete MRN & Auto-Bill", key=f"del_{rid}", use_container_width=True):
                                delete_mrn_dialog(rid, mrn_no)

                basic = _num(row_dict.get('Basic Amount', 0))
                tot = _num(row_dict.get('Total Amount', 0))
                team_pct = pd.to_numeric(row_dict.get('Team Percent', ''), errors='coerce')
                team_pct_display = f"{team_pct:g}%" if pd.notna(team_pct) else "—"
                team_nm = _clean(row_dict.get('Team Name'))

                rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)
                rcols[2].markdown(_chip(mrn_no, "mrn"), unsafe_allow_html=True)
                rcols[3].markdown(f"<div class='slux-cell' title='{html.escape(team_nm)}'><span class='mrn-team'>👷 {html.escape(team_nm)}</span></div>" if team_nm else _MUTED, unsafe_allow_html=True)
                rcols[4].markdown(_chip(row_dict.get('Project ID'), "proj"), unsafe_allow_html=True)
                rcols[5].markdown(_chip(row_dict.get('Site ID')), unsafe_allow_html=True)
                rcols[6].markdown(_txt(row_dict.get('Site Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[7].markdown(_pill(row_dict.get('Cluster')), unsafe_allow_html=True)
                rcols[8].markdown(f"<div class='slux-cell mrn-amt'>₹ {basic:,.2f}</div>", unsafe_allow_html=True)
                rcols[9].markdown(f"<div class='slux-cell mrn-amt total'>₹ {tot:,.2f}</div>", unsafe_allow_html=True)
                rcols[10].markdown(f"<div style='text-align:center;'><span class='mrn-rate'>{team_pct_display}</span></div>", unsafe_allow_html=True)
                rcols[11].markdown(_txt(row_dict.get('Description'), "slux-soft"), unsafe_allow_html=True)
                rcols[12].markdown(_date_cell(row_dict.get('Date')), unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    st.markdown(
        '<div class="slux-foot">'
        f'<div>{total_rows:,} MRN{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small></div>'
        f'<div class="slux-foot-amts"><span>Total: <b style="color:#059669;">₹ {k_total:,.2f}</b></span>'
        f'<span class="slux-foot-badge">Page {st.session_state.mrn_current_page} of {total_pages}</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- 11. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.mrn_current_page == 1)):
        st.session_state.mrn_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.mrn_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.mrn_current_page == total_pages)):
        st.session_state.mrn_current_page += 1
        st.rerun()
