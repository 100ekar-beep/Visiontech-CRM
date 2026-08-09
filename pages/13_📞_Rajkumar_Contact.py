import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Rajkumar Contact", page_icon="📞", layout="wide")
st.title("📞 Rajkumar Contact Management")

# --- SUPABASE SECRETS CONNECTION ---
@st.cache_resource
def get_supabase_client():
    try:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase Secrets fetch karne me error: {e}")
        st.stop()

supabase = get_supabase_client()

# --- FETCH DATA FUNCTION ---
def fetch_data():
    try:
        response = supabase.table("whatsapp_contacts").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return pd.DataFrame()

# --- MAIN UI LAYOUT (TABS) ---
tab1, tab2, tab3 = st.tabs(["📋 View & Search", "➕ Add New Contact", "📂 Bulk Upload (.tsv)"])

# ====== TAB 1: VIEW, SEARCH & DOWNLOAD ======
with tab1:
    df_contacts = fetch_data()
    
    if not df_contacts.empty:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("🔍 Search by Name or Mobile Number", "")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            # TSV Format me download
            tsv_data = df_contacts.to_csv(sep='\t', index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data (.tsv)",
                data=tsv_data,
                file_name="rajkumar_contacts.tsv",
                mime="text/tab-separated-values"
            )
        
        # Search Filter Logic
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
            list_name = st.text_input("List Name (e.g., Template Name / Group)")
            contact_name = st.text_input("Contact Name")
        with col2:
            mobile_number = st.text_input("Mobile Number (with country code, eg: 919876543210)")
            is_active = st.checkbox("Is Active?", value=True)
            
        submit_btn = st.form_submit_button("Save Contact")
        
        if submit_btn:
            if contact_name and mobile_number and list_name:
                new_data = {
                    "list_name": list_name,
                    "contact_name": contact_name,
                    "mobile_number": mobile_number,
                    "is_active": is_active
                }
                try:
                    supabase.table("whatsapp_contacts").insert(new_data).execute()
                    st.success("✅ Contact successfully add ho gaya!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("⚠️ List Name, Contact Name aur Mobile Number mandatory hain.")

# ====== TAB 3: BULK UPLOAD (.tsv) ======
with tab3:
    st.subheader("Bulk Upload Contacts (.tsv File Only)")
    
    bulk_list_name = st.text_input("Is poori file ke liye List Name (Template Name) set karein:")
    
    uploaded_file = st.file_uploader("Upload your .tsv file here", type=['tsv'])
    
    if uploaded_file is not None and bulk_list_name:
        try:
            # Strictly parsing .tsv file as requested
            df_upload = pd.read_csv(uploaded_file, sep='\t')
            df_upload = df_upload.fillna(value="")
            
            df_upload['list_name'] = bulk_list_name
            if 'is_active' not in df_upload.columns:
                df_upload['is_active'] = True
                
            if 'contact_name' not in df_upload.columns or 'mobile_number' not in df_upload.columns:
                st.error("Aapki .tsv file me 'contact_name' aur 'mobile_number' column headings hona zaruri hai.")
            else:
                st.write("File Preview:")
                st.dataframe(df_upload[['list_name', 'contact_name', 'mobile_number', 'is_active']].head(5))
                
                if st.button("Upload to Database"):
                    final_data = df_upload[['list_name', 'contact_name', 'mobile_number', 'is_active']].to_dict(orient="records")
                    supabase.table("whatsapp_contacts").insert(final_data).execute()
                    st.success(f"✅ Success! Total {len(final_data)} contacts upload ho gaye.")
                    
        except Exception as e:
            st.error(f"❌ Upload me error aayi. Ensure file .tsv format me ho. Error: {e}")
    elif uploaded_file is not None and not bulk_list_name:
        st.warning("⚠️ Pehle upar 'List Name' daalein, uske baad hi file upload ka button aayega.")
