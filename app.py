import streamlit as st
import streamlit.components.v1 as components
import json
import hashlib

st.set_page_config(
    page_title="Visiontech CRM",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================
# --- 1. CREDENTIALS (username -> password + fixed workspace) ---
# ==============================================================
# NOTE: Production me ye plaintext dict st.secrets me rakhna better hoga
# (Settings > Secrets on Streamlit Cloud, ya .streamlit/secrets.toml locally).
# Abhi ke liye simple rakha hai taaki aap seedha copy-paste karke use kar sakein.
USERS = {
    "vispl":        {"password": "Vispl@2024",       "workspace": "VISPL"},
    "bhagyashree":  {"password": "Bhagya@2024",       "workspace": "BHAGYASHREE"},
    "rajkumar":     {"password": "Rajkumar@2024",     "workspace": "RAJKUMAR KALYA"},
    "saitele":      {"password": "Saitele@2024",      "workspace": "SAI TELE SERVICES"},
    "bhajan":       {"password": "Bhajan@2024",       "workspace": "BHAJAN"},
}

SECRET_SALT = "visiontech-crm-static-salt-change-me"  # isse bhi change kar dein apni marzi se

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

# Precompute hashed lookup (password kabhi bhi plain compare nahi hota)
USERS_HASHED = {
    uname: {"password_hash": _hash(u["password"]), "workspace": u["workspace"]}
    for uname, u in USERS.items()
}

def _make_token(username: str, password_hash: str) -> str:
    # Ye token URL (query_params) me store hoga taaki refresh/reconnect pe login persist rahe.
    # Password khud kabhi URL me nahi jaata, sirf iska derived hash-of-hash jaata hai.
    return _hash(f"{username}:{password_hash}:{SECRET_SALT}")


# ==============================================================
# --- 2. RESTORE SESSION FROM URL TOKEN (refresh-safe login) ---
# ==============================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

    _q_user = st.query_params.get("u", None)
    _q_token = st.query_params.get("token", None)

    if _q_user and _q_token and _q_user in USERS_HASHED:
        _expected_token = _make_token(_q_user, USERS_HASHED[_q_user]["password_hash"])
        if _q_token == _expected_token:
            st.session_state["logged_in"] = True
            st.session_state["username"] = _q_user
            st.session_state["active_workspace"] = USERS_HASHED[_q_user]["workspace"]


# ==============================================================
# --- 3. GLOBAL CSS (same premium look, unchanged) ---
# ==============================================================
st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }

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

    div[data-baseweb="select"] * { font-weight: 800 !important; }

    .dash-card { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: white; border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; margin-top: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); border-left: 5px solid #3b82f6;}
    .dash-card h2, .dash-card p { color: white !important; }

    .login-box { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-radius: 16px; padding: 2rem; border: 1px solid rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)


# ==============================================================
# --- 4. LOGIN GATE ---
# ==============================================================
if not st.session_state["logged_in"]:

    st.markdown("""
        <div style="padding: 2.5rem; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); border-radius: 16px; text-align: center; color: white;">
            <h1>⚡ Visiontech CRM⚡</h1>
            <p style="font-size: 1.1rem; margin-top: 10px;">Apne company login se sign in karein.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _c1, _c2, _c3 = st.columns([1, 1, 1])
    with _c2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 🔐 Login")
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            uname = username_input.strip().lower()
            user = USERS_HASHED.get(uname)
            if user and _hash(password_input) == user["password_hash"]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = uname
                st.session_state["active_workspace"] = user["workspace"]

                # URL me refresh-safe token save karo
                st.query_params["u"] = uname
                st.query_params["token"] = _make_token(uname, user["password_hash"])
                st.rerun()
            else:
                st.error("❌ Galat Username ya Password")
        st.markdown('</div>', unsafe_allow_html=True)

    # Login nahi hua to sidebar ke saare pages hide kar do (sirf UI-level;
    # asli security har page ke andar ke check se milegi — neeche note dekhein)
    components.html("""
    <script>
    function hideAllNav() {
        const navLinks = window.parent.document.querySelectorAll('[data-testid="stSidebarNav"] a');
        navLinks.forEach(function(link) { link.style.display = "none"; });
    }
    hideAllNav();
    const navContainer = window.parent.document.querySelector('[data-testid="stSidebarNav"]');
    if (navContainer) {
        const observer = new MutationObserver(hideAllNav);
        observer.observe(navContainer, { childList: true, subtree: true });
    }
    setInterval(hideAllNav, 400);
    </script>
    """, height=0)

    st.stop()  # Login hone tak neeche ka dashboard code bilkul nahi chalega


# ==============================================================
# --- 5. LOGGED IN: DASHBOARD (workspace login se hi fix hai) ---
# ==============================================================
_active_ws = st.session_state["active_workspace"]

st.markdown(f"""
    <div style="padding: 2.5rem; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); border-radius: 16px; text-align: center; color: white;">
        <h1>⚡ Visiontech CRM⚡</h1>
        <p style="font-size: 1.1rem; margin-top: 10px;">Workspace: <b>{_active_ws}</b> | User: <b>{st.session_state['username']}</b></p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.success(f"✅ Aap **{_active_ws}** workspace me login hain. Sirf isi company ka data yahan dikhega.")

# --- Sidebar: user info + logout ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['username']}")
    st.markdown(f"🏢 **{_active_ws}**")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    st.markdown("---")

st.markdown("<br>", unsafe_allow_html=True)

# --- Dashboard card (workspace ke hisaab se) ---
_DASHBOARD_CONTENT = {
    "RAJKUMAR KALYA": ("📱 Personal Marketing Zone",
        "Welcome! Ye aapka personal aur fully isolated workspace hai. Yahan se aap apne WhatsApp campaigns aur Interakt templates manage kar sakte hain.",
        "👈 Kripya sidebar se <b>Marketing</b> ya <b>Template Registration</b> select karein."),
    "VISPL": ("🚀 VISPL Enterprise Operations",
        "Welcome to VISPL Workspace! Yahan aap apne saare bills, quotations, POs aur site data ko securely manage kar sakte hain.",
        "👈 Kripya sidebar se apne desired business modules select karein."),
    "BHAGYASHREE": ("🏗️ BHAGYASHREE Management",
        "Welcome to Bhagyashree Workspace! Yahan aapki property aur construction ventures ka saara record secure rakha gaya hai.",
        "👈 Kripya sidebar se apne desired business modules select karein."),
    "SAI TELE SERVICES": ("📡 SAI TELE SERVICES Operations",
        "Welcome to Sai Tele Services Workspace! Yahan aap apne saare bills, quotations, POs aur service data ko securely manage kar sakte hain.",
        "👈 Kripya sidebar se apne desired business modules select karein."),
    "BHAJAN": ("🪔 BHAJAN SANGRAH",
        "Welcome to Bhajan Workspace! Yahan aap category-wise bhajan save, search, PDF download aur WhatsApp share kar sakte hain.",
        "👈 Kripya sidebar se <b>Bhajan</b> page select karein."),
}

_title, _desc, _hint = _DASHBOARD_CONTENT[_active_ws]
st.markdown(f"""
<div class="dash-card">
    <h2>{_title}</h2>
    <p>{_desc}</p>
    <p style="color: #38bdf8 !important;">{_hint}</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================
# --- 6. SIDEBAR PAGE FILTER (workspace login se locked, no manual switch) ---
# ==============================================================
RAJKUMAR_PAGES = ["Marketing", "Rajkumar Contact"]
BHAJAN_PAGES = ["Bhajan"]

if _active_ws == "BHAJAN":
    _allowed_pages = BHAJAN_PAGES
    _mode = "whitelist"
elif _active_ws == "RAJKUMAR KALYA":
    _allowed_pages = RAJKUMAR_PAGES
    _mode = "whitelist"
else:
    _allowed_pages = RAJKUMAR_PAGES + BHAJAN_PAGES
    _mode = "blacklist"

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
