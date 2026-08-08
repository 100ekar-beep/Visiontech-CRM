import streamlit as st

# --- EXISTING CODE (100% UNTOUCHED) ---
st.set_page_config(
    page_title="Visiontech CRM | Home",
    page_icon="⚡",
    layout="wide"
)

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
    st.session_state['active_workspace'] = 'VISPL'  # Default Open

# --- MASTER WORKSPACE SELECTOR ---
st.markdown("<h2>🏢 Master Workspace Controller</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([3, 7])
with col1:
    workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA"]
    current_index = workspaces.index(st.session_state['active_workspace'])
    
    selected_workspace = st.selectbox(
        "Active Workspace Select Karein:", 
        workspaces, 
        index=current_index,
        key="workspace_selector"
    )
    
    if selected_workspace != st.session_state['active_workspace']:
        st.session_state['active_workspace'] = selected_workspace
        st.rerun()

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
