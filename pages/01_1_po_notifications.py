    is_up_closed_tab = st.session_state.upload_notif_tab == "closed"
    up_rows = closed_up if is_up_closed_tab else open_up

    sc1, sc2 = st.columns([3, 2])
    with sc1:
        search_q = st.text_input(
            "Search", key="up_search", label_visibility="collapsed",
            placeholder="🔍 Search: Team, Site Name, Site ID, Project ID, Project Name..."
        ).strip().lower()
    with sc2:
        type_filter = st.radio("Type", ["All", "Photo", "JMS"], horizontal=True,
                               key="up_type_filter", label_visibility="collapsed")

    if type_filter != "All":
        up_rows = [r for r in up_rows if str(r.get("upload_type", "")).lower() == type_filter.lower()]

    if search_q:
        def _hay(r):
            return " ".join(str(r.get(k) or "") for k in
                            ("team_name", "uploaded_by", "site_name", "site_id",
                             "project_id", "project_name", "upload_type")).lower()
        up_rows = [r for r in up_rows if search_q in _hay(r)]

    if st.session_state.get("dl_error"):
        st.error(st.session_state.pop("dl_error"))

    if not up_rows:
        if is_up_closed_tab:
            st.info("Abhi tak kuch close nahi kiya gaya.")
        else:
            st.success("✅ Koi naya upload pending nahi hai. Sab clear hai!")
    else:
        if is_up_closed_tab:
            col_ratios = [0.4, 1.3, 1.7, 1.0, 1.2, 1.7, 1.2, 1.4, 1.5, 1.2]
            col_labels = ["#", "TEAM NAME", "SITE NAME", "SITE ID", "PROJECT ID", "PROJECT NAME",
                          "PHOTO / JMS", "DOWNLOAD", "CLOSED AT", "ACTION"]
        else:
            col_ratios = [0.4, 1.3, 1.7, 1.0, 1.2, 1.7, 1.2, 1.4, 1.2]
            col_labels = ["#", "TEAM NAME", "SITE NAME", "SITE ID", "PROJECT ID", "PROJECT NAME",
                          "PHOTO / JMS", "DOWNLOAD", "ACTION"]

        st.markdown(
            f"<div class='notif-lux-title'><div>📸 Photo / JMS Register <small>Scroll right for more columns →</small></div><span class='notif-lux-count'>{len(up_rows)} records</span></div>",
            unsafe_allow_html=True,
        )
        with st.container(key="notif_table_wrap"):
            with st.container(key="notif_head"):
                h_cols = st.columns(col_ratios)
                for h_col, label in zip(h_cols, col_labels):
                    h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)


            for pos, row in enumerate(up_rows):
                with st.container(key=f"notifrow_{'odd' if pos % 2 else 'even'}_{pos}"):
                    rid = row["ids"][0]
                    rcols = st.columns(col_ratios)
                    up_type = str(row.get("upload_type", "-"))
                    type_cls = "status-blue" if up_type.lower() == "photo" else "status-yellow"
                    team = row.get("team_name") or row.get("uploaded_by") or "-"
                    pname = row.get("project_name") or "-"

                    rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)
                    rcols[1].markdown(f"<div class='tbl-cell' title=\"{team}\">{team}</div>", unsafe_allow_html=True)
                    rcols[2].markdown(f"<div class='tbl-cell'>{row.get('site_name') or '-'}</div>", unsafe_allow_html=True)
                    rcols[3].markdown(f"<div class='tbl-cell'>{row.get('site_id') or '-'}</div>", unsafe_allow_html=True)
                    rcols[4].markdown(f"<div class='tbl-cell'>{row.get('project_id') or '-'}</div>", unsafe_allow_html=True)
                    rcols[5].markdown(f"<div class='tbl-cell' title=\"{pname}\">{pname}</div>", unsafe_allow_html=True)
                    rcols[6].markdown(
                        f"<span class='status-badge {type_cls}'>{up_type} ({row.get('file_count', 1)})</span>",
                        unsafe_allow_html=True)

                    # --- Download (2 step: prepare -> save) ---
                    dl_key = f"dl_data_{rid}"
                    with rcols[7]:
                        if dl_key in st.session_state:
                            data, fname, mime = st.session_state[dl_key]
                            st.download_button("💾 Save", data=data, file_name=fname, mime=mime,
                                               key=f"up_save_{rid}", use_container_width=True)
                        elif row.get("links"):
                            if st.button("⬇️ Download", key=f"up_dl_{rid}", use_container_width=True):
                                try:
                                    with st.spinner("Files la raha hu..."):
                                        base = f"{row.get('site_id') or 'site'}_{up_type}"
                                        st.session_state[dl_key] = build_download(row["links"], base)
                                except Exception as e:
                                    st.session_state["dl_error"] = (
                                        f"❌ Download fail ({row.get('site_id')}): {e}. "
                                        f"Link check karo: {row['links'][0]}"
                                    )
                                st.rerun()
                        else:
                            st.markdown("<div class='tbl-cell'>-</div>", unsafe_allow_html=True)

                    if is_up_closed_tab:
                        closed_at = str(row.get("closed_at", "") or "")[:19].replace("T", " ") or "-"
                        rcols[8].markdown(f"<div class='tbl-cell'>{closed_at}</div>", unsafe_allow_html=True)
                        with rcols[9]:
                            if st.button("↩️ Reopen", key=f"up_reopen_{rid}", use_container_width=True):
                                if reopen_upload_rows(row["ids"]):
                                    clear_upload_cache()
                                    st.rerun()
                    else:
                        with rcols[8]:
                            if st.button("✅ Close", key=f"up_close_{rid}", use_container_width=True):
                                if close_upload_rows(row["ids"]):
                                    clear_upload_cache()
                                    st.rerun()

        st.markdown(f"<div class='notif-lux-footer'><span>Total Records <small>{len(up_rows)} shown</small></span><span>{len(up_rows)} records</span></div>", unsafe_allow_html=True)
