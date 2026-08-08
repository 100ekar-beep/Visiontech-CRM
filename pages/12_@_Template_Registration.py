import streamlit as st
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Template Registration", page_icon="📝", layout="centered")

# --- LAVISH BOLD & WHITE CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); font-family: 'Inter', sans-serif; }
    
    /* ALL TEXT BOLD & WHITE */
    label, p, h1, h2, h3, li, .st-metric-label {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
    
    /* Input Boxes Text Black for Readability */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
        color: #000000 !important;
        font-weight: 700 !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}") 
        return None

supabase = init_connection()

st.markdown("<h1>📝 Interakt Template Registration</h1>", unsafe_allow_html=True)
st.markdown("---")
st.info("💡 Yaha wahi Template Name dalein jo Interakt par approved hai. Variable count me total variables likhein (Jaise agar {{1}} naam hai aur {{2}}, {{3}} message hai, toh total 3 likhein).")

with st.form("template_form", clear_on_submit=True):
    t_name = st.text_input("🔗 Template Name (Exactly as in Interakt):")
    v_count = st.number_input("🔢 Total Variables Count (e.g., 2, 3, 4):", min_value=1, max_value=10, value=2)
    
    submit_btn = st.form_submit_button("✅ Register Template")
    
    if submit_btn:
        if not t_name.strip():
            st.warning("⚠️ Kripya Template ka naam likhein.")
        elif supabase:
            try:
                # Insert into database
                supabase.table("whatsapp_templates").insert({
                    "template_name": t_name.strip(),
                    "variable_count": int(v_count)
                }).execute()
                st.success(f"🎉 Template '{t_name.strip()}' successfully register ho gaya hai!")
                st.balloons()
            except Exception as e:
                st.error(f"🚨 Error saving template: {e}")
        else:
            st.error("Database connection fail hai.")
