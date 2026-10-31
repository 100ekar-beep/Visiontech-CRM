
# WHIZ KEY IOT PRIVATE LIMITED
# Streamlit Consolidated Invoice & Payment Module
# Filename: wizhkey_module.py

import io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st


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
            wk_pick(row, "invoice_status", "Sub_status", "status") or ""
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

    # Keep every source database record. Invoice numbers are not unique.
    seen_ids = set()
    unique_rows = []
    for entry in output:
        record_id = entry["source_invoice_id"]
        if not record_id:
            raise ValueError("Source invoice has no database ID; billing stopped for safety.")
        if record_id in seen_ids:
            raise ValueError(f"Repeated source database ID: {record_id}")
        seen_ids.add(record_id)
        unique_rows.append(entry)

    return unique_rows, f"{skipped} source records skipped."


def wk_pdf(header, items, settings=None):
    """Approved royal-design PDF: branded artwork + live, selectable invoice data."""
    from pathlib import Path
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    import textwrap

    settings = settings or {}
    navy = HexColor('#092657')
    blue = HexColor('#073A7D')
    gold = HexColor('#F2BC47')
    ink = HexColor('#13244A')
    pale = HexColor('#EAF3FD')
    border = HexColor('#B9D2F0')
    W, H = A4
    sx, sy = W/768, H/1024
    number = str(header.get('invoice_no') or 'PREVIEW')
    invdate = str(header.get('invoice_date') or '')[:10]
    company = WK_COMPANY
    buyer = WK_BUYER
    keys = ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')
    totals = {k:sum((money(r.get(k)) for r in items),Decimal('0.00')) for k in keys}
    page_size=15
    chunks=[items[i:i+page_size] for i in range(0,len(items),page_size)] or [[]]
    total_annexure=len(chunks)
    out=io.BytesIO()
    c=canvas.Canvas(out,pagesize=A4,pageCompression=1)
    c.setTitle(number+' | WHIZ KEY IOT PRIVATE LIMITED')
    assets=Path(__file__).resolve().parent
    art=assets/'wk_royal_template.png'
    stamp=assets/'wk_stamp.png'
    
    if not art.exists():
        raise FileNotFoundError('Royal PDF design missing: wk_royal_template.png. Keep this PNG in the same folder as wizhkey_module.py.')
    source=Image.open(art).convert('RGB')
    if source.size != (1536,1024):
        raise ValueError('wk_royal_template.png must be the supplied 1536x1024 approved design image')
    def rect(x,y,w,h,fill,stroke=None,r=0):
        c.setFillColor(fill)
        if stroke:c.setStrokeColor(stroke)
        if r:c.roundRect(x*sx,H-(y+h)*sy,w*sx,h*sy,r*sx,fill=1,stroke=int(bool(stroke)))
        else:c.rect(x*sx,H-(y+h)*sy,w*sx,h*sy,fill=1,stroke=int(bool(stroke)))
    def tx(x,y,value,size=12,color=ink,bold=False,align='left'):
        c.setFillColor(color)
        c.setFont('Helvetica-Bold' if bold else 'Helvetica',size*sx)
        fn={'left':c.drawString,'right':c.drawRightString,'center':c.drawCentredString}[align]
        fn(x*sx,H-y*sy,str(value))
    def fit(x,y,value,max_width,size=12,color=ink,bold=False,align='left'):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        value=str(value)
        while size>6 and stringWidth(value,'Helvetica-Bold' if bold else 'Helvetica',size*sx)>max_width*sx:
            size-=.4
        tx(x,y,value,size,color,bold,align)
    def money_fmt(value):return f'{money(value):,.2f}'
    def panel(x,y,w,h):rect(x,y,w,h,white,border,6)
    def image_crop(page,top,bottom,x=0,w=768):
        if source:
            start=0 if page==0 else 768
            im=source.crop((start,top,start+768,bottom))
            c.drawImage(ImageReader(im),x*sx,H-bottom*sy,w*sx,(bottom-top)*sy,mask='auto')
    def base(page,annex=False):
        rect(0,0,768,1024,white)
        image_crop(page,0,210 if not annex else 195)
        # Approved banner art is used verbatim; lower body is vector text and tables.
        # Royal artwork is required; no silent black-and-white fallback.
        rect(0,943,768,81,navy)
        rect(0,940,768,4,gold)
        rect(620,944,148,80,gold)
        tx(30,984,company['name'],12,white,True)
        tx(744,986,(f'Page {page+1} of {total_annexure+1}' if annex else f'Page 1 of {total_annexure+1}'),12,navy,True,'right')
    def title(label,annex=False):
        rect(235 if not annex else 145,204,300 if not annex else 480,42,navy,gold,8)
        fit(384,232,label,450 if annex else 290,23,gold,True,'center')
    def amount_words(v):
        units=['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen']
        tens=['','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety']
        def small(n):
            bits=[]
            if n>=100:bits.append(units[n//100]+' Hundred');n%=100
            if n>=20:bits.append(tens[n//10]);n%=10
            if n:bits.append(units[n])
            return ' '.join(bits)
        amt=money(v);whole=int(amt);paise=int((amt-Decimal(whole))*100)
        bits=[]
        for div,name in [(10000000,'Crore'),(100000,'Lakh'),(1000,'Thousand'),(1,'')]:
            if whole>=div:
                q,whole=divmod(whole,div)
                bits.append(small(q)+(' '+name if name else ''))
        return 'INR '+(' '.join(bits) or 'Zero')+' Rupees'+(' and '+small(paise)+' Paise' if paise else '')+' Only'

    # PAGE 1 - tax invoice
    base(0)
    title('TAX INVOICE')
    panel(44,254,680,181)
    tx(89,279,'BILL TO',15,blue,True)
    fit(89,309,buyer['name'],315,18,ink,True)
    for i,line in enumerate(textwrap.wrap(buyer['address'],45)[:3]):tx(89,334+i*20,line,12)
    fit(89,413,'GSTIN: '+buyer['gstin'],300,13,ink,True)
    rect(415,260,1,170,border)
    tx(439,280,'INVOICE DETAILS',15,blue,True)
    for i,(k,v) in enumerate([('Invoice No.',number),('Invoice Date',invdate),('Place of Supply','Maharashtra (27)'),('Original Sites',str(len(items)))]):
        yy=312+i*31
        tx(439,yy,k,11,ink)
        fit(707,yy,v,140,12,ink,i==0,'right')
    # Item table
    xs=[44,100,336,417,497,610,724]
    rect(44,446,680,39,navy)
    for x,txt0 in [(70,'Sr.'),(215,'Particulars'),(377,'HSN/SAC'),(458,'Qty'),(553,'Rate (INR)'),(665,'Amount (INR)')]:
        tx(x,471,txt0,11,white,True,'center')
    panel(44,485,680,74)
    tx(70,526,'1',13,ink,True,'center')
    tx(112,516,'Mobile Tower Work',14,ink,True)
    tx(112,540,'(Annexure Attached)',12)
    tx(377,527,'998719',12,ink,False,'center')
    tx(458,527,'1',13,ink,True,'center')
    fit(603,527,money_fmt(totals['original_basic']),100,12,ink,True,'right')
    fit(714,527,money_fmt(totals['original_basic']),105,12,ink,True,'right')
    labels=[('Original Basic Amount','original_basic'),('Less: 2% Discount','discount_amount'),('Net Taxable Amount','taxable_amount'),('CGST @ 9%','cgst'),('SGST @ 9%','sgst')]
    for i,(label,key) in enumerate(labels):
        yy=569+i*35
        rect(44,yy,680,35,HexColor('#DFF4E2') if i==1 else pale if i in (0,2) else white,border)
        tx(65,yy+24,label,14,ink,i in (0,1,2))
        tx(708,yy+24,'INR '+money_fmt(totals[key]),14,ink,True,'right')
    rect(44,744,680,44,navy)
    tx(65,773,'GRAND TOTAL',19,gold,True)
    tx(708,773,'INR '+money_fmt(totals['total_amount']),18,gold,True,'right')
    rect(44,800,680,53,pale)
    tx(60,820,'Amount In Words:',12,blue,True)
    for i,line in enumerate(textwrap.wrap(amount_words(totals['total_amount']),78)[:2]):tx(198,821+i*16,line,10,ink)
    tx(46,876,'Terms & Conditions:',12,navy,True)
    tx(46,894,'1. Payment as per agreed credit terms.',10)
    tx(46,910,'2. Annexure is an integral part of this invoice.',10)
    tx(46,925,'3. Please contact us for invoice queries.',10)
    tx(716,869,'For '+company['name'],11,navy,True,'right')
    if stamp.exists():
        try:
            im=Image.open(stamp).convert('RGB')
            from PIL import ImageChops
            diff=ImageChops.difference(im,Image.new('RGB',im.size,'white'))
            bb=diff.getbbox()
            if bb: im=im.crop(bb)
            c.drawImage(ImageReader(im),510*sx,H-931*sy,190*sx,64*sy,mask='auto',preserveAspectRatio=True,anchor='c')
        except Exception:pass
    tx(705,933,'Authorised Signatory',10,navy,True,'right')
    c.showPage()

    # Annexure pages - same approved header and footer, real dynamic rows
    cols=[('Sr.',30),('Project ID',86),('Site ID',70),('Site Name',105),('Invoice No.',82),('Date',70),('Basic',65),('2% Discount',68),('Net',66),('CGST',61),('SGST',61),('Total',74)]
    factor=728/sum(w for _,w in cols)
    widths=[w*factor for _,w in cols]
    for idx,chunk in enumerate(chunks):
        base(idx+1,True)
        title('ANNEXURE A - SITE-WISE INVOICE DETAILS',True)
        panel(30,251,708,65)
        tx(44,274,'Invoice No.:  '+number,11,ink,True)
        tx(44,299,'Invoice Date:  '+invdate,11)
        tx(432,274,'Work Period:  '+str(settings.get('work_period') or 'Sep & Oct 2026'),11)
        tx(432,299,'Total Sites:  '+str(len(items)),11,ink,True)
        left=20
        rect(left,330,728,43,navy)
        x=left
        for (name,_),w in zip(cols,widths):
            parts=name.split(' ')
            if name=='2% Discount':
                tx(x+w/2,348,'2%',9,white,True,'center');tx(x+w/2,361,'Discount',8,white,True,'center')
            else:fit(x+w/2,356,name,w-3,10,white,True,'center')
            x+=w
        page_tot={k:Decimal('0.00') for k in keys}
        row_height=28
        for j,row in enumerate(chunk):
            y=373+j*row_height
            rect(left,y,728,row_height,pale if j%2==0 else white,border)
            values=[str(idx*page_size+j+1),str(row.get('project_id') or ''),str(row.get('site_id') or ''),str(row.get('site_name') or ''),str(row.get('source_invoice_no') or ''),str(row.get('source_invoice_date') or '')[:10]]+[money_fmt(row.get(k)) for k in keys]
            x=left
            for k,((name,_),w,value) in enumerate(zip(cols,widths,values)):
                if k in (1,2,3,4,5):
                    fit(x+3,y+18,value,w-5,9,ink,False)
                else:fit(x+w-3,y+18,value,w-5,9,ink,False,'right')
                x+=w
            for key in keys:page_tot[key]+=money(row.get(key))
        y=373+len(chunk)*row_height+8
        rect(left,y,728,34,HexColor('#DCEBFB'),border)
        tx(36,y+23,f'PAGE TOTAL ({len(chunk)} SITES)',12,navy,True)
        tx(730,y+23,'INR '+money_fmt(page_tot['total_amount']),12,navy,True,'right')
        y+=42
        if idx==len(chunks)-1:
            rect(left,y,728,36,HexColor('#FFF0D1'),gold)
            tx(36,y+24,f'GRAND TOTAL ({len(items)} SITES)',13,navy,True)
            tx(730,y+24,'INR '+money_fmt(totals['total_amount']),13,navy,True,'right')
        tx(32,888,'Note: This annexure forms part of Invoice No. '+number,11,blue,True)
        tx(32,907,'All amounts are in Indian Rupees. Discount and GST are shown site-wise.',10)
        c.showPage()
    c.save()
    return out.getvalue()

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

    # Prefer exact source row ID, not the invoice number. Older billed items
    # without IDs are handled conservatively so they cannot be rebilled blindly.
    billed_ids = set()
    legacy_billed_numbers = set()
    for item in items:
        if item.get("consolidated_invoice_id") not in active:
            continue
        if item.get("source_table") != "invoice_management":
            continue
        source_id = str(item.get("source_invoice_id") or "").strip()
        if source_id:
            billed_ids.add(source_id)
        else:
            legacy_billed_numbers.add(str(item.get("source_invoice_no") or "").strip())

    pending = [
        row for row in source
        if row["source_invoice_id"] not in billed_ids
        and row["source_invoice_no"] not in legacy_billed_numbers
    ]
    if legacy_billed_numbers:
        st.warning(
            "Some older billed items have no source ID. Matching invoice numbers "
            "are held back to prevent double billing until verified."
        )

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
        row["source_invoice_id"]
        for row in pending
    }

    selected_keys = set(
        st.session_state["wk_selected_keys"]
    ) & valid_keys

    chosen = [
        row for row in pending
        if row["source_invoice_id"] in selected_keys
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

    # Apply tab navigation on the next rerun, BEFORE the radio widget exists.
    next_tab = st.session_state.pop("wk_next_invoice_subtab", None)
    if next_tab in ("🟠 Pending", "🟢 Created"):
        st.session_state["wk_invoice_subtab"] = next_tab

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
                row["source_invoice_id"]
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
            "source_invoice_id",
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
                        row["source_invoice_id"] in selected_keys
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
                source_id = row["source_invoice_id"]

                if bool(edited.iloc[index]["Select"]):
                    selected_keys.add(source_id)
                else:
                    selected_keys.discard(source_id)

            st.session_state["wk_selected_keys"] = list(selected_keys)

        chosen = [
            row for row in pending
            if row["source_invoice_id"] in selected_keys
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
                            # Do not mutate a widget key after instantiation.
                            # Schedule the tab switch for the next rerun instead.
                            st.session_state["wk_next_invoice_subtab"] = "🟢 Created"
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
