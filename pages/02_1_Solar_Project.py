import streamlit as st
import pandas as pd
import math
import io
import datetime
import os
from collections import defaultdict
from supabase import create_client, Client
from st_keyup import st_keyup

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Solar Project Hub", page_icon="☀️", layout="wide")

# --- INIT SESSION STATE ---
if 'solar_current_page' not in st.session_state:
    st.session_state.solar_current_page = 1

# --- 2. CSS (premium dark theme) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%);
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
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important; font-weight: 800 !important;
    }

    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #ffffff !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p {
        color: #e2e8f0 !important;
    }
    .modal-section-title {
        color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;
        margin-top: 15px; margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 5px;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important; font-weight: 700 !important; -webkit-text-fill-color: #000000 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important;
        font-weight: 600 !important; font-size: 1.05rem !important; transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; display: flex !important;
        align-items: center !important; gap: 12px !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important; transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important; color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%) !important;
        color: #ffffff !important; border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* Tabs styling - target button elements directly for maximum compatibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        border-bottom: none !important;
        background: transparent !important;
        padding: 4px 0 16px 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(236,72,153,0.18) 100%) !important;
        border-radius: 12px !important;
        padding: 14px 26px !important;
        border: 1.5px solid rgba(255,255,255,0.18) !important;
        height: auto !important;
        margin: 0 !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25) !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background: linear-gradient(135deg, rgba(99,102,241,0.35) 0%, rgba(236,72,153,0.35) 100%) !important;
        border-color: rgba(255,255,255,0.35) !important;
        transform: translateY(-2px) !important;
    }
    .stTabs [data-baseweb="tab-list"] button * {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.02rem !important;
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%) !important;
        border-color: transparent !important;
        box-shadow: 0 6px 18px rgba(245, 158, 11, 0.5) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* Summary cards */
    .solar-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px 18px;
        text-align: center;
    }
    .solar-card .label { color: #94a3b8; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; }
    .solar-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 900; margin-top: 6px; }
    .solar-card .value-green { color: #4ade80; font-size: 1.5rem; font-weight: 900; margin-top: 6px; }
    .solar-card .value-red { color: #f87171; font-size: 1.5rem; font-weight: 900; margin-top: 6px; }

    /* Generic table wraps (sites / ledger / payments / site-ledger all reuse this) */
    .st-key-solar_table_wrap, .st-key-ledger_table_wrap, .st-key-payments_table_wrap, .st-key-site_ledger_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important;
    }
    .st-key-solar_table_wrap div[data-testid="stHorizontalBlock"],
    .st-key-ledger_table_wrap div[data-testid="stHorizontalBlock"],
    .st-key-payments_table_wrap div[data-testid="stHorizontalBlock"],
    .st-key-site_ledger_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1900px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-ledger_table_wrap div[data-testid="stHorizontalBlock"] { min-width: 1500px !important; }
    .st-key-payments_table_wrap div[data-testid="stHorizontalBlock"] { min-width: 1200px !important; }
    .st-key-solar_table_wrap div[data-testid="stHorizontalBlock"]:hover,
    .st-key-ledger_table_wrap div[data-testid="stHorizontalBlock"]:hover,
    .st-key-payments_table_wrap div[data-testid="stHorizontalBlock"]:hover,
    .st-key-site_ledger_table_wrap div[data-testid="stHorizontalBlock"]:hover { background: rgba(255,255,255,0.04); }
    .st-key-solar_table_wrap div[data-testid="column"],
    .st-key-ledger_table_wrap div[data-testid="column"],
    .st-key-payments_table_wrap div[data-testid="column"],
    .st-key-site_ledger_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; display: flex; align-items: center; justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-solar_table_wrap div[data-testid="column"]:last-child,
    .st-key-ledger_table_wrap div[data-testid="column"]:last-child,
    .st-key-payments_table_wrap div[data-testid="column"]:last-child,
    .st-key-site_ledger_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .tbl-head {
        background: transparent; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px;
        color: #94a3b8; text-transform: uppercase; white-space: nowrap !important;
    }
    .tbl-cell {
        color: #e2e8f0; font-size: 0.86rem; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    .tbl-serial { color: #64748b; font-size: 0.85rem; font-weight: 800; }
    .tbl-cell.team-name { font-weight: 800; color: #f59e0b; }
    .tbl-cell.paid-amt { color: #4ade80; font-weight: 800; }
    .tbl-cell.pending-amt { color: #f87171; font-weight: 800; }

    .st-key-solar_table_wrap button, .st-key-ledger_table_wrap button, .st-key-payments_table_wrap button {
        height: 32px !important; width: 100% !important; max-width: 40px !important; padding: 0 !important;
        min-height: 0 !important; border-radius: 6px !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
        background: rgba(245,158,11,0.15) !important; border: 1px solid rgba(245,158,11,0.35) !important;
        margin: 0 auto !important; box-shadow: none !important; cursor: pointer !important;
    }
    .st-key-solar_table_wrap button:hover, .st-key-ledger_table_wrap button:hover, .st-key-payments_table_wrap button:hover {
        background: #f59e0b !important; border-color: #fbbf24 !important; transform: translateY(-2px) !important;
    }
    .st-key-payments_table_wrap div[class*="st-key-delpay_"] button {
        background: rgba(239,68,68,0.15) !important; border: 1px solid rgba(239,68,68,0.35) !important;
    }
    .st-key-payments_table_wrap div[class*="st-key-delpay_"] button:hover {
        background: #ef4444 !important; border-color: #f87171 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

def get_simple_opts(category, all_data, fallback):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return opts if opts else fallback

def num(v):
    try:
        return float(v) if v not in (None, "", "None") else 0.0
    except Exception:
        return 0.0

# --- 4. MANAGE TEAMS DIALOG (amount-only, no payment status) ---
@st.dialog("⚙️ Manage Solar Teams & Charges", width="large")
def manage_solar_teams_dialog(site_row, alloc_row):
    st.caption("Civil / Electrical / Transporter teams ke charges yahan manage karein")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("PROJECT ID", value=site_row.get("Project ID", ""), disabled=True)
    with c2: st.text_input("SITE ID", value=site_row.get("Site ID", ""), disabled=True)
    with c3: st.text_input("SITE NAME", value=site_row.get("Site Name", ""), disabled=True)
    with c4: st.text_input("CLUSTER", value=site_row.get("Cluster", ""), disabled=True)

    all_dd = get_all_dropdowns()
    team_opts = get_opts("Team Name", all_dd)

    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    def team_section(label, key_prefix, alloc):
        st.markdown(f'<div class="modal-section-title">👷 {label} TEAM</div>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_name = st.selectbox(
                f"{label} TEAM NAME", team_opts,
                index=get_idx(alloc.get(f"{key_prefix}_team_name", ""), team_opts),
                key=f"solar_{key_prefix}_team"
            )
        with tc2:
            status_opts = ["Pending", "Completed"]
            t_status = st.selectbox(
                f"{label} STATUS", status_opts,
                index=(1 if alloc.get(f"{key_prefix}_status") == "Completed" else 0),
                key=f"solar_{key_prefix}_status"
            )
        with tc3:
            t_charge = st.number_input(
                f"{label} CHARGE AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_charge_amount", 0)),
                key=f"solar_{key_prefix}_charge"
            )
        tc4, tc5 = st.columns([1, 2])
        with tc4:
            t_appr_amt = st.number_input(
                f"{label} EXTRA APPROVAL AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_extra_approval_amount", 0)),
                key=f"solar_{key_prefix}_apprvamt"
            )
        with tc5:
            t_appr_remark = st.text_input(
                f"{label} EXTRA APPROVAL REMARK (kis baat ka approval hai)",
                value=alloc.get(f"{key_prefix}_extra_approval_remark", ""),
                placeholder="Amount > 0 hai to yeh likhna compulsory hai",
                key=f"solar_{key_prefix}_apprvremark"
            )
        return {
            f"{key_prefix}_team_name": t_name if t_name != "Select" else "",
            f"{key_prefix}_status": t_status,
            f"{key_prefix}_charge_amount": t_charge,
            f"{key_prefix}_extra_approval_amount": t_appr_amt,
            f"{key_prefix}_extra_approval_remark": t_appr_remark,
        }

    civil_data = team_section("CIVIL", "civil", alloc_row)
    electrical_data = team_section("ELECTRICAL", "electrical", alloc_row)
    transport_data = team_section("TRANSPORTER", "transport", alloc_row)

    st.markdown('<div class="modal-section-title">📝 REMARKS</div>', unsafe_allow_html=True)
    remarks = st.text_area("REMARKS", value=alloc_row.get("remarks", ""), key="solar_remarks", height=80)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        save_clicked = st.button("💾 Save Allocation", type="primary", use_container_width=True)

    if save_clicked:
        has_error = False
        for label, data, key_prefix in [("CIVIL", civil_data, "civil"), ("ELECTRICAL", electrical_data, "electrical"), ("TRANSPORTER", transport_data, "transport")]:
            amt = num(data.get(f"{key_prefix}_extra_approval_amount", 0))
            rmk = str(data.get(f"{key_prefix}_extra_approval_remark", "")).strip()
            if amt > 0 and not rmk:
                st.error(f"⚠️ {label} Extra Approval Amount ₹{amt:,.0f} diya hai, iske liye Remark likhna compulsory hai (kis baat ka approval hai)!")
                has_error = True

        if has_error:
            st.stop()

        payload = {
            "workspace": st.session_state.get('active_workspace', 'VISPL'),
            "Project ID": site_row.get("Project ID", ""),
            "Site ID": site_row.get("Site ID", ""),
            "Site Name": site_row.get("Site Name", ""),
            "Cluster": site_row.get("Cluster", ""),
            "remarks": remarks,
        }
        payload.update(civil_data)
        payload.update(electrical_data)
        payload.update(transport_data)

        try:
            existing = supabase.table("solar_team_allocation") \
                .select("id") \
                .eq("workspace", payload["workspace"]) \
                .eq("Project ID", payload["Project ID"]) \
                .execute()
            if existing.data:
                supabase.table("solar_team_allocation").update(payload).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("solar_team_allocation").insert(payload).execute()
            st.success("✅ Solar Team Allocation Saved!")
            st.rerun()
        except Exception as e:
            err_str = str(e)
            if "schema cache" in err_str.lower() or "PGRST204" in err_str:
                st.error("❌ Database mein zaroori columns nahi mile. Kripya 'solar_setup.sql' script Supabase SQL Editor mein (dobara) run karein, phir 30 second wait karke retry karein.")
            else:
                st.error(f"❌ Error saving allocation: {e}")

# --- 5. VIEW TEAM SITE DETAILS DIALOG (Ledger tab) ---
@st.dialog("🧾 Team Site-wise & Payment Detail", width="large")
def view_team_detail_dialog(team_name, entries, payments):
    st.caption(f"Team '{team_name}' ke saare Solar sites aur payments ka detailed hisaab")

    st.markdown('<div class="modal-section-title">🏗️ WORK DONE (SITE-WISE)</div>', unsafe_allow_html=True)
    h1, h2, h3, h4, h5, h6, h7 = st.columns([1.3, 1.3, 0.9, 0.9, 1.0, 1.0, 2.0])
    for c, label in zip([h1, h2, h3, h4, h5, h6, h7],
                         ["SITE ID", "PROJECT ID", "ROLE", "STATUS", "CHARGE (₹)", "APPROVAL (₹)", "APPROVAL REMARK"]):
        c.markdown(f"<b style='color:#94a3b8; font-size:0.78rem;'>{label}</b>", unsafe_allow_html=True)
    st.markdown("<hr style='border:1px solid rgba(255,255,255,0.08); margin:6px 0;'>", unsafe_allow_html=True)
    for e in entries:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.3, 1.3, 0.9, 0.9, 1.0, 1.0, 2.0])
        c1.markdown(f"<span style='color:#e2e8f0;'>{e['site_id']}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span style='color:#e2e8f0;'>{e['project_id']}</span>", unsafe_allow_html=True)
        c3.markdown(f"<span style='color:#e2e8f0;'>{e['role']}</span>", unsafe_allow_html=True)
        status_color = "#4ade80" if e.get('status') == "Completed" else "#facc15"
        c4.markdown(f"<span style='color:{status_color}; font-weight:700;'>{e.get('status','Pending')}</span>", unsafe_allow_html=True)
        c5.markdown(f"<span style='color:#e2e8f0;'>{e['charge']:,.0f}</span>", unsafe_allow_html=True)
        c6.markdown(f"<span style='color:#e2e8f0;'>{e['approval']:,.0f}</span>", unsafe_allow_html=True)
        c7.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>{e['approval_remark'] or '-'}</span>", unsafe_allow_html=True)
    st.caption("💡 Sirf 'Completed' status wale kaam ka amount Total Billed / Balance mein count hota hai.")

    st.markdown('<div class="modal-section-title">💰 PAYMENTS RECEIVED</div>', unsafe_allow_html=True)
    if payments:
        p1, p2, p3, p4, p5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.2])
        for c, label in zip([p1, p2, p3, p4, p5], ["DATE", "PAID FROM", "TYPE", "AMOUNT (₹)", "REMARK"]):
            c.markdown(f"<b style='color:#94a3b8; font-size:0.78rem;'>{label}</b>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid rgba(255,255,255,0.08); margin:6px 0;'>", unsafe_allow_html=True)
        for p in payments:
            p1, p2, p3, p4, p5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.2])
            p1.markdown(f"<span style='color:#e2e8f0;'>{p.get('pay_date','')}</span>", unsafe_allow_html=True)
            p2.markdown(f"<span style='color:#e2e8f0;'>{p.get('pay_from','')}</span>", unsafe_allow_html=True)
            p3.markdown(f"<span style='color:#e2e8f0;'>{p.get('pay_type','')}</span>", unsafe_allow_html=True)
            p4.markdown(f"<span style='color:#4ade80; font-weight:700;'>{num(p.get('amount')):,.0f}</span>", unsafe_allow_html=True)
            p5.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>{p.get('remark','') or '-'}</span>", unsafe_allow_html=True)
    else:
        st.info("Is team ko abhi tak koi payment nahi kiya gaya.")

    completed_entries = [e for e in entries if e.get("status") == "Completed"]
    total_billed = sum(e['charge'] + e['approval'] for e in completed_entries)
    total_paid = sum(num(p.get('amount')) for p in payments)
    balance = total_billed - total_paid
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 12px 18px; border-radius: 8px; margin-top:15px; display:flex; justify-content:space-between;">
            <div style="color:#ffffff; font-weight:700;">Total Billed: <span style="color:#3b82f6;">₹ {total_billed:,.0f}</span></div>
            <div style="color:#ffffff; font-weight:700;">Total Paid: <span style="color:#4ade80;">₹ {total_paid:,.0f}</span></div>
            <div style="color:#ffffff; font-weight:700;">Balance: <span style="color:{'#f87171' if balance>0 else '#4ade80'};">₹ {balance:,.0f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    def generate_team_pdf():
        if FPDF is None:
            raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()

        if os.path.exists("logo (1).png"):
            pdf.image("logo (1).png", x=75, y=10, w=60)
            pdf.ln(28)

        primary_color = (15, 23, 42)
        secondary_color = (245, 158, 11)
        green_color = (16, 185, 129)
        red_color = (239, 68, 68)

        pdf.set_text_color(*primary_color)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(190, 10, "VISIONTECH INFRA SOLUTION PVT. LTD.", ln=True, align='C')

        pdf.set_text_color(*secondary_color)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 8, "SOLAR PROJECT - TEAM LEDGER", ln=True, align='C')

        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, f"Team: {team_name}", ln=True, align='C')
        pdf.ln(4)

        def draw_table(title, cols, col_widths, rows, header_color):
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(*header_color)
            pdf.cell(190, 8, title, ln=True, align='L')

            pdf.set_fill_color(*header_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 8)
            for i, col in enumerate(cols):
                pdf.cell(col_widths[i], 8, col, border=1, align='C', fill=True)
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 8)
            fill = False
            for row in rows:
                pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
                for i, val in enumerate(row):
                    pdf.cell(col_widths[i], 7, str(val), border=1, align='L', fill=fill)
                pdf.ln()
                fill = not fill
            pdf.ln(6)

        # --- SITE-WISE WORK TABLE ---
        site_rows_pdf = [
            [e['site_id'], e['project_id'], e['site_name'], e.get('status', 'Pending'),
             f"Rs. {e['charge']:,.0f}", f"Rs. {e['approval']:,.0f}",
             f"Rs. {(e['charge'] + e['approval']):,.0f}" if e.get('status') == "Completed" else "-"]
            for e in entries
        ]
        draw_table("SITE-WISE WORK DONE", ["Site ID", "Project ID", "Site Name", "Status", "Charge Amt", "Extra Approval", "Total"],
                   [20, 22, 42, 22, 26, 28, 30], site_rows_pdf, secondary_color)

        # --- PAYMENTS TABLE ---
        payment_rows_pdf = [
            [p.get('pay_date', ''), p.get('pay_from', ''), f"Rs. {num(p.get('amount')):,.0f}"]
            for p in payments
        ]
        if payment_rows_pdf:
            draw_table("PAYMENTS RECEIVED", ["Payment Date", "Paid From", "Amount"],
                       [45, 55, 90], payment_rows_pdf, green_color)

        # --- TOTALS ---
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(10, pdf.get_y(), 190, 28, 'FD')
        pdf.set_y(pdf.get_y() + 5)

        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(*secondary_color)
        pdf.cell(190, 8, f"Total Site Amount: Rs. {total_billed:,.0f}", ln=True, align='L')

        pdf.set_text_color(*green_color)
        pdf.cell(190, 8, f"Total Paid Amount: Rs. {total_paid:,.0f}", ln=True, align='L')

        bal_color = red_color if balance > 0 else green_color
        pdf.set_text_color(*bal_color)
        pdf.cell(190, 8, f"Total Balance: Rs. {balance:,.0f}", ln=True, align='L')

        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, (bytes, bytearray)):
            return bytes(pdf_output)
        return pdf_output.encode('latin1')

    col_dl, col_close = st.columns(2)
    with col_dl:
        try:
            pdf_bytes = generate_team_pdf()
            st.download_button(
                "📄 Download PDF", data=pdf_bytes,
                file_name=f"{team_name}_Solar_Ledger.pdf", mime="application/pdf",
                use_container_width=True, type="primary"
            )
        except Exception as e:
            st.error(str(e))
    with col_close:
        if st.button("Close", use_container_width=True):
            st.rerun()

# --- TOP BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #f59e0b 0%, #ec4899 50%, #8b5cf6 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            ☀️ SOLAR PROJECT — {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 6. FETCH SOLAR SITES (Project Name = Solar) FROM site_data ---
active_ws = st.session_state.get('active_workspace', 'VISPL')
try:
    site_res = supabase.table("site_data").select("*").eq("workspace", active_ws).ilike("Project Name", "%solar%").execute()
    site_data = site_res.data if site_res.data else []
    site_data = [r for r in site_data if str(r.get("Project Name", "")).strip().lower() == "solar"]
except Exception:
    site_data = []

if not site_data:
    try:
        all_ws_res = supabase.table("site_data").select("Project Name").eq("workspace", active_ws).execute()
        distinct_pn = sorted(set(str(r.get("Project Name", "")).strip() for r in (all_ws_res.data or []) if str(r.get("Project Name", "")).strip()))
        if distinct_pn:
            st.info(f"ℹ️ Koi 'Solar' site nahi mili. Aapke workspace mein 'Project Name' column ki actual values hain: {', '.join(distinct_pn)}")
    except Exception:
        pass

try:
    alloc_res = supabase.table("solar_team_allocation").select("*").eq("workspace", active_ws).execute()
    alloc_data = alloc_res.data if alloc_res.data else []
except Exception:
    alloc_data = []

try:
    pay_res = supabase.table("solar_payments").select("*").eq("workspace", active_ws).order("id", desc=True).execute()
    solar_payments_data = pay_res.data if pay_res.data else []
except Exception:
    solar_payments_data = []

alloc_map = {row.get("Project ID", ""): row for row in alloc_data}

df = pd.DataFrame(site_data) if site_data else pd.DataFrame(
    columns=["id", "Project ID", "Site ID", "Site Name", "Cluster", "Site Status"]
)

if 'created_at' in df.columns and not df.empty:
    df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.sort_values(by='created_at_dt', ascending=False).drop(columns=['created_at_dt']).reset_index(drop=True)
elif not df.empty:
    df = df.iloc[::-1].reset_index(drop=True)

# --- Build team_entries (used by Ledger + Payments tabs) ---
team_entries = defaultdict(list)
for a in alloc_data:
    for role, role_label in [("civil", "Civil"), ("electrical", "Electrical"), ("transport", "Transporter")]:
        t_name = str(a.get(f"{role}_team_name", "")).strip()
        if not t_name:
            continue
        team_entries[t_name].append({
            "site_id": a.get("Site ID", ""),
            "project_id": a.get("Project ID", ""),
            "site_name": a.get("Site Name", ""),
            "role": role_label,
            "status": a.get(f"{role}_status", "Pending"),
            "charge": num(a.get(f"{role}_charge_amount")),
            "approval": num(a.get(f"{role}_extra_approval_amount")),
            "approval_remark": a.get(f"{role}_extra_approval_remark", ""),
        })

payments_by_team = defaultdict(list)
for p in solar_payments_data:
    payments_by_team[str(p.get("team_name", "")).strip()].append(p)

solar_team_names = sorted(set(team_entries.keys()) | set(payments_by_team.keys()))

# ================================================================
# --- TABS: SOLAR SITES  |  TEAM LEDGER  |  PAYMENTS ---
# ================================================================
tab_sites, tab_ledger, tab_payments = st.tabs(["📍 Solar Sites", "🧾 Team Ledger", "💳 Payments"])

# ================================================================
# TAB 1: SOLAR SITES
# ================================================================
with tab_sites:
    total_sites = len(df)
    civil_total = sum(num(a.get("civil_charge_amount")) for a in alloc_data)
    electrical_total = sum(num(a.get("electrical_charge_amount")) for a in alloc_data)
    transport_total = sum(num(a.get("transport_charge_amount")) for a in alloc_data)
    approval_total = sum(
        num(a.get("civil_extra_approval_amount")) + num(a.get("electrical_extra_approval_amount")) + num(a.get("transport_extra_approval_amount"))
        for a in alloc_data
    )

    s1, s2, s3, s4, s5 = st.columns(5)
    with s1: st.markdown(f'<div class="solar-card"><div class="label">Total Solar Sites</div><div class="value">{total_sites}</div></div>', unsafe_allow_html=True)
    with s2: st.markdown(f'<div class="solar-card"><div class="label">Civil Charges (₹)</div><div class="value">{civil_total:,.0f}</div></div>', unsafe_allow_html=True)
    with s3: st.markdown(f'<div class="solar-card"><div class="label">Electrical Charges (₹)</div><div class="value">{electrical_total:,.0f}</div></div>', unsafe_allow_html=True)
    with s4: st.markdown(f'<div class="solar-card"><div class="label">Transport Charges (₹)</div><div class="value">{transport_total:,.0f}</div></div>', unsafe_allow_html=True)
    with s5: st.markdown(f'<div class="solar-card"><div class="label">Total Extra Approval (₹)</div><div class="value">{approval_total:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_title, col_search, col_export = st.columns([5, 3, 1.5])
    with col_title:
        st.markdown("##### 🗄️ Solar Project Sites")
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search solar sites...", label_visibility="collapsed", key="solar_search")
    with col_export:
        export_clicked = st.button("📥 Export", use_container_width=True, key="solar_export_btn")

    df_view = df.copy()
    if search_query and not df_view.empty:
        mask = df_view.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_view = df_view[mask]

    if export_clicked and not df_view.empty:
        rows = []
        for _, r in df_view.iterrows():
            a = alloc_map.get(r.get("Project ID", ""), {})
            rows.append({
                "Project ID": r.get("Project ID", ""),
                "Site ID": r.get("Site ID", ""),
                "Site Name": r.get("Site Name", ""),
                "Cluster": r.get("Cluster", ""),
                "Site Status": r.get("Site Status", ""),
                "Civil Team": a.get("civil_team_name", ""),
                "Civil Status": a.get("civil_status", "Pending"),
                "Civil Charge": num(a.get("civil_charge_amount")),
                "Civil Extra Approval": num(a.get("civil_extra_approval_amount")),
                "Civil Approval Remark": a.get("civil_extra_approval_remark", ""),
                "Electrical Team": a.get("electrical_team_name", ""),
                "Electrical Status": a.get("electrical_status", "Pending"),
                "Electrical Charge": num(a.get("electrical_charge_amount")),
                "Electrical Extra Approval": num(a.get("electrical_extra_approval_amount")),
                "Electrical Approval Remark": a.get("electrical_extra_approval_remark", ""),
                "Transport Team": a.get("transport_team_name", ""),
                "Transport Status": a.get("transport_status", "Pending"),
                "Transport Charge": num(a.get("transport_charge_amount")),
                "Transport Extra Approval": num(a.get("transport_extra_approval_amount")),
                "Transport Approval Remark": a.get("transport_extra_approval_remark", ""),
                "Remarks": a.get("remarks", ""),
            })
        export_df = pd.DataFrame(rows)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Solar Project')
        st.download_button(
            label="📊 Download Solar_Project_Export.xlsx",
            data=buffer.getvalue(),
            file_name="Solar_Project_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="solar_export_dl"
        )

    rows_per_page = 10
    total_rows = len(df_view)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state.solar_current_page > total_pages:
        st.session_state.solar_current_page = total_pages
    elif st.session_state.solar_current_page < 1:
        st.session_state.solar_current_page = 1

    start_idx = (st.session_state.solar_current_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df_view.iloc[start_idx:end_idx].copy()

    COL_RATIOS = [0.5, 0.4, 1.1, 1.4, 1.0, 1.1, 0.9,
                  1.1, 0.8, 1.1, 0.8, 1.1, 0.8,
                  1.1, 1.1]
    COL_LABELS = ["⚙️", "#", "SITE ID", "SITE NAME", "CLUSTER", "PROJECT ID", "STATUS",
                  "CIVIL TEAM", "AMT (₹)", "ELECTRICAL TEAM", "AMT (₹)", "TRANSPORT TEAM", "AMT (₹)",
                  "TOTAL CHARGE (₹)", "TOTAL APPROVAL (₹)"]

    with st.container(key="solar_table_wrap", height=560):
        if df_page.empty:
            st.info("Koi Solar site nahi mili. Site Data Hub mein 'Project Name' = Solar select karke site add karein.")
        else:
            h_cols = st.columns(COL_RATIOS)
            for h_col, label in zip(h_cols, COL_LABELS):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                proj_id = str(row_dict.get("Project ID", ""))
                alloc = alloc_map.get(proj_id, {})
                serial_no = start_idx + page_pos + 1

                civil_charge = num(alloc.get("civil_charge_amount"))
                electrical_charge = num(alloc.get("electrical_charge_amount"))
                transport_charge = num(alloc.get("transport_charge_amount"))
                total_charge = civil_charge + electrical_charge + transport_charge

                total_approval = (
                    num(alloc.get("civil_extra_approval_amount")) +
                    num(alloc.get("electrical_extra_approval_amount")) +
                    num(alloc.get("transport_extra_approval_amount"))
                )

                def status_tag(prefix):
                    s = alloc.get(f"{prefix}_status", "Pending")
                    return " ✅" if s == "Completed" else (" ⏳" if alloc.get(f"{prefix}_team_name") else "")

                rcols = st.columns(COL_RATIOS)
                with rcols[0]:
                    if st.button("⚙️", key=f"solar_mgr_{row_dict.get('id')}", help="Manage Teams", use_container_width=True):
                        manage_solar_teams_dialog(row_dict, alloc)
                rcols[1].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
                rcols[2].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
                rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
                rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
                rcols[5].markdown(f"<div class='tbl-cell'>{proj_id or '-'}</div>", unsafe_allow_html=True)
                rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Status','') or '-'}</div>", unsafe_allow_html=True)
                rcols[7].markdown(f"<div class='tbl-cell'>{(alloc.get('civil_team_name','') or '-')}{status_tag('civil')}</div>", unsafe_allow_html=True)
                rcols[8].markdown(f"<div class='tbl-cell'>{civil_charge:,.0f}</div>", unsafe_allow_html=True)
                rcols[9].markdown(f"<div class='tbl-cell'>{(alloc.get('electrical_team_name','') or '-')}{status_tag('electrical')}</div>", unsafe_allow_html=True)
                rcols[10].markdown(f"<div class='tbl-cell'>{electrical_charge:,.0f}</div>", unsafe_allow_html=True)
                rcols[11].markdown(f"<div class='tbl-cell'>{(alloc.get('transport_team_name','') or '-')}{status_tag('transport')}</div>", unsafe_allow_html=True)
                rcols[12].markdown(f"<div class='tbl-cell'>{transport_charge:,.0f}</div>", unsafe_allow_html=True)
                rcols[13].markdown(f"<div class='tbl-cell'>{total_charge:,.0f}</div>", unsafe_allow_html=True)
                rcols[14].markdown(f"<div class='tbl-cell'>{total_approval:,.0f}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.solar_current_page == 1), key="solar_prev"):
            st.session_state.solar_current_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state.solar_current_page} of {total_pages} (Total Solar Sites: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.solar_current_page == total_pages), key="solar_next"):
            st.session_state.solar_current_page += 1
            st.rerun()

# ================================================================
# TAB 2: TEAM LEDGER (Team-wise + Site-wise toggle)
# ================================================================
with tab_ledger:
    ledger_view_mode = st.radio("Ledger View:", ["👷 Team Wise", "📍 Site Wise"], horizontal=True, key="ledger_view_mode")
    st.markdown("<br>", unsafe_allow_html=True)

    if ledger_view_mode == "👷 Team Wise":
        ledger_rows = []
        for t_name in solar_team_names:
            entries = team_entries.get(t_name, [])
            completed_entries = [e for e in entries if e.get("status") == "Completed"]
            payments = payments_by_team.get(t_name, [])
            site_ids = set(e["project_id"] for e in completed_entries)
            total_charge = sum(e["charge"] for e in completed_entries)
            total_approval = sum(e["approval"] for e in completed_entries)
            total_billed = total_charge + total_approval
            total_paid = sum(num(p.get("amount")) for p in payments)
            balance = total_billed - total_paid
            ledger_rows.append({
                "Team Name": t_name,
                "Sites Worked": len(site_ids),
                "Total Charge (₹)": total_charge,
                "Total Approval (₹)": total_approval,
                "Total Billed (₹)": total_billed,
                "Total Paid (₹)": total_paid,
                "Balance (₹)": balance,
                "_entries": entries,
                "_payments": payments,
            })

        ledger_rows.sort(key=lambda r: r["Balance (₹)"], reverse=True)

        grand_billed = sum(r["Total Billed (₹)"] for r in ledger_rows)
        grand_paid = sum(r["Total Paid (₹)"] for r in ledger_rows)
        grand_balance = sum(r["Balance (₹)"] for r in ledger_rows)

        s1, s2, s3, s4 = st.columns(4)
        with s1: st.markdown(f'<div class="solar-card"><div class="label">Total Teams</div><div class="value">{len(ledger_rows)}</div></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="solar-card"><div class="label">Total Billed (₹)</div><div class="value">{grand_billed:,.0f}</div></div>', unsafe_allow_html=True)
        with s3: st.markdown(f'<div class="solar-card"><div class="label">Total Paid (₹)</div><div class="value-green">{grand_paid:,.0f}</div></div>', unsafe_allow_html=True)
        with s4: st.markdown(f'<div class="solar-card"><div class="label">Total Balance (₹)</div><div class="value-red">{grand_balance:,.0f}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_title, col_search = st.columns([7, 3])
        with col_title:
            st.markdown("##### 🗄️ Team-wise Hisaab (Civil + Electrical + Transporter combined)")
        with col_search:
            ledger_search = st_keyup("Search", placeholder="🔍 Search team...", label_visibility="collapsed", key="ledger_search")

        display_rows = ledger_rows
        if ledger_search:
            display_rows = [r for r in ledger_rows if ledger_search.lower() in r["Team Name"].lower()]

        LCOL_RATIOS = [1.8, 1.0, 1.2, 1.2, 1.2, 1.2, 1.2, 0.7]
        LCOL_LABELS = ["TEAM NAME", "SITES", "CHARGE (₹)", "APPROVAL (₹)", "TOTAL BILLED (₹)", "PAID (₹)", "BALANCE (₹)", "👁️"]

        with st.container(key="ledger_table_wrap", height=520):
            if not display_rows:
                st.info("Abhi tak kisi bhi team ko Solar site allocate nahi hui. 'Solar Sites' tab se ⚙️ Manage Teams se allocation karein.")
            else:
                h_cols = st.columns(LCOL_RATIOS)
                for h_col, label in zip(h_cols, LCOL_LABELS):
                    h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

                for r in display_rows:
                    rcols = st.columns(LCOL_RATIOS)
                    rcols[0].markdown(f"<div class='tbl-cell team-name'>{r['Team Name']}</div>", unsafe_allow_html=True)
                    rcols[1].markdown(f"<div class='tbl-cell'>{r['Sites Worked']}</div>", unsafe_allow_html=True)
                    rcols[2].markdown(f"<div class='tbl-cell'>{r['Total Charge (₹)']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[3].markdown(f"<div class='tbl-cell'>{r['Total Approval (₹)']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[4].markdown(f"<div class='tbl-cell'>{r['Total Billed (₹)']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[5].markdown(f"<div class='tbl-cell paid-amt'>{r['Total Paid (₹)']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[6].markdown(f"<div class='tbl-cell pending-amt'>{r['Balance (₹)']:,.0f}</div>", unsafe_allow_html=True)
                    with rcols[7]:
                        if st.button("👁️", key=f"ledger_view_{r['Team Name']}", help="View Detail", use_container_width=True):
                            view_team_detail_dialog(r["Team Name"], r["_entries"], r["_payments"])

    else:
        # ---- SITE WISE VIEW (lavish custom table, same style as other tabs) ----
        col_title2, col_search2 = st.columns([7, 3])
        with col_title2:
            st.markdown("##### 🗄️ Site-wise Hisaab (Kis site pe kaunsi team, kitna amount)")
        with col_search2:
            site_search = st_keyup("Search", placeholder="🔍 Search site...", label_visibility="collapsed", key="site_ledger_search")

        site_rows = []
        for _, r in df.iterrows():
            proj_id = str(r.get("Project ID", ""))
            a = alloc_map.get(proj_id, {})
            civil_status = a.get("civil_status", "Pending")
            electrical_status = a.get("electrical_status", "Pending")
            transport_status = a.get("transport_status", "Pending")

            civil_charge = num(a.get("civil_charge_amount")) if civil_status == "Completed" else 0.0
            electrical_charge = num(a.get("electrical_charge_amount")) if electrical_status == "Completed" else 0.0
            transport_charge = num(a.get("transport_charge_amount")) if transport_status == "Completed" else 0.0
            total_approval = (
                (num(a.get("civil_extra_approval_amount")) if civil_status == "Completed" else 0.0) +
                (num(a.get("electrical_extra_approval_amount")) if electrical_status == "Completed" else 0.0) +
                (num(a.get("transport_extra_approval_amount")) if transport_status == "Completed" else 0.0)
            )
            total_charge = civil_charge + electrical_charge + transport_charge

            def tag(name, status):
                if not name or name == "-":
                    return "-"
                return f"{name} ✅" if status == "Completed" else f"{name} ⏳"

            site_rows.append({
                "Site ID": r.get("Site ID", "") or "-",
                "Site Name": r.get("Site Name", "") or "-",
                "Cluster": r.get("Cluster", "") or "-",
                "Project ID": proj_id or "-",
                "Civil Team": tag(a.get("civil_team_name", ""), civil_status),
                "Civil Amt": civil_charge,
                "Electrical Team": tag(a.get("electrical_team_name", ""), electrical_status),
                "Electrical Amt": electrical_charge,
                "Transport Team": tag(a.get("transport_team_name", ""), transport_status),
                "Transport Amt": transport_charge,
                "Total Charge": total_charge,
                "Total Approval": total_approval,
                "Grand Total": total_charge + total_approval,
            })

        st.caption("💡 Sirf ✅ Completed status wale kaam ka amount yahan count hota hai. ⏳ = Pending (abhi count nahi hoga).")

        if site_search:
            site_rows = [
                sr for sr in site_rows
                if site_search.lower() in " ".join(str(v) for v in sr.values()).lower()
            ]

        SCOL_RATIOS = [0.4, 1.1, 1.4, 0.9, 1.1, 1.1, 0.8, 1.1, 0.8, 1.1, 0.8, 1.1, 1.1, 1.1]
        SCOL_LABELS = ["#", "SITE ID", "SITE NAME", "CLUSTER", "PROJECT ID",
                       "CIVIL TEAM", "AMT (₹)", "ELECTRICAL TEAM", "AMT (₹)", "TRANSPORT TEAM", "AMT (₹)",
                       "TOTAL CHARGE (₹)", "TOTAL APPROVAL (₹)", "GRAND TOTAL (₹)"]

        with st.container(key="site_ledger_table_wrap", height=560):
            if not site_rows:
                st.info("Koi Solar site data nahi mila.")
            else:
                h_cols = st.columns(SCOL_RATIOS)
                for h_col, label in zip(h_cols, SCOL_LABELS):
                    h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

                for idx, sr in enumerate(site_rows, start=1):
                    rcols = st.columns(SCOL_RATIOS)
                    rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{idx}</div>", unsafe_allow_html=True)
                    rcols[1].markdown(f"<div class='tbl-cell'>{sr['Site ID']}</div>", unsafe_allow_html=True)
                    rcols[2].markdown(f"<div class='tbl-cell'>{sr['Site Name']}</div>", unsafe_allow_html=True)
                    rcols[3].markdown(f"<div class='tbl-cell'>{sr['Cluster']}</div>", unsafe_allow_html=True)
                    rcols[4].markdown(f"<div class='tbl-cell'>{sr['Project ID']}</div>", unsafe_allow_html=True)
                    rcols[5].markdown(f"<div class='tbl-cell'>{sr['Civil Team']}</div>", unsafe_allow_html=True)
                    rcols[6].markdown(f"<div class='tbl-cell'>{sr['Civil Amt']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[7].markdown(f"<div class='tbl-cell'>{sr['Electrical Team']}</div>", unsafe_allow_html=True)
                    rcols[8].markdown(f"<div class='tbl-cell'>{sr['Electrical Amt']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[9].markdown(f"<div class='tbl-cell'>{sr['Transport Team']}</div>", unsafe_allow_html=True)
                    rcols[10].markdown(f"<div class='tbl-cell'>{sr['Transport Amt']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[11].markdown(f"<div class='tbl-cell'>{sr['Total Charge']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[12].markdown(f"<div class='tbl-cell'>{sr['Total Approval']:,.0f}</div>", unsafe_allow_html=True)
                    rcols[13].markdown(f"<div class='tbl-cell' style='font-weight:800; color:#f59e0b;'>{sr['Grand Total']:,.0f}</div>", unsafe_allow_html=True)

# ================================================================
# TAB 3: PAYMENTS
# ================================================================
with tab_payments:
    st.markdown("##### 💳 Solar Team Payment Entry")

    if not solar_team_names:
        st.info("Abhi tak koi team Solar site pe allocate nahi hui. Pehle 'Solar Sites' tab se ⚙️ Manage Teams se team allocate karein, phir yahan payment kar sakte ho.")
    else:
        all_dd = get_all_dropdowns()
        pay_from_opts = get_simple_opts("Payment From", all_dd, ["Bank", "Cash"])
        pay_type_opts = get_simple_opts("Payment Type", all_dd, ["NEFT", "RTGS", "UPI"])

        with st.form("solar_payment_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                pay_team = st.selectbox("Pay To (Solar Team) *", solar_team_names)
            with f2:
                pay_from = st.selectbox("Payment From *", pay_from_opts)
            with f3:
                pay_type = st.selectbox("Payment Type *", pay_type_opts)

            f4, f5, f6 = st.columns(3)
            with f4:
                pay_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, value=0.0)
            with f5:
                pay_date = st.date_input("Payment Date", value=datetime.date.today(), format="DD/MM/YYYY")
            with f6:
                pay_remark = st.text_input("Remark", placeholder="e.g. Civil work advance")

            submitted = st.form_submit_button("💾 Save Payment", type="primary", use_container_width=True)

            if submitted:
                if pay_amount <= 0:
                    st.error("⚠️ Amount 0 se zyada hona chahiye!")
                else:
                    try:
                        ws = st.session_state.get('active_workspace', 'VISPL')

                        # 1. Mirror into main Team & Vendor Billing (billing_payments) so it shows there too
                        billing_payload = {
                            "workspace": ws,
                            "pay_from": pay_from,
                            "pay_to": pay_team,
                            "pay_type": pay_type,
                            "amount": pay_amount,
                            "date": str(pay_date),
                            "remark": f"[Solar] {pay_remark}".strip(),
                            "mode": "Team",
                        }
                        billing_res = supabase.table("billing_payments").insert(billing_payload).execute()
                        billing_id = billing_res.data[0].get("id") if (hasattr(billing_res, 'data') and billing_res.data) else None

                        # 2. Save into solar_payments (for Solar Ledger reporting)
                        solar_payload = {
                            "workspace": ws,
                            "team_name": pay_team,
                            "pay_from": pay_from,
                            "pay_type": pay_type,
                            "amount": pay_amount,
                            "pay_date": str(pay_date),
                            "remark": pay_remark,
                            "billing_payment_id": billing_id,
                        }
                        supabase.table("solar_payments").insert(solar_payload).execute()

                        st.success(f"✅ Payment Saved! Yeh Team Billing page ke Payment Entry mein bhi save ho gaya hai.")
                        st.rerun()
                    except Exception as e:
                        err_str = str(e)
                        if "schema cache" in err_str.lower() or "PGRST204" in err_str or "does not exist" in err_str.lower():
                            st.error("❌ 'solar_payments' table nahi mila. Kripya 'solar_setup.sql' script Supabase mein run karein.")
                        else:
                            st.error(f"❌ Error saving payment: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🗄️ Solar Payment History")

    pcol_search, pcol_export = st.columns([8, 2])
    with pcol_search:
        payment_search = st_keyup("Search", placeholder="🔍 Search payments...", label_visibility="collapsed", key="solar_payment_search")
    with pcol_export:
        payment_export_clicked = st.button("📥 Export", use_container_width=True, key="solar_payment_export_btn")

    pdf_view = pd.DataFrame(solar_payments_data) if solar_payments_data else pd.DataFrame(
        columns=["id", "team_name", "pay_from", "pay_type", "amount", "pay_date", "remark"]
    )
    if payment_search and not pdf_view.empty:
        mask = pdf_view.astype(str).apply(lambda x: x.str.contains(payment_search, case=False, na=False)).any(axis=1)
        pdf_view = pdf_view[mask]

    if payment_export_clicked and not pdf_view.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            pdf_view.drop(columns=[c for c in ["id", "billing_payment_id", "created_at"] if c in pdf_view.columns]).to_excel(writer, index=False, sheet_name='Solar Payments')
        st.download_button(
            label="📊 Download Solar_Payments.xlsx",
            data=buffer.getvalue(),
            file_name="Solar_Payments.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="solar_payment_export_dl"
        )

    PCOL_RATIOS = [1.6, 1.2, 1.2, 1.2, 1.2, 2.4, 0.7]
    PCOL_LABELS = ["TEAM NAME", "DATE", "PAID FROM", "TYPE", "AMOUNT (₹)", "REMARK", "🗑️"]

    with st.container(key="payments_table_wrap", height=420):
        if pdf_view.empty:
            st.info("Abhi tak koi Solar payment record nahi hai.")
        else:
            h_cols = st.columns(PCOL_RATIOS)
            for h_col, label in zip(h_cols, PCOL_LABELS):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for _, prow in pdf_view.iterrows():
                pd_dict = prow.to_dict()
                rcols = st.columns(PCOL_RATIOS)
                rcols[0].markdown(f"<div class='tbl-cell team-name'>{pd_dict.get('team_name','') or '-'}</div>", unsafe_allow_html=True)
                rcols[1].markdown(f"<div class='tbl-cell'>{pd_dict.get('pay_date','') or '-'}</div>", unsafe_allow_html=True)
                rcols[2].markdown(f"<div class='tbl-cell'>{pd_dict.get('pay_from','') or '-'}</div>", unsafe_allow_html=True)
                rcols[3].markdown(f"<div class='tbl-cell'>{pd_dict.get('pay_type','') or '-'}</div>", unsafe_allow_html=True)
                rcols[4].markdown(f"<div class='tbl-cell paid-amt'>{num(pd_dict.get('amount')):,.0f}</div>", unsafe_allow_html=True)
                rcols[5].markdown(f"<div class='tbl-cell'>{pd_dict.get('remark','') or '-'}</div>", unsafe_allow_html=True)
                with rcols[6]:
                    if st.button("🗑️", key=f"delpay_{pd_dict.get('id')}", help="Delete", use_container_width=True):
                        try:
                            supabase.table("solar_payments").delete().eq("id", pd_dict["id"]).execute()
                            b_id = pd_dict.get("billing_payment_id")
                            if b_id:
                                supabase.table("billing_payments").delete().eq("id", b_id).execute()
                            st.success("✅ Payment Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting: {e}")
