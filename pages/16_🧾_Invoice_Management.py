import streamlit as st
import pandas as pd
import math
import io
import json
from supabase import create_client, Client
from st_keyup import st_keyup
from datetime import datetime, date

# --- Crash-proof import for fpdf (Add 'fpdf' to requirements.txt in GitHub) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Invoice Management", page_icon="🧾", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'ers_page' not in st.session_state:
    st.session_state.ers_page = 1
if 'invdata_page' not in st.session_state:
    st.session_state.invdata_page = 1
if 'bhagya_page' not in st.session_state:
    st.session_state.bhagya_page = 1
if 'saitele_page' not in st.session_state:
    st.session_state.saitele_page = 1

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }

    /* Top Action Buttons */
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

    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }

    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* =========================================================
       CUSTOM PAGE NAVIGATION BAR (replaces st.tabs — fully reliable styling)
       ========================================================= */
    .st-key-nav_bar div[data-testid="stHorizontalBlock"] {
        gap: 12px !important;
        flex-wrap: wrap !important;
    }
    .st-key-nav_bar button {
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        padding: 16px 10px !important;
        height: auto !important;
        border-radius: 12px !important;
        transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-nav_bar button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        box-shadow: none !important;
    }
    .st-key-nav_bar button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.16) !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
    }
    .st-key-nav_bar button[kind="secondary"] p,
    .st-key-nav_bar button[kind="secondary"] span,
    .st-key-nav_bar button[kind="secondary"] div {
        color: #cbd5e1 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }
    .st-key-nav_bar button[kind="secondary"]:hover p,
    .st-key-nav_bar button[kind="secondary"]:hover span,
    .st-key-nav_bar button[kind="secondary"]:hover div {
        color: #ffffff !important;
    }
    .st-key-nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.45) !important;
    }
    .st-key-nav_bar button[kind="primary"] p,
    .st-key-nav_bar button[kind="primary"] span,
    .st-key-nav_bar button[kind="primary"] div {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }

    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }

    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
    div[data-testid="stDialog"] p {
        color: #e2e8f0 !important;
    }
    div[data-testid="stDialog"] button[kind="icon"] svg {
        fill: #ffffff !important;
    }

    .modal-section-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
    }

    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important;
        margin: 0.5rem 1rem !important;
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* =========================================================
       FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING
       Applies to ALL table wrappers whose container key ends with "_table_wrap"
       (invoice_table_wrap, ers_table_wrap, invdata_table_wrap, ...)
       ========================================================= */
    div[class*="_table_wrap"] {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important;
        padding: 0px 0 !important;
    }
    div[class*="_table_wrap"] div[data-testid="stHorizontalBlock"] {
        min-width: 3400px;
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    div[class*="_table_wrap"] div[data-testid="stHorizontalBlock"]:hover {
        background: rgba(255,255,255,0.04);
    }
    div[class*="_table_wrap"] div[data-testid="column"] {
        padding: 0 12px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    div[class*="_table_wrap"] div[data-testid="column"]:last-child {
        border-right: none;
    }

    div[class*="_table_wrap"] .tbl-head {
        background: transparent;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #94a3b8;
        text-transform: uppercase;
        white-space: nowrap !important;
    }
    div[class*="_table_wrap"] .tbl-cell {
        color: #e2e8f0;
        font-size: 0.86rem;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100%;
    }
    div[class*="_table_wrap"] .tbl-serial {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 800;
    }

    div[class*="_table_wrap"] button {
        height: 32px !important;
        width: 100% !important;
        padding: 0 !important;
        min-height: 0 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important;
        cursor: pointer !important;
    }
    div[class*="_table_wrap"] button:hover {
        background: #3b82f6 !important;
        border-color: #60a5fa !important;
        transform: translateY(-2px) !important;
    }

    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(1) { padding: 0 10px 0 15px !important; }
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(2),
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(3),
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(4) {
        padding: 4px 4px !important;
        border-right: none !important;
    }
    .st-key-invoice_table_wrap div[data-testid="column"]:nth-child(5) {
        padding: 4px 15px 4px 4px !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
# FIX: Ab hardcoded URL/Key ki jagah st.secrets se liya jaa raha hai — isse
# ek hi jagah (Streamlit Cloud Secrets) update karke sabhi pages naye
# Supabase project se automatically connect ho jaate hain.
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase connection error: {e}")
        return None

supabase: Client = init_connection()

# =========================================================================
# ERS PROCESS — FIXED "Indus Towers Invoice Submission Checklist" PDF
# ⚠️ IMPORTANT: Ye PDF sirf ON-DEMAND generate hoke seedha download hota hai.
# Isko kabhi bhi Supabase me insert/save/upload NAHI kiya jaata — sirf memory
# me banta hai aur turant user ko st.download_button se milta hai.
# Sirf 5 fields row ke data se aate hain (Inward Number, Inward Date, Invoice
# No., PO No, Invoice Date) — baaki poora checklist (Partner Name, User Name,
# E-Mail, saare check/cross marks) fixed/static hai jaisa original template me hai.
# =========================================================================

ERS_CHECKLIST_PART1 = [
    ("1", "Original Invoice", ["v", "v", "v", "v", "v"]),
    ("a", "Printed Invoice/Digital Invoice. No Manual correction on Printed Invoice. Manual Correction, if any, should be only PO / WCC/WCR No, which needs to be duly signed and stamped by auth. Person", ["v", "v", "v", "v", "v"]),
    ("b", 'Invoice No. should not exceed 16 characters, containing alphabets or numerals or special characters hyphen or dash and slash symbolised as "-" , "\\" and "/" respectively', ["v", "v", "v", "v", "v"]),
    ("c", "In case of debit / credit note, Number and date of the corresponding original tax invoice", ["v", "v", "v", "v", "v"]),
    ("d", "Name, Addresss & GSTIN of Partner & Indus Towers Limited on Invoice to be matched with PO", ["v", "v", "v", "v", "v"]),
    ("e", "Ship TO & Bill TO need to mention on invoices", ["v", "x", "x", "x", "x"]),
    ("f", "HSN/SAC code present on Invoice to be matched with PO/WCR", ["v", "v", "v", "v", "v"]),
    ("g", "Description of Goods/ services", ["v", "v", "v", "v", "v"]),
    ("h", "Quantity in case of goods and Unit/ Unique Quantity Code (UQC) of the same", ["v", "v", "v", "v", "v"]),
    ("i", "Taxes applied (IGST/CGST+SGST) in invoices to be matched with GRN/WCR", ["v", "v", "v", "v", "v"]),
    ("j", "Rate & Quantity should match with GRN/WCR", ["v", "v", "v", "v", "v"]),
    ("k", "In case of Agreement based invoices, rates should match with valid contract summary/valid agreement.", ["x", "x", "x", "x", "v"]),
    ("l", "Rates which are not part of PO/GBPA need to be verify through BOQ & for NON BOQ Rates circle SCM Head approval is required", ["x", "v", "v", "v", "x"]),
    ("m", "Total value of supply of goods or services should match with GRN / WCR", ["v", "v", "v", "v", "v"]),
    ("n", "Place of supply and name of State in case of inter-State Supply", ["v", "v", "v", "v", "v"]),
    ("o", "Stamp & Signature on printed invoice or digital signature on a digital invoice", ["v", "v", "v", "v", "v"]),
    ("p", "PO No & WCC/WCR No to be mentioned on Invoice. PO Date should be before Invoice Date", ["v", "v", "v", "v", "v"]),
]

ERS_CHECKLIST_PART2 = [
    ("2", "E-Waybill /LR copy", ["v", "x", "x", "x", "x"]),
    ("3", "Delivery Challans (in case multiple supply below 50K and consolidated bill above 50K is raised)", ["x", "x", "v", "x", "x"]),
    ("4", "In case of Direct Tower Supply, PDI copy is required", ["v", "x", "x", "x", "x"]),
    ("5", "Measurement sheet / Annexure sheet", ["x", "v", "x", "x", "x"]),
    ("6", "PF/ESIC/Wages Register/Returns proof attached (in case labour charges are mentioned)", ["x", "v", "v", "x", "x"]),
    ("7", "Receipt copy in cases of New connections / Load Up gradation / Transfer Installation", ["x", "x", "x", "v", "x"]),
    ("8", "Original Receipt required in EB Reimbursement bills with security & other Expense bifurcation", ["x", "x", "x", "v", "x"]),
    ("9", "Increase of HT EB Liaisoning Electricity Board approval letter required", ["x", "x", "x", "v", "x"]),
    ("10", "STN (Stock Transfer note) / MRN / SRN", ["x", "v", "x", "x", "x"]),
    ("11", "Photocopy of NOC from Gram panchayat in case of Municipal service charges", [None, None, None, None, None]),
    ("12", "Photocopy Pollution control certificate copy in case of PUC Service Depart.", [None, None, None, None, None]),
]


def _ers_draw_check(pdf, cx, cy, size=3.2):
    pdf.set_draw_color(20, 110, 20)
    pdf.set_line_width(0.45)
    x0, y0 = cx - size * 0.5, cy
    x1, y1 = cx - size * 0.12, cy + size * 0.42
    x2, y2 = cx + size * 0.55, cy - size * 0.5
    pdf.line(x0, y0, x1, y1)
    pdf.line(x1, y1, x2, y2)


def _ers_draw_cross(pdf, cx, cy, size=2.6):
    pdf.set_draw_color(160, 30, 30)
    pdf.set_line_width(0.45)
    half = size * 0.5
    pdf.line(cx - half, cy - half, cx + half, cy + half)
    pdf.line(cx - half, cy + half, cx + half, cy - half)


def _ers_wrap_text(pdf, text, max_width):
    words = text.replace("\n", " ").split(" ")
    lines = []
    current = ""
    for w in words:
        trial = (current + " " + w).strip()
        if pdf.get_string_width(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines if lines else [""]


def _ers_find_field(row_dict, candidates):
    """Case/space-insensitive lookup of a column value from a generic row dict.
    Tries each candidate name (exact match first), then falls back to any
    column whose name *contains* one of the candidate words."""
    if not row_dict:
        return ""
    cleaned_map = {str(k).strip().lower().replace("_", " "): k for k in row_dict.keys()}
    for cand in candidates:
        c = cand.strip().lower().replace("_", " ")
        if c in cleaned_map:
            val = row_dict.get(cleaned_map[c], "")
            if val not in (None, "", "nan"):
                return str(val)
    for cand in candidates:
        c = cand.strip().lower().replace("_", " ")
        for cleaned_key, orig_key in cleaned_map.items():
            if c in cleaned_key:
                val = row_dict.get(orig_key, "")
                if val not in (None, "", "nan"):
                    return str(val)
    return ""


def generate_ers_checklist_pdf(invoice_no, po_no, inv_date):
    """Builds the fixed Indus Towers invoice-submission-checklist PDF in memory
    (nothing is written to Supabase). Takes the 3 values directly (confirmed/
    edited by the user just before generating) instead of guessing column
    names — the rest of the checklist (names, contact info, all check/cross
    marks) is a fixed template, identical every time."""
    if FPDF is None:
        raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(8, 8, 8)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    PAGE_W = 194  # usable width (210mm page - 8mm margins each side)

    # ---------------- TITLE BAR ----------------
    pdf.set_fill_color(191, 191, 191)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(PAGE_W, 7, "Indus Towers Limited (Invoice submission checklist)", border=1, align="C", fill=True, ln=1)

    # ---------------- HEADER INFO TABLE ----------------
    label_w = 30
    value_w = 67
    row_h = 6.2

    header_rows = [
        ("Inward\nNumber-", invoice_no, "Inward Date-", inv_date),
        ("Partner\nName : -", "Visiontech Infra Solutions", "Invoice No.", invoice_no),
        ("PO NO:", po_no, "Invoice Date", inv_date),
        ("User Name :-", "Pramodkumar Jaju", "Depart.", "Deployment"),
        ("E-Mail ID : -", "vispltower@gmail.com", "Contact No-", "9552273181"),
    ]

    for lbl1, val1, lbl2, val2 in header_rows:
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        pdf.set_font("Arial", "B", 8)
        pdf.multi_cell(label_w, row_h / 2 if "\n" in lbl1 else row_h, lbl1, border=1, align="L")
        pdf.set_xy(x_start + label_w, y_start)
        pdf.set_font("Arial", "", 8.5)
        pdf.cell(value_w, row_h, " " + str(val1), border=1, align="L")
        pdf.set_font("Arial", "B", 8)
        pdf.cell(label_w, row_h, lbl2, border=1, align="L")
        pdf.set_font("Arial", "", 8.5)
        pdf.cell(value_w, row_h, " " + str(val2), border=1, align="L", ln=1)
        pdf.set_xy(x_start, y_start + row_h)

    # ---------------- CHECKLIST TABLE ----------------
    col_widths = [10, 68, 16, 24, 24, 22, 30]  # SNo, Particulars, Supply, TSP, IME, EB, Others
    headers_row2 = ["S.No.", "Particulars", "Supply\n(Y/N)", "TSP\n(Electrical/\nCivil & others)", "IME/OME/SMS/\nSME", "EB/Liasio\nning", "Others Services\n(Legal/Rent etc.)"]

    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(sum(col_widths[:3]), 4.3, "", border=1)
    pdf.cell(sum(col_widths[3:]), 4.3, "Services", border=1, align="C")
    pdf.ln(4.3)

    pdf.set_font("Arial", "B", 7)
    y_h = pdf.get_y()
    x_h = pdf.get_x()
    max_lines = max(len(h.split("\n")) for h in headers_row2)
    hdr_line_h = 2.9
    hdr_h = hdr_line_h * max_lines
    for w, h in zip(col_widths, headers_row2):
        xx = pdf.get_x()
        pdf.multi_cell(w, hdr_line_h, h, border=1, align="C")
        pdf.set_xy(xx + w, y_h)
    pdf.set_xy(x_h, y_h + hdr_h)

    def render_row(no_label, particulars, marks):
        pdf.set_font("Arial", "", 7)
        lines = _ers_wrap_text(pdf, particulars, col_widths[1] - 2)
        line_h = 3.05
        row_height = max(line_h * len(lines), 4.8)

        x_row = pdf.get_x()
        y_row = pdf.get_y()

        pdf.multi_cell(col_widths[0], row_height, no_label, border=1, align="C")
        pdf.set_xy(x_row + col_widths[0], y_row)
        pdf.multi_cell(col_widths[1], line_h, particulars, border=1, align="L")
        cur_y = pdf.get_y()
        if cur_y < y_row + row_height:
            pdf.rect(x_row + col_widths[0], cur_y, col_widths[1], (y_row + row_height) - cur_y)

        cx = x_row + col_widths[0] + col_widths[1]
        for i, w in enumerate(col_widths[2:]):
            pdf.rect(cx, y_row, w, row_height)
            mark = marks[i] if i < len(marks) else None
            if mark == "v":
                _ers_draw_check(pdf, cx + w / 2, y_row + row_height / 2)
            elif mark == "x":
                _ers_draw_cross(pdf, cx + w / 2, y_row + row_height / 2)
            cx += w

        pdf.set_xy(x_row, y_row + row_height)

    for no_label, particulars, marks in ERS_CHECKLIST_PART1:
        if pdf.get_y() + 6 > 290:
            pdf.add_page()
        render_row(no_label, particulars, marks)

    if pdf.get_y() + 6 > 290:
        pdf.add_page()
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_fill_color(235, 235, 235)
    pdf.cell(sum(col_widths), 4.5, "  Mandatory Documents", border=1, align="L", fill=True, ln=1)

    for no_label, particulars, marks in ERS_CHECKLIST_PART2:
        if pdf.get_y() + 6 > 290:
            pdf.add_page()
        render_row(no_label, particulars, marks)

    if pdf.get_y() + 14 > 290:
        pdf.add_page()
    pdf.ln(2)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(PAGE_W, 5, "PHD USE ONLY", border=1, ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(PAGE_W, 7, "  PHD Inward No.(Mandatory)", border=1, ln=1)

    out = pdf.output(dest='S')
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return out.encode('latin1')


def _ers_pdf_filename(invoice_no):
    inv_no_for_name = invoice_no or "ERS"
    # Replace slashes with hyphens (e.g. "VIS/26-27/1373" -> "VIS-26-27-1373")
    # instead of just stripping them out, then drop anything else unsafe for filenames.
    slashes_replaced = str(inv_no_for_name).replace("/", "-").replace("\\", "-")
    safe_name = "".join(c for c in slashes_replaced if c.isalnum() or c in ("-", "_")) or "ERS_Checklist"
    return f"DOC_{safe_name}.pdf"


# --- SAFE DATE PARSER HELPER ---
def parse_date_safely(val):
    if not val or str(val).strip() in ['', '-', 'nan', 'None']:
        return None
    val_str = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None

# =========================================================================
# GENERIC HELPERS (used by ERS Process & Invoice Data tabs)
# =========================================================================

@st.cache_data(ttl=30, show_spinner=False)
def get_table_df(table_name):
    """Fetch a Supabase table into a DataFrame, newest (highest id) first.
    Cached for 30s so search/pagination/dialogs on the same tab don't
    re-download the whole table on every rerun — call get_table_df.clear()
    right before st.rerun() after any insert/update/delete."""
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data
    except Exception:
        data = []

    if data:
        df = pd.DataFrame(data)
        if 'id' in df.columns:
            id_numeric = pd.to_numeric(df['id'], errors='coerce')
            if id_numeric.notna().any():
                df['id_num'] = id_numeric.fillna(-1)
                df = df.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
            else:
                df = df.iloc[::-1].reset_index(drop=True)
    else:
        df = pd.DataFrame()
    return df


def field_widget(col_name, value, key, container):
    """Renders the right input widget for a column based on its name, returns the value to save."""
    cl = col_name.lower()
    if 'date' in cl:
        parsed = parse_date_safely(value) if value not in (None, '') else None
        raw = container.date_input(col_name.replace("_", " ").title(), value=parsed, key=key)
        return raw.strftime("%d/%m/%Y") if raw else ""
    elif any(k in cl for k in ['amount', 'gst', 'total', 'balance', 'percentage', 'price', 'rate']) and 'number' not in cl:
        try:
            fv = float(value) if value not in (None, '', 'nan') else 0.0
        except (ValueError, TypeError):
            fv = 0.0
        return container.number_input(col_name.replace("_", " ").title(), value=fv, format="%.2f", key=key)
    else:
        sv = "" if value is None else str(value)
        if sv.lower() == 'nan':
            sv = ""
        return container.text_input(col_name.replace("_", " ").title(), value=sv, key=key)


@st.dialog("➕ Add Record", width="large")
def generic_add_dialog(table_name, columns, prefix):
    st.caption(f"Add a new record to {table_name}")
    values = {}

    if not columns:
        st.info("Table has no records yet, so columns can't be auto-detected. Define fields below (name + value), then save.")
        editor_df = pd.DataFrame({"Field": [""], "Value": [""]})
        edited = st.data_editor(editor_df, num_rows="dynamic", use_container_width=True, key=f"{prefix}_add_kv_editor")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Record", type="primary", use_container_width=True, key=f"{prefix}_add_kv_save"):
            insert_data = {}
            for _, r in edited.iterrows():
                f = str(r.get("Field", "")).strip()
                v = str(r.get("Value", "")).strip()
                if f:
                    insert_data[f] = v
            if insert_data:
                try:
                    supabase.table(table_name).insert(insert_data).execute()
                    st.success("✅ Record Added!")
                    get_table_df.clear()
                    st.session_state[f"{prefix}_page"] = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Saving: {e}")
            else:
                st.warning("Please define at least one field.")
        return

    chunks = [columns[i:i + 4] for i in range(0, len(columns), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            values[col_name] = field_widget(col_name, "", f"{prefix}_add_{col_name}", c)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Record", type="primary", use_container_width=True, key=f"{prefix}_add_save"):
        try:
            supabase.table(table_name).insert(values).execute()
            st.success("✅ Record Added!")
            get_table_df.clear()
            st.session_state[f"{prefix}_page"] = 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error Saving: {e}")


@st.dialog("✏️ Edit Record", width="large")
def generic_edit_dialog(table_name, row_data, columns, prefix):
    st.caption("Update record")
    rid = row_data.get('id')
    values = {}
    data_cols = [c for c in columns if c != 'id']

    chunks = [data_cols[i:i + 4] for i in range(0, len(data_cols), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            values[col_name] = field_widget(col_name, row_data.get(col_name, ""), f"{prefix}_edit_{col_name}_{rid}", c)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Update Record", type="primary", use_container_width=True, key=f"{prefix}_edit_save_{rid}"):
        try:
            supabase.table(table_name).update(values).eq("id", rid).execute()
            st.success("✅ Updated Successfully!")
            get_table_df.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error Updating: {e}")


@st.dialog("👁️ View Record", width="large")
def generic_view_dialog(row_data, columns, prefix):
    st.caption("Read-only preview")
    rid = row_data.get('id')
    data_cols = [c for c in columns if c != 'id']

    chunks = [data_cols[i:i + 4] for i in range(0, len(data_cols), 4)]
    for chunk in chunks:
        row_cols = st.columns(len(chunk))
        for c, col_name in zip(row_cols, chunk):
            val = row_data.get(col_name, "")
            c.text_input(col_name.replace("_", " ").title(), value="" if val is None else str(val), disabled=True, key=f"{prefix}_view_{col_name}_{rid}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True, key=f"{prefix}_view_close_{rid}"):
        st.rerun()


@st.dialog("🗑️ Confirm Deletion", width="small")
def generic_delete_dialog(table_name, rid, label, prefix):
    st.warning(f"Delete record '{label}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True, key=f"{prefix}_del_cancel_{rid}"):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True, key=f"{prefix}_del_confirm_{rid}"):
            try:
                supabase.table(table_name).delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


def render_generic_tab(table_name, prefix, tab_title, icon, pdf_button=False):
    """Renders a full CRUD tab (refresh, add, search, export, paginated table with view/edit/delete)
    for any Supabase table, auto-detecting whatever columns it has.
    pdf_button=True adds an extra 📄 button per row (used only for ERS Process)
    that opens the fixed Indus Towers checklist PDF dialog — this never touches
    Supabase, it's purely a download generated on click."""

    col_title, col_ref, col_add, col_export = st.columns([3, 1, 1.5, 1.5])
    with col_title:
        st.markdown(f"<h2 style='margin:0; color:white;'>{icon} {tab_title}</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key=f"{prefix}_refresh"):
            get_table_df.clear()
            st.rerun()

    df = get_table_df(table_name)
    known_cols = [c for c in df.columns if c != 'id'] if not df.empty else st.session_state.get(f"{prefix}_columns", [])
    if not df.empty:
        st.session_state[f"{prefix}_columns"] = known_cols

    with col_add:
        if st.button("➕ Add Record", use_container_width=True, key=f"{prefix}_add_btn"):
            generic_add_dialog(table_name, known_cols, prefix)
    with col_export:
        if st.button("📥 Export Data", use_container_width=True, key=f"{prefix}_export_btn"):
            st.session_state[f"{prefix}_action"] = "export"

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get(f"{prefix}_action") == "export":
        export_df = df.copy()
        if "id" in export_df.columns:
            export_df = export_df.drop(columns=["id"])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name=tab_title[:31])
        st.download_button(
            f"📊 Download {tab_title} Excel",
            data=buffer.getvalue(),
            file_name=f"{table_name}_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key=f"{prefix}_dl_btn"
        )
        st.session_state[f"{prefix}_action"] = ""

    if df.empty:
        st.info(f"No records found in '{table_name}'. Click ➕ Add Record to create the first one.")
        return

    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown(f"##### 🗄️ {tab_title} Records")
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search...", label_visibility="collapsed", key=f"{prefix}_search")

    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    rows_per_page = 10
    total_rows = len(df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state[f"{prefix}_page"] > total_pages:
        st.session_state[f"{prefix}_page"] = total_pages
    elif st.session_state[f"{prefix}_page"] < 1:
        st.session_state[f"{prefix}_page"] = 1

    start_idx = (st.session_state[f"{prefix}_page"] - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df.iloc[start_idx:end_idx].copy()

    data_cols = [c for c in df.columns if c != 'id']
    if pdf_button:
        col_ratios = [0.3, 0.35, 0.35, 0.35, 0.35] + [1.0] * len(data_cols)
        col_labels = ["#", "👁️", "✏️", "🗑️", "📄"] + [c.replace("_", " ").title() for c in data_cols]
    else:
        col_ratios = [0.3, 0.35, 0.35, 0.35] + [1.0] * len(data_cols)
        col_labels = ["#", "👁️", "✏️", "🗑️"] + [c.replace("_", " ").title() for c in data_cols]

    wrap_key = f"{prefix}_table_wrap"
    min_width = max(1200, 260 + len(data_cols) * 170)
    st.markdown(
        f"<style>.st-key-{wrap_key} div[data-testid='stHorizontalBlock'] {{ min-width: {min_width}px !important; }}</style>",
        unsafe_allow_html=True
    )

    with st.container(key=wrap_key, height=560):
        if df_page.empty:
            st.info("No records found.")
        else:
            h_cols = st.columns(col_ratios)
            for h_col, label in zip(h_cols, col_labels):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                serial_no = start_idx + page_pos + 1
                rcols = st.columns(col_ratios)

                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
                with rcols[1]:
                    if st.button("👁️", key=f"{prefix}_view_{rid}", use_container_width=True):
                        generic_view_dialog(row_dict, df.columns.tolist(), prefix)
                with rcols[2]:
                    if st.button("✏️", key=f"{prefix}_editbtn_{rid}", use_container_width=True):
                        generic_edit_dialog(table_name, row_dict, df.columns.tolist(), prefix)
                with rcols[3]:
                    label_val = str(row_dict.get(data_cols[0], rid)) if data_cols else str(rid)
                    if st.button("🗑️", key=f"{prefix}_delbtn_{rid}", use_container_width=True):
                        generic_delete_dialog(table_name, rid, label_val, prefix)

                data_start_idx = 4
                if pdf_button:
                    with rcols[4]:
                        # TRUE 1-CLICK DOWNLOAD: PDF bytes are computed right here,
                        # inline, every render (cheap — pure in-memory PDF build,
                        # no Supabase/network calls, never saved anywhere) so the
                        # button IS the download button — a single click downloads
                        # immediately, no separate "generate" step needed anymore.
                        guess_inv = _ers_find_field(row_dict, [
                            "tally invoice number", "tally invoice no", "tally_invoice_number", "tally invoice",
                            "invoice_number", "invoice no", "invoiceno", "invoice num", "invoice_no",
                            "inv number", "inv no", "invno", "inv_no", "bill number", "bill no",
                            "invoice", "ers number", "ers no", "ers_number"
                        ])
                        guess_po = _ers_find_field(row_dict, ["po_number", "po no", "ponumber", "po", "po num"])
                        guess_date = _ers_find_field(row_dict, ["date", "invoice_date", "invoice date"])
                        try:
                            pdf_bytes = generate_ers_checklist_pdf(guess_inv, guess_po, guess_date)
                            st.download_button(
                                "📥",
                                data=pdf_bytes,
                                file_name=_ers_pdf_filename(guess_inv),
                                mime="application/pdf",
                                key=f"{prefix}_pdfdl_{rid}",
                                help="Download checklist PDF (not saved anywhere)",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.button("⚠️", key=f"{prefix}_pdferr_{rid}", help=f"PDF error: {e}", use_container_width=True, disabled=True)
                    data_start_idx = 5

                for idx, k in enumerate(data_cols, start=data_start_idx):
                    val = row_dict.get(k, '')
                    display_val = val if val is not None and str(val).strip() != '' else '-'
                    rcols[idx].markdown(f"<div class='tbl-cell'>{display_val}</div>", unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state[f"{prefix}_page"] == 1), key=f"{prefix}_prev"):
            st.session_state[f"{prefix}_page"] -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state[f'{prefix}_page']} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state[f"{prefix}_page"] == total_pages), key=f"{prefix}_next"):
            st.session_state[f"{prefix}_page"] += 1
            st.rerun()


# =========================================================================
# BHAGYASHREE INVOICE — Custom PO-based invoice builder
# =========================================================================

BHAGYA_WORKSPACE = "BHAGYASHREE"
BHAGYA_TABLE = "bhagyashree_invoices"

# Placeholder billing-entity details — update address/GSTIN as needed
BILL_FROM_DETAILS = {
    "VISPL": {
        "full_name": "Visiontech Infra Solution Pvt. Ltd.",
        "address": "Address line 1, City, State - PIN",
        "gstin": "GSTIN NOT SET",
    },
    "Whizkey": {
        "full_name": "Whizkey",
        "address": "Address line 1, City, State - PIN",
        "gstin": "GSTIN NOT SET",
    },
}


@st.cache_data(ttl=30, show_spinner=False)
def bhagya_get_site_options():
    """Sites where workspace = BHAGYASHREE, minus project_ids already invoiced.
    Cached because this reruns on every widget interaction inside the Add Invoice dialog."""
    try:
        site_res = supabase.table("site_data").select("*").eq("workspace", BHAGYA_WORKSPACE).execute()
        sites = site_res.data if site_res.data else []
    except Exception as e:
        st.error(f"❌ Error fetching sites: {e}")
        sites = []

    try:
        inv_res = supabase.table(BHAGYA_TABLE).select("project_id").eq("workspace", BHAGYA_WORKSPACE).execute()
        already_invoiced = set(r.get("project_id") for r in (inv_res.data or []) if r.get("project_id"))
    except Exception:
        already_invoiced = set()

    site_map = {}
    for s in sites:
        pid = str(s.get("Project ID", "")).strip()
        if pid and pid not in already_invoiced and pid not in site_map:
            site_map[pid] = s
    return site_map


@st.cache_data(ttl=30, show_spinner=False)
def bhagya_get_po_lines(site_id):
    try:
        res = supabase.table("po_working").select("*") \
            .eq("workspace", BHAGYA_WORKSPACE).eq("Site ID", site_id).execute()
        rows = res.data if res.data else []
        rows.sort(key=lambda r: (r.get("Line Number") is None, r.get("Line Number")))
        return rows
    except Exception:
        return []


def bhagya_generate_pdf(row_data):
    if FPDF is None:
        raise Exception("fpdf library is missing. Please add 'fpdf' to your requirements.txt file.")

    bill_from = row_data.get("bill_from", "")
    bf_details = BILL_FROM_DETAILS.get(bill_from, {"full_name": bill_from, "address": "", "gstin": ""})
    line_items = row_data.get("line_items", [])
    if isinstance(line_items, str):
        try:
            line_items = json.loads(line_items)
        except Exception:
            line_items = []

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(190, 9, "TAX INVOICE", ln=True, align='C')
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 6, "Bill From:", ln=False)
    pdf.cell(95, 6, "Bill To:", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 5, str(bf_details.get("full_name", "")), ln=False)
    pdf.cell(95, 5, "Bhagyashree Enterprises", ln=True)
    pdf.cell(95, 5, str(bf_details.get("address", "")), ln=False)
    pdf.cell(95, 5, f"Site: {row_data.get('site_name', '')}", ln=True)
    pdf.cell(95, 5, f"GSTIN: {bf_details.get('gstin', '')}", ln=False)
    pdf.cell(95, 5, f"Cluster: {row_data.get('cluster', '')}", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", '', 9)
    pdf.cell(63, 6, f"Invoice No: {row_data.get('invoice_no', '')}", ln=False)
    pdf.cell(63, 6, f"Invoice Date: {row_data.get('invoice_date', '')}", ln=False)
    pdf.cell(64, 6, f"Project ID: {row_data.get('project_id', '')}", ln=True)
    pdf.cell(63, 6, f"Site ID: {row_data.get('site_id', '')}", ln=False)
    pdf.cell(127, 6, f"Project Name: {row_data.get('project_name', '')}", ln=True)
    pdf.ln(4)

    # --- Line items table ---
    headers = ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]
    widths = [12, 22, 62, 20, 22, 22, 30]

    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(59, 130, 246)
    pdf.set_text_color(255, 255, 255)
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for li in line_items:
        pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(widths[0], 7, str(li.get("line_number", "")), border=1, align='C', fill=fill)
        pdf.cell(widths[1], 7, str(li.get("item_code", ""))[:14], border=1, align='C', fill=fill)
        pdf.cell(widths[2], 7, str(li.get("description", ""))[:40], border=1, align='L', fill=fill)
        pdf.cell(widths[3], 7, str(li.get("po_qty", "")), border=1, align='C', fill=fill)
        pdf.cell(widths[4], 7, f"{li.get('price', 0):,.0f}", border=1, align='R', fill=fill)
        pdf.cell(widths[5], 7, str(li.get("claim_qty", "")), border=1, align='C', fill=fill)
        pdf.cell(widths[6], 7, f"{li.get('amount', 0):,.0f}", border=1, align='R', fill=fill)
        pdf.ln()
        fill = not fill

    pdf.ln(4)
    subtotal = row_data.get("subtotal", 0) or 0
    cgst = row_data.get("cgst", 0) or 0
    sgst = row_data.get("sgst", 0) or 0
    total = row_data.get("total", 0) or 0

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(150, 7, "Subtotal", border=0, align='R')
    pdf.cell(40, 7, f"Rs. {subtotal:,.0f}", border=0, align='R', ln=True)
    pdf.cell(150, 7, "CGST (9%)", border=0, align='R')
    pdf.cell(40, 7, f"Rs. {cgst:,.0f}", border=0, align='R', ln=True)
    pdf.cell(150, 7, "SGST (9%)", border=0, align='R')
    pdf.cell(40, 7, f"Rs. {sgst:,.0f}", border=0, align='R', ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(150, 9, "Final Amount", border=0, align='R')
    pdf.cell(40, 9, f"Rs. {total:,.0f}", border=0, align='R', ln=True)

    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, (bytes, bytearray)):
        return bytes(pdf_output)
    return pdf_output.encode('latin1')


@st.dialog("➕ Add New Invoice (Bhagyashree)", width="large")
def bhagya_add_invoice_dialog():
    st.caption("PO Working ke saamne wale Claim Qty bharke invoice banayein")

    bf1, bf2 = st.columns(2)
    with bf1:
        bill_from = st.selectbox("Bill From *", options=list(BILL_FROM_DETAILS.keys()), key="bhagya_bill_from")
    with bf2:
        invoice_no = st.text_input("Invoice No *", key="bhagya_inv_no")

    site_map = bhagya_get_site_options()
    project_options = ["Select"] + sorted(site_map.keys())

    pc1, pc2 = st.columns(2)
    with pc1:
        selected_pid = st.selectbox("Project ID *", options=project_options, key="bhagya_project_id")
    with pc2:
        invoice_date = st.date_input("Invoice Date", value=date.today(), format="DD/MM/YYYY", key="bhagya_inv_date")

    if selected_pid == "Select":
        st.info("Pehle ek Project ID select karein.")
        return

    site_row = site_map.get(selected_pid, {})
    site_id = site_row.get("Site ID", "")

    st.markdown('<div class="modal-section-title">📍 SITE DETAILS</div>', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    with d1: st.text_input("Site ID", value=site_row.get("Site ID", ""), disabled=True, key="bhagya_disp_site_id")
    with d2: st.text_input("Site Name", value=site_row.get("Site Name", ""), disabled=True, key="bhagya_disp_site_name")
    with d3: st.text_input("Cluster", value=site_row.get("Cluster", ""), disabled=True, key="bhagya_disp_cluster")
    with d4: st.text_input("Project Name", value=site_row.get("Project Name", ""), disabled=True, key="bhagya_disp_proj_name")

    st.markdown('<div class="modal-section-title">📦 PO LINE ITEMS — Enter Claim Qty</div>', unsafe_allow_html=True)
    po_lines = bhagya_get_po_lines(site_id)

    if not po_lines:
        st.warning("Is Project ID ke liye PO Working me koi line nahi mili.")
        return

    h_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
    for c, label in zip(h_cols, ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]):
        c.markdown(f"<b style='color:#94a3b8; font-size:0.78rem;'>{label}</b>", unsafe_allow_html=True)

    line_items = []
    subtotal = 0.0
    for po in po_lines:
        r_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
        line_no = po.get("Line Number", "")
        item_code = po.get("Item Num", "")
        description = po.get("Description", "")
        po_qty = po.get("PO Qty", 0) or 0
        price = po.get("Price", 0) or 0

        r_cols[0].markdown(f"<div class='tbl-cell'>{line_no}</div>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<div class='tbl-cell'>{item_code}</div>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<div class='tbl-cell'>{description}</div>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<div class='tbl-cell'>{po_qty}</div>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<div class='tbl-cell'>{price:,.0f}</div>", unsafe_allow_html=True)

        claim_qty = r_cols[5].number_input(
            "Claim Qty", min_value=0, max_value=int(po_qty) if po_qty else 0, step=1, value=0,
            key=f"bhagya_claim_{line_no}_{item_code}", label_visibility="collapsed"
        )
        amount = claim_qty * price
        r_cols[6].markdown(f"<div class='tbl-cell' style='font-weight:800; color:#3b82f6;'>{amount:,.0f}</div>", unsafe_allow_html=True)

        subtotal += amount
        line_items.append({
            "line_number": line_no,
            "item_code": item_code,
            "description": description,
            "po_qty": po_qty,
            "price": price,
            "claim_qty": claim_qty,
            "amount": amount,
        })

    cgst = subtotal * 0.09
    sgst = subtotal * 0.09
    total = subtotal + cgst + sgst

    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 14px 20px; border-radius: 10px; margin-top:15px;">
            <div style="display:flex; justify-content:space-between; padding:3px 0;"><span style="color:#94a3b8; font-weight:700;">Subtotal</span><span style="color:#ffffff; font-weight:800;">₹ {subtotal:,.0f}</span></div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;"><span style="color:#94a3b8; font-weight:700;">CGST (9%)</span><span style="color:#ffffff; font-weight:800;">₹ {cgst:,.0f}</span></div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;"><span style="color:#94a3b8; font-weight:700;">SGST (9%)</span><span style="color:#ffffff; font-weight:800;">₹ {sgst:,.0f}</span></div>
            <div style="display:flex; justify-content:space-between; padding:8px 0 0 0; border-top:1px solid rgba(255,255,255,0.15); margin-top:6px;"><span style="color:#3b82f6; font-weight:900; font-size:1.1rem;">Final Amount</span><span style="color:#3b82f6; font-weight:900; font-size:1.1rem;">₹ {total:,.0f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Invoice", type="primary", use_container_width=True, key="bhagya_save_btn"):
        if not invoice_no.strip():
            st.error("⚠️ Invoice No is required!")
        elif subtotal <= 0:
            st.error("⚠️ Kam se kam ek line me Claim Qty > 0 dalein!")
        else:
            payload = {
                "workspace": BHAGYA_WORKSPACE,
                "invoice_no": invoice_no.strip(),
                "invoice_date": str(invoice_date),
                "bill_from": bill_from,
                "project_id": selected_pid,
                "site_id": site_row.get("Site ID", ""),
                "site_name": site_row.get("Site Name", ""),
                "cluster": site_row.get("Cluster", ""),
                "project_name": site_row.get("Project Name", ""),
                "line_items": line_items,
                "subtotal": subtotal,
                "cgst": cgst,
                "sgst": sgst,
                "total": total,
            }
            try:
                supabase.table(BHAGYA_TABLE).insert(payload).execute()
                st.success("✅ Invoice Saved! Neeche table me 🧾 button se PDF download kar sakte hain.")
                get_table_df.clear()
                bhagya_get_site_options.clear()
                st.session_state.bhagya_page = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving invoice: {e}")


@st.dialog("🧾 Invoice Detail & Download", width="large")
def bhagya_view_invoice_dialog(row_data):
    st.caption(f"Invoice No: {row_data.get('invoice_no','')}")

    d1, d2, d3, d4 = st.columns(4)
    with d1: st.text_input("Bill From", value=row_data.get("bill_from", ""), disabled=True)
    with d2: st.text_input("Project ID", value=row_data.get("project_id", ""), disabled=True)
    with d3: st.text_input("Site ID", value=row_data.get("site_id", ""), disabled=True)
    with d4: st.text_input("Invoice Date", value=str(row_data.get("invoice_date", "")), disabled=True)

    st.text_input("Site Name / Cluster / Project Name",
                   value=f"{row_data.get('site_name','')} | {row_data.get('cluster','')} | {row_data.get('project_name','')}",
                   disabled=True)

    line_items = row_data.get("line_items", [])
    if isinstance(line_items, str):
        try:
            line_items = json.loads(line_items)
        except Exception:
            line_items = []

    st.markdown('<div class="modal-section-title">📦 LINE ITEMS</div>', unsafe_allow_html=True)
    h_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
    for c, label in zip(h_cols, ["Line", "Item Code", "Description", "PO Qty", "Price", "Claim Qty", "Amount"]):
        c.markdown(f"<b style='color:#94a3b8; font-size:0.78rem;'>{label}</b>", unsafe_allow_html=True)
    for li in line_items:
        r_cols = st.columns([0.8, 1.3, 3.0, 1.0, 1.2, 1.2, 1.4])
        r_cols[0].markdown(f"<span style='color:#e2e8f0;'>{li.get('line_number','')}</span>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<span style='color:#e2e8f0;'>{li.get('item_code','')}</span>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<span style='color:#e2e8f0;'>{li.get('description','')}</span>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<span style='color:#e2e8f0;'>{li.get('po_qty','')}</span>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<span style='color:#e2e8f0;'>{li.get('price',0):,.0f}</span>", unsafe_allow_html=True)
        r_cols[5].markdown(f"<span style='color:#e2e8f0;'>{li.get('claim_qty','')}</span>", unsafe_allow_html=True)
        r_cols[6].markdown(f"<span style='color:#4ade80; font-weight:700;'>{li.get('amount',0):,.0f}</span>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 12px 18px; border-radius: 8px; margin-top:15px; display:flex; justify-content:space-between;">
            <div style="color:#ffffff; font-weight:700;">Subtotal: <span style="color:#3b82f6;">₹ {row_data.get('subtotal',0):,.0f}</span></div>
            <div style="color:#ffffff; font-weight:700;">CGST+SGST: <span style="color:#f59e0b;">₹ {(row_data.get('cgst',0)+row_data.get('sgst',0)):,.0f}</span></div>
            <div style="color:#ffffff; font-weight:700;">Final: <span style="color:#4ade80;">₹ {row_data.get('total',0):,.0f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_dl, col_close = st.columns(2)
    with col_dl:
        try:
            pdf_bytes = bhagya_generate_pdf(row_data)
            st.download_button(
                "📄 Download PDF", data=pdf_bytes,
                file_name=f"{row_data.get('invoice_no','invoice')}.pdf", mime="application/pdf",
                use_container_width=True, type="primary"
            )
        except Exception as e:
            st.error(str(e))
    with col_close:
        if st.button("Close", use_container_width=True):
            st.rerun()


def render_bhagyashree_tab():
    col_title, col_ref, col_add = st.columns([3.5, 1, 1.5])
    with col_title:
        st.markdown("<h2 style='margin:0; color:white;'>🏢 Bhagyashree Invoice</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key="bhagya_refresh"):
            get_table_df.clear()
            bhagya_get_site_options.clear()
            st.rerun()
    with col_add:
        if st.button("➕ Add New Invoice", use_container_width=True, key="bhagya_add_btn"):
            bhagya_add_invoice_dialog()

    st.markdown("<br>", unsafe_allow_html=True)

    df = get_table_df(BHAGYA_TABLE)

    if not df.empty:
        buffer = io.BytesIO()
        export_df = df.drop(columns=[c for c in ["line_items"] if c in df.columns])
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Bhagyashree Invoices')
        st.download_button(
            "📥 Download Excel", data=buffer.getvalue(),
            file_name="Bhagyashree_Invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="bhagya_dl_btn"
        )

    if 'bhagya_page' not in st.session_state:
        st.session_state.bhagya_page = 1

    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown("##### 🗄️ Bhagyashree Invoices")
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search...", label_visibility="collapsed", key="bhagya_search")

    if df.empty:
        st.info("Abhi tak koi invoice nahi bani. ➕ Add New Invoice se shuru karein.")
        return

    view_df = df.copy()
    if search_query:
        mask = view_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        view_df = view_df[mask]

    rows_per_page = 10
    total_rows = len(view_df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
    if st.session_state.bhagya_page > total_pages: st.session_state.bhagya_page = total_pages
    elif st.session_state.bhagya_page < 1: st.session_state.bhagya_page = 1
    start_idx = (st.session_state.bhagya_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    page_df = view_df.iloc[start_idx:end_idx]

    b_cols = ["#", "🧾", "Invoice No", "Date", "Bill From", "Project ID", "Site Name", "Subtotal", "GST", "Total"]
    b_ratios = [0.3, 0.35, 1.1, 1.0, 1.0, 1.0, 1.4, 1.0, 1.0, 1.1]

    with st.container(key="bhagya_table_wrap", height=520):
        h_cols = st.columns(b_ratios)
        for h_col, label in zip(h_cols, b_cols):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

        for pos, (_, row) in enumerate(page_df.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            r_cols = st.columns(b_ratios)
            r_cols[0].markdown(f"<div class='tbl-cell tbl-serial'>{start_idx + pos + 1}</div>", unsafe_allow_html=True)
            with r_cols[1]:
                if st.button("🧾", key=f"bhagya_view_{rid}", use_container_width=True):
                    bhagya_view_invoice_dialog(row_dict)
            r_cols[2].markdown(f"<div class='tbl-cell'>{row_dict.get('invoice_no','-')}</div>", unsafe_allow_html=True)
            r_cols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('invoice_date','-')}</div>", unsafe_allow_html=True)
            r_cols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('bill_from','-')}</div>", unsafe_allow_html=True)
            r_cols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('project_id','-')}</div>", unsafe_allow_html=True)
            r_cols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('site_name','-')}</div>", unsafe_allow_html=True)
            r_cols[7].markdown(f"<div class='tbl-cell'>{row_dict.get('subtotal',0):,.0f}</div>", unsafe_allow_html=True)
            gst_total = (row_dict.get('cgst', 0) or 0) + (row_dict.get('sgst', 0) or 0)
            r_cols[8].markdown(f"<div class='tbl-cell'>{gst_total:,.0f}</div>", unsafe_allow_html=True)
            r_cols[9].markdown(f"<div class='tbl-cell' style='font-weight:800; color:#4ade80;'>{row_dict.get('total',0):,.0f}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.bhagya_page == 1), key="bhagya_prev"):
            st.session_state.bhagya_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state.bhagya_page} of {total_pages} (Total: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.bhagya_page == total_pages), key="bhagya_next"):
            st.session_state.bhagya_page += 1
            st.rerun()


# =========================================================================
# VIS INVOICE — DIALOGS (unchanged logic from original file)
# =========================================================================

@st.dialog("📄 Add Invoice Record", width="large")
def add_invoice_dialog():
    st.caption("Configure invoice details, taxation, and milestone payments")

    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", placeholder="Circle name")
        with c2: invoice_number = st.text_input("Invoice_number", placeholder="Inv Number")
        with c3:
            raw_inv_date = st.date_input("Invoice_date", value=None)
            invoice_date = raw_inv_date.strftime("%d/%m/%Y") if raw_inv_date else ""
        with c4: project_id = st.text_input("Project_id", placeholder="Project ID")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", placeholder="Site ID")
        with c6: site_name = st.text_input("Site_name", placeholder="Site Name")
        with c7: po_number = st.text_input("Po_number", placeholder="PO Number")
        with c8: wcc_number = st.text_input("Wcc_number", placeholder="WCC Number")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION (Basic + CGST + SGST + IGST = Total)</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=0.0, format="%.2f")
        with c10: cgst = st.number_input("CGST", value=0.0, format="%.2f")
        with c11: sgst = st.number_input("SGST", value=0.0, format="%.2f")
        with c12: igst = st.number_input("IGST", value=0.0, format="%.2f")

        total = basic_amount + cgst + sgst + igst
        with c13:
            st.markdown(f"<p style='color:#3b82f6; font-weight:800; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", placeholder="Receipt No")
        with c15: percentage_amount = st.number_input("%Amount", value=0.0, format="%.2f")

        sub_status = st.text_input("Sub_status", placeholder="Sub Status")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=0.0, format="%.2f")
        with p2:
            raw_p1_date = st.date_input("Payment_1_date", value=None)
            payment_1_date = raw_p1_date.strftime("%d/%m/%Y") if raw_p1_date else ""
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=0.0, format="%.2f")
        with p4:
            raw_p2_date = st.date_input("Payment_2_date", value=None)
            payment_2_date = raw_p2_date.strftime("%d/%m/%Y") if raw_p2_date else ""
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=0.0, format="%.2f")
        with p6:
            raw_p3_date = st.date_input("Payment_3_date", value=None)
            payment_3_date = raw_p3_date.strftime("%d/%m/%Y") if raw_p3_date else ""

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=0.0, format="%.2f")
        with b2: remark = st.text_input("Remark", placeholder="Enter remarks...")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            insert_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "sub_status": sub_status,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            try:
                supabase.table("invoice_management").insert(insert_data).execute()
                st.success("✅ Invoice Added Successfully!")
                get_table_df.clear()
                st.session_state.current_page = 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Saving: {e}")


@st.dialog("✏️ Edit Invoice Record", width="large")
def edit_invoice_dialog(row_data):
    st.caption("Update invoice parameters")

    with st.container():
        st.markdown('<div class="modal-section-title">🧾 GENERAL & SITE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: circle = st.text_input("Circle", value=str(row_data.get('circle', '')), key="ed_circle")
        with c2: invoice_number = st.text_input("Invoice_number", value=str(row_data.get('invoice_number', '')), key="ed_inv_num")
        with c3:
            parsed_date = parse_date_safely(row_data.get('invoice_date', ''))
            raw_inv_date = st.date_input("Invoice_date", value=parsed_date, key="ed_inv_date")
            invoice_date = raw_inv_date.strftime("%d/%m/%Y") if raw_inv_date else ""
        with c4: project_id = st.text_input("Project_id", value=str(row_data.get('project_id', '')), key="ed_proj_id")

        c5, c6, c7, c8 = st.columns(4)
        with c5: site_id = st.text_input("Site_id", value=str(row_data.get('site_id', '')), key="ed_site_id")
        with c6: site_name = st.text_input("Site_name", value=str(row_data.get('site_name', '')), key="ed_site_name")
        with c7: po_number = st.text_input("Po_number", value=str(row_data.get('po_number', '')), key="ed_po_num")
        with c8: wcc_number = st.text_input("Wcc_number", value=str(row_data.get('wcc_number', '')), key="ed_wcc_num")

        st.markdown('<div class="modal-section-title">💰 AMOUNTS & TAXATION</div>', unsafe_allow_html=True)
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9: basic_amount = st.number_input("Basic_amount", value=float(row_data.get('basic_amount', 0.0) or 0.0), format="%.2f", key="ed_basic")
        with c10: cgst = st.number_input("CGST", value=float(row_data.get('cgst', 0.0) or 0.0), format="%.2f", key="ed_cgst")
        with c11: sgst = st.number_input("SGST", value=float(row_data.get('sgst', 0.0) or 0.0), format="%.2f", key="ed_sgst")
        with c12: igst = st.number_input("IGST", value=float(row_data.get('igst', 0.0) or 0.0), format="%.2f", key="ed_igst")

        total = basic_amount + cgst + sgst + igst
        with c13:
            st.markdown(f"<p style='color:#3b82f6; font-weight:800; margin-top:28px;'>Total: {total:.2f}</p>", unsafe_allow_html=True)

        c14, c15 = st.columns(2)
        with c14: receipt_number = st.text_input("Receipt_number", value=str(row_data.get('receipt_number', '')), key="ed_receipt")
        with c15: percentage_amount = st.number_input("%Amount", value=float(row_data.get('percentage_amount', 0.0) or 0.0), format="%.2f", key="ed_pct")

        sub_status = st.text_input("Sub_status", value=str(row_data.get('sub_status', '')), key="ed_substatus")

        st.markdown('<div class="modal-section-title">💳 PAYMENTS & BALANCE</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6 = st.columns(6)
        with p1: payment_1_amount = st.number_input("Paymet_1_amount", value=float(row_data.get('payment_1_amount', 0.0) or 0.0), format="%.2f", key="ed_p1_amt")
        with p2:
            p1_d = parse_date_safely(row_data.get('payment_1_date', ''))
            raw_p1 = st.date_input("Payment_1_date", value=p1_d, key="ed_p1_date")
            payment_1_date = raw_p1.strftime("%d/%m/%Y") if raw_p1 else ""
        with p3: payment_2_amount = st.number_input("Paymet_2_amount", value=float(row_data.get('payment_2_amount', 0.0) or 0.0), format="%.2f", key="ed_p2_amt")
        with p4:
            p2_d = parse_date_safely(row_data.get('payment_2_date', ''))
            raw_p2 = st.date_input("Payment_2_date", value=p2_d, key="ed_p2_date")
            payment_2_date = raw_p2.strftime("%d/%m/%Y") if raw_p2 else ""
        with p5: payment_3_amount = st.number_input("Paymet_3_amount", value=float(row_data.get('payment_3_amount', 0.0) or 0.0), format="%.2f", key="ed_p3_amt")
        with p6:
            p3_d = parse_date_safely(row_data.get('payment_3_date', ''))
            raw_p3 = st.date_input("Payment_3_date", value=p3_d, key="ed_p3_date")
            payment_3_date = raw_p3.strftime("%d/%m/%Y") if raw_p3 else ""

        b1, b2 = st.columns([2, 4])
        with b1: balance = st.number_input("Balance", value=float(row_data.get('balance', 0.0) or 0.0), format="%.2f", key="ed_bal")
        with b2: remark = st.text_input("Remark", value=str(row_data.get('remark', '')), key="ed_rem")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Update Invoice", type="primary", use_container_width=True):
            update_data = {
                "circle": circle,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "basic_amount": basic_amount,
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "total": total,
                "project_id": project_id,
                "site_id": site_id,
                "site_name": site_name,
                "po_number": po_number,
                "wcc_number": wcc_number,
                "receipt_number": receipt_number,
                "percentage_amount": percentage_amount,
                "sub_status": sub_status,
                "payment_1_amount": payment_1_amount,
                "payment_1_date": payment_1_date,
                "payment_2_amount": payment_2_amount,
                "payment_2_date": payment_2_date,
                "payment_3_amount": payment_3_amount,
                "payment_3_date": payment_3_date,
                "balance": balance,
                "remark": remark
            }
            try:
                supabase.table("invoice_management").update(update_data).eq("id", row_data['id']).execute()
                st.success("✅ Invoice Updated Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating: {e}")


@st.dialog("👁️ View Invoice Record", width="large")
def view_invoice_dialog(row_data):
    st.caption("Read-only preview")
    st.markdown('<div class="modal-section-title">🧾 GENERAL DETAILS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("Circle", value=row_data.get('circle', ''), disabled=True)
    with c2: st.text_input("Invoice Number", value=row_data.get('invoice_number', ''), disabled=True)
    with c3: st.text_input("Invoice Date", value=row_data.get('invoice_date', ''), disabled=True)
    with c4: st.text_input("Project ID", value=row_data.get('project_id', ''), disabled=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5: st.text_input("Site ID", value=row_data.get('site_id', ''), disabled=True)
    with c6: st.text_input("Site Name", value=row_data.get('site_name', ''), disabled=True)
    with c7: st.text_input("PO Number", value=row_data.get('po_number', ''), disabled=True)
    with c8: st.text_input("WCC Number", value=row_data.get('wcc_number', ''), disabled=True)

    st.markdown('<div class="modal-section-title">💰 AMOUNTS & TOTAL</div>', unsafe_allow_html=True)
    c9, c10, c11, c12, c13, c14 = st.columns(6)

    b_amt = float(row_data.get('basic_amount', 0) or 0)
    c_amt = float(row_data.get('cgst', 0) or 0)
    s_amt = float(row_data.get('sgst', 0) or 0)
    i_amt = float(row_data.get('igst', 0) or 0)
    t_amt = row_data.get('total')
    if not t_amt or str(t_amt).lower() in ['nan', 'none', '']:
        t_amt = b_amt + c_amt + s_amt + i_amt

    with c9: st.text_input("Basic Amount", value=str(b_amt), disabled=True)
    with c10: st.text_input("CGST", value=str(c_amt), disabled=True)
    with c11: st.text_input("SGST", value=str(s_amt), disabled=True)
    with c12: st.text_input("IGST", value=str(i_amt), disabled=True)
    with c13: st.text_input("Total", value=str(t_amt), disabled=True)
    with c14: st.text_input("% Amount", value=str(row_data.get('percentage_amount', '')), disabled=True)

    st.text_input("Sub Status", value=row_data.get('sub_status', ''), disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True):
        st.rerun()


@st.dialog("🗑️ Confirm Deletion", width="small")
def delete_invoice_dialog(rid, inv_num):
    st.warning(f"Delete invoice '{inv_num}'? This action cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                supabase.table("invoice_management").delete().eq("id", rid).execute()
                st.success("✅ Deleted Successfully!")
                get_table_df.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


@st.dialog("📤 Bulk Upload Invoices", width="large")
def bulk_upload_dialog():
    st.caption("Upload an Excel file to bulk import invoice records.")
    uploaded_file = st.file_uploader("Choose File", type=["xlsx", "xls", "tsv"], key="bulk_inv_file")

    if uploaded_file and st.button("🚀 Process & Upload", type="primary", use_container_width=True):
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df_upload = pd.read_excel(uploaded_file)
            else:
                df_upload = pd.read_csv(uploaded_file, sep='\t')

            added = 0
            for _, row in df_upload.iterrows():
                p_id = str(row.get("project_id", row.get("Project ID", ""))).strip()
                if not p_id or p_id.lower() == "nan": continue

                insert_dict = {}
                for col in columns_list:
                    if col != "id" and col != "🎯 Select":
                        val = row.get(col, row.get(col.lower(), ""))
                        insert_dict[col] = str(val).strip() if pd.notna(val) and str(val).lower() != 'nan' else ""

                try:
                    b = float(insert_dict.get('basic_amount', 0) or 0)
                    c = float(insert_dict.get('cgst', 0) or 0)
                    s = float(insert_dict.get('sgst', 0) or 0)
                    i = float(insert_dict.get('igst', 0) or 0)
                    insert_dict['total'] = b + c + s + i
                except:
                    pass

                try:
                    supabase.table("invoice_management").insert(insert_dict).execute()
                    added += 1
                except:
                    pass
            st.success(f"✅ Bulk Upload Complete! {added} records added.")
            get_table_df.clear()
            st.session_state.current_page = 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")


# --- TOP BANNER (shared across all tabs) ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🧾 Invoice Management Hub
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
columns_list = [
    "id", "circle", "invoice_number", "invoice_date", "basic_amount", "cgst", "sgst", "igst", "total",
    "project_id", "site_id", "site_name", "po_number", "wcc_number", "receipt_number", "percentage_amount",
    "sub_status",
    "payment_1_amount", "payment_1_date", "payment_2_amount", "payment_2_date", "payment_3_amount", "payment_3_date",
    "balance", "remark"
]

# --- NAVIGATION BAR (custom buttons, replaces st.tabs for guaranteed styling) ---
if 'active_page' not in st.session_state:
    st.session_state.active_page = "vis"

NAV_PAGES = [
    ("vis", "📋 VIS Invoice"),
    ("ers", "⚙️ ERS Process"),
    ("invdata", "📁 Invoice Data"),
    ("bhagya", "🏢 Bhagyashree Invoice"),
    ("saitele", "📡 Sai Tele Invoice"),
]

with st.container(key="nav_bar"):
    nav_cols = st.columns(len(NAV_PAGES))
    for nav_col, (page_id, page_label) in zip(nav_cols, NAV_PAGES):
        is_active = st.session_state.active_page == page_id
        with nav_col:
            if st.button(page_label, key=f"nav_{page_id}", use_container_width=True, type=("primary" if is_active else "secondary")):
                st.session_state.active_page = page_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================================
# TAB 1 — VIS INVOICE (unchanged, uses "invoice_management" table)
# =========================================================================
if st.session_state.active_page == "vis":
    # --- 4. TOP ACTION BAR ---
    col_title, col_ref, col_add, col_upload, col_export = st.columns([3, 1, 1.5, 1.5, 1.5])
    with col_title:
        st.markdown("<h2 style='margin:0; color:white;'>📊 Live Invoices Master</h2>", unsafe_allow_html=True)
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key="vis_refresh"):
            get_table_df.clear()
            st.rerun()
    with col_add:
        if st.button("➕ Add Invoice", use_container_width=True, key="vis_add"):
            add_invoice_dialog()
    with col_upload:
        if st.button("📤 Bulk Upload", use_container_width=True, key="vis_bulk"):
            bulk_upload_dialog()
    with col_export:
        if st.button("📥 Export Data", use_container_width=True, key="vis_export"):
            st.session_state.action = "export"

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. FETCH DATA FROM SUPABASE (cached — see get_table_df above) ---
    table_name = "invoice_management"

    df = get_table_df(table_name).copy()
    if not df.empty:
        for col in columns_list:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=columns_list)

    if "🎯 Select" not in df.columns:
        df.insert(0, "🎯 Select", False)

    # Export Trigger
    if st.session_state.get('action') == "export":
        export_df = df.copy()
        if "🎯 Select" in export_df.columns: export_df = export_df.drop(columns=["🎯 Select"])
        if "id" in export_df.columns: export_df = export_df.drop(columns=["id"])

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Invoices')
        st.download_button("📊 Download Excel File", data=buffer.getvalue(), file_name="Invoice_Management_Export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary", key="vis_dl")
        st.session_state.action = ""

    # --- LIVE SEARCH BOX ---
    col_table_title, col_search = st.columns([7, 3])
    with col_table_title:
        st.markdown("##### 🗄️ Database Records")
    with col_search:
        search_query = st_keyup("Search", placeholder="🔍 Search invoices...", label_visibility="collapsed", key="vis_search")

    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    # --- 6. PAGINATION LOGIC ---
    rows_per_page = 10
    total_rows = len(df)
    total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

    if st.session_state.current_page > total_pages: st.session_state.current_page = total_pages
    elif st.session_state.current_page < 1: st.session_state.current_page = 1

    start_idx = (st.session_state.current_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df.iloc[start_idx:end_idx].copy()

    keys_seq = [
        'circle', 'invoice_number', 'invoice_date', 'basic_amount', 'cgst', 'sgst', 'igst', 'total',
        'project_id', 'site_id', 'site_name', 'po_number', 'wcc_number', 'receipt_number', 'percentage_amount',
        'sub_status',
        'payment_1_amount', 'payment_1_date', 'payment_2_amount', 'payment_2_date', 'payment_3_amount', 'payment_3_date',
        'balance', 'remark'
    ]

    COL_RATIOS = [0.3, 0.35, 0.35, 0.35] + [1.0] * len(keys_seq)
    COL_LABELS = [
        "#", "👁️", "✏️", "🗑️",
        "Circle", "Invoice No", "Invoice Date", "Basic Amount", "CGST", "SGST", "IGST", "Total",
        "Project ID", "Site ID", "Site Name", "PO Number", "WCC Number", "Receipt No", "% Amount",
        "Sub Status",
        "Pay 1 Amt", "Pay 1 Date", "Pay 2 Amt", "Pay 2 Date", "Pay 3 Amt", "Pay 3 Date", "Balance", "Remark"
    ]

    with st.container(key="invoice_table_wrap", height=560):
        if df_page.empty:
            st.info("No invoice records found.")
        else:
            h_cols = st.columns(COL_RATIOS)
            for h_col, label in zip(h_cols, COL_LABELS):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

            for page_pos, (_, row) in enumerate(df_page.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                serial_no = start_idx + page_pos + 1
                rcols = st.columns(COL_RATIOS)

                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
                with rcols[1]:
                    if st.button("👁️", key=f"view_inv_{rid}", use_container_width=True):
                        view_invoice_dialog(row_dict)
                with rcols[2]:
                    if st.button("✏️", key=f"edit_inv_{rid}", use_container_width=True):
                        edit_invoice_dialog(row_dict)
                with rcols[3]:
                    if st.button("🗑️", key=f"del_inv_{rid}", use_container_width=True):
                        delete_invoice_dialog(rid, row_dict.get('invoice_number', ''))

                for idx, k in enumerate(keys_seq, start=4):
                    val = row_dict.get(k, '')

                    if k == 'total' and (val is None or str(val).strip() == '' or str(val).lower() == 'nan'):
                        try:
                            b = float(row_dict.get('basic_amount', 0) or 0)
                            c = float(row_dict.get('cgst', 0) or 0)
                            s = float(row_dict.get('sgst', 0) or 0)
                            i = float(row_dict.get('igst', 0) or 0)
                            val = f"{b + c + s + i:.2f}"
                        except:
                            val = '-'

                    display_val = val if val is not None and str(val).strip() != '' else '-'
                    rcols[idx].markdown(f"<div class='tbl-cell'>{display_val}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 7. PAGINATION CONTROLS ---
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 1), key="vis_prev"):
            st.session_state.current_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<div class='page-count'>Page {st.session_state.current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages), key="vis_next"):
            st.session_state.current_page += 1
            st.rerun()

# =========================================================================
# TAB 2 — ERS PROCESS (Supabase table: "ERSprocess")
# =========================================================================
elif st.session_state.active_page == "ers":
    render_generic_tab(table_name="ERSprocess", prefix="ers", tab_title="ERS Process", icon="⚙️", pdf_button=True)

# =========================================================================
# TAB 3 — INVOICE DATA (Supabase table: "Invoicedata")
# =========================================================================
elif st.session_state.active_page == "invdata":
    render_generic_tab(table_name="Invoicedata", prefix="invdata", tab_title="Invoice Data", icon="📁")

# =========================================================================
# TAB 4 — BHAGYASHREE INVOICE (Supabase table: "BhagyashreeInvoice")
# =========================================================================
elif st.session_state.active_page == "bhagya":
    render_bhagyashree_tab()

# =========================================================================
# TAB 5 — SAI TELE INVOICE (Supabase table: "SaiTeleInvoice")
# =========================================================================
elif st.session_state.active_page == "saitele":
    render_generic_tab(table_name="SaiTeleInvoice", prefix="saitele", tab_title="Sai Tele Invoice", icon="📡")
