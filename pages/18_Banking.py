import datetime
import hashlib
import html
import hmac
import io
import math
import re
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from supabase import Client, create_client


st.set_page_config(page_title="Banking", page_icon="🏦", layout="wide")

ALLOWED_WORKSPACE = "VISPL"
PAGE_SIZE = 20
PAGE_PASSWORD_HASH = "7559103d4a3e65bbdc120e9e0bf6ad3c542690213b4d74e29ddb4b51ea00a261"

ACCOUNTS = {
    "HDFC VISPL": {
        "key": "HDFC_VISPL",
        "pay_from": "VISPL HDFC",
    },
    "HDFC VIS": {
        "key": "HDFC_VIS",
        "pay_from": "Visiontech Partnership",
    },
    "Pramodkumar Jaju": {
        "key": "PRAMODKUMAR_JAJU",
        "pay_from": "Pramodkumar Jaju",
    },
    "Radhika Jaju": {
        "key": "RADHIKA_JAJU",
        "pay_from": "Radhika Jaju",
    },
}

MATERIAL_VENDORS = {
    "RUSHIKESH STEEL": {
        "key": "MATERIAL_RUSHIKESH_STEEL",
        "pay_from": "RUSHIKESH STEEL",
    },
    "RUSHIKESH STEEL CORPORATION": {
        "key": "MATERIAL_RUSHIKESH_STEEL_CORPORATION",
        "pay_from": "RUSHIKESH STEEL CORPORATION",
    },
    "Vighanharta Enterprises": {
        "key": "MATERIAL_VIGHANHARTA_ENTERPRISES",
        "pay_from": "Vighanharta Enterprises",
    },
    "S M ENTERPRISES": {
        "key": "MATERIAL_S_M_ENTERPRISES",
        "pay_from": "S M ENTERPRISES",
    },
    "S K AND SONS ENTERPRISES": {
        "key": "MATERIAL_S_K_AND_SONS_ENTERPRISES",
        "pay_from": "S K AND SONS ENTERPRISES",
    },
}

MAIN_ACCOUNT_TABS = list(ACCOUNTS.keys()) + ["Material", "INDUS"]


st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%); }

    /* Premium sidebar navigation — same as Site Data page */
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
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important; border: none; border-radius: 10px;
        font-weight: 800 !important; padding: 0.65rem 1rem;
        min-height: 48px; transition: all 0.25s ease;
        box-shadow: 0 5px 12px rgba(59, 130, 246, 0.25);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.32);
    }
    div.stButton > button:disabled {
        background: #cbd5e1 !important; color: #64748b !important;
        box-shadow: none !important; transform: none !important;
        cursor: not-allowed !important; opacity: 0.75 !important;
    }
    div.stButton > button:disabled p,
    div.stButton > button:disabled span,
    div.stButton > button:disabled div { color: #64748b !important; }
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div { color: #ffffff !important; font-weight: 800 !important; }
    div.stDownloadButton > button {
        background: linear-gradient(90deg, #059669 0%, #0d9488 100%) !important;
        color: #ffffff !important; border: none !important; border-radius: 10px !important;
        font-weight: 800 !important; min-height: 48px !important;
        box-shadow: 0 5px 12px rgba(5,150,105,0.24) !important;
        transition: all 0.25s ease !important;
    }
    div.stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(5,150,105,0.30) !important;
    }
    div.stDownloadButton > button p,
    div.stDownloadButton > button span,
    div.stDownloadButton > button div { color: #ffffff !important; font-weight: 800 !important; }

    .st-key-banking_account_nav div[data-testid="stHorizontalBlock"],
    .st-key-banking_view_nav div[data-testid="stHorizontalBlock"],
    .st-key-banking_material_vendor_nav div[data-testid="stHorizontalBlock"] {
        gap: 14px !important; flex-wrap: wrap !important;
    }
    .st-key-banking_account_nav button,
    .st-key-banking_view_nav button,
    .st-key-banking_material_vendor_nav button {
        font-size: 1.05rem !important; font-weight: 800 !important;
        min-height: 58px !important; padding: 14px 12px !important;
        border-radius: 13px !important; white-space: nowrap !important;
        transition: all 0.25s ease !important;
    }
    .st-key-banking_account_nav button[kind="secondary"],
    .st-key-banking_view_nav button[kind="secondary"],
    .st-key-banking_material_vendor_nav button[kind="secondary"] {
        background: #ffffff !important; color: #475569 !important;
        border: 1.5px solid rgba(15,23,42,0.12) !important;
        box-shadow: 0 3px 8px rgba(15,23,42,0.08) !important;
    }
    .st-key-banking_account_nav button[kind="secondary"] p,
    .st-key-banking_account_nav button[kind="secondary"] span,
    .st-key-banking_account_nav button[kind="secondary"] div,
    .st-key-banking_view_nav button[kind="secondary"] p,
    .st-key-banking_view_nav button[kind="secondary"] span,
    .st-key-banking_view_nav button[kind="secondary"] div,
    .st-key-banking_material_vendor_nav button[kind="secondary"] p,
    .st-key-banking_material_vendor_nav button[kind="secondary"] span,
    .st-key-banking_material_vendor_nav button[kind="secondary"] div {
        color: #475569 !important; font-weight: 800 !important;
    }
    .st-key-banking_account_nav button[kind="secondary"]:hover,
    .st-key-banking_view_nav button[kind="secondary"]:hover,
    .st-key-banking_material_vendor_nav button[kind="secondary"]:hover {
        background: #f8fafc !important; transform: translateY(-2px) !important;
        border-color: rgba(79,70,229,0.35) !important;
    }
    .st-key-banking_account_nav button[kind="primary"],
    .st-key-banking_view_nav button[kind="primary"],
    .st-key-banking_material_vendor_nav button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: #ffffff !important; border: none !important;
        box-shadow: 0 7px 18px rgba(79,70,229,0.38) !important;
    }
    .bank-title {
        color: white; padding: 28px 24px; border-radius: 14px;
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 52%, #ec4899 100%);
        box-shadow: 0 9px 24px rgba(79,70,229,.30); margin: 14px 0 22px;
        text-align: center;
    }
    .bank-title h1 { color: white !important; margin: 0; font-size: 2.35rem; letter-spacing: 1px; }
    .bank-title p { color: #e0e7ff !important; margin: 5px 0 0; font-weight: 600; }
    .table-head {
        background: #312e81; color: white; border-radius: 9px;
        padding: 10px 8px; font-weight: 800; margin-top: 8px;
    }
    .txn-row {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 9px 8px; margin: 6px 0; box-shadow: 0 2px 7px rgba(15,23,42,.05);
    }
    .narration { white-space: normal; overflow-wrap: anywhere; line-height: 1.35; }
    .amount { color: #dc2626; font-weight: 900; font-size: 1.02rem; }
    .approved { color: #047857; font-weight: 800; }
    .preview-wrap {
        max-height: 480px; overflow: auto; background: white;
        border: 1px solid #dbe3ef; border-radius: 12px;
    }
    .preview-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .preview-table th {
        position: sticky; top: 0; z-index: 1; background: #312e81; color: white;
        padding: 11px 9px; text-align: left; font-weight: 800;
    }
    .preview-table td {
        padding: 9px; border-bottom: 1px solid #e5e7eb; vertical-align: top;
        color: #1f2937;
    }
    .preview-table .p-date { width: 125px; white-space: nowrap; }
    .preview-table .p-narration { width: auto; white-space: normal; overflow-wrap: anywhere; }
    .preview-table .p-ref { width: 205px; overflow-wrap: anywhere; }
    .preview-table .p-amount { width: 125px; white-space: nowrap; text-align: right; font-weight: 800; }
    .bulk-panel-title {
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 55%, #db2777 100%);
        color: #ffffff; border-radius: 13px; padding: 16px 20px;
        font-size: 1.15rem; font-weight: 900; letter-spacing: 0.3px;
        box-shadow: 0 7px 18px rgba(79,70,229,0.28); margin-bottom: 14px;
    }
    .st-key-bulk_move_panel [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.94) !important;
        border: 1px solid rgba(99,102,241,0.20) !important;
        border-radius: 16px !important; padding: 8px !important;
        box-shadow: 0 8px 24px rgba(15,23,42,0.09) !important;
    }
    .st-key-bulk_move_panel input {
        min-height: 52px !important; border-radius: 11px !important;
        font-size: 1rem !important; font-weight: 650 !important;
    }
    div[data-baseweb="select"] * { font-weight: 700 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Always keep a visible way back, including on password/error screens.
if st.button("← Back to Home", key="banking_back_home", use_container_width=False):
    st.switch_page("app.py")


active_workspace = st.session_state.get("active_workspace", "VISPL")
if active_workspace != ALLOWED_WORKSPACE:
    st.error("Access Restricted")
    st.warning("Banking module केवल VISPL login के लिए उपलब्ध है।")
    st.stop()


# Separate password protection for this financial page.
if not st.session_state.get("banking_page_unlocked", False):
    st.markdown(
        """
        <div class="bank-title">
            <h1>Banking Access</h1>
            <p>इस financial page को खोलने के लिए personal password डालें।</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("banking_password_form", clear_on_submit=True):
        entered_password = st.text_input("Personal Password", type="password")
        unlock_clicked = st.form_submit_button(
            "Unlock Banking",
            type="primary",
            use_container_width=True,
        )

    if unlock_clicked:
        entered_hash = hashlib.sha256(entered_password.encode("utf-8")).hexdigest()
        if hmac.compare_digest(entered_hash, PAGE_PASSWORD_HASH):
            st.session_state["banking_page_unlocked"] = True
            st.rerun()
        else:
            st.error("Incorrect Banking password.")
    st.stop()

with st.sidebar:
    if st.button("Lock Banking", use_container_width=True):
        st.session_state["banking_page_unlocked"] = False
        st.rerun()


@st.cache_resource
def init_connection() -> Client:
    supabase_section = st.secrets.get("supabase", {})

    raw_url = (
        supabase_section.get("url")
        or supabase_section.get("SUPABASE_URL")
        or st.secrets.get("SUPABASE_URL")
        or st.secrets.get("supabase_url")
    )
    raw_key = (
        supabase_section.get("key")
        or supabase_section.get("SUPABASE_KEY")
        or st.secrets.get("SUPABASE_KEY")
        or st.secrets.get("supabase_key")
    )

    if not raw_url or not raw_key:
        raise ValueError("Supabase URL/Key is missing in Streamlit Secrets")

    url = str(raw_url).strip().strip('"').strip("'").strip()
    key = str(raw_key).strip().strip('"').strip("'").strip()

    # create_client needs the project base URL, not the REST endpoint URL.
    if "/rest/v1" in url:
        url = url.split("/rest/v1", 1)[0]
    url = url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid Supabase project URL in Streamlit Secrets")

    return create_client(url, key)


try:
    supabase: Client = init_connection()
except Exception as exc:
    st.error(f"Supabase connection error: {exc}")
    st.stop()


def current_user() -> str:
    return str(st.session_state.get("username", "VISPL"))


@st.cache_data(ttl=60, show_spinner=False)
def load_people(category: str):
    response = (
        supabase.table("dropdown_master")
        .select("option_value")
        .eq("category", category)
        .eq("is_active", True)
        .order("option_value")
        .execute()
    )
    return [
        str(row.get("option_value", "")).strip()
        for row in (response.data or [])
        if str(row.get("option_value", "")).strip()
    ]


@st.cache_data(ttl=60, show_spinner=False)
def load_expense_categories():
    response = (
        supabase.table("bank_expense_categories")
        .select("category_name")
        .eq("is_active", True)
        .order("category_name")
        .execute()
    )
    return [
        str(row.get("category_name", "")).strip()
        for row in (response.data or [])
        if str(row.get("category_name", "")).strip()
    ]


def add_expense_category(category_name: str):
    clean_name = " ".join(str(category_name or "").strip().split())
    if not clean_name:
        raise ValueError("Expense category name required")
    existing = (
        supabase.table("bank_expense_categories")
        .select("id,is_active")
        .ilike("category_name", clean_name)
        .limit(1)
        .execute()
    )
    if existing.data:
        if not existing.data[0].get("is_active", True):
            supabase.table("bank_expense_categories").update(
                {"is_active": True}
            ).eq("id", existing.data[0]["id"]).execute()
            load_expense_categories.clear()
            return
        raise ValueError("यह expense category पहले से मौजूद है")
    supabase.table("bank_expense_categories").insert(
        {
            "category_name": clean_name,
            "created_by": current_user(),
            "is_active": True,
        }
    ).execute()
    load_expense_categories.clear()


def assignment_options():
    teams = load_people("Team Name")
    vendors = load_people("Vendor Name")
    return ["— Select Team/Vendor —", "Suspense", "Other Expense"] + [f"Team — {name}" for name in teams] + [f"Vendor — {name}" for name in vendors]


def parse_assignment(value: str):
    if value == "Suspense":
        return "Suspense", "Suspense"
    if value == "Other Expense":
        return "Other Expense", "Other Expense"
    if " — " not in value:
        raise ValueError("Please select a Team or Vendor")
    mode, name = value.split(" — ", 1)
    if mode not in {"Team", "Vendor"} or not name.strip():
        raise ValueError("Invalid Team/Vendor selection")
    return mode, name.strip()


def clean_header(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def to_text(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def to_amount(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(value).replace(",", ""))
    if cleaned in {"", "-", ".", "-."}:
        return None
    try:
        amount = round(float(cleaned), 2)
        return amount if amount > 0 else None
    except ValueError:
        return None


def to_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def infer_pay_type(narration: str) -> str:
    text = narration.upper()
    if "PHONEPE" in text or "PHONE PE" in text or "PAYMENT FROM PHONE" in text:
        return "Phone pe"
    if "UPI" in text or "GPAY" in text or "GOOGLE PAY" in text:
        return "GPay"
    return "NEFT"


def workbook_sheet_names(file_bytes: bytes):
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


def parse_statement(file_bytes: bytes, sheet_name: str, account_label: str, file_name: str):
    raw = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=sheet_name,
        header=None,
        dtype=object,
    )

    required = {
        "date": "date",
        "narration": "narration",
        "chqrefno": "reference",
        "withdrawalamt": "withdrawal",
    }
    header_row = None
    column_map = {}

    for row_index in range(len(raw)):
        found = {}
        for column_index, value in enumerate(raw.iloc[row_index].tolist()):
            normalized = clean_header(value)
            if normalized in required:
                found[required[normalized]] = column_index
        if all(name in found for name in required.values()):
            header_row = row_index
            column_map = found
            break

    if header_row is None:
        raise ValueError(
            "Date, Narration, Chq./Ref.No. और Withdrawal Amt. वाली header row नहीं मिली।"
        )

    account = ACCOUNTS[account_label]
    records = []
    seen_hashes = set()
    for row_index in range(header_row + 1, len(raw)):
        row = raw.iloc[row_index]
        txn_date = to_date(row.iloc[column_map["date"]])
        amount = to_amount(row.iloc[column_map["withdrawal"]])
        narration = to_text(row.iloc[column_map["narration"]])
        reference = to_text(row.iloc[column_map["reference"]])

        if not txn_date or amount is None or not narration:
            continue

        fingerprint_source = "|".join(
            [
                account["key"],
                txn_date.isoformat(),
                narration.strip().upper(),
                reference.strip().upper(),
                f"{amount:.2f}",
            ]
        )
        transaction_hash = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

        # Same file me exact same transaction repeat ho to ek hi baar lo.
        if transaction_hash in seen_hashes:
            continue
        seen_hashes.add(transaction_hash)

        records.append(
            {
                "workspace": ALLOWED_WORKSPACE,
                "account_key": account["key"],
                "pay_from": account["pay_from"],
                "transaction_date": txn_date.isoformat(),
                "narration": narration,
                "reference_no": reference,
                "withdrawal_amount": amount,
                "pay_type": infer_pay_type(narration),
                "transaction_hash": transaction_hash,
                "source_file_name": file_name,
                "source_sheet_name": sheet_name,
                "status": "Pending",
                "imported_by": current_user(),
            }
        )

    if not records:
        raise ValueError("Selected sheet में कोई Withdrawal transaction नहीं मिला।")
    return records


def parse_material_statement(file_bytes: bytes, sheet_name: str, vendor_name: str, file_name: str):
    raw = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=sheet_name,
        header=None,
        dtype=object,
    )

    header_aliases = {
        "invoicedate": "date",
        "date": "date",
        "billdate": "date",
        "invoiceno": "invoice_no",
        "invoicenumber": "invoice_no",
        "billno": "invoice_no",
        "billnumber": "invoice_no",
        "referenceno": "invoice_no",
        "invoiceamount": "amount",
        "billamount": "amount",
        "amount": "amount",
    }
    header_row = None
    column_map = {}
    for row_index in range(len(raw)):
        found = {}
        for column_index, value in enumerate(raw.iloc[row_index].tolist()):
            mapped_name = header_aliases.get(clean_header(value))
            if mapped_name and mapped_name not in found:
                found[mapped_name] = column_index
        if all(name in found for name in ("date", "invoice_no", "amount")):
            header_row = row_index
            column_map = found
            break

    if header_row is None:
        raise ValueError("Invoice Date, Invoice No. और Invoice Amount वाली header row नहीं मिली।")

    vendor = MATERIAL_VENDORS[vendor_name]
    records = []
    seen_hashes = set()
    for row_index in range(header_row + 1, len(raw)):
        row = raw.iloc[row_index]
        invoice_date = to_date(row.iloc[column_map["date"]])
        invoice_no = to_text(row.iloc[column_map["invoice_no"]])
        invoice_amount = to_amount(row.iloc[column_map["amount"]])
        if not invoice_date or not invoice_no or invoice_amount is None:
            continue

        fingerprint_source = "|".join(
            [
                vendor["key"],
                invoice_date.isoformat(),
                invoice_no.strip().upper(),
                f"{invoice_amount:.2f}",
            ]
        )
        transaction_hash = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
        if transaction_hash in seen_hashes:
            continue
        seen_hashes.add(transaction_hash)
        material_remark = (
            f"Material Payment - Ref No. {invoice_no.strip()} "
            f"Dt. {invoice_date.strftime('%d-%b-%Y')}"
        )

        records.append(
            {
                "workspace": ALLOWED_WORKSPACE,
                "account_key": vendor["key"],
                "pay_from": vendor["pay_from"],
                "transaction_date": invoice_date.isoformat(),
                "narration": material_remark,
                "reference_no": invoice_no,
                "withdrawal_amount": invoice_amount,
                "pay_type": "Material",
                "payment_remark": material_remark,
                "transaction_hash": transaction_hash,
                "source_file_name": file_name,
                "source_sheet_name": sheet_name,
                "status": "Pending",
                "imported_by": current_user(),
            }
        )

    if not records:
        raise ValueError("Selected sheet में कोई valid material invoice नहीं मिला।")
    return records


def build_manual_material_record(vendor_name: str, invoice_date, invoice_no, invoice_amount, allow_duplicate=False):
    vendor = MATERIAL_VENDORS[vendor_name]
    clean_invoice_no = to_text(invoice_no).strip()
    clean_amount = to_amount(invoice_amount)
    if not clean_invoice_no:
        raise ValueError("Invoice Number डालें।")
    if clean_amount is None or clean_amount <= 0:
        raise ValueError("Invoice Amount 0 से ज्यादा डालें।")

    parsed_date = to_date(invoice_date)
    if not parsed_date:
        raise ValueError("Valid Invoice Date डालें।")

    fingerprint_source = "|".join(
        [
            vendor["key"],
            parsed_date.isoformat(),
            clean_invoice_no.upper(),
            f"{clean_amount:.2f}",
        ]
    )
    if allow_duplicate:
        fingerprint_source += f"|MANUAL-PROCEED|{datetime.datetime.now().isoformat()}"

    material_remark = (
        f"Material Payment - Ref No. {clean_invoice_no} "
        f"Dt. {parsed_date.strftime('%d-%b-%Y')}"
    )

    return {
        "workspace": ALLOWED_WORKSPACE,
        "account_key": vendor["key"],
        "pay_from": vendor["pay_from"],
        "transaction_date": parsed_date.isoformat(),
        "narration": material_remark,
        "reference_no": clean_invoice_no,
        "withdrawal_amount": clean_amount,
        "pay_type": "Material",
        "payment_remark": material_remark,
        "transaction_hash": hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest(),
        "source_file_name": "Manual Entry",
        "source_sheet_name": "Manual",
        "status": "Pending",
        "imported_by": current_user(),
    }


def find_manual_material_duplicate(record: dict):
    response = (
        supabase.table("bank_transactions")
        .select("id,transaction_date,reference_no,withdrawal_amount,status,pay_from")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("account_key", record["account_key"])
        .eq("transaction_date", record["transaction_date"])
        .eq("reference_no", record["reference_no"])
        .eq("withdrawal_amount", record["withdrawal_amount"])
        .order("id", desc=True)
        .execute()
    )
    return response.data or []


def fetch_transactions(account_key: str, status: str):
    query = (
        supabase.table("bank_transactions")
        .select("*")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("account_key", account_key)
        .eq("status", status)
        .order("transaction_date", desc=True)
        .order("id", desc=True)
    )
    return query.execute().data or []



def get_bank_last_data_date(account_key: str):
    """Latest transaction date already saved for this bank account."""
    try:
        response = (
            supabase.table("bank_transactions")
            .select("transaction_date")
            .eq("workspace", ALLOWED_WORKSPACE)
            .eq("account_key", account_key)
            .order("transaction_date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return to_date(response.data[0].get("transaction_date"))
    except Exception:
        pass
    return None


def render_last_data_date_card(last_date, source_name="STATEMENT"):
    """Large premium reminder card shown above upload area."""
    if last_date:
        date_big = last_date.strftime("%d %b %Y").upper()
        next_date = last_date + datetime.timedelta(days=1)
        next_text = next_date.strftime("%d %b %Y").upper()
        st.markdown(
            f"""
            <div style="
                margin:8px 0 20px 0;
                padding:18px 24px;
                border-radius:18px;
                background:linear-gradient(100deg,#0f172a 0%,#312e81 45%,#6d28d9 100%);
                border:1px solid rgba(255,255,255,.16);
                box-shadow:0 14px 32px rgba(49,46,129,.24);
                display:flex;justify-content:space-between;align-items:center;
                gap:18px;flex-wrap:wrap;">
                <div>
                    <div style="color:#c7d2fe;font-size:.72rem;font-weight:900;
                                letter-spacing:1.5px;text-transform:uppercase;">
                        📅 LAST {html.escape(source_name)} DATA DATE
                    </div>
                    <div style="color:#ffffff;font-size:2rem;font-weight:950;
                                letter-spacing:.5px;line-height:1.15;margin-top:5px;">
                        {date_big}
                    </div>
                </div>
                <div style="
                    background:rgba(255,255,255,.12);
                    border:1px solid rgba(255,255,255,.18);
                    padding:11px 16px;border-radius:12px;
                    color:#ffffff;font-weight:800;">
                    Next data download from
                    <span style="color:#fde68a;font-size:1.05rem;"> {next_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="
                margin:8px 0 20px 0;padding:17px 22px;border-radius:18px;
                background:linear-gradient(100deg,#0f172a,#312e81,#6d28d9);
                color:white;box-shadow:0 14px 32px rgba(49,46,129,.22);">
                <div style="font-size:.72rem;font-weight:900;letter-spacing:1.5px;color:#c7d2fe;">
                    📅 LAST {html.escape(source_name)} DATA DATE
                </div>
                <div style="font-size:1.35rem;font-weight:950;margin-top:5px;">
                    NO DATA UPLOADED YET
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def refresh_material_payment_details(transaction_ids):
    clean_ids = [int(value) for value in transaction_ids]
    if not clean_ids:
        return
    rows = (
        supabase.table("bank_transactions")
        .select("id,pay_type,transaction_date,reference_no")
        .in_("id", clean_ids)
        .execute()
    ).data or []
    for row in rows:
        if str(row.get("pay_type", "")).strip().lower() != "material":
            continue
        invoice_date = to_date(row.get("transaction_date"))
        invoice_no = to_text(row.get("reference_no")).strip()
        if not invoice_date or not invoice_no:
            continue
        material_remark = (
            f"Material Payment - Ref No. {invoice_no} "
            f"Dt. {invoice_date.strftime('%d-%b-%Y')}"
        )
        (
            supabase.table("bank_transactions")
            .update({
                "narration": material_remark,
                "payment_remark": material_remark,
            })
            .eq("id", int(row["id"]))
            .execute()
        )


def approve_transaction(transaction_id: int, assignment: str):
    mode, pay_to = parse_assignment(assignment)
    refresh_material_payment_details([transaction_id])
    return supabase.rpc(
        "approve_bank_transaction",
        {
            "p_transaction_id": int(transaction_id),
            "p_mode": mode,
            "p_pay_to": pay_to,
            "p_approved_by": current_user(),
        },
    ).execute()


def move_to_suspense(transaction_id: int, suspense_remark: str):
    return supabase.rpc(
        "mark_bank_transaction_suspense",
        {
            "p_transaction_id": int(transaction_id),
            "p_suspense_remark": str(suspense_remark).strip(),
            "p_updated_by": current_user(),
        },
    ).execute()


def mark_other_expense(transaction_id: int, expense_category: str):
    return supabase.rpc(
        "mark_bank_transaction_other_expense",
        {
            "p_transaction_id": int(transaction_id),
            "p_expense_category": expense_category,
            "p_updated_by": current_user(),
        },
    ).execute()


def restore_to_pending(transaction_id: int):
    return supabase.rpc(
        "restore_bank_transaction_pending",
        {
            "p_transaction_id": int(transaction_id),
            "p_updated_by": current_user(),
        },
    ).execute()


def revoke_approved_transaction(transaction_id: int):
    return supabase.rpc(
        "revoke_bank_transaction_approval",
        {
            "p_transaction_id": int(transaction_id),
            "p_revoked_by": current_user(),
        },
    ).execute()


def change_approved_transaction_assignment(transaction_id: int, assignment: str):
    mode, pay_to = parse_assignment(assignment)
    if mode not in {"Team", "Vendor"}:
        raise ValueError("Team या Vendor select करें")
    return supabase.rpc(
        "change_approved_bank_transaction_assignment",
        {
            "p_transaction_id": int(transaction_id),
            "p_mode": mode,
            "p_pay_to": pay_to,
            "p_updated_by": current_user(),
        },
    ).execute()


def bulk_move_transactions(transaction_ids, destination: str, suspense_remark=""):
    if destination == "Suspense":
        destination_type = "Suspense"
        expense_category = None
    elif destination.startswith("Other Expense — "):
        destination_type = "Other Expense"
        expense_category = destination.split(" — ", 1)[1].strip()
    else:
        raise ValueError("Valid destination select करें")

    return supabase.rpc(
        "bulk_move_bank_transactions",
        {
            "p_transaction_ids": [int(value) for value in transaction_ids],
            "p_destination": destination_type,
            "p_expense_category": expense_category,
            "p_suspense_remark": str(suspense_remark).strip(),
            "p_updated_by": current_user(),
        },
    ).execute()


def bulk_approve_transactions(transaction_ids, assignment: str, duplicate_action="proceed"):
    mode, pay_to = parse_assignment(assignment)
    if mode not in {"Team", "Vendor"}:
        raise ValueError("Team या Vendor select करें")
    refresh_material_payment_details(transaction_ids)
    return supabase.rpc(
        "bulk_approve_bank_transactions",
        {
            "p_transaction_ids": [int(value) for value in transaction_ids],
            "p_mode": mode,
            "p_pay_to": pay_to,
            "p_duplicate_action": duplicate_action,
            "p_approved_by": current_user(),
        },
    ).execute()


def find_possible_duplicates(row: dict, assignment: str):
    mode, pay_to = parse_assignment(assignment)
    if mode == "Suspense":
        return []
    response = (
        supabase.table("billing_payments")
        .select("id,date,amount,mode,pay_to,pay_from,pay_type,remark,workspace")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("date", str(row.get("transaction_date")))
        .eq("amount", row.get("withdrawal_amount"))
        .eq("mode", mode)
        .eq("pay_to", pay_to)
        .order("id", desc=True)
        .execute()
    )
    return response.data or []


def link_as_duplicate(transaction_id: int, existing_payment_id: int, assignment: str):
    mode, pay_to = parse_assignment(assignment)
    return supabase.rpc(
        "link_bank_transaction_duplicate",
        {
            "p_transaction_id": int(transaction_id),
            "p_existing_payment_id": int(existing_payment_id),
            "p_mode": mode,
            "p_pay_to": pay_to,
            "p_approved_by": current_user(),
        },
    ).execute()


def format_date(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%d-%b-%Y") if not pd.isna(parsed) else ""


def format_amount(value) -> str:
    try:
        formatted = f"{float(value):,.2f}".rstrip("0").rstrip(".")
        return f"₹{formatted}"
    except (TypeError, ValueError):
        return "₹0"


def filter_transaction_records(records, search_text):
    terms = [term.lower() for term in str(search_text).split() if term.strip()]
    if not terms:
        return records
    search_fields = (
        "transaction_date", "narration", "reference_no", "withdrawal_amount",
        "status", "assignment_mode", "pay_to", "expense_category", "suspense_remark",
        "pay_from", "pay_type",
    )
    filtered = []
    for row in records:
        searchable_text = " ".join(str(row.get(field, "")) for field in search_fields).lower()
        if all(term in searchable_text for term in terms):
            filtered.append(row)
    return filtered


def transaction_excel(records, sheet_name):
    export_rows = []
    for row in records:
        parsed_date = pd.to_datetime(row.get("transaction_date"), errors="coerce")
        export_rows.append(
            {
                "Date": None if pd.isna(parsed_date) else parsed_date.date(),
                "Narration": str(row.get("narration", "")),
                "Chq./Ref.No.": str(row.get("reference_no", "")),
                "Withdrawal Amount": float(row.get("withdrawal_amount") or 0),
                "Status": str(row.get("status", "")),
                "Type": str(row.get("assignment_mode", "")),
                "Team/Vendor": str(row.get("pay_to", "")),
                "Expense Category": str(row.get("expense_category", "")),
                "Suspense Remark": str(row.get("suspense_remark", "")),
                "Payment From": str(row.get("pay_from", "")),
                "Payment Type": str(row.get("pay_type", "")),
            }
        )

    export_df = pd.DataFrame(export_rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        worksheet = writer.sheets[sheet_name[:31]]
        from openpyxl.styles import Alignment, Font, PatternFill

        header_fill = PatternFill("solid", fgColor="4F46E5")
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for column_index, width in enumerate([15, 70, 25, 20, 18, 16, 28, 28, 42, 25, 18], start=1):
            worksheet.column_dimensions[worksheet.cell(1, column_index).column_letter].width = width
        for row_index in range(2, worksheet.max_row + 1):
            worksheet.cell(row_index, 1).number_format = "DD-MMM-YYYY"
            worksheet.cell(row_index, 2).alignment = Alignment(wrap_text=True, vertical="top")
            worksheet.cell(row_index, 4).number_format = "#,##0.##"
    return output.getvalue()


@st.cache_data(show_spinner=False)
def material_upload_template_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Material Upload"
    worksheet.sheet_view.showGridLines = False

    worksheet.merge_cells("A1:C1")
    worksheet["A1"] = "Material Invoice Upload"
    worksheet["A1"].fill = PatternFill("solid", fgColor="4F46E5")
    worksheet["A1"].font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    worksheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
    worksheet.row_dimensions[1].height = 28

    worksheet.merge_cells("A2:C2")
    worksheet["A2"] = "Enter one invoice per row. Do not change the three column names."
    worksheet["A2"].fill = PatternFill("solid", fgColor="EEF2FF")
    worksheet["A2"].font = Font(name="Arial", size=10, italic=True, color="3730A3")
    worksheet["A2"].alignment = Alignment(horizontal="left", vertical="center")

    headers = ["Invoice Date", "Invoice No.", "Invoice Amount"]
    for column_number, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=4, column=column_number, value=header)
        cell.fill = PatternFill("solid", fgColor="312E81")
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    worksheet.column_dimensions["A"].width = 18
    worksheet.column_dimensions["B"].width = 25
    worksheet.column_dimensions["C"].width = 20
    worksheet.freeze_panes = "A5"
    for row_number in range(5, 105):
        worksheet.cell(row_number, 1).number_format = "DD-MMM-YYYY"
        worksheet.cell(row_number, 2).number_format = "@"
        worksheet.cell(row_number, 3).number_format = "#,##0.00"

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def render_table_toolbar(records, account_key, view_name):
    safe_view = re.sub(r"[^a-z0-9]+", "_", view_name.lower()).strip("_")
    safe_account = re.sub(r"[^a-z0-9]+", "_", account_key.lower()).strip("_")
    search_column, download_column = st.columns([4.5, 1.5])
    with search_column:
        search_text = st.text_input(
            f"Search {view_name}",
            placeholder="🔍 Search date, narration, reference, amount, team/vendor...",
            key=f"table_search_{safe_view}_{safe_account}",
            label_visibility="collapsed",
        )
    filtered_records = filter_transaction_records(records, search_text)
    with download_column:
        st.download_button(
            "📥 Download Excel",
            data=transaction_excel(filtered_records, view_name),
            file_name=f"{safe_account}_{safe_view}_{datetime.date.today():%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"table_download_{safe_view}_{safe_account}",
            use_container_width=True,
        )
    st.caption(f"Showing {len(filtered_records)} of {len(records)} transactions")
    return filtered_records


def render_statement_preview(preview_df: pd.DataFrame):
    date_column = "Invoice Date" if "Invoice Date" in preview_df.columns else "Date"
    reference_column = "Invoice No." if "Invoice No." in preview_df.columns else "Chq./Ref.No."
    amount_column = "Invoice Amount" if "Invoice Amount" in preview_df.columns else "Withdrawal Amt."
    rows_html = []
    for _, row in preview_df.iterrows():
        rows_html.append(
            "<tr>"
            f"<td class='p-date'>{html.escape(str(row[date_column]))}</td>"
            f"<td class='p-narration'>{html.escape(str(row['Narration']))}</td>"
            f"<td class='p-ref'>{html.escape(str(row[reference_column]))}</td>"
            f"<td class='p-amount'>{html.escape(str(row[amount_column]))}</td>"
            "</tr>"
        )

    table_html = (
        "<div class='preview-wrap'><table class='preview-table'>"
        "<colgroup>"
        "<col style='width:125px'>"
        "<col>"
        "<col style='width:205px'>"
        "<col style='width:125px'>"
        "</colgroup>"
        "<thead><tr>"
        f"<th class='p-date'>{date_column}</th>"
        "<th class='p-narration'>Narration</th>"
        f"<th class='p-ref'>{reference_column}</th>"
        f"<th class='p-amount'>{amount_column}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_bulk_search_and_move(records, account_key):
    with st.container(key="bulk_move_panel", border=True):
        st.markdown(
            "<div class='bulk-panel-title'>🔎 Bulk Transaction Move</div>",
            unsafe_allow_html=True,
        )
        search_column, amount_column = st.columns([3.2, 1.2])
        with search_column:
            search_text = st.text_input(
                "Search Transaction Type",
                placeholder="Search...  UPI-LITE / RENT / GST / Team name",
                key=f"bulk_search_{account_key}",
            ).strip()
        with amount_column:
            amount_less_than = st.number_input(
                "Amount Less Than",
                min_value=0,
                value=0,
                step=100,
                key=f"bulk_amount_less_than_{account_key}",
                help="Example: 1000 डालने पर केवल ₹1,000 से कम entries दिखेंगी।",
            )

        if not search_text and amount_less_than <= 0:
            return

        search_lower = search_text.lower()
        matches = [
            row
            for row in records
            if (
                not search_lower
                or search_lower in str(row.get("narration", "")).lower()
                or search_lower in str(row.get("reference_no", "")).lower()
            )
            and (
                amount_less_than <= 0
                or float(row.get("withdrawal_amount") or 0) < amount_less_than
            )
        ]

        if not matches:
            st.warning("इस search की कोई Pending entry नहीं मिली।")
            return

        total_amount = sum(float(row.get("withdrawal_amount") or 0) for row in matches)
        st.success(f"{len(matches)} matching entries मिलीं | Total {format_amount(total_amount)}")

        select_all = st.checkbox(
            "Select All",
            key=(
                f"bulk_select_all_{account_key}_"
                f"{hashlib.sha1(f'{search_lower}|{amount_less_than}'.encode()).hexdigest()[:10]}"
            ),
        )

        selection_df = pd.DataFrame(
            [
                {
                    "Select": select_all,
                    "ID": int(row["id"]),
                    "Date": format_date(row.get("transaction_date")),
                    "Narration": str(row.get("narration", "")),
                    "Chq./Ref.No.": str(row.get("reference_no", "")),
                    "Amount": format_amount(row.get("withdrawal_amount")),
                }
                for row in matches
            ]
        )

        editor_key = hashlib.sha1(
            f"{account_key}|{search_lower}|{amount_less_than}|{select_all}".encode("utf-8")
        ).hexdigest()[:12]
        edited_df = st.data_editor(
            selection_df,
            key=f"bulk_editor_{editor_key}",
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Date", "Narration", "Chq./Ref.No.", "Amount"],
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", width="small"),
                "ID": None,
                "Date": st.column_config.TextColumn(width="small"),
                "Narration": st.column_config.TextColumn(width="large"),
                "Chq./Ref.No.": st.column_config.TextColumn(width="medium"),
                "Amount": st.column_config.TextColumn(width="small"),
            },
            height=min(520, 42 + (len(selection_df) * 36)),
        )

        selected_ids = edited_df.loc[edited_df["Select"] == True, "ID"].astype(int).tolist()
        expense_categories = load_expense_categories()
        destination_options = (
            ["— Select Destination —", "Suspense"]
            + [f"Other Expense — {category}" for category in expense_categories]
            + [f"Team — {name}" for name in load_people("Team Name")]
            + [f"Vendor — {name}" for name in load_people("Vendor Name")]
        )

        destination_column, action_column = st.columns([3, 1.4])
        with destination_column:
            destination = st.selectbox(
                "Move To",
                options=destination_options,
                key=f"bulk_destination_{account_key}",
            )
            bulk_suspense_remark = ""
            if destination == "Suspense":
                bulk_suspense_remark = st.text_area(
                    "Suspense Remark",
                    placeholder="इस transaction को Suspense में रखने का कारण लिखें...",
                    key=f"bulk_suspense_remark_{account_key}",
                    height=80,
                )
        with action_column:
            st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
            move_clicked = st.button(
                f"Move Selected ({len(selected_ids)})",
                key=f"bulk_move_{account_key}",
                type="primary",
                use_container_width=True,
            )

        if move_clicked:
            try:
                if not selected_ids:
                    raise ValueError("कम से कम एक entry select करें")
                if destination == "— Select Destination —":
                    raise ValueError("Move To destination select करें")
                if destination == "Suspense" and not bulk_suspense_remark.strip():
                    raise ValueError("Suspense Remark लिखें")
                if destination.startswith(("Team — ", "Vendor — ")):
                    selected_id_set = set(selected_ids)
                    selected_rows = [
                        row for row in matches if int(row["id"]) in selected_id_set
                    ]
                    duplicate_rows = []
                    for selected_row in selected_rows:
                        existing_matches = find_possible_duplicates(selected_row, destination)
                        if existing_matches:
                            duplicate_rows.append(
                                {
                                    "transaction": selected_row,
                                    "existing": existing_matches,
                                }
                            )

                    if duplicate_rows:
                        st.session_state["banking_bulk_duplicate_review"] = {
                            "transaction_ids": selected_ids,
                            "assignment": destination,
                            "duplicate_rows": duplicate_rows,
                        }
                        bulk_duplicate_payment_dialog()
                        return

                    bulk_approve_transactions(selected_ids, destination, "proceed")
                    st.success(f"{len(selected_ids)} payments approve हो गईं।")
                else:
                    bulk_move_transactions(selected_ids, destination, bulk_suspense_remark)
                    st.success(f"{len(selected_ids)} selected entries successfully move हो गईं।")
                st.rerun()
            except Exception as exc:
                st.error(f"Bulk move failed: {exc}")


def render_header(show_assignment=True):
    widths = [0.9, 5.1, 1.5, 1.1, 2.3, 1.0] if show_assignment else [0.9, 5.4, 1.5, 1.1, 2.3]
    labels = ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Team/Vendor", "Action"] if show_assignment else ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Booked To"]
    columns = st.columns(widths)
    for column, label in zip(columns, labels):
        column.markdown(f"<div class='table-head'>{label}</div>", unsafe_allow_html=True)


def get_paginated_records(records, state_key):
    total_pages = max(1, math.ceil(len(records) / PAGE_SIZE))
    if state_key not in st.session_state:
        st.session_state[state_key] = 1
    st.session_state[state_key] = max(
        1,
        min(int(st.session_state[state_key]), total_pages),
    )
    current_page = int(st.session_state[state_key])
    start = (current_page - 1) * PAGE_SIZE
    return records[start : start + PAGE_SIZE], current_page, total_pages


def render_pagination_buttons(state_key, current_page, total_pages):
    st.markdown("<br>", unsafe_allow_html=True)
    previous_column, count_column, next_column = st.columns([1.5, 2, 1.5])

    with previous_column:
        if st.button(
            "⬅️ Previous Page",
            key=f"previous_{state_key}",
            use_container_width=True,
            disabled=current_page <= 1,
        ):
            st.session_state[state_key] = current_page - 1
            st.rerun()

    with count_column:
        st.markdown(
            f"<div style='text-align:center;font-size:1.1rem;font-weight:800;"
            f"color:#334155;padding:13px 8px;'>Page {current_page} of {total_pages}</div>",
            unsafe_allow_html=True,
        )

    with next_column:
        if st.button(
            "Next Page ➡️",
            key=f"next_{state_key}",
            use_container_width=True,
            disabled=current_page >= total_pages,
        ):
            st.session_state[state_key] = current_page + 1
            st.rerun()


def render_pending(records, account_key, view_status="Pending"):
    if not records:
        empty_message = "Suspense में कोई transaction नहीं है।" if view_status == "Suspense" else "सभी imported transactions process हो चुके हैं।"
        st.success(empty_message)
        return

    records = render_table_toolbar(records, account_key, view_status)
    if not records:
        st.warning("Search से कोई matching transaction नहीं मिला।")
        return

    options = assignment_options()
    if not options:
        st.error("Active Team/Vendor master खाली है।")
        return

    page_state_key = f"pending_page_{view_status}_{account_key}"
    visible, current_page, page_count = get_paginated_records(records, page_state_key)

    render_header(show_assignment=True)

    for row in visible:
        row_id = int(row["id"])
        cols = st.columns([0.9, 5.1, 1.5, 1.1, 2.3, 1.0])
        cols[0].markdown(f"<div class='txn-row'><b>{format_date(row.get('transaction_date'))}</b></div>", unsafe_allow_html=True)
        safe_narration = html.escape(str(row.get("narration", "")))
        safe_reference = html.escape(str(row.get("reference_no", "")))
        safe_suspense_remark = html.escape(str(row.get("suspense_remark", "") or ""))
        remark_html = (
            f"<br><span style='color:#b45309;font-weight:700;'>📝 {safe_suspense_remark}</span>"
            if view_status == "Suspense" and safe_suspense_remark
            else ""
        )
        cols[1].markdown(
            f"<div class='txn-row narration'>{safe_narration}{remark_html}</div>",
            unsafe_allow_html=True,
        )
        cols[2].markdown(f"<div class='txn-row narration'>{safe_reference}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='txn-row amount'>{format_amount(row.get('withdrawal_amount'))}</div>", unsafe_allow_html=True)
        assignment = cols[4].selectbox(
            "Team/Vendor",
            options=options,
            key=f"assignment_{view_status}_{account_key}_{row_id}",
            label_visibility="collapsed",
        )
        expense_category = None
        suspense_remark = ""
        if assignment == "Suspense":
            suspense_remark = cols[4].text_input(
                "Suspense Remark",
                value=str(row.get("suspense_remark", "") or ""),
                placeholder="Suspense का कारण...",
                key=f"suspense_remark_{view_status}_{account_key}_{row_id}",
                label_visibility="collapsed",
            )
        if assignment == "Other Expense":
            expense_categories = load_expense_categories()
            if expense_categories:
                expense_category = cols[4].selectbox(
                    "Expense Category",
                    options=expense_categories,
                    key=f"expense_category_{view_status}_{account_key}_{row_id}",
                    label_visibility="collapsed",
                )
            else:
                cols[4].error("पहले Expense Category Master में category add करें।")
        if cols[5].button("Approve", key=f"approve_{view_status}_{account_key}_{row_id}", type="primary", use_container_width=True):
            try:
                mode, _ = parse_assignment(assignment)
                if mode == "Suspense":
                    if not suspense_remark.strip():
                        raise ValueError("Suspense Remark लिखें")
                    move_to_suspense(row_id, suspense_remark)
                    st.success("Transaction Suspense में रख दिया गया।")
                    st.rerun()

                if mode == "Other Expense":
                    if not expense_category:
                        raise ValueError("Expense category select करें")
                    mark_other_expense(row_id, expense_category)
                    st.success("Transaction Other Expenses में save हुआ। Team/Vendor payment नहीं बनी।")
                    st.rerun()

                matches = find_possible_duplicates(row, assignment)
                if matches:
                    st.session_state["banking_duplicate_review"] = {
                        "transaction": row,
                        "assignment": assignment,
                        "matches": matches,
                    }
                    duplicate_payment_dialog()
                    return

                approve_transaction(row_id, assignment)
                st.success("Payment approved and booked successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Approval failed: {exc}")

    render_pagination_buttons(page_state_key, current_page, page_count)


@st.dialog("↩ Revoke Approved Payment", width="large")
def revoke_approved_payment_dialog():
    row = st.session_state.get("banking_revoke_review")
    if not row:
        st.info("Revoke के लिए कोई payment select नहीं है।")
        return

    st.warning("यह payment Team/Vendor ledger से हटेगी और transaction वापस Assign & Approve में आएगी।")
    booked_to = f"{row.get('assignment_mode', '')}: {row.get('pay_to', '')}"
    details = pd.DataFrame(
        [
            {
                "Date": format_date(row.get("transaction_date")),
                "Narration": str(row.get("narration", "")),
                "Ref. No.": str(row.get("reference_no", "")),
                "Amount": format_amount(row.get("withdrawal_amount")),
                "Booked To": booked_to,
            }
        ]
    )
    st.dataframe(details, use_container_width=True, hide_index=True)

    cancel_column, revoke_column = st.columns(2)
    if cancel_column.button("Cancel", use_container_width=True):
        st.session_state.pop("banking_revoke_review", None)
        st.rerun()
    if revoke_column.button(
        "Confirm Revoke",
        type="primary",
        use_container_width=True,
    ):
        try:
            revoke_approved_transaction(int(row["id"]))
            st.session_state.pop("banking_revoke_review", None)
            st.success("Payment revoke हो गई। Transaction वापस Assign & Approve में आ गया।")
            st.rerun()
        except Exception as exc:
            st.error(f"Revoke failed: {exc}")


def render_approved(records, account_key):
    if not records:
        st.info("अभी कोई approved transaction नहीं है।")
        return

    booked_filter_columns = st.columns([0.9, 5.0, 1.4, 1.1, 2.1, 1.0])
    booked_to_values = sorted(
        {
            (
                str(row.get("assignment_mode", "")).strip(),
                str(row.get("pay_to", "")).strip(),
            )
            for row in records
            if str(row.get("pay_to", "")).strip()
        },
        key=lambda value: (value[0].lower(), value[1].lower()),
    )
    booked_to_options = ["All Team & Vendor"] + [
        f"{mode}: {pay_to}" if mode else pay_to
        for mode, pay_to in booked_to_values
    ]
    with booked_filter_columns[4]:
        booked_to_filter = st.selectbox(
            "Booked To Filter",
            options=booked_to_options,
            key=f"approved_booked_to_filter_{account_key}",
        )

    if booked_to_filter != "All Team & Vendor":
        records = [
            row
            for row in records
            if (
                f"{str(row.get('assignment_mode', '')).strip()}: "
                f"{str(row.get('pay_to', '')).strip()}"
            ).strip(": ")
            == booked_to_filter
        ]

    records = render_table_toolbar(records, account_key, "Approved Payments")
    if not records:
        st.warning("Search से कोई matching transaction नहीं मिला।")
        return

    page_state_key = f"approved_page_{account_key}"
    visible, current_page, page_count = get_paginated_records(records, page_state_key)

    header_columns = st.columns([0.9, 5.0, 1.4, 1.1, 2.1, 1.0])
    for column, label in zip(
        header_columns,
        ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Booked To", "Action"],
    ):
        column.markdown(f"<div class='table-head'>{label}</div>", unsafe_allow_html=True)
    for row in visible:
        row_id = int(row["id"])
        cols = st.columns([0.9, 5.0, 1.4, 1.1, 2.1, 1.0])
        cols[0].markdown(f"<div class='txn-row'><b>{format_date(row.get('transaction_date'))}</b></div>", unsafe_allow_html=True)
        safe_narration = html.escape(str(row.get("narration", "")))
        safe_reference = html.escape(str(row.get("reference_no", "")))
        cols[1].markdown(f"<div class='txn-row narration'>{safe_narration}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='txn-row narration'>{safe_reference}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='txn-row amount'>{format_amount(row.get('withdrawal_amount'))}</div>", unsafe_allow_html=True)
        change_options = (
            [f"Team — {name}" for name in load_people("Team Name")]
            + [f"Vendor — {name}" for name in load_people("Vendor Name")]
        )
        current_assignment = (
            f"{str(row.get('assignment_mode', '')).strip()} — "
            f"{str(row.get('pay_to', '')).strip()}"
        ).strip(" —")
        if current_assignment and current_assignment not in change_options:
            change_options.insert(0, current_assignment)
        selected_assignment = cols[4].selectbox(
            "Booked To",
            options=change_options,
            index=change_options.index(current_assignment) if current_assignment in change_options else 0,
            key=f"approved_assignment_{account_key}_{row_id}",
            label_visibility="collapsed",
        )
        if cols[5].button(
            "✓ Update",
            key=f"update_approved_{account_key}_{row_id}",
            type="primary",
            use_container_width=True,
        ):
            try:
                if selected_assignment == current_assignment:
                    raise ValueError("नई Team/Vendor select करें")
                change_approved_transaction_assignment(row_id, selected_assignment)
                st.success("Booked To successfully change हो गया।")
                st.rerun()
            except Exception as exc:
                st.error(f"Change failed: {exc}")
        if cols[5].button(
            "↩ Revoke",
            key=f"revoke_approved_{account_key}_{row_id}",
            use_container_width=True,
        ):
            st.session_state["banking_revoke_review"] = row
            revoke_approved_payment_dialog()

    render_pagination_buttons(page_state_key, current_page, page_count)


def render_other_expenses(records, account_key):
    if not records:
        st.info("अभी कोई Other Expense transaction नहीं है।")
        return

    records = render_table_toolbar(records, account_key, "Other Expenses")
    if not records:
        st.warning("Search से कोई matching transaction नहीं मिला।")
        return

    page_state_key = f"other_expense_page_{account_key}"
    visible, current_page, page_count = get_paginated_records(records, page_state_key)
    columns = st.columns([0.9, 5.0, 1.5, 1.1, 2.0, 1.2])
    for column, label in zip(
        columns,
        ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Expense Category", "Action"],
    ):
        column.markdown(f"<div class='table-head'>{label}</div>", unsafe_allow_html=True)

    for row in visible:
        row_id = int(row["id"])
        cols = st.columns([0.9, 5.0, 1.5, 1.1, 2.0, 1.2])
        safe_narration = html.escape(str(row.get("narration", "")))
        safe_reference = html.escape(str(row.get("reference_no", "")))
        safe_category = html.escape(str(row.get("expense_category", "")))
        cols[0].markdown(f"<div class='txn-row'><b>{format_date(row.get('transaction_date'))}</b></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='txn-row narration'>{safe_narration}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='txn-row narration'>{safe_reference}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='txn-row amount'>{format_amount(row.get('withdrawal_amount'))}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div class='txn-row approved'>{safe_category}</div>", unsafe_allow_html=True)
        if cols[5].button("Restore", key=f"restore_expense_{account_key}_{row_id}", use_container_width=True):
            try:
                restore_to_pending(row_id)
                st.success("Transaction वापस Assign & Approve में आ गया।")
                st.rerun()
            except Exception as exc:
                st.error(f"Restore failed: {exc}")

    render_pagination_buttons(page_state_key, current_page, page_count)


@st.dialog("Possible Duplicate Payment", width="large")
def duplicate_payment_dialog():
    review = st.session_state.get("banking_duplicate_review")
    if not review:
        return

    transaction = review["transaction"]
    assignment = review["assignment"]
    matches = review["matches"]

    st.warning("Same Date + Same Amount + Same Team/Vendor की payment पहले से मौजूद है।")
    st.markdown(
        f"**Current bank transaction:** {format_date(transaction.get('transaction_date'))} | "
        f"{format_amount(transaction.get('withdrawal_amount'))} | {html.escape(assignment)}"
    )

    match_df = pd.DataFrame(matches)
    show_columns = ["id", "date", "amount", "mode", "pay_to", "pay_from", "pay_type", "remark"]
    match_df = match_df[[column for column in show_columns if column in match_df.columns]].copy()
    if "date" in match_df.columns:
        match_df["date"] = match_df["date"].apply(format_date)
    if "amount" in match_df.columns:
        match_df["amount"] = match_df["amount"].apply(format_amount)
    st.dataframe(match_df, use_container_width=True, hide_index=True)

    payment_ids = [int(item["id"]) for item in matches]
    selected_payment_id = st.selectbox(
        "Existing Payment",
        options=payment_ids,
        format_func=lambda payment_id: next(
            (
                f"ID {payment_id} | {format_date(item.get('date'))} | "
                f"{format_amount(item.get('amount'))} | {item.get('mode')}: {item.get('pay_to')}"
                for item in matches
                if int(item["id"]) == payment_id
            ),
            str(payment_id),
        ),
    )

    left, right = st.columns(2)
    if left.button("Duplicate Entry", type="secondary", use_container_width=True):
        try:
            link_as_duplicate(
                int(transaction["id"]),
                int(selected_payment_id),
                assignment,
            )
            st.session_state.pop("banking_duplicate_review", None)
            st.success("Existing payment से link किया। नई payment entry नहीं बनी।")
            st.rerun()
        except Exception as exc:
            st.error(f"Duplicate link failed: {exc}")

    if right.button("Proceed", type="primary", use_container_width=True):
        try:
            approve_transaction(int(transaction["id"]), assignment)
            st.session_state.pop("banking_duplicate_review", None)
            st.success("नई payment entry save हो गई।")
            st.rerun()
        except Exception as exc:
            st.error(f"Payment approval failed: {exc}")


@st.dialog("Bulk Possible Duplicate Payments", width="large")
def bulk_duplicate_payment_dialog():
    review = st.session_state.get("banking_bulk_duplicate_review")
    if not review:
        return

    assignment = review["assignment"]
    duplicate_rows = review["duplicate_rows"]
    st.warning(
        f"{len(duplicate_rows)} selected transaction(s) में Same Date + Amount + "
        f"{html.escape(assignment)} payment पहले से मौजूद है।"
    )

    display_rows = []
    for item in duplicate_rows:
        transaction = item["transaction"]
        for existing in item["existing"]:
            display_rows.append(
                {
                    "Bank Date": format_date(transaction.get("transaction_date")),
                    "Bank Amount": format_amount(transaction.get("withdrawal_amount")),
                    "Selected For": assignment,
                    "Existing Payment ID": existing.get("id"),
                    "Existing Date": format_date(existing.get("date")),
                    "Existing Amount": format_amount(existing.get("amount")),
                    "Existing Name": f"{existing.get('mode')}: {existing.get('pay_to')}",
                }
            )
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    if left.button("Duplicate Entry", key="bulk_duplicate_link", use_container_width=True):
        try:
            bulk_approve_transactions(
                review["transaction_ids"],
                assignment,
                "link",
            )
            st.session_state.pop("banking_bulk_duplicate_review", None)
            st.success("Existing matching payments link हुईं; duplicate payments नहीं बनीं।")
            st.rerun()
        except Exception as exc:
            st.error(f"Bulk duplicate link failed: {exc}")

    if right.button("Proceed", key="bulk_duplicate_proceed", type="primary", use_container_width=True):
        try:
            bulk_approve_transactions(
                review["transaction_ids"],
                assignment,
                "proceed",
            )
            st.session_state.pop("banking_bulk_duplicate_review", None)
            st.success("सभी selected transactions की नई payments save हो गईं।")
            st.rerun()
        except Exception as exc:
            st.error(f"Bulk approval failed: {exc}")


@st.dialog("➕ Manual Material Invoice", width="large")
def manual_material_invoice_dialog(vendor_name: str):
    vendor = MATERIAL_VENDORS[vendor_name]
    st.markdown(f"### {html.escape(vendor['pay_from'])}")

    review_key = f"banking_manual_material_review_{vendor['key']}"
    review = st.session_state.get(review_key)

    if review:
        record = review["record"]
        duplicates = review["duplicates"]
        st.warning("यह invoice पहले से मौजूद हो सकता है। नीचे existing entry check करें।")
        duplicate_df = pd.DataFrame(
            [
                {
                    "Vendor": row.get("pay_from", vendor["pay_from"]),
                    "Invoice Date": format_date(row.get("transaction_date")),
                    "Invoice No.": row.get("reference_no", ""),
                    "Invoice Amount": format_amount(row.get("withdrawal_amount")),
                    "Status": row.get("status", ""),
                }
                for row in duplicates
            ]
        )
        st.dataframe(duplicate_df, use_container_width=True, hide_index=True)
        left, right = st.columns(2)
        if left.button("Duplicate Entry — Do Not Add", use_container_width=True):
            st.session_state.pop(review_key, None)
            st.rerun()
        if right.button("Proceed Anyway", type="primary", use_container_width=True):
            try:
                duplicate_record = build_manual_material_record(
                    vendor_name,
                    record["transaction_date"],
                    record["reference_no"],
                    record["withdrawal_amount"],
                    allow_duplicate=True,
                )
                supabase.table("bank_transactions").insert(duplicate_record).execute()
                st.session_state.pop(review_key, None)
                st.success("Manual invoice Pending में add हो गया।")
                st.rerun()
            except Exception as exc:
                st.error(f"Manual invoice save नहीं हुआ: {exc}")
        return

    with st.form(f"manual_material_form_{vendor['key']}", clear_on_submit=False):
        date_column, invoice_column, amount_column = st.columns([1.1, 1.5, 1.1])
        with date_column:
            invoice_date = st.date_input("Invoice Date", value=datetime.date.today())
        with invoice_column:
            invoice_no = st.text_input("Invoice Number", placeholder="Example: 1254/26-27")
        with amount_column:
            invoice_amount = st.number_input("Invoice Amount", min_value=0.0, step=1.0, format="%.2f")
        save_clicked = st.form_submit_button(
            "Save Manual Invoice",
            type="primary",
            use_container_width=True,
        )

    if save_clicked:
        try:
            record = build_manual_material_record(
                vendor_name,
                invoice_date,
                invoice_no,
                invoice_amount,
            )
            duplicates = find_manual_material_duplicate(record)
            if duplicates:
                st.session_state[review_key] = {
                    "record": record,
                    "duplicates": duplicates,
                }
                st.rerun(scope="fragment")
            else:
                supabase.table("bank_transactions").insert(record).execute()
                st.success("Manual invoice Pending में add हो गया।")
                st.rerun()
        except Exception as exc:
            st.error(f"Manual invoice save नहीं हुआ: {exc}")


if "banking_active_account" not in st.session_state:
    st.session_state.banking_active_account = "HDFC VISPL"
if "banking_active_material_vendor" not in st.session_state:
    st.session_state.banking_active_material_vendor = next(iter(MATERIAL_VENDORS))
if "banking_active_view" not in st.session_state:
    st.session_state.banking_active_view = "Assign & Approve"

with st.container(key="banking_account_nav"):
    account_nav_columns = st.columns(len(MAIN_ACCOUNT_TABS))
    for nav_column, account_name in zip(account_nav_columns, MAIN_ACCOUNT_TABS):
        with nav_column:
            account_active = st.session_state.banking_active_account == account_name
            if st.button(
                account_name,
                key=f"bank_account_nav_{clean_header(account_name)}",
                type="primary" if account_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.banking_active_account = account_name
                st.rerun()

is_indus = st.session_state.banking_active_account == "INDUS"
is_material = st.session_state.banking_active_account == "Material"
if not is_indus:
    if is_material:
        with st.container(key="banking_material_vendor_nav"):
            vendor_columns = st.columns(len(MATERIAL_VENDORS))
            for vendor_column, vendor_name in zip(vendor_columns, MATERIAL_VENDORS.keys()):
                with vendor_column:
                    vendor_active = st.session_state.banking_active_material_vendor == vendor_name
                    if st.button(
                        vendor_name,
                        key=f"material_vendor_nav_{MATERIAL_VENDORS[vendor_name]['key']}",
                        type="primary" if vendor_active else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state.banking_active_material_vendor = vendor_name
                        st.rerun()
        active_account_label = st.session_state.banking_active_material_vendor
        active_account_data = MATERIAL_VENDORS[active_account_label]
        active_account_heading = f"Material — {html.escape(active_account_label)}"
    else:
        active_account_label = st.session_state.banking_active_account
        active_account_data = ACCOUNTS[active_account_label]
        active_account_heading = html.escape(active_account_label)

    st.markdown(
        f"""
        <div class="bank-title">
            <h1>🏦 {active_account_heading}</h1>
            <p>{'Material invoice upload, allocation and payment approval' if is_material else 'Statement upload, Team/Vendor allocation and payment approval'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Expense Category Master — नया खर्च जोड़ें"):
        st.caption("यहाँ जो category add करेंगे, वही Other Expense dropdown में दिखेगी।")
        with st.form("add_expense_category_form", clear_on_submit=True):
            new_expense_category = st.text_input(
                "New Expense Category",
                placeholder="Example: Office Rent, EMI, GST Paid",
            )
            add_category_clicked = st.form_submit_button(
                "Add Category",
                type="primary",
            )
        if add_category_clicked:
            try:
                add_expense_category(new_expense_category)
                st.success("Expense category add हो गई।")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        try:
            active_expenses = load_expense_categories()
            if active_expenses:
                st.write("Active Categories: " + ", ".join(active_expenses))
        except Exception as exc:
            st.warning(f"Expense categories load नहीं हुईं: {exc}")

    for account_label, account in [(active_account_label, active_account_data)]:
        with st.container():
            st.subheader(account_label)

            # Material ko chhodkar har banking account par latest saved data date.
            if not is_material:
                render_last_data_date_card(
                    get_bank_last_data_date(account["key"]),
                    "BANK STATEMENT",
                )

            workflow_views = [
                ("Assign & Approve", "✅ Assign & Approve"),
                ("Approved Payments", "💳 Approved Payments"),
                ("Suspense", "⏳ Suspense"),
                ("Other Expenses", "🧾 Other Expenses"),
            ]
            with st.container(key="banking_view_nav"):
                view_columns = st.columns(len(workflow_views))
                for view_column, (view_key, view_label) in zip(view_columns, workflow_views):
                    with view_column:
                        view_active = st.session_state.banking_active_view == view_key
                        if st.button(
                            view_label,
                            key=f"bank_view_nav_{view_key}",
                            type="primary" if view_active else "secondary",
                            use_container_width=True,
                        ):
                            st.session_state.banking_active_view = view_key
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Step 1: Material Invoice Upload" if is_material else "#### Step 1: Statement Upload")
            if is_material:
                manual_column, template_column, blank_column = st.columns([1.5, 1.9, 3.6])
                with manual_column:
                    if st.button(
                        "➕ Manual Add Entry",
                        key=f"manual_material_entry_{account['key']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        manual_material_invoice_dialog(account_label)
                with template_column:
                    st.download_button(
                        "⬇️ Download Material Excel Format",
                        data=material_upload_template_excel(),
                        file_name="Material_Statement_Upload_Template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_material_template_{account['key']}",
                        use_container_width=True,
                    )
            uploaded = st.file_uploader(
                "Upload material statement (.xls or .xlsx)" if is_material else "Upload bank statement (.xls or .xlsx)",
                type=["xls", "xlsx"],
                key=f"upload_{account['key']}",
            )

            if uploaded is not None:
                try:
                    file_bytes = uploaded.getvalue()
                    sheet_names = workbook_sheet_names(file_bytes)
                    selected_sheet = st.selectbox(
                        "Excel Sheet",
                        options=sheet_names,
                        key=f"sheet_{account['key']}",
                    )
                    if is_material:
                        preview_records = parse_material_statement(
                            file_bytes,
                            selected_sheet,
                            account_label,
                            uploaded.name,
                        )
                        st.info(f"Preview: {len(preview_records)} material invoices मिले। Existing duplicate invoices import नहीं होंगे।")
                    else:
                        preview_records = parse_statement(
                            file_bytes,
                            selected_sheet,
                            account_label,
                            uploaded.name,
                        )
                        st.info(
                            f"Preview: {len(preview_records)} unique withdrawal transactions मिले। "
                            "Same-file और already-saved duplicate transactions import नहीं होंगे। "
                            "Deposit और Closing Balance शामिल नहीं हैं।"
                        )

                    preview_df = pd.DataFrame(preview_records)[
                        ["transaction_date", "narration", "reference_no", "withdrawal_amount"]
                    ].sort_values("transaction_date", ascending=False)
                    preview_df.columns = [
                        "Invoice Date" if is_material else "Date",
                        "Narration",
                        "Invoice No." if is_material else "Chq./Ref.No.",
                        "Invoice Amount" if is_material else "Withdrawal Amt.",
                    ]
                    date_column = "Invoice Date" if is_material else "Date"
                    amount_column = "Invoice Amount" if is_material else "Withdrawal Amt."
                    preview_df[date_column] = pd.to_datetime(preview_df[date_column]).dt.strftime("%d-%b-%Y")
                    preview_df[amount_column] = preview_df[amount_column].apply(format_amount)
                    render_statement_preview(preview_df)

                    if st.button("Save Transactions & Continue", key=f"import_{account['key']}", type="primary"):
                        before = sum(
                            len(fetch_transactions(account["key"], status))
                            for status in ("Pending", "Approved", "Suspense", "Other Expense")
                        )
                        supabase.table("bank_transactions").upsert(
                            preview_records,
                            on_conflict="workspace,account_key,transaction_hash",
                            ignore_duplicates=True,
                        ).execute()
                        after = sum(
                            len(fetch_transactions(account["key"], status))
                            for status in ("Pending", "Approved", "Suspense", "Other Expense")
                        )
                        st.success(f"Import completed. New entries: {max(0, after - before)} | Duplicate skipped: {max(0, len(preview_records) - max(0, after - before))}")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Statement save नहीं हुआ: {exc}")

            if st.session_state.banking_active_view == "Assign & Approve":
                try:
                    pending_records = fetch_transactions(account["key"], "Pending")
                    render_bulk_search_and_move(pending_records, account["key"])
                    render_pending(pending_records, account["key"], "Pending")
                except Exception as exc:
                    st.warning(f"Supabase connect नहीं हुआ, इसलिए Team/Vendor dropdown अभी नहीं दिख सकता: {exc}")
            elif st.session_state.banking_active_view == "Approved Payments":
                try:
                    render_approved(fetch_transactions(account["key"], "Approved"), account["key"])
                except Exception as exc:
                    st.warning(f"Approved payments load नहीं हुए: {exc}")
            elif st.session_state.banking_active_view == "Suspense":
                try:
                    render_pending(fetch_transactions(account["key"], "Suspense"), account["key"], "Suspense")
                except Exception as exc:
                    st.warning(f"Suspense transactions load नहीं हुए: {exc}")
            elif st.session_state.banking_active_view == "Other Expenses":
                try:
                    render_other_expenses(
                        fetch_transactions(account["key"], "Other Expense"),
                        account["key"],
                    )
                except Exception as exc:
                    st.warning(f"Other Expenses load नहीं हुए: {exc}")

# =============================================================================
# INDUS RECEIVABLES — Invoice / Payments / Prepayment / Credit Note
# Added at the end of the existing Banking page.
# Existing Banking logic above is unchanged.
# =============================================================================

st.markdown("""
<style>
.indus-hero {
    margin-top: 34px;
    padding: 26px 28px;
    border-radius: 22px;
    background: linear-gradient(120deg,#0f172a 0%,#1d4ed8 38%,#7c3aed 72%,#db2777 100%);
    box-shadow: 0 18px 45px rgba(30,64,175,.24);
    color: white;
}
.indus-hero h2 {margin:0;color:#fff!important;font-size:2rem;font-weight:900;}
.indus-hero p {margin:6px 0 0;color:#e0e7ff!important;font-weight:650;}
.indus-card {
    background:rgba(255,255,255,.97);
    border:1px solid rgba(99,102,241,.15);
    border-radius:18px;
    padding:17px 18px;
    box-shadow:0 8px 24px rgba(15,23,42,.08);
    min-height:112px;
}
.indus-card .label {font-size:.84rem;color:#64748b;font-weight:800;text-transform:uppercase;letter-spacing:.5px;}
.indus-card .value {font-size:1.55rem;color:#0f172a;font-weight:950;margin-top:7px;}
.indus-card .sub {font-size:.78rem;color:#64748b;font-weight:650;margin-top:4px;}
.indus-section {
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:18px;
    box-shadow:0 8px 25px rgba(15,23,42,.06);
}
div[data-testid="stTabs"] button {font-weight:900!important;font-size:1rem!important;}
div[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:10px;}
div[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius:12px 12px 0 0;
    padding:12px 20px;
}
</style>
""", unsafe_allow_html=True)


def indus_clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def indus_number(value, default=0.0):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return float(default)

    raw = str(value).strip().replace(",", "")
    trailing_minus = raw.endswith("-")
    if trailing_minus:
        raw = raw[:-1].strip()

    cleaned = re.sub(r"[^0-9.\-]", "", raw)
    if cleaned in {"", "-", ".", "-."}:
        return float(default)

    try:
        number = float(cleaned)
        if trailing_minus:
            number = -abs(number)
        return round(number, 2)
    except Exception:
        return float(default)


def indus_date(value):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def indus_read_tsv(file_bytes):
    # Oracle export is tab separated. utf-8-sig also safely removes BOM.
    df = pd.read_csv(
        io.BytesIO(file_bytes),
        sep="\t",
        dtype=object,
        encoding="utf-8-sig",
        keep_default_na=False,
    )
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not c.lower().startswith("unnamed")]]
    required = {"Invoice", "Invoice Date", "Type", "Amount", "Due"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError("Indus TSV columns missing: " + ", ".join(missing))
    return df


def indus_original_invoice_from_credit_memo(credit_memo_no):
    text = indus_clean_text(credit_memo_no)
    # Example: VIS/26-27/1435-TDS-CM-11428046 -> VIS/26-27/1435
    match = re.match(r"^(.*?)-TDS-CM-", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def indus_po_from_prepayment(invoice_text, po_value=""):
    direct_po = indus_clean_text(po_value)
    if direct_po:
        return direct_po
    text = indus_clean_text(invoice_text)
    match = re.search(r"ADV[_\-\s]*PO[_\-\s]*(\d+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def indus_fetch_all(table_name, order_column=None, descending=False):
    """
    Fetch ALL INDUS rows from Supabase.
    Supabase/PostgREST commonly returns max 1000 rows per request,
    so fetch in 1000-row pages until the final partial page.
    """
    all_rows = []
    page_size = 1000
    start_row = 0

    while True:
        query = (
            supabase.table(table_name)
            .select("*")
            .eq("workspace", ALLOWED_WORKSPACE)
        )

        if order_column:
            query = query.order(order_column, desc=descending)

        response = query.range(start_row, start_row + page_size - 1).execute()
        batch = response.data or []
        all_rows.extend(batch)

        if len(batch) < page_size:
            break

        start_row += page_size

    return all_rows


def indus_existing_invoice(receipt_no):
    if not receipt_no:
        return None
    response = (
        supabase.table("indus_invoices")
        .select("*")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("receipt_no", receipt_no)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def indus_invoice_by_number(invoice_no):
    if not invoice_no:
        return None
    response = (
        supabase.table("indus_invoices")
        .select("*")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("invoice_no", invoice_no)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def indus_tds_for_invoice(invoice_no):
    if not invoice_no:
        return 0.0
    response = (
        supabase.table("indus_credit_memos")
        .select("tds_amount")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("original_invoice_no", invoice_no)
        .execute()
    )
    return round(sum(indus_number(r.get("tds_amount")) for r in (response.data or [])), 2)


def indus_recalculate_invoice(invoice_no):
    row = indus_invoice_by_number(invoice_no)
    if not row:
        return
    amount = indus_number(row.get("invoice_amount"))
    due = max(0.0, indus_number(row.get("outstanding_amount")))
    tds = max(0.0, indus_tds_for_invoice(invoice_no))
    net = max(0.0, amount - tds)
    received = max(0.0, net - due)
    supabase.table("indus_invoices").update({
        "tds_amount": tds,
        "payment_received": received,
        "updated_by": current_user(),
    }).eq("id", row["id"]).execute()


def indus_import_tsv(df, file_name):
    counts = {
        "total": len(df),
        "standard": 0,
        "credit": 0,
        "debit": 0,
        "prepayment": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
    }
    touched_invoices = set()

    # Standard first so Credit Memo can immediately attach to invoice.
    type_order = {"Standard": 0, "Credit Memo": 1, "Prepayment": 2, "Debit Memo": 3}
    work_df = df.copy()
    work_df["_sort"] = work_df["Type"].map(type_order).fillna(99)
    work_df = work_df.sort_values("_sort")

    for _, raw in work_df.iterrows():
        row_type = indus_clean_text(raw.get("Type"))
        source_invoice = indus_clean_text(raw.get("Invoice"))
        amount = indus_number(raw.get("Amount"))
        due = max(0.0, indus_number(raw.get("Due")))
        invoice_date = indus_date(raw.get("Invoice Date"))
        due_date = indus_date(raw.get("Due Date"))
        po_number = indus_clean_text(raw.get("PO Number"))
        receipt_no = indus_clean_text(raw.get("Receipt"))
        payment_ref = indus_clean_text(raw.get("Payment"))
        payment_utr = indus_clean_text(raw.get("Payment UTR#"))
        payment_status = indus_clean_text(raw.get("Payment Status"))
        invoice_status = indus_clean_text(raw.get("Invoice Status"))

        if row_type == "Standard":
            counts["standard"] += 1
            if not receipt_no:
                counts["skipped"] += 1
                continue

            existing = indus_existing_invoice(receipt_no)
            is_ers = source_invoice.upper().startswith("ERS")
            ers_no = source_invoice if is_ers else (existing or {}).get("ers_no")
            invoice_no = (existing or {}).get("invoice_no") if is_ers else source_invoice
            tds = indus_tds_for_invoice(invoice_no) if invoice_no else indus_number((existing or {}).get("tds_amount"))
            net = max(0.0, amount - tds)
            received = max(0.0, net - due)

            payload = {
                "workspace": ALLOWED_WORKSPACE,
                "receipt_no": receipt_no,
                "ers_no": ers_no or None,
                "invoice_no": invoice_no or None,
                "invoice_date": invoice_date,
                "due_date": due_date,
                "po_number": po_number or None,
                "invoice_amount": amount,
                "tds_amount": tds,
                "payment_received": received,
                "outstanding_amount": due,
                "payment_status": payment_status or None,
                "invoice_status": invoice_status or None,
                "payment_reference": payment_ref or None,
                "payment_utr": payment_utr or None,
                "source_invoice_text": source_invoice,
                "source_type": "Standard",
                "source_file_name": file_name,
                "updated_by": current_user(),
            }
            if existing:
                supabase.table("indus_invoices").update(payload).eq("id", existing["id"]).execute()
                counts["updated"] += 1
            else:
                payload["created_by"] = current_user()
                supabase.table("indus_invoices").insert(payload).execute()
                counts["inserted"] += 1

            if invoice_no:
                touched_invoices.add(invoice_no)

        elif row_type == "Credit Memo":
            counts["credit"] += 1
            original_invoice = indus_original_invoice_from_credit_memo(source_invoice)
            if not original_invoice:
                counts["skipped"] += 1
                continue
            payload = {
                "workspace": ALLOWED_WORKSPACE,
                "credit_memo_no": source_invoice,
                "original_invoice_no": original_invoice,
                "credit_memo_date": invoice_date,
                "tds_amount": abs(amount),
                "raw_amount": amount,
                "status": invoice_status or payment_status or None,
                "source_file_name": file_name,
                "created_by": current_user(),
            }
            supabase.table("indus_credit_memos").upsert(
                payload,
                on_conflict="workspace,credit_memo_no",
            ).execute()
            touched_invoices.add(original_invoice)

        elif row_type == "Prepayment":
            counts["prepayment"] += 1
            prepayment_ref = source_invoice
            po = indus_po_from_prepayment(source_invoice, po_number)
            if not prepayment_ref or not po:
                counts["skipped"] += 1
                continue
            payload = {
                "workspace": ALLOWED_WORKSPACE,
                "prepayment_ref": prepayment_ref,
                "po_number": po,
                "prepayment_date": invoice_date,
                "advance_amount": abs(amount),
                "status": invoice_status or payment_status or None,
                "source_file_name": file_name,
                "created_by": current_user(),
            }
            supabase.table("indus_prepayments").upsert(
                payload,
                on_conflict="workspace,prepayment_ref",
            ).execute()

        elif row_type == "Debit Memo":
            counts["debit"] += 1
            if not source_invoice:
                counts["skipped"] += 1
                continue
            payload = {
                "workspace": ALLOWED_WORKSPACE,
                "debit_memo_no": source_invoice,
                "debit_memo_date": invoice_date,
                "amount": abs(amount),
                "due_amount": due,
                "status": invoice_status or payment_status or None,
                "description": indus_clean_text(raw.get("Ref. Invoice Number")) or None,
                "source_file_name": file_name,
                "created_by": current_user(),
            }
            supabase.table("indus_debit_memos").upsert(
                payload,
                on_conflict="workspace,debit_memo_no",
            ).execute()
        else:
            counts["skipped"] += 1

    # Recalculate TDS/payment after all credit memos are saved.
    for invoice_no in touched_invoices:
        indus_recalculate_invoice(invoice_no)

    supabase.table("indus_import_history").insert({
        "workspace": ALLOWED_WORKSPACE,
        "file_name": file_name,
        "total_rows": counts["total"],
        "standard_rows": counts["standard"],
        "credit_memo_rows": counts["credit"],
        "debit_memo_rows": counts["debit"],
        "prepayment_rows": counts["prepayment"],
        "inserted_rows": counts["inserted"],
        "updated_rows": counts["updated"],
        "skipped_rows": counts["skipped"],
        "uploaded_by": current_user(),
    }).execute()

    return counts



def get_indus_last_data_date():
    """
    Latest business-data date in INDUS tables.
    Uses invoice/credit/prepayment/debit date, not browser upload time.
    """
    candidates = []
    checks = [
        ("indus_invoices", "invoice_date"),
        ("indus_credit_memos", "credit_memo_date"),
        ("indus_prepayments", "prepayment_date"),
        ("indus_debit_memos", "debit_memo_date"),
    ]
    for table_name, date_col in checks:
        try:
            response = (
                supabase.table(table_name)
                .select(date_col)
                .eq("workspace", ALLOWED_WORKSPACE)
                .not_.is_(date_col, "null")
                .order(date_col, desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                parsed = to_date(response.data[0].get(date_col))
                if parsed:
                    candidates.append(parsed)
        except Exception:
            pass
    return max(candidates) if candidates else None


def indus_is_blocked(row):
    """Blocked ERS/Invoice is excluded from every financial calculation."""
    return bool(row.get("is_blocked", False))


def indus_block_invoice(record_id, remark=""):
    supabase.table("indus_invoices").update({
        "is_blocked": True,
        "block_remark": str(remark or "").strip(),
        "blocked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "blocked_by": indus_current_user_value(),
        "last_updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }).eq("id", record_id).execute()


def indus_unblock_invoice(record_id):
    supabase.table("indus_invoices").update({
        "is_blocked": False,
        "block_remark": None,
        "blocked_at": None,
        "blocked_by": None,
        "last_updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }).eq("id", record_id).execute()

def indus_read_payment_tsv(file_bytes):
    """
    Read Indus Oracle day-wise Payment TSV.

    Oracle format:
      Row 1: Payment Date / Method / Status ...
      Row 2: payment header values
      blank rows
      later row: Invoice / Invoice Date / Invoice Type / ... / Receipt
      following rows: actual allocations
    """
    import csv

    decoded = file_bytes.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(decoded), delimiter="\t"))

    if not rows:
        raise ValueError("Payment TSV empty hai.")

    # ---- Payment Date from the top payment-summary section ----
    payment_date = ""
    top_header = [str(x).strip().strip('"') for x in rows[0]]
    if "Payment Date" in top_header and len(rows) > 1:
        idx = top_header.index("Payment Date")
        if idx < len(rows[1]):
            payment_date = str(rows[1][idx]).strip().strip('"')

    # ---- Find the real invoice table header ----
    invoice_header_index = None
    for i, row in enumerate(rows):
        cleaned = [str(x).strip().strip('"') for x in row]
        if (
            "Invoice" in cleaned
            and "Invoice Date" in cleaned
            and "Invoice Type" in cleaned
            and "Payment Amount" in cleaned
        ):
            invoice_header_index = i
            break

    if invoice_header_index is None:
        raise ValueError(
            "Payment file me Invoice table header nahi mila. "
            "Expected columns: Invoice, Invoice Date, Invoice Type, Payment Amount."
        )

    headers = [str(x).strip().strip('"') for x in rows[invoice_header_index]]
    wanted = [
        "Payment Date", "Invoice", "Invoice Date", "Invoice Type", "Currency",
        "Amount", "Status", "Payment Status", "Payment Amount", "PO Number", "Receipt"
    ]

    records = []
    for row in rows[invoice_header_index + 1:]:
        values = [str(x).strip().strip('"') for x in row]

        # Skip fully blank lines.
        if not any(values):
            continue

        # Pad short rows.
        if len(values) < len(headers):
            values += [""] * (len(headers) - len(values))

        rec = dict(zip(headers, values))
        invoice_no = str(rec.get("Invoice", "")).strip()
        if not invoice_no:
            continue

        records.append({
            "Payment Date": payment_date,
            "Invoice": invoice_no,
            "Invoice Date": str(rec.get("Invoice Date", "")).strip(),
            "Invoice Type": str(rec.get("Invoice Type", "")).strip(),
            "Currency": str(rec.get("Currency", "")).strip(),
            "Amount": str(rec.get("Amount", "")).strip(),
            "Status": str(rec.get("Status", "")).strip(),
            "Payment Status": str(rec.get("Payment Status", "")).strip(),
            "Payment Amount": str(rec.get("Payment Amount", "")).strip(),
            "PO Number": str(rec.get("PO Number", "")).strip(),
            "Receipt": str(rec.get("Receipt", "")).strip(),
        })

    if not records:
        raise ValueError("Payment file me koi invoice/payment row nahi mili.")

    return pd.DataFrame(records, columns=wanted)

def indus_payment_key(row):
    """Stable duplicate key for one payment allocation line."""
    parts = [
        indus_clean_text(row.get("Payment Date")),
        indus_clean_text(row.get("Invoice")),
        indus_clean_text(row.get("Invoice Type")),
        indus_clean_text(row.get("Receipt")),
        f"{indus_number(row.get('Payment Amount')):.2f}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()



def indus_current_user_value():
    """Return JSON-safe current user text whether current_user is a function or value."""
    try:
        value = current_user() if callable(current_user) else current_user
    except Exception:
        value = ""
    if isinstance(value, dict):
        value = (
            value.get("username")
            or value.get("name")
            or value.get("email")
            or value.get("user")
            or ""
        )
    return str(value or "").strip() or "System"

def indus_import_payment_tsv(df, file_name):
    """
    Import actual day-wise payment allocation.

    CRITICAL RULE:
    Payment sirf tab save hoga jab uska ORIGINAL invoice already
    indus_invoices table me present ho.

    Standard row:
        Invoice itself must exist.

    Credit Memo / TDS row:
        '-TDS-CM-' ke pehle wala original invoice must exist.

    Isse 01-Jan-2026 se pehle ke old invoices ki later payments
    portal me accidentally enter nahi hongi.
    """
    inserted = 0
    skipped = 0
    skipped_invoice_not_found = 0
    touched_invoices = set()

    # Load all portal invoice numbers once for fast & reliable matching.
    existing_invoice_rows = indus_fetch_all("indus_invoices", "invoice_date", True)
    existing_invoice_map = {
        indus_clean_text(r.get("invoice_no")).upper(): r
        for r in existing_invoice_rows
        if indus_clean_text(r.get("invoice_no")) and not indus_is_blocked(r)
    }

    for _, row in df.iterrows():
        invoice_text = indus_clean_text(row.get("Invoice"))
        if not invoice_text:
            continue

        inv_type = indus_clean_text(row.get("Invoice Type"))
        payment_amount_raw = indus_number(row.get("Payment Amount"))
        payment_amount = abs(payment_amount_raw)

        # TDS/Credit Memo ko original Standard Invoice se map karo.
        original_invoice = (
            indus_original_invoice_from_credit_memo(invoice_text)
            if inv_type.lower() == "credit memo"
            else invoice_text
        )
        original_invoice = indus_clean_text(original_invoice)

        # --------------------------------------------------------
        # IMPORTANT: Invoice portal me nahi hai => payment SKIP.
        # --------------------------------------------------------
        matched_invoice = existing_invoice_map.get(original_invoice.upper())
        if not matched_invoice:
            skipped_invoice_not_found += 1
            continue

        # Prefer master invoice's PO/Receipt if payment row is blank.
        receipt = (
            indus_clean_text(row.get("Receipt"))
            or indus_clean_text(matched_invoice.get("receipt_no"))
        )
        po_no = (
            indus_clean_text(row.get("PO Number"))
            or indus_clean_text(matched_invoice.get("po_number"))
        )

        pdate = indus_date(row.get("Payment Date"))
        if pdate:
            if hasattr(pdate, "isoformat"):
                pdate_db = pdate.isoformat()
            else:
                pdate_db = str(pdate).strip()
        else:
            pdate_db = None

        pkey = indus_payment_key(row)

        # Duplicate payment allocation never insert twice.
        exists = (
            supabase.table("indus_payments")
            .select("id")
            .eq("workspace", ALLOWED_WORKSPACE)
            .eq("payment_key", pkey)
            .limit(1)
            .execute()
        )
        if exists.data:
            skipped += 1
            continue

        payload = {
            "workspace": ALLOWED_WORKSPACE,
            "invoice_no": original_invoice,
            "receipt_no": receipt or None,
            "po_number": po_no or None,
            "payment_date": pdate_db,
            "payment_amount": payment_amount,
            # Preserve actual payment-export invoice text.
            # TDS rows therefore retain the -TDS-CM- reference.
            "payment_reference": invoice_text,
            "utr_no": None,
            "payment_status": indus_clean_text(row.get("Payment Status")),
            "source_file_name": file_name,
            "payment_key": pkey,
            "created_by": indus_current_user_value(),
        }

        supabase.table("indus_payments").insert(payload).execute()
        inserted += 1
        touched_invoices.add(original_invoice)

    # Recalculate only invoices that genuinely exist in our portal.
    for invoice_no in touched_invoices:
        indus_recalculate_invoice_from_payments(invoice_no)

    return {
        "inserted": inserted,
        "skipped": skipped,
        "skipped_invoice_not_found": skipped_invoice_not_found,
        "touched": len(touched_invoices),
    }


def indus_recalculate_invoice_from_payments(invoice_no):
    """
    Final settlement:
      Standard payment rows => Invoice Payment
      Credit Memo payment rows => TDS Payment
      Total Settled = Invoice Payment + TDS Payment
      Outstanding = Invoice Amount - Total Settled
    """
    inv_rows = (
        supabase.table("indus_invoices")
        .select("*")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("invoice_no", invoice_no)
        .limit(1)
        .execute()
    ).data or []
    if not inv_rows:
        return

    inv = inv_rows[0]
    payments = (
        supabase.table("indus_payments")
        .select("*")
        .eq("workspace", ALLOWED_WORKSPACE)
        .eq("invoice_no", invoice_no)
        .execute()
    ).data or []

    invoice_payment = 0.0
    tds_payment = 0.0
    for p in payments:
        source_ref = indus_clean_text(p.get("payment_reference"))
        amt = abs(indus_number(p.get("payment_amount")))
        if "-TDS-CM-" in source_ref.upper():
            tds_payment += amt
        else:
            invoice_payment += amt

    invoice_amount = abs(indus_number(inv.get("invoice_amount")))
    total_settled = invoice_payment + tds_payment
    outstanding = max(0.0, invoice_amount - total_settled)

    if outstanding <= 0.01 and invoice_amount > 0:
        payment_status = "Paid"
    elif total_settled > 0:
        payment_status = "Partially Paid"
    else:
        payment_status = "Not Paid"

    supabase.table("indus_invoices").update({
        # Existing schema has one payment_received column; store CASH/Standard payment here.
        "payment_received": round(invoice_payment, 2),
        "outstanding_amount": round(outstanding, 2),
        "payment_status": payment_status,
        "last_updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_by": indus_current_user_value(),
    }).eq("id", inv["id"]).execute()


def indus_payment_breakup(invoice_no, payment_rows):
    """Return actual Standard payment and TDS payment separately."""
    cash = 0.0
    tds = 0.0
    for p in payment_rows:
        if indus_clean_text(p.get("invoice_no")) != indus_clean_text(invoice_no):
            continue
        amt = abs(indus_number(p.get("payment_amount")))
        source_ref = indus_clean_text(p.get("payment_reference"))
        if "-TDS-CM-" in source_ref.upper():
            tds += amt
        else:
            cash += amt
    return cash, tds

def indus_excel_bytes(df, sheet_name):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        ws = writer.sheets[sheet_name[:31]]
        from openpyxl.styles import Alignment, Font, PatternFill
        fill = PatternFill("solid", fgColor="312E81")
        for cell in ws[1]:
            cell.fill = fill
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 34)
    return output.getvalue()


def indus_search_df(df, search_text):
    if df.empty or not str(search_text).strip():
        return df
    terms = [t.lower() for t in str(search_text).split() if t.strip()]
    mask = pd.Series(True, index=df.index)
    joined = df.astype(str).apply(lambda r: " ".join(r.values).lower(), axis=1)
    for term in terms:
        mask &= joined.str.contains(re.escape(term), regex=True, na=False)
    return df[mask]


def indus_money_card(label, value, sub=""):
    st.markdown(
        f"""<div class="indus-card">
        <div class="label">{html.escape(label)}</div>
        <div class="value">{format_amount(value)}</div>
        <div class="sub">{html.escape(sub)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def indus_count_card(label, value, sub=""):
    st.markdown(
        f"""<div class="indus-card">
        <div class="label">{html.escape(label)}</div>
        <div class="value">{int(value):,}</div>
        <div class="sub">{html.escape(sub)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

if is_indus:
    if "indus_active_view" not in st.session_state:
        st.session_state.indus_active_view = "Invoice"

    st.markdown("""
    <style>
    .st-key-indus_view_nav div[data-testid="stHorizontalBlock"] {
        gap: 14px !important; flex-wrap: wrap !important;
    }
    .st-key-indus_view_nav button {
        font-size: 1.05rem !important; font-weight: 800 !important;
        min-height: 58px !important; padding: 14px 12px !important;
        border-radius: 13px !important; white-space: nowrap !important;
        transition: all .25s ease !important;
    }
    .st-key-indus_view_nav button p,
    .st-key-indus_view_nav button span,
    .st-key-indus_view_nav button div {
        display: inline-flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: auto !important;
        max-width: none !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: nowrap !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
    }
    .st-key-indus_view_nav button[kind="secondary"] {
        background:#fff !important; color:#475569 !important;
        border:1.5px solid rgba(15,23,42,.12) !important;
        box-shadow:0 3px 8px rgba(15,23,42,.08) !important;
    }
    .st-key-indus_view_nav button[kind="primary"] {
        background:linear-gradient(90deg,#3b82f6 0%,#8b5cf6 100%) !important;
        color:#fff !important; border:none !important;
        box-shadow:0 7px 18px rgba(79,70,229,.38) !important;
    }
    .indus-kpi-grid {
        display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr));
        gap:14px; margin:4px 0 22px;
    }
    .indus-kpi {
        position:relative; background:#fff; border-radius:16px; padding:18px 18px 16px;
        border:1px solid #e0e7ff; overflow:hidden;
        box-shadow:0 12px 28px -14px rgba(79,70,229,.35);
    }
    .indus-kpi:before {
        content:""; position:absolute; left:0; right:0; top:0; height:4px;
        background:linear-gradient(90deg,#6366f1,#8b5cf6,#ec4899);
    }
    .indus-kpi-label {font-size:.70rem;font-weight:900;letter-spacing:1.1px;text-transform:uppercase;color:#64748b;}
    .indus-kpi-value {font-size:1.48rem;font-weight:950;color:#0f172a;margin-top:8px;}
    .indus-kpi-foot {font-size:.74rem;color:#94a3b8;font-weight:650;margin-top:4px;}

    .indus-table-box {
        background:#fff; border:1px solid #e0e7ff; border-top:none;
        border-radius:0 0 18px 18px; overflow:auto; max-height:68vh;
        box-shadow:0 24px 48px -24px rgba(30,27,75,.38);
    }
    .indus-table {border-collapse:separate;border-spacing:0;width:100%;min-width:1450px;font-size:.82rem;}
    .indus-table thead th {
        position:sticky;top:0;z-index:4;
        background:linear-gradient(90deg,#312e81,#4338ca,#6d28d9);
        color:#fff;padding:13px 11px;text-align:left;white-space:nowrap;
        font-size:.69rem;font-weight:900;letter-spacing:.8px;text-transform:uppercase;
        border-right:1px solid rgba(255,255,255,.15);border-bottom:3px solid #f59e0b;
    }
    .indus-table tbody td {
        padding:10px 11px;border-right:1px solid #f1f5f9;border-bottom:1px solid #f1f5f9;
        color:#334155;white-space:nowrap;vertical-align:middle;
    }
    .indus-table tbody tr:nth-child(odd){background:#fff;}
    .indus-table tbody tr:nth-child(even){background:#fafaff;}
    .indus-table tbody tr:hover{background:#eef2ff;box-shadow:inset 4px 0 0 #6366f1;}
    .indus-chip {
        display:inline-block;font-family:ui-monospace,Consolas,monospace;
        background:#eef2ff;border:1px solid #c7d2fe;color:#4338ca;
        padding:3px 8px;border-radius:6px;font-weight:800;
    }
    .indus-money {font-weight:900;color:#334155;font-variant-numeric:tabular-nums;}
    .indus-money.green{color:#059669}.indus-money.red{color:#dc2626}.indus-money.amber{color:#d97706}
    .indus-status {
        display:inline-flex;padding:4px 10px;border-radius:999px;font-size:.69rem;
        font-weight:900;letter-spacing:.35px;text-transform:uppercase;border:1px solid;
    }
    .indus-status.green{background:#dcfce7;color:#15803d;border-color:#bbf7d0}
    .indus-status.red{background:#fee2e2;color:#b91c1c;border-color:#fecaca}
    .indus-status.amber{background:#fef3c7;color:#b45309;border-color:#fde68a}
    .indus-status.blue{background:#dbeafe;color:#1d4ed8;border-color:#bfdbfe}
    .indus-foot {
        display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;
        padding:14px 20px;background:linear-gradient(90deg,#f5f3ff,#eef2ff);
        border:1px solid #e0e7ff;border-top:2px solid #c7d2fe;border-radius:0 0 18px 18px;
        font-weight:900;color:#312e81;margin-bottom:18px;
    }
    </style>
    """, unsafe_allow_html=True)

    def _indus_status_html(v):
        s = str(v or "").strip()
        sl = s.lower()
        cls = "green" if sl in ("paid","approved","processed","active") else (
            "red" if sl in ("rejected","cancelled","not paid") else (
                "amber" if "partial" in sl or "pending" in sl or "hold" in sl else "blue"
            )
        )
        return f"<span class='indus-status {cls}'>{html.escape(s or '-')}</span>"

    def _indus_money_html(v, cls=""):
        return f"<span class='indus-money {cls}'>₹ {indus_number(v):,.2f}</span>"

    def _indus_chip_html(v):
        return f"<span class='indus-chip'>{html.escape(str(v or '-'))}</span>"

    def _indus_table(title, subtitle, badge, df, money_cols=None, status_cols=None, chip_cols=None):
        money_cols = set(money_cols or [])
        status_cols = set(status_cols or [])
        chip_cols = set(chip_cols or [])
        st.markdown(
            f"<div class='slux-head-bar'><div class='slux-title'>{html.escape(title)}"
            f"<span>{html.escape(subtitle)}</span></div>"
            f"<div class='slux-badge'>{html.escape(str(badge))}</div></div>",
            unsafe_allow_html=True,
        )
        if df is None or df.empty:
            st.markdown("<div class='slux-empty'><div>🗂️</div>No records found</div>", unsafe_allow_html=True)
            return
        parts = ["<div class='indus-table-box'><table class='indus-table'><thead><tr>"]
        for col in df.columns:
            parts.append(f"<th>{html.escape(str(col))}</th>")
        parts.append("</tr></thead><tbody>")
        for _, row in df.iterrows():
            parts.append("<tr>")
            for col in df.columns:
                val = row.get(col, "")
                if col in money_cols:
                    cls = "red" if col in ("Outstanding","Due") and indus_number(val) > 0 else (
                        "green" if col in ("Payment Received","Balance Advance") else (
                            "amber" if col in ("TDS","TDS Amount") else ""
                        )
                    )
                    cell_html = _indus_money_html(val, cls)
                elif col in status_cols:
                    cell_html = _indus_status_html(val)
                elif col in chip_cols:
                    cell_html = _indus_chip_html(val)
                else:
                    cell_html = html.escape(str(val if val not in (None, "") else "-"))
                parts.append(f"<td>{cell_html}</td>")
            parts.append("</tr>")
        parts.append("</tbody></table></div>")
        st.markdown("".join(parts), unsafe_allow_html=True)
        st.markdown(
            f"<div class='indus-foot'><span>{len(df):,} record(s)</span><span>{html.escape(str(badge))}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """<div class="bank-title">
            <h1>🏢 INDUS RECEIVABLES</h1>
            <p>Invoice, Payment, Prepayment and TDS / Credit Note Management</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Latest INDUS business date — clearly visible before navigation.
    render_last_data_date_card(get_indus_last_data_date(), "INDUS")

    indus_views = [
        ("Invoice", "Invoice", ":material/description:"),
        ("Blocked ERS", "Blocked ERS", ":material/block:"),
        ("Payments", "Payments", ":material/payments:"),
        ("Prepayment", "Prepayment", ":material/account_balance_wallet:"),
        ("Credit Note", "Credit Note", ":material/receipt_long:"),
    ]
    with st.container(key="indus_view_nav"):
        nav_cols = st.columns(len(indus_views))
        for col, (view_key, view_label, view_icon) in zip(nav_cols, indus_views):
            with col:
                active = st.session_state.indus_active_view == view_key
                if st.button(
                    view_label,
                    key=f"indus_view_{view_key}",
                    type="primary" if active else "secondary",
                    icon=view_icon,
                    use_container_width=True,
                ):
                    st.session_state.indus_active_view = view_key
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Upload is kept on the Invoice page only.
    if st.session_state.indus_active_view == "Invoice":
        upload_col, refresh_col = st.columns([5, 1.2])
        with upload_col:
            indus_upload = st.file_uploader(
                "⬆️ Upload Latest Indus TSV Export",
                type=["tsv", "txt"],
                key="indus_receivable_tsv_upload",
                help="Same export repeat upload kar sakte hain. Receipt Number ke basis par Standard invoice update hoga.",
            )
        with refresh_col:
            st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", key="indus_refresh", use_container_width=True):
                st.rerun()

        if indus_upload is not None:
            try:
                indus_preview = indus_read_tsv(indus_upload.getvalue())
                type_counts = indus_preview["Type"].value_counts().to_dict()
                st.info(
                    f"Rows: {len(indus_preview):,} | Standard: {type_counts.get('Standard',0):,} | "
                    f"Credit Memo: {type_counts.get('Credit Memo',0):,} | "
                    f"Debit Memo: {type_counts.get('Debit Memo',0):,} | "
                    f"Prepayment: {type_counts.get('Prepayment',0):,}"
                )
                if st.button("🚀 Import / Update Indus Data", key="indus_import_update",
                             type="primary", use_container_width=True):
                    with st.spinner("Indus data import/update ho raha hai..."):
                        result = indus_import_tsv(indus_preview, indus_upload.name)
                    st.success(
                        f"Import complete ✅ Standard {result['standard']:,} | Credit Memo {result['credit']:,} | "
                        f"Debit Memo {result['debit']:,} | Prepayment {result['prepayment']:,} | "
                        f"New {result['inserted']:,} | Updated {result['updated']:,}"
                    )
                    st.rerun()
            except Exception as exc:
                st.error(f"Indus TSV error: {exc}")

    try:
        invoice_rows = indus_fetch_all("indus_invoices", "invoice_date", True)
        payment_rows = indus_fetch_all("indus_payments", "payment_date", True)
        credit_rows = indus_fetch_all("indus_credit_memos", "credit_memo_date", True)
        prepayment_rows = indus_fetch_all("indus_prepayments", "prepayment_date", True)
        debit_rows = indus_fetch_all("indus_debit_memos", "debit_memo_date", True)
    except Exception as exc:
        st.error(f"Indus tables load nahi hui: {exc}")
        invoice_rows, payment_rows, credit_rows, prepayment_rows, debit_rows = [], [], [], [], []

    # Blocked ERS/Invoice must never enter KPI/payment/outstanding calculations.
    blocked_invoice_rows = [r for r in invoice_rows if indus_is_blocked(r)]
    active_invoice_rows = [r for r in invoice_rows if not indus_is_blocked(r)]

    invoice_total = sum(indus_number(r.get("invoice_amount")) for r in active_invoice_rows)
    tds_total = sum(indus_number(r.get("tds_amount")) for r in active_invoice_rows)
    net_total = max(0.0, invoice_total - tds_total)
    invoice_payment_total = 0.0
    tds_payment_total = 0.0
    for _inv in active_invoice_rows:
        _cash, _tdsp = indus_payment_breakup(_inv.get("invoice_no"), payment_rows)
        invoice_payment_total += _cash
        tds_payment_total += _tdsp
    received_total = invoice_payment_total + tds_payment_total
    outstanding_total = sum(
        max(0.0, abs(indus_number(r.get("invoice_amount"))) - sum(indus_payment_breakup(r.get("invoice_no"), payment_rows)))
        for r in active_invoice_rows
    )
    advance_total = sum(indus_number(r.get("balance_amount")) for r in prepayment_rows)

    st.markdown(
        "<div class='indus-kpi-grid'>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>Total Invoice</div><div class='indus-kpi-value'>₹ {invoice_total:,.2f}</div><div class='indus-kpi-foot'>{len(invoice_rows):,} invoices</div></div>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>TDS</div><div class='indus-kpi-value'>₹ {tds_total:,.2f}</div><div class='indus-kpi-foot'>Credit Memo mapped</div></div>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>Net Receivable</div><div class='indus-kpi-value'>₹ {net_total:,.2f}</div><div class='indus-kpi-foot'>Invoice - TDS</div></div>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>Payment Received</div><div class='indus-kpi-value'>₹ {received_total:,.2f}</div><div class='indus-kpi-foot'>Settled receipts</div></div>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>Outstanding</div><div class='indus-kpi-value'>₹ {outstanding_total:,.2f}</div><div class='indus-kpi-foot'>Current due</div></div>"
        f"<div class='indus-kpi'><div class='indus-kpi-label'>Advance Balance</div><div class='indus-kpi-value'>₹ {advance_total:,.2f}</div><div class='indus-kpi-foot'>PO prepayment</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    today = datetime.date.today()

    if st.session_state.indus_active_view == "Invoice":
        data = [{
            "Receipt No": r.get("receipt_no") or "",
            "ERS No": r.get("ers_no") or "",
            "Invoice No": r.get("invoice_no") or "",
            "Invoice Date": format_date(r.get("invoice_date")),
            "PO Number": r.get("po_number") or "",
            "Invoice Amount": indus_number(r.get("invoice_amount")),
            "TDS": indus_number(r.get("tds_amount")),
            "Net Receivable": max(0.0, indus_number(r.get("invoice_amount")) - indus_number(r.get("tds_amount"))),
            "Invoice Payment": indus_payment_breakup(r.get("invoice_no"), payment_rows)[0],
            "TDS Payment": indus_payment_breakup(r.get("invoice_no"), payment_rows)[1],
            "Total Settled": sum(indus_payment_breakup(r.get("invoice_no"), payment_rows)),
            "Outstanding": max(
                0.0,
                abs(indus_number(r.get("invoice_amount"))) -
                sum(indus_payment_breakup(r.get("invoice_no"), payment_rows))
            ),
            "Payment Status": r.get("payment_status") or "",
            "Invoice Status": r.get("invoice_status") or "",
            "Due Date": format_date(r.get("due_date")),
            "Payment Ref": r.get("payment_reference") or "",
            "UTR": r.get("payment_utr") or "",
        } for r in active_invoice_rows]
        df = pd.DataFrame(data)
        c1, c2, c3 = st.columns([3.6,1.5,1.5])
        with c1:
            q = st.text_input("Search", placeholder="🔍 Invoice / ERS / Receipt / PO / UTR / Status...",
                              key="indus_invoice_search", label_visibility="collapsed")
        with c2:
            statuses = ["All"] + sorted({str(r.get("payment_status") or "") for r in active_invoice_rows if r.get("payment_status")})
            sf = st.selectbox("Status", statuses, key="indus_invoice_status_filter", label_visibility="collapsed")
        fdf = indus_search_df(df, q)
        if sf != "All" and not fdf.empty:
            fdf = fdf[fdf["Payment Status"] == sf]
        with c3:
            st.download_button("📥 Download Excel", indus_excel_bytes(fdf, "Invoices"),
                               f"Indus_Invoices_{today:%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="indus_invoice_download", use_container_width=True)

        st.markdown("#### 🚫 Block ERS / Invoice")
        block_candidates = {
            f"{(r.get('ers_no') or r.get('invoice_no') or '-') } | Receipt {r.get('receipt_no') or '-'} | ₹ {indus_number(r.get('invoice_amount')):,.2f}": r
            for r in active_invoice_rows
        }
        if block_candidates:
            bc1, bc2, bc3 = st.columns([3.2, 3.2, 1.2])
            with bc1:
                selected_block_label = st.selectbox(
                    "Select ERS / Invoice",
                    ["-- Select --"] + list(block_candidates.keys()),
                    key="indus_block_select",
                )
            with bc2:
                block_reason = st.text_input(
                    "Block Remark",
                    placeholder="Reason for blocking...",
                    key="indus_block_reason",
                )
            with bc3:
                st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
                if st.button("🚫 Block", key="indus_block_btn", type="primary", use_container_width=True):
                    if selected_block_label == "-- Select --":
                        st.warning("ERS / Invoice select karo.")
                    else:
                        rec = block_candidates[selected_block_label]
                        indus_block_invoice(rec.get("id"), block_reason)
                        st.success("Blocked. Ye record ab financial calculation me include nahi hoga.")
                        st.rerun()

        _indus_table("📄 Invoice Register", "Receipt based ERS → Invoice tracking",
                     f"Outstanding ₹ {fdf['Outstanding'].sum():,.2f}" if not fdf.empty else "₹ 0.00",
                     fdf,
                     money_cols={"Invoice Amount","TDS","Net Receivable","Invoice Payment","TDS Payment","Total Settled","Outstanding"},
                     status_cols={"Payment Status","Invoice Status"},
                     chip_cols={"Receipt No","ERS No","Invoice No","PO Number","UTR"})

    elif st.session_state.indus_active_view == "Blocked ERS":
        st.markdown(
            """<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:16px;
            padding:14px 18px;margin-bottom:16px;color:#9a3412;font-weight:800;">
            🚫 Blocked records are completely excluded from Invoice Total, TDS, Payment,
            Settlement and Outstanding calculations.
            </div>""",
            unsafe_allow_html=True,
        )

        if blocked_invoice_rows:
            for rec in blocked_invoice_rows:
                c1, c2, c3, c4, c5 = st.columns([2.1, 2.2, 1.5, 3.0, 1.1])
                c1.markdown(f"**{rec.get('ers_no') or '-'}**")
                c2.markdown(f"**{rec.get('invoice_no') or '-'}**")
                c3.markdown(f"₹ {indus_number(rec.get('invoice_amount')):,.2f}")
                c4.markdown(str(rec.get("block_remark") or "-"))
                with c5:
                    if st.button("Unblock", key=f"indus_unblock_{rec.get('id')}", use_container_width=True):
                        indus_unblock_invoice(rec.get("id"))
                        st.success("Record unblocked.")
                        st.rerun()
        else:
            st.info("Abhi koi Blocked ERS / Invoice nahi hai.")

    elif st.session_state.indus_active_view == "Payments":
        st.markdown(
            """<div style="background:#fff;border:1px solid #e0e7ff;border-radius:16px;
            padding:16px 18px;margin-bottom:16px;box-shadow:0 8px 22px rgba(15,23,42,.07);">
            <b style="color:#312e81;font-size:1rem;">💰 Daily Payment Export Upload</b><br>
            <span style="color:#64748b;font-size:.84rem;">
            Standard row = Invoice Payment &nbsp;•&nbsp; Credit Memo row = TDS Payment
            &nbsp;•&nbsp; Duplicate payment rows automatically skipped
            </span></div>""",
            unsafe_allow_html=True,
        )

        up_col, refresh_col = st.columns([5, 1.2])
        with up_col:
            payment_upload = st.file_uploader(
                "Upload Indus Payment TSV",
                type=["tsv", "txt"],
                key="indus_payment_tsv_upload",
            )
        with refresh_col:
            st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
            if st.button("Refresh", key="indus_payment_refresh", use_container_width=True):
                st.rerun()

        if payment_upload is not None:
            try:
                pay_preview = indus_read_payment_tsv(payment_upload.getvalue())
                std_count = int((pay_preview["Invoice Type"].str.lower() == "standard").sum())
                tds_count = int((pay_preview["Invoice Type"].str.lower() == "credit memo").sum())
                pay_total = pay_preview["Payment Amount"].apply(indus_number).abs().sum()
                st.info(
                    f"Rows: {len(pay_preview):,} | Invoice Payment rows: {std_count:,} | "
                    f"TDS Payment rows: {tds_count:,} | Payment allocation: ₹ {pay_total:,.2f}"
                )
                if st.button(
                    "Import / Update Payments",
                    key="indus_payment_import",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("Payment data import ho raha hai..."):
                        result = indus_import_payment_tsv(pay_preview, payment_upload.name)
                    st.success(
                        f"Payment import complete ✅ New: {result['inserted']:,} | "
                        f"Duplicate skipped: {result['skipped']:,} | "
                        f"Invoice not in portal skipped: {result['skipped_invoice_not_found']:,} | "
                        f"Invoices recalculated: {result['touched']:,}"
                    )
                    st.rerun()
            except Exception as exc:
                st.error(f"Payment TSV error: {exc}")

        # Reload after possible upload.
        payment_rows = indus_fetch_all("indus_payments", "payment_date", True)

        data = []
        for p in payment_rows:
            source_invoice = indus_clean_text(p.get("payment_reference"))
            is_tds = "-TDS-CM-" in source_invoice.upper()
            original_invoice = indus_clean_text(p.get("invoice_no"))
            inv = next(
                (x for x in active_invoice_rows if indus_clean_text(x.get("invoice_no")) == original_invoice),
                {},
            )
            data.append({
                "Payment Date": format_date(p.get("payment_date")),
                "Invoice": source_invoice or original_invoice,
                "Invoice Date": format_date(inv.get("invoice_date")),
                "Invoice Type": "Credit Memo" if is_tds else "Standard",
                "Currency": "INR",
                "Amount": indus_number(inv.get("tds_amount")) if is_tds else indus_number(inv.get("invoice_amount")),
                "Status": inv.get("invoice_status") or "",
                "Payment Status": p.get("payment_status") or "",
                "Payment Amount": indus_number(p.get("payment_amount")),
                "PO Number": p.get("po_number") or inv.get("po_number") or "",
                "Receipt": p.get("receipt_no") or inv.get("receipt_no") or "",
            })

        df = pd.DataFrame(data)

        # ------------------------------------------------------------
        # Invoice-wise grouping:
        # Standard Invoice first, then SAME invoice ka TDS Credit Memo.
        # Example:
        # VIS/26-27/1400
        # VIS/26-27/1400-TDS-CM-xxxxx
        # ------------------------------------------------------------
        if not df.empty:
            def _payment_parent_invoice(invoice_value):
                invoice_value = str(invoice_value or "").strip()
                upper_value = invoice_value.upper()
                marker = "-TDS-CM-"
                if marker in upper_value:
                    marker_pos = upper_value.find(marker)
                    return invoice_value[:marker_pos]
                return invoice_value

            df["_parent_invoice"] = df["Invoice"].apply(_payment_parent_invoice)
            df["_type_order"] = (
                df["Invoice Type"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({"standard": 0, "credit memo": 1})
                .fillna(2)
            )

            # Payment Date latest first; within each date:
            # parent invoice -> Standard -> Credit Memo/TDS.
            df["_payment_date_sort"] = pd.to_datetime(
                df["Payment Date"], errors="coerce", dayfirst=True
            )

            df = (
                df.sort_values(
                    by=["_payment_date_sort", "_parent_invoice", "_type_order", "Invoice"],
                    ascending=[False, True, True, True],
                    kind="stable",
                )
                .drop(columns=["_parent_invoice", "_type_order", "_payment_date_sort"])
                .reset_index(drop=True)
            )

        c1, c2 = st.columns([5, 1.6])
        with c1:
            q = st.text_input(
                "Search",
                placeholder="Search Payment Date / Invoice / PO / Receipt / Status...",
                key="indus_payment_search",
                label_visibility="collapsed",
            )
        fdf = indus_search_df(df, q)
        with c2:
            st.download_button(
                "Download Excel",
                indus_excel_bytes(fdf, "Payments"),
                f"Indus_Payments_{today:%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="indus_payment_download",
                use_container_width=True,
            )

        _indus_table(
            "Payment Register",
            "Actual day-wise Indus payment allocation",
            f"Payment ₹ {fdf['Payment Amount'].sum():,.2f}" if not fdf.empty else "₹ 0.00",
            fdf,
            money_cols={"Amount", "Payment Amount"},
            status_cols={"Status", "Payment Status"},
            chip_cols={"Invoice", "PO Number", "Receipt"},
        )

    elif st.session_state.indus_active_view == "Prepayment":
        data = [{
            "Prepayment Ref":r.get("prepayment_ref") or "",
            "PO Number":r.get("po_number") or "",
            "Date":format_date(r.get("prepayment_date")),
            "Advance Amount":indus_number(r.get("advance_amount")),
            "Adjusted Amount":indus_number(r.get("adjusted_amount")),
            "Balance Advance":indus_number(r.get("balance_amount")),
            "Status":r.get("status") or "",
        } for r in prepayment_rows]
        df=pd.DataFrame(data)
        c1,c2=st.columns([5,1.6])
        with c1:
            q=st.text_input("Search",placeholder="🔍 PO Number / Advance Ref / Status...",
                            key="indus_prepayment_search",label_visibility="collapsed")
        fdf=indus_search_df(df,q)
        with c2:
            st.download_button("📥 Download Excel",indus_excel_bytes(fdf,"Prepayment"),
                               f"Indus_Prepayment_{today:%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="indus_prepayment_download",use_container_width=True)
        _indus_table("💵 Prepayment / Advance Register","PO wise advance tracking",
                     f"Balance ₹ {fdf['Balance Advance'].sum():,.2f}" if not fdf.empty else "₹ 0.00",
                     fdf,money_cols={"Advance Amount","Adjusted Amount","Balance Advance"},
                     status_cols={"Status"},chip_cols={"Prepayment Ref","PO Number"})

    elif st.session_state.indus_active_view == "Credit Note":
        credit_mode = st.radio("Credit Note Type",["TDS Credit Memo","Debit Memo"],
                               horizontal=True,key="indus_credit_mode")
        if credit_mode == "TDS Credit Memo":
            lookup={str(r.get("invoice_no") or ""):r for r in invoice_rows}
            data=[]
            for r in credit_rows:
                original=r.get("original_invoice_no") or ""
                inv=lookup.get(original,{})
                inv_amt=indus_number(inv.get("invoice_amount"))
                tds=indus_number(r.get("tds_amount"))
                data.append({
                    "Credit Memo No":r.get("credit_memo_no") or "",
                    "Original Invoice":original,
                    "Date":format_date(r.get("credit_memo_date")),
                    "Invoice Amount":inv_amt,
                    "TDS Amount":tds,
                    "TDS %":round((tds/inv_amt*100),3) if inv_amt else 0,
                    "Status":r.get("status") or "",
                })
            df=pd.DataFrame(data)
            c1,c2=st.columns([5,1.6])
            with c1:
                q=st.text_input("Search",placeholder="🔍 Credit Memo / Original Invoice / Status...",
                                key="indus_credit_search",label_visibility="collapsed")
            fdf=indus_search_df(df,q)
            with c2:
                st.download_button("📥 Download Excel",indus_excel_bytes(fdf,"TDS Credit Memo"),
                                   f"Indus_TDS_Credit_Memo_{today:%Y%m%d}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="indus_credit_download",use_container_width=True)
            _indus_table("🧾 TDS Credit Memo","Invoice number based automatic mapping",
                         f"TDS ₹ {fdf['TDS Amount'].sum():,.2f}" if not fdf.empty else "₹ 0.00",
                         fdf,money_cols={"Invoice Amount","TDS Amount"},status_cols={"Status"},
                         chip_cols={"Credit Memo No","Original Invoice"})
        else:
            data=[{
                "Debit Memo No":r.get("debit_memo_no") or "",
                "Date":format_date(r.get("debit_memo_date")),
                "Amount":indus_number(r.get("amount")),
                "Due":indus_number(r.get("due_amount")),
                "Status":r.get("status") or "",
                "Description":r.get("description") or "",
            } for r in debit_rows]
            df=pd.DataFrame(data)
            c1,c2=st.columns([5,1.6])
            with c1:
                q=st.text_input("Search",placeholder="🔍 Debit Memo / Status / Description...",
                                key="indus_debit_search",label_visibility="collapsed")
            fdf=indus_search_df(df,q)
            with c2:
                st.download_button("📥 Download Excel",indus_excel_bytes(fdf,"Debit Memo"),
                                   f"Indus_Debit_Memo_{today:%Y%m%d}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="indus_debit_download",use_container_width=True)
            _indus_table("🧾 Debit Memo","separate debit adjustment register",
                         f"Amount ₹ {fdf['Amount'].sum():,.2f}" if not fdf.empty else "₹ 0.00",
                         fdf,money_cols={"Amount","Due"},status_cols={"Status"},chip_cols={"Debit Memo No"})
