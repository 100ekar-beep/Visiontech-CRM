
# WHIZ KEY IOT PRIVATE LIMITED
# Streamlit Consolidated Invoice & Payment Module
# Filename: wizhkey_module.py

import io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st
from fpdf import FPDF


WK_COMPANY = {
    "name": "WHIZ KEY IOT PRIVATE LIMITED",
    "gstin": "27AADCW7297D1ZY",
    "pan": "AADCW7297D",
    "address": (
        "Office No. 1, S No. 23, 24, 55, Near Vikas Mitra Mandal, "
        "Karve Nagar, Pune, Maharashtra - 411052"
    ),
}

WK_BUYER = {
    "name": "Bhagyashree Enterprises",
    "gstin": "27ABWPV2922M1ZQ",
    "address": (
        "S. No. 66, Sai Pritam Nagar, Rahtani, "
        "BLD-A Flat-7, Pune, Maharashtra - 411017"
    ),
}


def money(value):
    try:
        return Decimal(
            str(value if value is not None else 0).replace(",", "")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def wk_calc(basic):
    basic = money(basic)
    discount = money(basic * Decimal("0.02"))
    taxable = basic - discount
    cgst = money(taxable * Decimal("0.09"))
    sgst = money(taxable * Decimal("0.09"))

    return {
        "original_basic": float(basic),
        "discount_amount": float(discount),
        "taxable_amount": float(taxable),
        "cgst": float(cgst),
        "sgst": float(sgst),
        "total_amount": float(taxable + cgst + sgst),
    }


def wk_pick(row, *names):
    normalized = {
        str(k).lower().replace(" ", "").replace("_", ""): v
        for k, v in row.items()
    }
    for name in names:
        key = name.lower().replace(" ", "").replace("_", "")
        value = normalized.get(key)
        if value is not None and str(value).strip() not in (
            "", "None", "null", "nan"
        ):
            return value
    return None


def wk_date(value):
    try:
        if value:
            return pd.to_datetime(value).date().isoformat()
    except Exception:
        pass
    return None


def wk_fetch_all(db, table, workspace=None):
    result = []
    start = 0

    while True:
        query = db.table(table).select("*").range(start, start + 999)

        if workspace:
            query = query.eq("workspace", workspace)

        chunk = query.execute().data or []
        result.extend(chunk)

        if len(chunk) < 1000:
            break

        start += 1000

    return result


def wk_source_rows(db):
    records = wk_fetch_all(
        db, "invoice_management", "BHAGYASHREE"
    )

    if not records:
        return [], "No BHAGYASHREE invoice records found."

    sites = wk_fetch_all(db, "site_data", "BHAGYASHREE")

    by_project = {
        str(wk_pick(s, "Project ID", "project_id")): s
        for s in sites
    }
    by_site = {
        str(wk_pick(s, "Site ID", "site_id")): s
        for s in sites
    }

    output = []
    skipped = 0

    for row in records:
        invoice_no = wk_pick(
            row,
            "invoice_no",
            "invoice_number",
            "Invoice No",
            "Tally Invoice Number",
        )

        if not invoice_no:
            skipped += 1
            continue

        status = str(
            wk_pick(row, "invoice_status", "status") or ""
        ).upper()

        if "CANCEL" in status or "DRAFT" in status:
            continue

        project_id = str(
            wk_pick(row, "project_id", "Project ID") or ""
        )
        site_id = str(
            wk_pick(row, "site_id", "Site ID") or ""
        )

        site = (
            by_project.get(project_id)
            or by_site.get(site_id)
            or {}
        )

        project_id = project_id or str(
            wk_pick(site, "Project ID") or ""
        )
        site_id = site_id or str(
            wk_pick(site, "Site ID") or ""
        )

        site_name = str(
            wk_pick(row, "site_name", "Site Name")
            or wk_pick(site, "Site Name")
            or ""
        )

        basic = wk_pick(
            row,
            "basic_amount",
            "basic amount",
            "taxable_amount",
            "taxable value",
            "basic",
        )

        if basic is None:
            skipped += 1
            continue

        if money(basic) <= 0:
            continue

        output.append({
            "source_table": "invoice_management",
            "source_invoice_id": str(row.get("id") or ""),
            "source_invoice_no": str(invoice_no).strip(),
            "source_invoice_date": wk_date(
                wk_pick(row, "invoice_date", "Invoice Date", "date")
            ),
            "project_id": project_id,
            "site_id": site_id,
            "site_name": site_name,
            **wk_calc(basic),
        })

    unique = {
        row["source_invoice_no"]: row
        for row in output
    }

    return list(unique.values()), (
        f"{skipped} source records skipped."
    )


def wk_pdf(header, items, settings=None):
    settings = settings or {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=13)
    pdf.add_page()

    pdf.set_font("Arial", "B", 15)
    pdf.cell(
        0, 10, WK_COMPANY["name"],
        ln=1, align="C"
    )

    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, WK_COMPANY["address"])
    pdf.cell(
        0, 6, "GSTIN: " + WK_COMPANY["gstin"],
        ln=1
    )

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 9, "TAX INVOICE", ln=1, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(
        0, 7,
        "Invoice No: " + str(header.get("invoice_no") or "PREVIEW"),
        ln=1
    )
    pdf.cell(
        0, 7,
        "Invoice Date: " + str(header.get("invoice_date") or ""),
        ln=1
    )

    pdf.multi_cell(
        0, 6,
        "Bill To: " + WK_BUYER["name"]
        + " | GSTIN: " + WK_BUYER["gstin"]
        + "\n" + WK_BUYER["address"]
    )

    pdf.ln(5)
    pdf.multi_cell(
        0, 6,
        "Description: Consolidated service charges "
        "against Indus Towers invoices as per Annexure A."
    )

    keys = (
        "original_basic",
        "discount_amount",
        "taxable_amount",
        "cgst",
        "sgst",
        "total_amount",
    )

    totals = {
        key: sum(
            (money(row.get(key)) for row in items),
            Decimal("0.00")
        )
        for key in keys
    }

    labels = [
        ("Original Basic Amount", "original_basic"),
        ("Less: 2% Deduction", "discount_amount"),
        ("Net Taxable Amount", "taxable_amount"),
        ("CGST @ 9%", "cgst"),
        ("SGST @ 9%", "sgst"),
        ("GRAND TOTAL", "total_amount"),
    ]

    pdf.ln(5)

    for label, key in labels:
        pdf.set_font(
            "Arial",
            "B" if key == "total_amount" else "",
            10
        )
        pdf.cell(115, 9, label, border=1)
        pdf.cell(
            75, 9,
            f"INR {totals[key]:,.2f}",
            border=1, align="R", ln=1
        )

    if settings.get("bank_name"):
        pdf.ln(7)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(
            0, 5,
            f"Bank: {settings.get('bank_name')}\n"
            f"Account: {settings.get('account_number') or ''}\n"
            f"IFSC: {settings.get('ifsc') or ''}"
        )

    pdf.ln(10)
    pdf.set_font("Arial", "", 9)
    pdf.cell(
        0, 7,
        "For WHIZ KEY IOT PRIVATE LIMITED",
        ln=1, align="R"
    )
    pdf.ln(9)
    pdf.cell(
        0, 7,
        "Authorised Signatory",
        ln=1, align="R"
    )

    # Annexure
    pdf.add_page("L")
    pdf.set_font("Arial", "B", 13)
    pdf.cell(
        0, 9,
        "ANNEXURE A - SITE-WISE INVOICE DETAILS",
        ln=1
    )

    columns = [
        ("Project ID", 31),
        ("Site ID", 26),
        ("Site Name", 40),
        ("Invoice No", 30),
        ("Date", 22),
        ("Basic", 20),
        ("2%", 16),
        ("Net", 20),
        ("CGST", 18),
        ("SGST", 18),
        ("Total", 20),
    ]

    def draw_header():
        pdf.set_font("Arial", "B", 7)
        for label, width in columns:
            pdf.cell(width, 8, label, border=1)
        pdf.ln()

    draw_header()

    for row in items:
        if pdf.get_y() > 180:
            pdf.add_page("L")
            draw_header()

        pdf.set_font("Arial", "", 7)

        values = [
            row.get("project_id", ""),
            row.get("site_id", ""),
            row.get("site_name", ""),
            row.get("source_invoice_no", ""),
            row.get("source_invoice_date", ""),
        ] + [
            f"{money(row.get(key)):,.2f}"
            for key in keys
        ]

        for (label, width), value in zip(columns, values):
            text = str(value or "")
            if len(text) > int(width / 1.6):
                text = text[:int(width / 1.6)]

            pdf.cell(
                width, 7, text,
                border=1,
                align="R" if label in (
                    "Basic", "2%", "Net", "CGST", "SGST", "Total"
                ) else "L"
            )
        pdf.ln()

    if pdf.get_y() > 180:
        pdf.add_page("L")
        draw_header()

    pdf.set_font("Arial", "B", 7)

    grand_values = [
        "GRAND TOTAL", "", "", "", ""
    ] + [
        f"{totals[key]:,.2f}"
        for key in keys
    ]

    for (_, width), value in zip(columns, grand_values):
        pdf.cell(width, 8, str(value), border=1)

    result = pdf.output(dest="S")

    if isinstance(result, (bytes, bytearray)):
        return bytes(result)

    return result.encode("latin-1")


def wk_pager(df, key):
    c1, c2, c3 = st.columns([1, 3, 1])

    with c1:
        size = st.selectbox(
            "Rows",
            [25, 50, 100, 200],
            index=1,
            key=key + "_size"
        )

    pages = max(1, (len(df) + size - 1) // size)
    page = min(st.session_state.get(key + "_page", 1), pages)

    with c2:
        st.caption(
            f"Page {page} of {pages} | {len(df)} Records"
        )

    with c3:
        p1, p2 = st.columns(2)
        if p1.button(
            "◀",
            disabled=page <= 1,
            key=key + "_prev"
        ):
            page -= 1
        if p2.button(
            "▶",
            disabled=page >= pages,
            key=key + "_next"
        ):
            page += 1

    st.session_state[key + "_page"] = page

    return df.iloc[
        (page - 1) * size:page * size
    ]


def wk_styles():
    st.markdown("""
    <style>
    .wk-hero {
        background:linear-gradient(110deg,#edf4ff,#f9efff);
        border:1px solid #dce5ff;
        border-radius:15px;
        padding:13px 19px;
        margin:5px 0 12px;
    }
    .wk-hero h3 {
        color:#30318a;
        margin:0;
        font-weight:850;
    }
    .wk-hero p {
        margin:4px 0 0;
        color:#64748b;
        font-size:12px;
    }
    .wk-section {
        padding:9px 13px;
        border-radius:12px;
        background:linear-gradient(110deg,#edf4ff,#f6f1ff);
        border:1px solid #dfe6f4;
        font-weight:850;
        margin:8px 0;
    }
    div.st-key-wk_nav_invoices button {
        background:linear-gradient(115deg,#315cf4,#8154fb)!important;
    }
    div.st-key-wk_nav_payment button {
        background:linear-gradient(115deg,#0793c2,#05bdd9)!important;
    }
    div.st-key-wk_nav_settings button {
        background:linear-gradient(115deg,#a63ae8,#e453c9)!important;
    }
    div.st-key-wk_nav_invoices button,
    div.st-key-wk_nav_payment button,
    div.st-key-wk_nav_settings button {
        min-height:76px!important;
        border:0!important;
        border-radius:17px!important;
        color:white!important;
        font-size:17px!important;
        font-weight:850!important;
        box-shadow:0 6px 14px #4c4fb02b!important;
        width:100%;
    }
    div.st-key-wk_create button {
        background:linear-gradient(110deg,#4057ff,#d73bdf)!important;
        color:white!important;
        border:0!important;
        font-weight:850!important;
        min-height:47px!important;
        border-radius:11px!important;
    }
    div[data-testid="stMetric"] {
        background:white;
        border:1px solid #dce6f7;
        border-radius:13px;
        padding:10px 14px;
        box-shadow:0 3px 10px #27345a0c;
    }
    div[data-testid="stMetricLabel"] p {
        font-size:12px!important;
        font-weight:750!important;
    }
    div[data-testid="stMetricValue"] {
        font-size:24px!important;
    }
    div[data-testid="stVerticalBlock"] {
        gap:0.55rem;
    }
    </style>
    """, unsafe_allow_html=True)


def wk_settings_data(db):
    try:
        rows = (
            db.table("wizhkey_company_settings")
            .select("*")
            .eq("company_code", "WIZHKEY")
            .execute().data or []
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def wk_invoice_screen(db):
    try:
        headers = wk_fetch_all(db, "wizhkey_invoices")
        items = wk_fetch_all(db, "wizhkey_invoice_items")
        source, message = wk_source_rows(db)
    except Exception as error:
        st.error(f"Unable to load invoice data: {error}")
        return

    active = {
        h["id"]: h
        for h in headers
        if h.get("status") != "CANCELLED"
    }

    billed = {
        (item["source_table"], item["source_invoice_no"])
        for item in items
        if item["consolidated_invoice_id"] in active
    }

    pending = [
        row for row in source
        if (
            row["source_table"],
            row["source_invoice_no"]
        ) not in billed
    ]

    pending.sort(
        key=lambda r: (
            r.get("source_invoice_date") or "",
            r["source_invoice_no"]
        ),
        reverse=True
    )

    created = []

    for item in items:
        header = active.get(item["consolidated_invoice_id"])
        if not header:
            continue

        created.append({
            "Wizh Key Invoice No": header.get("invoice_no"),
            "Wizh Key Invoice Date": header.get("invoice_date"),
            "Original Invoice No": item.get("source_invoice_no"),
            "Original Invoice Date": item.get("source_invoice_date"),
            "Project ID": item.get("project_id"),
            "Site ID": item.get("site_id"),
            "Site Name": item.get("site_name"),
            "Original Basic": item.get("original_basic"),
            "2% Deduction": item.get("discount_amount"),
            "Taxable Amount": item.get("taxable_amount"),
            "CGST": item.get("cgst"),
            "SGST": item.get("sgst"),
            "Total Amount": item.get("total_amount"),
        })

    st.markdown("""
    <div class="wk-hero">
      <h3>🧾 Wizh Key Billing</h3>
      <p>Pending original invoices remain available until billed.
      Each source invoice can be billed only once.</p>
    </div>
    """, unsafe_allow_html=True)

    if "wk_selected_keys" not in st.session_state:
        st.session_state["wk_selected_keys"] = []

    valid_keys = {
        row["source_invoice_no"]
        for row in pending
    }

    selected_keys = set(
        st.session_state["wk_selected_keys"]
    ) & valid_keys

    chosen = [
        row for row in pending
        if row["source_invoice_no"] in selected_keys
    ]

    m1, m2, m3, m4 = st.columns(4, gap="small")

    m1.metric("🟠 Pending Invoices", len(pending))
    m2.metric("🔵 Selected Invoices", len(chosen))
    m3.metric(
        "💰 Selected Basic",
        f"₹{sum(r['original_basic'] for r in chosen):,.2f}"
    )
    m4.metric(
        "💎 Estimated Invoice",
        f"₹{sum(r['total_amount'] for r in chosen):,.2f}"
    )

    subtab = st.radio(
        "Invoice Register",
        ["🟠 Pending", "🟢 Created"],
        horizontal=True,
        label_visibility="collapsed",
        key="wk_invoice_subtab",
    )

    if subtab == "🟠 Pending":
        st.markdown(
            '<div class="wk-section">'
            '📋 Pending Indus Invoices — Select to Create Invoice'
            '</div>',
            unsafe_allow_html=True
        )

        f1, f2, f3 = st.columns(
            [1.3, 3.2, 1], gap="small"
        )

        with f1:
            inv_date = st.date_input(
                "Wizh Key Invoice Date",
                value=date.today(),
                key="wk_invoice_date"
            )

        with f2:
            query = st.text_input(
                "Search Invoice / Project / Site",
                key="wk_pending_search",
                placeholder="Search invoice no, project id, site id..."
            )

        with f3:
            size = st.selectbox(
                "Rows per page",
                [25, 50, 100, 200],
                index=1,
                key="wk_pending_size"
            )

        visible = [
            row for row in pending
            if not query or query.lower() in " ".join(
                str(v) for v in row.values()
            ).lower()
        ]

        a, b, c = st.columns(
            [1.15, 1.15, 4],
            gap="small"
        )

        if a.button(
            "☑ Select All Filtered",
            key="wk_select_all",
            use_container_width=True
        ):
            selected_keys.update(
                row["source_invoice_no"]
                for row in visible
            )
            st.session_state["wk_editor_rev"] = (
                st.session_state.get("wk_editor_rev", 0) + 1
            )
            st.session_state["wk_selected_keys"] = list(selected_keys)
            st.rerun()

        if b.button(
            "✖ Clear Selection",
            key="wk_clear_selection",
            use_container_width=True
        ):
            st.session_state["wk_selected_keys"] = []
            st.session_state["wk_editor_rev"] = (
                st.session_state.get("wk_editor_rev", 0) + 1
            )
            st.rerun()

        c.caption(
            f"{len(visible)} matching invoices | "
            f"{len(selected_keys)} selected"
        )

        pages = max(
            1, (len(visible) + size - 1) // size
        )

        page = min(
            st.session_state.get("wk_pending_page", 1),
            pages
        )

        p1, p2, p3 = st.columns([1, 4, 1])

        if p1.button(
            "◀ Previous",
            disabled=page <= 1,
            key="wk_prev"
        ):
            page -= 1

        p2.markdown(
            f"<p style='text-align:center'>"
            f"Page {page} of {pages}</p>",
            unsafe_allow_html=True
        )

        if p3.button(
            "Next ▶",
            disabled=page >= pages,
            key="wk_next"
        ):
            page += 1

        st.session_state["wk_pending_page"] = page

        page_rows = visible[
            (page - 1) * size:page * size
        ]

        columns = [
            "source_invoice_no",
            "source_invoice_date",
            "project_id",
            "site_id",
            "site_name",
            "original_basic",
            "discount_amount",
            "taxable_amount",
            "cgst",
            "sgst",
            "total_amount",
        ]

        if page_rows:
            display = pd.DataFrame([
                {
                    "Select": (
                        row["source_invoice_no"] in selected_keys
                    ),
                    **{
                        key: row.get(key)
                        for key in columns
                    }
                }
                for row in page_rows
            ])

            editor_key = (
                f"wk_editor_{page}_"
                f"{st.session_state.get('wk_editor_rev', 0)}"
            )

            edited = st.data_editor(
                display,
                key=editor_key,
                hide_index=True,
                use_container_width=True,
                disabled=columns,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select", width="small"
                    ),
                    "original_basic": st.column_config.NumberColumn(
                        "Original Basic", format="%.2f"
                    ),
                    "discount_amount": st.column_config.NumberColumn(
                        "2% Deduction", format="%.2f"
                    ),
                    "taxable_amount": st.column_config.NumberColumn(
                        "Taxable Basic", format="%.2f"
                    ),
                    "cgst": st.column_config.NumberColumn(
                        "CGST 9%", format="%.2f"
                    ),
                    "sgst": st.column_config.NumberColumn(
                        "SGST 9%", format="%.2f"
                    ),
                    "total_amount": st.column_config.NumberColumn(
                        "Final Amount", format="%.2f"
                    ),
                },
                height=390
            )

            for index, row in enumerate(page_rows):
                invoice_no = row["source_invoice_no"]

                if bool(edited.iloc[index]["Select"]):
                    selected_keys.add(invoice_no)
                else:
                    selected_keys.discard(invoice_no)

            st.session_state["wk_selected_keys"] = list(selected_keys)

        chosen = [
            row for row in pending
            if row["source_invoice_no"] in selected_keys
        ]

        st.markdown(
            '<div class="wk-section">'
            '💳 Selected Invoice Summary & Actions'
            '</div>',
            unsafe_allow_html=True
        )

        s1, s2, s3, s4 = st.columns(4, gap="small")

        s1.metric("Selected", len(chosen))
        s2.metric(
            "Original Basic",
            f"₹{sum(r['original_basic'] for r in chosen):,.2f}"
        )
        s3.metric(
            "2% Deduction",
            f"₹{sum(r['discount_amount'] for r in chosen):,.2f}"
        )
        s4.metric(
            "Final Amount",
            f"₹{sum(r['total_amount'] for r in chosen):,.2f}"
        )

        if chosen:
            draft_header = {
                "invoice_no": "PREVIEW",
                "invoice_date": inv_date.isoformat(),
            }

            try:
                preview_pdf = wk_pdf(
                    draft_header,
                    chosen,
                    wk_settings_data(db)
                )
            except Exception as error:
                preview_pdf = None
                st.error(f"PDF Preview error: {error}")

            excel_buffer = io.BytesIO()
            pd.DataFrame(chosen).to_excel(
                excel_buffer, index=False
            )

            x1, x2, x3 = st.columns(
                [1.1, 1.1, 1.6],
                gap="small"
            )

            with x1:
                if preview_pdf:
                    st.download_button(
                        "👁 Preview Selected",
                        data=preview_pdf,
                        file_name="WizhKey_Preview.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            with x2:
                st.download_button(
                    "⬇ Export Excel",
                    data=excel_buffer.getvalue(),
                    file_name="WizhKey_Selected.xlsx",
                    use_container_width=True
                )

            with x3:
                if st.button(
                    "💾 Create Consolidated Invoice",
                    type="primary",
                    use_container_width=True,
                    key="wk_create"
                ):
                    missing = [
                        row["source_invoice_no"]
                        for row in chosen
                        if not (
                            row["project_id"]
                            and row["site_id"]
                            and row["site_name"]
                        )
                    ]

                    if missing:
                        st.error(
                            "Project ID / Site ID / Site Name "
                            "missing for: " + ", ".join(missing[:10])
                        )
                    else:
                        totals = {
                            key: float(sum(
                                (money(row[key]) for row in chosen),
                                Decimal("0.00")
                            ))
                            for key in (
                                "original_basic",
                                "discount_amount",
                                "taxable_amount",
                                "cgst",
                                "sgst",
                                "total_amount",
                            )
                        }

                        payload = {
                            "invoice_date": inv_date.isoformat(),
                            "billing_month": (
                                inv_date.replace(day=1).isoformat()
                            ),
                            "bill_to": WK_BUYER["name"],
                            "discount_percent": 2,
                            "status": "FINAL",
                            **totals,
                        }

                        try:
                            response = db.rpc(
                                "wk_create_consolidated_invoice",
                                {
                                    "p_header": payload,
                                    "p_items": chosen,
                                }
                            ).execute()

                            result = response.data or {}

                            if isinstance(result, dict):
                                number = result.get("invoice_no", "")
                            else:
                                number = str(result)

                            st.session_state["wk_selected_keys"] = []
                            st.session_state["wk_last_created"] = number
                            st.session_state["wk_invoice_subtab"] = (
                                "🟢 Created"
                            )
                            st.rerun()

                        except Exception as error:
                            st.error(
                                "Invoice not created: "
                                + str(error)
                            )
        else:
            st.info(
                "Select one or more invoices from the table "
                "to preview or create a consolidated invoice."
            )

    else:
        st.markdown(
            '<div class="wk-section">'
            '🟢 Created Invoices Register'
            '</div>',
            unsafe_allow_html=True
        )

        last_created = st.session_state.pop(
            "wk_last_created", None
        )

        if last_created:
            st.success(
                f"Invoice created successfully: {last_created}"
            )

        search = st.text_input(
            "Search Wizh Key Invoice / Project / Site",
            key="wk_created_search"
        )

        rows = [
            row for row in created
            if not search or search.lower() in " ".join(
                str(v) for v in row.values()
            ).lower()
        ]

        if rows:
            df = pd.DataFrame(rows)

            st.dataframe(
                wk_pager(df, "wk_created"),
                hide_index=True,
                use_container_width=True,
                height=390
            )

            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)

            st.download_button(
                "⬇ Export Created Register",
                buffer.getvalue(),
                "WizhKey_Created.xlsx"
            )
        else:
            st.info("No matching created invoices.")

        if active:
            st.markdown(
                '<div class="wk-section">'
                '📄 Download Consolidated Invoice & Annexure'
                '</div>',
                unsafe_allow_html=True
            )

            choices = {
                (
                    f"{header.get('invoice_no')} | "
                    f"{header.get('invoice_date')} | "
                    f"{header.get('status')}"
                ): header
                for header in sorted(
                    active.values(),
                    key=lambda x: x["id"],
                    reverse=True
                )
            }

            selected = st.selectbox(
                "Select Wizh Key Invoice",
                ["Select"] + list(choices),
                key="wk_created_invoice_select"
            )

            if selected != "Select":
                header = choices[selected]

                pdf_items = [
                    item for item in items
                    if item["consolidated_invoice_id"] == header["id"]
                ]

                try:
                    pdf_bytes = wk_pdf(
                        header,
                        pdf_items,
                        wk_settings_data(db)
                    )

                    st.download_button(
                        "⬇ Download Invoice + Annexure PDF",
                        pdf_bytes,
                        f"{header.get('invoice_no')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as error:
                    st.error(f"PDF error: {error}")

                if header.get("status") == "FINAL":
                    confirm = st.checkbox(
                        "I confirm this invoice should be cancelled",
                        key="wk_cancel_confirm"
                    )

                    if confirm and st.button(
                        "Cancel Consolidated Invoice",
                        key="wk_cancel"
                    ):
                        try:
                            (
                                db.table("wizhkey_invoices")
                                .update({"status": "CANCELLED"})
                                .eq("id", header["id"])
                                .execute()
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(str(error))


def wk_payment_screen(db):
    st.markdown("### 💳 Payment Received / Paid")

    try:
        payments = wk_fetch_all(db, "wizhkey_payments")
    except Exception as error:
        st.error(str(error))
        return

    df = pd.DataFrame(payments)

    if not df.empty:
        df = df.sort_values(["payment_date", "id"])

        df["received"] = df.apply(
            lambda row: float(row["amount"])
            if row["payment_type"] == "RECEIVED"
            else 0,
            axis=1
        )

        df["paid"] = df.apply(
            lambda row: float(row["amount"])
            if row["payment_type"] == "PAID"
            else 0,
            axis=1
        )

        df["balance"] = (
            df["received"] - df["paid"]
        ).cumsum()

        a, b, c = st.columns(3)

        a.metric(
            "Payment Received",
            f"₹{df['received'].sum():,.2f}"
        )
        b.metric(
            "Payment Paid",
            f"₹{df['paid'].sum():,.2f}"
        )
        c.metric(
            "Net Balance",
            f"₹{df['balance'].iloc[-1]:,.2f}"
        )

        search = st.text_input(
            "🔎 Search Payments",
            key="wk_payment_search"
        )

        shown = df[
            df.astype(str).apply(
                lambda column: column.str.contains(
                    search, case=False, regex=False
                )
            ).any(axis=1)
        ] if search else df

        st.dataframe(
            wk_pager(shown.iloc[::-1], "wk_payments"),
            hide_index=True,
            use_container_width=True
        )

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)

        st.download_button(
            "⬇ Download Payment Ledger Excel",
            buffer.getvalue(),
            "WizhKey_Payment_Ledger.xlsx"
        )
    else:
        st.info("No payments recorded yet.")

    with st.expander("➕ Create New Payment"):
        with st.form("wk_payment_form"):
            a, b, c = st.columns(3)

            with a:
                payment_date = st.date_input(
                    "Payment Date", value=date.today()
                )
                payment_type = st.selectbox(
                    "Payment Type", ["RECEIVED", "PAID"]
                )

            with b:
                party = st.text_input(
                    "Party Name", value=WK_BUYER["name"]
                )
                amount = st.number_input(
                    "Amount", min_value=0.01, step=100.0
                )

            with c:
                mode = st.selectbox(
                    "Payment Mode",
                    [
                        "BANK TRANSFER",
                        "UPI",
                        "CHEQUE",
                        "CASH",
                        "OTHER",
                    ]
                )
                bank = st.text_input("Bank Name")

            reference = st.text_input(
                "UTR / Reference Number"
            )
            remarks = st.text_area("Remarks")

            if st.form_submit_button("💾 Save Payment"):
                try:
                    (
                        db.table("wizhkey_payments")
                        .insert({
                            "payment_date": payment_date.isoformat(),
                            "payment_type": payment_type,
                            "party_name": party,
                            "amount": amount,
                            "payment_mode": mode,
                            "bank_name": bank,
                            "reference_no": reference,
                            "remarks": remarks,
                        })
                        .execute()
                    )
                    st.success("Payment saved successfully.")
                    st.rerun()
                except Exception as error:
                    st.error(str(error))

    st.caption(
        "This is a date-wise cash ledger. "
        "Invoice-wise payment allocation is not yet implemented."
    )


def wk_settings_screen(db):
    st.markdown("### ⚙️ Company & Bank Settings")

    st.write(WK_COMPANY)

    old = wk_settings_data(db)

    with st.form("wk_company_settings"):
        bank = st.text_input(
            "Bank Name",
            value=old.get("bank_name") or ""
        )
        account = st.text_input(
            "Account Number",
            value=old.get("account_number") or ""
        )
        ifsc = st.text_input(
            "IFSC Code",
            value=old.get("ifsc") or ""
        )

        if st.form_submit_button("💾 Save Company Settings"):
            try:
                (
                    db.table("wizhkey_company_settings")
                    .upsert({
                        "company_code": "WIZHKEY",
                        "legal_name": WK_COMPANY["name"],
                        "address": WK_COMPANY["address"],
                        "gstin": WK_COMPANY["gstin"],
                        "pan": WK_COMPANY["pan"],
                        "state": "Maharashtra",
                        "bank_name": bank,
                        "account_number": account,
                        "ifsc": ifsc,
                    }, on_conflict="company_code")
                    .execute()
                )
                st.success("Company Settings Saved.")
                st.rerun()
            except Exception as error:
                st.error(str(error))


def wk_show(db):
    wk_styles()

    st.markdown(
        "### 💎 WHIZ KEY · Consolidated Billing & Ledger"
    )

    st.caption(
        "Seller: WHIZ KEY IOT PRIVATE LIMITED | "
        "GSTIN: 27AADCW7297D1ZY | "
        "Buyer: Bhagyashree Enterprises"
    )

    if "wk_active_section" not in st.session_state:
        st.session_state["wk_active_section"] = "invoices"

    nav1, nav2, nav3 = st.columns(3, gap="medium")

    with nav1:
        if st.button(
            "🧾 INVOICES",
            key="wk_nav_invoices",
            use_container_width=True
        ):
            st.session_state["wk_active_section"] = "invoices"
            st.rerun()

    with nav2:
        if st.button(
            "💳 PAYMENT & LEDGER",
            key="wk_nav_payment",
            use_container_width=True
        ):
            st.session_state["wk_active_section"] = "payment"
            st.rerun()

    with nav3:
        if st.button(
            "⚙️ COMPANY SETTINGS",
            key="wk_nav_settings",
            use_container_width=True
        ):
            st.session_state["wk_active_section"] = "settings"
            st.rerun()

    section = st.session_state["wk_active_section"]

    if section == "invoices":
        wk_invoice_screen(db)

    elif section == "payment":
        wk_payment_screen(db)

    elif section == "settings":
        wk_settings_screen(db)
