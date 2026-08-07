import streamlit as st

# ... (Upar ka password wala aur database fetch wala code same rahega) ...

st.subheader("3. Select Interakt Template")
# Yaha template ka exact naam daalna hai jo Interakt me approve hua hai
templates = ["Sample"] 
selected_template_name = st.selectbox("Template choose karein:", templates)

st.subheader("4 & 5. Edit Your Message")
st.info("💡 Niche box me wo message type karein jo **{{2}}** ki jagah jayega. **{{1}}** ki jagah Supabase list ka naam apne aap aa jayega.")

# Yaha aap sirf {{2}} ka message type karoge
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

st.code(preview_msg, language="text")

st.markdown("---")

# 6. Send Button & API Logic
if st.button("📤 Send Message to All", use_container_width=True):
    if not custom_message.strip():
        st.warning("⚠️ Message box khali hai! Kripya {{2}} ke liye kuch text likhein.")
    else:
        st.success("⏳ Messages bheje ja rahe hai... Please wait.")
        
        # Yahan hum maan lete hai 'contacts_list' aapne Supabase se fetch kar li hai
        # Example dummy list:
        contacts_list = [
            {"contact_name": "Ramesh Kumar", "mobile_number": "919876543210"},
            {"contact_name": "Suresh Verma", "mobile_number": "919876543211"}
        ]
        
        for person in contacts_list:
            name = person['contact_name']
            number = person['mobile_number']
            
            # --- INTERAKT API PAYLOAD KAISE BANEGA ---
            # Aapko Python requests library se ye data bhejna hoga:
            
            payload = {
                "countryCode": "+91",
                "phoneNumber": number.replace("91", "", 1), # Starting ka 91 hata ke, kyuki Interakt me country code alag se jata hai
                "type": "Template",
                "template": {
                    "name": "Sample", # Aapka template naam
                    "languageCode": "hi", # Hindi ke liye 'hi', English ke liye 'en'
                    "bodyValues": [
                        name,           # {{1}} ki jagah naam jayega
                        custom_message  # {{2}} ki jagah aapka text box ka message jayega
                    ]
                }
            }
            
            # Request bhejne ka code (jab aap API integrate karoge):
            # headers = {"Authorization": "Basic YOUR_API_KEY"}
            # response = requests.post("https://api.interakt.ai/v1/public/message/", json=payload, headers=headers)
            
        st.balloons()
        st.success("✅ Sabhi ko message successfully send ho gaya!")
