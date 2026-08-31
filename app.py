import streamlit as st
import streamlit.components.v1 as components
import json

# --- EXISTING CODE (100% UNTOUCHED) ---
st.set_page_config(
    page_title="Visiontech CRM | Home",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================
# --- NEW REQUIREMENT: SEPARATE BHAJAN LOGIN ---
# ==============================================================
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'CRM'

with st.sidebar:
    if st.session_state.get('user_role') == 'BHAJAN':
        st.success("🪔 Bhajan Login Active")
        if st.button("🚪 Bhajan Logout", key="bhajan_logout_home", use_container_width=True):
            st.session_state['user_role'] = 'CRM'
            st.rerun()
    else:
        with st.expander("🪔 Bhajan Login"):
            with st.form("bhajan_login_form"):
                bhajan_username = st.text_input("Username", key="bhajan_login_username")
                bhajan_password = st.text_input("Password", type="password", key="bhajan_login_password")
                bhajan_submit = st.form_submit_button("Login", use_container_width=True)

            if bhajan_submit:
                try:
                    correct_username = str(st.secrets["bhajan_login"]["username"])
                    correct_password = str(st.secrets["bhajan_login"]["password"])

                    if bhajan_username.strip() == correct_username and bhajan_password == correct_password:
                        st.session_state['user_role'] = 'BHAJAN'
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Username ya Password galat hai.")
                except Exception as e:
                    st.error(f"🚨 Bhajan login configuration error: {e}")

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
    # FIX: Session idle/websocket-reconnect hone par st.session_state reset ho jaata hai,
    # isliye pehle URL query_params me saved workspace check karte hain (ye reset nahi hota).
    _valid_workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA", "SAI TELE SERVICES"]
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
    workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA", "SAI TELE SERVICES"]
    current_index = workspaces.index(st.session_state['active_workspace'])
    
    selected_workspace = st.selectbox(
        "Active Workspace Select Karein:", 
        workspaces, 
        index=current_index,
        key="workspace_selector"
    )
    
    if selected_workspace != st.session_state['active_workspace']:
        st.session_state['active_workspace'] = selected_workspace
        st.query_params['workspace'] = selected_workspace  # FIX: URL me bhi persist karo
        st.rerun()

    # FIX: Agar URL me query param abhi tak set nahi hai (pehli baar load), to sync kar do
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


# ==============================================================
# --- NEW REQUIREMENT: WORKSPACE-BASED SIDEBAR PAGE FILTER ---
# ==============================================================
# Rajkumar Kalya login me sirf ye 2 page dikhne chahiye:
#   1. Marketing
#   2. Rajkumar Contact
# Baaki sab workspaces (VISPL, Bhagyashree, Sai Tele Services) me
# ye 2 page CHHOD KAR baaki sab pages dikhne chahiye.
#
# IMPORTANT: Neeche list me EXACT wahi naam daalein jo aapke
# "pages/" folder ki files se sidebar me dikh rahe hain
# (numbers "1_", "2_" aur underscores hat jaate hain, emoji/icon
# alag se render hota hai — sirf text label match karna hai).
# Agar aapke actual sidebar labels different hain to yahan update kar dein.

RAJKUMAR_PAGES = ["Marketing", "Rajkumar Contact"]
BHAJAN_PAGES = ["Bhajan"]

_active_ws = st.session_state['active_workspace']

if st.session_state.get('user_role') == "BHAJAN":
    _allowed_pages = BHAJAN_PAGES
    _mode = "whitelist"       # Bhajan login me sirf Bhajan page dikhega
elif _active_ws == "RAJKUMAR KALYA":
    _allowed_pages = RAJKUMAR_PAGES
    _mode = "whitelist"       # sirf RAJKUMAR_PAGES dikhenge
else:
    _allowed_pages = RAJKUMAR_PAGES + BHAJAN_PAGES
    _mode = "blacklist"       # Rajkumar aur Bhajan pages chhod kar baaki sab dikhenge

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

// Fallback: Streamlit kabhi kabhi nav ko re-render karta hai bina mutation trigger kiye
setInterval(filterSidebarNav, 400);
</script>
""", height=0)
