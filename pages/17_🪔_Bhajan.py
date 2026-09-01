import html
import re
import unicodedata
from datetime import datetime, timezone
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


def go_home():
    """app.py पर वापस भेजता है; अगर multipage setup में app.py नहीं मिलता तो
    पूरा page crash होने की बजाय एक साफ़ सन्देश दिखाता है."""
    try:
        st.switch_page("app.py")
    except Exception:
        st.error("🚫 Home page (app.py) नहीं मिला। कृपया apna multipage app.py file naam confirm karein.")


# ---------------------------------------------------------------------------
# SIDEBAR — अब हमेशा दिखेगा (login screen से पहले भी), पहले सिर्फ़ login के
# बाद दिखता था क्योंकि यह block login-check के नीचे था और st.stop() उसे रोक
# देता था. यही missing-sidebar वाला bug था.
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🪔 Bhajan Menu")
    if st.button("🏠 Home / Change Workspace", key="bhajan_back_home", use_container_width=True):
        go_home()
    if st.session_state.get("bhajan_authenticated"):
        if st.button("🚪 Logout", key="bhajan_sidebar_logout", use_container_width=True):
            st.session_state["bhajan_authenticated"] = False
            st.rerun()
    else:
        st.caption("Login करने के बाद यहाँ और options दिखेंगे।")


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
    .stApp {background:#000000 !important;color:#ffffff !important;}
    .main, [data-testid="stMain"], [data-testid="stMainBlockContainer"] {background:#000000 !important;}
    h1,h2,h3,h4,h5,h6,p,span,small,div,label {color:#ffffff !important;font-weight:700 !important;}
    [data-testid="stCaptionContainer"] p {color:#ffffff !important;font-weight:700 !important;}
    [data-testid="stWidgetLabel"] p {color:#ffffff !important;font-weight:800 !important;}
    [data-testid="stTabs"] button p {color:#ffffff !important;font-weight:800 !important;}
    [data-testid="stTabs"] button[aria-selected="true"] {border-bottom-color:#f97316 !important;}
    [data-testid="stRadio"] label p {color:#ffffff !important;font-weight:800 !important;}
    [data-testid="stSidebar"] {background:#050505 !important;border-right:1px solid #262626 !important;}
    .bhajan-card {background:#111111;border:1px solid #404040;border-radius:16px;
      padding:18px;margin:10px 0;box-shadow:0 5px 18px rgba(255,255,255,.05)}
    .bhajan-text {white-space:pre-wrap;line-height:1.9;font-size:1.08rem;color:#ffffff !important;font-weight:700 !important;}
    div.stButton>button {border-radius:9px;font-weight:800 !important;color:#ffffff !important;}
    div.stButton>button p, div.stDownloadButton>button p, a[data-testid="stLinkButton"] p {
      color:#ffffff !important;font-weight:800 !important;
    }
    input, textarea {
      background:#111111 !important;color:#ffffff !important;font-weight:700 !important;
      -webkit-text-fill-color:#ffffff !important;border-color:#404040 !important;
    }
    input::placeholder, textarea::placeholder {color:#a3a3a3 !important;-webkit-text-fill-color:#a3a3a3 !important;}
    div[data-baseweb="select"] > div {background:#111111 !important;border-color:#404040 !important;}
    div[data-baseweb="select"] span {color:#ffffff !important;font-weight:800 !important;}
    div[role="listbox"], div[role="option"] {background:#111111 !important;color:#ffffff !important;}
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
      background:#080808 !important;border-color:#333333 !important;
    }
    [data-testid="stExpander"] {background:#0a0a0a !important;border-color:#333333 !important;}
    [data-testid="stAlert"] {background:#111111 !important;border-color:#404040 !important;}
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


def _find_asset(*names: str) -> Path | None:
    roots = [
        Path(__file__).resolve().parent / "assets",
        Path(__file__).resolve().parent.parent / "assets",
        Path(__file__).resolve().parent,        # pages/ folder सीधे (assets के बिना)
        Path(__file__).resolve().parent.parent,  # repo root सीधे (assets के बिना)
        Path.cwd() / "assets",
        Path.cwd(),
        Path("assets"),
        Path("."),
    ]
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.exists():
                return candidate
    return None


def _asset_search_paths(*names: str) -> list[str]:
    roots = [
        Path(__file__).resolve().parent / "assets",
        Path(__file__).resolve().parent.parent / "assets",
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
        Path.cwd() / "assets",
        Path.cwd(),
    ]
    return [str(root / name) for root in roots for name in names]


def find_font_regular() -> Path | None:
    return _find_asset("NotoSansDevanagari-Regular.ttf")


def find_font_bold() -> Path | None:
    return _find_asset("NotoSansDevanagari-Bold.ttf")


def find_font_black() -> Path | None:
    # Black न मिले तो Bold से ही काम चला लेंगे (हल्का कम भारी दिखेगा, टूटेगा नहीं).
    return _find_asset("NotoSansDevanagari-Black.ttf") or find_font_bold()


def find_logo() -> Path | None:
    exact = _find_asset("logo.png")
    if exact:
        return exact
    # अगर logo.png नाम से नहीं मिला, तो root/pages/assets में जो भी पहली PNG
    # image मिले उसे logo मान लें (uploaded_files के original नाम वाले लिए).
    search_dirs = [
        Path(__file__).resolve().parent / "assets",
        Path(__file__).resolve().parent.parent / "assets",
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
    ]
    for d in search_dirs:
        if d.exists():
            pngs = sorted(d.glob("*.png"))
            if pngs:
                return pngs[0]
    return None


# ---------------------------------------------------------------------------
# PDF — मंडळ का नाम, logo, marketing tagline box, double border, हल्का
# watermark और नीचे colourful संपर्क सूची
# ---------------------------------------------------------------------------
ORG_NAME = "कर्वेनगर माहेश्वरी भजनी मंडळ"
TAGLINE = "काया के भजन । संगीतमय हनुमान चालिसा । सुंदरकांड । भजन संध्या"
CONTACT_PEOPLE = [
    ("रामकिशोर जाजू", "8830928952"),
    ("विष्णू काळ्या", "9822443350"),
]

MAROON = (122, 24, 24)
MAROON_DARK = (84, 14, 14)
GOLD = (180, 131, 46)
GOLD_LIGHT = (250, 236, 204)
DARK_TEXT = (35, 24, 16)


class LavishBhajanPDF(FPDF):
    def __init__(self, font_regular: Path, font_bold: Path, font_black: Path,
                 logo_path: Path | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_path = logo_path
        self.add_font("Noto", fname=str(font_regular))
        self.add_font("Noto", style="B", fname=str(font_bold))
        self.add_font("NotoBlack", fname=str(font_black))
        try:
            # सही जोड़ाक्षर/मात्रा दिखाने के लिए ज़रूरी — requirements.txt में
            # "uharfbuzz" ज़रूर जोड़ें, वरना पूरा हिंदी टेक्स्ट (सिर्फ़
            # watermark नहीं, हर जगह) टूटा/गलत क्रम में दिखेगा.
            self.set_text_shaping(True)
        except Exception:
            pass
        self.set_auto_page_break(auto=True, margin=56)

    def _border(self):
        self.set_draw_color(*MAROON)
        self.set_line_width(1.1)
        self.rect(8, 8, self.w - 16, self.h - 16)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.rect(11, 11, self.w - 22, self.h - 22)

    def _watermark(self):
        with self.local_context(fill_opacity=0.13):
            self.set_font("Noto", size=11.5)
            self.set_text_color(*MAROON)
            text_w = self.get_string_width(ORG_NAME)
            row_h = 48
            col_w = text_w + 30
            y = 34
            row_i = 0
            while y < self.h - 12:
                offset = (col_w / 2) if (row_i % 2) else 0
                x = -offset
                while x < self.w:
                    self.text(x, y, ORG_NAME)
                    x += col_w
                y += row_h
                row_i += 1

    def _tagline_box(self, y: float) -> float:
        box_h = 9
        x = 22
        w = self.w - 44
        self.set_fill_color(*MAROON)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.rect(x, y, w, box_h, style="DF")
        self.set_xy(x, y + 1.3)
        self.set_font("Noto", style="B", size=10.5)
        self.set_text_color(*GOLD_LIGHT)
        self.cell(w, box_h - 2.2, TAGLINE, align="C")
        return y + box_h

    def header(self):
        self._border()
        self._watermark()
        if self.page_no() == 1:
            if self.logo_path:
                logo_w = 28
                self.image(str(self.logo_path), x=(self.w - logo_w) / 2, y=14, w=logo_w)
                y = 14 + logo_w + 5
            else:
                y = 18
            self.set_xy(15, y)
            self.set_font("NotoBlack", size=25)
            self.set_text_color(*MAROON_DARK)
            self.cell(self.w - 30, 12, ORG_NAME, align="C")
            y += 12
            self.set_draw_color(*GOLD)
            self.set_line_width(0.6)
            self.line(self.w / 2 - 30, y, self.w / 2 + 30, y)
            self.set_y(y + 5)
        else:
            self.set_y(14)
            self.set_font("Noto", style="B", size=11)
            self.set_text_color(*GOLD)
            self.cell(0, 6, ORG_NAME, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(5)

    def footer(self):
        self.set_y(-54)
        y = self._tagline_box(self.get_y())
        y += 2.5
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(20, y, self.w - 20, y)
        y += 2.5
        self.set_xy(15, y)
        self.set_font("NotoBlack", size=13)
        self.set_text_color(*MAROON_DARK)
        self.cell(self.w - 30, 7, "भजन के लिये संपर्क", align="C")
        y += 8
        self.set_font("Noto", style="B", size=12)
        for name, number in CONTACT_PEOPLE:
            name_w = self.get_string_width(name + "  ")
            num_w = self.get_string_width(number)
            self.set_xy((self.w - (name_w + num_w)) / 2, y)
            self.set_text_color(*DARK_TEXT)
            self.cell(name_w, 6.5, name + "  ")
            self.set_text_color(*GOLD)
            self.cell(num_w, 6.5, number)
            y += 6.5


def _render_pdf(font_regular, font_bold, font_black, logo_path,
                 title: str, category: str, lyrics: str, lyrics_size: float) -> LavishBhajanPDF:
    pdf = LavishBhajanPDF(
        font_regular=font_regular, font_bold=font_bold, font_black=font_black,
        logo_path=logo_path, format="A4",
    )
    pdf.add_page()
    pdf.set_font("NotoBlack", size=21)
    pdf.set_text_color(*MAROON_DARK)
    pdf.multi_cell(0, 11, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Noto", style="B", size=11)
    pdf.set_text_color(*GOLD)
    pdf.multi_cell(0, 6.5, f"श्रेणी: {category}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("Noto", style="B", size=lyrics_size)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(0, lyrics_size * 0.62, lyrics, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return pdf


def make_pdf(title: str, category: str, lyrics: str) -> bytes:
    font_regular = find_font_regular()
    font_bold = find_font_bold()
    font_black = find_font_black()
    if not font_regular or not font_bold:
        tried = _asset_search_paths("NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-Bold.ttf")
        tried_list = "\n".join(f"• {p}" for p in tried)
        raise FileNotFoundError(
            "Font files नहीं मिलीं। इन जगहों पर ढूंढा गया, पर कहीं नहीं मिलीं:\n"
            f"{tried_list}\n\n"
            "इनमें से किसी एक 'assets' folder में NotoSansDevanagari-Regular.ttf और "
            "NotoSansDevanagari-Bold.ttf दोनों रखें (यह app file जिस folder में है, "
            "उसी में या उसके parent folder में 'assets' नाम का folder बनाएं)।"
        )
    logo_path = find_logo()  # ना मिले तो भी PDF बन जाएगी, बस logo के बिना.

    # भजन को हो सके तो 1 ही page में fit करने की कोशिश — बड़े size से शुरू करके
    # ज़रूरत पड़ने पर छोटा करते जाते हैं; अगर फिर भी ना समाए तो जितना बड़ा size
    # 1 page में possible नहीं, उसे छोड़ते हुए आख़िरी (सबसे छोटे) size पर भजन
    # अगले page पर अपने आप चला जाएगा — यह पूरी तरह सामान्य है, कोई ग़लती नहीं.
    pdf = None
    for size in (15.5, 14, 12.5, 11.5, 10.5):
        pdf = _render_pdf(font_regular, font_bold, font_black, logo_path, title, category, lyrics, size)
        if pdf.page_no() == 1:
            break
    return bytes(pdf.output())


def whatsapp_url(message: str) -> str:
    return f"https://wa.me/?text={quote(message)}"


# PDF कहीं भी Supabase Storage या किसी और cloud पर save नहीं होती — यह सिर्फ़
# memory में बनती है और सीधे user के device पर download होती है।


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

    c1, c2 = st.columns(2)
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
        st.link_button("📲 WhatsApp पर Text भेजें", whatsapp_url(text_message), use_container_width=True)

    if pdf_bytes:
        st.caption("PDF को WhatsApp पर भेजने के लिए: ऊपर Download करें, फिर WhatsApp में Attach कर दें।")
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
                    "updated_at": datetime.now(timezone.utc).isoformat(),
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
    category_mode = st.radio(
        "Category चुनने का तरीका",
        ["Existing Category", "नई Category"],
        horizontal=True,
        key="bhajan_category_mode",
    )

    if existing_categories:
        st.markdown("**पहले से Registered Categories:**")
        st.caption(" • ".join(existing_categories))

    with st.form("add_bhajan_form", clear_on_submit=True):
        title = st.text_input("भजन का नाम *", placeholder="जैसे: हनुमान चालीसा")
        if category_mode == "Existing Category":
            if existing_categories:
                category = st.selectbox(
                    "Existing Category dropdown से चुनें *",
                    existing_categories,
                    key="existing_bhajan_category",
                )
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
                    view_bhajan(row)
                if c.button("✏️", key=f"edit_{row['id']}", help="Edit", use_container_width=True):
                    edit_bhajan(row, categories)
                if d.button("🗑️", key=f"delete_{row['id']}", help="Delete", use_container_width=True):
                    st.session_state["delete_bhajan_id"] = row["id"]

                if st.session_state.get("delete_bhajan_id") == row["id"]:
                    st.warning(f"क्या आप '{row['title']}' permanently delete करना चाहते हैं?")
                    yes, no = st.columns(2)
                    if yes.button("हाँ, Delete", key=f"confirm_{row['id']}", type="primary", use_container_width=True):
                        supabase.table("bhajans").delete().eq("id", row["id"]).execute()
                        st.session_state.pop("delete_bhajan_id", None)
                        clear_cache()
                        st.rerun()
                    if no.button("Cancel", key=f"cancel_{row['id']}", use_container_width=True):
                        st.session_state.pop("delete_bhajan_id", None)
                        st.rerun()
