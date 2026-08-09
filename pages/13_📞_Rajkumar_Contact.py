import streamlit as st
import pandas as pd
from supabase import create_client, Client

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
tab1, tab2, tab3 = st.tabs(["📋 View, Edit & Delete", "➕ Add New Contact", "📂 Bulk Upload (.tsv)"])

# ====== TAB 1: VIEW, FILTER, EDIT & DELETE ======
with tab1:
    df_contacts = fetch_data()
    
    if not df_contacts.empty:
        # 1. Top Filters (Dropdown & Search)
        col1, col2 = st.columns(2)
        
        with col1:
            # Dropdown ke liye automatically unique list names nikalna
            unique_lists = ["All Lists"] + df_contacts['list_name'].dropna().unique().tolist()
            selected_list = st.selectbox("📂 Filter by List Name", unique_lists)
            
        with col2:
            search_query = st.text_input("🔍 Search by Name or Mobile Number", "")
        
        # 2. Filter Apply Karna
        filtered_df = df_contacts.copy()
        if selected_list != "All Lists":
            filtered_df = filtered_df[filtered_df['list_name'] == selected_list]
            
        if search_query:
            filtered_df = filtered_df[
                filtered_df['contact_name'].str.contains(search_query, case=False, na=False) |
                filtered_df['mobile_number'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        
        # Index reset karna zaruri hai taaki backend me edit/delete row sahi map ho
        filtered_df = filtered_df.reset_index(drop=True)
        
        st.markdown("---")
        st.info("💡 **Tip:** Table me kisi bhi cell par double-click karke **Edit** karein. Row **Delete** karne ke liye sabse left wale gray box ko tick karein aur table ke upar right side me **Trash (Delete) icon** dabayein.")
        
        # 3. Interactive Data Editor (Excel jaisa)
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic", # Ye row delete karne ki permission deta hai
            disabled=["id", "created_at"], # Inko edit hone se lock kar diya hai
            key="contact_editor" # Ye memory me changes save rakhega
        )
        
        # 4. Save & Download Buttons
        action_col1, action_col2 = st.columns([1.5, 3.5])
        
        with action_col1:
            # Jo bhi changes user ne table me kiye, unhe actual Supabase me save karna
            if st.button("💾 Save Database Changes", type="primary", use_container_width=True):
                editor_state = st.session_state.get("contact_editor", {})
                edited_rows = editor_state.get("edited_rows", {})
                deleted_rows = editor_state.get("deleted_rows", [])
                
                changes_made = False
                
                try:
                    # 4.1 Process Edits (Update)
                    for row_idx, changes in edited_rows.items():
                        row_id = int(filtered_df.iloc[row_idx]["id"])
                        supabase.table("whatsapp_contacts").update(changes).eq("id", row_id).execute()
                        changes_made = True
                        
                    # 4.2 Process Deletions (Delete)
                    for row_idx in deleted_rows:
                        row_id = int(filtered_df.iloc[row_idx]["id"])
                        supabase.table("whatsapp_contacts").delete().eq("id", row_id).execute()
                        changes_made = True
                        
                    if changes_made:
                        st.success("✅ Changes successfully saved to Database!")
                        st.rerun() # Page ko turant refresh karega naya data dikhane ke liye
                    else:
                        st.warning("⚠️ Koi naya change detect nahi hua. Pehle table me kuch edit karein.")
                except Exception as e:
                    st.error(f"❌ Error saving changes: {e}")
                    
        with action_col2:
            st.markdown("<br>", unsafe_allow_html=True) # UI adjust karne ke liye
            # Download Filtered Data as .tsv
            tsv_data = filtered_df.to_csv(sep='\t', index=False).encode('utf-8')
            st.download_button(
                label="📥 Download This Filtered Data (.tsv)",
                data=tsv_data,
                file_name=f"rajkumar_contacts_{selected_list}.tsv",
                mime="text/tab-separated-values"
            )
            
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
