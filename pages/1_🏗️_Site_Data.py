import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Page Configuration
st.set_page_config(
    page_title="Site Data Management",
    page_icon="🏗️",
    layout="wide"
)

# Custom Styling for Site Data Page
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .sub-text {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏗️ Site Data Management Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Yahan aapke saare sites ka live database records display hoga.</div>', unsafe_allow_html=True)

# Supabase Credentials
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# Table name (Agar aapka table ka naam 'site_data' hai ya kuch aur, toh yahan change kar sakte hain)
table_name = "site_data" 

try:
    # Supabase se data fetch karna
    response = supabase.table(table_name).select("*").execute()
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        
        # Search / Filter Bar
        search_query = st.text_input("🔍 Search Site / Client Name:", "")
        if search_query:
            # Flexible search across text columns
            text_cols = df.select_dtypes(include=['object']).columns
            mask = df[text_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
            df = df[mask]
            
        st.markdown(f"**Total Records Found:** {len(df)}")
        
        # Display Lavish Dataframe Table
        st.dataframe(df, use_container_width=True, height=450)
        
    else:
        st.info(f"ℹ️ `{table_name}` table mein abhi koi data nahi hai. Aap pehle Supabase mein is table mein data add karein.")
        
        # Agar table nahi hai ya data add karna hai toh guide
        with st.expander("🛠️ Table Setup Guide"):
            st.write(f"Ensure karein ki Supabase mein **{table_name}** naam ka table bana hua hai.")

except Exception as e:
    st.error(f"⚠️ Database connection ya query mein error aaya: {e}")
