import streamlit as st
import streamlit.components.v1 as components
import json
import bcrypt
from supabase import create_client, Client

# ==============================================================
# --- LOGIN SYSTEM (mobile number + password) ---
# ==============================================================
st.set_page_config(
    page_title="Visiontech CRM | Home",
    page_icon="⚡",
    layout="wide"
)

@st.cache_resource
def init_login_connection():
    url = st.secrets["supabase"]["url"].rstrip("/")
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase_login: Client = init_login_connection()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("""
        <div style="max-width: 420px; margin: 80px auto; padding: 2.5rem; 
                    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); 
                    border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h2 style="color:white; text-align:center; margin-bottom: 5px;">⚡ Visiontech CRM</h2>
            <p style="color:#94a3b8; text-align:center; margin-bottom: 25px;">Login to continue</p>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        mobile_input = st.text_input("📱 Mobile Number", placeholder="10 digit mobile number")
        password_input = st.text_input("🔒 Password", type="password")
        login_btn = st.button("Login", type="primary", use_container_width=True)

        if login_btn:
            if not mobile_input or not password_input:
                st.error("⚠️ Mobile number aur password dono bharo")
            else:
                try:
                    res = supabase_login.table("app_users").select("*").eq("mobile_number", mobile_input.strip()).execute()
                    if not res.data:
                        st.error("❌ Ye mobile number registered nahi hai")
                    else:
                        user = res.data[0]
                        stored_hash = user.get("password_hash", "").encode('utf-8')
                        if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                            st.session_state['logged_in'] = True
                            st.session_state['is_admin'] = user.get('is_admin', False)
                            st.session_state['allowed_pages'] = user.get('allowed_pages', [])
                            st.session_state['full_name'] = user.get('full_name', '')
                            st.session_state['user_mobile'] = mobile_input.strip()
                            st.rerun()
                        else:
                            st.error("❌ Password galat hai")
                except Exception as e:
                    st.error(f"❌ Login Error: {e}")
    st.stop()

# --- LOGOUT BUTTON (sidebar mein) ---
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('full_name', 'User')}**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ['logged_in', 'is_admin', 'allowed_pages', 'full_name', 'user_mobile']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ==============================================================
# --- YAHAN SE AAPKA PURANA EXISTING CODE START HOTA HAI (waisa hi rehne do) ---
# ==============================================================
