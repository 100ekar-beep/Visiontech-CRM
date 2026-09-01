import streamlit as st
import bcrypt
from supabase import create_client, Client

st.set_page_config(page_title="Add User", page_icon="👤", layout="wide")

# --- ADMIN-ONLY GATE ---
if not st.session_state.get('logged_in', False):
    st.error("🚫 Please login first from the Home page.")
    st.stop()

if not st.session_state.get('is_admin', False):
    st.error("🚫 Access Restricted! Sirf Admin ye page dekh sakta hai.")
    st.stop()

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("👤 Add / Manage Ground Team User")

# --- FETCH TEAM NAMES FROM dropdown_master ---
@st.cache_data(ttl=30)
def get_team_names():
    res = supabase.table("dropdown_master").select("*").eq("category", "Team Name").execute()
    return res.data or []

teams = get_team_names()
team_options = ["Select"] + [t["option_value"] for t in teams]

# --- LIST OF ALL AVAILABLE PAGES ---
ALL_PAGES = [
    "Pending Task", "Site Data", "Solar Project", "Invoice Management",
    "Warehouse", "PO Working", "Quotation", "MRN GRN", "Team Billing",
    "Indus Site Data", "STN Detail", "SRN Detail", "Master Data",
    "Quotation Template", "Marketing", "Template Registration",
    "Rajkumar Contact", "Bhajan"
]

st.markdown("### ➕ Create New User")

with st.form("add_user_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        selected_team = st.selectbox("Team Name (dropdown_master se)", team_options)
        mobile_number = st.text_input("Mobile Number (Login ID)", placeholder="10 digit mobile number")
    with c2:
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name (optional)", value="")

    st.markdown("**Allowed Pages** (sirf ye pages is user ko dikhenge)")
    allowed_pages = st.multiselect("Select Pages", ALL_PAGES)

    submitted = st.form_submit_button("💾 Create User", type="primary", use_container_width=True)

    if submitted:
        errors = []
        if selected_team == "Select":
            errors.append("Team Name select karo")
        if not mobile_number or not mobile_number.isdigit() or len(mobile_number) != 10:
            errors.append("Mobile Number 10 digit ka valid number hona chahiye")
        if not password or len(password) < 4:
            errors.append("Password kam se kam 4 characters ka hona chahiye")
        if not allowed_pages:
            errors.append("Kam se kam 1 page select karo")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            try:
                existing = supabase.table("app_users").select("id").eq("mobile_number", mobile_number).execute()
                if existing.data:
                    st.error("❌ Ye mobile number already registered hai!")
                else:
                    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table("app_users").insert({
                        "mobile_number": mobile_number,
                        "password_hash": hashed_pw,
                        "full_name": full_name if full_name else selected_team,
                        "allowed_pages": allowed_pages,
                        "is_admin": False
                    }).execute()
                    st.success(f"✅ User successfully created for team '{selected_team}'!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.markdown("---")
st.markdown("### 📋 Existing Users")

try:
    all_users = supabase.table("app_users").select("*").execute().data or []
    if all_users:
        for u in all_users:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{u.get('full_name', 'N/A')}** — {u.get('mobile_number')}")
                with col2:
                    st.write(f"Pages: {', '.join(u.get('allowed_pages', []))}")
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{u['id']}"):
                        supabase.table("app_users").delete().eq("id", u['id']).execute()
                        st.rerun()
    else:
        st.info("Abhi koi user nahi bana hai.")
except Exception as e:
    st.error(f"Error loading users: {e}")
