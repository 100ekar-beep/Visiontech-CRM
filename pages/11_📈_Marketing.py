import streamlit as st
import requests
import time
from supabase import create_client, Client
from fpdf import FPDF
import base64
from datetime import datetime, timezone, timedelta

# --- PAGE CONFIGURATION (Premium UI) ---
st.set_page_config(page_title="Marketing Dashboard", page_icon="📈", layout="wide")

# --- LAVISH COLORFUL CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Top Action Buttons & Primary Buttons Styling */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    /* Colorful Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
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

    # Premium Colorful Header with Top Clear Button Option
    head_title_col, head_btn_col = st.columns([5, 1])
    with head_title_col:
        st.markdown("<h1 style='text-align: left; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>🚀 WhatsApp Marketing Sender</h1>", unsafe_allow_html=True)
    with head_btn_col:
        if st.button("🧹 Clear Page", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                if key != "password_correct":
                    del st.session_state[key]
            st.rerun()

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
        st.markdown("### 📎 2. Attach Photo / PDF (Optional)")
        attachment = st.file_uploader("Agar koi file bhejni hai toh yaha upload karein", type=["jpg", "png", "jpeg", "pdf"])
        st.caption("✅ Aapki file automatically internet par upload ho kar link ban jayegi.")

    st.markdown("---")

    st.markdown("### 🗂️ 3. Select Interakt Template")
    templates = ["Sample", "Text_Massage"] 
    selected_template_name = st.selectbox("Template choose karein:", templates)

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
            # IST (Indian Standard Time, UTC+5:30) Accurate Timestamp
            ist_offset = timezone(timedelta(hours=5, minutes=30))
            current_dt_str = datetime.now(ist_offset).strftime("%d-%m-%Y %H:%M:%S")
            st.success(f"⏳ **{selected_list}** ko messages bheje ja rahe hai... ({current_dt_str}) Please wait.")
            
            if supabase:
                media_url = ""
                if attachment:
                    with st.spinner("⏳ File ko Supabase par upload karke Auto-Link banaya ja raha hai..."):
                        try:
                            file_ext = attachment.name.split('.')[-1]
                            unique_filename = f"{int(time.time())}.{file_ext}"
                            
                            supabase.storage.from_("whatsapp_media").upload(
                                unique_filename,
                                attachment.getvalue(),
                                {"content-type": attachment.type}
                            )
                            media_url = supabase.storage.from_("whatsapp_media").get_public_url(unique_filename)
                            st.toast("✅ File Upload Success!")
                        except Exception as e:
                            st.error(f"🚨 File upload fail ho gaya: {e}")
                            st.warning("👉🏻 Kripya dhyaan dein: Kya aapne Supabase me 'whatsapp_media' naam ka PUBLIC bucket banaya hai?")
                            st.stop()

                contact_data = supabase.table("whatsapp_contacts").select("contact_name, mobile_number").eq("list_name", selected_list).eq("is_active", True).execute()
                contacts_list = contact_data.data
                
                st.write(f"Total **{len(contacts_list)}** active contacts mile.")
                
                success_count = 0
                error_count = 0
                report_logs = []

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
                    
                    if media_url:
                        payload["template"]["headerValues"] = [media_url]
                    
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
                            report_logs.append({"Name": name, "Mobile": number, "Status": "Send Successfully"})
                        else:
                            error_count += 1
                            err_msg = api_response.json().get("message", api_response.text) if api_response.content else "Failed"
                            report_logs.append({"Name": name, "Mobile": number, "Status": f"Failed: {err_msg}"})
                    except Exception as e:
                        error_count += 1
                        report_logs.append({"Name": name, "Mobile": number, "Status": f"Error: {str(e)}"})
                
                st.session_state["last_report"] = {
                    "list_name": selected_list,
                    "template": selected_template_name,
                    "message": preview_msg,
                    "timestamp": current_dt_str,
                    "total": len(contacts_list),
                    "success": success_count,
                    "failed": error_count,
                    "logs": report_logs
                }

                st.write("---")
                if success_count > 0:
                    st.balloons()
                    st.success(f"✅ {success_count} logon ko message successfully send ho gaya!")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} logon ko message nahi gaya. Upar errors check karein.")
            else:
                st.error("Database connection issue. Messages send nahi huye.")

    # ==========================================
    # --- REPORT & METRICS SECTION ---
    # ==========================================
    if "last_report" in st.session_state:
        rep = st.session_state["last_report"]
        
        st.markdown("---")
        st.markdown("<h2>📊 Live Campaign Execution Report</h2>", unsafe_allow_html=True)
        st.markdown(f"**Execution Date & Time:** {rep.get('timestamp', 'N/A')}")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric(label="📱 Total Numbers Targeted", value=rep["total"])
        with m_col2:
            st.metric(label="✅ Successfully Sent", value=rep["success"])
        with m_col3:
            st.metric(label="❌ Failed", value=rep["failed"])
            
        st.markdown("### 📝 Detailed Status Table:")
        
        table_data = []
        for idx, item in enumerate(rep["logs"], 1):
            table_data.append({
                "Sr No": idx,
                "Contact Name": item["Name"],
                "Mobile Number": item["Mobile"],
                "Delivery Status": item["Status"]
            })
            
        st.dataframe(table_data, use_container_width=True)
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'WhatsApp Marketing Campaign Report', 0, 1, 'C')
                self.set_font('Arial', '', 10)
                self.cell(0, 6, f'Target List: {rep["list_name"]} | Template: {rep["template"]}', 0, 1, 'C')
                self.cell(0, 6, f'Date & Time: {rep.get("timestamp", "N/A")}', 0, 1, 'C')
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        def generate_pdf():
            pdf = PDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Campaign Summary:', 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, f"Execution Time: {rep.get('timestamp', 'N/A')}", 0, 1)
            pdf.cell(0, 6, f"Total Target Numbers: {rep['total']}", 0, 1)
            pdf.cell(0, 6, f"Successfully Sent: {rep['success']}", 0, 1)
            pdf.cell(0, 6, f"Failed: {rep['failed']}", 0, 1)
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Message Sent Preview:', 0, 1)
            pdf.set_font('Arial', '', 9)
            
            # Using exact original Hindi text encoded safely without transliteration loss
            safe_msg = rep['message'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, safe_msg)
            pdf.ln(8)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Detailed Contact Delivery Status:', 0, 1)
            
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(15, 7, 'Sr', 1, 0, 'C')
            pdf.cell(60, 7, 'Contact Name', 1, 0, 'C')
            pdf.cell(40, 7, 'Mobile', 1, 0, 'C')
            pdf.cell(75, 7, 'Status', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 9)
            for idx, item in enumerate(rep["logs"], 1):
                safe_name = item["Name"].encode('latin-1', 'replace').decode('latin-1')
                safe_status = item["Status"].encode('latin-1', 'replace').decode('latin-1')
                
                pdf.cell(15, 6, str(idx), 1, 0, 'C')
                pdf.cell(60, 6, safe_name, 1, 0, 'L')
                pdf.cell(40, 6, str(item["Mobile"]), 1, 0, 'C')
                pdf.cell(75, 6, safe_status, 1, 1, 'L')
                
            return pdf.output(dest='S').encode('latin1')

        pdf_bytes = generate_pdf()
        
        st.markdown("---")
        st.download_button(
            label="📥 Download Professional PDF Report for Client",
            data=pdf_bytes,
            file_name=f"WhatsApp_Report_{rep['list_name']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
