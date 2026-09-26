# =====================================================================
# ✨ SITE DATA — LAVISH TABLE (Quotation page jaisa look)
# ---------------------------------------------------------------------
# ⚠️ YE POORI FILE NAHI HAI — sirf ek hissa hai.
#
# Apni Site Data page file me ye line dhundo:
#       # --- 7. TABLE / CARD DISPLAY ---
# Us line se lekar FILE KE BILKUL END tak ka sab kuch DELETE karo,
# aur uski jagah is file ka saara content paste kar do.
# Upar ka baaki code (imports, dialogs, search, pagination logic) waisa hi rahega.
# =====================================================================

# --- 7. TABLE / CARD DISPLAY (✨ LAVISH STYLE) ---
df_page = df.iloc[start_idx:end_idx].copy()

st.markdown("""
    <style>
    /* ================= KPI STRIP ================= */
    .lux-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 4px 0 22px; }
    @media (max-width: 900px) { .lux-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
    .lux-kpi {
        position: relative; background: #ffffff; border-radius: 16px; padding: 18px 20px 16px;
        border: 1px solid #e0e7ff; overflow: hidden;
        box-shadow: 0 12px 28px -14px rgba(79, 70, 229, 0.35);
        transition: transform .25s ease, box-shadow .25s ease;
    }
    .lux-kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 34px -14px rgba(79, 70, 229, 0.45); }
    .lux-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--accent); }
    .lux-kpi-icon {
        position: absolute; right: 16px; top: 16px; width: 42px; height: 42px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center; font-size: 1.3rem; background: var(--soft);
    }
    .lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; }
    .lux-kpi-value { font-size: 1.65rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

    /* ================= TABLE TITLE BAR ================= */
    .slux-head-bar {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 16px 22px; border-radius: 18px 18px 0 0;
        background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
    }
    .slux-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
    .slux-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
    .slux-badge {
        background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
        padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
    }

    /* ================= SCROLLING TABLE BODY ================= */
    .st-key-site_lux_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important;
        border-radius: 0 !important;
    }
    .st-key-site_lux_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-site_lux_wrap [data-testid="stHorizontalBlock"] {
        min-width: 4600px !important; flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important;
    }
    .st-key-site_lux_wrap [data-testid="stColumn"],
    .st-key-site_lux_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }

    /* Sticky header row */
    .st-key-slux_head {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important;
        padding: 13px 0 !important; min-width: 4600px !important;
    }
    .st-key-slux_head [data-testid="stColumn"], .st-key-slux_head [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }

    /* Data rows */
    div[class*="st-key-sluxrow_"] {
        padding: 9px 0 !important; min-width: 4600px !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-sluxrow_odd"] { background: #fafaff; }
    div[class*="st-key-sluxrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-sluxrow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .86rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
    .slux-strong { font-weight: 700; color: #0f172a; }
    .slux-soft { color: #475569; font-weight: 600; }
    .slux-muted { color: #cbd5e1; }
    .slux-num {
        display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
        align-items: center; justify-content: center;
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
        font-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
    }
    .slux-chip {
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
        padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
    }
    .slux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
    .slux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }

    /* Status pills (table + mobile cards) */
    .status-badge {
        display: inline-flex !important; align-items: center; gap: 6px;
        padding: 4px 11px !important; border-radius: 999px !important; border: 1px solid transparent;
        font-size: .7rem !important; font-weight: 800 !important; letter-spacing: .4px; white-space: nowrap;
    }
    .status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
    .status-green  { background: #dcfce7 !important; color: #15803d !important; border-color: #bbf7d0 !important; }
    .status-blue   { background: #dbeafe !important; color: #1d4ed8 !important; border-color: #bfdbfe !important; }
    .status-yellow { background: #fef9c3 !important; color: #a16207 !important; border-color: #fde68a !important; }
    .status-red    { background: #fee2e2 !important; color: #b91c1c !important; border-color: #fecaca !important; }
    .status-grey   { background: #f1f5f9 !important; color: #475569 !important; border-color: #e2e8f0 !important; }

    /* Inline action buttons: ⚙️ Manage (blue) + 📦 Material (purple) */
    .st-key-site_lux_wrap div[class*="st-key-mgrbtn_"] button,
    .st-key-site_lux_wrap div[class*="st-key-mbtn_"] button {
        width: 38px !important; max-width: 38px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        box-shadow: none !important; font-size: 1rem !important; transition: all .2s ease !important;
    }
    .st-key-site_lux_wrap div[class*="st-key-mgrbtn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
    .st-key-site_lux_wrap div[class*="st-key-mgrbtn_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    .st-key-site_lux_wrap div[class*="st-key-mbtn_"] button { background: rgba(168,85,247,0.15) !important; border: 1px solid rgba(168,85,247,0.3) !important; }
    .st-key-site_lux_wrap div[class*="st-key-mbtn_"] button:hover {
        background: #a855f7 !important; border-color: #c084fc !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(168,85,247,.6) !important;
    }

    /* Footer bar */
    .slux-foot {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
        font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .slux-foot small { color: #6366f1; font-weight: 700; letter-spacing: .5px; margin-left: 10px; text-transform: none; font-size: .8rem; }
    .slux-foot-badge {
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 5px 14px;
        border-radius: 999px; font-size: .75rem; letter-spacing: .5px;
    }

    /* Empty state */
    .slux-empty {
        background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
        text-align: center; color: #64748b; font-weight: 600;
    }
    .slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }

    /* Pager */
    .st-key-slux_pager .page-count { color: #4338ca !important; font-weight: 800 !important; font-size: .95rem !important; }
    .st-key-slux_pager [data-testid="stNumberInput"] input { text-align: center; font-weight: 800; color: #312e81; }

    /* Mobile cards — slightly richer */
    .site-card-title { color: #312e81 !important; }
    </style>
""", unsafe_allow_html=True)


def status_badge(val):
    v = str(val).strip()
    if not v or v.lower() in ("nan", "none", "-"):
        return "<span class='slux-muted'>—</span>"
    vl = v.lower()
    if vl == "not required":
        cls = "status-grey"
    elif "not" in vl and ("received" in vl or "available" in vl):
        cls = "status-red"
    elif any(k in vl for k in ["completed", "approved", "done", "available"]):
        cls = "status-green"
    elif any(k in vl for k in ["hold", "progress"]):
        cls = "status-blue"
    elif any(k in vl for k in ["pending", "awaiting", "required"]):
        cls = "status-yellow"
    elif any(k in vl for k in ["cancel", "reject"]):
        cls = "status-red"
    else:
        cls = "status-grey"
    return f"<span class='status-badge {cls}'>{escape(v)}</span>"


def _clean(v):
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("nan", "none", "null", "-") else s


def _txt(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell {extra_cls}' title='{escape(s)}'>{escape(s)}</div>"


def _chip(v, extra_cls=""):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell'><span class='slux-chip {extra_cls}'>{escape(s)}</span></div>"


def _pill(v):
    s = _clean(v)
    if not s:
        return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"
    return f"<div class='slux-cell'><span class='slux-pill'>{escape(s)}</span></div>"


# ---------------- KPI STRIP (filtered data par based) ----------------
def _col_series(col):
    return df[col].astype(str).str.strip().str.lower() if col in df.columns else pd.Series([], dtype=str)

kpi_total = len(df)
kpi_completed = int(_col_series("Site Status").str.contains("complet", na=False).sum())
_po_series = _col_series("PO No.")
kpi_po = int((~_po_series.isin(["", "nan", "none", "null", "-"])).sum())
kpi_bill_pending = int(_col_series("Vision Billing Status").str.contains("pending", na=False).sum())
kpi_filter_note = "Filtered results" if (search_query or selected_team_filter != "All Teams") else "All records"

st.markdown(
    '<div class="lux-kpi-grid">'
    '<div class="lux-kpi" style="--accent:linear-gradient(90deg,#6366f1,#8b5cf6);--soft:#eef2ff;">'
    '<div class="lux-kpi-icon">🏗️</div><div class="lux-kpi-label">Total Sites</div>'
    f'<div class="lux-kpi-value">{kpi_total:,}</div><div class="lux-kpi-foot">{kpi_filter_note}</div></div>'
    '<div class="lux-kpi" style="--accent:linear-gradient(90deg,#10b981,#14b8a6);--soft:#ecfdf5;">'
    '<div class="lux-kpi-icon">✅</div><div class="lux-kpi-label">Completed</div>'
    f'<div class="lux-kpi-value">{kpi_completed:,}</div><div class="lux-kpi-foot">Site Status = Completed</div></div>'
    '<div class="lux-kpi" style="--accent:linear-gradient(90deg,#f59e0b,#f97316);--soft:#fffbeb;">'
    '<div class="lux-kpi-icon">🧾</div><div class="lux-kpi-label">PO Received</div>'
    f'<div class="lux-kpi-value">{kpi_po:,}</div><div class="lux-kpi-foot">{max(kpi_total - kpi_po, 0):,} without PO No.</div></div>'
    '<div class="lux-kpi" style="--accent:linear-gradient(90deg,#ec4899,#a855f7);--soft:#fdf2f8;">'
    '<div class="lux-kpi-icon">💼</div><div class="lux-kpi-label">Vision Billing Pending</div>'
    f'<div class="lux-kpi-value">{kpi_bill_pending:,}</div><div class="lux-kpi-foot">Awaiting billing</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

if df_page.empty:
    st.markdown(
        '<div class="slux-empty"><div>🗂️</div>'
        f'{"No records match your search / team filter." if (search_query or selected_team_filter != "All Teams") else "No site records yet. Click ➕ Add Record to create one."}'
        '</div>',
        unsafe_allow_html=True,
    )

elif st.session_state.site_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE-FRIENDLY CARD VIEW - one card per record, no horizontal scroll
    # ---------------------------------------------------------------
    for page_pos, (_, row) in enumerate(df_page.iterrows()):
        row_dict = row.to_dict()
        rid = row_dict.get("id")
        serial_no = start_idx + page_pos + 1
        is_wh_required = str(row_dict.get("WH Material", "")).strip().lower() == "required"

        with st.container(border=True):
            st.markdown(f"""
                <div class="site-card-title">#{serial_no} — {row_dict.get('Site ID','') or '-'} | {row_dict.get('Site Name','') or '-'}</div>
                <div class="site-card-sub">{row_dict.get('Project ID','') or '-'} • {row_dict.get('Cluster','') or '-'}</div>
                <div class="site-card-row"><span class="site-card-label">Site Status</span><span class="site-card-value">{status_badge(row_dict.get('Site Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Operator</span><span class="site-card-value">{row_dict.get('Operator','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">Project Name</span><span class="site-card-value">{row_dict.get('Project Name','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">Team Name</span><span class="site-card-value">{row_dict.get('Team Name','') or '-'}</span></div>
                <div class="site-card-row"><span class="site-card-label">Photos</span><span class="site-card-value">{status_badge(row_dict.get('Photos',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Audit</span><span class="site-card-value">{status_badge(row_dict.get('Audit',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">JMS</span><span class="site-card-value">{status_badge(row_dict.get('JMS',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Commissioning Report</span><span class="site-card-value">{status_badge(row_dict.get('Commissioning Report',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">PO Status</span><span class="site-card-value">{status_badge(row_dict.get('PO Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Team Billing</span><span class="site-card-value">{status_badge(row_dict.get('Team Billing Status',''))}</span></div>
                <div class="site-card-row"><span class="site-card-label">Vision Billing</span><span class="site-card-value">{status_badge(row_dict.get('Vision Billing Status',''))}</span></div>
            """, unsafe_allow_html=True)

            if is_wh_required:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("⚙️ Manage", key=f"card_mgr_{rid}", use_container_width=True):
                        if 'edit_po_count' in st.session_state:
                            del st.session_state['edit_po_count']
                        edit_record_dialog(row_dict)
                with bc2:
                    if st.button("📦 Material", key=f"card_mat_{rid}", use_container_width=True):
                        if 'mat_count' in st.session_state:
                            st.session_state.mat_count = 1
                        material_movement_dialog(row_dict)
            else:
                if st.button("⚙️ Manage", key=f"card_mgr_{rid}", use_container_width=True):
                    if 'edit_po_count' in st.session_state:
                        del st.session_state['edit_po_count']
                    edit_record_dialog(row_dict)

else:
    # ---------------------------------------------------------------
    # ✨ LAVISH DESKTOP TABLE VIEW (wide, horizontal + vertical scroll)
    # ---------------------------------------------------------------
    COL_RATIOS = [
        0.45, 0.4, 0.4,              # 0-2 (Sr No, Manage, Material)
        1.2, 1.0, 1.5, 1.3, 1.1,     # Dept, Op, Proj Name, Proj ID, Site ID
        1.6, 1.1, 1.2, 1.2, 1.0,     # Site Name, Cluster, Status, PO No, PO Date
        1.0, 1.3, 1.0, 1.2, 2.0,     # PO Status, PO Upload Status, Product, RFAI, Work Desc
        1.0, 1.2,                    # WH Mat, Team Name
        1.0, 1.0, 1.0, 1.3,          # Photos, Audit, JMS, Commissioning Report
        1.2, 1.2, 1.0,               # Team Bill, Vis Bill, Extra App
        1.2, 1.0                     # WCC Number, WCC Status
    ]

    COL_LABELS = [
        "#", "⚙️", "📦",
        "DEPARTMENT", "OPERATOR", "PROJECT NAME", "PROJECT ID", "SITE ID",
        "SITE NAME", "CLUSTER", "SITE STATUS", "PO NO.", "PO DATE",
        "PO STATUS", "PO UPLOAD STATUS", "PRODUCT", "RFAI STATUS", "WORK DESCRIPTION",
        "WH MATERIAL", "TEAM NAME", "PHOTOS", "AUDIT", "JMS", "COMMISSIONING REPORT",
        "TEAM BILLING STATUS", "VISION BILLING STATUS", "EXTRA APPROVAL",
        "WCC NUMBER", "WCC STATUS"
    ]

    # ---- Title bar ----
    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">🏗️ Site Register<span>newest first • scroll right for more columns →</span></div>'
        f'<div class="slux-badge">Page {st.session_state.current_page} / {total_pages}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="site_lux_wrap", height=560):
        # --- PRE-FETCH PO UPLOAD AVAILABILITY FOR CURRENT PAGE ITEMS ---
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        project_ids_on_page = [str(x).strip() for x in df_page['Project ID'].unique() if str(x).strip() and str(x).strip() != '-']
        site_ids_on_page = [str(x).strip() for x in df_page['Site ID'].unique() if str(x).strip() and str(x).strip() != '-']

        uploaded_po_identifiers = fetch_po_upload_identifiers_cached(active_ws) if (project_ids_on_page or site_ids_on_page) else set()

        # --- HEADER ROW (sticky) ---
        with st.container(key="slux_head"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for h_idx, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                center_cls = " c" if h_idx < 3 else ""
                h_col.markdown(f"<div class='slux-th{center_cls}'>{label}</div>", unsafe_allow_html=True)

        # --- DATA ROWS ---
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            serial_no = start_idx + page_pos + 1
            row_key = rid if (rid is not None and str(rid).strip() not in ("", "nan", "None")) else f"s{serial_no}"
            is_wh_required = str(row_dict.get("WH Material", "")).strip().lower() == "required"

            proj_id_val = str(row_dict.get("Project ID", "")).strip()
            site_id_val = str(row_dict.get("Site ID", "")).strip()

            if (proj_id_val and proj_id_val in uploaded_po_identifiers) or (site_id_val and site_id_val in uploaded_po_identifiers):
                po_upload_status_html = "<span class='status-badge status-green'>Available</span>"
            else:
                po_upload_status_html = "<span class='status-badge status-yellow'>Pending</span>"

            parity = "odd" if serial_no % 2 else "even"
            with st.container(key=f"sluxrow_{parity}_{row_key}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")

                rcols[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)

                with rcols[1]:
                    if st.button("⚙️", key=f"mgrbtn_{row_key}", help="Manage (View/Edit/Delete)"):
                        if 'edit_po_count' in st.session_state:
                            del st.session_state['edit_po_count']
                        edit_record_dialog(row_dict)
                with rcols[2]:
                    if is_wh_required:
                        if st.button("📦", key=f"mbtn_{row_key}", help="Material"):
                            if 'mat_count' in st.session_state:
                                st.session_state.mat_count = 1
                            material_movement_dialog(row_dict)
                    else:
                        st.markdown("<div style='text-align:center;'><span class='slux-muted'>—</span></div>", unsafe_allow_html=True)

                rcols[3].markdown(_txt(row_dict.get('Department'), "slux-soft"), unsafe_allow_html=True)
                rcols[4].markdown(_txt(row_dict.get('Operator'), "slux-soft"), unsafe_allow_html=True)
                rcols[5].markdown(_txt(row_dict.get('Project Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[6].markdown(_chip(row_dict.get('Project ID'), "proj"), unsafe_allow_html=True)
                rcols[7].markdown(_chip(row_dict.get('Site ID')), unsafe_allow_html=True)
                rcols[8].markdown(_txt(row_dict.get('Site Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[9].markdown(_pill(row_dict.get('Cluster')), unsafe_allow_html=True)
                rcols[10].markdown(status_badge(row_dict.get('Site Status', '')), unsafe_allow_html=True)
                rcols[11].markdown(_chip(row_dict.get('PO No.')), unsafe_allow_html=True)
                rcols[12].markdown(_txt(row_dict.get('PO Date'), "slux-soft"), unsafe_allow_html=True)
                rcols[13].markdown(status_badge(row_dict.get('PO Status', '')), unsafe_allow_html=True)
                rcols[14].markdown(po_upload_status_html, unsafe_allow_html=True)
                rcols[15].markdown(_txt(row_dict.get('Product')), unsafe_allow_html=True)
                rcols[16].markdown(status_badge(row_dict.get('RFAI Status', '')), unsafe_allow_html=True)
                rcols[17].markdown(_txt(row_dict.get('Work Description'), "slux-soft"), unsafe_allow_html=True)
                rcols[18].markdown(status_badge(row_dict.get('WH Material', '')), unsafe_allow_html=True)
                rcols[19].markdown(_txt(row_dict.get('Team Name'), "slux-strong"), unsafe_allow_html=True)
                rcols[20].markdown(status_badge(row_dict.get('Photos', '')), unsafe_allow_html=True)
                rcols[21].markdown(status_badge(row_dict.get('Audit', '')), unsafe_allow_html=True)
                rcols[22].markdown(status_badge(row_dict.get('JMS', '')), unsafe_allow_html=True)
                rcols[23].markdown(status_badge(row_dict.get('Commissioning Report', '')), unsafe_allow_html=True)
                rcols[24].markdown(status_badge(row_dict.get('Team Billing Status', '')), unsafe_allow_html=True)
                rcols[25].markdown(status_badge(row_dict.get('Vision Billing Status', '')), unsafe_allow_html=True)
                rcols[26].markdown(status_badge(row_dict.get('Extra Approval', '')), unsafe_allow_html=True)
                rcols[27].markdown(_chip(row_dict.get('WCC Number')), unsafe_allow_html=True)
                rcols[28].markdown(status_badge(row_dict.get('WCC Status', '')), unsafe_allow_html=True)

    # ---- Footer bar ----
    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    st.markdown(
        '<div class="slux-foot">'
        f'<div>Total {total_rows:,} site record{"s" if total_rows != 1 else ""}'
        f'<small>Showing {shown_from}–{shown_to}</small></div>'
        f'<div class="slux-foot-badge">Page {st.session_state.current_page} of {total_pages}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS (with Go-To-Page box) ---
with st.container(key="slux_pager"):
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page -= 1
            st.rerun()

    with col_p2:
        jc1, jc2, jc3 = st.columns([2, 1.3, 2])
        with jc2:
            page_input = st.number_input(
                "Go to page",
                min_value=1,
                max_value=total_pages,
                step=1,
                key="page_jump_input",
                label_visibility="collapsed"
            )
        st.markdown(f"<div class='page-count'>Page {st.session_state.current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)
        if page_input != st.session_state.current_page:
            st.session_state.current_page = int(page_input)
            st.rerun()

    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages)):
            st.session_state.current_page += 1
            st.rerun()
