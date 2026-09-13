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


st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%); }
    .bank-title {
        color: white; padding: 18px 22px; border-radius: 14px;
        background: linear-gradient(90deg, #1e3a8a, #4f46e5, #7c3aed);
        box-shadow: 0 8px 22px rgba(49,46,129,.22); margin-bottom: 16px;
    }
    .bank-title h1 { color: white !important; margin: 0; font-size: 2rem; }
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


def approve_transaction(transaction_id: int, assignment: str):
    mode, pay_to = parse_assignment(assignment)
    return supabase.rpc(
        "approve_bank_transaction",
        {
            "p_transaction_id": int(transaction_id),
            "p_mode": mode,
            "p_pay_to": pay_to,
            "p_approved_by": current_user(),
        },
    ).execute()


def move_to_suspense(transaction_id: int):
    return supabase.rpc(
        "mark_bank_transaction_suspense",
        {
            "p_transaction_id": int(transaction_id),
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


def render_statement_preview(preview_df: pd.DataFrame):
    rows_html = []
    for _, row in preview_df.iterrows():
        rows_html.append(
            "<tr>"
            f"<td class='p-date'>{html.escape(str(row['Date']))}</td>"
            f"<td class='p-narration'>{html.escape(str(row['Narration']))}</td>"
            f"<td class='p-ref'>{html.escape(str(row['Chq./Ref.No.']))}</td>"
            f"<td class='p-amount'>{html.escape(str(row['Withdrawal Amt.']))}</td>"
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
        "<th class='p-date'>Date</th>"
        "<th class='p-narration'>Narration</th>"
        "<th class='p-ref'>Chq./Ref.No.</th>"
        "<th class='p-amount'>Withdrawal</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_header(show_assignment=True):
    widths = [0.9, 5.1, 1.5, 1.1, 2.3, 1.0] if show_assignment else [0.9, 5.4, 1.5, 1.1, 2.3]
    labels = ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Team/Vendor", "Action"] if show_assignment else ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Booked To"]
    columns = st.columns(widths)
    for column, label in zip(columns, labels):
        column.markdown(f"<div class='table-head'>{label}</div>", unsafe_allow_html=True)


def render_pending(records, account_key, view_status="Pending"):
    if not records:
        empty_message = "Suspense में कोई transaction नहीं है।" if view_status == "Suspense" else "सभी imported transactions process हो चुके हैं।"
        st.success(empty_message)
        return

    options = assignment_options()
    if not options:
        st.error("Active Team/Vendor master खाली है।")
        return

    page_count = max(1, math.ceil(len(records) / PAGE_SIZE))
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=page_count,
        value=1,
        step=1,
        key=f"pending_page_{view_status}_{account_key}",
    )
    start = (int(page) - 1) * PAGE_SIZE
    visible = records[start : start + PAGE_SIZE]

    st.caption(f"{view_status}: {len(records)} | Page {int(page)} of {page_count}")
    render_header(show_assignment=True)

    for row in visible:
        row_id = int(row["id"])
        cols = st.columns([0.9, 5.1, 1.5, 1.1, 2.3, 1.0])
        cols[0].markdown(f"<div class='txn-row'><b>{format_date(row.get('transaction_date'))}</b></div>", unsafe_allow_html=True)
        safe_narration = html.escape(str(row.get("narration", "")))
        safe_reference = html.escape(str(row.get("reference_no", "")))
        cols[1].markdown(f"<div class='txn-row narration'>{safe_narration}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='txn-row narration'>{safe_reference}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='txn-row amount'>{format_amount(row.get('withdrawal_amount'))}</div>", unsafe_allow_html=True)
        assignment = cols[4].selectbox(
            "Team/Vendor",
            options=options,
            key=f"assignment_{view_status}_{account_key}_{row_id}",
            label_visibility="collapsed",
        )
        expense_category = None
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
                    move_to_suspense(row_id)
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


def render_approved(records, account_key):
    if not records:
        st.info("अभी कोई approved transaction नहीं है।")
        return

    page_count = max(1, math.ceil(len(records) / PAGE_SIZE))
    page = st.number_input(
        "Approved Page",
        min_value=1,
        max_value=page_count,
        value=1,
        step=1,
        key=f"approved_page_{account_key}",
    )
    start = (int(page) - 1) * PAGE_SIZE
    visible = records[start : start + PAGE_SIZE]

    st.caption(f"Approved: {len(records)} | Page {int(page)} of {page_count}")
    render_header(show_assignment=False)
    for row in visible:
        cols = st.columns([0.9, 5.4, 1.5, 1.1, 2.3])
        cols[0].markdown(f"<div class='txn-row'><b>{format_date(row.get('transaction_date'))}</b></div>", unsafe_allow_html=True)
        safe_narration = html.escape(str(row.get("narration", "")))
        safe_reference = html.escape(str(row.get("reference_no", "")))
        cols[1].markdown(f"<div class='txn-row narration'>{safe_narration}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='txn-row narration'>{safe_reference}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='txn-row amount'>{format_amount(row.get('withdrawal_amount'))}</div>", unsafe_allow_html=True)
        booked_to = html.escape(f"{row.get('assignment_mode', '')}: {row.get('pay_to', '')}")
        cols[4].markdown(f"<div class='txn-row approved'>{booked_to}</div>", unsafe_allow_html=True)


def render_other_expenses(records, account_key):
    if not records:
        st.info("अभी कोई Other Expense transaction नहीं है।")
        return

    st.caption(f"Other Expenses: {len(records)}")
    columns = st.columns([0.9, 5.0, 1.5, 1.1, 2.0, 1.2])
    for column, label in zip(
        columns,
        ["Date", "Narration", "Chq./Ref.No.", "Withdrawal", "Expense Category", "Action"],
    ):
        column.markdown(f"<div class='table-head'>{label}</div>", unsafe_allow_html=True)

    for row in records:
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


st.markdown(
    """
    <div class="bank-title">
        <h1>Banking</h1>
        <p>Statement upload, Team/Vendor allocation and payment approval</p>
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

tabs = st.tabs(list(ACCOUNTS.keys()))

for tab, (account_label, account) in zip(tabs, ACCOUNTS.items()):
    with tab:
        st.subheader(account_label)
        st.markdown("#### Step 1: Statement Upload")
        uploaded = st.file_uploader(
            "Upload bank statement (.xls or .xlsx)",
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
                preview_records = parse_statement(
                    file_bytes,
                    selected_sheet,
                    account_label,
                    uploaded.name,
                )
                st.info(f"Preview: {len(preview_records)} withdrawal transactions मिले। Deposit और Closing Balance शामिल नहीं हैं।")

                preview_df = pd.DataFrame(preview_records)[
                    ["transaction_date", "narration", "reference_no", "withdrawal_amount"]
                ].sort_values("transaction_date", ascending=False)
                preview_df.columns = ["Date", "Narration", "Chq./Ref.No.", "Withdrawal Amt."]
                preview_df["Date"] = pd.to_datetime(preview_df["Date"]).dt.strftime("%d-%b-%Y")
                preview_df["Withdrawal Amt."] = preview_df["Withdrawal Amt."].apply(format_amount)
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

        pending_tab, approved_tab, suspense_tab, other_expense_tab = st.tabs(
            ["Assign & Approve", "Approved Payments", "Suspense", "Other Expenses"]
        )
        with pending_tab:
            try:
                render_pending(fetch_transactions(account["key"], "Pending"), account["key"], "Pending")
            except Exception as exc:
                st.warning(f"Supabase connect नहीं हुआ, इसलिए Team/Vendor dropdown अभी नहीं दिख सकता: {exc}")
        with approved_tab:
            try:
                render_approved(fetch_transactions(account["key"], "Approved"), account["key"])
            except Exception as exc:
                st.warning(f"Approved payments load नहीं हुए: {exc}")
        with suspense_tab:
            try:
                render_pending(fetch_transactions(account["key"], "Suspense"), account["key"], "Suspense")
            except Exception as exc:
                st.warning(f"Suspense transactions load नहीं हुए: {exc}")
        with other_expense_tab:
            try:
                render_other_expenses(
                    fetch_transactions(account["key"], "Other Expense"),
                    account["key"],
                )
            except Exception as exc:
                st.warning(f"Other Expenses load नहीं हुए: {exc}")
