import streamlit as st

st.set_page_config(page_title="Marketing Dashboard", page_icon="📈")

def check_password():
    """Password protection logic"""
    def password_entered():
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

# --- MAIN PAGE LOGIC ---
if check_password():
    st.title("🚀 WhatsApp Marketing Sender")
    st.markdown("---")

    # 1. Dropdown for Target List
    st.subheader("1. Select Target List")
    # Yaha aap Supabase se aayi hui list daal sakte ho
    target_lists = ["List 1 - Jaju Heights Customers", "List 2 - Indus Tower Contacts", "List 3 - New Leads"] 
    selected_list = st.selectbox("Kisko message bhejna hai?", target_lists)

    # 2. Photo / PDF Attachment (Optional)
    st.subheader("2. Attach Photo / PDF (Optional)")
    attachment = st.file_uploader("Agar koi file bhejni hai toh yaha upload karein", type=["jpg", "png", "jpeg", "pdf"])

    # 3. Interakt Template Selection
    st.subheader("3. Select Interakt Template")
    # Aapke Interakt ke templates yaha define karein
    interakt_templates = {
        "None": "",
        "Offer Template": "Hello {{1}},\n\nWe have a special offer for you regarding our new project! Please check the attached file for details.\n\nThanks,\nVisionTech Team",
        "Reminder Template": "Dear {{1}},\n\nThis is a gentle reminder regarding your pending invoice.\n\nRegards.",
        "Festive Greeting": "Hi {{1}},\n\nWishing you and your family a very Happy Festival! 🎉"
    }
    selected_template_name = st.selectbox("Template choose karein:", list(interakt_templates.keys()))

    # 4 & 5. Editable Message Box
    st.subheader("4 & 5. Edit Your Message")
    st.info("💡 Niche diye gaye box me template aa jayega. Aap chaho toh isme kuch bhi type karke edit kar sakte ho.")
    
    # Text area ka default value selected template rahega
    final_message = st.text_area(
        "Final Message Box:", 
        value=interakt_templates[selected_template_name], 
        height=150
    )

    st.markdown("---")

    # 6. Send Button
    if st.button("📤 Send Message to All", use_container_width=True):
        if not final_message.strip():
            st.warning("⚠️ Message box khali hai! Kripya kuch text likhein ya template select karein.")
        else:
            # --- API SENDING LOGIC YAHAN AAYEGA ---
            st.success(f"⏳ Sending messages to **{selected_list}**... Please wait.")
            
            # Aapke reference ke liye preview dikha raha hu
            st.write("### 📝 Message Preview:")
            st.code(final_message, language="text")
            
            if attachment:
                st.write(f"📎 **Attached File:** {attachment.name}")
            else:
                st.write("📎 **Attached File:** No attachment")
                
            # Interakt API integrate karne ke baad niche wala success message aayega
            st.balloons()
            st.success("✅ Sabhi ko message successfully send ho gaya!")
