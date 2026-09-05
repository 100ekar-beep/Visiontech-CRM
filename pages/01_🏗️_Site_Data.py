import streamlit as st
import pandas as pd
import math
import io
import smtplib  # <--- NEW: For Email Sending
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from st_keyup import st_keyup # <--- NEW: For Live Search without Enter
from datetime import datetime, timedelta # <--- Added for parsing existing date strings

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Site Data Hub", page_icon="🏗️", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'po_count' not in st.session_state:
    st.session_state.po_count = 1

if 'mat_count' not in st.session_state:
    st.session_state.mat_count = 1

if 'add_mat_count' not in st.session_state:
    st.session_state.add_mat_count = 1

if 'pending_comm_email' not in st.session_state:
    st.session_state.pending_comm_email = False
if 'comm_site_data' not in st.session_state:
    st.session_state.comm_site_data = {}

if 'site_view_mode' not in st.session_state:
    st.session_state.site_view_mode = "table"

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Top Action Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Pagination Text & Button Font Color Fix */
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    
    div.stButton > button p, 
    div.stButton > button span, 
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    
    /* FIX FOR DIALOG TITLE AND CAPTION COLOR */
    div[data-testid="stDialog"] h1, 
    div[data-testid="stDialog"] h2, 
    div[data-testid="stDialog"] h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
    div[data-testid="stDialog"] p {
        color: #e2e8f0 !important; 
    }
    div[data-testid="stDialog"] button[kind="icon"] svg {
        fill: #ffffff !important; 
    }

    .modal-section-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
    }
    
    /* FIX FOR FIELD LABELS COLOR (Make them bright white) */
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* Make disabled/read-only input text inside Warehouse Site Info strictly BLACK and BOLD */
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important;
        font-weight: 700 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Individual Sidebar Links / Buttons */
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

    /* Hover Effect for Sidebar Links */
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }

    /* Active/Selected Page Button */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Clean up the default Streamlit styling overrides */
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* =========================================================
       FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING
       ========================================================= */
    .st-key-site_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important; /* Enables both Horizontal & Vertical Scroll */
        padding: 0px 0 !important;
    }
    /* Force inner rows to be extremely wide so they NEVER squish or overlap */
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 4600px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    /* Cell padding and border */
    .st-key-site_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; /* Increased padding for proper spacing */
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-site_table_wrap div[data-testid="column"]:last-child {
        border-right: none;
    }
    
    .st-key-site_table_wrap .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    /* Strict nowrap with ellipsis to prevent column bleeding */
    .st-key-site_table_wrap .tbl-cell {
        color: #e2e8f0;
        font-size: 0.86rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    .st-key-site_table_wrap .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    /* Fixed native Action Buttons strictly constrained to their columns */
    .st-key-site_table_wrap button {
        height: 32px !important;
        width: 100% !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important;
        pointer-events: auto !important; /* Force clickability */
        cursor: pointer !important;
    }
    .st-key-site_table_wrap button:hover {
        background: #3b82f6 !important;
        border-color: #60a5fa !important;
        transform: translateY(-2px) !important;
    }

    /* -------------------------------------------------------------
       FORCE LEFT BUTTON CSS: Action Columns (2 = Manage, 3 = Material)
       ------------------------------------------------------------- */
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(1) {
        padding: 0 10px 0 15px !important;
    }
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(2) .tbl-head,
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(3) .tbl-head {
        color: #94a3b8; 
    }
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(2) {
        padding: 4px 4px !important;
        border-right: none !important;
    }
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(3) {
        padding: 4px 15px 4px 4px !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* Round, color-coded, compact action icon buttons */
    .st-key-site_table_wrap div[class*="st-key-mgrbtn_"] button,
    .st-key-site_table_wrap div[class*="st-key-mbtn_"] button {
        width: 100% !important; 
        max-width: 34px !important;
        height: 32px !important;
        padding: 0 !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
        margin: 0 auto !important;
    }
    div[class*="st-key-mgrbtn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    div[class*="st-key-mbtn_"] button { background: rgba(168,85,247,0.15) !important; border: 1px solid rgba(168,85,247,0.3) !important; }
    
    /* Status badge pill */
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
    .status-green  { background: rgba(34,197,94,0.18);  color: #4ade80; }
    .status-blue   { background: rgba(59,130,246,0.18); color: #60a5fa; }
    .status-yellow { background: rgba(234,179,8,0.18);  color: #facc15; }
    .status-red    { background: rgba(239,68,68,0.18);  color: #f87171; }
    .status-grey   { background: rgba(148,163,184,0.15); color: #94a3b8; }

    /* =========================================================
       MOBILE-FRIENDLY CARD VIEW
       ========================================================= */
    .site-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .site-card-title { font-size: 1.05rem; font-weight: 800; color: #ffffff; margin-bottom: 2px; }
    .site-card-sub { font-size: 0.82rem; color: #94a3b8; margin-bottom: 10px; }
    .site-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed rgba(255,255,255,0.06); font-size: 0.85rem; }
    .site-card-row:last-child { border-bottom: none; }
    .site-card-label { color: #94a3b8; font-weight: 600; }
    .site-card-value { color: #e2e8f0; font-weight: 600; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

# --- 3. SUPABASE CONNECTION ---
# FIX: Ab hardcoded URL/Key ki jagah st.secrets se liya jaa raha hai — isse
# ek hi jagah (Streamlit Cloud Secrets) update karke sabhi pages naye
# Supabase project se automatically connect ho jaate hain, har page ki
# code alag se badalne ki zaroorat nahi padti.
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        # Agar secrets me galti se '/rest/v1' ya trailing slash aa gaya ho, use clean kar dete hain
        url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase connection error: {e}")
        return None

supabase: Client = init_connection()

# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: CACHED DATA FETCHERS ---
# Without this, every keystroke in search / every rerun re-downloads the
# whole table from Supabase, which is what was eating up the free-tier
# egress quota. These cache results for a short time (30s) so repeated
# reruns (typing in search, opening dialogs, pagination) reuse the same
# data instead of hitting Supabase again. Call .clear() right before any
# insert/update/delete so the next read is fresh, not stale.
# -------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_site_data_cached(workspace):
    try:
        response = supabase.table("site_data").select("*").eq("workspace", workspace).execute()
        return response.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_po_upload_identifiers_cached(workspace):
    """Returns the set of Project Name / Site ID values that already have a PO Working entry."""
    identifiers = set()
    try:
        res_po = supabase.table("po_working").select("*").eq("workspace", workspace).execute()
        for item in (res_po.data or []):
            p_name = str(item.get("Project Name", "")).strip()
            s_id = str(item.get("Site ID", "")).strip()
            if p_name:
                identifiers.add(p_name)
            if s_id:
                identifiers.add(s_id)
    except Exception:
        pass
    return identifiers


def clear_site_data_cache():
    """Call this right before st.rerun() after any insert/update/delete on site_data or po_working."""
    fetch_site_data_cached.clear()
    fetch_po_upload_identifiers_cached.clear()


# -------------------------------------------------------------
# --- SMTP EMAIL SENDING CONFIGURATION
# -------------------------------------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "visiontechinfrasolution@gmail.com"

# PRAMOD BHAU: YAHAN APNA 16-DIGIT APP PASSWORD DAALIYE
SENDER_PASSWORD = "ngamnbrvtlrnfrzm"

def send_commissioning_email(to_email, cc_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Cc'] = cc_email
        msg['Subject'] = subject
        
        # HTML MIME Type is used here so bold tags work perfectly
        msg.attach(MIMEText(body, 'html'))
        
        recipients = [e.strip() for e in to_email.split(',') if e.strip()]
        if cc_email:
            recipients.extend([e.strip() for e in cc_email.split(',') if e.strip()])
            
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"SMTP Error: {str(e)}"

# -------------------------------------------------------------
# --- WHATSAPP SENDING LOGIC REMOVED (disabled for now) ---
# -------------------------------------------------------------

# --- 3.1 HELPER FOR DYNAMIC DROPDOWNS ---
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

# --- HELPER: FETCH ITEM MASTER DETAILS FOR AUTO-FILL IN MATERIAL MODAL ---
def get_item_master_details():
    mapping = {}
    table_names_to_try = ["Item Code", "item_code"]
    
    for t_name in table_names_to_try:
        try:
            res = supabase.table(t_name).select("*").execute()
            if res.data:
                for item in res.data:
                    code = str(item.get("item_code", "")).strip()
                    if code:
                        mapping[code] = {
                            "description": str(item.get("item_description", "") or ""),
                            "stn_status": str(item.get("stn_status", "Required") or "Required"),
                            "material_of": str(item.get("material_of", "Indus") or "Indus"),
                            "rate": item.get("rate")
                        }
                return mapping 
        except Exception as e:
            continue
            
    return mapping

# --- 3.5 ADD RECORD DIALOG FUNCTION (POP-UP) ---
@st.dialog("📄 Add Site Data", width="large")
def add_record_dialog():
    st.caption("Configure comprehensive site metrics and procurement status")

    # --- FIX: Defensive re-init in case session_state got reset mid-dialog
    # (happens on mobile/tablet when the websocket reconnects after backgrounding) ---
    if 'po_count' not in st.session_state:
        st.session_state.po_count = 1
    if 'add_mat_count' not in st.session_state:
        st.session_state.add_mat_count = 1

    all_dd = get_all_dropdowns() 
    
    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
        
        # Row 1
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dept = st.selectbox("DEPARTMENT", get_opts("Department", all_dd))
        with c2:
            operator = st.selectbox("OPERATOR", get_opts("Operator", all_dd))
        with c3:
            proj_name = st.selectbox("PROJECT NAME", get_opts("Project Name", all_dd))
        with c4:
            proj_id = st.text_input("PROJECT ID * (REQUIRED)", placeholder="Project ID")
            
        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            site_id = st.text_input("Site ID * (REQUIRED)", placeholder="Enter Site ID")
            
        site_name_val = ""
        cluster_val = ""
        area_val = "N/A"
        km_val = "N/A"
        lat_val = "N/A"
        long_val = "N/A"
        tech_val = "N/A"
        fse_val = "N/A"
        aom_val = "N/A"
        
        if site_id:
            try:
                master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id.strip()).execute()
                if master_res.data:
                    site_name_val = master_res.data[0].get("Site Name", "")
                    cluster_val = master_res.data[0].get("Cluster", "")
                    area_val = master_res.data[0].get("Area", "N/A")
                    km_val = master_res.data[0].get("KM", "N/A")
                    lat_val = master_res.data[0].get("Lat", "N/A")
                    long_val = master_res.data[0].get("Long", "N/A")
                    tech_val = master_res.data[0].get("Technician Detail", "N/A")
                    fse_val = master_res.data[0].get("FSE Detail", "N/A")
                    aom_val = master_res.data[0].get("AOM Detail", "N/A")
                    st.toast("Site Data Auto-Fetched Successfully! ✅", icon="✅")
                else:
                    st.toast("Site ID not found in Excalation Matrix table ⚠️", icon="⚠️")
            except Exception as e:
                st.toast(f"Table Error: {e} ❌", icon="❌")

        with c6:
            site_name = st.text_input("SITE NAME", value=site_name_val, placeholder="Auto Fetch")
        with c7:
            cluster = st.text_input("CLUSTER", value=cluster_val, placeholder="Auto Fetch")
        with c8:
            site_status = st.selectbox("SITE STATUS", get_opts("Site Status", all_dd))

        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 8px; margin-top: 5px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-around; margin-bottom: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🏢 Area: <span style="color: #3b82f6;">{area_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">📍 KM: <span style="color: #3b82f6;">{km_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🌍 LAT LONG: <span style="color: #3b82f6; white-space: pre;">{lat_val}  {long_val}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">🧑‍🔧 Technician: <span style="color: #3b82f6;">{tech_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👨‍💼 FSE: <span style="color: #3b82f6;">{fse_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👑 AOM: <span style="color: #3b82f6;">{aom_val}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
            
        st.markdown('<div class="modal-section-title">📦 MATERIAL, BILLING & RFAI DETAILS</div>', unsafe_allow_html=True)
        
        work_desc = st.text_input("WORK DESCRIPTION", placeholder="Enter detailed work description")
        
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            product = st.selectbox("PRODUCT", get_opts("Product", all_dd))
        with c10:
            rfai_status = st.selectbox("RFAI STATUS", get_opts("RFAI Status", all_dd))
        with c11:
            wh_material = st.selectbox("WH MATERIAL", get_opts("WH Material", all_dd))
        with c12:
            team_name = st.selectbox("TEAM NAME", get_opts("Team Name", all_dd))
            
        c13, c14, c15 = st.columns(3)
        with c13:
            ex_opts = get_opts("Extra Approval", all_dd)
            def_extra = ex_opts.index("Not Available") if "Not Available" in ex_opts else 0
            extra_approval = st.selectbox("EXTRA APPROVAL", ex_opts, index=def_extra)
        with c14:
            tb_opts = get_opts("Team Billing Status", all_dd)
            def_team = tb_opts.index("Pending") if "Pending" in tb_opts else 0
            team_billing = st.selectbox("TEAM BILLING STATUS", tb_opts, index=def_team)
        with c15:
            vb_opts = get_opts("Vision Billing Status", all_dd)
            def_vis = vb_opts.index("Pending") if "Pending" in vb_opts else 0
            vision_billing = st.selectbox("VISION BILLING STATUS", vb_opts, index=def_vis)

        st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        po_nos, po_dates, po_statuses, wcc_nums, wcc_statuses = [], [], [], [], []
        
        for i in range(st.session_state.po_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
            
            c17, c18, c19, c20, c21 = st.columns(5)
            with c17:
                p_n = st.text_input("PO NO.", placeholder="11 digits", key=f"po_no_{i}")
                po_nos.append(p_n)
            with c18:
                raw_p_d = st.date_input("PO DATE", value=None, key=f"po_date_{i}")
                p_d = raw_p_d.strftime("%d/%m/%Y") if raw_p_d else ""
                po_dates.append(p_d)
            with c19:
                p_s = st.selectbox("PO STATUS", get_opts("PO Status", all_dd), key=f"po_status_{i}")
                po_statuses.append(p_s)
            with c20:
                w_n = st.text_input("WCC NUMBER", placeholder="10 digits", key=f"wcc_num_{i}")
                wcc_nums.append(w_n)
            with c21:
                w_s = st.selectbox("WCC STATUS", get_opts("WCC Status", all_dd), key=f"wcc_status_{i}")
                wcc_statuses.append(w_s)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE PO BUTTONS ---
        col_btn_add, col_btn_rem, _ = st.columns([3, 3, 4])
        with col_btn_add:
            if st.button("➕ Add Additional PO", use_container_width=True):
                st.session_state.po_count += 1
        with col_btn_rem:
            if st.session_state.po_count > 1:
                if st.button("➖ Remove PO", use_container_width=True):
                    st.session_state.po_count -= 1
            
        # -------------------------------------------------------------
        # WAREHOUSE MATERIAL TRACKING IN ADD RECORD
        # -------------------------------------------------------------
        st.markdown('<div class="modal-section-title">📦 WAREHOUSE MATERIAL TRACKING (OPTIONAL)</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        a_mat_trans_types, a_mat_boqs, a_mat_item_codes, a_mat_descs, a_mat_qtys = [], [], [], [], []
        a_mat_statuses, a_mat_dates, a_mat_stn_statuses, a_mat_remarks = [], [], [], []
        
        for i in range(st.session_state.add_mat_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"a_trans_{i}")
                a_mat_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER", placeholder="BOQ No", key=f"a_boq_{i}")
                a_mat_boqs.append(boq_no)
            with mc3:
                i_code = st.text_input("ITEM CODE", placeholder="Type & Press Enter", key=f"a_icode_{i}")
                a_mat_item_codes.append(i_code)

            code_val = i_code.strip()
            if code_val:
                try:
                    item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                    if not item_res.data:
                        item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                        
                    if item_res.data:
                        fetched_desc = str(item_res.data[0].get("item_description", ""))
                        fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                        
                        st.session_state[f"a_idesc_{i}"] = fetched_desc
                        if fetched_stn in stn_status_opts:
                            st.session_state[f"a_stn_{i}"] = fetched_stn
                            
                        st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                    else:
                        st.toast("Item Code not found in database ⚠️", icon="⚠️")
                except Exception as e:
                    st.toast(f"Table Error: {e} ❌", icon="❌")

            with mc4:
                current_desc_val = st.session_state.get(f"a_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"a_idesc_{i}")
                a_mat_descs.append(i_desc)
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"a_iqty_{i}")
                a_mat_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"a_mstat_{i}")
                a_mat_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"a_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                a_mat_dates.append(d_date)
            with mc8:
                default_stn = "Select"
                if code_val and 'item_res' in locals() and item_res.data:
                    default_stn = fetched_stn if fetched_stn in stn_status_opts else "Select"
                
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"a_stn_{i}")
                a_mat_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"a_rem_{i}")
                a_mat_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE MATERIAL BUTTONS ---
        col_a_add, col_a_rem, _ = st.columns([3, 3, 4])
        with col_a_add:
            if st.button("➕ Add Material Item", key="btn_a_add_mat", use_container_width=True):
                st.session_state.add_mat_count += 1
        with col_a_rem:
            if st.session_state.add_mat_count > 1:
                if st.button("➖ Remove Material", key="btn_a_rem_mat", use_container_width=True):
                    st.session_state.add_mat_count -= 1

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- SUBMIT LOGIC ---
        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.button("💾 Save All Data", type="primary", use_container_width=True)
            
        if submitted:
            # Treat any leftover "nan"/"none"/"null" text as blank instead of failing validation
            po_nos = ["" if p.strip().lower() in ("nan", "none", "null") else p for p in po_nos]
            wcc_nums = ["" if w.strip().lower() in ("nan", "none", "null") else w for w in wcc_nums]

            has_error = False
            if not proj_id or not site_id:
                st.error("⚠️ Project ID aur Site ID dalna compulsory hai!")
                has_error = True
            for p in po_nos:
                if p and (not p.isdigit() or len(p) != 11):
                    st.error(f"⚠️ PO NO. '{p}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            for w in wcc_nums:
                if w and (not w.isdigit() or len(w) != 10):
                    st.error(f"⚠️ WCC NUMBER '{w}' strict 10 digit ka number hona chahiye!")
                    has_error = True
            
            # --- FIX: DUPLICATE PROJECT ID CHECK — NOW SCOPED TO CURRENT WORKSPACE ONLY ---
            if not has_error:
                active_ws_check = st.session_state.get('active_workspace', 'VISPL')
                try:
                    dup_check = supabase.table("site_data").select("id").eq("Project ID", proj_id).eq("workspace", active_ws_check).execute()
                    if len(dup_check.data) > 0:
                        st.error(f"❌ Project ID already exist in '{active_ws_check}' workspace")
                        has_error = True
                except Exception:
                    pass
                    
            if not has_error:
                insert_data = {
                    "workspace": st.session_state.get('active_workspace', 'VISPL'),
                    "created_at": datetime.utcnow().isoformat(),
                    "Department": dept if dept != "Select" else "",
                    "Operator": operator if operator != "Select" else "",
                    "Project Name": proj_name if proj_name != "Select" else "",
                    "Project ID": proj_id,
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Cluster": cluster,
                    "Site Status": site_status if site_status != "Select" else "",
                    "Work Description": work_desc,
                    "Product": product if product != "Select" else "",
                    
                    "PO No.": ", ".join([p for p in po_nos if p]),
                    "PO Date": ", ".join([str(d) for d in po_dates if d]),
                    "PO Status": ", ".join([ps if ps != "Select" else "" for ps in po_statuses]),
                    
                    "RFAI Status": rfai_status if rfai_status != "Select" else "",
                    "WH Material": wh_material if wh_material != "Select" else "",
                    "Team Name": team_name if team_name != "Select" else "",
                    "Team Billing Status": team_billing if team_billing != "Select" else "",
                    "Extra Approval": extra_approval if extra_approval != "Select" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Select" else "",
                    
                    "WCC Number": ", ".join([w for w in wcc_nums if w]),
                    "WCC Status": ", ".join([ws if ws != "Select" else "" for ws in wcc_statuses])
                }
                
                try:
                    res = supabase.table("site_data").insert(insert_data).execute()
                    new_id = res.data[0].get('id') if (hasattr(res, 'data') and res.data) else None
                    
                    # --- WHATSAPP MESSAGE ON FIRST ASSIGNMENT: DISABLED FOR NOW ---
                    
                    # --- SAVE OPTIONAL WAREHOUSE MATERIAL ---
                    active_ws_save = st.session_state.get('active_workspace', 'VISPL')
                    for i in range(len(a_mat_item_codes)):
                        if a_mat_item_codes[i].strip() != "" and a_mat_boqs[i].strip() != "":
                            insert_wh = {
                                "workspace": active_ws_save,
                                "Project ID": proj_id,
                                "Site ID": site_id,
                                "Site Name": site_name,
                                "Cluster": cluster,
                                "Team": team_name if team_name != "Select" else "",
                                "SRN Status": "Required",
                                "Transaction Type": a_mat_trans_types[i] if a_mat_trans_types[i] != "Select" else "",
                                "BOQ Number": a_mat_boqs[i],
                                "Item Code": a_mat_item_codes[i].strip(),
                                "Item Description": a_mat_descs[i],
                                "Indus Qty": a_mat_qtys[i],
                                "Material Status": a_mat_statuses[i] if a_mat_statuses[i] != "Select" else "",
                                "Dispatch Date": a_mat_dates[i],
                                "STN Status": a_mat_stn_statuses[i] if a_mat_stn_statuses[i] != "Select" else "",
                                "Remark": a_mat_remarks[i]
                            }
                            try:
                                # --- FIX: DUPLICATE ITEM CODE CHECK — NOW SCOPED TO CURRENT WORKSPACE ONLY ---
                                dup_wh = supabase.table("warehouse_data").select("id").eq("Project ID", proj_id).eq("Item Code", a_mat_item_codes[i].strip()).eq("workspace", active_ws_save).execute()
                                if not dup_wh.data:
                                    supabase.table("warehouse_data").insert(insert_wh).execute()
                            except Exception:
                                pass
                    
                    st.success("✅ Record Successfully Added!")
                    st.session_state.current_page = 1 # <--- NEW: Switch to page 1
                    
                    # --- TRIGGER POST-SAVE EMAIL POPUP LOGIC ---
                    if proj_name in ["Battery Bank", "SMPS", "SPS"] and site_status == "Completed":
                        st.session_state.pending_comm_email = True
                        st.session_state.comm_site_data = {
                            "db_id": new_id,
                            "proj_name": proj_name,
                            "proj_id": proj_id,
                            "site_id": site_id,
                            "site_name": site_name,
                            "cluster": cluster,
                            "team_name": team_name,
                            "tech_val": tech_val,
                            "fse_val": fse_val,
                            "lat_val": lat_val,
                            "long_val": long_val,
                        }
                    
                    clear_site_data_cache()
                    st.rerun() 
                except Exception as e:
                    st.error(f"❌ Error Saving Data: {e}")

# --- 3.6 EDIT RECORD DIALOG FUNCTION (NOW: VIEW + EDIT + DELETE COMBINED "MANAGE") ---
@st.dialog("⚙️ Manage Site Data (View / Edit / Delete)", width="large")
def edit_record_dialog(row_data):
    st.caption("Update comprehensive site metrics and procurement status")
    all_dd = get_all_dropdowns() 
    
    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dept_opts = get_opts("Department", all_dd)
            dept = st.selectbox("DEPARTMENT", dept_opts, index=get_idx(row_data.get('Department'), dept_opts), key="ed_dept")
        with c2:
            op_opts = get_opts("Operator", all_dd)
            operator = st.selectbox("OPERATOR", op_opts, index=get_idx(row_data.get('Operator'), op_opts), key="ed_op")
        with c3:
            pn_opts = get_opts("Project Name", all_dd)
            proj_name = st.selectbox("PROJECT NAME", pn_opts, index=get_idx(row_data.get('Project Name'), pn_opts), key="ed_pn")
        with c4:
            # --- FIX: Project ID field ab EDITABLE hai (pehle disabled=True tha) ---
            proj_id = st.text_input("PROJECT ID * (REQUIRED)", value=row_data.get('Project ID', ''), key="ed_pid")
            
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            site_id = st.text_input("Site ID * (REQUIRED)", value=row_data.get('Site ID', ''), key="ed_sid")
            
        area_val, km_val, lat_val, long_val, tech_val, fse_val, aom_val = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
        if site_id:
            try:
                master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id.strip()).execute()
                if master_res.data:
                    area_val = master_res.data[0].get("Area", "N/A")
                    km_val = master_res.data[0].get("KM", "N/A")
                    lat_val = master_res.data[0].get("Lat", "N/A")
                    long_val = master_res.data[0].get("Long", "N/A")
                    tech_val = master_res.data[0].get("Technician Detail", "N/A")
                    fse_val = master_res.data[0].get("FSE Detail", "N/A")
                    aom_val = master_res.data[0].get("AOM Detail", "N/A")
            except:
                pass

        with c6:
            site_name = st.text_input("SITE NAME", value=row_data.get('Site Name', ''), key="ed_sname")
        with c7:
            cluster = st.text_input("CLUSTER", value=row_data.get('Cluster', ''), key="ed_clu")
        with c8:
            ss_opts = get_opts("Site Status", all_dd)
            site_status = st.selectbox("SITE STATUS", ss_opts, index=get_idx(row_data.get('Site Status'), ss_opts), key="ed_ss")

        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 8px; margin-top: 5px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-around; margin-bottom: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🏢 Area: <span style="color: #3b82f6;">{area_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">📍 KM: <span style="color: #3b82f6;">{km_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 1rem;">🌍 LAT LONG: <span style="color: #3b82f6; white-space: pre;">{lat_val}  {long_val}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 12px;">
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">🧑‍🔧 Technician: <span style="color: #3b82f6;">{tech_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👨‍💼 FSE: <span style="color: #3b82f6;">{fse_val}</span></div>
                    <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem;">👑 AOM: <span style="color: #3b82f6;">{aom_val}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
            
        st.markdown('<div class="modal-section-title">📦 MATERIAL, BILLING & RFAI DETAILS</div>', unsafe_allow_html=True)
        
        work_desc = st.text_input("WORK DESCRIPTION", value=row_data.get('Work Description', ''), key="ed_wd")
        
        c9, c10, c11, c12 = st.columns(4)
        with c9:
            prod_opts = get_opts("Product", all_dd)
            product = st.selectbox("PRODUCT", prod_opts, index=get_idx(row_data.get('Product'), prod_opts), key="ed_prod")
        with c10:
            rfai_opts = get_opts("RFAI Status", all_dd)
            rfai_status = st.selectbox("RFAI STATUS", rfai_opts, index=get_idx(row_data.get('RFAI Status'), rfai_opts), key="ed_rfai")
        with c11:
            wh_opts = get_opts("WH Material", all_dd)
            wh_material = st.selectbox("WH MATERIAL", wh_opts, index=get_idx(row_data.get('WH Material'), wh_opts), key="ed_wh")
        with c12:
            team_opts = get_opts("Team Name", all_dd)
            team_name = st.selectbox("TEAM NAME", team_opts, index=get_idx(row_data.get('Team Name'), team_opts), key="ed_team")
            
        c13, c14, c15 = st.columns(3)
        with c13:
            ex_opts = get_opts("Extra Approval", all_dd)
            extra_approval = st.selectbox("EXTRA APPROVAL", ex_opts, index=get_idx(row_data.get('Extra Approval'), ex_opts), key="ed_ex")
        with c14:
            tb_opts = get_opts("Team Billing Status", all_dd)
            team_billing = st.selectbox("TEAM BILLING STATUS", tb_opts, index=get_idx(row_data.get('Team Billing Status'), tb_opts), key="ed_tb")
        with c15:
            vb_opts = get_opts("Vision Billing Status", all_dd)
            vision_billing = st.selectbox("VISION BILLING STATUS", vb_opts, index=get_idx(row_data.get('Vision Billing Status'), vb_opts), key="ed_vb")

        st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
        
        def _clean_stored_list(raw_value):
            """Split a comma-joined DB field into a list, dropping empty and
            'nan'/'none'/'null' junk values so they never pre-fill a text box."""
            items = []
            for x in str(raw_value if raw_value is not None else "").split(","):
                x = x.strip()
                if x and x.lower() not in ("nan", "none", "null"):
                    items.append(x)
            return items

        po_no_list = _clean_stored_list(row_data.get("PO No.", ""))
        po_date_list = _clean_stored_list(row_data.get("PO Date", ""))
        po_status_list = _clean_stored_list(row_data.get("PO Status", ""))
        wcc_num_list = _clean_stored_list(row_data.get("WCC Number", ""))
        wcc_status_list = _clean_stored_list(row_data.get("WCC Status", ""))
        
        max_boxes = max(1, len(po_no_list), len(wcc_num_list))
        if 'edit_po_count' not in st.session_state:
            st.session_state.edit_po_count = max_boxes
            
        po_nos, po_dates, po_statuses, wcc_nums, wcc_statuses = [], [], [], [], []
        
        for i in range(st.session_state.edit_po_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
            
            c17, c18, c19, c20, c21 = st.columns(5)
            with c17:
                val = po_no_list[i] if i < len(po_no_list) else ""
                p_n = st.text_input("PO NO.", value=val, key=f"e_po_no_{i}")
                po_nos.append(p_n)
            with c18:
                val = po_date_list[i] if i < len(po_date_list) else ""
                parsed_date = None
                if val:
                    try:
                        parsed_date = datetime.strptime(val.strip(), "%d/%m/%Y").date()
                    except Exception:
                        pass
                raw_p_d = st.date_input("PO DATE", value=parsed_date, key=f"e_po_date_{i}")
                p_d = raw_p_d.strftime("%d/%m/%Y") if raw_p_d else ""
                po_dates.append(p_d)
            with c19:
                val = po_status_list[i] if i < len(po_status_list) else "Select"
                ps_opts = get_opts("PO Status", all_dd)
                p_s = st.selectbox("PO STATUS", ps_opts, index=get_idx(val, ps_opts), key=f"e_po_status_{i}")
                po_statuses.append(p_s)
            with c20:
                val = wcc_num_list[i] if i < len(wcc_num_list) else ""
                w_n = st.text_input("WCC NUMBER", value=val, key=f"e_wcc_num_{i}")
                wcc_nums.append(w_n)
            with c21:
                val = wcc_status_list[i] if i < len(wcc_status_list) else "Select"
                ws_opts = get_opts("WCC Status", all_dd)
                w_s = st.selectbox("WCC STATUS", ws_opts, index=get_idx(val, ws_opts), key=f"e_wcc_status_{i}")
                wcc_statuses.append(w_s)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE PO BUTTONS ---
        col_btn_add, col_btn_rem, _ = st.columns([3, 3, 4])
        with col_btn_add:
            if st.button("➕ Add Additional PO", key="e_add_po", use_container_width=True):
                st.session_state.edit_po_count += 1
        with col_btn_rem:
            if st.session_state.edit_po_count > 1:
                if st.button("➖ Remove PO", key="e_rem_po", use_container_width=True):
                    st.session_state.edit_po_count -= 1
            
        st.markdown("<br>", unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns([8, 2])
        with col_btn2:
            submitted = st.button("💾 Update Data", type="primary", use_container_width=True)
            
        if submitted:
            # Treat any leftover "nan"/"none"/"null" text as blank instead of failing validation
            po_nos = ["" if p.strip().lower() in ("nan", "none", "null") else p for p in po_nos]
            wcc_nums = ["" if w.strip().lower() in ("nan", "none", "null") else w for w in wcc_nums]

            has_error = False
            if not site_id:
                st.error("⚠️ Site ID dalna compulsory hai!")
                has_error = True
            # --- FIX: Project ID bhi ab required + validated ---
            if not proj_id or not proj_id.strip():
                st.error("⚠️ Project ID dalna compulsory hai!")
                has_error = True
            for p in po_nos:
                if p and (not p.isdigit() or len(p) != 11):
                    st.error(f"⚠️ PO NO. '{p}' strict 11 digit ka number hona chahiye!")
                    has_error = True
            for w in wcc_nums:
                if w and (not w.isdigit() or len(w) != 10):
                    st.error(f"⚠️ WCC NUMBER '{w}' strict 10 digit ka number hona chahiye!")
                    has_error = True

            # --- FIX: DUPLICATE PROJECT ID CHECK (scoped to workspace, excluding this record itself) ---
            if not has_error and proj_id.strip() != str(row_data.get('Project ID', '')).strip():
                active_ws_check = st.session_state.get('active_workspace', 'VISPL')
                try:
                    dup_check = (
                        supabase.table("site_data")
                        .select("id")
                        .eq("Project ID", proj_id.strip())
                        .eq("workspace", active_ws_check)
                        .neq("id", row_data['id'])
                        .execute()
                    )
                    if dup_check.data and len(dup_check.data) > 0:
                        st.error(f"❌ Project ID already exist in '{active_ws_check}' workspace")
                        has_error = True
                except Exception:
                    pass
                    
            if not has_error:
                old_team_name = row_data.get('Team Name', '')
                old_proj_id = row_data.get('Project ID', '')
                
                update_data = {
                    # --- FIX: Project ID ab update_data me included hai ---
                    "Project ID": proj_id.strip(),
                    "Department": dept if dept != "Select" else "",
                    "Operator": operator if operator != "Select" else "",
                    "Project Name": proj_name if proj_name != "Select" else "",
                    "Site ID": site_id,
                    "Site Name": site_name,
                    "Cluster": cluster,
                    "Site Status": site_status if site_status != "Select" else "",
                    "Work Description": work_desc,
                    "Product": product if product != "Select" else "",
                    
                    "PO No.": ", ".join([p for p in po_nos if p]),
                    "PO Date": ", ".join([str(d) for d in po_dates if d]),
                    "PO Status": ", ".join([ps if ps != "Select" else "" for ps in po_statuses]),
                    
                    "RFAI Status": rfai_status if rfai_status != "Select" else "",
                    "WH Material": wh_material if wh_material != "Select" else "",
                    "Team Name": team_name if team_name != "Select" else "",
                    "Team Billing Status": team_billing if team_billing != "Select" else "",
                    "Extra Approval": extra_approval if extra_approval != "Select" else "",
                    "Vision Billing Status": vision_billing if vision_billing != "Select" else "",
                    
                    "WCC Number": ", ".join([w for w in wcc_nums if w]),
                    "WCC Status": ", ".join([ws if ws != "Select" else "" for ws in wcc_statuses])
                }
                
                try:
                    supabase.table("site_data").update(update_data).eq("id", row_data['id']).execute()
                    
                    # --- WHATSAPP MESSAGE ON TEAM CHANGE: DISABLED FOR NOW ---
                    
                    st.success("✅ Record Successfully Updated!")
                    
                    # --- TRIGGER POST-SAVE EMAIL POPUP LOGIC ---
                    # Strictly fetch fresh flag status from Supabase handling both case variations safely
                    try:
                        fresh_check = supabase.table("site_data").select("*").eq("id", row_data['id']).execute()
                        if fresh_check.data:
                            row_fetched = fresh_check.data[0]
                            val = row_fetched.get("Commissioning Email Sent")
                            if val is None:
                                val = row_fetched.get("commissioning_email_sent", "")
                            already_sent_flag = str(val).strip().lower() if val else ""
                        else:
                            already_sent_flag = ""
                    except Exception as e:
                        already_sent_flag = ""
                    
                    if proj_name in ["Battery Bank", "SMPS", "SPS"] and site_status == "Completed" and already_sent_flag != "yes":
                        st.session_state.pending_comm_email = True
                        st.session_state.comm_site_data = {
                            "db_id": row_data['id'],
                            "proj_name": proj_name,
                            "proj_id": proj_id,
                            "site_id": site_id,
                            "site_name": site_name,
                            "cluster": cluster,
                            "team_name": team_name,
                            "tech_val": tech_val,
                            "fse_val": fse_val,
                            "lat_val": lat_val,
                            "long_val": long_val,
                        }
                    # -------------------------------------------------

                    if 'edit_po_count' in st.session_state:
                        del st.session_state['edit_po_count']
                    clear_site_data_cache()
                    st.rerun() 
                except Exception as e:
                    st.error(f"❌ Error Updating Data: {e}")

        # ---------------------------------------------------------------
        # --- DANGER ZONE: DELETE THIS RECORD (merged from separate button)
        # ---------------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="border-top: 1px dashed rgba(239,68,68,0.4); margin-top: 10px; padding-top: 15px;">
                <div style="color:#f87171; font-weight:800; font-size:0.85rem; letter-spacing:1px; text-transform:uppercase;">⚠️ Danger Zone</div>
            </div>
        """, unsafe_allow_html=True)
        confirm_del = st.checkbox(
            "Main is record ko permanently DELETE karna chahta hoon (is action ko undo nahi kiya ja sakta)",
            key=f"del_confirm_{row_data['id']}"
        )
        if confirm_del:
            if st.button("🗑️ Delete This Record Permanently", key=f"del_now_{row_data['id']}", type="secondary", use_container_width=True):
                try:
                    supabase.table("site_data").delete().eq("id", row_data['id']).execute()
                    st.success("✅ Record Successfully Deleted!")
                    clear_site_data_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Deleting Record: {e}")

# --- 3.7 WAREHOUSE MATERIAL POP-UP DIALOG FUNCTION ---
@st.dialog("📦 Warehouse Material Tracking", width="large")
def material_movement_dialog(row_data):
    st.caption("Manage transaction items and asset movements for selected site")

    # --- FIX: Defensive re-init in case session_state got reset mid-dialog ---
    if 'mat_count' not in st.session_state:
        st.session_state.mat_count = 1

    all_dd = get_all_dropdowns()
    
    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    with st.container():
        st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.text_input("PROJECT ID", value=row_data.get('Project ID', ''), disabled=True, key="m_pid")
        with c2:
            st.text_input("SITE ID", value=row_data.get('Site ID', ''), disabled=True, key="m_sid")
        with c3:
            st.text_input("SITE NAME", value=row_data.get('Site Name', ''), disabled=True, key="m_sname")
        with c4:
            st.text_input("CLUSTER", value=row_data.get('Cluster', ''), disabled=True, key="m_clu")
        with c5:
            st.text_input("TEAM", value=row_data.get('Team Name', ''), disabled=True, key="m_team")
        with c6:
            srn_opts = get_opts("SRN Status", all_dd)
            srn_status = st.selectbox("SRN STATUS *", srn_opts, key="m_srn_status")

        st.markdown('<div class="modal-section-title">📦 TRANSACTION & ASSET ITEMS</div>', unsafe_allow_html=True)
        
        trans_types = get_opts("Transaction Type", all_dd)
        mat_status_opts = get_opts("Material Status", all_dd)
        stn_status_opts = get_opts("STN Status", all_dd)
        
        mat_trans_types, mat_boqs, mat_item_codes, mat_descs, mat_qtys = [], [], [], [], []
        mat_statuses, mat_dates, mat_stn_statuses, mat_remarks = [], [], [], []
        
        for i in range(st.session_state.mat_count):
            if i > 0:
                st.markdown(f"<p style='color:#cbd5e1; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"m_trans_{i}")
                mat_trans_types.append(t_type)
            with mc2:
                boq_no = st.text_input("BOQ NUMBER *", placeholder="BOQ No", key=f"m_boq_{i}")
                mat_boqs.append(boq_no)
            
            with mc3:
                i_code = st.text_input("ITEM CODE *", placeholder="Type & Press Enter", key=f"m_icode_{i}")
                mat_item_codes.append(i_code)

            code_val = i_code.strip()
            if code_val:
                try:
                    item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                    if not item_res.data:
                        item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                        
                    if item_res.data:
                        fetched_desc = str(item_res.data[0].get("item_description", ""))
                        fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                        
                        st.session_state[f"m_idesc_{i}"] = fetched_desc
                        if fetched_stn in stn_status_opts:
                            st.session_state[f"m_stn_{i}"] = fetched_stn
                            
                        st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                    else:
                        st.toast("Item Code not found in database ⚠️", icon="⚠️")
                except Exception as e:
                    st.toast(f"Table Error: {e} ❌", icon="❌")

            with mc4:
                current_desc_val = st.session_state.get(f"m_idesc_{i}", "")
                i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_val, placeholder="Description", key=f"m_idesc_{i}")
                mat_descs.append(i_desc)
                
            with mc5:
                i_qty = st.number_input("INDUS QTY", min_value=0, value=0, key=f"m_iqty_{i}")
                mat_qtys.append(i_qty)
                
            mc6, mc7, mc8, mc9 = st.columns(4)
            with mc6:
                m_stat = st.selectbox("MATERIAL STATUS", mat_status_opts, key=f"m_mstat_{i}")
                mat_statuses.append(m_stat)
            with mc7:
                raw_d_date = st.date_input("DISPATCH DATE", value=None, key=f"m_ddate_{i}")
                d_date = raw_d_date.strftime("%d/%m/%Y") if raw_d_date else ""
                mat_dates.append(d_date)
            with mc8:
                default_stn = "Select"
                if code_val and 'item_res' in locals() and item_res.data:
                    default_stn = fetched_stn if fetched_stn in stn_status_opts else "Select"
                
                stn_idx = stn_status_opts.index(default_stn) if default_stn in stn_status_opts else 0
                stn_stat = st.selectbox("STN STATUS", stn_status_opts, index=stn_idx, key=f"m_stn_{i}")
                mat_stn_statuses.append(stn_stat)
            with mc9:
                rem = st.text_input("REMARKS", placeholder="Remarks notes", key=f"m_rem_{i}")
                mat_remarks.append(rem)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIXED ADD/REMOVE MATERIAL BUTTONS ---
        col_m_add, col_m_rem, _ = st.columns([3, 3, 4])
        with col_m_add:
            if st.button("➕ Add Item", key="btn_add_mat_item", use_container_width=True):
                st.session_state.mat_count += 1
        with col_m_rem:
            if st.session_state.mat_count > 1:
                if st.button("➖ Remove Item", key="btn_rem_mat_item", use_container_width=True):
                    st.session_state.mat_count -= 1
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_ms1, col_ms2 = st.columns([8, 2])
        with col_ms2:
            save_mat = st.button("💾 Save Material", type="primary", use_container_width=True)
            
        if save_mat:
            has_m_err = False
            for b in mat_boqs:
                if not b:
                    st.error("⚠️ BOQ Number dalna compulsory hai!")
                    has_m_err = True
                    break
                    
            proj_id = row_data.get('Project ID', '')
            active_ws_mat = st.session_state.get('active_workspace', 'VISPL')
            seen_codes = set()
            if not has_m_err:
                for idx, ic in enumerate(mat_item_codes):
                    code_str = ic.strip()
                    if not code_str:
                        st.error(f"⚠️ Item {idx+1}: Item Code cannot be empty!")
                        has_m_err = True
                        break
                    if code_str in seen_codes:
                        st.error(f"⚠️ Item {idx+1}: You entered duplicate Item Code '{code_str}' in this form!")
                        has_m_err = True
                        break
                    seen_codes.add(code_str)

            # --- FIX: DUPLICATE ITEM CODE CHECK — NOW SCOPED TO CURRENT WORKSPACE ONLY ---
            if not has_m_err and proj_id:
                for ic in mat_item_codes:
                    code_str = ic.strip()
                    try:
                        dup_check = supabase.table("warehouse_data").select("id").eq("Project ID", proj_id).eq("Item Code", code_str).eq("workspace", active_ws_mat).execute()
                        if dup_check.data and len(dup_check.data) > 0:
                            st.error(f"❌ This item '{code_str}' already exist against this project id '{proj_id}' in '{active_ws_mat}' workspace.")
                            has_m_err = True
                            break
                    except Exception:
                        pass
                        
            if not has_m_err:
                try:
                    for i in range(len(mat_item_codes)):
                        insert_dict = {
                            "workspace": active_ws_mat,
                            "Project ID": proj_id,
                            "Site ID": row_data.get('Site ID', ''),
                            "Site Name": row_data.get('Site Name', ''),
                            "Cluster": row_data.get('Cluster', ''),
                            "Team": row_data.get('Team Name', ''),
                            "SRN Status": "Required",
                            "Transaction Type": mat_trans_types[i] if mat_trans_types[i] != "Select" else "",
                            "BOQ Number": mat_boqs[i],
                            "Item Code": mat_item_codes[i].strip(),
                            "Item Description": mat_descs[i],
                            "Indus Qty": mat_qtys[i],
                            "Material Status": mat_statuses[i] if mat_statuses[i] != "Select" else "",
                            "Dispatch Date": mat_dates[i],
                            "STN Status": mat_stn_statuses[i] if mat_stn_statuses[i] != "Select" else "",
                            "Remark": mat_remarks[i]
                        }
                        supabase.table("warehouse_data").insert(insert_dict).execute()
                        
                    st.success("✅ Warehouse Material Successfully Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving Material: {e}")

# --- 3.78 NEW: EXCLUSIVE COMMISSIONING EMAIL POPUP DIALOG ---
@st.dialog("📧 Commissioning Email Notification", width="large")
def commissioning_email_dialog():
    st.markdown("<p style='color:#cbd5e1; font-size:1rem;'>Please configure the commissioning email action for this completed site.</p>", unsafe_allow_html=True)
    
    data = st.session_state.get("comm_site_data", {})
    db_id = data.get("db_id")
    proj_name = data.get("proj_name", "")
    proj_id = data.get("proj_id", "")
    site_id = data.get("site_id", "")
    site_name = data.get("site_name", "")
    cluster = data.get("cluster", "")
    tech_val = data.get("tech_val", "N/A")
    fse_val = data.get("fse_val", "N/A")
    team_name = data.get("team_name", "N/A")
    lat_val = data.get("lat_val", "N/A")
    long_val = data.get("long_val", "N/A")
    
    # Fetch Team Mobile
    team_mobile = "N/A"
    if team_name and team_name != "Select":
        try:
            t_res = supabase.table("dropdown_master").select("mobile").eq("category", "Team Name").eq("option_value", team_name).execute()
            if t_res.data:
                mob = t_res.data[0].get("mobile", "")
                if mob and str(mob).upper() != "EMPTY":
                    team_mobile = str(mob).strip()
        except:
            pass
    
    all_dd = get_all_dropdowns()
    
    comm_req = st.radio("Email For Commissioning Action:", ["Not Required", "Required"], horizontal=True, key="comm_popup_radio")
    
    if comm_req == "Required":
        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.1); margin: 15px 0;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        
        with c1:
            make_opts = get_opts("Make", all_dd)
            if len(make_opts) <= 1:
                make_opts = ["Select", "Amraraja", "Vertiv", "Exide", "HBL", "Other"]
            comm_make = st.selectbox("Make *", make_opts, key="comm_popup_make")
            comm_desc = st.text_area("Description *", placeholder="Enter description details here...", height=110, key="comm_popup_desc")
            
        auto_to = ""
        auto_cc = ""
        if comm_make != "Select":
            try:
                to_list = []
                cc_list = []
                
                # 1. Fetch from Make_Email_Master (Filters by Project Name AND Make)
                res_make = supabase.table("Make_Email_Master").select("*").eq("Project Name", proj_name).ilike("Make", comm_make).execute()
                if res_make.data:
                    for row in res_make.data:
                        m_to = str(row.get("Make_TO", "")).strip()
                        m_cc = str(row.get("Make_CC", "")).strip()
                        
                        if m_to and m_to.lower() != "nan":
                            to_list.extend([e.strip() for e in m_to.split(',') if e.strip()])
                        if m_cc and m_cc.lower() != "nan":
                            cc_list.extend([e.strip() for e in m_cc.split(',') if e.strip()])
                                
                # 2. Fetch Cluster FSE & AOM Emails from Cluster_Email_Master
                res_cluster = supabase.table("Cluster_Email_Master").select("*").ilike("Cluster", cluster).execute()
                if res_cluster.data:
                    for row in res_cluster.data:
                        fse_email = str(row.get("FSE Email", "")).strip()
                        aom_email = str(row.get("AOM Email", "")).strip()
                        
                        if fse_email and fse_email.lower() != "nan":
                            cc_list.extend([e.strip() for e in fse_email.split(',') if e.strip()])
                        if aom_email and aom_email.lower() != "nan":
                            cc_list.extend([e.strip() for e in aom_email.split(',') if e.strip()])
                            
                # Remove duplicates while preserving order
                auto_to = ", ".join(list(dict.fromkeys(to_list)))
                auto_cc = ", ".join(list(dict.fromkeys(cc_list)))
            except Exception as e:
                pass 
                
        with c2:
            to_email = st.text_input("To Email *", value=auto_to, placeholder="Auto-fetched from DB or enter manually")
            cc_email = st.text_input("CC Email", value=auto_cc, placeholder="Auto-fetched from DB or enter manually")
            
        # DYNAMIC EMAIL BODY GENERATION (HTML for Bold Support)
        proj_type = "Battery Bank" if proj_name == "Battery Bank" else "SMPS/SPS"
        subject = f"Request for {proj_type} Commissioning – {proj_id}_{site_id}_{site_name}"
        
        body = f"""<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Dear Sir,</p>

<p>We are pleased to inform you that the {proj_type} installation work at the below-mentioned site has been completed successfully.</p>

<p>Kindly arrange to depute your commissioning engineer at the earliest to carry out the {proj_type} commissioning.</p>

<p><b>Site Details:</b><br>
<b>Project ID:</b> {proj_id}<br>
<b>Site ID:</b> {site_id}<br>
<b>Site Name:</b> {site_name}<br>
<b>Cluster:</b> {cluster}<br>
<b>Lat Long :-</b> ({lat_val} / {long_val})<br>
<b>Product Detial :-</b> {comm_desc}<br>
<b>Technician Detail :</b> {tech_val}<br>
<b>FSE Detail :</b> {fse_val}<br>
<b>Team Name :</b> {team_name}<br>
<b>Team Number :</b> {team_mobile}</p>

<p>Kindly confirm the engineer's visit schedule so that the necessary arrangements can be made at the site.</p>

<p>If any issue regarding PO of commissioning Kindly confirm from Indus team. and share Commissioning report ASAP so we can claim our billing.</p>

<p>Looking forward to your confirmation.</p>

<p>Regards,<br>
Visiontech Infra</p>
</div>"""

        with st.expander("👁️ Preview Email Template"):
            st.markdown(f"**Subject:** {subject}")
            st.markdown(body, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("❌ Close / Ignore", use_container_width=True):
            st.session_state.pending_comm_email = False
            st.rerun()
            
    with col3:
        if st.button("🚀 Send Email & Complete", type="primary", use_container_width=True):
            if comm_req == "Required":
                if comm_make == "Select":
                    st.error("⚠️ Please select a Make.")
                    return
                if not comm_desc.strip():
                    st.error("⚠️ Please enter a Description.")
                    return
                if not to_email.strip():
                    st.error("⚠️ To Email address is required.")
                    return
                
                success, err_msg = send_commissioning_email(to_email, cc_email, subject, body)
                if success:
                    st.toast("✅ Commissioning Email Sent Successfully!", icon="📨")
                    if db_id:
                        try:
                            # SUPABASE ME SAVE KAREGA YAHAN
                            try:
                                supabase.table("site_data").update({"Commissioning Email Sent": "Yes"}).eq("id", db_id).execute()
                            except:
                                supabase.table("site_data").update({"commissioning_email_sent": "Yes"}).eq("id", db_id).execute()
                        except Exception as e:
                            pass # Silently ignore so user isn't stuck
                else:
                    st.error(f"❌ Failed to send email: {err_msg}")
                    return
            else:
                st.toast("✅ Commissioning marked as Not Required. Action closed.", icon="✅")
                
            st.session_state.pending_comm_email = False
            clear_site_data_cache()
            st.rerun()

# --- 3.8 BULK UPLOAD DIALOG FUNCTION (FIXED: proper error reporting + summary popup) ---
@st.dialog("📤 Bulk Upload Site Data", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel (.xlsx) or .tsv file to bulk import site records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_site_file")

    # --- SHOW LAST UPLOAD RESULT (persists across the rerun so it doesn't vanish) ---
    if st.session_state.get("bulk_upload_result"):
        result = st.session_state["bulk_upload_result"]
        st.markdown("---")
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px;">
                <div style="font-weight:800; color:#ffffff; font-size:1.05rem; margin-bottom:10px;">📊 Upload Summary</div>
                <div style="color:#e2e8f0; margin-bottom:4px;">📄 Total Rows in File: <b>{result['total']}</b></div>
                <div style="color:#4ade80; margin-bottom:4px;">✅ Successfully Added: <b>{result['added']}</b></div>
                <div style="color:#facc15; margin-bottom:4px;">🟡 Skipped (Duplicate Project ID in '{result['workspace']}'): <b>{result['dup']}</b></div>
                <div style="color:#94a3b8; margin-bottom:4px;">⚪ Skipped (Missing/Blank Project ID): <b>{result['missing_pid']}</b></div>
                <div style="color:#f87171;">❌ Failed (Error): <b>{result['failed']}</b></div>
            </div>
        """, unsafe_allow_html=True)

        if result["fail_details"]:
            with st.expander(f"❌ View {len(result['fail_details'])} Failed Row Details (Reason)"):
                for f in result["fail_details"]:
                    st.markdown(f"- **Excel Row {f['row']}** (Project ID: `{f['pid'] or 'N/A'}`) → {f['reason']}")

        col_close, _ = st.columns([1, 3])
        with col_close:
            if st.button("✅ OK, Close This Summary", type="primary", use_container_width=True):
                st.session_state["bulk_upload_result"] = None
                st.rerun()
        st.markdown("---")

    if uploaded_file:
        if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file, sep='\t')
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                return

            if df_upload.empty:
                st.warning("⚠️ Uploaded file me koi data row nahi mili.")
                return

            active_ws_bulk = st.session_state.get('active_workspace', 'VISPL')
            added_count = 0
            skipped_dup_count = 0
            missing_pid_count = 0
            fail_details = []

            total_rows = len(df_upload)
            progress = st.progress(0, text="Processing rows...")
            bulk_upload_base_time = datetime.utcnow()  # base time; each row gets +1ms so file order is preserved

            for index, row in df_upload.iterrows():
                progress.progress(
                    min((index + 1) / total_rows, 1.0),
                    text=f"Processing row {index + 1} of {total_rows}..."
                )

                # Excel row number as user sees it (header = row 1, data starts row 2)
                excel_row_no = index + 2

                p_id = str(row.get("Project ID", row.get("project_id", ""))).strip()
                if not p_id or p_id.lower() == "nan":
                    missing_pid_count += 1
                    continue

                # --- DUPLICATE PROJECT ID CHECK (scoped to current workspace) ---
                try:
                    dup_bulk = (
                        supabase.table("site_data")
                        .select("id")
                        .eq("Project ID", p_id)
                        .eq("workspace", active_ws_bulk)
                        .execute()
                    )
                    if dup_bulk.data and len(dup_bulk.data) > 0:
                        skipped_dup_count += 1
                        continue
                except Exception as e:
                    fail_details.append({"row": excel_row_no, "pid": p_id, "reason": f"Duplicate-check DB error: {e}"})
                    continue

                insert_dict = {
                    "workspace": active_ws_bulk,
                    "created_at": (bulk_upload_base_time + timedelta(milliseconds=index)).isoformat(),
                }
                for col in columns_list:
                    if col not in ("id", "🎯 Select"):
                        val = row.get(col, row.get(col.lower(), ""))
                        val_str = str(val).strip() if pd.notna(val) else ""
                        if val_str.lower() == 'nan':
                            val_str = ""
                        insert_dict[col] = val_str

                # Handle Excel float artifact on Site ID (e.g. "123.0" -> "123")
                site_id_val = insert_dict.get("Site ID", "").strip()
                if site_id_val.endswith(".0"):
                    site_id_val = site_id_val[:-2]
                insert_dict["Site ID"] = site_id_val

                # Auto-fetch Site Name / Cluster from Excalation Matrix if blank
                if site_id_val:
                    sn = insert_dict.get("Site Name", "").strip()
                    cl = insert_dict.get("Cluster", "").strip()
                    is_sn_empty = not sn or sn.lower() in ["-", "nan", "none", "empty"]
                    is_cl_empty = not cl or cl.lower() in ["-", "nan", "none", "empty"]
                    if is_sn_empty or is_cl_empty:
                        try:
                            master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id_val).execute()
                            if master_res.data:
                                if is_sn_empty:
                                    insert_dict["Site Name"] = str(master_res.data[0].get("Site Name", "") or "").strip()
                                if is_cl_empty:
                                    insert_dict["Cluster"] = str(master_res.data[0].get("Cluster", "") or "").strip()
                        except Exception:
                            pass  # non-fatal: auto-fetch failing shouldn't block the insert

                try:
                    supabase.table("site_data").insert(insert_dict).execute()
                    added_count += 1
                except Exception as e:
                    # THIS is the actual reason a row failed — now captured instead of swallowed
                    fail_details.append({"row": excel_row_no, "pid": p_id, "reason": str(e)})

            progress.empty()

            # --- Save summary in session_state so it survives st.rerun() below ---
            st.session_state["bulk_upload_result"] = {
                "total": total_rows,
                "added": added_count,
                "dup": skipped_dup_count,
                "missing_pid": missing_pid_count,
                "failed": len(fail_details),
                "fail_details": fail_details,
                "workspace": active_ws_bulk,
            }

            st.session_state.current_page = 1
            clear_site_data_cache()
            st.rerun()

# --- 3.8.5 NEW: FIXED UPDATE PO STATUS DIALOG FUNCTION ---
@st.dialog("📝 Update PO Status", width="large")
def update_po_status_dialog():
    st.caption("Upload Excel (Col 1: 'PO No.', Col 2: 'PO Status') to bulk update existing records.")
    st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#cbd5e1; margin-bottom:5px;'>UPDATE FILE <span style='color:#ef4444;'>*</span></p>", unsafe_allow_html=True)
    status_file = st.file_uploader("UPLOAD FILE", label_visibility="collapsed", type=["xlsx", "xls"], key="po_status_file")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_s = st.columns(2)
    with col_c:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col_s:
        if st.button("🚀 Process & Update", type="primary", use_container_width=True):
            if not status_file:
                st.error("⚠️ Update file upload karna compulsory hai!")
            else:
                try:
                    df_status = pd.read_excel(status_file)
                        
                    if 'PO No.' not in df_status.columns or 'PO Status' not in df_status.columns:
                        st.error("❌ File me exactly 'PO No.' aur 'PO Status' naam ke columns hone chahiye!")
                        return
                    
                    updated_count = 0
                    not_found_count = 0
                    
                    active_ws = st.session_state.get('active_workspace', 'VISPL')
                    all_db_res = supabase.table("site_data").select("*").eq("workspace", active_ws).execute()
                    all_db_records = all_db_res.data if all_db_res.data else []
                    
                    for index, row in df_status.iterrows():
                        try:
                            po_no = str(int(float(row['PO No.']))).strip()
                        except:
                            po_no = str(row['PO No.']).strip()
                            
                        new_status = str(row['PO Status']).strip()
                        
                        if not po_no or po_no.lower() == 'nan' or po_no == '0':
                            continue
                            
                        match_found = False
                        for record in all_db_records:
                            db_po_string = str(record.get('PO No.', ''))
                            db_po_list = [p.strip() for p in db_po_string.split(',')]
                            
                            if po_no in db_po_list:
                                try:
                                    supabase.table("site_data").update({"PO Status": new_status}).eq("id", record['id']).execute()
                                    updated_count += 1
                                    match_found = True
                                except Exception:
                                    pass
                                    
                        if not match_found:
                            not_found_count += 1
                            
                    if updated_count > 0:
                        st.success(f"✅ Status Update Complete! {updated_count} records updated successfully. ({not_found_count} not found)")
                        clear_site_data_cache()
                    else:
                        st.warning(f"⚠️ No records were updated. ({not_found_count} PO numbers not found in database)")
                    
                except Exception as e:
                    st.error(f"❌ Error processing file: {e}")

# --- 3.9 EXPORT DIALOG FUNCTION ---
@st.dialog("📥 Export Data", width="large")
def export_dialog(df_export):
    st.caption("Download your live database records as an Excel file.")
    
    export_df = df_export.copy()
    if "🎯 Select" in export_df.columns:
        export_df = export_df.drop(columns=["🎯 Select"])
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    # --- ADDING PO UPLOAD STATUS TO EXCEL ---
    active_ws = st.session_state.get('active_workspace', 'VISPL')
    uploaded_po_identifiers = set()
    try:
        res_po = supabase.table("po_working").select("*").eq("workspace", active_ws).execute()
        if res_po.data:
            for item in res_po.data:
                p_name = str(item.get("Project Name", "")).strip()
                s_id = str(item.get("Site ID", "")).strip()
                if p_name: uploaded_po_identifiers.add(p_name)
                if s_id: uploaded_po_identifiers.add(s_id)
    except Exception:
        pass

    def get_po_upload_status(row):
        pid = str(row.get("Project ID", "")).strip()
        sid = str(row.get("Site ID", "")).strip()
        if (pid and pid in uploaded_po_identifiers) or (sid and sid in uploaded_po_identifiers):
            return "Available"
        return "Pending"
        
    # Insert right after PO Status in Excel
    if 'PO Status' in export_df.columns:
        loc = export_df.columns.get_loc('PO Status') + 1
        export_df.insert(loc, 'PO UPLOAD STATUS', export_df.apply(get_po_upload_status, axis=1))
    else:
        export_df['PO UPLOAD STATUS'] = export_df.apply(get_po_upload_status, axis=1)
    # ----------------------------------------
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Site Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="Site_Data_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# ==============================================================
# --- TRIGGER FOR COMMISSIONING POPUP AFTER MAIN MODAL CLOSES
# ==============================================================
if st.session_state.get('pending_comm_email'):
    commissioning_email_dialog()
# ==============================================================

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 4. TOP ACTION BAR (RIGHT SIDE BUTTONS) ---
col_title, col_ref, col_add, col_upload, col_update, col_export = st.columns([2.5, 1, 1.5, 1.5, 1.5, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>🏗️ Site Data Master</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        clear_site_data_cache()
        st.rerun() 
with col_add:
    if st.button("➕ Add Record", use_container_width=True):
        st.session_state.action = "add"
        st.session_state.po_count = 1 
        add_record_dialog() 
with col_upload:
    if st.button("📤 Bulk Upload", use_container_width=True):
        bulk_upload_dialog() 
with col_update:
    if st.button("📝 Update Status", type="primary", use_container_width=True):
        update_po_status_dialog() 
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. FETCH & PREPARE DATA (cached — see fetch_site_data_cached above) ---
table_name = "site_data"
active_ws = st.session_state.get('active_workspace', 'VISPL')
data = fetch_site_data_cached(active_ws)

columns_list = [
    "id", "Department", "Operator", "Project Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Site Status", "PO No.", "PO Date", 
    "PO Status", "Product", "RFAI Status", "Work Description", "WH Material", 
    "Team Name", "Team Billing Status", "Vision Billing Status", "Extra Approval", 
    "WCC Number", "WCC Status", "Commissioning Email Sent"
]

if data:
    df = pd.DataFrame(data)
    
    # ---> FIXED: Robust Sorting Logic to guarantee newest record is ALWAYS on Page 1, Row 1 <---
    if 'created_at' in df.columns:
        # If Supabase has 'created_at' timestamp, this is the most accurate way to sort newest first
        df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
        df = df.sort_values(by='created_at_dt', ascending=False).drop(columns=['created_at_dt']).reset_index(drop=True)
    elif 'id' in df.columns:
        # Fallback if created_at is missing: Check if ID is numeric
        id_numeric = pd.to_numeric(df['id'], errors='coerce')
        if id_numeric.notna().any():
            # Sort numeric IDs descending
            df['id_num'] = id_numeric.fillna(-1)
            df = df.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
        else:
            # If ID is UUID string, reverse the order (Postgres appends new rows to the bottom)
            df = df.iloc[::-1].reset_index(drop=True)
            
    for col in columns_list:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=columns_list)

if "🎯 Select" not in df.columns:
    df.insert(0, "🎯 Select", False)
else:
    df["🎯 Select"] = False

# --- 5.5 LAVISH UNIVERSAL SEARCH BOX + TEAM FILTER + VIEW MODE TOGGLE ---
col_table_title, col_team_filter, col_search, col_viewtoggle = st.columns([2.5, 2.2, 3, 2])
with col_table_title:
    st.markdown("##### 🗄️ Live Database Records")
with col_team_filter:
    _team_dd = get_all_dropdowns()
    team_filter_opts = ["All Teams"] + sorted({
        row["option_value"] for row in _team_dd if row["category"] == "Team Name" and row.get("option_value")
    })
    selected_team_filter = st.selectbox(
        "Filter by Team", team_filter_opts, key="team_filter_select", label_visibility="collapsed"
    )
with col_search:
    search_query = st_keyup("Search", placeholder="🔍 Search records...", label_visibility="collapsed")
with col_viewtoggle:
    toggle_label = "📱 Mobile View" if st.session_state.site_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="view_mode_toggle"):
        st.session_state.site_view_mode = "cards" if st.session_state.site_view_mode == "table" else "table"
        st.rerun()

# --- APPLY TEAM FILTER ---
if selected_team_filter and selected_team_filter != "All Teams":
    df = df[df["Team Name"].astype(str).str.strip() == selected_team_filter]

# --- APPLY SEARCH FILTER ---
if search_query:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

# --- EXPORT LOGIC TRIGGER: AFTER team filter + search, so export matches exactly
#     what's currently shown in the table (whether that's 1 row or 100,000) ---
if st.session_state.get('action') == "export":
    export_dialog(df)
    st.session_state.action = ""

# --- 6. PAGINATION LOGIC (10 lines per page) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages
elif st.session_state.current_page < 1:
    st.session_state.current_page = 1

# Keep the "go to page" input box in sync if current_page got clamped
# (e.g. after a search filters the results down to fewer pages)
if st.session_state.get('page_jump_input', 1) > total_pages or st.session_state.get('page_jump_input', 1) < 1:
    st.session_state['page_jump_input'] = st.session_state.current_page

start_idx = (st.session_state.current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

# --- 7. TABLE / CARD DISPLAY ---
df_page = df.iloc[start_idx:end_idx].copy()

def status_badge(val):
    v = str(val).strip()
    if not v or v.lower() in ("nan", "none", "-"):
        return "<span class='tbl-cell'>-</span>"
    vl = v.lower()
    if "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "available"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<span class='status-badge {cls}'>{v}</span>"

if df_page.empty:
    st.info("No records found.")

elif st.session_state.site_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE-FRIENDLY CARD VIEW - one card per record, no horizontal scroll
    # ---------------------------------------------------------------
    for page_pos, (_, row) in enumerate(df_page.iterrows()):
        row_dict = row.to_dict()
        rid = row_dict.get("id")
        serial_no = start_idx + page_pos + 1
        is_wh_required = str(row_dict.get("WH Material", "")).strip().lower() == "required"

        with st.container(border=True):
            st.markdown(f"""
                <div class="site-card-title">#{serial_no} — {row_dict.get('Site ID','') or '-'} | {row_dict.get('Site Name','') or '-'}</div>
                <div class="site-card-sub">{row_dict.get('Project ID','') or '-'} • {row_dict.get('Cluster','') or '-'}</div>
                <div class="site-card-row"><span class="site-card-label">Site Status</span><span class="site-card-value">{status_badge(row_dict.get('Site Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Operator</span><span class="site-card-value">{row_dict.get('Operator','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">Project Name</span><span class="site-card-value">{row_dict.get('Project Name','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">Team Name</span><span class="site-card-value">{row_dict.get('Team Name','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">PO Status</span><span class="site-card-value">{status_badge(row_dict.get('PO Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Team Billing</span><span class="site-card-value">{status_badge(row_dict.get('Team Billing Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Vision Billing</span><span class="site-card-value">{status_badge(row_dict.get('Vision Billing Status',''))}</span></div>
            """, unsafe_allow_html=True)

            if is_wh_required:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("⚙️ Manage", key=f"card_mgr_{rid}", use_container_width=True):
                        edit_record_dialog(row_dict)
                with bc2:
                    if st.button("📦 Material", key=f"card_mat_{rid}", use_container_width=True):
                        if 'mat_count' in st.session_state:
                            st.session_state.mat_count = 1
                        material_movement_dialog(row_dict)
            else:
                if st.button("⚙️ Manage (View / Edit / Delete)", key=f"card_mgr_{rid}", use_container_width=True):
                    edit_record_dialog(row_dict)

else:
    # ---------------------------------------------------------------
    # DESKTOP WIDE TABLE VIEW (unchanged spreadsheet-style, horizontal scroll)
    # ---------------------------------------------------------------
    COL_RATIOS = [
        0.3, 0.4, 0.4,               # 0-2 (Sr No, Manage, Material)
        1.2, 1.0, 1.5, 1.2, 1.2,     # 3-7 (Dept, Op, Proj Name, Proj ID, Site ID)
        1.5, 1.0, 1.2, 1.2, 1.0,     # 8-12 (Site Name, Cluster, Status, PO No, PO Date)
        1.0, 1.3, 1.0, 1.2, 2.0,     # 13-17 (PO Status, PO Upload Status, Product, RFAI, Work Desc)
        1.0, 1.2, 1.2, 1.2, 1.0,     # 18-22 (WH Mat, Team Name, Team Bill, Vis Bill, Extra App)
        1.2, 1.0                     # 23-24 (WCC Number, WCC Status)
    ]

    COL_LABELS = [
        "#", "⚙️", "📦",
        "DEPARTMENT", "OPERATOR", "PROJECT NAME", "PROJECT ID", "SITE ID", 
        "SITE NAME", "CLUSTER", "SITE STATUS", "PO NO.", "PO DATE", 
        "PO STATUS", "PO UPLOAD STATUS", "PRODUCT", "RFAI STATUS", "WORK DESCRIPTION", 
        "WH MATERIAL", "TEAM NAME", "TEAM BILLING STATUS", "VISION BILLING STATUS", "EXTRA APPROVAL", 
        "WCC NUMBER", "WCC STATUS"
    ]

    with st.container(key="site_table_wrap", height=560):
        # --- PRE-FETCH PO UPLOAD AVAILABILITY FOR CURRENT PAGE ITEMS ---
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        project_ids_on_page = [str(x).strip() for x in df_page['Project ID'].unique() if str(x).strip() and str(x).strip() != '-']
        site_ids_on_page = [str(x).strip() for x in df_page['Site ID'].unique() if str(x).strip() and str(x).strip() != '-']
        
        uploaded_po_identifiers = fetch_po_upload_identifiers_cached(active_ws) if (project_ids_on_page or site_ids_on_page) else set()

        # --- HEADER ROW ---
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)

        # --- DATA ROWS ---
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1
            is_wh_required = str(row_dict.get("WH Material", "")).strip().lower() == "required"

            proj_id_val = str(row_dict.get("Project ID", "")).strip()
            site_id_val = str(row_dict.get("Site ID", "")).strip()

            if (proj_id_val and proj_id_val in uploaded_po_identifiers) or (site_id_val and site_id_val in uploaded_po_identifiers):
                po_upload_status_html = "<span class='status-badge status-green'>Available</span>"
            else:
                po_upload_status_html = "<span class='status-badge status-yellow'>Pending</span>"

            rcols = st.columns(COL_RATIOS)

            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)

            with rcols[1]:
                if st.button("⚙️", key=f"mgrbtn_{rid}", help="Manage (View/Edit/Delete)", use_container_width=True):
                    if 'edit_po_count' in st.session_state:
                        del st.session_state['edit_po_count']
                    edit_record_dialog(row_dict)
            with rcols[2]:
                if is_wh_required:
                    if st.button("📦", key=f"mbtn_{rid}", help="Material", use_container_width=True):
                        if 'mat_count' in st.session_state:
                            st.session_state.mat_count = 1
                        material_movement_dialog(row_dict)

            rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Department','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Operator','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Project Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[7].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[8].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[9].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            rcols[10].markdown(status_badge(row_dict.get('Site Status', '')), unsafe_allow_html=True)
            rcols[11].markdown(f"<div class='tbl-cell'>{row_dict.get('PO No.','') or '-'}</div>", unsafe_allow_html=True)
            rcols[12].markdown(f"<div class='tbl-cell'>{row_dict.get('PO Date','') or '-'}</div>", unsafe_allow_html=True)
            rcols[13].markdown(status_badge(row_dict.get('PO Status', '')), unsafe_allow_html=True)
            rcols[14].markdown(po_upload_status_html, unsafe_allow_html=True)
            rcols[15].markdown(f"<div class='tbl-cell'>{row_dict.get('Product','') or '-'}</div>", unsafe_allow_html=True)
            rcols[16].markdown(status_badge(row_dict.get('RFAI Status', '')), unsafe_allow_html=True)
            rcols[17].markdown(f"<div class='tbl-cell'>{row_dict.get('Work Description','') or '-'}</div>", unsafe_allow_html=True)
            rcols[18].markdown(f"<div class='tbl-cell'>{row_dict.get('WH Material','') or '-'}</div>", unsafe_allow_html=True)
            rcols[19].markdown(f"<div class='tbl-cell'>{row_dict.get('Team Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[20].markdown(status_badge(row_dict.get('Team Billing Status', '')), unsafe_allow_html=True)
            rcols[21].markdown(status_badge(row_dict.get('Vision Billing Status', '')), unsafe_allow_html=True)
            rcols[22].markdown(f"<div class='tbl-cell'>{row_dict.get('Extra Approval','') or '-'}</div>", unsafe_allow_html=True)
            rcols[23].markdown(f"<div class='tbl-cell'>{row_dict.get('WCC Number','') or '-'}</div>", unsafe_allow_html=True)
            rcols[24].markdown(status_badge(row_dict.get('WCC Status', '')), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS (with Go-To-Page box) ---
if 'page_jump_input' not in st.session_state:
    st.session_state['page_jump_input'] = st.session_state.current_page

col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 1)):
        st.session_state.current_page -= 1
        st.session_state['page_jump_input'] = st.session_state.current_page
        st.rerun()

with col_p2:
    jc1, jc2, jc3 = st.columns([2, 1.3, 2])
    with jc2:
        page_input = st.number_input(
            "Go to page",
            min_value=1,
            max_value=total_pages,
            step=1,
            key="page_jump_input",
            label_visibility="collapsed"
        )
    st.markdown(f"<div class='page-count'>Page {st.session_state.current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
    if page_input != st.session_state.current_page:
        st.session_state.current_page = int(page_input)
        st.rerun()

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages)):
        st.session_state.current_page += 1
        st.session_state['page_jump_input'] = st.session_state.current_page
        st.rerun()
