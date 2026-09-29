"""
================================================================================
 VISIONTECH INFRA SOLUTION PVT. LTD.
 NOTIFICATIONS  —  Streamlit page (PO / RFAI / Photo-JMS)
================================================================================
"""

import io
import zipfile
import urllib.request
import streamlit as st
import html
import base64
import streamlit.components.v1 as components
from datetime import datetime, timezone
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="PO Notification - Visiontech", page_icon="🔔", layout="wide")

TABLE_NAME = "po_notifications"

# --- WORKSPACE / COMPANY STATE (mirrors Site Data Hub) ---
NOTIF_COMPANIES = [("VISPL", "VISPL"), ("Bhagyashree", "Bhagyashree")]
NOTIF_COMPANY_WORKSPACE_MAP = {"VISPL": "VISPL", "Bhagyashree": "BHAGYASHREE"}

if 'notification_company' not in st.session_state:
    st.session_state.notification_company = "VISPL"
if 'notification_workspace' not in st.session_state:
    st.session_state.notification_workspace = NOTIF_COMPANY_WORKSPACE_MAP[st.session_state.notification_company]
if 'notif_tab' not in st.session_state:
    st.session_state.notif_tab = "open"
if 'notif_main_tab' not in st.session_state:
    st.session_state.notif_main_tab = "po"
if 'rfai_notif_tab' not in st.session_state:
    st.session_state.rfai_notif_tab = "open"
if 'upload_notif_tab' not in st.session_state:
    st.session_state.upload_notif_tab = "open"

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Light Premium Theme */
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Gradient action buttons everywhere */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important; border: none; border-radius: 8px;
        font-weight: 800 !important; padding: 0.5rem 1rem;
        transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
    }
    div.stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.25);
    }
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important; font-weight: 800 !important;
    }

    /* PREMIUM SIDEBAR NAVIGATION */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        font-size: 1.05rem !important; transition: all 0.3s ease !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
        display: flex !important; align-items: center !important; gap: 12px !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important; transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important; color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border-color: transparent !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* WORKSPACE / TAB NAV BAR */
    .st-key-notif_company_nav_bar div[data-testid="stHorizontalBlock"],
    .st-key-notif_tab_nav_bar div[data-testid="stHorizontalBlock"],
    .st-key-notif_main_tab_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    
    .st-key-notif_company_nav_bar button, .st-key-notif_tab_nav_bar button, .st-key-notif_main_tab_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"], .st-key-notif_tab_nav_bar button[kind="secondary"], .st-key-notif_main_tab_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover, .st-key-notif_tab_nav_bar button[kind="secondary"]:hover, .st-key-notif_main_tab_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important; color: #0f172a !important; border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"] p, .st-key-notif_tab_nav_bar button[kind="secondary"] p, .st-key-notif_main_tab_bar button[kind="secondary"] p { color: #475569 !important; font-weight: 800 !important; }
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover p, .st-key-notif_tab_nav_bar button[kind="secondary"]:hover p, .st-key-notif_main_tab_bar button[kind="secondary"]:hover p { color: #0f172a !important; }
    
    .st-key-notif_company_nav_bar button[kind="primary"], .st-key-notif_tab_nav_bar button[kind="primary"], .st-key-notif_main_tab_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    .st-key-notif_company_nav_bar button[kind="primary"] p, .st-key-notif_tab_nav_bar button[kind="primary"] p, .st-key-notif_main_tab_bar button[kind="primary"] p { color: #ffffff !important; font-weight: 800 !important; }

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
    .st-key-notif_lux_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        max-height: 78vh !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 0 18px 18px !important;
        box-shadow: 0 12px 28px -14px rgba(79, 70, 229, 0.35) !important;
    }
    .st-key-notif_lux_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-notif_lux_wrap [data-testid="stHorizontalBlock"] {
        min-width: 1400px !important; flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-notif_lux_wrap [data-testid="stColumn"],
    .st-key-notif_lux_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    .st-key-notif_lux_wrap > .st-key-nlux_head,
    .st-key-notif_lux_wrap > div:has(.st-key-nlux_head) {
        position: sticky !important; top: 0 !important; z-index: 20 !important;
    }
    .st-key-nlux_head {
        background: linear-gradient(90deg, #312e81 0%, #4338ca 45%, #6d28d9 100%) !important;
        border-bottom: 3px solid #f59e0b !important;
        box-shadow: 0 8px 14px -8px rgba(30, 27, 75, .55) !important;
        padding: 14px 0 !important;
    }
    .st-key-nlux_head [data-testid="stColumn"], .st-key-nlux_head [data-testid="column"] { border-right: 1px solid rgba(255,255,255,.18) !important; }
    .slux-th { color: #ffffff !important; font-size: .76rem; font-weight: 900; letter-spacing: 1.2px; text-transform: uppercase; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.25); }
    .slux-th.c { text-align: center; }

    div[class*="st-key-nluxrow_"] {
        padding: 9px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-nluxrow_odd"] { background: #fafaff; }
    div[class*="st-key-nluxrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-nluxrow_"] p { margin: 0 !important; }

    /* Lavish Text Styles */
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

    /* Badges */
    .status-badge {
        display: inline-flex !important; align-items: center; gap: 6px;
        padding: 4px 11px !important; border-radius: 999px !important; border: 1px solid transparent;
        font-size: .7rem !important; font-weight: 800 !important; letter-spacing: .4px; white-space: nowrap;
    }
    .status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
    .status-green  { background: #dcfce7 !important; color: #15803d !important; border-color: #bbf7d0 !important; }
    .status-blue   { background: #dbeafe !important; color: #1d4ed8 !important; border-color: #bfdbfe !important; }
    .status-yellow { background: #fef9c3 !important; color: #a16207 !important; border-color: #fde68a !important; }
    .status-red    { background: #fee2e2 !important; color: #b91c1c !important; border-color: #fecaca !important; }
    .status-grey   { background: #f1f5f9 !important; color: #475569 !important; border-color: #e2e8f0 !important; }

    /* ==========================================================
       ACTION BUTTONS: BLACK, BOLD & 100% WIDTH
       ========================================================== */
    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a {
        height: 34px !important; min-height: 34px !important;
        padding: 0 10px !important; margin: 0 auto !important; border-radius: 8px !important;
        box-shadow: none !important; transition: all .2s ease !important;
        width: 100% !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        text-decoration: none !important;
    }

    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a { background: rgba(168,85,247,0.15) !important; border: 1px solid rgba(168,85,247,0.3) !important; }

    /* Force Text to BLACK & EXTRA BOLD */
    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button p,
    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button span,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button p,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button span,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a p,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a span {
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 0.9rem !important;
    }

    /* Hover Effects -> Turns White & Elevates */
    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button:hover,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a:hover {
        background: #a855f7 !important; border-color: #c084fc !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(168,85,247,.6) !important;
    }

    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button:hover p,
    .st-key-notif_lux_wrap div[class*="st-key-action_btn_"] button:hover span,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button:hover p,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] button:hover span,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a:hover p,
    .st-key-notif_lux_wrap div[class*="st-key-dl_btn_"] a:hover span {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)


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

# --- LAVISH TEXT HELPERS ---
def _clean(v):
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("nan", "none", "null", "-") else s

def _txt(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell {extra_cls}' title='{html.escape(s)}'>{html.escape(s)}</div>"

def _chip(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell'><span class='slux-chip {extra_cls}'>{html.escape(s)}</span></div>"

def _pill(v):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell'><span class='slux-pill'>{html.escape(s)}</span></div>"

def status_badge(val):
    v = str(val).strip()
    if not v or v.lower() in ("nan", "none", "-"):
        return "<span class='slux-muted'>—</span>"
    vl = v.lower()
    if vl == "not required":
        cls = "status-grey"
    elif "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "available", "closed"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress", "open"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<span class='status-badge {cls}'>{html.escape(v)}</span>"


# --- 4. PO NOTIFICATION DATA ---
@st.cache_data(ttl=15, show_spinner=False)
def fetch_notifications_cached(workspace, is_closed):
    try:
        res = (
            supabase.table(TABLE_NAME)
            .select("*")
            .eq("workspace", workspace)
            .eq("is_closed", is_closed)
            .order("closed_at" if is_closed else "po_number", desc=is_closed)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def clear_notif_cache():
    fetch_notifications_cached.clear()

def close_row(row_id):
    try:
        supabase.table(TABLE_NAME).update({
            "is_closed": True,
            "closed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Close karne me error: {e}")
        return False

def reopen_row(row_id):
    try:
        supabase.table(TABLE_NAME).update({
            "is_closed": False,
            "closed_at": None,
        }).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Reopen karne me error: {e}")
        return False


# ==============================================================
# --- RFAI NOTIFICATION DATA ---
# ==============================================================
RFAI_TABLE_NAME = "rfai_notifications"
RFAI_TARGET_STATUSES = [
    "Build Complete by BV",
    "Build Complete by PM",
    "Pending RFAI",
    "Post RFAI Hold",
    "RFAI Notice Accepted",
    "RFAI Notice Deemed Accepted",
    "RFAI Notice Rejected",
]
RFAI_TARGET_STATUSES_LOWER = {s.lower() for s in RFAI_TARGET_STATUSES}

def _fetch_all_site_data_paginated(workspace):
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        res = (
            supabase.table("site_data")
            .select('"Project ID","Project Name","Site ID","Site Name","RFAI Status","PO No.","WCC Number","Team Name"')
            .eq("workspace", workspace)
            .range(offset, offset + limit - 1)
            .execute()
        )
        chunk = res.data or []
        if not chunk:
            break
        all_rows.extend(chunk)
        if len(chunk) < limit:
            break
        offset += limit
    return all_rows

def sync_rfai_notifications(workspace):
    try:
        site_rows = _fetch_all_site_data_paginated(workspace)
        records = []
        for r in site_rows:
            status_val = str(r.get("RFAI Status", "") or "").strip()
            if status_val.lower() not in RFAI_TARGET_STATUSES_LOWER:
                continue
            proj_id = str(r.get("Project ID", "") or "").strip()
            if not proj_id:
                continue
            records.append({
                "workspace": workspace,
                "project_id": proj_id,
                "project_name": str(r.get("Project Name", "") or "").strip(),
                "site_id": str(r.get("Site ID", "") or "").strip(),
                "site_name": str(r.get("Site Name", "") or "").strip(),
                "rfai_status": status_val,
                "po_no": str(r.get("PO No.", "") or "").strip(),
                "wcc_number": str(r.get("WCC Number", "") or "").strip(),
                "updated_at": datetime.utcnow().isoformat(),
            })
        if records:
            supabase.table(RFAI_TABLE_NAME).upsert(
                records, on_conflict="workspace,project_id,rfai_status"
            ).execute()
    except Exception as e:
        st.error(f"🚨 RFAI sync error: {e}")

@st.cache_data(ttl=20, show_spinner=False)
def sync_rfai_cached(workspace):
    sync_rfai_notifications(workspace)
    return True

@st.cache_data(ttl=20, show_spinner=False)
def fetch_rfai_cached(workspace, is_closed):
    try:
        res = (
            supabase.table(RFAI_TABLE_NAME)
            .select("*")
            .eq("workspace", workspace)
            .eq("is_closed", is_closed)
            .order("closed_at" if is_closed else "project_id", desc=is_closed)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def clear_rfai_cache():
    sync_rfai_cached.clear()
    fetch_rfai_cached.clear()

def close_rfai_row(row_id):
    try:
        supabase.table(RFAI_TABLE_NAME).update({
            "is_closed": True,
            "closed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Close karne me error: {e}")
        return False

def reopen_rfai_row(row_id):
    try:
        supabase.table(RFAI_TABLE_NAME).update({
            "is_closed": False,
            "closed_at": None,
        }).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Reopen karne me error: {e}")
        return False


# ==============================================================
# --- PHOTO / JMS UPLOAD NOTIFICATION DATA ---
# ==============================================================
UPLOAD_TABLE_NAME = "upload_notifications"

@st.cache_data(ttl=15, show_spinner=False)
def fetch_uploads_cached(workspace, is_closed):
    try:
        res = (
            supabase.table(UPLOAD_TABLE_NAME)
            .select("*")
            .eq("workspace", workspace)
            .eq("is_closed", is_closed)
            .order("closed_at" if is_closed else "uploaded_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def clear_upload_cache():
    fetch_uploads_cached.clear()

def close_upload_rows(ids):
    try:
        supabase.table(UPLOAD_TABLE_NAME).update({
            "is_closed": True,
            "closed_at": datetime.now(timezone.utc).isoformat(),
        }).in_("id", ids).execute()
        return True
    except Exception as e:
        st.error(f"❌ Close karne me error: {e}")
        return False

def reopen_upload_rows(ids):
    try:
        supabase.table(UPLOAD_TABLE_NAME).update({
            "is_closed": False,
            "closed_at": None,
        }).in_("id", ids).execute()
        return True
    except Exception as e:
        st.error(f"❌ Reopen karne me error: {e}")
        return False

def group_uploads(rows):
    """Same site + same type ke rows ko ek line me jodo."""
    groups = {}
    for r in rows:
        key = (r.get("workspace"), r.get("project_id"), r.get("site_id"), r.get("upload_type"))
        g = groups.get(key)
        if not g:
            g = dict(r)
            g["ids"] = []
            g["links"] = []
            g["file_count"] = 0
            groups[key] = g
        g["ids"].append(r["id"])
        if r.get("file_link"):
            g["links"].append(r["file_link"])
        g["file_count"] += int(r.get("file_count") or 1)
        if str(r.get("uploaded_at", "")) > str(g.get("uploaded_at", "")):
            g["uploaded_at"] = r.get("uploaded_at")
        for f in ("team_name", "project_name", "site_name", "uploaded_by"):
            if r.get(f) and not g.get(f):
                g[f] = r.get(f)
    return sorted(groups.values(), key=lambda x: str(x.get("uploaded_at", "")), reverse=True)

@st.cache_data(ttl=300, show_spinner=False)
def site_lookup_maps():
    """site_data se (project_id, site_id) -> names. Dono workspace cover karta hai."""
    by_pair, by_site = {}, {}
    for ws in ("VISPL", "BHAGYASHREE"):
        try:
            for r in _fetch_all_site_data_paginated(ws):
                pid = str(r.get("Project ID", "") or "").strip()
                sid = str(r.get("Site ID", "") or "").strip()
                pname = str(r.get("Project Name", "") or "").strip()
                sname = str(r.get("Site Name", "") or "").strip()
                tname = str(r.get("Team Name", "") or "").strip()

                if sid:
                    by_pair[(pid, sid)] = (pid, pname, sname, tname)
                    by_site.setdefault(sid, (pid, pname, sname, tname))
        except Exception:
            pass
    return by_pair, by_site

def enrich_groups(groups):
    """Jis row me project/site/team name khali ho, use site_data se bharo."""
    by_pair, by_site = site_lookup_maps()
    for g in groups:
        pid = str(g.get("project_id") or "").strip()
        sid = str(g.get("site_id") or "").strip()
        hit = by_pair.get((pid, sid)) or by_site.get(sid)
        if not hit:
            continue
        if not g.get("project_id"):
            g["project_id"] = hit[0]
        if not g.get("project_name"):
            g["project_name"] = hit[1]
        if not g.get("site_name"):
            g["site_name"] = hit[2]
        
        if not g.get("team_name") and len(hit) > 3:
            g["team_name"] = hit[3]
            
    return groups

def build_download(links, base_name):
    """1 file -> seedha file. Bahut saari -> ZIP. Returns (bytes, filename, mime)."""
    def _get(u):
        req = urllib.request.Request(u, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()

    if len(links) == 1:
        name = links[0].split("/")[-1]
        mime = "application/pdf" if name.lower().endswith(".pdf") else "application/octet-stream"
        if name.lower().endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        elif name.lower().endswith(".png"):
            mime = "image/png"
        return _get(links[0]), name, mime

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for u in links:
            try:
                z.writestr(u.split("/")[-1], _get(u))
            except Exception:
                pass
    return buf.getvalue(), f"{base_name}.zip", "application/zip"


# --- 5. WORKSPACE NAV BAR ---
with st.container(key="notif_company_nav_bar"):
    nav_cols = st.columns(len(NOTIF_COMPANIES))
    for nav_col, (company_id, company_label) in zip(nav_cols, NOTIF_COMPANIES):
        is_active = st.session_state.notification_company == company_id
        with nav_col:
            if st.button(
                company_label, key=f"notif_nav_{company_id}",
                use_container_width=True, type=("primary" if is_active else "secondary")
            ):
                st.session_state.notification_company = company_id
                st.session_state.notification_workspace = NOTIF_COMPANY_WORKSPACE_MAP[company_id]
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

workspace = st.session_state.notification_workspace
company_display = st.session_state.notification_company

# --- 5.5 MAIN TAB BAR: PO / RFAI / Photo-JMS ---
upload_open_count_tab = len(group_uploads(fetch_uploads_cached(workspace, False)))

with st.container(key="notif_main_tab_bar"):
    mt1, mt2, mt3 = st.columns(3)
    with mt1:
        if st.button("📄 PO Notification", key="main_tab_po", use_container_width=True,
                     type=("primary" if st.session_state.notif_main_tab == "po" else "secondary")):
            st.session_state.notif_main_tab = "po"
            st.rerun()
    with mt2:
        if st.button("📋 RFAI Notification", key="main_tab_rfai", use_container_width=True,
                     type=("primary" if st.session_state.notif_main_tab == "rfai" else "secondary")):
            st.session_state.notif_main_tab = "rfai"
            st.rerun()
    with mt3:
        if st.button(f"📸 Photo / JMS ({upload_open_count_tab})", key="main_tab_upload", use_container_width=True,
                     type=("primary" if st.session_state.notif_main_tab == "upload" else "secondary")):
            st.session_state.notif_main_tab = "upload"
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. TOP BANNER ---
banner_label = {
    "po": "PO Notification",
    "rfai": "RFAI Notification",
    "upload": "Photo / JMS Notification",
}[st.session_state.notif_main_tab]

st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.2rem; text-transform: uppercase;">
            🔔 {company_display} — {banner_label}
        </h1>
    </div>
""", unsafe_allow_html=True)


# ==============================================================
# TAB 1: PO NOTIFICATION
# ==============================================================
if st.session_state.notif_main_tab == "po":
    open_rows_preview = fetch_notifications_cached(workspace, False)
    closed_rows_preview = fetch_notifications_cached(workspace, True)
    open_count = len(open_rows_preview)
    closed_count = len(closed_rows_preview)

    col_title, col_tabs, col_ref = st.columns([2, 3, 1])
    with col_title:
        st.markdown("<h2 style='margin:0; color:#0f172a;'>📋 Notifications</h2>", unsafe_allow_html=True)
    with col_tabs:
        with st.container(key="notif_tab_nav_bar"):
            t1, t2 = st.columns(2)
            with t1:
                if st.button(f"🔔 Open ({open_count})", key="notif_tab_open", use_container_width=True,
                             type=("primary" if st.session_state.notif_tab == "open" else "secondary")):
                    st.session_state.notif_tab = "open"
                    st.rerun()
            with t2:
                if st.button(f"✅ Closed ({closed_count})", key="notif_tab_closed", use_container_width=True,
                             type=("primary" if st.session_state.notif_tab == "closed" else "secondary")):
                    st.session_state.notif_tab = "closed"
                    st.rerun()
    with col_ref:
        if st.button("🔄 Refresh", key="refresh_po", use_container_width=True):
            clear_notif_cache()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    is_closed_tab = st.session_state.notif_tab == "closed"
    rows = closed_rows_preview if is_closed_tab else open_rows_preview

    if not rows:
        if is_closed_tab:
            st.info("Abhi tak kuch close nahi kiya gaya.")
        else:
            st.success("✅ Koi open notification nahi hai. Sab clear hai!")
    else:
        if is_closed_tab:
            col_ratios = [0.5, 1.8, 1.2, 1.4, 1.4, 1.6, 1.2]
            col_labels = ["#", "PO NUMBER", "REV NUMBER", "PO AMOUNT", "PO STATUS", "CLOSED AT", "ACTION"]
        else:
            col_ratios = [0.5, 1.8, 1.2, 1.4, 1.4, 1.2]
            col_labels = ["#", "PO NUMBER", "REV NUMBER", "PO AMOUNT", "PO STATUS", "ACTION"]

        st.markdown(
            '<div class="slux-head-bar">'
            '<div class="slux-title">📄 PO Notifications<span>manage purchase order approvals</span></div>'
            f'<div class="slux-badge">Total {len(rows)}</div>'
            '</div>', unsafe_allow_html=True
        )

        with st.container(key="notif_lux_wrap"):
            with st.container(key="nlux_head"):
                h_cols = st.columns(col_ratios, vertical_alignment="center")
                for h_idx, (h_col, label) in enumerate(zip(h_cols, col_labels)):
                    center_cls = " c" if h_idx == 0 else ""
                    h_col.markdown(f"<div class='slux-th{center_cls}'>{label}</div>", unsafe_allow_html=True)

            for pos, row in enumerate(rows):
                rid = row.get("id")
                parity = "odd" if pos % 2 else "even"
                with st.container(key=f"nluxrow_{parity}_{rid}"):
                    rcols = st.columns(col_ratios, vertical_alignment="center")
                    rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos + 1}</span></div>", unsafe_allow_html=True)
                    rcols[1].markdown(_chip(row.get('po_number'), "proj"), unsafe_allow_html=True)
                    rcols[2].markdown(_pill(row.get('rev_number')), unsafe_allow_html=True)
                    rcols[3].markdown(_txt(row.get('amount'), "slux-strong"), unsafe_allow_html=True)
                    rcols[4].markdown(status_badge(row.get('po_status')), unsafe_allow_html=True)

                    if is_closed_tab:
                        closed_at = row.get("closed_at", "-")
                        closed_at_display = str(closed_at)[:19].replace("T", " ") if closed_at else "-"
                        rcols[5].markdown(_txt(closed_at_display, "slux-soft"), unsafe_allow_html=True)
                        with rcols[6]:
                            with st.container(key=f"action_btn_reopen_{rid}"):
                                if st.button("↩️ Reopen", key=f"reopen_{rid}", use_container_width=True):
                                    if reopen_row(rid):
                                        clear_notif_cache()
                                        st.rerun()
                    else:
                        with rcols[5]:
                            with st.container(key=f"action_btn_close_{rid}"):
                                if st.button("✅ Close", key=f"close_{rid}", use_container_width=True):
                                    if close_row(rid):
                                        clear_notif_cache()
                                        st.rerun()


# ==============================================================
# TAB 2: RFAI NOTIFICATION
# ==============================================================
elif st.session_state.notif_main_tab == "rfai":
    sync_rfai_cached(workspace)
    open_rfai_preview = fetch_rfai_cached(workspace, False)
    closed_rfai_preview = fetch_rfai_cached(workspace, True)
    open_rfai_count = len(open_rfai_preview)
    closed_rfai_count = len(closed_rfai_preview)

    col_title, col_tabs, col_ref = st.columns([2, 3, 1])
    with col_title:
        st.markdown("<h2 style='margin:0; color:#0f172a;'>📋 Notifications</h2>", unsafe_allow_html=True)
    with col_tabs:
        with st.container(key="notif_tab_nav_bar"):
            t1, t2 = st.columns(2)
            with t1:
                if st.button(f"🔔 Open ({open_rfai_count})", key="rfai_tab_open", use_container_width=True,
                             type=("primary" if st.session_state.rfai_notif_tab == "open" else "secondary")):
                    st.session_state.rfai_notif_tab = "open"
                    st.rerun()
            with t2:
                if st.button(f"✅ Closed ({closed_rfai_count})", key="rfai_tab_closed", use_container_width=True,
                             type=("primary" if st.session_state.rfai_notif_tab == "closed" else "secondary")):
                    st.session_state.rfai_notif_tab = "closed"
                    st.rerun()
    with col_ref:
        if st.button("🔄 Refresh", key="refresh_rfai", use_container_width=True):
            clear_rfai_cache()
            st.rerun()

    st.caption("Tracked RFAI statuses: " + ", ".join(RFAI_TARGET_STATUSES))
    st.markdown("<br>", unsafe_allow_html=True)

    is_rfai_closed_tab = st.session_state.rfai_notif_tab == "closed"
    rfai_rows = closed_rfai_preview if is_rfai_closed_tab else open_rfai_preview

    if not rfai_rows:
        if is_rfai_closed_tab:
            st.info("Abhi tak kuch close nahi kiya gaya.")
        else:
            st.success("✅ Koi open RFAI notification nahi hai. Sab clear hai!")
    else:
        if is_rfai_closed_tab:
            col_ratios = [0.5, 1.5, 1.8, 1.1, 1.6, 1.6, 1.3, 1.3, 1.6, 1.2]
            col_labels = ["#", "PROJECT ID", "PROJECT NAME", "SITE ID", "SITE NAME", "RFAI STATUS",
                          "PO NUMBER", "WCC NUMBER", "CLOSED AT", "ACTION"]
        else:
            col_ratios = [0.5, 1.5, 1.8, 1.1, 1.6, 1.6, 1.3, 1.3, 1.2]
            col_labels = ["#", "PROJECT ID", "PROJECT NAME", "SITE ID", "SITE NAME", "RFAI STATUS",
                          "PO NUMBER", "WCC NUMBER", "ACTION"]

        st.markdown(
            '<div class="slux-head-bar">'
            '<div class="slux-title">📋 RFAI Notifications<span>manage readiness for active integration</span></div>'
            f'<div class="slux-badge">Total {len(rfai_rows)}</div>'
            '</div>', unsafe_allow_html=True
        )

        with st.container(key="notif_lux_wrap"):
            with st.container(key="nlux_head"):
                h_cols = st.columns(col_ratios, vertical_alignment="center")
                for h_idx, (h_col, label) in enumerate(zip(h_cols, col_labels)):
                    center_cls = " c" if h_idx == 0 else ""
                    h_col.markdown(f"<div class='slux-th{center_cls}'>{label}</div>", unsafe_allow_html=True)

            for pos, row in enumerate(rfai_rows):
                rid = row.get("id")
                project_name = row.get("project_name", "") or ""
                parity = "odd" if pos % 2 else "even"
                
                with st.container(key=f"nluxrow_{parity}_{rid}"):
                    rcols = st.columns(col_ratios, vertical_alignment="center")
                    rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos + 1}</span></div>", unsafe_allow_html=True)
                    rcols[1].markdown(_chip(row.get('project_id'), "proj"), unsafe_allow_html=True)
                    rcols[2].markdown(_txt(project_name, "slux-strong"), unsafe_allow_html=True)
                    rcols[3].markdown(_chip(row.get('site_id')), unsafe_allow_html=True)
                    rcols[4].markdown(_txt(row.get('site_name'), "slux-strong"), unsafe_allow_html=True)
                    rcols[5].markdown(status_badge(row.get('rfai_status')), unsafe_allow_html=True)
                    rcols[6].markdown(_chip(row.get('po_no')), unsafe_allow_html=True)
                    rcols[7].markdown(_chip(row.get('wcc_number')), unsafe_allow_html=True)

                    if is_rfai_closed_tab:
                        closed_at = row.get("closed_at", "-")
                        closed_at_display = str(closed_at)[:19].replace("T", " ") if closed_at else "-"
                        rcols[8].markdown(_txt(closed_at_display, "slux-soft"), unsafe_allow_html=True)
                        with rcols[9]:
                            with st.container(key=f"action_btn_rreopen_{rid}"):
                                if st.button("↩️ Reopen", key=f"rfai_reopen_{rid}", use_container_width=True):
                                    if reopen_rfai_row(rid):
                                        clear_rfai_cache()
                                        st.rerun()
                    else:
                        with rcols[8]:
                            with st.container(key=f"action_btn_rclose_{rid}"):
                                if st.button("✅ Close", key=f"rfai_close_{rid}", use_container_width=True):
                                    if close_rfai_row(rid):
                                        clear_rfai_cache()
                                        st.rerun()


# ==============================================================
# TAB 3: PHOTO / JMS UPLOAD NOTIFICATION
# ==============================================================
else:
    open_up = enrich_groups(group_uploads(fetch_uploads_cached(workspace, False)))
    closed_up = enrich_groups(group_uploads(fetch_uploads_cached(workspace, True)))

    col_title, col_tabs, col_ref = st.columns([2, 3, 1])
    with col_title:
        st.markdown("<h2 style='margin:0; color:#0f172a;'>📸 Uploads</h2>", unsafe_allow_html=True)
    with col_tabs:
        with st.container(key="notif_tab_nav_bar"):
            t1, t2 = st.columns(2)
            with t1:
                if st.button(f"🔔 Open ({len(open_up)})", key="up_tab_open", use_container_width=True,
                             type=("primary" if st.session_state.upload_notif_tab == "open" else "secondary")):
                    st.session_state.upload_notif_tab = "open"
                    st.rerun()
            with t2:
                if st.button(f"✅ Billed / Closed ({len(closed_up)})", key="up_tab_closed", use_container_width=True,
                             type=("primary" if st.session_state.upload_notif_tab == "closed" else "secondary")):
                    st.session_state.upload_notif_tab = "closed"
                    st.rerun()
    with col_ref:
        if st.button("🔄 Refresh", key="refresh_upload", use_container_width=True):
            clear_upload_cache()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    is_up_closed_tab = st.session_state.upload_notif_tab == "closed"
    up_rows = closed_up if is_up_closed_tab else open_up

    sc1, sc2 = st.columns([3, 2])
    with sc1:
        search_q = st.text_input(
            "Search", key="up_search", label_visibility="collapsed",
            placeholder="🔍 Search: Team, Site Name, Site ID, Project ID, Project Name..."
        ).strip().lower()
    with sc2:
        type_filter = st.radio("Type", ["All", "Photo", "JMS"], horizontal=True,
                               key="up_type_filter", label_visibility="collapsed")

    if type_filter != "All":
        up_rows = [r for r in up_rows if str(r.get("upload_type", "")).lower() == type_filter.lower()]

    if search_q:
        def _hay(r):
            return " ".join(str(r.get(k) or "") for k in
                            ("team_name", "uploaded_by", "site_name", "site_id",
                             "project_id", "project_name", "upload_type")).lower()
        up_rows = [r for r in up_rows if search_q in _hay(r)]

    if st.session_state.get("dl_error"):
        st.error(st.session_state.pop("dl_error"))

    if not up_rows:
        if is_up_closed_tab:
            st.info("Abhi tak kuch close nahi kiya gaya.")
        else:
            st.success("✅ Koi naya upload pending nahi hai. Sab clear hai!")
    else:
        if is_up_closed_tab:
            col_ratios = [0.4, 1.3, 1.7, 1.0, 1.2, 1.7, 1.2, 1.4, 1.5, 1.2]
            col_labels = ["#", "TEAM NAME", "SITE NAME", "SITE ID", "PROJECT ID", "PROJECT NAME",
                          "PHOTO / JMS", "DOWNLOAD", "CLOSED AT", "ACTION"]
        else:
            col_ratios = [0.4, 1.3, 1.7, 1.0, 1.2, 1.7, 1.2, 1.4, 1.2]
            col_labels = ["#", "TEAM NAME", "SITE NAME", "SITE ID", "PROJECT ID", "PROJECT NAME",
                          "PHOTO / JMS", "DOWNLOAD", "ACTION"]

        st.markdown(
            '<div class="slux-head-bar">'
            '<div class="slux-title">📸 Photo / JMS Uploads<span>manage site assets & documents</span></div>'
            f'<div class="slux-badge">Total {len(up_rows)}</div>'
            '</div>', unsafe_allow_html=True
        )

        with st.container(key="notif_lux_wrap"):
            with st.container(key="nlux_head"):
                h_cols = st.columns(col_ratios, vertical_alignment="center")
                for h_idx, (h_col, label) in enumerate(zip(h_cols, col_labels)):
                    center_cls = " c" if h_idx == 0 else ""
                    h_col.markdown(f"<div class='slux-th{center_cls}'>{label}</div>", unsafe_allow_html=True)

            for pos, row in enumerate(up_rows):
                rid = row["ids"][0]
                parity = "odd" if pos % 2 else "even"
                
                with st.container(key=f"nluxrow_{parity}_{rid}"):
                    rcols = st.columns(col_ratios, vertical_alignment="center")
                    up_type = str(row.get("upload_type", "-"))
                    type_cls = "status-blue" if up_type.lower() == "photo" else "status-yellow"
                    team = row.get("team_name") or row.get("uploaded_by") or "-"
                    pname = row.get("project_name") or "-"

                    rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos + 1}</span></div>", unsafe_allow_html=True)
                    rcols[1].markdown(_pill(team), unsafe_allow_html=True)
                    rcols[2].markdown(_txt(row.get('site_name'), "slux-strong"), unsafe_allow_html=True)
                    rcols[3].markdown(_chip(row.get('site_id')), unsafe_allow_html=True)
                    rcols[4].markdown(_chip(row.get('project_id'), "proj"), unsafe_allow_html=True)
                    rcols[5].markdown(_txt(pname, "slux-strong"), unsafe_allow_html=True)
                    rcols[6].markdown(f"<span class='status-badge {type_cls}'>{up_type} ({row.get('file_count', 1)})</span>", unsafe_allow_html=True)

                    # --- 1-CLICK DOWNLOAD LOGIC ---
                    with rcols[7]:
                        with st.container(key=f"dl_btn_{rid}"):
                            if row.get("links"):
                                if len(row["links"]) == 1:
                                    # Native Streamlit link button for Single file (Native 1-click)
                                    st.link_button("⬇️ Download", row["links"][0], use_container_width=True)
                                else:
                                    # For ZIP (Multiple files), clicking builds zip & triggers auto download via JS
                                    if st.button("⬇️ Download ZIP", key=f"up_dl_{rid}", use_container_width=True):
                                        with st.spinner("Zipping..."):
                                            try:
                                                base = f"{row.get('site_id') or 'site'}_{up_type}"
                                                zip_data, fname, mime = build_download(row["links"], base)
                                                b64 = base64.b64encode(zip_data).decode()
                                                
                                                js_trigger = f"""
                                                <script>
                                                    var link = document.createElement('a');
                                                    link.href = 'data:{mime};base64,{b64}';
                                                    link.download = '{fname}';
                                                    document.body.appendChild(link);
                                                    link.click();
                                                    document.body.removeChild(link);
                                                </script>
                                                """
                                                components.html(js_trigger, height=0)
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")
                            else:
                                st.markdown("<div style='text-align:center;'><span class='slux-muted'>—</span></div>", unsafe_allow_html=True)

                    if is_up_closed_tab:
                        closed_at = str(row.get("closed_at", "") or "")[:19].replace("T", " ") or "-"
                        rcols[8].markdown(_txt(closed_at, "slux-soft"), unsafe_allow_html=True)
                        with rcols[9]:
                            with st.container(key=f"action_btn_ureopen_{rid}"):
                                if st.button("↩️ Reopen", key=f"up_reopen_{rid}", use_container_width=True):
                                    if reopen_upload_rows(row["ids"]):
                                        clear_upload_cache()
                                        st.rerun()
                    else:
                        with rcols[8]:
                            with st.container(key=f"action_btn_uclose_{rid}"):
                                if st.button("✅ Close", key=f"up_close_{rid}", use_container_width=True):
                                    if close_upload_rows(row["ids"]):
                                        clear_upload_cache()
                                        st.rerun()
