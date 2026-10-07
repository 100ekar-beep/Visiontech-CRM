"""
TEAM APP (alag Streamlit app ki main file) — Streamlit Cloud pe Main file path = team_app.py

- Ek hi login ([dg] password)
- Login ke baad DG Project + Site Data + SRN Pending page
- Team: dekh sakti hai, status edit, file upload kar sakti hai
- Team: koi bhi SITE DELETE nahi kar sakti
- Main CRM app (app.py) pe iska koi asar nahi
- SRN Pending dono apps me SAME Supabase data use karega
"""

import streamlit as st


# ================================================================
# TEAM KO KAUN KAUN SE PAGES DIKHANE HAIN
# ================================================================
TEAM_PAGES = [
    ("pages/02_2_DG Removal.py", "DG Project", "⚡"),
    ("pages/01_🏗️_Site_Data.py", "Site Data", "🏗️"),
    ("pages/08_🛢️_SRN Detail.py", "SRN Pending", "📦"),
]


# ------------------------------------------------------------------
# SITE DELETE BAND (sirf is team app me)
#
# Site Data page me delete ke liye pehle ek checkbox
# (key "del_confirm_<id>") tick karna padta hai,
# tabhi "Delete This Record Permanently" button aata hai.
#
# Is app me wo checkbox kabhi banega hi nahi,
# isliye delete button bhi kabhi nahi aayega.
#
# "Danger Zone" heading bhi chhupa di hai.
#
# Main CRM app (app.py) par iska koi effect nahi hoga.
# ------------------------------------------------------------------
if not getattr(st, "_team_delete_guard", False):

    _orig_checkbox = st.checkbox
    _orig_markdown = st.markdown

    def _team_checkbox(label, *args, **kwargs):

        if str(kwargs.get("key", "")).startswith("del_confirm_"):
            return False

        return _orig_checkbox(label, *args, **kwargs)

    def _team_markdown(body, *args, **kwargs):

        if isinstance(body, str) and "Danger Zone" in body:
            return None

        return _orig_markdown(body, *args, **kwargs)

    st.checkbox = _team_checkbox
    st.markdown = _team_markdown

    st._team_delete_guard = True


# ================================================================
# TEAM PASSWORD
# ================================================================
def _team_password():

    try:

        return str(
            st.secrets.get("dg", {}).get("password", "") or ""
        ).strip()

    except Exception:

        return ""


# ================================================================
# LOGIN PAGE
# ================================================================
def login_page():

    _, mid, _ = st.columns([1, 1.3, 1])

    with mid:

        st.markdown(
            """
            <div style="
                background:linear-gradient(
                    100deg,
                    #1e1b4b,
                    #4338ca,
                    #7c3aed
                );
                border-radius:18px;
                padding:28px 24px;
                text-align:center;
                margin-top:60px;
                box-shadow:
                    0 20px 40px -18px
                    rgba(30,27,75,.6);
            ">

                <div style="font-size:2.4rem">
                    🔐
                </div>

                <div style="
                    color:#fff;
                    font-weight:900;
                    font-size:1.6rem;
                    letter-spacing:1px;
                ">
                    Team Login
                </div>

                <div style="
                    color:#c7d2fe;
                    font-weight:600;
                    margin-top:4px;
                ">
                    DG Project • Site Data • SRN Pending
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if not _team_password():

            st.error(
                "Secrets me [dg] password set nahi hai. "
                "Streamlit Cloud → Settings → Secrets me add karein."
            )

            return


        with st.form("team_login"):

            pwd = st.text_input(
                "PASSWORD",
                type="password"
            )

            login_clicked = st.form_submit_button(
                "🔓 Login",
                use_container_width=True
            )

            if login_clicked:

                if pwd == _team_password():

                    st.session_state.team_authed = True

                    # DG page dobara password na maange
                    st.session_state.dg_authed = True

                    st.rerun()

                st.error("Password galat hai.")


# ================================================================
# NAVIGATION
#
# IMPORTANT:
# pg.run() se pehle st.write / st.markdown mat lagana.
# Child pages ka st.set_page_config pehla Streamlit command
# rehna chahiye.
# ================================================================

if st.session_state.get("team_authed"):

    pages = [

        st.Page(
            path,
            title=title,
            icon=icon,
            default=(i == 0)
        )

        for i, (path, title, icon)
        in enumerate(TEAM_PAGES)
    ]

else:

    pages = [

        st.Page(
            login_page,
            title="Login",
            icon="🔐"
        )

    ]


pg = st.navigation(pages)

pg.run()
