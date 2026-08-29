import streamlit as st
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Template Registration", page_icon="📝", layout="centered")

# --- LAVISH BOLD & WHITE CSS (With Premium Sidebar) ---
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
    
    /* Table headers styling for better readability in dark mode */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
    }

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

# -------------------------------------------------------------
# --- EGRESS OPTIMIZATION: cached templates list fetch ---
# Chhoti table hai, par phir bhi bina caching ke har page load/rerun par
# dobara fetch ho rahi thi. Ab 30s cache kiya gaya hai, aur naya template
# register karne ke turant baad cache clear karke fresh list dikhayi
# jaati hai.
# -------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_templates_list_cached():
    fetch_response = supabase.table("whatsapp_templates").select("id, template_name, variable_count, created_at").order("id", desc=True).execute()
    return fetch_response.data

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
                fetch_templates_list_cached.clear()
            except Exception as e:
                st.error(f"🚨 Error saving template: {e}")
        else:
            st.error("Database connection fail hai.")

# --- DISPLAY REGISTERED TEMPLATES SECTION ---
st.markdown("---")
st.markdown("<h3>🗃️ Registered Templates List</h3>", unsafe_allow_html=True)

if supabase:
    try:
        # Fetching data from Supabase (cached — see fetch_templates_list_cached above), newest first
        data = fetch_templates_list_cached()
        
        if data:
            # Formatting the data for a premium table display
            formatted_data = []
            for row in data:
                formatted_data.append({
                    "ID": row.get("id"),
                    "Template Name": row.get("template_name"),
                    "Variables Count": row.get("variable_count"),
                    "Registered On": row.get("created_at")[:10] if row.get("created_at") else "N/A"
                })
            
            # Displaying as a modern interactive dataframe
            st.dataframe(formatted_data, use_container_width=True)
        else:
            st.info("💡 Abhi tak koi template database me register nahi hua hai.")
    except Exception as e:
        st.error(f"🚨 Data fetch karne me error aayi: {e}")
