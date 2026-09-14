import streamlit as st
import pandas as pd
import math
import io
import uuid
import subprocess
import tempfile
import os
import zipfile
import requests
import boto3
from botocore.client import Config
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
import smtplib  # <--- NEW: For Email Sending
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from st_keyup import st_keyup # <--- NEW: For Live Search without Enter
from datetime import datetime, timedelta # <--- Added for parsing existing date strings

--- 1. PAGE CONFIGURATION ---

st.set_page_config(page_title="Site Data Hub", page_icon="🏗️", layout="wide")

--- INITIALIZE SESSION STATES ---

if 'po_count' not in st.session_state:
st.session_state.po_count = 1

if 'mat_count' not in st.session_state:
st.session_state.mat_count = 1

if 'add_mat_count' not in st.session_state:
st.session_state.add_mat_count = 1

if 'pending_comm_email' not in st.session_state:
st.session_state.pending_comm_email = False
if 'comm_site_data' not in st.session_state:
st.session_state.comm_site_data = {}

if 'site_view_mode' not in st.session_state:
st.session_state.site_view_mode = "table"

--- MULTI-COMPANY TAB SETUP (single login — switch company inside this page) ---

SITE_COMPANIES = [
("VISPL", "VISPL"),
("Bhagyashree", "Bhagyashree"),
("Sai Tele", "Sai Tele"),
]
SITE_COMPANY_WORKSPACE_MAP = {
"VISPL": "VISPL",
"Bhagyashree": "BHAGYASHREE",
"Sai Tele": "SAI TELE SERVICES",
}
if 'site_active_company' not in st.session_state:
st.session_state.site_active_company = "VISPL"

Derive the actual workspace used by every query in this file from the active tab,

so switching tabs is the only thing needed — no separate per-company login required.

st.session_state['active_workspace'] = SITE_COMPANY_WORKSPACE_MAP.get(st.session_state.site_active_company, "VISPL")

--- 2. LAVISH CUSTOM CSS ---

st.markdown("""
<style>
/* Light Premium Theme */
.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

/* Top Action Buttons */
div.stButton > button {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    color: white !important;
    border: none;
    border-radius: 8px;
    font-weight: 800 !important;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.25);
}

/* Pagination Text & Button Font Color Fix */
.page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #334155; margin-top: 10px; }

div.stButton > button p, 
div.stButton > button span, 
div.stButton > button div {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Modal/Dialog Glassmorphism */
div[data-testid="stDialog"] > div {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 16px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* FIX FOR DIALOG TITLE AND CAPTION COLOR */
div[data-testid="stDialog"] h1, 
div[data-testid="stDialog"] h2, 
div[data-testid="stDialog"] h3 {
    color: #0f172a !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px;
}
div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p,
div[data-testid="stDialog"] p {
    color: #1e293b !important; 
}
div[data-testid="stDialog"] button[kind="icon"] svg {
    fill: #0f172a !important; 
}

.modal-section-title {
    color: #475569;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 15px;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    padding-bottom: 5px;
}

/* FIX FOR FIELD LABELS COLOR (dark black, bold) */
label p, label[data-testid="stWidgetLabel"] p {
    color: #0f172a !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
}

/* Make disabled/read-only input text inside Warehouse Site Info strictly BLACK and BOLD */
div[data-testid="stTextInput"] input:disabled {
    color: #000000 !important;
    font-weight: 700 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* =========================================================
   PREMIUM SIDEBAR NAVIGATION BUTTONS (kept dark for contrast
   against the now-light main content, matching other pages)
   ========================================================= */

/* Sidebar Background */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Individual Sidebar Links / Buttons */
[data-testid="stSidebarNav"] a {
    padding: 0.85rem 1.2rem !important;
    margin: 0.5rem 1rem !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.03) !important;
    color: #cbd5e1 !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    transition: all 0.3s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
}

/* Hover Effect for Sidebar Links */
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    transform: translateX(4px) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    color: #ffffff !important;
}

/* Active/Selected Page Button */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    border-color: transparent !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
}

/* Clean up the default Streamlit styling overrides */
[data-testid="stSidebarNav"] a span {
    color: inherit !important;
}

/* =========================================================
   FIXED: HORIZONTAL SCROLLING DATA TABLE WITH PERFECT SPACING
   ========================================================= */
.st-key-site_table_wrap {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.15);
    border-radius: 10px;
    overflow: auto !important; /* Enables both Horizontal & Vertical Scroll */
    padding: 0px 0 !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}
/* Every row: plain white background, clear bottom border (simple clean grid, no colour fill) */
.st-key-site_table_wrap div[data-testid="stHorizontalBlock"] {
    min-width: 4600px !important;
    align-items: center !important;
    border-bottom: 1px solid rgba(0,0,0,0.12) !important;
    padding: 8px 0 !important;
    flex-wrap: nowrap !important;
    background: #ffffff !important;
}
/* Header row = the one row that contains .tbl-head cells — targeted directly
   instead of :first-of-type (which unreliably matched every row in Streamlit's
   nested DOM and painted the whole table purple). */
.st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:has(.tbl-head) {
    background: #eef2ff !important;
    border-bottom: 2px solid rgba(79,70,229,0.35) !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 2 !important;
}
.st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:not(:has(.tbl-head)):hover {
    background: #f8fafc !important;
}
/* Cell padding and border — visible grid lines between columns, like a real table */
.st-key-site_table_wrap div[data-testid="column"] {
    padding: 0 15px !important; /* Increased padding for proper spacing */
    display: flex;
    align-items: center;
    justify-content: flex-start;
    border-right: 1px solid rgba(0,0,0,0.08);
}
.st-key-site_table_wrap div[data-testid="column"]:last-child {
    border-right: none;
}

.st-key-site_table_wrap .tbl-head {
    background: transparent;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: #312e81;
    text-transform: uppercase;
    white-space: nowrap !important;
}
/* Strict nowrap with ellipsis to prevent column bleeding */
.st-key-site_table_wrap .tbl-cell {
    color: #0f172a;
    font-size: 0.86rem;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    width: 100%;
}
.st-key-site_table_wrap .tbl-serial {
    color: #64748b;
    font-size: 0.85rem;
    font-weight: 800;
}

/* Fixed native Action Buttons strictly constrained to their columns */
.st-key-site_table_wrap button {
    height: 32px !important;
    width: 100% !important;
    padding: 0 !important;
    min-height: 0 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #f1f5f9 !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
    box-shadow: none !important;
    pointer-events: auto !important; /* Force clickability */
    cursor: pointer !important;
}
.st-key-site_table_wrap button:hover {
    background: #3b82f6 !important;
    border-color: #60a5fa !important;
    transform: translateY(-2px) !important;
}

/* -------------------------------------------------------------
   FORCE LEFT BUTTON CSS: Action Columns (2 = Manage, 3 = Material)
   ------------------------------------------------------------- */
.st-key-site_table_wrap div[data-testid="column"]:nth-child(1) {
    padding: 0 10px 0 15px !important;
}
.st-key-site_table_wrap div[data-testid="column"]:nth-child(2) .tbl-head,
.st-key-site_table_wrap div[data-testid="column"]:nth-child(3) .tbl-head {
    color: #475569; 
}
.st-key-site_table_wrap div[data-testid="column"]:nth-child(2) {
    padding: 4px 4px !important;
    border-right: none !important;
}
.st-key-site_table_wrap div[data-testid="column"]:nth-child(3) {
    padding: 4px 15px 4px 4px !important;
    border-right: 1px solid rgba(0,0,0,0.05) !important;
}

/* Round, color-coded, compact action icon buttons */
.st-key-site_table_wrap div[class*="st-key-mgrbtn_"] button,
.st-key-site_table_wrap div[class*="st-key-mbtn_"] button {
    width: 100% !important; 
    max-width: 34px !important;
    height: 32px !important;
    padding: 0 !important;
    border-radius: 6px !important;
    font-size: 0.95rem !important;
    margin: 0 auto !important;
}
div[class*="st-key-mgrbtn_"] button { background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important; }
div[class*="st-key-mbtn_"] button { background: rgba(168,85,247,0.15) !important; border: 1px solid rgba(168,85,247,0.3) !important; }

/* Status badge pill */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.4px;
    white-space: nowrap !important;
    text-align: center;
}
.status-green  { background: rgba(34,197,94,0.15);  color: #15803d; }
.status-blue   { background: rgba(59,130,246,0.15); color: #1d4ed8; }
.status-yellow { background: rgba(234,179,8,0.15);  color: #a16207; }
.status-red    { background: rgba(239,68,68,0.15);  color: #b91c1c; }
.status-grey   { background: rgba(148,163,184,0.18); color: #334155; }

/* =========================================================
   MOBILE-FRIENDLY CARD VIEW
   ========================================================= */
.site-card {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.10);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}
.site-card-title { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; }
.site-card-sub { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
.site-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed rgba(0,0,0,0.08); font-size: 0.85rem; }
.site-card-row:last-child { border-bottom: none; }
.site-card-label { color: #64748b; font-weight: 600; }
.site-card-value { color: #0f172a; font-weight: 600; text-align: right; }

/* =========================================================
   MULTI-COMPANY NAV BAR (VISPL / Bhagyashree / Sai Tele)
   ========================================================= */
.st-key-site_company_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
.st-key-site_company_nav_bar button {
    font-size: 1.05rem !important; font-weight: 800 !important; padding: 14px 10px !important;
    height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
    white-space: nowrap !important;
}
.st-key-site_company_nav_bar button[kind="secondary"] {
    background: #ffffff !important; color: #475569 !important;
    border: 1.5px solid rgba(0,0,0,0.12) !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important;
}
.st-key-site_company_nav_bar button[kind="secondary"]:hover {
    background: #f1f5f9 !important; color: #0f172a !important;
    border-color: rgba(0,0,0,0.2) !important; transform: translateY(-2px) !important;
}
.st-key-site_company_nav_bar button[kind="secondary"] p,
.st-key-site_company_nav_bar button[kind="secondary"] span,
.st-key-site_company_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
.st-key-site_company_nav_bar button[kind="secondary"]:hover p,
.st-key-site_company_nav_bar button[kind="secondary"]:hover span,
.st-key-site_company_nav_bar button[kind="secondary"]:hover div { color: #0f172a !important; }
.st-key-site_company_nav_bar button[kind="primary"] {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
    border: none !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
}
.st-key-site_company_nav_bar button[kind="primary"] p,
.st-key-site_company_nav_bar button[kind="primary"] span,
.st-key-site_company_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; }

/* =========================================================
   LAVISH ATTACHMENT UPLOAD ZONES (Photo / JMS / Comm. Report)
   The whole colourful drop-zone IS the upload control now — click
   "Browse files" inside it and the OS file picker opens directly,
   no extra reveal/confirm click needed.
   ========================================================= */
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"],
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"],
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] {
    border: none !important;
    border-radius: 14px !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
    padding: 10px !important;
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.45) !important;
}
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%) !important;
    box-shadow: 0 6px 16px rgba(239, 68, 68, 0.40) !important;
}
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.40) !important;
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"]:hover,
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"]:hover,
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"]:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.08);
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] *,
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"] *,
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] * {
    color: #ffffff !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] svg,
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"] svg,
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] svg {
    fill: #ffffff !important;
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] button,
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"] button,
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] button {
    background: rgba(255,255,255,0.25) !important;
    border: 1.5px solid rgba(255,255,255,0.65) !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
}
.st-key-attach_lav_photo [data-testid="stFileUploaderDropzone"] button:hover,
.st-key-attach_lav_jms [data-testid="stFileUploaderDropzone"] button:hover,
.st-key-attach_lav_report [data-testid="stFileUploaderDropzone"] button:hover {
    background: rgba(255,255,255,0.4) !important;
}

/* Row 2 attachments: MRN / SRC / DC / EWAY — same lavish drop-zone pattern */
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"],
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"],
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"],
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] {
    border: none !important;
    border-radius: 14px !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
    padding: 10px !important;
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%) !important;
    box-shadow: 0 6px 16px rgba(139, 92, 246, 0.45) !important;
}
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #14b8a6 0%, #0891b2 100%) !important;
    box-shadow: 0 6px 16px rgba(20, 184, 166, 0.40) !important;
}
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #f97316 0%, #eab308 100%) !important;
    box-shadow: 0 6px 16px rgba(249, 115, 22, 0.40) !important;
}
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #ec4899 0%, #be123c 100%) !important;
    box-shadow: 0 6px 16px rgba(236, 72, 153, 0.40) !important;
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"]:hover,
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"]:hover,
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"]:hover,
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"]:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.08);
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"] *,
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"] *,
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"] *,
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] * {
    color: #ffffff !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"] svg,
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"] svg,
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"] svg,
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] svg {
    fill: #ffffff !important;
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"] button,
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"] button,
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"] button,
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] button {
    background: rgba(255,255,255,0.25) !important;
    border: 1.5px solid rgba(255,255,255,0.65) !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
}
.st-key-attach_lav_mrn [data-testid="stFileUploaderDropzone"] button:hover,
.st-key-attach_lav_src [data-testid="stFileUploaderDropzone"] button:hover,
.st-key-attach_lav_dc [data-testid="stFileUploaderDropzone"] button:hover,
.st-key-attach_lav_eway [data-testid="stFileUploaderDropzone"] button:hover {
    background: rgba(255,255,255,0.4) !important;
}

/* Download button — distinct indigo "call to action" style.
   st.link_button renders as an <a> tag, not <button>, so both are targeted. */
div[class*="st-key-attach_lav_download_"] button,
div[class*="st-key-attach_lav_download_"] a {
    background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.40) !important;
    margin-top: 6px;
    margin-bottom: 6px;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 800 !important;
    display: flex !important;
    justify-content: center !important;
    text-decoration: none !important;
}
div[class*="st-key-attach_lav_download_"] button:hover,
div[class*="st-key-attach_lav_download_"] a:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.1);
}
div[class*="st-key-attach_lav_download_"] button p,
div[class*="st-key-attach_lav_download_"] button span,
div[class*="st-key-attach_lav_download_"] button div,
div[class*="st-key-attach_lav_download_"] a,
div[class*="st-key-attach_lav_download_"] a p,
div[class*="st-key-attach_lav_download_"] a span,
div[class*="st-key-attach_lav_download_"] a div {
    color: #ffffff !important; font-weight: 800 !important;
}

/* Available / Not Available status pill under each upload zone */
.attach-status {
    display: block;
    text-align: center;
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.4px;
    margin: 8px auto 6px auto;
    padding: 6px 14px;
    border-radius: 20px;
    width: fit-content;
}
.attach-status-available {
    background: rgba(21, 128, 61, 0.14);
    color: #15803d;
    border: 1px solid rgba(21, 128, 61, 0.35);
}
.attach-status-missing {
    background: rgba(148, 163, 184, 0.18);
    color: #64748b;
    border: 1px solid rgba(148, 163, 184, 0.3);
}
</style>

""", unsafe_allow_html=True)

--- MULTI-COMPANY NAV BAR (single login, switch company right here) ---

with st.container(key="site_company_nav_bar"):
nav_cols = st.columns(len(SITE_COMPANIES))
for nav_col, (company_id, company_label) in zip(nav_cols, SITE_COMPANIES):
is_active = st.session_state.site_active_company == company_id
with nav_col:
if st.button(
company_label, key=f"site_nav_{company_id}",
use_container_width=True, type=("primary" if is_active else "secondary")
):
st.session_state.site_active_company = company_id
st.session_state.active_workspace = SITE_COMPANY_WORKSPACE_MAP[company_id]
st.session_state.current_page = 1  # reset pagination when switching company
st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

--- 3. SUPABASE CONNECTION ---

FIX: Ab hardcoded URL/Key ki jagah st.secrets se liya jaa raha hai — isse

ek hi jagah (Streamlit Cloud Secrets) update karke sabhi pages naye

Supabase project se automatically connect ho jaate hain, har page ki

code alag se badalne ki zaroorat nahi padti.

@st.cache_resource
def init_connection():
try:
url: str = st.secrets["supabase"]["url"]
# Agar secrets me galti se '/rest/v1' ya trailing slash aa gaya ho, use clean kar dete hain
url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
key: str = st.secrets["supabase"]["key"]
return create_client(url, key)
except Exception as e:
st.error(f"🚨 Supabase connection error: {e}")
return None

supabase: Client = init_connection()

-------------------------------------------------------------

--- CLOUDFLARE R2 CONNECTION (for Photos / JMS / Commissioning Report uploads) ---

R2 is S3-API-compatible, so the standard boto3 's3' client works — we just

point it at Cloudflare's endpoint instead of AWS. Files are uploaded here

and their public download URL is saved as a comma-separated list in the

corresponding site_data column ("Photos Files", "JMS Files", etc.).

-------------------------------------------------------------

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
"""Resize + re-compress a photo before upload. A typical 4-5MB phone photo
usually comes down to 200-400KB this way, with barely any visible quality loss."""
try:
img = Image.open(uploaded_file)
img = ImageOps.exif_transpose(img)  # fix phone photo rotation
if img.mode in ("RGBA", "P", "LA"):
img = img.convert("RGB")
img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=quality, optimize=True)
buf.seek(0)
return buf, "image/jpeg", "jpg"
except Exception:
# If compression fails for any reason, upload the original rather than blocking the user
uploaded_file.seek(0)
orig_ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else "jpg"
return uploaded_file, (uploaded_file.type or "image/jpeg"), orig_ext

def _compress_pdf_bytes(raw_bytes):
"""Best-effort PDF compression, in order of how much it saves:
1) Ghostscript (if installed on the server via packages.txt) — big savings,
especially for scanned/image-heavy PDFs.
2) pypdf content-stream compression — modest but always safe fallback.
3) If both fail or don't shrink the file, the original bytes are kept.
"""
# --- Try Ghostscript first ---
try:
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
tmp_in.write(raw_bytes)
tmp_in_path = tmp_in.name
tmp_out_path = tmp_in_path.replace(".pdf", "_out.pdf")
subprocess.run(
[
"gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
"-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dBATCH", "-dQUIET",
f"-sOutputFile={tmp_out_path}", tmp_in_path,
],
check=True, timeout=60,
)
with open(tmp_out_path, "rb") as f:
gs_compressed = f.read()
os.unlink(tmp_in_path)
os.unlink(tmp_out_path)
if gs_compressed and len(gs_compressed) < len(raw_bytes):
return gs_compressed
except Exception:
pass  # Ghostscript not installed or failed — fall through to pypdf

# --- Fallback: pypdf content-stream compression (modest, but safe) ---
try:
    reader = PdfReader(io.BytesIO(raw_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # compress_content_streams() only works once the page belongs to a PdfWriter,
    # so this must run AFTER add_page(), not before.
    for page in writer.pages:
        try:
            page.compress_content_streams()
        except Exception:
            pass
    out_buf = io.BytesIO()
    writer.write(out_buf)
    pypdf_compressed = out_buf.getvalue()
    if pypdf_compressed and len(pypdf_compressed) < len(raw_bytes):
        return pypdf_compressed
except Exception:
    pass

return raw_bytes  # nothing worked better — upload as-is rather than fail

def upload_file_to_r2(uploaded_file, folder, project_id, site_id, field_tag):
"""Compresses (if image/PDF) then uploads one Streamlit UploadedFile to R2,
returning its public download URL. Filename format: ProjectID_SiteID_FieldTag_xxxx.ext
(e.g. OM-RESPS-0580588_IN-3279057_Photo_a1b2c3.jpg)."""
if r2_client is None:
raise RuntimeError("R2 client not configured — check [r2] section in Streamlit secrets.")

orig_name = uploaded_file.name
ext = orig_name.split(".")[-1].lower() if "." in orig_name else "bin"

if ext in ("jpg", "jpeg", "png"):
    file_obj, content_type, ext = _compress_image(uploaded_file)
elif ext == "pdf":
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    compressed_bytes = _compress_pdf_bytes(raw_bytes)
    file_obj = io.BytesIO(compressed_bytes)
    content_type = "application/pdf"
else:
    uploaded_file.seek(0)
    file_obj = uploaded_file
    content_type = uploaded_file.type or "application/octet-stream"

def _safe(v, fallback):
    cleaned = "".join(c for c in str(v) if c.isalnum() or c in ("-", "_"))
    return cleaned or fallback

safe_proj = _safe(project_id, "proj")
safe_site = _safe(site_id, "site")
safe_field = _safe(field_tag, "file")
object_key = f"{folder}/{safe_proj}_{safe_site}_{safe_field}_{uuid.uuid4().hex[:6]}.{ext}"
r2_client.upload_fileobj(
    file_obj,
    R2_BUCKET,
    object_key,
    ExtraArgs={"ContentType": content_type},
)
return f"{R2_PUBLIC_URL}/{object_key}"

def build_zip_from_urls(urls):
"""Fetches each file from its public R2 URL and bundles them into one
in-memory ZIP, so the user can download everything with a single click
instead of one click per file."""
zip_buf = io.BytesIO()
with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
used_names = set()
for url in urls:
try:
resp = requests.get(url, timeout=30)
resp.raise_for_status()
name = url.split("/")[-1] or f"file_{uuid.uuid4().hex[:6]}"
# avoid collisions inside the zip if two URLs somehow share a filename
final_name = name
dup_counter = 1
while final_name in used_names:
base, dot, extn = name.rpartition(".")
final_name = f"{base}{dup_counter}.{extn}" if dot else f"{name}{dup_counter}"
dup_counter += 1
used_names.add(final_name)
zf.writestr(final_name, resp.content)
except Exception:
continue  # skip a file that failed to fetch rather than failing the whole zip
zip_buf.seek(0)
return zip_buf.getvalue()

-------------------------------------------------------------

--- EGRESS OPTIMIZATION: CACHED DATA FETCHERS ---

Without this, every keystroke in search / every rerun re-downloads the

whole table from Supabase, which is what was eating up the free-tier

egress quota. These cache results for a short time (30s) so repeated

reruns (typing in search, opening dialogs, pagination) reuse the same

data instead of hitting Supabase again. Call .clear() right before any

insert/update/delete so the next read is fresh, not stale.

-------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def fetch_site_data_cached(workspace):
try:
response = supabase.table("site_data").select("*").eq("workspace", workspace).execute()
return response.data or []
except Exception:
return []

@st.cache_data(ttl=30, show_spinner=False)
def fetch_po_upload_identifiers_cached(workspace):
"""Returns the set of Project Name / Site ID values that already have a PO Working entry."""
identifiers = set()
try:
res_po = supabase.table("po_working").select("*").eq("workspace", workspace).execute()
for item in (res_po.data or []):
p_name = str(item.get("Project Name", "")).strip()
s_id = str(item.get("Site ID", "")).strip()
if p_name:
identifiers.add(p_name)
if s_id:
identifiers.add(s_id)
except Exception:
pass
return identifiers

def clear_site_data_cache():
"""Call this right before st.rerun() after any insert/update/delete on site_data or po_working."""
fetch_site_data_cached.clear()
fetch_po_upload_identifiers_cached.clear()

-------------------------------------------------------------

--- 🟢 NEW: BULK SYNC PO/WCC → SITE DATA ---

Backfills "PO No." and "WCC Number"/"WCC Status" into site_data rows

whose Project ID was added AFTER its PO/WCC was already uploaded via the

desktop PO & WCC Upload tool (that tool's one-time sync-on-upload

silently skips a Project ID that doesn't exist in site_data yet). This

only ever fills BLANK fields — anything already filled in is left alone.

-------------------------------------------------------------

def _fetch_all_rows_paginated(table_name, workspace):
"""Supabase caps a single select() at ~1000 rows by default — this
pages through with .range() so large workspaces are fully covered."""
all_rows = []
limit = 1000
offset = 0
while True:
res = supabase.table(table_name).select("*").eq("workspace", workspace) 
.range(offset, offset + limit - 1).execute()
chunk = res.data or []
if not chunk:
break
all_rows.extend(chunk)
if len(chunk) < limit:
break
offset += limit
return all_rows

def _split_list_field(raw):
"""Split a comma-joined site_data field into a clean list, same rules
used by the Add/Edit Site Data dialogs (drops empty / 'nan' junk)."""
items = []
normalized = str(raw if raw is not None else "").replace("|", ",")
for x in normalized.split(","):
x = x.strip()
if x and x.lower() not in ("nan", "none", "null"):
items.append(x)
return items

def run_bulk_sync_po_wcc(workspace):
"""
Returns a summary dict: {po_filled, wcc_filled, date_status_filled,
already_ok, no_site_row, errors}.

"PO No." and "WCC Number"/"WCC Status" are backfilled from po_working.
"PO Date" and "PO Status" aren't stored on po_working at all — but they
ARE already sitting in Supabase, just on a DIFFERENT site_data row: the
project that existed in Site Data at the moment the PO was originally
uploaded got its Date/Status written directly. So here we also scan
every OTHER site_data row for a matching PO Number and copy its Date/
Status across to any row that's missing them for that same PO.
"""
summary = {"po_filled": 0, "wcc_filled": 0, "date_status_filled": 0,
           "already_ok": 0, "no_site_row": 0, "errors": 0}
try:
    po_rows = _fetch_all_rows_paginated("po_working", workspace)

    # One summary entry per Project Name (= Project ID) — a project can
    # span many PO lines, so keep the LAST non-empty value seen for
    # each field.
    project_info = {}
    for r in po_rows:
        proj = str(r.get("Project Name", "")).strip()
        if not proj or proj.lower() == "nan":
            continue
        info = project_info.setdefault(proj, {"po_number": "", "wcc_number": "", "wcc_status": ""})
        po_num = str(r.get("PO Number", "")).strip()
        if po_num and po_num.lower() != "nan":
            info["po_number"] = po_num
        wcc_num = str(r.get("wcc_number", "") or "").strip()
        if wcc_num and wcc_num.lower() != "nan":
            info["wcc_number"] = wcc_num
        wcc_stat = str(r.get("wcc_status", "") or "").strip()
        if wcc_stat and wcc_stat.lower() != "nan":
            info["wcc_status"] = wcc_stat

    site_rows = _fetch_all_rows_paginated("site_data", workspace)

    # 🟢 Build PO Number -> (date, status) from whichever site_data row(s)
    # already have it recorded. A project can list multiple PO Numbers,
    # each with its own date/status at the same list position.
    po_date_status_map = {}
    for srow in site_rows:
        po_list = _split_list_field(srow.get("PO No.", ""))
        date_list = _split_list_field(srow.get("PO Date", ""))
        status_list = _split_list_field(srow.get("PO Status", ""))
        for idx, pono in enumerate(po_list):
            entry = po_date_status_map.setdefault(pono, {"date": "", "status": ""})
            if not entry["date"] and idx < len(date_list):
                entry["date"] = date_list[idx]
            if not entry["status"] and idx < len(status_list):
                entry["status"] = status_list[idx]

    for srow in site_rows:
        proj_id = str(srow.get("Project ID", "")).strip()
        if not proj_id or proj_id.lower() == "nan":
            continue
        info = project_info.get(proj_id)
        if not info:
            continue  # this project has no PO/WCC data uploaded at all yet

        update_payload = {}
        cur_po_no = str(srow.get("PO No.", "") or "").strip()
        if not cur_po_no and info["po_number"]:
            update_payload["PO No."] = info["po_number"]

        cur_wcc_no = str(srow.get("WCC Number", "") or "").strip()
        if not cur_wcc_no and info["wcc_number"]:
            update_payload["WCC Number"] = info["wcc_number"]
            if info["wcc_status"]:
                update_payload["WCC Status"] = info["wcc_status"]

        # 🟢 Backfill PO Date / PO Status by matching each PO Number this
        # row will end up having (existing + whatever we just filled in
        # above) against po_date_status_map.
        effective_po_list = _split_list_field(update_payload.get("PO No.", cur_po_no))
        cur_date = str(srow.get("PO Date", "") or "").strip()
        cur_status = str(srow.get("PO Status", "") or "").strip()
        if effective_po_list and (not cur_date or not cur_status):
            found_dates = [po_date_status_map.get(p, {}).get("date", "") for p in effective_po_list]
            found_statuses = [po_date_status_map.get(p, {}).get("status", "") for p in effective_po_list]
            if not cur_date and any(found_dates):
                update_payload["PO Date"] = ", ".join([d for d in found_dates if d])
            if not cur_status and any(found_statuses):
                update_payload["PO Status"] = ", ".join([s for s in found_statuses if s])

        if not update_payload:
            summary["already_ok"] += 1
            continue

        row_id = srow.get("id")
        if row_id is None:
            summary["errors"] += 1
            continue
        try:
            supabase.table("site_data").update(update_payload).eq("id", row_id).execute()
            if "PO No." in update_payload:
                summary["po_filled"] += 1
            if "WCC Number" in update_payload:
                summary["wcc_filled"] += 1
            if "PO Date" in update_payload or "PO Status" in update_payload:
                summary["date_status_filled"] += 1
        except Exception:
            summary["errors"] += 1

    matched_projects = {str(s.get("Project ID", "")).strip() for s in site_rows}
    summary["no_site_row"] = len([p for p in project_info if p not in matched_projects])
    return summary
except Exception as e:
    summary["errors"] += 1
    summary["fatal_error"] = str(e)
    return summary

@st.dialog("🔁 Bulk Sync PO/WCC → Site Data", width="large")
def bulk_sync_dialog():
active_ws = st.session_state.get('active_workspace', 'VISPL')
st.caption(
f"Scans '{active_ws}' workspace's PO/WCC uploads and fills in 'PO No.', 'PO Date'/'PO Status', and "
f"'WCC Number'/'WCC Status' for any Project ID that's currently BLANK — for example, sites that were "
f"added to Site Data after their PO/WCC was already uploaded. PO Date/Status are recovered by copying "
f"from another site that already has the same PO Number recorded. Fields that already have a value are never touched."
)

if st.session_state.get("bulk_sync_result"):
    result = st.session_state["bulk_sync_result"]
    st.markdown("---")
    if result.get("fatal_error"):
        st.error(f"❌ Bulk Sync failed: {result['fatal_error']}")
    else:
        st.markdown(f"""
            <div style="background: #f8fafc; padding: 15px 20px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08); margin-bottom: 15px;">
                <div style="font-weight:800; color:#0f172a; font-size:1.05rem; margin-bottom:10px;">📊 Bulk Sync Summary</div>
                <div style="color:#15803d; margin-bottom:4px;">✅ PO No. bhari gayi: <b>{result['po_filled']}</b> project(s)</div>
                <div style="color:#15803d; margin-bottom:4px;">✅ PO Date/Status bhari gayi (kisi doosri project ke record se copy karke): <b>{result['date_status_filled']}</b> project(s)</div>
                <div style="color:#15803d; margin-bottom:4px;">✅ WCC Number/Status bhari gayi: <b>{result['wcc_filled']}</b> project(s)</div>
                <div style="color:#64748b; margin-bottom:4px;">ℹ️ Pehle se sahi thi (kuch nahi kiya): <b>{result['already_ok']}</b> project(s)</div>
                <div style="color:#a16207; margin-bottom:4px;">⚠️ PO/WCC data hai par Site Data me site hi nahi hai: <b>{result['no_site_row']}</b> project(s)</div>
                <div style="color:#b91c1c;">❌ Errors: <b>{result['errors']}</b></div>
            </div>
        """, unsafe_allow_html=True)
        if result['no_site_row'] > 0:
            st.info(
                f"👉 In {result['no_site_row']} project(s) ka PO/WCC data upload ho chuka hai, lekin inki "
                f"Project ID abhi Site Data me hai hi nahi. Pehle 'Add Record' se site add karo, "
                f"phir Bulk Sync dobara chalao."
            )
    col_close, _ = st.columns([1, 3])
    with col_close:
        if st.button("✅ OK, Close This Summary", type="primary", use_container_width=True, key="bulk_sync_close"):
            st.session_state["bulk_sync_result"] = None
            st.rerun()
    st.markdown("---")

if st.button("🚀 Run Bulk Sync", type="primary", use_container_width=True, key="bulk_sync_run"):
    with st.spinner("po_working aur site_data scan kiya ja raha hai..."):
        summary = run_bulk_sync_po_wcc(active_ws)
    st.session_state["bulk_sync_result"] = summary
    clear_site_data_cache()
    st.rerun()

-------------------------------------------------------------

--- SMTP EMAIL SENDING CONFIGURATION

-------------------------------------------------------------

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "visiontechinfrasolution@gmail.com"

PRAMOD BHAU: YAHAN APNA 16-DIGIT APP PASSWORD DAALIYE

SENDER_PASSWORD = "ngamnbrvtlrnfrzm"

def send_commissioning_email(to_email, cc_email, subject, body):
try:
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = to_email
msg['Cc'] = cc_email
msg['Subject'] = subject

    # HTML MIME Type is used here so bold tags work perfectly
    msg.attach(MIMEText(body, 'html'))
    
    recipients = [e.strip() for e in to_email.split(',') if e.strip()]
    if cc_email:
        recipients.extend([e.strip() for e in cc_email.split(',') if e.strip()])
        
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
    server.quit()
    return True, "Email sent successfully"
except Exception as e:
    return False, f"SMTP Error: {str(e)}"

-------------------------------------------------------------

--- WHATSAPP SENDING LOGIC REMOVED (disabled for now) ---

-------------------------------------------------------------

--- 3.1 HELPER FOR DYNAMIC DROPDOWNS ---

def get_all_dropdowns():
try:
res = supabase.table("dropdown_master").select("*").execute()
return res.data if res.data else []
except Exception:
return []

def get_opts(category, all_data):
opts = [row["option_value"] for row in all_data if row["category"] == category]
return ["Select"] + opts

--- HELPER: FETCH ITEM MASTER DETAILS FOR AUTO-FILL IN MATERIAL MODAL ---

def get_item_master_details():
mapping = {}
table_names_to_try = ["Item Code", "item_code"]

for t_name in table_names_to_try:
    try:
        res = supabase.table(t_name).select("*").execute()
        if res.data:
            for item in res.data:
                code = str(item.get("item_code", "")).strip()
                if code:
                    mapping[code] = {
                        "description": str(item.get("item_description", "") or ""),
                        "stn_status": str(item.get("stn_status", "Required") or "Required"),
                        "material_of": str(item.get("material_of", "Indus") or "Indus"),
                        "rate": item.get("rate")
                    }
            return mapping 
    except Exception as e:
        continue
        
return mapping

--- 3.5 ADD RECORD DIALOG FUNCTION (POP-UP) ---

@st.dialog("📄 Add Site Data", width="large")
def add_record_dialog():
st.caption("Configure comprehensive site metrics and procurement status")

# --- FIX: Defensive re-init in case session_state got reset mid-dialog
# (happens on mobile/tablet when the websocket reconnects after backgrounding) ---
if 'po_count' not in st.session_state:
    st.session_state.po_count = 1
if 'add_mat_count' not in st.session_state:
    st.session_state.add_mat_count = 1

all_dd = get_all_dropdowns() 

with st.container():
    st.markdown('<div class="modal-section-title">🏢 SITE PARAMETERS & PROJECT EXECUTION</div>', unsafe_allow_html=True)
    
    # Row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        dept = st.selectbox("DEPARTMENT", get_opts("Department", all_dd))
    with c2:
        operator = st.selectbox("OPERATOR", get_opts("Operator", all_dd))
    with c3:
        proj_name = st.selectbox("PROJECT NAME", get_opts("Project Name", all_dd))
    with c4:
        proj_id = st.text_input("PROJECT ID * (REQUIRED)", placeholder="Project ID")
        
    # Row 2
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        site_id = st.text_input("Site ID * (REQUIRED)", placeholder="Enter Site ID")
        
    site_name_val = ""
    cluster_val = ""
    area_val = "N/A"
    km_val = "N/A"
    lat_val = "N/A"
    long_val = "N/A"
    tech_val = "N/A"
    fse_val = "N/A"
    aom_val = "N/A"
    
    if site_id:
        try:
            master_res = supabase.table("Excalation Matrix").select("*").eq("Site ID", site_id.strip()).execute()
            if master_res.data:
                site_name_val = master_res.data[0].get("Site Name", "")
                cluster_val = master_res.data[0].get("Cluster", "")
                area_val = master_res.data[0].get("Area", "N/A")
                km_val = master_res.data[0].get("KM", "N/A")
                lat_val = master_res.data[0].get("Lat", "N/A")
                long_val = master_res.data[0].get("Long", "N/A")
                tech_val = master_res.data[0].get("Technician Detail", "N/A")
                fse_val = master_res.data[0].get("FSE Detail", "N/A")
                aom_val = master_res.data[0].get("AOM Detail", "N/A")
                st.toast("Site Data Auto-Fetched Successfully! ✅", icon="✅")
            else:
                st.toast("Site ID not found in Excalation Matrix table ⚠️", icon="⚠️")
        except Exception as e:
            st.toast(f"Table Error: {e} ❌", icon="❌")

    with c6:
        site_name = st.text_input("SITE NAME", value=site_name_val, placeholder="Auto Fetch")
    with c7:
        cluster = st.text_input("CLUSTER", value=cluster_val, placeholder="Auto Fetch")
    with c8:
        site_status = st.selectbox("SITE STATUS", get_opts("Site Status", all_dd))

    st.markdown(f"""
        <div style="background: #f8fafc; padding: 15px 20px; border-radius: 8px; margin-top: 5px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.08);">
            <div style="display: flex; justify-content: space-around; margin-bottom: 12px;">
                <div style="color: #0f172a; font-weight: 600; font-size: 1rem;">🏢 Area: <span style="color: #2563eb;">{area_val}</span></div>
                <div style="color: #0f172a; font-weight: 600; font-size: 1rem;">📍 KM: <span style="color: #2563eb;">{km_val}</span></div>
                <div style="color: #0f172a; font-weight: 600; font-size: 1rem;">🌍 LAT LONG: <span style="color: #2563eb; white-space: pre;">{lat_val}  {long_val}</span></div>
            </div>
            <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(0,0,0,0.12); padding-top: 12px;">
                <div style="color: #0f172a; font-weight: 600; font-size: 0.95rem;">🧑‍🔧 Technician: <span style="color: #2563eb;">{tech_val}</span></div>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.95rem;">👨‍💼 FSE: <span style="color: #2563eb;">{fse_val}</span></div>
                <div style="color: #0f172a; font-weight: 600; font-size: 0.95rem;">👑 AOM: <span style="color: #2563eb;">{aom_val}</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
        
    st.markdown('<div class="modal-section-title">📦 MATERIAL, BILLING & RFAI DETAILS</div>', unsafe_allow_html=True)
    
    work_desc = st.text_input("WORK DESCRIPTION", placeholder="Enter detailed work description")
    
    c9, c10, c11, c12 = st.columns(4)
    with c9:
        product = st.selectbox("PRODUCT", get_opts("Product", all_dd))
    with c10:
        rfai_status = st.selectbox("RFAI STATUS", get_opts("RFAI Status", all_dd))
    with c11:
        wh_material = st.selectbox("WH MATERIAL", get_opts("WH Material", all_dd))
    with c12:
        team_name = st.selectbox("TEAM NAME", get_opts("Team Name", all_dd))

    c12a, c12b, c12c, c12d = st.columns(4)
    with c12a:
        photos_status = st.selectbox("PHOTOS", ["Select", "Available", "Pending"])
    with c12b:
        audit_status = st.selectbox("AUDIT", ["Select", "Done", "Pending", "Not Required"])
    with c12c:
        jms_status = st.selectbox("JMS", ["Select", "Available", "Pending", "Not Required"])
    with c12d:
        comm_report_status = st.selectbox("COMMISSIONING REPORT", ["Select", "Available", "Pending", "Not Required"])
        
    c13, c14, c15 = st.columns(3)
    with c13:
        ex_opts = get_opts("Extra Approval", all_dd)
        def_extra = ex_opts.index("Not Available") if "Not Available" in ex_opts else 0
        extra_approval = st.selectbox("EXTRA APPROVAL", ex_opts, index=def_extra)
    with c14:
        tb_opts = get_opts("Team Billing Status", all_dd)
        def_team = tb_opts.index("Pending") if "Pending" in tb_opts else 0
        team_billing = st.selectbox("TEAM BILLING STATUS", tb_opts, index=def_team)
    with c15:
        vb_opts = get_opts("Vision Billing Status", all_dd)
        def_vis = vb_opts.index("Pending") if "Pending" in vb_opts else 0
        vision_billing = st.selectbox("VISION BILLING STATUS", vb_opts, index=def_vis)

    st.markdown('<div class="modal-section-title">💰 PURCHASE ORDERS & WCC FINALIZATION</div>', unsafe_allow_html=True)
    
    po_nos, po_dates, po_statuses, wcc_nums, wcc_statuses = [], [], [], [], []
    
    for i in range(st.session_state.po_count):
        if i > 0:
            st.markdown(f"<p style='color:#334155; font-size:0.85rem; margin-top:10px; margin-bottom:5px; font-weight:700;'>➕ Additional PO & WCC {i+1}</p>", unsafe_allow_html=True)
        
        c17, c18, c19, c20, c21 = st.columns(5)
        with c17:
            p_n = st.text_input("PO NO.", placeholder="11 digits", key=f"po_no_{i}")
            po_nos.append(p_n)
        with c18:
            raw_p_d = st.date_input("PO DATE", value=None, key=f"po_date_{i}")
            p_d = raw_p_d.strftime("%d/%m/%Y") if raw_p_d else ""
            po_dates.append(p_d)
        with c19:
            p_s = st.selectbox("PO STATUS", get_opts("PO Status", all_dd), key=f"po_status_{i}")
            po_statuses.append(p_s)
        with c20:
            w_n = st.text_input("WCC NUMBER", placeholder="10 digits", key=f"wcc_num_{i}")
            wcc_nums.append(w_n)
        with c21:
            w_s = st.selectbox("WCC STATUS", get_opts("WCC Status", all_dd), key=f"wcc_status_{i}")
            wcc_statuses.append(w_s)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- FIXED ADD/REMOVE PO BUTTONS ---
    col_btn_add, col_btn_rem, _ = st.columns([3, 3, 4])
    with col_btn_add:
        if st.button("➕ Add Additional PO", use_container_width=True):
            st.session_state.po_count += 1
    with col_btn_rem:
        if st.session_state.po_count > 1:
            if st.button("➖ Remove PO", use_container_width=True):
                st.session_state.po_count -= 1
        
    # -------------------------------------------------------------
    # WAREHOUSE MATERIAL TRACKING IN ADD RECORD
    # -------------------------------------------------------------
    st.markdown('<div class="modal-section-title">📦 WAREHOUSE MATERIAL TRACKING (OPTIONAL)</div>', unsafe_allow_html=True)
    
    trans_types = get_opts("Transaction Type", all_dd)
    mat_status_opts = get_opts("Material Status", all_dd)
    stn_status_opts = get_opts("STN Status", all_dd)
    
    a_mat_trans_types, a_mat_boqs, a_mat_item_codes, a_mat_descs, a_mat_qtys = [], [], [], [], []
    a_mat_statuses, a_mat_dates, a_mat_stn_statuses, a_mat_remarks = [], [], [], []
    
    for i in range(st.session_state.add_mat_count):
        if i > 0:
            st.markdown(f"<p style='color:#334155; font-size:0.85rem; margin-top:15px; margin-bottom:5px; font-weight:700;'>➕ Transaction Item {i+1}</p>", unsafe_allow_html=True)
        
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            t_type = st.selectbox("TRANSACTION TYPE", trans_types, key=f"a_trans_{i}")
            a_mat_trans_types.append(t_type)
        with mc2:
            boq_no = st.text_input("BOQ NUMBER", placeholder="BOQ No", key=f"a_boq_{i}")
            a_mat_boqs.append(boq_no)
        with mc3:
            i_code = st.text_input("ITEM CODE", placeholder="Type & Press Enter", key=f"a_icode_{i}")
            a_mat_item_codes.append(i_code)

        code_val = i_code.strip()
        if code_val:
            try:
                item_res = supabase.table("Item Code").select("*").eq("item_code", code_val).execute()
                if not item_res.data:
                    item_res = supabase.table("item_code").select("*").eq("item_code", code_val).execute()
                    
                if item_res.data:
                    fetched_desc = str(item_res.data[0].get("item_description", ""))
                    fetched_stn = str(item_res.data[0].get("stn_status", "Required"))
                    
                    st.session_state[f"a_idesc_{i}"] = fetched_desc
                    if fetched_stn in stn_status_opts:
                        st.session_state[f"a_stn_{i}"] = fetched_stn
                        
                    st.toast("Item Data Auto-Fetched Successfully! ✅", icon="✅")
                else:
                    st.toast("Item Code not found in database ⚠️", icon="⚠️")
            except Exception as e:
                st.toast(f"Table Error: {e} ❌", icon="❌")

        with mc4:
            current_desc_val = st.session_state.get(f"a_idesc_{i}", "")
            i_desc = st.text_input("ITEM DESCRIPTION", value=current_desc_
