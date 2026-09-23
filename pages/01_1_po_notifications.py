"""
================================================================================
 VISIONTECH INFRA SOLUTION PVT. LTD.
 PO NOTIFICATION  —  Streamlit page (matches Site Data Hub's design system)
 --------------------------------------------------------------------------
 IMPORTANT: save this file at exactly:
     pages/15_🔔_PO_Notifications.py
 (same folder structure as your other numbered pages), because Site Data
 Hub navigates here with:
     st.switch_page("pages/15_🔔_PO_Notifications.py")

 Reads/writes the Supabase table `po_notifications` (see
 supabase_po_notifications.sql). Data lands there from the desktop "PO &
 WCC Upload Software" app's Notification tab.

 Workspace handling:
   - If opened via the "🔔 Notifications" button on Site Data Hub, it
     already set st.session_state['notification_workspace'] /
     ['notification_company'] to match whichever company tab was active
     there — this page picks that up automatically.
   - If opened directly (e.g. from the sidebar), a VISPL / Bhagyashree
     switcher bar (same style as Site Data Hub's company tabs) lets the
     user pick.

 Flow:
   - "🔔 Open" tab (default): every revised PO not yet closed, each row
     with a "✅ Close" button. Clicking it marks that row is_closed = True
     and it moves to the Closed tab.
   - "✅ Closed" tab: history of everything already closed, with a
     "↩️ Reopen" button in case something was closed by mistake.
   - When the desktop app finds a NEW revision for a PO you already
     closed, that new revision inserts as a brand-new (open) row — so it
     shows up in Open again, while your closed record for the old
     revision stays untouched in Closed.
================================================================================
"""

import streamlit as st
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

# --- 2. LAVISH CUSTOM CSS (same design language as Site Data Hub) ---
st.markdown("""
    <style>
    /* Light Premium Theme */
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    /* Gradient action buttons everywhere (Refresh, tabs, Close/Reopen...) */
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
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION (identical to other pages)
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

    /* =========================================================
       WORKSPACE / TAB NAV BAR (VISPL / Bhagyashree AND Open / Closed)
       — same segmented-button pattern as Site Data Hub's company bar
       ========================================================= */
    .st-key-notif_company_nav_bar div[data-testid="stHorizontalBlock"],
    .st-key-notif_tab_nav_bar div[data-testid="stHorizontalBlock"],
    .st-key-notif_main_tab_bar div[data-testid="stHorizontalBlock"] {
        gap: 12px !important; flex-wrap: wrap !important;
    }
    .st-key-notif_company_nav_bar button,
    .st-key-notif_tab_nav_bar button,
    .st-key-notif_main_tab_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"],
    .st-key-notif_tab_nav_bar button[kind="secondary"],
    .st-key-notif_main_tab_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover,
    .st-key-notif_tab_nav_bar button[kind="secondary"]:hover,
    .st-key-notif_main_tab_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important; color: #0f172a !important;
        border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
    }
    .st-key-notif_company_nav_bar button[kind="secondary"] p,
    .st-key-notif_company_nav_bar button[kind="secondary"] span,
    .st-key-notif_company_nav_bar button[kind="secondary"] div,
    .st-key-notif_tab_nav_bar button[kind="secondary"] p,
    .st-key-notif_tab_nav_bar button[kind="secondary"] span,
    .st-key-notif_tab_nav_bar button[kind="secondary"] div,
    .st-key-notif_main_tab_bar button[kind="secondary"] p,
    .st-key-notif_main_tab_bar button[kind="secondary"] span,
    .st-key-notif_main_tab_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover p,
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover span,
    .st-key-notif_company_nav_bar button[kind="secondary"]:hover div,
    .st-key-notif_tab_nav_bar button[kind="secondary"]:hover p,
    .st-key-notif_tab_nav_bar button[kind="secondary"]:hover span,
    .st-key-notif_tab_nav_bar button[kind="secondary"]:hover div,
    .st-key-notif_main_tab_bar button[kind="secondary"]:hover p,
    .st-key-notif_main_tab_bar button[kind="secondary"]:hover span,
    .st-key-notif_main_tab_bar button[kind="secondary"]:hover div { color: #0f172a !important; }
    .st-key-notif_company_nav_bar button[kind="primary"],
    .st-key-notif_tab_nav_bar button[kind="primary"],
    .st-key-notif_main_tab_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    .st-key-notif_company_nav_bar button[kind="primary"] p,
    .st-key-notif_company_nav_bar button[kind="primary"] span,
    .st-key-notif_company_nav_bar button[kind="primary"] div,
    .st-key-notif_tab_nav_bar button[kind="primary"] p,
    .st-key-notif_tab_nav_bar button[kind="primary"] span,
    .st-key-notif_tab_nav_bar button[kind="primary"] div,
    .st-key-notif_main_tab_bar button[kind="primary"] p,
    .st-key-notif_main_tab_bar button[kind="primary"] span,
    .st-key-notif_main_tab_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; }

    /* =========================================================
       LAVISH TABLE (identical pattern to site_table_wrap)
       ========================================================= */
    .st-key-notif_table_wrap {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.15);
        border-radius: 10px;
        overflow: auto !important;
        padding: 0px 0 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .st-key-notif_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 900px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(0,0,0,0.12) !important;
        padding: 10px 0 !important;
        flex-wrap: nowrap !important;
        background: #ffffff !important;
    }
    .st-key-notif_table_wrap div[data-testid="stHorizontalBlock"]:has(.tbl-head) {
        background: #eef2ff !important;
        border-bottom: 2px solid rgba(79,70,229,0.35) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 2 !important;
    }
    .st-key-notif_table_wrap div[data-testid="stHorizontalBlock"]:not(:has(.tbl-head)):hover {
        background: #f8fafc !important;
    }
    .st-key-notif_table_wrap div[data-testid="column"] {
        padding: 0 15px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(0,0,0,0.08);
    }
    .st-key-notif_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-notif_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #312e81;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    .st-key-notif_table_wrap .tbl-cell {
        color: #0f172a;
        font-size: 0.9rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-notif_table_wrap .tbl-serial { color: #64748b; font-size: 0.85rem; font-weight: 800; }

    /* Status badge pill (same palette as Site Data Hub) */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.4px;
        white-space: nowrap !important;
        text-align: center;
    }
    .status-green  { background: rgba(34,197,94,0.15);  color: #15803d; }
    .status-blue   { background: rgba(59,130,246,0.15); color: #1d4ed8; }
    .status-yellow { background: rgba(234,179,8,0.15);  color: #a16207; }
    .status-red    { background: rgba(239,68,68,0.15);  color: #b91c1c; }
    .status-grey   { background: rgba(148,163,184,0.18); color: #334155; }
    </style>
""", unsafe_allow_html=True)


# --- 3. SUPABASE CONNECTION (same pattern as Site Data Hub) ---
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


def status_badge(val):
    v = str(val).strip()
    if not v or v.lower() in ("nan", "none", "-"):
        return "<span class='tbl-cell'>-</span>"
    vl = v.lower()
    if vl == "not required":
        cls = "status-grey"
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
    return f"<span class='status-badge {cls}'>{v}</span>"


# --- 4. CACHED DATA FETCHERS (same TTL-cache pattern as Site Data Hub) ---
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
# --- RFAI NOTIFICATION (2nd tab) ---
# Pulled directly from site_data's "RFAI Status" column — no desktop app
# involved. Synced into its own rfai_notifications table on each load so
# Close/Reopen state can persist independently of the live site_data row.
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
    """Supabase caps a single select() at ~1000 rows by default — page through
    with .range() so large workspaces are fully covered."""
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        res = (
            supabase.table("site_data")
            .select("Project ID, Site ID, Site Name, RFAI Status")
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
    """Scans site_data for the 7 tracked RFAI statuses and upserts them into
    rfai_notifications (is_closed is never touched by this upsert)."""
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
                "site_id": str(r.get("Site ID", "") or "").strip(),
                "site_name": str(r.get("Site Name", "") or "").strip(),
                "rfai_status": status_val,
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


# --- 5. WORKSPACE NAV BAR (VISPL / Bhagyashree — same style as Site Data Hub) ---
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

# --- 5.5 MAIN TAB BAR: PO Notification / RFAI Notification ---
with st.container(key="notif_main_tab_bar"):
    mt1, mt2 = st.columns(2)
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

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. TOP BANNER (same gradient banner style as Site Data Hub) ---
banner_label = "PO Notification" if st.session_state.notif_main_tab == "po" else "RFAI Notification"
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.2rem; text-transform: uppercase;">
            🔔 {company_display} — {banner_label}
        </h1>
    </div>
""", unsafe_allow_html=True)

if st.session_state.notif_main_tab == "po":
    # --- 7. TOP ACTION BAR: title + Open/Closed segmented tabs + Refresh ---
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

    # --- 8. LAVISH TABLE ---
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

        with st.container(key="notif_table_wrap", height=520):
            h_cols = st.columns(col_ratios)
            for h_col, label in zip(h_cols, col_labels):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for pos, row in enumerate(rows):
                rid = row.get("id")
                rcols = st.columns(col_ratios)
                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)
                rcols[1].markdown(f"<div class='tbl-cell'>{row.get('po_number', '-')}</div>", unsafe_allow_html=True)
                rcols[2].markdown(f"<div class='tbl-cell'>{row.get('rev_number', '-')}</div>", unsafe_allow_html=True)
                rcols[3].markdown(f"<div class='tbl-cell'>{row.get('amount', '-')}</div>", unsafe_allow_html=True)
                rcols[4].markdown(status_badge(row.get('po_status', '-')), unsafe_allow_html=True)

                if is_closed_tab:
                    closed_at = row.get("closed_at", "-")
                    closed_at_display = str(closed_at)[:19].replace("T", " ") if closed_at else "-"
                    rcols[5].markdown(f"<div class='tbl-cell'>{closed_at_display}</div>", unsafe_allow_html=True)
                    with rcols[6]:
                        if st.button("↩️ Reopen", key=f"reopen_{rid}", use_container_width=True):
                            if reopen_row(rid):
                                clear_notif_cache()
                                st.rerun()
                else:
                    with rcols[5]:
                        if st.button("✅ Close", key=f"close_{rid}", use_container_width=True):
                            if close_row(rid):
                                clear_notif_cache()
                                st.rerun()

else:
    # ==============================================================
    # RFAI NOTIFICATION TAB
    # ==============================================================
    sync_rfai_cached(workspace)  # keeps rfai_notifications fresh (cached ~20s)
    open_rfai_preview = fetch_rfai_cached(workspace, False)
    closed_rfai_preview = fetch_rfai_cached(workspace, True)
    open_rfai_count = len(open_rfai_preview)
    closed_rfai_count = len(closed_rfai_preview)

    col_title, col_tabs, col_ref = st.columns([2, 3, 1])
    with col_title:
        st.markdown("<h2 style='margin:0; color:#0f172a;'>📋 Notifications</h2>", unsafe_allow_html=True)
    with col_tabs:
        with st.container(key="rfai_tab_nav_bar"):
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

    st.caption(
        "Tracked RFAI statuses: " + ", ".join(RFAI_TARGET_STATUSES)
    )
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
            col_ratios = [0.5, 1.6, 1.2, 1.6, 1.8, 1.6, 1.2]
            col_labels = ["#", "PROJECT ID", "SITE ID", "SITE NAME", "RFAI STATUS", "CLOSED AT", "ACTION"]
        else:
            col_ratios = [0.5, 1.6, 1.2, 1.6, 1.8, 1.2]
            col_labels = ["#", "PROJECT ID", "SITE ID", "SITE NAME", "RFAI STATUS", "ACTION"]

        with st.container(key="notif_table_wrap", height=520):
            h_cols = st.columns(col_ratios)
            for h_col, label in zip(h_cols, col_labels):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for pos, row in enumerate(rfai_rows):
                rid = row.get("id")
                rcols = st.columns(col_ratios)
                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)
                rcols[1].markdown(f"<div class='tbl-cell'>{row.get('project_id', '-')}</div>", unsafe_allow_html=True)
                rcols[2].markdown(f"<div class='tbl-cell'>{row.get('site_id', '-')}</div>", unsafe_allow_html=True)
                rcols[3].markdown(f"<div class='tbl-cell'>{row.get('site_name', '-')}</div>", unsafe_allow_html=True)
                rcols[4].markdown(status_badge(row.get('rfai_status', '-')), unsafe_allow_html=True)

                if is_rfai_closed_tab:
                    closed_at = row.get("closed_at", "-")
                    closed_at_display = str(closed_at)[:19].replace("T", " ") if closed_at else "-"
                    rcols[5].markdown(f"<div class='tbl-cell'>{closed_at_display}</div>", unsafe_allow_html=True)
                    with rcols[6]:
                        if st.button("↩️ Reopen", key=f"rfai_reopen_{rid}", use_container_width=True):
                            if reopen_rfai_row(rid):
                                clear_rfai_cache()
                                st.rerun()
                else:
                    with rcols[5]:
                        if st.button("✅ Close", key=f"rfai_close_{rid}", use_container_width=True):
                            if close_rfai_row(rid):
                                clear_rfai_cache()
                                st.rerun()
