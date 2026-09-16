import streamlit as st
import pandas as pd
import math
import io
import json
from datetime import datetime
from uuid import uuid4
from supabase import create_client, Client
from st_keyup import st_keyup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="JMS - Joint Measurement Sheet", page_icon="🧾", layout="wide")

# --- SESSION STATE ---
if 'jmspage_open_row' not in st.session_state:
    st.session_state.jmspage_open_row = None
if 'jmspage_loaded_key' not in st.session_state:
    st.session_state.jmspage_loaded_key = None
if 'jmspage_lines' not in st.session_state:
    st.session_state.jmspage_lines = []
if 'jmspage_last_pdf' not in st.session_state:
    st.session_state.jmspage_last_pdf = None
if 'jmspage_add_gen' not in st.session_state:
    st.session_state.jmspage_add_gen = 0
if 'jmspage_current_page' not in st.session_state:
    st.session_state.jmspage_current_page = 1

# --- GUARD AGAINST STALE DIALOG STATE AFTER PAGE NAVIGATION ---
# session_state is shared across every page in the app, so if a JMS dialog was left
# open (user navigated away without clicking "Close"), jmspage_open_row would still
# be set on the next visit and the dialog would auto-pop-up. We tie "the dialog is
# genuinely open on THIS page visit" to a URL marker instead: it only survives
# reruns caused by interacting with widgets inside this same page (typing, editing,
# clicking Save/Add/Reload — none of which change the URL), but a fresh sidebar
# navigation to this page does NOT carry it over, so we know to reset stale state.
if st.query_params.get("jms_ctx") != "open":
    st.session_state.jmspage_open_row = None
    st.session_state.jmspage_loaded_key = None
    st.session_state.jmspage_last_pdf = None

# --- MULTI-COMPANY TAB SETUP (same as Site Data page) ---
SITE_COMPANIES = [
    ("VISPL", "VISPL"),
    ("Bhagyashree", "Bhagyashree"),
    ("Sai Tele", "Sai Tele"),
]
SITE_COMPANY_WORKSPACE_MAP = {
    "VISPL": "VISPL",
    "Bhagyashree": "BHAGYASHREE",
    "Sai Tele": "SAI TELE SERVICES",
}
if 'site_active_company' not in st.session_state:
    st.session_state.site_active_company = "VISPL"
st.session_state['active_workspace'] = SITE_COMPANY_WORKSPACE_MAP.get(st.session_state.site_active_company, "VISPL")

# --- 2. CSS (nav bar + table look, matching Site Data page) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.25);
    }
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDialog"] > div {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #0f172a !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p {
        color: #1e293b !important;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #0f172a !important; font-weight: 700 !important; letter-spacing: 0.5px;
    }

    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #334155; margin-top: 10px; }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION (same theme as Site Data page,
       so switching pages doesn't flip the sidebar's look)
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

    /* Company Nav Bar */
    .st-key-jms_company_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-jms_company_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover {
        background: #f1f5f9 !important; color: #0f172a !important;
        border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
    }
    .st-key-jms_company_nav_bar button[kind="secondary"] p,
    .st-key-jms_company_nav_bar button[kind="secondary"] span,
    .st-key-jms_company_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover p,
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover span,
    .st-key-jms_company_nav_bar button[kind="secondary"]:hover div { color: #0f172a !important; }
    .st-key-jms_company_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    .st-key-jms_company_nav_bar button[kind="primary"] p,
    .st-key-jms_company_nav_bar button[kind="primary"] span,
    .st-key-jms_company_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; }

    /* Table wrap */
    .st-key-jms_table_wrap {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.15);
        border-radius: 10px;
        overflow: auto !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .st-key-jms_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1250px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(0,0,0,0.12) !important;
        padding: 8px 0 !important;
        flex-wrap: nowrap !important;
        background: #ffffff !important;
    }
    .st-key-jms_table_wrap div[data-testid="stHorizontalBlock"]:has(.tbl-head) {
        background: #eef2ff !important;
        border-bottom: 2px solid rgba(79,70,229,0.35) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 2 !important;
    }
    .st-key-jms_table_wrap div[data-testid="stHorizontalBlock"]:not(:has(.tbl-head)):hover {
        background: #f8fafc !important;
    }
    .st-key-jms_table_wrap div[data-testid="column"] {
        padding: 0 15px !important;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        border-right: 1px solid rgba(0,0,0,0.08);
    }
    .st-key-jms_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-jms_table_wrap .tbl-head {
        background: transparent; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px;
        color: #312e81; text-transform: uppercase; white-space: nowrap !important;
    }
    .st-key-jms_table_wrap .tbl-cell {
        color: #0f172a; font-size: 0.86rem; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    .st-key-jms_table_wrap .tbl-serial { color: #64748b; font-size: 0.85rem; font-weight: 800; }
    .st-key-jms_table_wrap button {
        height: 34px !important; padding: 0 10px !important; min-height: 0 !important;
        border-radius: 6px !important; box-shadow: none !important;
    }

    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem;
        font-weight: 800; letter-spacing: 0.4px; white-space: nowrap !important; text-align: center;
    }
    .status-green { background: rgba(34,197,94,0.15);  color: #15803d; }
    .status-grey  { background: rgba(148,163,184,0.18); color: #334155; }
    </style>
""", unsafe_allow_html=True)

# --- MULTI-COMPANY NAV BAR ---
with st.container(key="jms_company_nav_bar"):
    nav_cols = st.columns(len(SITE_COMPANIES))
    for nav_col, (company_id, company_label) in zip(nav_cols, SITE_COMPANIES):
        is_active = st.session_state.site_active_company == company_id
        with nav_col:
            if st.button(
                company_label, key=f"jms_nav_{company_id}",
                use_container_width=True, type=("primary" if is_active else "secondary")
            ):
                st.session_state.site_active_company = company_id
                st.session_state.active_workspace = SITE_COMPANY_WORKSPACE_MAP[company_id]
                st.session_state.jmspage_current_page = 1
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION ---
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

# --- CACHED FETCHERS ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_site_data_cached(workspace):
    try:
        response = supabase.table("site_data").select("*").eq("workspace", workspace).execute()
        return response.data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_jms_drafts_cached(workspace):
    """Returns {site_data_id: draft_row} for every JMS already saved in this workspace."""
    result = {}
    try:
        res = supabase.table("jms_drafts").select("*").eq("workspace", workspace).execute()
        for row in (res.data or []):
            sid = str(row.get("site_data_id", ""))
            if sid:
                result[sid] = row
    except Exception:
        pass
    return result


def clear_jms_cache():
    fetch_site_data_cached.clear()
    fetch_jms_drafts_cached.clear()


# --- 3.1 DROPDOWN / ITEM MASTER HELPERS (needed by "Add New Item" inside JMS form) ---
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts


def get_item_master_details():
    mapping = {}
    table_names_to_try = ["Item Code", "item_code"]
    for t_name in table_names_to_try:
        try:
            res = supabase.table(t_name).select("*").execute()
            if res.data:
                for item in res.data:
                    code = str(item.get("item_code", "")).strip()
                    if code:
                        mapping[code] = {
                            "description": str(item.get("item_description", "") or ""),
                            "stn_status": str(item.get("stn_status", "Required") or "Required"),
                            "material_of": str(item.get("material_of", "Indus") or "Indus"),
                            "rate": item.get("rate")
                        }
                return mapping
        except Exception:
            continue
    return mapping


# =============================================================
# JMS BUILDER (identical logic to the Site Data page's JMS module)
# =============================================================
JMS_COMPANY_NAMES = {
    "VISPL": "Visiontech Infra Solutions",
    "BHAGYASHREE": "Bhagyashree Enterprises",
    "SAI TELE SERVICES": "Sai Tele Services",
}

def _clean_text(value):
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.lower() in ("nan", "none", "null") else value

def _first_value(row, names, default=""):
    for name in names:
        value = _clean_text(row.get(name))
        if value:
            return value
    return default

def _normalized_po_value(row, aliases, default=""):
    normalized = {
        "".join(ch for ch in str(key).lower() if ch.isalnum()): value
        for key, value in row.items()
    }
    for alias in aliases:
        value = _clean_text(normalized.get("".join(ch for ch in alias.lower() if ch.isalnum())))
        if value:
            return value
    return default

def _detect_po_item_code(row):
    value = _normalized_po_value(row, [
        "Item Num", "Item Code", "ItemCode", "Item Number", "ItemNumber", "Item No",
        "ItemNo", "Oracle Item Code", "Material Code", "MaterialCode", "Item"
    ])
    if value:
        return value
    for key, raw in row.items():
        nk = "".join(ch for ch in str(key).lower() if ch.isalnum())
        if (("item" in nk and ("code" in nk or "number" in nk or nk.endswith("no")))
                or ("material" in nk and "code" in nk)):
            value = _clean_text(raw)
            if value:
                return value
    return ""

def _detect_po_qty(row):
    value = _normalized_po_value(row, [
        "PO Qty", "PO Quantity", "PO Ordered Qty", "Ordered Qty", "Order Qty",
        "Item Qty", "Quantity", "Qty", "VIS Qty", "User Qty"
    ], "")
    if value != "":
        return _number_value(value)
    for key, raw in row.items():
        nk = "".join(ch for ch in str(key).lower() if ch.isalnum())
        if (("po" in nk and ("qty" in nk or "quantity" in nk))
                or nk in ("orderedquantity", "orderedqty", "itemquantity", "itemqty")):
            value = _clean_text(raw)
            if value != "":
                return _number_value(value)
    return 0.0

@st.cache_data(ttl=300, show_spinner=False)
def _jms_item_description_code_map():
    return {
        " ".join(_clean_text(details.get("description")).lower().split()): code
        for code, details in get_item_master_details().items()
        if _clean_text(details.get("description"))
    }

def _code_from_item_master(description):
    wanted = " ".join(_clean_text(description).lower().split())
    if not wanted:
        return ""
    return _jms_item_description_code_map().get(wanted, "")

def _number_value(value):
    try:
        number = float(value)
        return 0.0 if math.isnan(number) else number
    except (TypeError, ValueError):
        return 0.0

def _split_list_field(raw):
    items = []
    normalized = str(raw if raw is not None else "").replace("|", ",")
    for x in normalized.split(","):
        x = x.strip()
        if x and x.lower() not in ("nan", "none", "null"):
            items.append(x)
    return items

def _jms_row_key(row_data):
    return f"{st.session_state.get('active_workspace', 'VISPL')}::{row_data.get('id')}"

def _fetch_po_lines_for_site(row_data):
    workspace = st.session_state.get("active_workspace", "VISPL")
    project_id = _clean_text(row_data.get("Project ID"))
    site_id = _clean_text(row_data.get("Site ID"))
    po_numbers = set(_split_list_field(row_data.get("PO No.", "")))
    candidates = []

    for field_name, field_value in (("Project Name", project_id), ("Site ID", site_id)):
        if not field_value:
            continue
        try:
            result = (supabase.table("po_working").select("*")
                      .eq("workspace", workspace).eq(field_name, field_value).execute())
            candidates.extend(result.data or [])
        except Exception:
            pass

    unique_rows, seen = [], set()
    for po_row in candidates:
        identity = po_row.get("id")
        if identity is None:
            identity = repr(sorted(po_row.items()))
        identity = str(identity)
        if identity not in seen:
            seen.add(identity)
            unique_rows.append(po_row)

    unique_rows.sort(key=lambda r: (
        _number_value(_normalized_po_value(r, ["Line Number", "Line Num", "Line No"], 999999)),
        _clean_text(r.get("id"))
    ))

    if po_numbers:
        matched = [r for r in unique_rows if _first_value(r, ["PO Number", "PO No.", "PO No", "po_number"]) in po_numbers]
        if matched:
            unique_rows = matched

    lines = []
    for po_row in unique_rows:
        item_code = _detect_po_item_code(po_row)
        description = _normalized_po_value(po_row, [
            "Item Description", "ItemDescription", "Description", "PO Item Description"
        ])
        qty = _detect_po_qty(po_row)
        if not item_code and description:
            item_code = _code_from_item_master(description)
        if item_code or description:
            lines.append({
                "item_code": item_code,
                "item_description": description,
                "qty": qty,
                "qty_manual": False,
                "remarks": "",
            })
    return lines

def _merge_saved_lines_with_po(saved_lines, po_lines):
    if not saved_lines:
        return po_lines
    po_by_desc = {_clean_text(x.get("item_description")).lower(): x for x in po_lines}
    po_by_code = {_clean_text(x.get("item_code")).lower(): x for x in po_lines if _clean_text(x.get("item_code"))}
    merged = []
    used_codes = set()
    for saved in saved_lines:
        row = dict(saved)
        code = _clean_text(row.get("item_code"))
        desc = _clean_text(row.get("item_description"))
        source = po_by_code.get(code.lower()) if code else None
        if source is None and desc:
            source = po_by_desc.get(desc.lower())
        if source:
            if not code:
                row["item_code"] = source.get("item_code", "")
            if not desc:
                row["item_description"] = source.get("item_description", "")
            if (not row.get("qty_manual") and _number_value(row.get("qty")) == 0
                    and _number_value(source.get("qty")) != 0):
                row["qty"] = source.get("qty", 0)
            used_codes.add(_clean_text(source.get("item_code")).lower())
        if not _clean_text(row.get("item_code")) and _clean_text(row.get("item_description")):
            row["item_code"] = _code_from_item_master(row.get("item_description"))
        merged.append(row)
    for po_line in po_lines:
        po_code = _clean_text(po_line.get("item_code")).lower()
        po_desc = _clean_text(po_line.get("item_description")).lower()
        already_present = po_code in used_codes if po_code else any(
            _clean_text(x.get("item_description")).lower() == po_desc for x in merged
        )
        if not already_present:
            merged.append(po_line)
    return merged

def _load_saved_jms(row_data):
    workspace = st.session_state.get("active_workspace", "VISPL")
    try:
        result = (supabase.table("jms_drafts").select("*")
                  .eq("workspace", workspace).eq("site_data_id", str(row_data.get("id")))
                  .limit(1).execute())
        return (result.data or [None])[0]
    except Exception:
        return None

def _save_jms_draft(row_data, circle, lines):
    workspace = st.session_state.get("active_workspace", "VISPL")
    payload = {
        "workspace": workspace,
        "site_data_id": str(row_data.get("id")),
        "project_id": _clean_text(row_data.get("Project ID")),
        "site_id": _clean_text(row_data.get("Site ID")),
        "site_name": _clean_text(row_data.get("Site Name")),
        "company_name": JMS_COMPANY_NAMES.get(workspace, workspace),
        "circle": circle,
        "line_items": lines,
        "updated_at": datetime.utcnow().isoformat(),
    }
    return supabase.table("jms_drafts").upsert(
        payload, on_conflict="workspace,site_data_id"
    ).execute()

def _build_jms_pdf(row_data, circle, lines):
    buffer = io.BytesIO()
    workspace = st.session_state.get("active_workspace", "VISPL")
    company = JMS_COMPANY_NAMES.get(workspace, workspace)
    page_w, page_h = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"JMS {_clean_text(row_data.get('Site ID'))}")

    def first_60_words(value):
        return " ".join(_clean_text(value).split()[:60])

    def fit_lines(text, max_width, font="Helvetica", size=4.2, max_lines=4):
        words = str(text).split()
        output, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            if stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                if current:
                    output.append(current)
                current = word
                if len(output) >= max_lines:
                    break
        if current and len(output) < max_lines:
            output.append(current)
        if len(output) == max_lines and len(" ".join(output).split()) < len(words):
            output[-1] = output[-1].rstrip(".") + "..."
        return output

    def draw_cell_text(text, x, y_top, width, height, size=4.2, bold=False, center=False, max_lines=4):
        font = "Helvetica-Bold" if bold else "Helvetica"
        rows = fit_lines(text, width - 4, font, size, max_lines)
        leading = size + 0.9
        total = len(rows) * leading
        y = y_top - (height - total) / 2 - size
        pdf.setFont(font, size)
        for line in rows:
            tx = x + width / 2 if center else x + 2
            if center:
                pdf.drawCentredString(tx, y, line)
            else:
                pdf.drawString(tx, y, line)
            y -= leading

    source_lines = list(lines)
    chunks = [source_lines[i:i + 30] for i in range(0, len(source_lines), 30)] or [[]]
    for page_no, chunk in enumerate(chunks, 1):
        margin = 10 * mm
        pdf.setLineWidth(0.8)
        pdf.rect(margin, margin, page_w - 2*margin, page_h - 2*margin)

        pdf.setFillColor(colors.HexColor("#3730a3"))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(page_w/2, page_h - 20*mm, company.upper())
        pdf.setFillColor(colors.HexColor("#334155"))
        pdf.setFont("Helvetica", 8.5)
        pdf.drawCentredString(page_w/2, page_h - 27*mm, "Joint Measurement Sheet")
        pdf.line(margin, page_h - 32*mm, page_w-margin, page_h - 32*mm)

        ix, iy, iw, ih = 16*mm, page_h - 52*mm, page_w - 32*mm, 14*mm
        pdf.setStrokeColor(colors.black); pdf.setLineWidth(0.55)
        pdf.rect(ix, iy, iw, ih); pdf.line(ix + iw/2, iy, ix + iw/2, iy + ih); pdf.line(ix, iy + ih/2, ix + iw, iy + ih/2)
        info = [
            ("Circle :-", circle or "Maharashtra", ix, iy + ih, iw/2, ih/2),
            ("Site ID :-", _clean_text(row_data.get("Site ID")), ix+iw/2, iy+ih, iw/2, ih/2),
            ("Site Name :-", _clean_text(row_data.get("Site Name")), ix, iy+ih/2, iw/2, ih/2),
            ("Project ID :-", _clean_text(row_data.get("Project ID")), ix+iw/2, iy+ih/2, iw/2, ih/2),
        ]
        for label, value, x, top, width, height in info:
            pdf.setFont("Helvetica-Bold", 6.2); pdf.drawString(x+3, top-height/2-2, label)
            pdf.setFont("Helvetica", 6.2); pdf.drawString(x+25*mm, top-height/2-2, value[:55])

        tx, table_top = 16*mm, iy - 4*mm
        widths = [10*mm, 33*mm, 91*mm, 18*mm, 26*mm]
        header_h, row_h = 8*mm, 6.35*mm
        headers = ["S.No.", "Item Code", "Item Description", "Qty as per site", "Remarks"]
        x = tx
        pdf.setFillColor(colors.HexColor("#e5e7eb")); pdf.rect(tx, table_top-header_h, sum(widths), header_h, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        for label, width in zip(headers, widths):
            pdf.rect(x, table_top-header_h, width, header_h, fill=0, stroke=1)
            draw_cell_text(label, x, table_top, width, header_h, size=5.4, bold=True, center=(label in ("S.No.", "Qty as per site")), max_lines=2)
            x += width

        for row_pos in range(30):
            y_top = table_top - header_h - row_pos*row_h
            line = chunk[row_pos] if row_pos < len(chunk) else {}
            global_no = (page_no - 1)*30 + row_pos + 1 if row_pos < len(chunk) else ""
            qty = _number_value(line.get("qty")) if line else 0
            qty_text = (str(int(qty)) if float(qty).is_integer() else f"{qty:g}") if line and qty != 0 else ""
            values = [global_no, _clean_text(line.get("item_code")), first_60_words(line.get("item_description")), qty_text, _clean_text(line.get("remarks"))]
            x = tx
            for col_no, (value, width) in enumerate(zip(values, widths)):
                pdf.rect(x, y_top-row_h, width, row_h, fill=0, stroke=1)
                draw_cell_text(value, x, y_top, width, row_h,
                               size=5.65 if col_no in (1,2) else 5.25,
                               bold=col_no in (1,2), center=col_no in (0,3), max_lines=2)
                x += width

        sig_y, sig_h, gap = 12*mm, 27*mm, 6*mm
        sig_w = (iw-gap)/2
        pdf.rect(ix, sig_y, sig_w, sig_h); pdf.rect(ix+sig_w+gap, sig_y, sig_w, sig_h)
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawString(ix+5*mm, sig_y+12*mm, "TSP Partner Name :")
        pdf.setFont("Helvetica", 6.0); pdf.drawString(ix+5*mm, sig_y+6*mm, company.upper())
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawString(ix+sig_w+gap+5*mm, sig_y+12*mm, "Auditor Name :-")
        pdf.drawString(ix+sig_w+gap+5*mm, sig_y+6*mm, "Audit Agency :-")
        pdf.showPage()

    pdf.save()
    return buffer.getvalue()

@st.cache_data(ttl=600, show_spinner=False)
def _cached_jms_pdf_bytes(workspace, site_data_id, updated_at, row_json, circle, lines_json):
    """Builds the JMS PDF straight from a saved draft, without opening the dialog.
    Cached on (workspace, site_data_id, updated_at) so it's instant after the first
    build and only regenerates when the draft is actually saved/changed again."""
    row_data = json.loads(row_json)
    lines = json.loads(lines_json)
    return _build_jms_pdf(row_data, circle, lines)


@st.dialog("🧾 Create / Edit JMS", width="large")
def jms_dialog(row_data):
    active_key = _jms_row_key(row_data)
    is_blank_jms = bool(row_data.get("_blank_jms"))
    if st.session_state.jmspage_loaded_key != active_key:
        saved = None if is_blank_jms else _load_saved_jms(row_data)
        saved_lines = saved.get("line_items") if saved else None
        po_lines = [] if is_blank_jms else _fetch_po_lines_for_site(row_data)
        st.session_state.jmspage_lines = _merge_saved_lines_with_po(saved_lines, po_lines) if isinstance(saved_lines, list) else po_lines
        st.session_state.jmspage_loaded_key = active_key
        st.session_state.jmspage_last_pdf = None
        st.session_state.jmspage_add_gen += 1
        st.session_state[f"jmspage_circle_{active_key}"] = (
            _clean_text(saved.get("circle")) if saved else ("" if is_blank_jms else "Maharashtra")
        )

    workspace = st.session_state.get("active_workspace", "VISPL")
    company = JMS_COMPANY_NAMES.get(workspace, workspace)
    st.markdown(f"### {company}")
    if is_blank_jms:
        st.caption("Blank JMS — site details blank rahenge. Item Code select karke Qty manually enter kijiye.")
    else:
        st.caption(f"Site: {_clean_text(row_data.get('Site ID'))} | Project: {_clean_text(row_data.get('Project ID'))} | PO: {_clean_text(row_data.get('PO No.')) or '-'}")
    circle = st.text_input("Circle", key=f"jmspage_circle_{active_key}")

    if not is_blank_jms:
        if st.button("🔄 Reload Item Code & Qty from PO", use_container_width=True, key=f"jmspage_reload_po_{active_key}"):
            fresh_po_lines = _fetch_po_lines_for_site(row_data)
            if fresh_po_lines:
                st.session_state.jmspage_lines = _merge_saved_lines_with_po(st.session_state.jmspage_lines, fresh_po_lines)
                st.session_state.jmspage_last_pdf = None
                st.success("PO se Item Code aur Qty reload ho gaye.")
                st.rerun()
            else:
                st.warning("Is Project ID / Site ID ke against po_working me koi line nahi mili.")

    st.markdown("#### Manual JMS Line Items" if is_blank_jms else "#### PO / Saved JMS Line Items")
    if st.session_state.jmspage_lines:
        editor_df = pd.DataFrame(st.session_state.jmspage_lines)
        for col, default in (("item_code", ""), ("item_description", ""), ("qty", 0.0), ("remarks", "")):
            if col not in editor_df.columns:
                editor_df[col] = default
        editor_df["qty"] = editor_df["qty"].apply(
            lambda value: "" if _number_value(value) == 0 else (
                str(int(_number_value(value))) if _number_value(value).is_integer()
                else f"{_number_value(value):g}"
            )
        )
        edited = st.data_editor(
            editor_df[["item_code", "item_description", "qty", "remarks"]],
            hide_index=True, use_container_width=True, num_rows="dynamic",
            column_config={
                "item_code": st.column_config.TextColumn("Item Code"),
                "item_description": st.column_config.TextColumn("Item Description", width="large"),
                "qty": st.column_config.TextColumn("Qty", help="Qty editable hai; 0 ya blank dono blank rahenge."),
                "remarks": st.column_config.TextColumn("Remarks", width="medium"),
            }, key=f"jmspage_editor_{active_key}")
        edited_records = edited.to_dict("records")
        for item in edited_records:
            raw_qty = _clean_text(item.get("qty"))
            if raw_qty:
                try:
                    parsed_qty = float(raw_qty.replace(",", ""))
                    item["qty"] = None if parsed_qty == 0 else parsed_qty
                except ValueError:
                    item["qty"] = None
            else:
                item["qty"] = None
            item["qty_manual"] = True
        st.session_state.jmspage_lines = edited_records
    else:
        if is_blank_jms:
            st.info("Neeche Item Code select karke Qty manually enter kijiye.")
        else:
            st.info("Is site ke PO me item lines nahi mili. Neeche se new item add kijiye.")

    st.markdown("#### Add New Item")
    master = get_item_master_details()
    gen = st.session_state.jmspage_add_gen
    add_code = st.selectbox(
        "Item Code", [""] + sorted(master.keys()),
        format_func=lambda code: "-- Select item --" if not code else f"{code} — {master[code]['description']}",
        key=f"jmspage_add_code_{active_key}_{gen}") if master else st.text_input("Item Code", key=f"jmspage_add_code_{active_key}_{gen}")
    add_desc = master.get(add_code, {}).get("description", "") if master else st.text_input("Item Description", key=f"jmspage_add_desc_{active_key}_{gen}")
    if master and add_code:
        st.caption(add_desc)
    add_qty_raw = st.text_input("Qty", value="", placeholder="Blank = 0", key=f"jmspage_add_qty_{active_key}_{gen}")
    if st.button("➕ Add New Item", use_container_width=True, key=f"jmspage_add_btn_{active_key}", disabled=not _clean_text(add_code)):
        add_qty = _number_value(add_qty_raw.replace(",", "")) if _clean_text(add_qty_raw) else None
        st.session_state.jmspage_lines.append({"item_code": add_code, "item_description": add_desc, "qty": None if add_qty == 0 else add_qty, "qty_manual": True, "remarks": ""})
        st.session_state.jmspage_add_gen += 1
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save JMS", type="primary", use_container_width=True, key=f"jmspage_save_{active_key}"):
            clean_lines = [x for x in st.session_state.jmspage_lines if _clean_text(x.get("item_code")) or _clean_text(x.get("item_description"))]
            if not clean_lines:
                st.error("Kam se kam ek item line required hai.")
            else:
                try:
                    _save_jms_draft(row_data, circle, clean_lines)
                    st.session_state.jmspage_lines = clean_lines
                    st.session_state.jmspage_last_pdf = _build_jms_pdf(row_data, circle, clean_lines)
                    clear_jms_cache()
                    st.success("JMS save ho gayi. Ab PDF download kar sakte hain.")
                except Exception as exc:
                    st.error(f"JMS save nahi hui: {exc}")
    with c2:
        if st.button("✖ Close", use_container_width=True, key=f"jmspage_close_{active_key}"):
            st.session_state.jmspage_open_row = None
            st.session_state.jmspage_loaded_key = None
            st.query_params.pop("jms_ctx", None)
            st.rerun()

    if st.session_state.get("jmspage_last_pdf"):
        safe_site = _clean_text(row_data.get("Site ID")) or "Site"
        st.download_button("⬇️ Download JMS PDF", st.session_state.jmspage_last_pdf,
                           file_name=f"JMS_{safe_site}.pdf", mime="application/pdf",
                           use_container_width=True, key=f"jmspage_download_{active_key}")


# --- TOP BANNER ---
active_ws_display = st.session_state.get('site_active_company', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #f59e0b 0%, #ef4444 50%, #d946ef 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.2rem; text-transform: uppercase;">
            🧾 JMS — {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

col_title, col_blank, col_ref = st.columns([4, 1.25, 1])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>Joint Measurement Sheets</h2>", unsafe_allow_html=True)
with col_blank:
    if st.button("➕ Blank JMS", type="primary", use_container_width=True):
        blank_id = f"blank-{uuid4().hex}"
        st.session_state.jmspage_open_row = {
            "id": blank_id,
            "_blank_jms": True,
            "Site Name": "",
            "Project ID": "",
            "Site ID": "",
            "Cluster": "",
            "PO No.": "",
        }
        st.session_state.jmspage_loaded_key = None
        st.session_state.jmspage_last_pdf = None
        st.query_params["jms_ctx"] = "open"
        st.rerun()
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        clear_jms_cache()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- FETCH DATA ---
active_ws = st.session_state.get('active_workspace', 'VISPL')
site_data_rows = fetch_site_data_cached(active_ws)
jms_drafts_map = fetch_jms_drafts_cached(active_ws)

columns_needed = ["id", "Site Name", "Project ID", "Site ID", "Cluster", "PO No."]
if site_data_rows:
    df = pd.DataFrame(site_data_rows)
    for col in columns_needed:
        if col not in df.columns:
            df[col] = ""
    if 'created_at' in df.columns:
        df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
        df = df.sort_values(by='created_at_dt', ascending=False).drop(columns=['created_at_dt']).reset_index(drop=True)
else:
    df = pd.DataFrame(columns=columns_needed)

# Keep the JMS dialog open across reruns while editing/saving
if st.session_state.get("jmspage_open_row") is not None:
    jms_dialog(st.session_state.jmspage_open_row)

# --- SEARCH ---
search_query = st_keyup("Search", placeholder="🔍 Search by Site Name / Project ID / Site ID / Cluster / PO No...", label_visibility="collapsed")
if search_query:
    mask = df[columns_needed].astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

st.markdown("<br>", unsafe_allow_html=True)

# --- PAGINATION ---
rows_per_page = 15
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
if st.session_state.jmspage_current_page > total_pages:
    st.session_state.jmspage_current_page = total_pages
elif st.session_state.jmspage_current_page < 1:
    st.session_state.jmspage_current_page = 1

start_idx = (st.session_state.jmspage_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page
df_page = df.iloc[start_idx:end_idx].copy()

# --- TABLE ---
COL_RATIOS = [0.4, 1.4, 1.1, 1.1, 1.1, 1.2, 1.1, 1.1, 1.2]
COL_LABELS = ["#", "SITE NAME", "PROJECT ID", "SITE ID", "CLUSTER", "PO NO.", "JMS STATUS", "ACTION", "DOWNLOAD"]

if df_page.empty:
    st.info("No records found.")
else:
    with st.container(key="jms_table_wrap", height=560):
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1
            has_jms = str(rid) in jms_drafts_map

            rcols = st.columns(COL_RATIOS)
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            rcols[1].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[2].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('PO No.','') or '-'}</div>", unsafe_allow_html=True)

            if has_jms:
                rcols[6].markdown("<span class='status-badge status-green'>✅ Created</span>", unsafe_allow_html=True)
            else:
                rcols[6].markdown("<span class='status-badge status-grey'>⭕ Not Created</span>", unsafe_allow_html=True)

            with rcols[7]:
                btn_label = "✏️ Edit JMS" if has_jms else "🧾 Create JMS"
                if st.button(btn_label, key=f"jmsrowbtn_{rid}", use_container_width=True):
                    st.session_state.jmspage_open_row = row_dict
                    st.query_params["jms_ctx"] = "open"
                    st.rerun()

            with rcols[8]:
                if has_jms:
                    draft = jms_drafts_map[str(rid)]
                    draft_circle = _clean_text(draft.get("circle")) or "Maharashtra"
                    draft_lines = draft.get("line_items") or []
                    updated_at = _clean_text(draft.get("updated_at"))
                    try:
                        pdf_bytes = _cached_jms_pdf_bytes(
                            active_ws, str(rid), updated_at,
                            json.dumps(row_dict, default=str), draft_circle,
                            json.dumps(draft_lines, default=str),
                        )
                        safe_site = _clean_text(row_dict.get("Site ID")) or "Site"
                        st.download_button(
                            "⬇️ PDF", data=pdf_bytes, file_name=f"JMS_{safe_site}.pdf",
                            mime="application/pdf", key=f"jmsrowdl_{rid}", use_container_width=True,
                        )
                    except Exception:
                        st.caption("PDF error")
                else:
                    st.markdown("<div class='tbl-cell' style='color:#94a3b8;'>-</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.jmspage_current_page == 1)):
        st.session_state.jmspage_current_page -= 1
        st.rerun()
with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.jmspage_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.jmspage_current_page == total_pages)):
        st.session_state.jmspage_current_page += 1
        st.rerun()
