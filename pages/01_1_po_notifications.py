"""
================================================================================
 VISIONTECH INFRA SOLUTION PVT. LTD.
 PO NOTIFICATION  —  Streamlit page
 --------------------------------------------------------------------------
 Reads/writes the Supabase table `po_notifications` (see
 supabase_po_notifications.sql). Data lands in that table from the desktop
 "PO & WCC Upload Software" app's new Notification tab (Rev Number > 0
 POs, last 1 month).

 Flow:
   - User picks their Workspace (VISPL / BHAGYASHREE) from the sidebar —
     no login/password. Data shown is always filtered by that workspace's
     `workspace` column, so each company only sees its own rows.
   - Main page = "Open" view: every revised PO not yet closed. Each row has
     a "✅ Close" button — clicking it marks that row is_closed = True and
     it disappears from this page (moves to the Closed page).
   - "Closed" page = history of everything you've already closed, with a
     "↩️ Reopen" button in case something was closed by mistake.
   - Next time the desktop app finds a NEW revision for a PO you already
     closed, that new revision inserts as a brand-new (open) row — so it
     will show up here again, while your closed record for the old
     revision stays in the Closed page untouched.
================================================================================
"""

import os
import streamlit as st
from datetime import datetime, timezone
from supabase import create_client, Client

# ==============================================================================
# CONFIG
# ==============================================================================
# 🟢 Key ab yaha hardcoded NAHI hai. Ye st.secrets se aati hai, isi format me
# jo already aapke doosre Streamlit pages (share.streamlit.io) me use ho raha
# hai:
#
#     [supabase]
#     url = "https://jddnuekuhjhoenmggmdj.supabase.co"
#     key = "yaha apni ABHI VALID wali secret/service_role key"
#
# Agar ye page usi existing Streamlit Cloud app me add ho raha hai jaha ye
# secrets pehle se saved hain, to kuch bhi naya banane ki zaroorat nahi.
# Local testing ke liye, apne is app ke folder me .streamlit/secrets.toml
# banao aur upar wala [supabase] block usme paste kar do.
_supabase_secrets = st.secrets.get("supabase", {})
SUPABASE_URL = _supabase_secrets.get("url") or st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
SUPABASE_KEY = _supabase_secrets.get("key") or st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))

WORKSPACES = ["VISPL", "BHAGYASHREE"]

TABLE_NAME = "po_notifications"

st.set_page_config(page_title="PO Notification - Visiontech", page_icon="🔔", layout="wide")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "❌ Supabase URL/Key configure nahi hai.\n\n"
        "Is app ke folder me `.streamlit/secrets.toml` banao aur usme "
        "SUPABASE_URL aur SUPABASE_KEY daalo (file ke top comment me exact "
        "format diya hai)."
    )
    st.stop()


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()


# ==============================================================================
# SIDEBAR STYLE  (rounded card-style nav buttons, matches the rest of the app)
# ==============================================================================
SIDEBAR_NAV_CSS = """
<style>
section[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    text-align: left;
    background-color: #1b1d2e;
    color: #d6d6e0;
    border: 1px solid #2a2d40;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-weight: 600;
    font-size: 15px;
    box-shadow: none;
    transition: all 0.15s ease-in-out;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #262a40;
    color: #ffffff;
    border-color: #3b3f58;
}
section[data-testid="stSidebar"] div.stButton > button:focus:not(:active) {
    color: inherit;
}
</style>
"""

ACTIVE_NAV_CSS_TEMPLATE = """
<style>
section[data-testid="stSidebar"] div.stButton:nth-of-type({idx}) > button {{
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    color: #ffffff !important;
    border: none;
}}
section[data-testid="stSidebar"] div.stButton:nth-of-type({idx}) > button:hover {{
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    color: #ffffff !important;
}}
</style>
"""


def get_count(workspace, is_closed):
    try:
        res = (
            supabase.table(TABLE_NAME)
            .select("id", count="exact")
            .eq("workspace", workspace)
            .eq("is_closed", is_closed)
            .execute()
        )
        return res.count or 0
    except Exception:
        return 0


def render_sidebar():
    st.sidebar.markdown("### 🏢 Workspace")
    workspace = st.sidebar.selectbox("Select Workspace", WORKSPACES, label_visibility="collapsed")
    st.sidebar.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)

    open_count = get_count(workspace, is_closed=False)
    closed_count = get_count(workspace, is_closed=True)

    st.session_state.setdefault("nav_page", "open")

    st.markdown(SIDEBAR_NAV_CSS, unsafe_allow_html=True)

    if st.sidebar.button(f"🔔  {open_count} Open Notification{'s' if open_count != 1 else ''}",
                          use_container_width=True, key="nav_open_btn"):
        st.session_state["nav_page"] = "open"
        st.rerun()

    if st.sidebar.button(f"✅  {closed_count} Closed", use_container_width=True, key="nav_closed_btn"):
        st.session_state["nav_page"] = "closed"
        st.rerun()

    active_idx = 1 if st.session_state["nav_page"] == "open" else 2
    st.markdown(ACTIVE_NAV_CSS_TEMPLATE.format(idx=active_idx), unsafe_allow_html=True)

    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    page = "🔔 Open Notifications" if st.session_state["nav_page"] == "open" else "✅ Closed"
    return workspace, page


# ==============================================================================
# DATA HELPERS
# ==============================================================================
def fetch_rows(workspace, is_closed):
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
    except Exception as e:
        st.error(f"❌ Supabase se data fetch karne me error: {e}")
        return []


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


# ==============================================================================
# RENDER: OPEN NOTIFICATIONS PAGE
# ==============================================================================
def render_open_page(workspace):
    st.title("🔔 PO Notification — Open")
    st.caption(f"Workspace: **{workspace}**  •  Revised PO's (Rev Number > 0) jinhe abhi close nahi kiya gaya.")

    rows = fetch_rows(workspace, is_closed=False)

    if not rows:
        st.info("✅ Koi open notification nahi hai. Sab clear hai!")
        return

    st.write(f"**{len(rows)} open notification(s)**")

    header = st.columns([2, 1.2, 1.5, 1.5, 1.2])
    for col, label in zip(header, ["PO Number", "Rev Number", "PO Amount", "PO Status", "Action"]):
        col.markdown(f"**{label}**")
    st.divider()

    for row in rows:
        c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1.5, 1.5, 1.2])
        c1.write(row.get("po_number", "-"))
        c2.write(row.get("rev_number", "-"))
        c3.write(row.get("amount", "-"))
        c4.write(row.get("po_status", "-"))
        if c5.button("✅ Close", key=f"close_{row['id']}", use_container_width=True):
            if close_row(row["id"]):
                st.rerun()


# ==============================================================================
# RENDER: CLOSED PAGE (history)
# ==============================================================================
def render_closed_page(workspace):
    st.title("✅ PO Notification — Closed")
    st.caption(f"Workspace: **{workspace}**  •  Jo notifications close kar di gayi hain (history).")

    rows = fetch_rows(workspace, is_closed=True)

    if not rows:
        st.info("Abhi tak kuch close nahi kiya gaya.")
        return

    st.write(f"**{len(rows)} closed notification(s)**")

    header = st.columns([2, 1.2, 1.5, 1.5, 1.8, 1.2])
    for col, label in zip(header, ["PO Number", "Rev Number", "PO Amount", "PO Status", "Closed At", "Action"]):
        col.markdown(f"**{label}**")
    st.divider()

    for row in rows:
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.2, 1.5, 1.5, 1.8, 1.2])
        c1.write(row.get("po_number", "-"))
        c2.write(row.get("rev_number", "-"))
        c3.write(row.get("amount", "-"))
        c4.write(row.get("po_status", "-"))
        closed_at = row.get("closed_at", "-")
        c5.write(str(closed_at)[:19].replace("T", " ") if closed_at else "-")
        if c6.button("↩️ Reopen", key=f"reopen_{row['id']}", use_container_width=True):
            if reopen_row(row["id"]):
                st.rerun()


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    workspace, page = render_sidebar()

    if page == "🔔 Open Notifications":
        render_open_page(workspace)
    else:
        render_closed_page(workspace)


if __name__ == "__main__":
    main()
