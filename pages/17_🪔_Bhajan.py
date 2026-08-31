import io
import html
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from supabase import Client, create_client


st.set_page_config(page_title="Bhajan", page_icon="🪔", layout="wide")


@st.cache_resource
def init_connection() -> Client | None:
    try:
        url = str(st.secrets["supabase"]["url"])
        url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key = str(st.secrets["supabase"]["key"])
        return create_client(url, key)
    except Exception as exc:
        st.error(f"Supabase connection error: {exc}")
        return None


supabase = init_connection()
if supabase is None:
    st.stop()

# यह page केवल BHAJAN workspace के लिए है.
if st.session_state.get("active_workspace", "VISPL") != "BHAJAN":
    st.error("🚫 यह page केवल BHAJAN workspace में उपलब्ध है।")
    st.info("Home page पर Master Workspace में BHAJAN select करें।")
    st.stop()

# Login इसी Bhajan page पर होगा.
if "bhajan_authenticated" not in st.session_state:
    st.session_state["bhajan_authenticated"] = False

if not st.session_state.get("bhajan_authenticated"):
    st.title("🪔 Bhajan Login")
    st.caption("Bhajan संग्रह खोलने के लिए login करें")

    with st.form("bhajan_page_login_form"):
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        login_submit = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)

    if login_submit:
        try:
            correct_username = str(st.secrets["bhajan_login"]["username"])
            correct_password = str(st.secrets["bhajan_login"]["password"])
            if login_username.strip() == correct_username and login_password == correct_password:
                st.session_state["bhajan_authenticated"] = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Username ya Password galat hai।")
        except Exception as exc:
            st.error(f"🚨 Bhajan login configuration error: {exc}")
    st.stop()


st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg,#fff7ed 0%,#fef3c7 48%,#fff1f2 100%);}
    h1,h2,h3 {color:#7c2d12 !important;}
    .bhajan-card {background:rgba(255,255,255,.85);border:1px solid #fed7aa;border-radius:16px;
      padding:18px;margin:10px 0;box-shadow:0 5px 18px rgba(124,45,18,.08)}
    .bhajan-text {white-space:pre-wrap;line-height:1.9;font-size:1.08rem;color:#292524;}
    div.stButton>button {border-radius:9px;font-weight:700;}
    @media (max-width: 768px) {
      .main .block-container {padding:1rem .75rem 4rem .75rem !important;max-width:100% !important;}
      h1 {font-size:1.75rem !important;}
      h2 {font-size:1.35rem !important;}
      .bhajan-card {padding:14px;margin:8px 0;border-radius:12px;}
      .bhajan-text {font-size:1rem;line-height:1.75;overflow-wrap:anywhere;}
      div[data-testid="stDialog"] > div {width:96vw !important;max-width:96vw !important;padding:10px !important;}
      div[data-testid="stDataFrame"] {font-size:.82rem !important;}
      div.stButton > button, div.stDownloadButton > button, a[data-testid="stLinkButton"] {
        min-height:44px !important;width:100% !important;
      }
      textarea {min-height:240px !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_bhajans():
    result = (
        supabase.table("bhajans")
        .select("id,title,category,lyrics,created_at,updated_at,workspace")
        .eq("workspace", "BHAJAN")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_existing_categories():
    result = (
        supabase.table("bhajans")
        .select("category")
        .eq("workspace", "BHAJAN")
        .order("category")
        .execute()
    )
    return sorted(
        {
            str(row.get("category", "")).strip()
            for row in (result.data or [])
            if str(row.get("category", "")).strip()
        },
        key=str.casefold,
    )


def clear_cache():
    fetch_bhajans.clear()
    fetch_existing_categories.clear()


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", unicodedata.normalize("NFKC", value), flags=re.UNICODE)
    return cleaned.strip("_")[:80] or "bhajan"


def find_font() -> Path | None:
    candidates = [
        Path(__file__).resolve().parent.parent / "assets" / "NotoSansDevanagari-Regular.ttf",
        Path("assets/NotoSansDevanagari-Regular.ttf"),
        Path("NotoSansDevanagari-Regular.ttf"),
    ]
    direct = next((path for path in candidates if path.exists()), None)
    if direct:
        return direct
    project_root = Path(__file__).resolve().parent.parent
    matching_fonts = list(project_root.glob("NotoSansDevanagari*.ttf"))
    return matching_fonts[0] if matching_fonts else None


def make_pdf(title: str, category: str, lyrics: str) -> bytes:
    font_path = find_font()
    if not font_path:
        raise FileNotFoundError(
            "assets/NotoSansDevanagari-Regular.ttf नहीं मिली। README के अनुसार font file जोड़ें।"
        )

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("Noto", fname=str(font_path))
    try:
        pdf.set_text_shaping(True)
    except Exception:
        pass
    pdf.set_font("Noto", size=18)
    pdf.set_text_color(124, 45, 18)
    pdf.multi_cell(0, 10, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Noto", size=10)
    pdf.set_text_color(146, 64, 14)
    pdf.multi_cell(0, 7, f"श्रेणी: {category}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(7)
    pdf.set_font("Noto", size=13)
    pdf.set_text_color(41, 37, 36)
    pdf.multi_cell(0, 8, lyrics, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_font("Noto", size=8)
    pdf.set_text_color(120, 113, 108)
    pdf.multi_cell(0, 5, "॥ भजन संग्रह ॥", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())


def whatsapp_url(message: str) -> str:
    return f"https://wa.me/?text={quote(message)}"


def upload_pdf_and_get_url(row: dict, pdf_bytes: bytes) -> str:
    stamp = int(time.time())
    filename = f"{safe_filename(row['title'])}_{row['id']}_{stamp}.pdf"
    storage_path = f"shared/{filename}"
    supabase.storage.from_("bhajan-pdfs").upload(
        storage_path,
        pdf_bytes,
        {"content-type": "application/pdf", "upsert": "true"},
    )
    public_result = supabase.storage.from_("bhajan-pdfs").get_public_url(storage_path)
    if isinstance(public_result, str):
        return public_result
    if isinstance(public_result, dict):
        return public_result.get("publicUrl") or public_result.get("publicURL") or ""
    return ""


@st.dialog("🪔 पूरा भजन", width="large")
def view_bhajan(row: dict):
    st.subheader(row["title"])
    st.caption(f"श्रेणी: {row['category']}")
    safe_lyrics = html.escape(str(row["lyrics"]))
    st.markdown(f'<div class="bhajan-card bhajan-text">{safe_lyrics}</div>', unsafe_allow_html=True)

    pdf_bytes = None
    pdf_error = None
    try:
        pdf_bytes = make_pdf(row["title"], row["category"], row["lyrics"])
    except Exception as exc:
        pdf_error = str(exc)

    c1, c2, c3 = st.columns(3)
    with c1:
        if pdf_bytes:
            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=f"{safe_filename(row['title'])}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("⬇️ PDF उपलब्ध नहीं", disabled=True, use_container_width=True)
    with c2:
        text_message = f"🪔 *{row['title']}*\n📂 {row['category']}\n\n{row['lyrics']}"
        st.link_button("📲 WhatsApp Text", whatsapp_url(text_message), use_container_width=True)
    with c3:
        if st.button("📄 WhatsApp PDF", use_container_width=True, disabled=not bool(pdf_bytes)):
            try:
                with st.spinner("PDF share link बन रही है..."):
                    public_url = upload_pdf_and_get_url(row, pdf_bytes)
                if not public_url:
                    raise RuntimeError("Public PDF URL नहीं मिली")
                st.session_state["pdf_share_url"] = whatsapp_url(
                    f"🪔 *{row['title']}*\n📂 {row['category']}\n\nPDF खोलें:\n{public_url}"
                )
            except Exception as exc:
                st.error(f"PDF share error: {exc}")

    if st.session_state.get("pdf_share_url"):
        st.link_button(
            "✅ WhatsApp खोलें और व्यक्ति चुनें",
            st.session_state["pdf_share_url"],
            type="primary",
            use_container_width=True,
        )
    if pdf_error:
        st.warning(pdf_error)


@st.dialog("✏️ भजन Edit करें", width="large")
def edit_bhajan(row: dict, categories: list[str]):
    title = st.text_input("भजन का नाम *", value=row["title"], key=f"edit_title_{row['id']}")
    options = sorted(set(categories + [row["category"]]))
    category = st.selectbox(
        "Category *", options, index=options.index(row["category"]), key=f"edit_cat_{row['id']}"
    )
    lyrics = st.text_area("पूरा भजन *", value=row["lyrics"], height=380, key=f"edit_lyrics_{row['id']}")
    if st.button("💾 Update", type="primary", use_container_width=True):
        if not title.strip() or not category.strip() or not lyrics.strip():
            st.error("सभी जरूरी fields भरें।")
        else:
            supabase.table("bhajans").update(
                {
                    "title": title.strip(),
                    "category": category.strip(),
                    "lyrics": lyrics.strip(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", row["id"]).execute()
            clear_cache()
            st.success("भजन update हो गया।")
            st.rerun()


title_col, logout_col = st.columns([8, 2])
with title_col:
    st.title("🪔 Bhajan संग्रह")
    st.caption("Category-wise भजन save, search, read, PDF download और WhatsApp share")
with logout_col:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["bhajan_authenticated"] = False
        st.rerun()

tab_library, tab_add = st.tabs(["📚 सभी भजन", "➕ नया भजन"])

with tab_add:
    existing_categories = fetch_existing_categories()
    with st.form("add_bhajan_form", clear_on_submit=True):
        title = st.text_input("भजन का नाम *", placeholder="जैसे: हनुमान चालीसा")
        category_mode = st.radio("Category", ["Existing Category", "नई Category"], horizontal=True)
        if category_mode == "Existing Category":
            if existing_categories:
                category = st.selectbox("Category चुनें *", existing_categories)
            else:
                st.info("अभी कोई existing category नहीं है। पहले नई Category बनाकर भजन save करें।")
                category = ""
        else:
            category = st.text_input("नई Category का नाम *", placeholder="जैसे: हनुमान भजन")
        lyrics = st.text_area("पूरा भजन लिखें *", height=420, placeholder="यहाँ पूरा भजन paste करें...")
        submitted = st.form_submit_button("💾 भजन Save करें", type="primary", use_container_width=True)

    if submitted:
        if not title.strip() or not category.strip() or not lyrics.strip():
            st.error("भजन का नाम, Category और पूरा भजन भरना जरूरी है।")
        else:
            try:
                supabase.table("bhajans").insert(
                    {
                        "workspace": "BHAJAN",
                        "title": title.strip(),
                        "category": category.strip(),
                        "lyrics": lyrics.strip(),
                    }
                ).execute()
                clear_cache()
                st.success("✅ भजन successfully save हो गया।")
                st.rerun()
            except Exception as exc:
                st.error(f"Save error: {exc}")

with tab_library:
    try:
        rows = fetch_bhajans()
    except Exception as exc:
        st.error(f"Bhajan data load नहीं हुआ: {exc}")
        st.info("पहले दिए गए `supabase_setup.sql` को Supabase SQL Editor में चलाएँ।")
        st.stop()

    categories = sorted({str(x.get("category", "")).strip() for x in rows if x.get("category")})
    c1, c2, c3 = st.columns([4, 3, 1])
    with c1:
        query = st.text_input("Search", placeholder="🔍 नाम या भजन की पंक्ति खोजें...", label_visibility="collapsed")
    with c2:
        selected_category = st.selectbox("Category", ["सभी Categories"] + categories, label_visibility="collapsed")
    with c3:
        if st.button("🔄", help="Refresh", use_container_width=True):
            clear_cache()
            st.rerun()

    filtered = rows
    if selected_category != "सभी Categories":
        filtered = [x for x in filtered if x.get("category") == selected_category]
    if query.strip():
        needle = query.strip().casefold()
        filtered = [
            x for x in filtered
            if needle in str(x.get("title", "")).casefold()
            or needle in str(x.get("lyrics", "")).casefold()
            or needle in str(x.get("category", "")).casefold()
        ]

    st.markdown(f"#### कुल भजन: {len(filtered)}")
    if not filtered:
        st.info("कोई भजन नहीं मिला।")
    else:
        with st.expander("📋 सभी भजनों की Table देखें"):
            table_df = pd.DataFrame(filtered)[["title", "category", "created_at"]].copy()
            table_df.columns = ["भजन का नाम", "Category", "Save Date"]
            table_df["Save Date"] = pd.to_datetime(table_df["Save Date"], errors="coerce").dt.strftime("%d-%m-%Y")
            st.dataframe(table_df, use_container_width=True, hide_index=True)

        st.markdown("### भजन खोलें")
        for row in filtered:
            with st.container(border=True):
                safe_title = html.escape(str(row["title"]))
                safe_category = html.escape(str(row["category"]))
                st.markdown(f"**🪔 {safe_title}**  \n<span style='color:#78716c'>{safe_category}</span>", unsafe_allow_html=True)
                b, c, d = st.columns(3)
                if b.button("📖 खोलें", key=f"open_{row['id']}", use_container_width=True):
                    st.session_state.pop("pdf_share_url", None)
                    view_bhajan(row)
                if c.button("✏️", key=f"edit_{row['id']}", help="Edit", use_container_width=True):
                    edit_bhajan(row, categories)
                if d.button("🗑️", key=f"delete_{row['id']}", help="Delete", use_container_width=True):
                    st.session_state["delete_bhajan_id"] = row["id"]

                if st.session_state.get("delete_bhajan_id") == row["id"]:
                    st.warning(f"क्या आप ‘{row['title']}’ permanently delete करना चाहते हैं?")
                    yes, no = st.columns(2)
                    if yes.button("हाँ, Delete", key=f"confirm_{row['id']}", type="primary", use_container_width=True):
                        supabase.table("bhajans").delete().eq("id", row["id"]).execute()
                        st.session_state.pop("delete_bhajan_id", None)
                        clear_cache()
                        st.rerun()
                    if no.button("Cancel", key=f"cancel_{row['id']}", use_container_width=True):
                        st.session_state.pop("delete_bhajan_id", None)
                        st.rerun()
