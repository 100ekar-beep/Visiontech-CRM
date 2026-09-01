import streamlit as st
import streamlit.components.v1 as components
import json
import bcrypt
from supabase import create_client, Client

# ==============================================================
# --- PAGE CONFIG (sirf ek hi baar, sabse upar) ---
# ==============================================================
st.set_page_config(
    page_title="Visiontech CRM | Home",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================
# --- SUPABASE CONNECTION (login ke liye) ---
# ==============================================================
@st.cache_resource
def init_login_connection():
    url = st.secrets["supabase"]["url"]
    url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    key = st.secrets["supabase"]["key"]
    st.write("DEBUG URL:", url)   # <-- TEMPORARY DEBUG LINE
    return create_client(url, key)

supabase_login: Client = init_login_connection()

# ==============================================================
# --- LOGIN SYSTEM (mobile number + password) ---
# ==============================================================
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

# --- LOGOUT BUTTON (sidebar mein, login ke baad hamesha dikhega) ---
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('full_name', 'User')}**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ['logged_in', 'is_admin', 'allowed_pages', 'full_name', 'user_mobile']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.markdown("---")

# ==============================================================
# --- EXISTING CODE (100% UNTOUCHED) ---
# ==============================================================
st.markdown("""
    <div style="padding: 2.5rem; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); border-radius: 16px; text-align: center; color: white;">
        <h1>⚡ Visiontech CRM⚡</h1>
        <p style="font-size: 1.1rem; margin-top: 10px;">Select a page from the sidebar to manage your workflows & database.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.success("✅ Multi-page mode active hai! Left sidebar se koi bhi page select karein.")


# ==============================================================
# --- NEW REQUIREMENT: MASTER WORKSPACE CONTROLLER & UI CSS ---
# ==============================================================

st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }
    
    /* PREMIUM SIDEBAR */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }
    
    /* Dropdown styling */
    div[data-baseweb="select"] * { font-weight: 800 !important; }
    
    /* Dashboard Cards */
    .dash-card { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: white; border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; margin-top: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); border-left: 5px solid #3b82f6;}
    .dash-card h2, .dash-card p { color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'active_workspace' not in st.session_state:
    _valid_workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA", "SAI TELE SERVICES", "BHAJAN"]
    _query_workspace = st.query_params.get('workspace', None)
    if _query_workspace in _valid_workspaces:
        st.session_state['active_workspace'] = _query_workspace
    else:
        st.session_state['active_workspace'] = 'VISPL'  # Default Open

# --- MASTER WORKSPACE SELECTOR ---
st.markdown("<h2>🏢 Master Workspace Controller</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([3, 7])
with col1:
    workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA", "SAI TELE SERVICES", "BHAJAN"]
    current_index = workspaces.index(st.session_state['active_workspace'])
    
    selected_workspace = st.selectbox(
        "Active Workspace Select Karein:", 
        workspaces, 
        index=current_index,
        key="workspace_selector"
    )
    
    if selected_workspace != st.session_state['active_workspace']:
        st.session_state['active_workspace'] = selected_workspace
        st.query_params['workspace'] = selected_workspace
        st.rerun()

    if st.query_params.get('workspace', None) != st.session_state['active_workspace']:
        st.query_params['workspace'] = st.session_state['active_workspace']

# --- DYNAMIC DASHBOARD DISPLAY ---
with col2:
    if st.session_state['active_workspace'] == 'RAJKUMAR KALYA':
        st.markdown("""
        <div class="dash-card">
            <h2>📱 Personal Marketing Zone</h2>
            <p>Welcome! Ye aapka personal aur fully isolated workspace hai. Yahan se aap apne WhatsApp campaigns aur Interakt templates manage kar sakte hain.</p>
            <p style="color: #38bdf8 !important;">👈 Kripya sidebar se <b>Marketing</b> ya <b>Template Registration</b> select karein.</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state['active_workspace'] == 'VISPL':
        st.markdown("""
        <div class="dash-card">
            <h2>🚀 VISPL Enterprise Operations</h2>
            <p>Welcome to VISPL Workspace! Yahan aap apne saare bills, quotations, POs aur site data ko securely manage kar sakte hain. Data completely isolated hai.</p>
            <p style="color: #38bdf8 !important;">👈 Kripya sidebar se apne desired business modules select karein.</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state['active_workspace'] == 'BHAGYASHREE':
        st.markdown("""
        <div class="dash-card">
            <h2>🏗️ BHAGYASHREE Management</h2>
            <p>Welcome to Bhagyashree Workspace! Yahan aapki property aur construction ventures ka saara record secure aur isolated rakha gaya hai.</p>
            <p style="color: #38bdf8 !important;">👈 Kripya sidebar se apne desired business modules select karein.</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state['active_workspace'] == 'SAI TELE SERVICES':
        st.markdown("""
        <div class="dash-card">
            <h2>📡 SAI TELE SERVICES Operations</h2>
            <p>Welcome to Sai Tele Services Workspace! Yahan aap apne saare bills, quotations, POs aur service data ko securely manage kar sakte hain. Data completely isolated hai.</p>
            <p style="color: #38bdf8 !important;">👈 Kripya sidebar se apne desired business modules select karein.</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state['active_workspace'] == 'BHAJAN':
        st.markdown("""
        <div class="dash-card">
            <h2>🪔 BHAJAN SANGRAH</h2>
            <p>Welcome to Bhajan Workspace! Yahan aap category-wise bhajan save, search, PDF download aur WhatsApp share kar sakte hain.</p>
            <p style="color: #38bdf8 !important;">👈 Kripya sidebar se <b>Bhajan</b> page select karke login karein.</p>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================
# --- SIDEBAR PAGE FILTER (LOGIN-BASED, PRIORITY) ---
# ==============================================================
is_admin_user = st.session_state.get('is_admin', False)

if is_admin_user:
    RAJKUMAR_PAGES = ["Marketing", "Rajkumar Contact"]
    BHAJAN_PAGES = ["Bhajan"]
    _active_ws = st.session_state['active_workspace']

    if _active_ws == "BHAJAN":
        _allowed_pages = BHAJAN_PAGES
        _mode = "whitelist"
    elif _active_ws == "RAJKUMAR KALYA":
        _allowed_pages = RAJKUMAR_PAGES
        _mode = "whitelist"
    else:
        _allowed_pages = RAJKUMAR_PAGES + BHAJAN_PAGES
        _mode = "blacklist"
else:
    _allowed_pages = st.session_state.get('allowed_pages', [])
    _mode = "whitelist"

components.html(f"""
<script>
const allowedPages = {json.dumps(_allowed_pages)};
const mode = "{_mode}";

function filterSidebarNav() {{
    const navLinks = window.parent.document.querySelectorAll('[data-testid="stSidebarNav"] a');
    navLinks.forEach(function(link) {{
        const span = link.querySelector('span');
        const label = (span ? span.textContent : link.textContent).trim();
        let hide = false;
        if (mode === "whitelist") {{
            hide = !allowedPages.includes(label);
        }} else {{
            hide = allowedPages.includes(label);
        }}
        link.style.display = hide ? "none" : "flex";
    }});
}}

filterSidebarNav();

const navContainer = window.parent.document.querySelector('[data-testid="stSidebarNav"]');
if (navContainer) {{
    const observer = new MutationObserver(filterSidebarNav);
    observer.observe(navContainer, {{ childList: true, subtree: true }});
}}

setInterval(filterSidebarNav, 400);
</script>
""", height=0)
