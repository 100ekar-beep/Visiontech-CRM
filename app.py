import streamlit as st
import streamlit.components.v1 as components
import json

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
    # FIX: Session idle/websocket-reconnect hone par st.session_state reset ho jaata hai,
    # isliye pehle URL query_params me saved workspace check karte hain (ye reset nahi hota).
    _valid_workspaces = ["VISPL", "BHAGYASHREE", "RAJKUMAR KALYA", "SAI TELE SERVICES", "BHAJAN"]
    _query_workspace = st.query_params.get('workspace', None)
    if _query_workspace in _valid_workspaces:
        st.session_state['active_workspace'] = _query_workspace
    else:
        st.session_state['active_workspace'] = 'VISPL'  # Default Open

# --- MASTER WORKSPACE SELECTOR ---
st.markdown("<h2>🏢 Master Workspace Controller</h2>", unsafe_allow_html=True)
st.markdown("---")
