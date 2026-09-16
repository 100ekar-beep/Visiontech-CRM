from datetime import datetime, timezone

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="PO Notifications", page_icon="🔔", layout="wide")

workspace = st.session_state.get("notification_workspace", st.session_state.get("active_workspace", "VISPL"))
company = st.session_state.get("notification_company", st.session_state.get("site_active_company", "VISPL"))

if workspace not in ("VISPL", "BHAGYASHREE"):
    st.info("Notifications abhi Sai Tele ke liye configured nahi hain.")
    if st.button("⬅️ Back to Site Data", use_container_width=True):
        st.switch_page("pages/01_🏗️_Site_Data.py")
    st.stop()

@st.cache_resource
def get_supabase():
    # Normalize accidental spaces/newlines copied into Streamlit Secrets.
    url = "".join(str(st.secrets["supabase"]["url"]).split())
    key = "".join(str(st.secrets["supabase"]["key"]).split())
    if not url.startswith(("https://", "http://")):
        raise ValueError("Supabase URL must start with https://")
    return create_client(url, key)

try:
    supabase = get_supabase()
except Exception as exc:
    st.error(f"Supabase connection initialize nahi hua: {exc}")
    st.info("Streamlit Cloud → Manage app → Settings → Secrets check karke app reboot karein.")
    st.stop()

st.markdown(f"""
<div style="background:linear-gradient(90deg,#2563eb,#7c3aed,#db2777);padding:20px;
border-radius:14px;color:white;margin-bottom:20px">
<h1 style="margin:0;color:white">🔔 {company} — PO Notifications</h1>
<p style="margin:6px 0 0;color:white">Revised Purchase Orders</p></div>
""", unsafe_allow_html=True)

back_col, check_col, refresh_col = st.columns([1.1, 2.2, 1.1])
with back_col:
    if st.button("⬅️ Site Data", use_container_width=True):
        st.switch_page("pages/01_🏗️_Site_Data.py")
with check_col:
    if st.button("🔄 Check Revised PO Now", type="primary", use_container_width=True):
        try:
            active = (supabase.table("po_revision_scan_requests").select("id,status")
                      .eq("workspace", workspace).in_("status", ["pending", "running"])
                      .limit(1).execute())
            if active.data:
                st.warning("Is company ka Oracle check already pending/running hai.")
            else:
                supabase.table("po_revision_scan_requests").insert({
                    "workspace": workspace,
                    "status": "pending",
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                    "request_source": "manual",
                }).execute()
                st.success("Oracle check request bhej di gayi hai. Windows worker ise process karega.")
                st.rerun()
        except Exception as exc:
            st.error(f"Scan request create nahi hui: {exc}")
with refresh_col:
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()

try:
    latest = (supabase.table("po_revision_scan_requests")
              .select("status,requested_at,new_notifications,error_message")
              .eq("workspace", workspace).order("requested_at", desc=True).limit(1).execute())
    if latest.data:
        scan = latest.data[0]
        labels = {"pending": "⏳ Waiting for Windows worker", "running": "🌐 Oracle check running",
                  "completed": "✅ Check completed", "failed": "❌ Check failed"}
        st.caption(f"Latest scan: {labels.get(scan.get('status'), scan.get('status'))} | "
                   f"Requested: {scan.get('requested_at', '-')} | "
                   f"New notifications: {scan.get('new_notifications') or 0}")
        if scan.get("error_message"):
            st.error(scan["error_message"])
except Exception as exc:
    st.warning(f"Scan status load nahi hua: {exc}")

try:
    result = (supabase.table("po_revision_notifications")
              .select("id,po_number,revision_number,description,order_date,is_read,discovered_at")
              .eq("workspace", workspace).order("discovered_at", desc=True).execute())
    notifications = result.data or []
except Exception as exc:
    notifications = []
    st.error(f"Notifications load nahi hui: {exc}")

unread_count = sum(not x.get("is_read", False) for x in notifications)
m1, m2 = st.columns(2)
m1.metric("Total Notifications", len(notifications))
m2.metric("Unread", unread_count)
st.markdown("### Revised PO List")
if not notifications:
    st.info("Abhi koi revised PO notification nahi hai.")

for item in notifications:
    is_read = bool(item.get("is_read"))
    bg, fg = ("#eff6ff", "#0f172a") if is_read else ("#1d4ed8", "#ffffff")
    card_col, action_col = st.columns([5, 1])
    with card_col:
        st.markdown(f"""
        <div style="background:{bg};color:{fg};padding:16px;border-radius:12px;margin-bottom:8px">
        <div style="font-size:18px;font-weight:800">PO {item.get('po_number', '-')} | Rev {item.get('revision_number', '-')}</div>
        <div style="margin-top:6px">{item.get('description') or '-'}</div>
        <div style="margin-top:6px;font-size:13px">Order Date: {item.get('order_date') or '-'}</div></div>
        """, unsafe_allow_html=True)
    with action_col:
        if is_read:
            st.button("✓ Read", key=f"read_{item['id']}", disabled=True, use_container_width=True)
        elif st.button("Mark Read", key=f"read_{item['id']}", type="primary", use_container_width=True):
            try:
                supabase.table("po_revision_notifications").update({
                    "is_read": True, "read_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", item["id"]).execute()
                st.rerun()
            except Exception as exc:
                st.error(f"Read status update nahi hua: {exc}")
