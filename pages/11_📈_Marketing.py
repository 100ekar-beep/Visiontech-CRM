import streamlit as st
import requests
import time
from supabase import create_client, Client

# --- PAGE CONFIGURATION (Premium UI) ---
st.set_page_config(page_title="Marketing Dashboard", page_icon="📈", layout="wide")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Asli Error Ye Hai: {e}") 
        return None

supabase = init_connection()

# --- PASSWORD PROTECTION LOGIC ---
def check_password():
    def password_entered():
        try:
            if st.session_state["password"] == st.secrets["app"]["password"]: 
                st.session_state["password_correct"] = True
                del st.session_state["password"]  
            else:
                st.session_state["password_correct"] = False
        except Exception:
            if st.session_state["password"] == "Vision@2026": 
                st.session_state["password_correct"] = True
                del st.session_state["password"]  
            else:
                st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Restricted Access")
        st.text_input("Marketing page access karne ke liye password daalein:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Restricted Access")
        st.text_input("Marketing page access karne ke liye password daalein:", type="password", on_change=password_entered, key="password")
        st.error("😕 Password galat hai. Kripya wapas try karein.")
        return False
    else:
        return True

# ==========================================
# --- MAIN MARKETING DASHBOARD LOGIC ---
# ==========================================

if check_password():
    
    # --- SIDEBAR LOGIC ---
    with st.sidebar:
        st.markdown("### ⚙️ Quick Actions")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state["password_correct"] = False
            st.rerun()

    # Premium Header
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🚀 WhatsApp Marketing Sender</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 1. Select Target List")
        selected_list = None
        
        if supabase:
            try:
                response = supabase.table("whatsapp_contacts").select("list_name").eq("is_active", True).execute()
                unique_lists = list(set([row["list_name"] for row in response.data]))
                unique_lists.sort()
                
                if unique_lists:
                    selected_list = st.selectbox("Kisko message bhejna hai?", unique_lists)
                else:
                    st.warning("Supabase me koi contact list nahi mili. Pehle data add karein.")
            except Exception as e:
                st.error(f"Database se connect karne me error aayi: {e}")
        else:
            st.error("⚠️ Supabase connection fail. Kripya secrets.toml check karein.")

    with col2:
        # YAHAN WAPAS UPLOAD BUTTON LAGA DIYA HAI
        st.markdown("### 📎 2. Attach Photo / PDF (Optional)")
        attachment = st.file_uploader("Agar koi file bhejni hai toh yaha upload karein", type=["jpg", "png", "jpeg", "pdf"])
        st.caption("✅ Aapki file automatically internet par upload ho kar link ban jayegi.")

    st.markdown("---")

    st.markdown("### 🗂️ 3. Select Interakt Template")
    templates = ["Sample", "Text_Massage"] 
    selected_template_name = st.selectbox("Template choose karein:", templates)

    # --- CLEAR BUTTON LOGIC SETUP ---
    if "msg_key" not in st.session_state:
        st.session_state["msg_key"] = ""

    def clear_message():
        st.session_state["msg_key"] = ""

    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.markdown("### ✏️ 4 & 5. Edit Your Message")
    with head_col2:
        st.button("🧹 Clear Message", on_click=clear_message, use_container_width=True)

    st.info("💡 Niche box me wo message type karein jo **{{2}}** ki jagah jayega. **{{1}}** ki jagah Supabase list ka naam apne aap aa jayega.")

    custom_message = st.text_area(
        "Massage likhein (Ye {{2}} me set hoga):", 
        height=150,
        key="msg_key"
    )

    st.markdown("### 👁️ Final Message Preview:")
    st.caption("Aapka message WhatsApp par kuch is tarah dikhega (Example: 'Ramesh' ke liye):")

    if selected_template_name == "Sample":
        preview_msg = f"""आदरणीय Ramesh,

{custom_message}
धन्यवाद।
राजकुमार काल्या"""
    elif selected_template_name == "Text_Massage":
        preview_msg = f"""आदरणीय Ramesh,
सादर जय महेश !

{custom_message}

आपके स्नेह, सहयोग एवं आशीर्वाद की अभिलाषा में…
आपका
राजकुमार काल्याटीम त्रिभुवन काबरा"""

    st.code(preview_msg, language="text")
    st.markdown("---")

    if st.button("📤 Send Message to All", use_container_width=True, type="primary"):
        if not custom_message.strip():
            st.warning("⚠️ Message box khali hai! Kripya {{2}} ke liye kuch text likhein.")
        elif not selected_list:
            st.warning("⚠️ Kripya pehle Dropdown se List select karein.")
        else:
            st.success(f"⏳ **{selected_list}** ko messages bheje ja rahe hai... Please wait.")
            
            if supabase:
                # --- NEW AUTO-URL GENERATOR LOGIC ---
                media_url = ""
                if attachment:
                    with st.spinner("⏳ File ko Supabase par upload karke Auto-Link banaya ja raha hai..."):
                        try:
                            # Unique naam banana taaki purani file se clash na ho
                            file_ext = attachment.name.split('.')[-1]
                            unique_filename = f"{int(time.time())}.{file_ext}"
                            
                            # Supabase me upload karna
                            supabase.storage.from_("whatsapp_media").upload(
                                unique_filename,
                                attachment.getvalue(),
                                {"content-type": attachment.type}
                            )
                            # Public URL nikalna
                            media_url = supabase.storage.from_("whatsapp_media").get_public_url(unique_filename)
                            st.toast("✅ File Upload Success!")
                        except Exception as e:
                            st.error(f"🚨 File upload fail ho gaya: {e}")
                            st.warning("👉🏻 Kripya dhyaan dein: Kya aapne Supabase me 'whatsapp_media' naam ka PUBLIC bucket banaya hai?")
                            st.stop()  # Agar upload fail ho toh message bhejna rok dega

                contact_data = supabase.table("whatsapp_contacts").select("contact_name, mobile_number").eq("list_name", selected_list).eq("is_active", True).execute()
                contacts_list = contact_data.data
                
                st.write(f"Total **{len(contacts_list)}** active contacts mile.")
                
                success_count = 0
                error_count = 0

                clean_custom_message = " ".join(custom_message.split())

                for person in contacts_list:
                    name = person['contact_name']
                    number = person['mobile_number']
                    
                    payload = {
                        "countryCode": "+91",
                        "phoneNumber": number.replace("91", "", 1) if number.startswith("91") else number,
                        "type": "Template",
                        "template": {
                            "name": selected_template_name.lower(),
                            "languageCode": "hi",
                            "bodyValues": [
                                name,           
                                clean_custom_message  
                            ]
                        }
                    }
                    
                    # Agar Auto-Link ban gaya hai, toh Interakt API ko de do
                    if media_url:
                        payload["template"]["headerValues"] = [media_url]
                    
                    # --- LIVE INTERAKT API CALL ---
                    try:
                        interakt_key = st.secrets["interakt"]["api_key"]
                        headers = {
                            "Authorization": f"Basic {interakt_key}",
                            "Content-Type": "application/json"
                        }
                        api_url = "https://api.interakt.ai/v1/public/message/"
                        
                        api_response = requests.post(api_url, json=payload, headers=headers)
                        
                        if api_response.status_code in [200, 201, 202]:
                            success_count += 1
                        else:
                            error_count += 1
                            st.error(f"⚠️ {name} ko message fail hua: {api_response.text}")
                    except Exception as e:
                        error_count += 1
                        st.error(f"🚨 API Error ({name}): {e}")
                
                st.write("---")
                if success_count > 0:
                    st.balloons()
                    st.success(f"✅ {success_count} logon ko message successfully send ho gaya!")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} logon ko message nahi gaya. Upar errors check karein.")
            else:
                st.error("Database connection issue. Messages send nahi huye.")
