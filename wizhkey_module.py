# Wizh Key monthly billing module. Imported into the existing Streamlit application.
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import io
import pandas as pd
import streamlit as st
from fpdf import FPDF

WK_COMPANY = {'name':'WHIZ KEY IOT PRIVATE LIMITED','gstin':'27AADCW7297D1ZY','pan':'AADCW7297D','address':'Office No. 1, S No. 23, 24, 55, Near Vikas Mitra Mandal, Karve Nagar, Pune, Maharashtra - 411052'}
WK_BUYER = {'name':'Bhagyashree Enterprises','gstin':'27ABWPV2922M1ZQ','address':'S. No. 66, Sai Pritam Nagar, Rahtani, BLD-A Flat-7, Pune, Maharashtra - 411017'}

def money(v):
    try: return Decimal(str(v or 0).replace(',','')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    except Exception: return Decimal('0.00')

def wk_calc(basic):
    b=money(basic); d=money(b*Decimal('.02')); n=b-d
    c=money(n*Decimal('.09')); s=money(n*Decimal('.09'))
    return dict(original_basic=float(b),discount_amount=float(d),taxable_amount=float(n),cgst=float(c),sgst=float(s),total_amount=float(n+c+s))

def wk_pick(row,*names):
    norm={str(k).lower().replace(' ','').replace('_',''):v for k,v in row.items()}
    for name in names:
        v=norm.get(name.lower().replace(' ','').replace('_',''))
        if v is not None and str(v).strip() not in ('','nan','None','null'): return v
    return None

def wk_date(v):
    try: return pd.to_datetime(v,dayfirst=False).date().isoformat() if v else None
    except Exception: return None

def wk_fetch_all(db,table,workspace=None):
    data=[]; start=0
    while True:
        q=db.table(table).select('*').range(start,start+999)
        if workspace: q=q.eq('workspace',workspace)
        chunk=q.execute().data or []
        data.extend(chunk)
        if len(chunk)<1000: break
        start+=1000
    return data

def wk_source_rows(db):
    # Source is Bhagyashree's Indus billing master, NOT the separate supplier-billing table.
    # Explicit schema mapping avoids treating a GST-inclusive invoice total as its basic value.
    records=wk_fetch_all(db,'invoice_management','BHAGYASHREE')
    if not records: return [],'No BHAGYASHREE records in invoice_management.'
    sites=wk_fetch_all(db,'site_data','BHAGYASHREE')
    by_project={str(wk_pick(s,'Project ID','project_id')):s for s in sites}
    by_site={str(wk_pick(s,'Site ID','site_id')):s for s in sites}
    out=[]; skipped=0
    for r in records:
        inv=wk_pick(r,'invoice_no','invoice_number','invoice number','Invoice No','Tally Invoice Number')
        if not inv: skipped+=1; continue
        status=str(wk_pick(r,'invoice_status','status') or '').upper()
        if 'CANCEL' in status or 'DRAFT' in status: continue
        pid=str(wk_pick(r,'project_id','Project ID') or '')
        sid=str(wk_pick(r,'site_id','Site ID') or '')
        site=by_project.get(pid) or by_site.get(sid) or {}
        pid=pid or str(wk_pick(site,'Project ID') or '')
        sid=sid or str(wk_pick(site,'Site ID') or '')
        name=str(wk_pick(r,'site_name','Site Name') or wk_pick(site,'Site Name') or '')
        basic=wk_pick(r,'basic_amount','basic amount','taxable_amount','taxable value','basic')
        if basic is None: skipped+=1; continue
        if money(basic)<=0: continue
        dt=wk_date(wk_pick(r,'invoice_date','Invoice Date','date'))
        out.append(dict(source_table='invoice_management',source_invoice_id=str(r.get('id') or ''),source_invoice_no=str(inv).strip(),source_invoice_date=dt,project_id=pid,site_id=sid,site_name=name,**wk_calc(basic)))
    dedup={r['source_invoice_no']:r for r in out}
    return list(dedup.values()),f'{skipped} records skipped (missing invoice number or verified basic amount). Check master column mapping if expected records are missing.'

def wk_pdf(header,items,settings=None):
    settings=settings or {}; pdf=FPDF();pdf.set_auto_page_break(auto=True,margin=13);pdf.add_page()
    pdf.set_font('Arial','B',15);pdf.cell(0,10,WK_COMPANY['name'],ln=1,align='C')
    pdf.set_font('Arial','',9);pdf.multi_cell(0,5,WK_COMPANY['address']);pdf.cell(0,6,'GSTIN: '+WK_COMPANY['gstin'],ln=1)
    pdf.line(10,pdf.get_y()+2,200,pdf.get_y()+2);pdf.ln(6)
    pdf.set_font('Arial','B',14);pdf.cell(0,9,'TAX INVOICE',ln=1,align='C')
    pdf.set_font('Arial','',10)
    pdf.cell(0,7,'Invoice No: '+str(header.get('invoice_no') or 'DRAFT'),ln=1)
    pdf.cell(0,7,'Invoice Date: '+str(header.get('invoice_date') or ''),ln=1)
    pdf.cell(0,7,'Billing Month: '+str(header.get('billing_month') or '')[:7],ln=1)
    pdf.multi_cell(0,6,'Bill To: '+WK_BUYER['name']+' | GSTIN: '+WK_BUYER['gstin']+'\n'+WK_BUYER['address'])
    pdf.ln(5);pdf.multi_cell(0,6,'Description: Consolidated service charges against Indus Towers invoices, as detailed in Annexure A.')
    totals={k:money(sum(money(r.get(k)) for r in items)) for k in ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')}
    for label,k in [('Original Basic','original_basic'),('Less: 2% Discount','discount_amount'),('Taxable Basic','taxable_amount'),('CGST @ 9%','cgst'),('SGST @ 9%','sgst'),('GRAND TOTAL','total_amount')]:
        pdf.set_font('Arial','B' if k=='total_amount' else '',11)
        pdf.cell(115,9,label,border=1);pdf.cell(75,9,f'INR {totals[k]:,.2f}',border=1,align='R',ln=1)
    pdf.ln(8);pdf.set_font('Arial','',9)
    if settings.get('bank_name'):
        pdf.multi_cell(0,5,'Bank: '+str(settings.get('bank_name'))+' | A/C: '+str(settings.get('account_number') or '')+' | IFSC: '+str(settings.get('ifsc') or ''))
    pdf.ln(12);pdf.cell(0,7,'For WHIZ KEY IOT PRIVATE LIMITED',ln=1,align='R');pdf.ln(12);pdf.cell(0,7,'Authorised Signatory',ln=1,align='R')
    pdf.add_page('L');pdf.set_font('Arial','B',13);pdf.cell(0,9,'ANNEXURE A - SITE-WISE INVOICE DETAILS',ln=1)
    cols=[('Project ID',31),('Site ID',26),('Site Name',40),('Invoice No',30),('Date',22),('Basic',20),('2%',16),('Net',20),('CGST',18),('SGST',18),('Total',20)]
    def hdr():
        pdf.set_font('Arial','B',7)
        for label,w in cols: pdf.cell(w,8,label,border=1)
        pdf.ln()
    hdr()
    pdf.set_font('Arial','',7)
    for r in items:
        if pdf.get_y()>180: pdf.add_page('L');hdr();pdf.set_font('Arial','',7)
        vals=[r.get('project_id',''),r.get('site_id',''),r.get('site_name',''),r.get('source_invoice_no',''),r.get('source_invoice_date','')]+[f"{money(r.get(k)):,.2f}" for k in ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')]
        for (label,w),v in zip(cols,vals):pdf.cell(w,7,str(v or '')[:int(w/1.6)],border=1,align='R' if label in ('Basic','2%','Net','CGST','SGST','Total') else 'L')
        pdf.ln()
    if pdf.get_y()>180:pdf.add_page('L');hdr()
    pdf.set_font('Arial','B',7)
    vals=['GRAND TOTAL','','','','']+[f'{totals[k]:,.2f}' for k in ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')]
    for (_,w),v in zip(cols,vals):pdf.cell(w,8,str(v),border=1)
    pdf.ln()
    return bytes(pdf.output(dest='S').encode('latin-1'))

def wk_pager(df,key):
    size=st.selectbox('Rows per page',[25,50,100,200],index=2,key=key+'_size')
    pages=max(1,(len(df)+size-1)//size)
    page=min(st.session_state.get(key+'_page',1),pages)
    a,b,c=st.columns([1,3,1])
    with a:
        if st.button('⬅ Previous',disabled=page<=1,key=key+'_prev'):page-=1
    with b:st.markdown(f'<p style="text-align:center;font-weight:800">Page {page} of {pages} · {len(df)} records</p>',unsafe_allow_html=True)
    with c:
        if st.button('Next ➡',disabled=page>=pages,key=key+'_next'):page+=1
    st.session_state[key+'_page']=page
    return df.iloc[(page-1)*size:page*size]

def wk_show(db):
    st.markdown('## 💎 WHIZ KEY · Consolidated Billing & Ledger')
    st.caption('Seller: WHIZ KEY IOT PRIVATE LIMITED · GSTIN 27AADCW7297D1ZY · Buyer: Bhagyashree Enterprises')
    invoices_tab,pay_tab,settings_tab=st.tabs(['🧾 Invoices','💳 Payment & Ledger','⚙️ Company Settings'])
    with invoices_tab:
        try: headers=wk_fetch_all(db,'wizhkey_invoices')
        except Exception as e:st.error('Run the supplied Wizh Key SQL setup first: '+str(e));return
        df=pd.DataFrame(headers)
        st.markdown('### Created Monthly Invoices')
        q=st.text_input('🔎 Search created invoice',key='wk_search')
        if not df.empty:
            if q:df=df[df.astype(str).apply(lambda c:c.str.contains(q,case=False,regex=False)).any(axis=1)]
            st.dataframe(wk_pager(df.sort_values('id',ascending=False),'wk_inv'),use_container_width=True,hide_index=True)
            b=io.BytesIO();df.to_excel(b,index=False);st.download_button('⬇ Export Invoice Register',b.getvalue(),'WizhKey_Invoices.xlsx')
            choices={f"{r['invoice_no'] or 'DRAFT'} · {r['id']} · {r['status']}":r for r in headers}
            picked=st.selectbox('View / Download Existing Invoice',['Select']+list(choices))
            if picked!='Select':
                h=choices[picked]; items=db.table('wizhkey_invoice_items').select('*').eq('consolidated_invoice_id',h['id']).execute().data or []
                st.download_button('⬇ Download Invoice + Site Annexure PDF',wk_pdf(h,items),'WizhKey_'+str(h.get('invoice_no') or h['id'])+'.pdf',mime='application/pdf')
                if h['status']=='DRAFT':
                    if st.button('✅ Finalize Draft',key='wk_finalize'):
                        if not items:st.error('Cannot finalize an empty invoice')
                        else:
                            db.table('wizhkey_invoices').update({'status':'FINAL','finalized_at':date.today().isoformat()}).eq('id',h['id']).eq('status','DRAFT').execute();st.rerun()
                if h['status']=='FINAL':
                    if st.checkbox('I confirm this bill must be cancelled',key='wk_cancel_check') and st.button('Cancel Final Invoice'):
                        db.table('wizhkey_invoices').update({'status':'CANCELLED'}).eq('id',h['id']).execute();st.rerun()
        else:st.info('No consolidated bills created yet.')
        st.divider();st.markdown('### ➕ Create New Consolidated Invoice')
        try:source,msg=wk_source_rows(db)
        except Exception as e:st.error('Unable to load Bhagyashree Indus invoices: '+str(e));source=[];msg=''
        if msg:st.caption(msg)
        try:
            items=wk_fetch_all(db,'wizhkey_invoice_items');active_ids={h['id'] for h in headers if h['status']!='CANCELLED'}
            billed={(i['source_table'],i['source_invoice_no']) for i in items if i['consolidated_invoice_id'] in active_ids}
        except Exception as e:st.error(str(e));return
        pending=[r for r in source if (r['source_table'],r['source_invoice_no']) not in billed]
        st.metric('Unbilled Indus Invoices',len(pending))
        month=st.date_input('Billing Month (select any date in month)',value=date.today(),key='wk_month')
        inv_date=st.date_input('Wizh Key Invoice Date',value=date.today(),key='wk_date')
        st.caption('All past unbilled source invoices remain eligible, even if their original date is in an earlier month.')
        query=st.text_input('🔎 Search pending invoices by invoice / project / site',key='wk_pending_search')
        visible=[r for r in pending if not query or query.lower() in ' '.join(str(v) for v in r.values()).lower()]
        if visible:
            pending_df=pd.DataFrame(visible)
            st.dataframe(pending_df[['source_invoice_no','source_invoice_date','project_id','site_id','site_name','original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount']],hide_index=True,use_container_width=True)
            choices={f"{r['source_invoice_no']} | {r['site_id']} | INR {r['original_basic']:,.2f}":r for r in visible}
            all_select=st.checkbox('Select All displayed invoices',key='wk_all')
            selected=st.multiselect('Select invoices for consolidated bill',list(choices),default=list(choices) if all_select else [],key='wk_select')
            chosen=[choices[x] for x in selected]
            if chosen:
                st.metric('Selected Invoices',len(chosen));st.metric('Final Total',f"₹{sum(r['total_amount'] for r in chosen):,.2f}")
                draft_header={'invoice_no':'DRAFT','invoice_date':inv_date.isoformat(),'billing_month':month.replace(day=1).isoformat()}
                st.download_button('👁 Preview Invoice PDF',wk_pdf(draft_header,chosen),'WizhKey_Preview.pdf',mime='application/pdf')
                if st.button('💾 Create Draft Consolidated Invoice',type='primary'):
                    if any(not r['project_id'] or not r['site_id'] or not r['site_name'] for r in chosen):
                        st.error('Missing Project ID / Site ID / Site Name. Complete source master before saving.')
                    else:
                        totals={k:float(sum(money(r[k]) for r in chosen)) for k in ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')}
                        payload={'invoice_date':inv_date.isoformat(),'billing_month':month.replace(day=1).isoformat(),'bill_to':WK_BUYER['name'],'discount_percent':2,'status':'DRAFT',**totals}
                        try:
                            h=db.table('wizhkey_invoices').insert(payload).execute().data[0]
                            # Sequence ID ensures uniqueness. Drafts get a number only on creation.
                            number=f"WK/{inv_date.year % 100:02d}-{(inv_date.year+1)%100:02d}/{h['id']:05d}"
                            db.table('wizhkey_invoices').update({'invoice_no':number}).eq('id',h['id']).execute()
                            for r in chosen:
                                try:db.table('wizhkey_invoice_items').insert({'consolidated_invoice_id':h['id'],**r}).execute()
                                except Exception:raise
                            st.success('Draft created: '+number);st.rerun()
                        except Exception as e:
                            if 'h' in locals():
                                try:db.table('wizhkey_invoices').delete().eq('id',h['id']).eq('status','DRAFT').execute()
                                except Exception:pass
                            st.error('Draft not saved completely: '+str(e))
        else:st.info('No matching unbilled invoices. Verify invoice_management workspace and source field mapping.')
    with pay_tab:
        st.markdown('### 💳 Payment Received / Paid')
        try:payments=wk_fetch_all(db,'wizhkey_payments')
        except Exception as e:st.error(str(e));return
        p_df=pd.DataFrame(payments)
        if not p_df.empty:
            p_df=p_df.sort_values(['payment_date','id']);p_df['received']=p_df.apply(lambda r:r['amount'] if r['payment_type']=='RECEIVED' else 0,axis=1);p_df['paid']=p_df.apply(lambda r:r['amount'] if r['payment_type']=='PAID' else 0,axis=1)
            p_df['balance']=(p_df['received']-p_df['paid']).cumsum()
            a,b,c=st.columns(3);a.metric('Received',f"₹{p_df['received'].sum():,.2f}");b.metric('Paid',f"₹{p_df['paid'].sum():,.2f}");c.metric('Net Balance',f"₹{p_df['balance'].iloc[-1]:,.2f}")
            q=st.text_input('🔎 Search payments',key='wk_payment_search')
            shown=p_df[p_df.astype(str).apply(lambda x:x.str.contains(q,case=False,regex=False)).any(axis=1)] if q else p_df
            st.dataframe(wk_pager(shown.iloc[::-1],'wk_pay'),use_container_width=True,hide_index=True)
            b=io.BytesIO();p_df.to_excel(b,index=False);st.download_button('⬇ Download Payment Ledger Excel',b.getvalue(),'WizhKey_Ledger.xlsx')
        else:st.info('No payments recorded.')
        with st.expander('➕ Create New Payment',expanded=False):
            with st.form('wk_new_payment'):
                dt=st.date_input('Payment Date',value=date.today());typ=st.selectbox('Type',['RECEIVED','PAID']);party=st.text_input('Party Name',value=WK_BUYER['name']);amount=st.number_input('Amount',min_value=0.01,step=100.0);mode=st.selectbox('Payment Mode',['BANK TRANSFER','UPI','CHEQUE','CASH','OTHER']);bank=st.text_input('Bank Name');ref=st.text_input('UTR / Reference No.');remarks=st.text_area('Remarks')
                if st.form_submit_button('💾 Save Payment'):
                    try:db.table('wizhkey_payments').insert({'payment_date':dt.isoformat(),'payment_type':typ,'party_name':party,'amount':amount,'payment_mode':mode,'bank_name':bank,'reference_no':ref,'remarks':remarks}).execute();st.success('Payment saved');st.rerun()
                    except Exception as e:st.error(str(e))
        st.caption('This is a date-wise cash ledger. Invoice-wise allocation and receivable aging require allocation entries.')
    with settings_tab:
        st.markdown('### Company & Bank Master')
        st.write(WK_COMPANY)
        try:rows=db.table('wizhkey_company_settings').select('*').eq('company_code','WIZHKEY').execute().data or []
        except Exception as e:st.error(str(e));return
        old=rows[0] if rows else {}
        with st.form('wk_settings'):
            bank=st.text_input('Bank Name',value=old.get('bank_name') or '');account=st.text_input('Account Number',value=old.get('account_number') or '');ifsc=st.text_input('IFSC',value=old.get('ifsc') or '')
            if st.form_submit_button('Save Company Settings'):
                try:db.table('wizhkey_company_settings').upsert({'company_code':'WIZHKEY','legal_name':WK_COMPANY['name'],'address':WK_COMPANY['address'],'gstin':WK_COMPANY['gstin'],'pan':WK_COMPANY['pan'],'state':'Maharashtra','bank_name':bank,'account_number':account,'ifsc':ifsc},on_conflict='company_code').execute();st.success('Saved');st.rerun()
                except Exception as e:st.error(str(e))
