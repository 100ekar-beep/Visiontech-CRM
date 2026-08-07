import streamlit as st
from supabase import create_client, Client

# --- PAGE CONFIGURATION (Premium UI) ---
st.set_page_config(page_title="Marketing Dashboard", page_icon="📈", layout="wide")

# --- SUPABASE CONNECTION ---
# st.secrets se securely connect karna (pichle discussion ke anusar)
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# --- PASSWORD PROTECTION LOGIC ---
def check_password():
    """Returns `True` agar password sahi hai."""
    def password_entered():
        try:
            # Secrets setup hone par
            if st.session_state["password"] == st.secrets["app"]["password"]: 
                st.session_state["password_correct"] = True
                del st.session_state["password"]  
            else:
                st.session_state["password_correct"] = False
        except Exception:
            # Agar secrets.toml abhi setup nahi kiya, to default fallback
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
    # Premium Header
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🚀 WhatsApp Marketing Sender</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Layout ko 2 columns me baata hai premium look ke liye
    col1, col2 = st.columns([1, 1])

    with col1:
        # 1. Dropdown for Target List (Fetching from Supabase)
        st.markdown("### 📋 1. Select Target List")
        selected_list = None
        
        if supabase:
            try:
                response = supabase.table("whatsapp_contacts").select("list_name").eq("is_active", True).execute()
                # Unique lists nikalna
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
        # 2. Photo / PDF Attachment (Optional)
        st.markdown("### 📎 2. Attach Photo / PDF (Optional)")
        attachment = st.file_uploader("Agar koi file bhejni hai toh yaha upload karein", type=["jpg", "png", "jpeg", "pdf"])

    st.markdown("---")

    # 3. Select Interakt Template
    st.markdown("### 🗂️ 3. Select Interakt Template")
    templates = ["Sample"] 
    selected_template_name = st.selectbox("Template choose karein:", templates)

    # 4 & 5. Edit Your Message
    st.markdown("### ✏️ 4 & 5. Edit Your Message")
    st.info("💡 Niche box me wo message type karein jo **{{2}}** ki jagah jayega. **{{1}}** ki jagah Supabase list ka naam apne aap aa jayega.")

    custom_message = st.text_area(
        "Massage likhein (Ye {{2}} me set hoga):", 
        height=150
    )

    # --- PREVIEW SECTION ---
    st.markdown("### 👁️ Final Message Preview:")
    st.caption("Aapka message WhatsApp par kuch is tarah dikhega (Example: 'Ramesh' ke liye):")

    preview_msg = f"""आदरणीय Ramesh,

{custom_message}
धन्यवाद।
राजकुमार काल्या"""

    # Preview box design
    st.code(preview_msg, language="text")

    st.markdown("---")

    # 6. Send Button & API Logic
    # use_container_width aur type="primary" se button bada aur attractive dikhega
    if st.button("📤 Send Message to All", use_container_width=True, type="primary"):
        if not custom_message.strip():
            st.warning("⚠️ Message box khali hai! Kripya {{2}} ke liye kuch text likhein.")
        elif not selected_list:
            st.warning("⚠️ Kripya pehle Dropdown se List select karein.")
        else:
            st.success(f"⏳ **{selected_list}** ko messages bheje ja rahe hai... Please wait.")
            
            if supabase:
                # Fetch contacts strictly for the selected list
                contact_data = supabase.table("whatsapp_contacts").select("contact_name, mobile_number").eq("list_name", selected_list).eq("is_active", True).execute()
                contacts_list = contact_data.data
                
                st.write(f"Total **{len(contacts_list)}** active contacts mile.")
                
                for person in contacts_list:
                    name = person['contact_name']
                    number = person['mobile_number']
                    
                    # --- INTERAKT API PAYLOAD ---
                    payload = {
                        "countryCode": "+91",
                        "phoneNumber": number.replace("91", "", 1) if number.startswith("91") else number,
                        "type": "Template",
                        "template": {
                            "name": "Sample",
                            "languageCode": "hi",
                            "bodyValues": [
                                name,           
                                custom_message  
                            ]
                        }
                    }
                    
                    # Agar aage chalkar headerValues (attachment) add karna ho, toh yaha logic aayega
                    # if attachment:
                    #     payload["template"]["headerValues"] = [attachment_url_or_logic]
                    
                    # API Request code aayega yahan
                    # response = requests.post("...", json=payload)
                
                st.balloons()
                st.success("✅ Sabhi ko message successfully send ho gaya!")
            else:
                st.error("Database connection issue. Messages send nahi huye.")
