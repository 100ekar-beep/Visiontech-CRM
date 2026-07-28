import streamlit as st
from supabase import create_client, Client

# Page Configuration
st.set_page_config(page_title="Visiontech CRM", layout="wide")

# Supabase Credentials
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

st.title("🚀 Visiontech CRM Dashboard")
st.write("Software successfully connect ho chuka hai!")

# Table Name (Supabase mein jo table banaya hai uska naam yahan likhein)
table_name = "bill_working" 

st.subheader(f"Table Data: {table_name}")

try:
    response = supabase.table(table_name).select("*").execute()
    data = response.data
    
    if data:
        st.dataframe(data)
    else:
        st.info("Table mein abhi koi data nahi hai. Aap Supabase mein data add kar sakte hain.")
except Exception as e:
    st.error(f"Error: {e}")
