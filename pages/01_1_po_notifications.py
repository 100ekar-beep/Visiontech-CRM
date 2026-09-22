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

import streamlit as st
from datetime import datetime, timezone
from supabase import create_client, Client

# ==============================================================================
# CONFIG  -- apni details yaha edit karo
# ==============================================================================
# 🟢 Same Supabase project the desktop app uses. For production, move these
# into .streamlit/secrets.toml and read via st.secrets["SUPABASE_URL"] etc.
SUPABASE_URL = "https://jddnuekuhjhoenmggmdj.supabase.co"
SUPABASE_KEY = "sb_secret_mY2J2QcZEcGAMIy5PTIjsg_8V2Sl0jO"

WORKSPACES = ["VISPL", "BHAGYASHREE"]

TABLE_NAME = "po_notifications"

st.set_page_config(page_title="PO Notification - Visiontech", page_icon="🔔", layout="wide")


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()


# ==============================================================================
# SIDEBAR (workspace selector — no password/login)
# ==============================================================================
def render_sidebar():
    st.sidebar.markdown("### 🏢 Workspace")
    workspace = st.sidebar.selectbox("Select Workspace", WORKSPACES, label_visibility="collapsed")
    st.sidebar.divider()
    page = st.sidebar.radio("📄 Page", ["🔔 Open Notifications", "✅ Closed"], index=0)
    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh", use_container_width=True):
        st.rerun()
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
