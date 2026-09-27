"""
DG Project page (Site Data page jaisa hi look & table)
- site_data me jin sites ka Project Name "DG Removal" hai (active company/workspace ke), wo yaha dikhti hain
- SRC / DC / E-Way / Photo / POD status + Remark seedha site_data me save hote hain
- Files Cloudflare R2 me upload hoti hain (Site Data page jaisa hi), URL site_data ke "<X> Files" column me
  => Site Data page aur ye page hamesha same data dikhate hain
"""
import io
import math
import os
import subprocess
import tempfile
import uuid
import zipfile
from html import escape

import boto3
import pandas as pd
import requests
import streamlit as st
from botocore.client import Config
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from st_keyup import st_keyup
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="DG Project", page_icon="⚡", layout="wide")

# ============================== CONFIG ==============================
PROJECT_MATCH = "DG Removal"          # Project Name me ye text ho to site yaha aayegi
STATUS_OPTS = ["Pending", "Available", "Not Required"]
ALLOWED_EXT = ["pdf", "jpg", "jpeg", "png"]
MAX_PHOTOS = 15
REMARK_COL = "Remark"

DOCS = [
    {"label": "SRC",   "status": "SRC Status",  "files": "SRC Files",    "folder": "src",    "tag": "SRC",   "icon": "📑", "css": "attach_lav_src"},
    {"label": "DC",    "status": "DC Status",   "files": "DC Files",     "folder": "dc",     "tag": "DC",    "icon": "📦", "css": "attach_lav_dc"},
    {"label": "E-Way", "status": "EWAY Status", "files": "EWAY Files",   "folder": "eway",   "tag": "EWAY",  "icon": "🚚", "css": "attach_lav_eway"},
    {"label": "Photo", "status": "Photos",      "files": "Photos Files", "folder": "photos", "tag": "Photo", "icon": "📷", "css": "attach_lav_photo"},
    {"label": "POD",   "status": "POD Status",  "files": "POD Files",    "folder": "pod",    "tag": "POD",   "icon": "✅", "css": "attach_lav_pod"},
]
NEW_COLS = ["SRC Status", "DC Status", "EWAY Status", "POD Status", "POD Files", REMARK_COL]

# --- MULTI-COMPANY TAB SETUP (Site Data page ke saath synced) ---
SITE_COMPANIES = [("VISPL", "VISPL"), ("Bhagyashree", "Bhagyashree"), ("Sai Tele", "Sai Tele")]
SITE_COMPANY_WORKSPACE_MAP = {"VISPL": "VISPL", "Bhagyashree": "BHAGYASHREE", "Sai Tele": "SAI TELE SERVICES"}
if "site_active_company" not in st.session_state:
    st.session_state.site_active_company = "VISPL"
st.session_state["active_workspace"] = SITE_COMPANY_WORKSPACE_MAP.get(st.session_state.site_active_company, "VISPL")

if "dg_view_mode" not in st.session_state:
    st.session_state.dg_view_mode = "table"

# ============================== 2. CSS (Site Data page ka hi theme) ==============================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    color: white !important; border: none; border-radius: 8px; font-weight: 800 !important;
    padding: 0.5rem 1rem; transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.25);
}
div.stButton > button p, div.stButton > button span, div.stButton > button div,
div.stDownloadButton > button p, div.stDownloadButton > button span, div.stDownloadButton > button div {
    color: #ffffff !important; font-weight: 800 !important;
}
.page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #334155; margin-top: 10px; }

div[data-testid="stDialog"] > div {
    background: rgba(255,255,255,0.98); backdrop-filter: blur(16px);
    border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
}
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
    color: #0f172a !important; font-weight: 800 !important; letter-spacing: 0.5px;
}
div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p { color: #1e293b !important; }
div[data-testid="stDialog"] button[kind="icon"] svg { fill: #0f172a !important; }
.modal-section-title {
    color: #475569; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; margin-top: 15px; margin-bottom: 10px;
    border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 5px;
}
label p, label[data-testid="stWidgetLabel"] p { color: #0f172a !important; font-weight: 700 !important; letter-spacing: 0.5px; }
div[data-testid="stTextInput"] input:disabled { color: #000 !important; font-weight: 700 !important; -webkit-text-fill-color: #000 !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); border-right: 1px solid rgba(255,255,255,0.05); }
[data-testid="stSidebarNav"] a {
    padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
    background: rgba(255,255,255,0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
    font-size: 1.05rem !important; transition: all 0.3s ease !important; border: 1px solid rgba(255,255,255,0.05) !important;
    display: flex !important; align-items: center !important; gap: 12px !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.1) !important; transform: translateX(4px) !important;
    border-color: rgba(255,255,255,0.2) !important; color: #fff !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #fff !important;
    border-color: transparent !important; box-shadow: 0 4px 15px rgba(59,130,246,0.4) !important;
}
[data-testid="stSidebarNav"] a span { color: inherit !important; }

/* Company nav bar */
.st-key-site_company_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
.st-key-site_company_nav_bar button {
    font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important; height: auto !important;
    border-radius: 12px !important; transition: all 0.25s ease !important; white-space: nowrap !important;
}
.st-key-site_company_nav_bar button[kind="secondary"] {
    background: #fff !important; color: #475569 !important; border: 1.5px solid rgba(0,0,0,0.12) !important;
    box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
}
.st-key-site_company_nav_bar button[kind="secondary"] p, .st-key-site_company_nav_bar button[kind="secondary"] span,
.st-key-site_company_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
.st-key-site_company_nav_bar button[kind="primary"] {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; border: none !important;
    box-shadow: 0 6px 16px rgba(59,130,246,0.4) !important;
}

/* Lavish upload zones (dialog) */
div[class*="st-key-attach_lav_"] [data-testid="stFileUploaderDropzone"] {
    border: none !important; border-radius: 14px !important; padding: 10px !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
}
div[class*="st-key-attach_lav_"] [data-testid="stFileUploaderDropzone"]:hover { transform: translateY(-2px) !important; filter: brightness(1.08); }
div[class*="st-key-attach_lav_"] [data-testid="stFileUploaderDropzone"] * { color: #fff !important; text-shadow: 0 1px 2px rgba(0,0,0,0.15); }
div[class*="st-key-attach_lav_"] [data-testid="stFileUploaderDropzone"] svg { fill: #fff !important; }
div[class*="st-key-attach_lav_"] [data-testid="stFileUploaderDropzone"] button {
    background: rgba(255,255,255,0.25) !important; border: 1.5px solid rgba(255,255,255,0.65) !important;
    border-radius: 8px !important; font-weight: 800 !important;
}
.st-key-attach_lav_src   [data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #14b8a6, #0891b2) !important; box-shadow: 0 6px 16px rgba(20,184,166,.40) !important; }
.st-key-attach_lav_dc    [data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #f97316, #eab308) !important; box-shadow: 0 6px 16px rgba(249,115,22,.40) !important; }
.st-key-attach_lav_eway  [data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #ec4899, #be123c) !important; box-shadow: 0 6px 16px rgba(236,72,153,.40) !important; }
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #3b82f6, #06b6d4) !important; box-shadow: 0 6px 16px rgba(59,130,246,.45) !important; }
.st-key-attach_lav_pod   [data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #10b981, #059669) !important; box-shadow: 0 6px 16px rgba(16,185,129,.40) !important; }

div[class*="st-key-dgdl_"] button, div[class*="st-key-dgdl_"] a {
    background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%) !important; box-shadow: 0 4px 12px rgba(99,102,241,.40) !important;
    border-radius: 14px !important; border: none !important; font-weight: 800 !important;
    display: flex !important; justify-content: center !important; text-decoration: none !important;
}
div[class*="st-key-dgdl_"] a, div[class*="st-key-dgdl_"] a p, div[class*="st-key-dgdl_"] button p { color: #fff !important; font-weight: 800 !important; }
.dg-doc-title { text-align: center; font-weight: 800; color: #334155; font-size: 0.9rem; margin-bottom: 4px; }
.dg-file-link { font-size: 0.8rem; word-break: break-all; margin: 2px 0; }
.dg-file-link a { color: #4338ca !important; font-weight: 600; text-decoration: none; }

/* KPI strip */
.lux-kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin: 4px 0 14px; }
@media (max-width: 1100px) { .lux-kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 600px) { .lux-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.lux-kpi {
    position: relative; background: #fff; border-radius: 16px; padding: 18px 20px 16px; border: 1px solid #e0e7ff; overflow: hidden;
    box-shadow: 0 12px 28px -14px rgba(79,70,229,0.35); transition: transform .25s ease, box-shadow .25s ease;
}
.lux-kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 34px -14px rgba(79,70,229,0.45); }
.lux-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--accent); }
.lux-kpi-icon {
    position: absolute; right: 14px; top: 14px; width: 38px; height: 38px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.15rem; background: var(--soft);
}
.lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; }
.lux-kpi-value { font-size: 1.65rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; }
.lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

.dg-status-strip { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 22px; }
.dg-status-card {
    background: #fff; border: 1px solid #e0e7ff; border-left: 4px solid #8b5cf6; border-radius: 12px;
    padding: 8px 14px; box-shadow: 0 8px 18px -14px rgba(79,70,229,.5);
}
.dg-status-card span { font-size: .72rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: .8px; }
.dg-status-card b { display: block; font-size: 1.2rem; font-weight: 900; color: #0f172a; }

/* Table title bar */
.slux-head-bar {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 16px 22px; border-radius: 18px 18px 0 0; background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
}
.slux-title { color: #fff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
.slux-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
.slux-badge {
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
    padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
}

/* Scrolling table body */
.st-key-site_lux_wrap {
    background: #fff !important; overflow: auto !important; padding: 0 !important; max-height: 78vh !important;
    border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important; border-radius: 0 !important;
}
.st-key-site_lux_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-site_lux_wrap [data-testid="stHorizontalBlock"] { min-width: 2450px !important; flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important; }
.st-key-site_lux_wrap [data-testid="stColumn"], .st-key-site_lux_wrap [data-testid="column"] { padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9; }
.st-key-site_lux_wrap > .st-key-slux_head, .st-key-site_lux_wrap > div:has(.st-key-slux_head) { position: sticky !important; top: 0 !important; z-index: 20 !important; }
.st-key-slux_head {
    background: linear-gradient(90deg, #312e81 0%, #4338ca 45%, #6d28d9 100%) !important; border-bottom: 3px solid #f59e0b !important;
    box-shadow: 0 8px 14px -8px rgba(30,27,75,.55) !important; padding: 14px 0 !important; min-width: 2450px !important;
}
.st-key-slux_head [data-testid="stColumn"], .st-key-slux_head [data-testid="column"] { border-right: 1px solid rgba(255,255,255,.18) !important; }
.slux-th { color: #fff !important; font-size: .76rem; font-weight: 900; letter-spacing: 1.2px; text-transform: uppercase; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.25); }
.slux-th.c { text-align: center; }
div[class*="st-key-sluxrow_"] { padding: 9px 0 !important; min-width: 2450px !important; background: #fff; border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease; }
div[class*="st-key-sluxrow_odd"] { background: #fafaff; }
div[class*="st-key-sluxrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
div[class*="st-key-sluxrow_"] p { margin: 0 !important; }
.slux-cell { font-size: .86rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
.slux-strong { font-weight: 700; color: #0f172a; }
.slux-soft { color: #475569; font-weight: 600; }
.slux-muted { color: #cbd5e1; }
.slux-num {
    display: inline-flex; width: 30px; height: 30px; border-radius: 50%; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; font-weight: 800; font-size: .75rem;
    box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
}
.slux-chip {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; background: #f8fafc; border: 1px solid #e2e8f0; color: #334155;
    padding: 3px 8px; border-radius: 6px; font-size: .78rem; font-weight: 700; white-space: nowrap;
}
.slux-chip.proj { background: #eef2ff; border-color: #c7d2fe; color: #4338ca; }
.slux-pill {
    display: inline-block; padding: 4px 11px; border-radius: 999px; white-space: nowrap; background: linear-gradient(90deg, #e0f2fe, #ede9fe);
    color: #4338ca; border: 1px solid #ddd6fe; font-weight: 800; font-size: .7rem; letter-spacing: .6px; text-transform: uppercase;
}
.status-badge {
    display: inline-flex !important; align-items: center; gap: 6px; padding: 4px 11px !important; border-radius: 999px !important;
    border: 1px solid transparent; font-size: .7rem !important; font-weight: 800 !important; letter-spacing: .4px; white-space: nowrap;
}
.status-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .85; }
.status-green  { background: #dcfce7 !important; color: #15803d !important; border-color: #bbf7d0 !important; }
.status-blue   { background: #dbeafe !important; color: #1d4ed8 !important; border-color: #bfdbfe !important; }
.status-yellow { background: #fef9c3 !important; color: #a16207 !important; border-color: #fde68a !important; }
.status-red    { background: #fee2e2 !important; color: #b91c1c !important; border-color: #fecaca !important; }
.status-grey   { background: #f1f5f9 !important; color: #475569 !important; border-color: #e2e8f0 !important; }

.st-key-site_lux_wrap div[class*="st-key-mgrbtn_"] button {
    width: 38px !important; max-width: 38px !important; height: 34px !important; min-height: 34px !important; padding: 0 !important;
    margin: 0 auto !important; border-radius: 8px !important; box-shadow: none !important; font-size: 1rem !important;
    background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
}
.st-key-site_lux_wrap div[class*="st-key-mgrbtn_"] button:hover {
    background: #3b82f6 !important; border-color: #60a5fa !important; transform: translateY(-2px) !important;
    box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
}

.slux-foot {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 14px 22px;
    background: linear-gradient(90deg, #f5f3ff, #eef2ff); border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe;
    border-radius: 0 0 18px 18px; box-shadow: 0 24px 48px -22px rgba(30,27,75,0.45);
    font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
}
.slux-foot small { color: #6366f1; font-weight: 700; letter-spacing: .5px; margin-left: 10px; text-transform: none; font-size: .8rem; }
.slux-foot-badge { background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 5px 14px; border-radius: 999px; font-size: .75rem; letter-spacing: .5px; }
.slux-empty { background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px; text-align: center; color: #64748b; font-weight: 600; }
.slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }
.st-key-slux_pager .page-count { color: #4338ca !important; font-weight: 800 !important; font-size: .95rem !important; }
.st-key-slux_pager [data-testid="stNumberInput"] input { text-align: center; font-weight: 800; color: #312e81; }

/* Mobile cards */
.site-card-title { font-size: 1.05rem; font-weight: 800; color: #312e81; margin-bottom: 2px; }
.site-card-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
.site-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed rgba(0,0,0,0.08); font-size: 0.85rem; }
.site-card-row:last-child { border-bottom: none; }
.site-card-label { color: #64748b; font-weight: 600; }
.site-card-value { color: #0f172a; font-weight: 600; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- MULTI-COMPANY NAV BAR ---
with st.container(key="site_company_nav_bar"):
    for nav_col, (company_id, company_label) in zip(st.columns(len(SITE_COMPANIES)), SITE_COMPANIES):
        with nav_col:
            is_active = st.session_state.site_active_company == company_id
            if st.button(company_label, key=f"dg_nav_{company_id}", use_container_width=True,
                         type=("primary" if is_active else "secondary")):
                st.session_state.site_active_company = company_id
                st.session_state.active_workspace = SITE_COMPANY_WORKSPACE_MAP[company_id]
                st.session_state.dg_current_page = 1
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ============================== 3. CONNECTIONS (Site Data page jaisa hi) ==============================
@st.cache_resource
def init_connection():
    try:
        url: str = st.secrets["supabase"]["url"]
        url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key: str = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase connection error: {e}")
        return None


supabase: Client = init_connection()
if supabase is None:
    st.stop()


@st.cache_resource
def init_r2_connection():
    try:
        r2_cfg = st.secrets["r2"]
        return boto3.client(
            "s3",
            endpoint_url=f"https://{r2_cfg['account_id']}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_cfg["access_key_id"],
            aws_secret_access_key=r2_cfg["secret_access_key"],
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    except Exception as e:
        st.error(f"🚨 R2 connection error: {e}")
        return None


r2_client = init_r2_connection()
R2_BUCKET = st.secrets.get("r2", {}).get("bucket_name", "")
R2_PUBLIC_URL = st.secrets.get("r2", {}).get("public_url", "").rstrip("/")


def _compress_image(uploaded_file, max_dimension=1600, quality=50):
    try:
        img = Image.open(uploaded_file)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        return buf, "image/jpeg", "jpg"
    except Exception:
        uploaded_file.seek(0)
        ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else "jpg"
        return uploaded_file, (uploaded_file.type or "image/jpeg"), ext


def _compress_pdf_bytes(raw_bytes):
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
            tmp_in.write(raw_bytes)
            tmp_in_path = tmp_in.name
        tmp_out_path = tmp_in_path.replace(".pdf", "_out.pdf")
        subprocess.run(["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dPDFSETTINGS=/ebook",
                        "-dNOPAUSE", "-dBATCH", "-dQUIET", f"-sOutputFile={tmp_out_path}", tmp_in_path],
                       check=True, timeout=60)
        with open(tmp_out_path, "rb") as f:
            gs_out = f.read()
        os.unlink(tmp_in_path)
        os.unlink(tmp_out_path)
        if gs_out and len(gs_out) < len(raw_bytes):
            return gs_out
    except Exception:
        pass
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            try:
                page.compress_content_streams()
            except Exception:
                pass
        out = io.BytesIO()
        writer.write(out)
        if len(out.getvalue()) < len(raw_bytes):
            return out.getvalue()
    except Exception:
        pass
    return raw_bytes


def upload_file_to_r2(uploaded_file, folder, project_id, site_id, field_tag):
    if r2_client is None:
        raise RuntimeError("R2 client not configured — check [r2] section in Streamlit secrets.")
    ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else "bin"
    if ext in ("jpg", "jpeg", "png"):
        file_obj, content_type, ext = _compress_image(uploaded_file)
    elif ext == "pdf":
        uploaded_file.seek(0)
        file_obj = io.BytesIO(_compress_pdf_bytes(uploaded_file.read()))
        content_type = "application/pdf"
    else:
        uploaded_file.seek(0)
        file_obj, content_type = uploaded_file, (uploaded_file.type or "application/octet-stream")

    def _safe(v, fb):
        return "".join(c for c in str(v) if c.isalnum() or c in ("-", "_")) or fb

    object_key = f"{folder}/{_safe(project_id, 'proj')}_{_safe(site_id, 'site')}_{_safe(field_tag, 'file')}_{uuid.uuid4().hex[:6]}.{ext}"
    r2_client.upload_fileobj(file_obj, R2_BUCKET, object_key, ExtraArgs={"ContentType": content_type})
    return f"{R2_PUBLIC_URL}/{object_key}"


def delete_from_r2(url):
    if r2_client is None or not R2_PUBLIC_URL or not url.startswith(R2_PUBLIC_URL + "/"):
        return
    try:
        r2_client.delete_object(Bucket=R2_BUCKET, Key=url[len(R2_PUBLIC_URL) + 1:])
    except Exception:
        pass


def build_zip_from_urls(urls):
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        used = set()
        for url in urls:
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                name = url.split("/")[-1] or f"file_{uuid.uuid4().hex[:6]}"
                final, n = name, 1
                while final in used:
                    base, dot, extn = name.rpartition(".")
                    final = f"{base}_{n}.{extn}" if dot else f"{name}_{n}"
                    n += 1
                used.add(final)
                zf.writestr(final, resp.content)
            except Exception:
                continue
    return zip_buf.getvalue()


# ============================== DATA HELPERS ==============================
def _clean(v):
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("nan", "none", "null", "-") else s


def parse_files(raw):
    return [u.strip() for u in _clean(raw).split(",") if u.strip().startswith("http")]


def effective_status(stored, files):
    """Status khali ho to files ke hisaab se: file hai -> Available, nahi -> Pending."""
    s = _clean(stored)
    if s:
        return s
    return "Available" if files else "Pending"


@st.cache_data(ttl=30, show_spinner=False)
def fetch_dg_sites(workspace):
    rows, offset, limit = [], 0, 1000
    while True:
        res = (supabase.table("site_data").select("*")
               .eq("workspace", workspace)
               .ilike("Project Name", f"%{PROJECT_MATCH}%")
               .order("id")
               .range(offset, offset + limit - 1).execute())
        chunk = res.data or []
        rows.extend(chunk)
        if len(chunk) < limit:
            break
        offset += limit
    return rows


@st.cache_data(ttl=300, show_spinner=False)
def site_status_options():
    try:
        res = supabase.table("dropdown_master").select("option_value").eq("category", "Site Status").execute()
        return [r["option_value"] for r in (res.data or []) if r.get("option_value")]
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def team_name_options():
    try:
        res = supabase.table("dropdown_master").select("option_value").eq("category", "Team Name").execute()
        return sorted({r["option_value"] for r in (res.data or []) if r.get("option_value")})
    except Exception:
        return []


def update_site(rid, payload):
    supabase.table("site_data").update(payload).eq("id", rid).execute()
    fetch_dg_sites.clear()


def flash(kind, msg):
    st.session_state["dg_flash"] = (kind, msg)


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


def reset_dialog_state(rid):
    """Dialog kholne se pehle purani (stale) state hatao, taaki fresh data dikhe."""
    for k in [k for k in st.session_state.keys() if str(k).startswith("dg_") and str(k).endswith(f"_{rid}")]:
        del st.session_state[k]


# ============================== MANAGE DIALOG ==============================
def _render_doc(rec, doc):
    ss = st.session_state
    rid, f = rec["id"], doc["folder"]
    files_key, proc_key, st_key = f"dg_files_{f}_{rid}", f"dg_proc_{f}_{rid}", f"dg_st_{f}_{rid}"
    if files_key not in ss:
        ss[files_key] = parse_files(rec.get(doc["files"]))
    if proc_key not in ss:
        ss[proc_key] = set()
    if st_key not in ss:
        ss[st_key] = effective_status(rec.get(doc["status"]), ss[files_key])
    files = ss[files_key]

    count = f" ({len(files)}/{MAX_PHOTOS})" if f == "photos" else (f" ({len(files)})" if files else "")
    st.markdown(f"<div class='dg-doc-title'>{doc['icon']} {doc['label']}{count}</div>", unsafe_allow_html=True)

    # --- Upload: file chunte hi upload ---
    with st.container(key=doc["css"]):
        picked = st.file_uploader(f"Upload {doc['label']}", type=ALLOWED_EXT, accept_multiple_files=True,
                                  key=f"dg_up_{f}_{rid}", label_visibility="collapsed")
    new_files = [u for u in (picked or []) if (u.name, u.size) not in ss[proc_key]]
    if new_files:
        if f == "photos":
            slots = MAX_PHOTOS - len(files)
            if slots <= 0:
                st.error(f"Photos pehle se {MAX_PHOTOS}/{MAX_PHOTOS} hain. Pehle kuch delete karein.")
                new_files = []
            elif len(new_files) > slots:
                st.warning(f"Sirf {slots} photo add hongi (max {MAX_PHOTOS}).")
                for extra in new_files[slots:]:
                    ss[proc_key].add((extra.name, extra.size))
                new_files = new_files[:slots]
        uploaded, errors = [], []
        with st.spinner("Upload ho raha hai..."):
            for uf in new_files:
                try:
                    uploaded.append(upload_file_to_r2(uf, f, rec.get("Project ID"), rec.get("Site ID"), doc["tag"]))
                    ss[proc_key].add((uf.name, uf.size))
                except Exception as e:
                    errors.append(f"{uf.name}: {e}")
        for e in errors:
            st.error(f"Upload fail: {e}")
        if uploaded:
            new_list = files + uploaded
            try:
                update_site(rid, {doc["files"]: ", ".join(new_list), doc["status"]: "Available"})
                ss[files_key] = new_list
                ss[st_key] = "Available"
                ss[f"dg_msg_{rid}"] = f"✅ {len(uploaded)} {doc['label']} file(s) upload hui, status Available."
                st.rerun(scope="fragment")
            except Exception as e:
                st.error(f"site_data update nahi hua: {e}")

    # --- Files list + download + delete ---
    if files:
        for url in files:
            name = url.rsplit("/", 1)[-1]
            icon = "📄" if name.lower().endswith(".pdf") else "🖼️"
            st.markdown(f"<div class='dg-file-link'>{icon} <a href='{escape(url)}' target='_blank'>{escape(name)}</a></div>",
                        unsafe_allow_html=True)

        with st.container(key=f"dgdl_{f}"):
            if len(files) == 1:
                st.link_button(f"⬇️ Download {doc['label']}", files[0], use_container_width=True)
            else:
                zip_key, src_key = f"dg_zip_{f}_{rid}", f"dg_zipsrc_{f}_{rid}"
                if ss.get(src_key) != tuple(files):
                    with st.spinner(f"{doc['label']} zip taiyar ho raha hai..."):
                        ss[zip_key] = build_zip_from_urls(files)
                        ss[src_key] = tuple(files)
                st.download_button(
                    f"⬇️ Download {doc['label']} ({len(files)}, .zip)", data=ss[zip_key],
                    file_name=f"{_clean(rec.get('Project ID')) or 'proj'}_{_clean(rec.get('Site ID')) or 'site'}_{doc['tag']}.zip",
                    mime="application/zip", key=f"dg_zipbtn_{f}_{rid}", use_container_width=True)

        with st.popover("🗑️ File delete karein", use_container_width=True):
            names = {u.rsplit("/", 1)[-1]: u for u in files}
            to_del = st.selectbox("File chunein", list(names), key=f"dg_delsel_{f}_{rid}")
            if st.button("Delete", key=f"dg_delbtn_{f}_{rid}", type="primary"):
                url = names[to_del]
                remaining = [u for u in files if u != url]
                payload = {doc["files"]: ", ".join(remaining)}
                if not remaining and ss[st_key] == "Available":
                    payload[doc["status"]] = "Pending"
                try:
                    update_site(rid, payload)
                    delete_from_r2(url)
                    ss[files_key] = remaining
                    if doc["status"] in payload:
                        ss[st_key] = "Pending"
                    ss[f"dg_msg_{rid}"] = f"🗑️ {to_del} delete ho gayi."
                    st.rerun(scope="fragment")
                except Exception as e:
                    st.error(f"Delete nahi hua: {e}")
    else:
        st.caption("Abhi koi file nahi hai.")

    opts = STATUS_OPTS if ss[st_key] in STATUS_OPTS else [ss[st_key]] + STATUS_OPTS
    st.selectbox(f"{doc['label'].upper()} STATUS", opts, key=st_key)


@st.dialog("⚙️ Manage DG Site (Documents / Status)", width="large")
def dg_site_dialog(rec):
    ss = st.session_state
    rid = rec["id"]
    st.caption("SRC, DC, E-Way, Photo aur POD upload karein, status aur remark update karein")

    st.markdown('<div class="modal-section-title">🏢 SITE INFORMATION</div>', unsafe_allow_html=True)
    info_cols = st.columns(5)
    for c, (lbl, col) in zip(info_cols, [("PROJECT NAME", "Project Name"), ("PROJECT ID", "Project ID"),
                                         ("SITE ID", "Site ID"), ("SITE NAME", "Site Name"), ("CLUSTER", "Cluster")]):
        c.text_input(lbl, value=_clean(rec.get(col)), disabled=True, key=f"dg_info_{col}_{rid}")

    msg = ss.pop(f"dg_msg_{rid}", None)
    if msg:
        st.success(msg)

    st.markdown('<div class="modal-section-title">📎 DOCUMENTS</div>', unsafe_allow_html=True)
    row1 = st.columns(3)
    for doc, col in zip(DOCS[:3], row1):
        with col:
            _render_doc(rec, doc)
    st.markdown("<br>", unsafe_allow_html=True)
    row2 = st.columns(3)
    for doc, col in zip(DOCS[3:], row2):
        with col:
            _render_doc(rec, doc)

    st.markdown('<div class="modal-section-title">📝 SITE STATUS, TEAM & REMARK</div>', unsafe_allow_html=True)
    ss_key, rm_key, tm_key = f"dg_sitestatus_{rid}", f"dg_remark_{rid}", f"dg_team_{rid}"
    cur_ss = _clean(rec.get("Site Status"))
    ss_opts = site_status_options()
    if cur_ss not in ss_opts:
        ss_opts = [cur_ss] + ss_opts
    if ss_key not in ss:
        ss[ss_key] = cur_ss
    if rm_key not in ss:
        ss[rm_key] = _clean(rec.get(REMARK_COL))
    cur_team = _clean(rec.get("Team Name"))
    team_opts = [""] + team_name_options()
    if cur_team not in team_opts:
        team_opts.insert(1, cur_team)
    if tm_key not in ss:
        ss[tm_key] = cur_team

    c1, c2, c3 = st.columns([1, 1, 2])
    c1.selectbox("SITE STATUS", ss_opts, key=ss_key, format_func=lambda x: x or "Select")
    c2.selectbox("TEAM NAME", team_opts, key=tm_key, format_func=lambda x: x or "Select")
    c3.text_area("REMARK", key=rm_key, height=90)

    _, col_save = st.columns([8, 2])
    with col_save:
        if st.button("💾 Update Data", type="primary", use_container_width=True, key=f"dg_save_{rid}"):
            payload = {"Site Status": ss[ss_key], "Team Name": ss[tm_key], REMARK_COL: ss[rm_key].strip()}
            for doc in DOCS:
                payload[doc["status"]] = ss[f"dg_st_{doc['folder']}_{rid}"]
            try:
                update_site(rid, payload)
                flash("success", f"✅ {_clean(rec.get('Site ID'))} update ho gaya (site_data me bhi).")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating Data: {e}")


# ============================== PAGE ==============================
active_company = st.session_state.get("site_active_company", "VISPL")
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 {escape(active_company)}
        </h1>
    </div>
""", unsafe_allow_html=True)

if "dg_flash" in st.session_state:
    kind, text = st.session_state.pop("dg_flash")
    getattr(st, kind)(text)

ws = st.session_state.active_workspace
try:
    rows = fetch_dg_sites(ws)
except Exception as e:
    st.error(f"site_data load nahi hua: {e}")
    st.stop()

if rows:
    available_cols = set().union(*(r.keys() for r in rows))
    missing = [c for c in NEW_COLS if c not in available_cols]
    if missing:
        st.error("site_data me ye columns abhi nahi hain. Supabase SQL Editor me `dg_project_setup.sql` run karein, "
                 "phir Refresh dabayein: " + ", ".join(missing))
        st.stop()

raw_by_id = {r["id"]: r for r in rows}
STATUS_COLS = [f"{d['label']} Status" for d in DOCS]
DISPLAY_COLS = ["Project Name", "Site ID", "Project ID", "Site Name", "Cluster", "Team Name", "Site Status"] + STATUS_COLS + ["Remark"]

records = []
for r in rows:
    rec = {"id": r["id"], "created_at": r.get("created_at")}
    for c in ["Project Name", "Site ID", "Project ID", "Site Name", "Cluster", "Team Name", "Site Status"]:
        rec[c] = _clean(r.get(c))
    for doc in DOCS:
        rec[f"{doc['label']} Status"] = effective_status(r.get(doc["status"]), parse_files(r.get(doc["files"])))
    rec["Remark"] = _clean(r.get(REMARK_COL))
    records.append(rec)

df = pd.DataFrame(records, columns=["id", "created_at"] + DISPLAY_COLS)
if not df.empty:
    df["_ts"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("_ts", ascending=False).drop(columns=["_ts"]).reset_index(drop=True)

# --- 4. TOP ACTION BAR ---
col_title, col_ref, col_export = st.columns([6, 1.2, 1.5])
with col_title:
    st.markdown("<h2 style='margin:0; color:#0f172a;'>⚡ DG Project</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_dg_sites.clear()
        st.rerun()

# --- 5. SEARCH + FILTERS + VIEW TOGGLE ---
c_head, c_cluster, c_status, c_pend, c_search, c_view = st.columns([1.8, 1.6, 1.6, 1.6, 2.6, 1.6])
with c_head:
    st.markdown("##### 🗄️ DG Removal Sites")
with c_cluster:
    cl_opts = ["All Clusters"] + sorted(x for x in df["Cluster"].unique() if x)
    sel_cluster = st.selectbox("Cluster", cl_opts, key="dg_cluster_filter", label_visibility="collapsed")
with c_status:
    st_opts = ["All Site Status"] + sorted({(x or "(Blank)") for x in df["Site Status"]})
    sel_status = st.selectbox("Site Status", st_opts, key="dg_status_filter", label_visibility="collapsed")
with c_pend:
    pend_map = {"All Documents": None, **{f"{d['label']} Pending": f"{d['label']} Status" for d in DOCS}}
    sel_pend = st.selectbox("Pending", list(pend_map), key="dg_pend_filter", label_visibility="collapsed")
with c_search:
    search_query = st_keyup("Search", placeholder="🔍 Search records...", label_visibility="collapsed", key="dg_search")
with c_view:
    toggle_label = "📱 Mobile View" if st.session_state.dg_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="dg_view_toggle"):
        st.session_state.dg_view_mode = "cards" if st.session_state.dg_view_mode == "table" else "table"
        st.rerun()

if sel_cluster != "All Clusters":
    df = df[df["Cluster"] == sel_cluster]
if sel_status != "All Site Status":
    df = df[df["Site Status"].replace("", "(Blank)") == sel_status]
if pend_map[sel_pend]:
    df = df[df[pend_map[sel_pend]].str.lower() == "pending"]
if search_query:
    mask = df[DISPLAY_COLS].astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False, regex=False)).any(axis=1)
    df = df[mask]
df = df.reset_index(drop=True)
is_filtered = bool(search_query) or sel_cluster != "All Clusters" or sel_status != "All Site Status" or pend_map[sel_pend] is not None

with col_export:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df[DISPLAY_COLS].to_excel(writer, index=False, sheet_name="DG Project")
    st.download_button("📥 Export Data", data=buffer.getvalue(), file_name="DG_Project_Export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- KPI STRIP ---
def _pending(col):
    return int((df[col].str.lower() == "pending").sum()) if not df.empty else 0

kpi_note = "Filtered results" if is_filtered else "All DG sites"
kpi_cards = [
    ("Total Sites", len(df), "🏗️", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff", kpi_note),
    ("SRC Pending", _pending("SRC Status"), "📑", "linear-gradient(90deg,#14b8a6,#0891b2)", "#f0fdfa", "SRC nahi aaya"),
    ("DC Pending", _pending("DC Status"), "📦", "linear-gradient(90deg,#f97316,#eab308)", "#fff7ed", "DC nahi aaya"),
    ("E-Way Pending", _pending("E-Way Status"), "🚚", "linear-gradient(90deg,#ec4899,#be123c)", "#fdf2f8", "E-Way nahi aaya"),
    ("Photo Pending", _pending("Photo Status"), "📷", "linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff", "Photos nahi aayi"),
    ("POD Pending", _pending("POD Status"), "✅", "linear-gradient(90deg,#10b981,#059669)", "#ecfdf5", "POD nahi aaya"),
]
st.markdown(
    '<div class="lux-kpi-grid">' + "".join(
        f'<div class="lux-kpi" style="--accent:{acc};--soft:{soft};"><div class="lux-kpi-icon">{icon}</div>'
        f'<div class="lux-kpi-label">{label}</div><div class="lux-kpi-value">{val:,}</div>'
        f'<div class="lux-kpi-foot">{foot}</div></div>'
        for label, val, icon, acc, soft, foot in kpi_cards) + '</div>',
    unsafe_allow_html=True,
)

if not df.empty:
    status_counts = df["Site Status"].replace("", "(Blank)").value_counts()
    st.markdown('<div class="dg-status-strip">' + "".join(
        f'<div class="dg-status-card"><span>{escape(str(k))}</span><b>{int(v):,}</b></div>'
        for k, v in status_counts.items()) + '</div>', unsafe_allow_html=True)

# --- 6. PAGINATION LOGIC ---
if "dg_current_page" not in st.session_state:
    st.session_state.dg_current_page = 1
if "dg_rows_per_page" not in st.session_state:
    st.session_state.dg_rows_per_page = 100

rows_per_page = int(st.session_state.dg_rows_per_page)
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
st.session_state.dg_current_page = min(max(st.session_state.dg_current_page, 1), total_pages)
st.session_state["dg_page_jump_input"] = st.session_state.dg_current_page

start_idx = (st.session_state.dg_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page
df_page = df.iloc[start_idx:end_idx]


def open_site(rid):
    reset_dialog_state(rid)
    dg_site_dialog(raw_by_id[rid])


# --- 7. TABLE / CARD DISPLAY ---
if df_page.empty:
    st.markdown(
        '<div class="slux-empty"><div>🗂️</div>'
        + ("Search / filter se koi site match nahi hui." if is_filtered
           else f"Is company me “{PROJECT_MATCH}” project ki koi site nahi hai. Site Data page se site add karein.")
        + '</div>', unsafe_allow_html=True)

elif st.session_state.dg_view_mode == "cards":
    for page_pos, (_, row) in enumerate(df_page.iterrows()):
        serial_no = start_idx + page_pos + 1
        with st.container(border=True):
            doc_rows = "".join(
                f"<div class='site-card-row'><span class='site-card-label'>{d['label']}</span>"
                f"<span class='site-card-value'>{status_badge(row[d['label'] + ' Status'])}</span></div>" for d in DOCS)
            st.markdown(f"""
                <div class="site-card-title">#{serial_no} — {escape(row['Site ID'] or '-')} | {escape(row['Site Name'] or '-')}</div>
                <div class="site-card-sub">{escape(row['Project ID'] or '-')} • {escape(row['Cluster'] or '-')}</div>
                <div class="site-card-row"><span class="site-card-label">Team Name</span><span class="site-card-value">{escape(row['Team Name'] or '-')}</span></div>
                <div class="site-card-row"><span class="site-card-label">Site Status</span><span class="site-card-value">{status_badge(row['Site Status'])}</span></div>
                {doc_rows}
                <div class="site-card-row"><span class="site-card-label">Remark</span><span class="site-card-value">{escape(row['Remark'] or '-')}</span></div>
            """, unsafe_allow_html=True)
            if st.button("⚙️ Manage", key=f"dg_card_{row['id']}", use_container_width=True):
                open_site(row["id"])

else:
    COL_RATIOS = [0.45, 0.45, 1.4, 1.1, 1.4, 1.7, 1.1, 1.3, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 2.2]
    COL_LABELS = ["#", "⚙️", "PROJECT NAME", "SITE ID", "PROJECT ID", "SITE NAME", "CLUSTER", "TEAM NAME", "SITE STATUS",
                  "SRC STATUS", "DC STATUS", "E-WAY STATUS", "PHOTO STATUS", "POD STATUS", "REMARK"]

    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">⚡ DG Site Register<span>newest first • ⚙️ se site kholein</span></div>'
        f'<div class="slux-badge">Page {st.session_state.dg_current_page} / {total_pages}</div>'
        '</div>', unsafe_allow_html=True)

    with st.container(key="site_lux_wrap"):
        with st.container(key="slux_head"):
            for h_idx, (h_col, label) in enumerate(zip(st.columns(COL_RATIOS, vertical_alignment="center"), COL_LABELS)):
                h_col.markdown(f"<div class='slux-th{' c' if h_idx < 2 else ''}'>{label}</div>", unsafe_allow_html=True)

        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            rid = row["id"]
            serial_no = start_idx + page_pos + 1
            parity = "odd" if serial_no % 2 else "even"
            with st.container(key=f"sluxrow_{parity}_{rid}"):
                rc = st.columns(COL_RATIOS, vertical_alignment="center")
                rc[0].markdown(f"<div style='text-align:center;'><span class='slux-num'>{serial_no}</span></div>", unsafe_allow_html=True)
                with rc[1]:
                    if st.button("⚙️", key=f"mgrbtn_{rid}", help="Manage (Documents / Status)"):
                        open_site(rid)
                rc[2].markdown(_txt(row["Project Name"], "slux-strong"), unsafe_allow_html=True)
                rc[3].markdown(_chip(row["Site ID"]), unsafe_allow_html=True)
                rc[4].markdown(_chip(row["Project ID"], "proj"), unsafe_allow_html=True)
                rc[5].markdown(_txt(row["Site Name"], "slux-strong"), unsafe_allow_html=True)
                rc[6].markdown(_pill(row["Cluster"]), unsafe_allow_html=True)
                rc[7].markdown(_txt(row["Team Name"], "slux-strong"), unsafe_allow_html=True)
                rc[8].markdown(status_badge(row["Site Status"]), unsafe_allow_html=True)
                for i, col in enumerate(STATUS_COLS):
                    rc[9 + i].markdown(status_badge(row[col]), unsafe_allow_html=True)
                rc[14].markdown(_txt(row["Remark"], "slux-soft"), unsafe_allow_html=True)

    shown_from = start_idx + 1 if total_rows else 0
    shown_to = min(end_idx, total_rows)
    st.markdown(
        '<div class="slux-foot">'
        f'<div>Total {total_rows:,} DG site{"s" if total_rows != 1 else ""}<small>Showing {shown_from}–{shown_to}</small></div>'
        f'<div class="slux-foot-badge">Page {st.session_state.dg_current_page} of {total_pages}</div>'
        '</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- 8. NEXT / PREVIOUS PAGINATION CONTROLS ---
def _reset_dg_page():
    st.session_state.dg_current_page = 1


_rp_space, _rp_col = st.columns([6, 1.3])
with _rp_col:
    st.selectbox("Rows per page", [25, 50, 100, 200], key="dg_rows_per_page", on_change=_reset_dg_page,
                 help="Ek page par kitni lines dikhni chahiye (default 100).")

with st.container(key="slux_pager"):
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.dg_current_page == 1)):
            st.session_state.dg_current_page -= 1
            st.rerun()
    with col_p2:
        _, jc2, _ = st.columns([2, 1.3, 2])
        with jc2:
            page_input = st.number_input("Go to page", min_value=1, max_value=total_pages, step=1,
                                         key="dg_page_jump_input", label_visibility="collapsed")
        st.markdown(f"<div class='page-count'>Page {st.session_state.dg_current_page} of {total_pages} "
                    f"(Total Records: {total_rows})</div>", unsafe_allow_html=True)
        if page_input != st.session_state.dg_current_page:
            st.session_state.dg_current_page = int(page_input)
            st.rerun()
    with col_p3:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.dg_current_page == total_pages)):
            st.session_state.dg_current_page += 1
            st.rerun()
