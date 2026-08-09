import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Rajkumar Contact", page_icon="📞", layout="wide")

st.title("📞 Rajkumar Contact Management")

# --- 2. SUPABASE CONNECTION ---
# Yahan apni Supabase details daalein (Ya agar app.py se session state me hai to wahan se call karein)
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# --- 3. FETCH DATA FUNCTION ---
def fetch_data():
    try:
        response = supabase.table("whatsapp_contacts").select("*").order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Data fetch karne me error: {e}")
        return pd.DataFrame()

# --- 4. MAIN UI LAYOUT (TABS) ---
tab1, tab2, tab3 = st.tabs(["📋 View & Search Contacts", "➕ Add New Contact", "📂 Bulk Upload (.tsv)"])

# ====== TAB 1: VIEW, SEARCH & DOWNLOAD ======
with tab1:
    df_contacts = fetch_data()
    
    if not df_contacts.empty:
        col1, col2 = st.columns([3, 1])
        
        # Search Box
        with col1:
            search_query = st.text_input("🔍 Search by Name or Mobile Number", "")
        
        # Download Button (.tsv format)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True) # thoda spacing ke liye
            tsv_data = df_contacts.to_csv(sep='\t', index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data (.tsv)",
                data=tsv_data,
                file_name="rajkumar_contacts.tsv",
                mime="text/tab-separated-values"
            )
        
        # Filter Logic
        if search_query:
            filtered_df = df_contacts[
                df_contacts['contact_name'].str.contains(search_query, case=False, na=False) |
                df_contacts['mobile_number'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = df_contacts
            
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi table me koi data nahi hai.")

# ====== TAB 2: ADD SINGLE CONTACT ======
with tab2:
    st.subheader("Add a Single Contact")
    with st.form("add_single_contact_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            list_name = st.text_input("List Name (e.g., Personal Testing)")
            contact_name = st.text_input("Contact Name")
        with col2:
            mobile_number = st.text_input("Mobile Number (with country code, no +)")
            is_active = st.checkbox("Is Active?", value=True)
            
        submit_btn = st.form_submit_button("Save Contact")
        
        if submit_btn:
            if contact_name and mobile_number:
                new_data = {
                    "list_name": list_name,
                    "contact_name": contact_name,
                    "mobile_number": mobile_number,
                    "is_active": is_active
                }
                try:
                    supabase.table("whatsapp_contacts").insert(new_data).execute()
                    st.success("✅ Contact successfully add ho gaya!")
                    st.rerun() # Page refresh karke table update karne ke liye
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("⚠️ Contact Name aur Mobile Number mandatory hain.")

# ====== TAB 3: BULK UPLOAD (.tsv) ======
with tab3:
    st.subheader("Bulk Upload Contacts (.tsv File Only)")
    st.info("Aapki .tsv file me headings hone chahiye: `list_name`, `contact_name`, `mobile_number`, `is_active`")
    
    uploaded_file = st.file_uploader("Upload your .tsv file here", type=['tsv'])
    
    if uploaded_file is not None:
        try:
            # Strictly parsing .tsv file
            df_upload = pd.read_csv(uploaded_file, sep='\t')
            df_upload = df_upload.fillna(value="")
            
            st.write("File Preview:")
            st.dataframe(df_upload.head(5)) # Start ke 5 rows preview ke liye
            
            if st.button("Upload to Database"):
                data_to_insert = df_upload.to_dict(orient="records")
                supabase.table("whatsapp_contacts").insert(data_to_insert).execute()
                st.success(f"✅ Success! Total {len(data_to_insert)} contacts upload ho gaye.")
                
        except Exception as e:
            st.error(f"❌ Upload me kuch error aayi. Check karein file sahi format me hai ya nahi. Error: {e}")
