import streamlit as st


st.set_page_config(page_title="PO Notifications", page_icon="🔔", layout="wide")

if not st.session_state.get("logged_in", False):
    st.error("Please login from the main page.")
    st.stop()

workspace = st.session_state.get(
    "notification_workspace",
    st.session_state.get("active_workspace", "VISPL"),
)
company = st.session_state.get(
    "notification_company",
    st.session_state.get("site_active_company", "VISPL"),
)

if workspace not in ("VISPL", "BHAGYASHREE"):
    st.info("Notifications abhi Sai Tele ke liye configured nahi hain.")
    if st.button("⬅️ Back to Site Data", use_container_width=True):
        st.switch_page("pages/01_🏗️_Site_Data.py")
    st.stop()

left, right = st.columns([5, 1])
with left:
    st.title(f"🔔 {company} — PO Notifications")
with right:
    if st.button("⬅️ Site Data", use_container_width=True):
        st.switch_page("pages/01_🏗️_Site_Data.py")

st.info("Notification list aur Oracle revision scanner agle module mein yahan connect honge.")
