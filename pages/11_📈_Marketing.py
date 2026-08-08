import streamlit as st
import requests
import time
from supabase import create_client, Client
from fpdf import FPDF
import base64
from datetime import datetime, timezone, timedelta
import os

# --- PAGE CONFIGURATION (Premium UI) ---
st.set_page_config(page_title="Marketing Dashboard", page_icon="📈", layout="wide")

# --- LAVISH COLORFUL CUSTOM CSS (Including Text Area Dark Black Font Fix) ---
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
    
    /* FIX: Text Area Font Color Dark Black inside light background text box */
    div[data-testid="stTextArea"] textarea {
        color: #000000 !important;
        font-weight: 700 !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #000000 !important;
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
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Automatically register Hindi Unicode font if present in root
                font_path = "NotoSansDevanagari-VariableFont_wdth,wght.ttf"
                if os.path.exists(font_path):
                    try:
                        self.add_font("HindiFont", "", font_path, uni=True)
                        self.hindi_font_available = True
                    except Exception:
                        self.hindi_font_available = False
                else:
                    self.hindi_font_available = False

            def header(self):
                self.set_fill_color(30, 27, 75)
                self.rect(10, 10, 190, 24, 'F')
                
                # Check font availability for header
                if getattr(self, 'hindi_font_available', False):
                    self.set_font('HindiFont', 'B', 13)
                else:
                    self.set_font('Arial', 'B', 14)
                    
                self.set_text_color(56, 189, 248)
                self.set_xy(10, 13)
                self.cell(190, 8, 'WHATSAPP MARKETING CAMPAIGN REPORT', 0, 1, 'C')
                
                if getattr(self, 'hindi_font_available', False):
                    self.set_font('HindiFont', '', 9)
                else:
                    self.set_font('Arial', '', 9)
                    
                self.set_text_color(226, 232, 240)
                self.set_xy(10, 22)
                self.cell(190, 6, f'Target List: {rep["list_name"]}  |  Template: {rep["template"]}  |  Date & Time: {rep.get("timestamp", "N/A")}', 0, 1, 'C')
                self.ln(12)

            def footer(self):
                self.set_y(-15)
                if getattr(self, 'hindi_font_available', False):
                    self.set_font('HindiFont', '', 8)
                else:
                    self.set_font('Arial', 'I', 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        def generate_pdf():
            pdf = PDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Select font based on availability
            h_font = 'HindiFont' if getattr(pdf, 'hindi_font_available', False) else 'Arial'
            
            # CAMPAIGN SUMMARY METRICS CENTERED HEADING
            pdf.set_font(h_font, 'B', 12)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(190, 8, 'CAMPAIGN SUMMARY METRICS:', 0, 1, 'C')
            pdf.ln(2)
            
            # 3 Colorful Metric Boxes (Yellow, Green, Orange)
            box_width = 58
            box_height = 20
            start_x = 10
            y_pos = pdf.get_y()
            
            # Box 1: Yellow (Total Target Numbers)
            pdf.set_fill_color(254, 243, 199)
            pdf.set_draw_color(217, 119, 6)
            pdf.set_line_width(0.6)
            pdf.rect(start_x, y_pos, box_width, box_height, 'DF')
            pdf.set_xy(start_x, y_pos + 3)
            pdf.set_font(h_font, 'B', 9)
            pdf.set_text_color(180, 83, 9)
            pdf.cell(box_width, 5, 'Total Target Numbers', 0, 1, 'C')
            pdf.set_xy(start_x, y_pos + 10)
            pdf.set_font(h_font, 'B', 12)
            pdf.set_text_color(146, 64, 14)
            pdf.cell(box_width, 6, str(rep['total']), 0, 0, 'C')
            
            # Box 2: Green (Successfully Sent)
            start_x += box_width + 8
            pdf.set_fill_color(220, 252, 231)
            pdf.set_draw_color(22, 163, 74)
            pdf.rect(start_x, y_pos, box_width, box_height, 'DF')
            pdf.set_xy(start_x, y_pos + 3)
            pdf.set_font(h_font, 'B', 9)
            pdf.set_text_color(21, 128, 61)
            pdf.cell(box_width, 5, 'Successfully Sent', 0, 1, 'C')
            pdf.set_xy(start_x, y_pos + 10)
            pdf.set_font(h_font, 'B', 12)
            pdf.set_text_color(20, 83, 45)
            pdf.cell(box_width, 6, str(rep['success']), 0, 0, 'C')
            
            # Box 3: Orange (Failed)
            start_x += box_width + 8
            pdf.set_fill_color(254, 215, 170)
            pdf.set_draw_color(234, 88, 12)
            pdf.rect(start_x, y_pos, box_width, box_height, 'DF')
            pdf.set_xy(start_x, y_pos + 3)
            pdf.set_font(h_font, 'B', 9)
            pdf.set_text_color(194, 65, 12)
            pdf.cell(box_width, 5, 'Failed', 0, 1, 'C')
            pdf.set_xy(start_x, y_pos + 10)
            pdf.set_font(h_font, 'B', 12)
            pdf.set_text_color(154, 52, 18)
            pdf.cell(box_width, 6, str(rep['failed']), 0, 0, 'C')
            
            pdf.set_y(y_pos + box_height + 10)
            
            # Message Preview Section Box
            pdf.set_font(h_font, 'B', 11)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 8, 'MESSAGE SENT PREVIEW:', 0, 1, 'L')
            
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.4)
            
            msg_text = rep['message']
            if not getattr(pdf, 'hindi_font_available', False):
                msg_text = msg_text.encode('latin-1', 'replace').decode('latin-1')
                
            pdf.set_font(h_font, '', 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(190, 5, msg_text, border=1, fill=True)
            
            pdf.ln(8)
            
            # Detailed Table Heading
            pdf.set_font(h_font, 'B', 11)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 8, 'DETAILED CONTACT DELIVERY STATUS:', 0, 1, 'L')
            
            # Table Header with Vibrant Theme Colors
            pdf.set_fill_color(30, 27, 75)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font(h_font, 'B', 9)
            pdf.cell(15, 7, 'Sr', 1, 0, 'C', fill=True)
            pdf.cell(65, 7, 'Contact Name', 1, 0, 'C', fill=True)
            pdf.cell(45, 7, 'Mobile Number', 1, 0, 'C', fill=True)
            pdf.cell(65, 7, 'Delivery Status', 1, 1, 'C', fill=True)
            
            # Table Rows
            pdf.set_font(h_font, '', 9)
            for idx, item in enumerate(rep["logs"], 1):
                c_name = item["Name"]
                c_status = item["Status"]
                if not getattr(pdf, 'hindi_font_available', False):
                    c_name = c_name.encode('latin-1', 'replace').decode('latin-1')
                    c_status = c_status.encode('latin-1', 'replace').decode('latin-1')
                
                if idx % 2 == 0:
                    pdf.set_fill_color(241, 245, 249)
                else:
                    pdf.set_fill_color(255, 255, 255)
                    
                pdf.set_text_color(51, 65, 85)
                pdf.cell(15, 6, str(idx), 1, 0, 'C', fill=True)
                pdf.cell(65, 6, c_name, 1, 0, 'L', fill=True)
                pdf.cell(45, 6, str(item["Mobile"]), 1, 0, 'C', fill=True)
                pdf.cell(65, 6, c_status, 1, 1, 'L', fill=True)
                
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
