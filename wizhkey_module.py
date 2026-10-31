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
    result = pdf.output(dest='S')
    return bytes(result) if isinstance(result, (bytes, bytearray)) else result.encode('latin-1')

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
    st.markdown('''
    <style>
    div[data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"],
    div[data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"] {
        min-height: 78px;
        border-radius: 16px;
        font-size: 1.12rem;
        font-weight: 850;
        border: 1px solid #dbe2ee;
        box-shadow: 0 5px 13px rgba(27, 39, 70, 0.10);
        width: 100%;
    }
    </style>
    ''', unsafe_allow_html=True)
    options = [('invoices', '🧾 INVOICES'), ('payment', '💳 PAYMENT & LEDGER'), ('settings', '⚙️ COMPANY SETTINGS')]
    if st.session_state.get('wk_active_section') not in dict(options):
        st.session_state['wk_active_section'] = 'invoices'
    nav_cols = st.columns(3, gap='medium')
    for nav_col, (section_id, section_label) in zip(nav_cols, options):
        with nav_col:
            if st.button(section_label, key='wk_nav_' + section_id,
                         type='primary' if st.session_state['wk_active_section'] == section_id else 'secondary',
                         use_container_width=True):
                st.session_state['wk_active_section'] = section_id
                st.rerun()
    st.divider()
    if st.session_state['wk_active_section'] == 'invoices':
        st.markdown("""<style>
        .wk-hero{padding:18px 24px;border-radius:18px;background:linear-gradient(105deg,#eef2ff,#e0f2fe,#faf5ff);border:1px solid #c7d2fe;margin:12px 0 18px}
        .wk-hero h3{margin:0;color:#312e81;font-weight:900}.wk-hero p{margin:6px 0 0;color:#475569}
        div[data-testid="stMetric"]{background:white;border:1px solid #dbeafe;border-radius:16px;padding:12px 18px;box-shadow:0 5px 18px #c7d2fe55}
        </style>""",unsafe_allow_html=True)
        try:
            headers=wk_fetch_all(db,'wizhkey_invoices')
            items=wk_fetch_all(db,'wizhkey_invoice_items')
            source,msg=wk_source_rows(db)
        except Exception as e:
            st.error('Could not load Wizh Key data: '+str(e));return
        active={h['id']:h for h in headers if h['status']!='CANCELLED'}
        billed={(i['source_table'],i['source_invoice_no']):i for i in items if i['consolidated_invoice_id'] in active}
        pending=sorted([r for r in source if (r['source_table'],r['source_invoice_no']) not in billed], key=lambda r: (r.get('source_invoice_date') or '', r['source_invoice_no']), reverse=True)
        created=[]
        for i in items:
            h=active.get(i['consolidated_invoice_id'])
            if h:
                created.append(dict(source_invoice_no=i['source_invoice_no'],source_invoice_date=i.get('source_invoice_date'),project_id=i.get('project_id'),site_id=i.get('site_id'),site_name=i.get('site_name'),original_basic=i.get('original_basic'),discount_amount=i.get('discount_amount'),taxable_amount=i.get('taxable_amount'),cgst=i.get('cgst'),sgst=i.get('sgst'),total_amount=i.get('total_amount'),wizhkey_invoice_no=h.get('invoice_no'),wizhkey_invoice_date=h.get('invoice_date'),status=h.get('status'),bill_id=h['id']))
        st.markdown('<div class="wk-hero"><h3>🧾 Wizh Key · Consolidated Invoice Management</h3><p>Pending original invoices remain available until billed. Each source invoice is billed only once.</p></div>',unsafe_allow_html=True)
        t1,t2,t3,t4=st.columns(4)
        t1.metric('🟠 Pending Invoices',len(pending));t2.metric('🟢 Created Source Invoices',len(created))
        t3.metric('📑 Consolidated Bills',len(active));t4.metric('💰 Pending Basic',f"₹{sum(r['original_basic'] for r in pending):,.2f}")
        if st.session_state.pop('wk_last_created_invoice', None):
            st.success('Consolidated Invoice created successfully. Check the Created tab.')
        sub=st.radio('Invoice Register',['🟠 Pending','🟢 Created'],horizontal=True,key='wk_invoice_subtab',label_visibility='collapsed')
        if sub=='🟠 Pending':
            st.markdown('### 🟠 Pending Indus Invoices')
            if msg:st.caption(msg)
            inv_date=st.date_input('Wizh Key Invoice Date',value=date.today(),key='wk_date')
            query=st.text_input('🔎 Search Invoice / Project ID / Site ID / Site Name',key='wk_pending_search')
            visible=[r for r in pending if not query or query.lower() in ' '.join(str(v) for v in r.values()).lower()]
            if not visible:st.info('No pending invoices match the search.');return
            selected_keys=set(st.session_state.get('wk_selected_keys',[])) & {r['source_invoice_no'] for r in pending}
            b1,b2,b3=st.columns([1,1,4])
            if b1.button('☑ Select All Filtered',key='wk_all_filtered'):
                selected_keys.update(r['source_invoice_no'] for r in visible)
                st.session_state['wk_editor_rev']=st.session_state.get('wk_editor_rev',0)+1
            if b2.button('✖ Clear Selection',key='wk_clear_selected'):
                selected_keys.clear()
                st.session_state['wk_editor_rev']=st.session_state.get('wk_editor_rev',0)+1
            st.session_state['wk_selected_keys']=list(selected_keys)
            cols=['source_invoice_no','source_invoice_date','project_id','site_id','site_name','original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount']
            size=st.selectbox('Rows per page',[25,50,100,200],index=2,key='wk_pending_size')
            pages=max(1,(len(visible)+size-1)//size)
            page=min(st.session_state.get('wk_pending_page',1),pages)
            pg1,pg2,pg3=st.columns([1,3,1])
            if pg1.button('⬅ Previous',disabled=page<=1,key='wk_pending_prev'):page-=1
            pg2.markdown(f'<p style="text-align:center;font-weight:800">Page {page} of {pages} · {len(visible)} matching</p>',unsafe_allow_html=True)
            if pg3.button('Next ➡',disabled=page>=pages,key='wk_pending_next'):page+=1
            st.session_state['wk_pending_page']=page
            page_rows=visible[(page-1)*size:page*size]
            display=pd.DataFrame([{'Select':r['source_invoice_no'] in selected_keys,**{k:r.get(k) for k in cols}} for r in page_rows])
            edited=st.data_editor(display,hide_index=True,use_container_width=True,key='wk_editor_'+str(page)+'_'+str(st.session_state.get('wk_editor_rev',0)),disabled=cols,column_config={'Select':st.column_config.CheckboxColumn('Select',width='small')},height=min(560,40+35*len(display)))
            for j,r in enumerate(page_rows):
                if bool(edited.iloc[j]['Select']):selected_keys.add(r['source_invoice_no'])
                else:selected_keys.discard(r['source_invoice_no'])
            st.session_state['wk_selected_keys']=list(selected_keys)
            chosen=[r for r in pending if r['source_invoice_no'] in selected_keys]
            s1,s2,s3,s4=st.columns(4)
            s1.metric('Selected',len(chosen));s2.metric('Original Basic',f"₹{sum(r['original_basic'] for r in chosen):,.2f}")
            s3.metric('2% Deduction',f"₹{sum(r['discount_amount'] for r in chosen):,.2f}")
            s4.metric('Final Amount incl. GST',f"₹{sum(r['total_amount'] for r in chosen):,.2f}")
            if chosen:
                draft_header={'invoice_no':'PREVIEW','invoice_date':inv_date.isoformat()}
                left,right=st.columns([1,2])
                left.download_button('👁 Preview Selected PDF',wk_pdf(draft_header,chosen),'WizhKey_Preview.pdf',mime='application/pdf',use_container_width=True)
                if right.button('💾 Create Consolidated Invoice',type='primary',use_container_width=True,key='wk_create'):
                    if any(not r['project_id'] or not r['site_id'] or not r['site_name'] for r in chosen):
                        st.error('Some selected invoices are missing Project ID, Site ID or Site Name. Correct the master first.')
                    else:
                        totals={k:float(sum(money(r[k]) for r in chosen)) for k in ('original_basic','discount_amount','taxable_amount','cgst','sgst','total_amount')}
                        payload={'invoice_date':inv_date.isoformat(),'billing_month':inv_date.replace(day=1).isoformat(),'bill_to':WK_BUYER['name'],'discount_percent':2,'status':'FINAL',**totals}
                        try:
                            response=db.rpc('wk_create_consolidated_invoice',{'p_header':payload,'p_items':chosen}).execute()
                            result=response.data or {}
                            st.session_state['wk_selected_keys']=[]
                            st.session_state['wk_last_created_invoice'] = str(result.get('invoice_no') if isinstance(result,dict) else result)
                            st.session_state['wk_invoice_subtab'] = '🟢 Created'
                            st.rerun()
                        except Exception as e:st.error('Invoice not created. Check SQL upgrade and data: '+str(e))
            else:st.info('Select invoice rows using the checkboxes to enable invoice creation.')
        else:
            st.markdown('### 🟢 Created · Original Invoice Register')
            search=st.text_input('🔎 Search Wizh Key Invoice No / Indus Invoice No / Project / Site',key='wk_created_search')
            rows=[r for r in created if not search or search.lower() in ' '.join(str(v) for v in r.values()).lower()]
            if rows:
                df=pd.DataFrame(rows).sort_values(['bill_id','source_invoice_no'],ascending=[False,True])
                st.dataframe(wk_pager(df,'wk_created'),use_container_width=True,hide_index=True)
                out=io.BytesIO();df.to_excel(out,index=False)
                st.download_button('⬇ Export Created Register',out.getvalue(),'WizhKey_Created_Invoices.xlsx')
            else:st.info('No created invoices yet.')
            if active:
                st.markdown('#### 📄 Download Consolidated Invoice + Annexure')
                options={f"{h['invoice_no']} · {h['invoice_date']} · {h['status']}":h for h in sorted(active.values(),key=lambda x:x['id'],reverse=True)}
                key=st.selectbox('Select Wizh Key Invoice',['Select']+list(options),key='wk_created_choose')
                if key!='Select':
                    h=options[key];rows_for_pdf=[i for i in items if i['consolidated_invoice_id']==h['id']]
                    st.download_button('⬇ Download Invoice PDF',wk_pdf(h,rows_for_pdf),f"{h['invoice_no']}.pdf",mime='application/pdf')
                    if h['status']=='DRAFT':
                        if st.button('✅ Finalize Draft',key='wk_finalize'):
                            db.table('wizhkey_invoices').update({'status':'FINAL','finalized_at':date.today().isoformat()}).eq('id',h['id']).eq('status','DRAFT').execute();st.rerun()
                    if h['status']=='FINAL':
                        if st.checkbox('I confirm this bill should be cancelled',key='wk_cancel_confirm') and st.button('Cancel Consolidated Invoice',key='wk_cancel'):
                            db.table('wizhkey_invoices').update({'status':'CANCELLED'}).eq('id',h['id']).execute();st.rerun()
    if st.session_state['wk_active_section'] == 'payment':
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
    if st.session_state['wk_active_section'] == 'settings':
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
