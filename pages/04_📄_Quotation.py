# =====================================================================
# STEP 1: File ke top par imports me ye line add karo
# =====================================================================
import html


# =====================================================================
# STEP 2: Apne existing <style> block me, "</style>" se theek PEHLE
#         ye pura CSS paste karo
# =====================================================================
LAVISH_TABLE_CSS = """
    /* ================= LAVISH KPI STRIP ================= */
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
        display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
        background: var(--soft);
    }
    .lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; }
    .lux-kpi-value { font-size: 1.65rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

    /* ================= LAVISH TABLE ================= */
    .lux-table-wrap {
        background: #ffffff; border-radius: 18px; border: 1px solid #e0e7ff; overflow: hidden;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
    }
    .lux-table-head {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 16px 22px;
        background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
    }
    .lux-table-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
    .lux-table-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
    .lux-table-badge {
        background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
        padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
    }
    .lux-scroll { max-height: 560px; overflow: auto; }
    table.lux-table { width: 100%; min-width: 980px; border-collapse: separate; border-spacing: 0; font-size: .88rem; }
    .lux-table thead th {
        position: sticky; top: 0; z-index: 2;
        background: #eef2ff; color: #3730a3;
        font-size: .7rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase;
        padding: 13px 14px; text-align: left; white-space: nowrap;
        border-bottom: 2px solid #c7d2fe;
    }
    .lux-table thead th.r, .lux-table td.r { text-align: right; }
    .lux-table thead th.c, .lux-table td.c { text-align: center; }
    .lux-table tbody td {
        padding: 12px 14px; color: #1e293b; vertical-align: middle;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease;
    }
    .lux-table tbody tr:nth-child(even) td { background: #fafaff; }
    .lux-table tbody tr:hover td { background: #eef2ff; }
    .lux-table tbody tr:hover td:first-child { box-shadow: inset 4px 0 0 #6366f1; }

    .lux-num {
        display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
        align-items: center; justify-content: center;
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
        font-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
    }
    .lux-date { font-weight: 800; color: #0f172a; white-space: nowrap; }
    .lux-date small { display: block; color: #94a3b8; font-weight: 600; font-size: .7rem; letter-spacing: .5px; }
    .lux-chip {
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
        padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
    }
    .lux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
    .lux-site { font-weight: 700; color: #0f172a; }
    .lux-pill {
        display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap;
        background: linear-gradient(90deg, #e0f2fe, #ede9fe); color: #4338ca;
        border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
    }
    .lux-proj { color: #475569; font-weight: 600; }
    .lux-amt { font-weight: 900; color: #4f46e5; white-space: nowrap; font-size: .95rem; }
    .lux-muted { color: #cbd5e1; }

    .lux-table tfoot td {
        position: sticky; bottom: 0; z-index: 2;
        background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border-top: 2px solid #c7d2fe; padding: 14px; font-weight: 900; color: #312e81;
        text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .lux-table tfoot td.r { font-size: 1.05rem; color: #4f46e5; letter-spacing: 0; }

    .lux-empty { padding: 48px 20px; text-align: center; color: #64748b; font-weight: 600; }
    .lux-empty div { font-size: 2.4rem; margin-bottom: 8px; }

    /* ================= ACTION BAR ================= */
    .lux-action-title {
        margin: 22px 0 8px; font-size: .78rem; font-weight: 800; letter-spacing: 1.2px;
        text-transform: uppercase; color: #4338ca; display: flex; align-items: center; gap: 8px;
    }
    .lux-action-title::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, #c7d2fe, transparent); }
"""
# Agar direct paste karna hai to upar ka CSS (triple quotes ke andar wala)
# copy karke apne st.markdown("""<style> ... </style>""") me </style> se
# pehle daal do. Ye Python variable sirf reference ke liye hai.


# =====================================================================
# STEP 3: "# --- 8. MAIN SCREEN QUOTATION LIST ..." se lekar FILE KE END
#         tak ka pura purana code DELETE karke ye paste karo
# =====================================================================

# --- 8. MAIN SCREEN QUOTATION LIST (lavish table or mobile cards) ---
df_display = st.session_state.quotations_df.copy()

# Newest quotations sabse upar
if not df_display.empty:
    if "id" in df_display.columns:
        df_display = df_display.sort_values(by="id", ascending=False).reset_index(drop=True)
    else:
        df_display = df_display.iloc[::-1].reset_index(drop=True)

if not df_display.empty and search_q:
    mask = df_display.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
    # FIX: reset_index zaroori hai, warna search ke baad galat row select/delete hoti thi
    df_display = df_display[mask].reset_index(drop=True)

disp_cols = ["Date", "Project ID", "Site ID", "Site Name", "Cluster", "Project Name", "Quotation Amount"]
for c in disp_cols + ["Quotation Name"]:
    if c not in df_display.columns:
        df_display[c] = ""


def _esc(v):
    """HTML-safe text; blank / NaN ko '—' dikhata hai."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan", "None"):
        return '<span class="lux-muted">—</span>'
    return html.escape(str(v))


def _amt(v):
    try:
        return f"₹ {int(float(v)):,}"
    except Exception:
        return "₹ 0"


def _delete_quotation(q_name):
    try:
        supabase.table("quotations").delete().eq("Quotation Name", q_name).execute()
        supabase.table("quotation_items").delete().eq("Quotation Name", q_name).execute()
        fetch_quotations_cached.clear()
        st.session_state.quotations_df = fetch_quotations()
        st.toast(f"✅ Deleted {q_name}")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting: {e}")


# ---------------- KPI STRIP (dono views me dikhega) ----------------
amounts = pd.to_numeric(df_display["Quotation Amount"], errors="coerce").fillna(0)
dates = pd.to_datetime(df_display["Date"], errors="coerce")
today = pd.Timestamp(datetime.date.today())
this_month = int(((dates.dt.year == today.year) & (dates.dt.month == today.month)).sum())
total_count = len(df_display)
total_value = int(amounts.sum())
avg_value = int(amounts.mean()) if total_count else 0
cluster_count = df_display["Cluster"].replace("", pd.NA).dropna().nunique()

st.markdown(
    '<div class="lux-kpi-grid">'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#6366f1,#8b5cf6);--soft:#eef2ff;">'
    f'<div class="lux-kpi-icon">📄</div><div class="lux-kpi-label">Total Quotations</div>'
    f'<div class="lux-kpi-value">{total_count:,}</div><div class="lux-kpi-foot">{"Filtered results" if search_q else "All records"}</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#10b981,#14b8a6);--soft:#ecfdf5;">'
    f'<div class="lux-kpi-icon">💰</div><div class="lux-kpi-label">Total Value</div>'
    f'<div class="lux-kpi-value">₹ {total_value:,}</div><div class="lux-kpi-foot">Sum of grand totals</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#f59e0b,#f97316);--soft:#fffbeb;">'
    f'<div class="lux-kpi-icon">📊</div><div class="lux-kpi-label">Average Quotation</div>'
    f'<div class="lux-kpi-value">₹ {avg_value:,}</div><div class="lux-kpi-foot">Per quotation</div></div>'
    f'<div class="lux-kpi" style="--accent:linear-gradient(90deg,#ec4899,#a855f7);--soft:#fdf2f8;">'
    f'<div class="lux-kpi-icon">🗓️</div><div class="lux-kpi-label">This Month</div>'
    f'<div class="lux-kpi-value">{this_month:,}</div><div class="lux-kpi-foot">{cluster_count} active clusters</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

if st.session_state.quo_view_mode == "cards":
    # ---------------------------------------------------------------
    # MOBILE CARD VIEW (same as before)
    # ---------------------------------------------------------------
    if df_display.empty:
        st.info("No quotation records found.")
    else:
        for pos, (_, row) in enumerate(df_display.iterrows(), start=1):
            row_dict = row.to_dict()
            q_name = row_dict.get("Quotation Name", "")
            with st.container(border=True):
                st.markdown(
                    f'<div class="quo-card-title">#{pos} — {_esc(q_name)}</div>'
                    f'<div class="quo-card-sub">{_esc(row_dict.get("Date"))} • {_esc(row_dict.get("Project ID"))}</div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Site ID</span><span class="quo-card-value">{_esc(row_dict.get("Site ID"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Site Name</span><span class="quo-card-value">{_esc(row_dict.get("Site Name"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Cluster</span><span class="quo-card-value">{_esc(row_dict.get("Cluster"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Project</span><span class="quo-card-value">{_esc(row_dict.get("Project Name"))}</span></div>'
                    f'<div class="quo-card-row"><span class="quo-card-label">Grand Total</span><span class="quo-card-value amount">{_amt(row_dict.get("Quotation Amount"))}</span></div>',
                    unsafe_allow_html=True,
                )
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("👁️ View / Edit", key=f"card_quo_view_{q_name}_{pos}", use_container_width=True):
                        quotation_dialog(row_dict)
                with bc2:
                    with st.popover("🗑️ Delete", use_container_width=True):
                        st.warning(f"Delete **{q_name}**?")
                        if st.button("Yes, delete", key=f"card_quo_del_{q_name}_{pos}", type="primary", use_container_width=True):
                            _delete_quotation(q_name)

else:
    # ---------------------------------------------------------------
    # LAVISH DESKTOP TABLE VIEW
    # ---------------------------------------------------------------
    rows_html = []
    for pos, (_, r) in enumerate(df_display.iterrows(), start=1):
        d = pd.to_datetime(r.get("Date"), errors="coerce")
        date_html = (
            f'<div class="lux-date">{d.strftime("%d %b %Y")}<small>{d.strftime("%A")}</small></div>'
            if pd.notna(d) else _esc(r.get("Date"))
        )
        pid = r.get("Project ID")
        sid = r.get("Site ID")
        clu = r.get("Cluster")
        rows_html.append(
            "<tr>"
            f'<td class="c"><span class="lux-num">{pos}</span></td>'
            f"<td>{date_html}</td>"
            f'<td>{f"<span class=\'lux-chip proj\'>{html.escape(str(pid))}</span>" if str(pid or "").strip() else _esc(pid)}</td>'
            f'<td>{f"<span class=\'lux-chip\'>{html.escape(str(sid))}</span>" if str(sid or "").strip() else _esc(sid)}</td>'
            f'<td class="lux-site">{_esc(r.get("Site Name"))}</td>'
            f'<td>{f"<span class=\'lux-pill\'>{html.escape(str(clu))}</span>" if str(clu or "").strip() else _esc(clu)}</td>'
            f'<td class="lux-proj">{_esc(r.get("Project Name"))}</td>'
            f'<td class="r lux-amt">{_amt(r.get("Quotation Amount"))}</td>'
            "</tr>"
        )

    if rows_html:
        body_html = "".join(rows_html)
        foot_html = (
            "<tfoot><tr>"
            f'<td colspan="7">Grand Total of {total_count:,} quotation{"s" if total_count != 1 else ""}</td>'
            f'<td class="r">₹ {total_value:,}</td>'
            "</tr></tfoot>"
        )
    else:
        body_html = (
            '<tr><td colspan="8"><div class="lux-empty"><div>🗂️</div>'
            f'{"No quotations match your search." if search_q else "No quotation records yet. Click ➕ Add Record to create one."}'
            "</div></td></tr>"
        )
        foot_html = ""

    table_html = (
        '<div class="lux-table-wrap">'
        '<div class="lux-table-head">'
        '<div class="lux-table-title">📑 Quotation Register<span>newest first</span></div>'
        f'<div class="lux-table-badge">₹ {total_value:,}</div>'
        "</div>"
        '<div class="lux-scroll"><table class="lux-table">'
        "<thead><tr>"
        '<th class="c">#</th><th>Date</th><th>Project ID</th><th>Site Code</th>'
        '<th>Site Name</th><th>Cluster</th><th>Project</th><th class="r">Grand Total</th>'
        "</tr></thead>"
        f"<tbody>{body_html}</tbody>{foot_html}"
        "</table></div></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # ---------------- ACTION BAR ----------------
    if not df_display.empty:
        st.markdown('<div class="lux-action-title">⚡ Quick Actions</div>', unsafe_allow_html=True)

        def _fmt_option(i):
            r = df_display.iloc[i]
            return (
                f"#{i + 1}  •  {r.get('Project ID', '') or '-'}  •  "
                f"{r.get('Site Name', '') or '-'}  •  {_amt(r.get('Quotation Amount'))}"
            )

        col_sel, col_act1, col_act2 = st.columns([6, 2, 2], vertical_alignment="bottom")
        with col_sel:
            sel_i = st.selectbox(
                "SELECT QUOTATION",
                options=list(range(len(df_display))),
                format_func=_fmt_option,
                index=None,
                placeholder="Choose a quotation to view, edit or delete...",
            )

        actual_data = df_display.iloc[sel_i].to_dict() if sel_i is not None else None

        with col_act1:
            if st.button("👁️ View / Edit", type="primary", use_container_width=True, disabled=actual_data is None):
                quotation_dialog(actual_data)
        with col_act2:
            with st.popover("🗑️ Delete", use_container_width=True, disabled=actual_data is None):
                if actual_data is not None:
                    q_name = actual_data.get("Quotation Name", "")
                    st.warning(f"Permanently delete **{q_name}** and all its items?")
                    if st.button("Yes, delete", key="lux_confirm_delete", type="primary", use_container_width=True):
                        _delete_quotation(q_name)
