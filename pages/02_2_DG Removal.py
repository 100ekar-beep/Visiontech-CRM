"""
DG Project page
- site_data me jin sites ka Project Name "DG Removal" hai (active company/workspace ke), wo yaha dikhti hain
- SRC / DC / E-Way / Photo / POD status + Remark seedha site_data me save hote hain
- Files Cloudflare R2 me upload hoti hain (Site Data page jaisa hi), URL site_data ke "<X> Files" column me
  => Site Data page aur ye page hamesha same data dikhate hain
"""
import io
import os
import subprocess
import tempfile
import uuid
from html import escape

import boto3
import pandas as pd
import streamlit as st
from botocore.client import Config
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from supabase import create_client, Client

st.set_page_config(page_title="DG Project", page_icon="⚡", layout="wide")

# ============================== CONFIG ==============================
PROJECT_MATCH = "DG Removal"          # Project Name me ye text ho to site yaha aayegi
STATUS_OPTS = ["Pending", "Available", "Not Required"]
ALLOWED_EXT = ["pdf", "jpg", "jpeg", "png"]
MAX_PHOTOS = 15
REMARK_COL = "Remark"

# label, status column, files column, R2 folder, filename tag, icon
DOCS = [
    {"label": "SRC",   "status": "SRC Status",  "files": "SRC Files",    "folder": "src",    "tag": "SRC",   "icon": "📑"},
    {"label": "DC",    "status": "DC Status",   "files": "DC Files",     "folder": "dc",     "tag": "DC",    "icon": "📦"},
    {"label": "E-Way", "status": "EWAY Status", "files": "EWAY Files",   "folder": "eway",   "tag": "EWAY",  "icon": "🚚"},
    {"label": "Photo", "status": "Photos",      "files": "Photos Files", "folder": "photos", "tag": "Photo", "icon": "📷"},
    {"label": "POD",   "status": "POD Status",  "files": "POD Files",    "folder": "pod",    "tag": "POD",   "icon": "✅"},
]
# site_data me ye columns naye add karne hain (baaki pehle se hain)
NEW_COLS = ["SRC Status", "DC Status", "EWAY Status", "POD Status", "POD Files", REMARK_COL]

SITE_COMPANIES = [("VISPL", "VISPL"), ("Bhagyashree", "Bhagyashree"), ("Sai Tele", "Sai Tele")]
SITE_COMPANY_WORKSPACE_MAP = {"VISPL": "VISPL", "Bhagyashree": "BHAGYASHREE", "Sai Tele": "SAI TELE SERVICES"}
if "site_active_company" not in st.session_state:
    st.session_state.site_active_company = "VISPL"
st.session_state["active_workspace"] = SITE_COMPANY_WORKSPACE_MAP.get(st.session_state.site_active_company, "VISPL")

# ============================== CSS ==============================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); }
[data-testid="stSidebarNav"] a {
    padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
    background: rgba(255,255,255,0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
}
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.1) !important; color: #fff !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #fff !important;
}
[data-testid="stSidebarNav"] a span { color: inherit !important; }
label p, label[data-testid="stWidgetLabel"] p { color: #0f172a !important; font-weight: 700 !important; }

.st-key-dg_company_nav button { font-weight: 800 !important; padding: 12px 10px !important; border-radius: 12px !important; }
.st-key-dg_company_nav button[kind="primary"] { background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important; border: none !important; }

.dg-banner { background: linear-gradient(100deg, #1e1b4b 0%, #312e81 50%, #5b21b6 100%);
    border-radius: 16px; padding: 18px 24px; margin: 6px 0 18px; color: #fff; }
.dg-banner h1 { color: #fff !important; margin: 0; font-size: 1.9rem; font-weight: 900; }
.dg-banner p { color: #c7d2fe; margin: 2px 0 0; font-weight: 600; }

.dg-kpis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 12px; }
@media (max-width: 1000px) { .dg-kpis { grid-template-columns: repeat(3, 1fr); } }
.dg-kpi { background: #fff; border: 1px solid #e0e7ff; border-radius: 14px; padding: 14px 16px;
    border-top: 4px solid var(--c); box-shadow: 0 10px 24px -16px rgba(79,70,229,.45); }
.dg-kpi .l { font-size: .78rem; font-weight: 800; color: #64748b; }
.dg-kpi .v { font-size: 1.7rem; font-weight: 900; color: #0f172a; line-height: 1.2; }

.dg-status-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 18px; }
.dg-chip { background: #fff; border: 1px solid #e2e8f0; border-radius: 999px; padding: 5px 12px;
    font-size: .82rem; font-weight: 700; color: #334155; }
.dg-chip b { color: #4338ca; margin-left: 6px; }

.dg-info { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; background: #f8fafc;
    border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; margin-bottom: 8px; }
.dg-info div { font-size: .75rem; color: #64748b; font-weight: 700; }
.dg-info b { display: block; font-size: .92rem; color: #0f172a; margin-top: 2px; word-break: break-word; }
.dg-sec { color: #475569; font-size: .85rem; font-weight: 800; margin: 14px 0 6px;
    border-bottom: 1px solid rgba(0,0,0,.1); padding-bottom: 4px; }
.dg-file { font-size: .85rem; color: #0f172a; word-break: break-all; padding-top: 6px; }
</style>
""", unsafe_allow_html=True)


# ============================== CONNECTIONS (same as Site Data page) ==============================
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
    """R2 se file hatao (fail ho to bhi site_data se link hat chuka hoga)."""
    if r2_client is None or not R2_PUBLIC_URL or not url.startswith(R2_PUBLIC_URL + "/"):
        return
    try:
        r2_client.delete_object(Bucket=R2_BUCKET, Key=url[len(R2_PUBLIC_URL) + 1:])
    except Exception:
        pass


# ============================== DATA HELPERS ==============================
def _clean(v):
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("nan", "none", "null") else s


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


def update_site(rid, payload):
    supabase.table("site_data").update(payload).eq("id", rid).execute()
    fetch_dg_sites.clear()


def flash(kind, msg):
    st.session_state["dg_flash"] = (kind, msg)


# ============================== SITE DIALOG ==============================
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
    picked = st.file_uploader(f"{doc['label']} files add karein (PDF, JPG, PNG; multiple allowed)",
                              type=ALLOWED_EXT, accept_multiple_files=True, key=f"dg_up_{f}_{rid}")
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
                ss[f"dg_msg_{rid}"] = f"{len(uploaded)} {doc['label']} file(s) upload hui, status Available."
                st.rerun(scope="fragment")
            except Exception as e:
                st.error(f"site_data update nahi hua: {e}")

    if not files:
        st.caption(f"Abhi koi {doc['label']} file nahi hai.")
    for url in files:
        name = url.rsplit("/", 1)[-1]
        c1, c2, c3 = st.columns([6, 1.3, 1])
        icon = "📄" if name.lower().endswith(".pdf") else "🖼️"
        c1.markdown(f"<div class='dg-file'>{icon} {escape(name)}</div>", unsafe_allow_html=True)
        c2.link_button("Open", url, use_container_width=True)
        with c3.popover("🗑️"):
            st.write("Ye file delete karein?")
            if st.button("Delete", key=f"dg_del_{f}_{rid}_{name}", type="primary"):
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
                    ss[f"dg_msg_{rid}"] = f"{name} delete ho gayi."
                    st.rerun(scope="fragment")
                except Exception as e:
                    st.error(f"Delete nahi hua: {e}")

    opts = STATUS_OPTS if ss[st_key] in STATUS_OPTS else [ss[st_key]] + STATUS_OPTS
    st.selectbox(f"{doc['label']} Status", opts, key=st_key)


@st.dialog("⚡ DG Site", width="large")
def dg_site_dialog(rec):
    ss = st.session_state
    rid = rec["id"]

    st.markdown(
        "<div class='dg-info'>"
        + "".join(f"<div>{lbl}<b>{escape(_clean(rec.get(col)) or '—')}</b></div>"
                  for lbl, col in [("Project Name", "Project Name"), ("Project ID", "Project ID"),
                                   ("Site ID", "Site ID"), ("Site Name", "Site Name"), ("Cluster", "Cluster")])
        + "</div>", unsafe_allow_html=True)

    msg = ss.pop(f"dg_msg_{rid}", None)
    if msg:
        st.success(msg)

    st.markdown("<div class='dg-sec'>Documents</div>", unsafe_allow_html=True)
    tab_labels = []
    for doc in DOCS:
        n = len(ss.get(f"dg_files_{doc['folder']}_{rid}", parse_files(rec.get(doc["files"]))))
        tab_labels.append(f"{doc['icon']} {doc['label']} ({n})")
    for tab, doc in zip(st.tabs(tab_labels), DOCS):
        with tab:
            _render_doc(rec, doc)

    st.markdown("<div class='dg-sec'>Site Status & Remark</div>", unsafe_allow_html=True)
    ss_key, rm_key = f"dg_sitestatus_{rid}", f"dg_remark_{rid}"
    cur_ss = _clean(rec.get("Site Status"))
    ss_opts = site_status_options()
    if cur_ss not in ss_opts:
        ss_opts = [cur_ss] + ss_opts
    if ss_key not in ss:
        ss[ss_key] = cur_ss
    if rm_key not in ss:
        ss[rm_key] = _clean(rec.get(REMARK_COL))

    c1, c2 = st.columns([1, 2])
    c1.selectbox("Site Status", ss_opts, key=ss_key, format_func=lambda x: x or "—")
    c2.text_area("Remark", key=rm_key, height=90)

    if st.button("💾 Save changes", type="primary", use_container_width=True, key=f"dg_save_{rid}"):
        payload = {"Site Status": ss[ss_key], REMARK_COL: ss[rm_key].strip()}
        for doc in DOCS:
            payload[doc["status"]] = ss[f"dg_st_{doc['folder']}_{rid}"]
        try:
            update_site(rid, payload)
            flash("success", f"{_clean(rec.get('Site ID'))} save ho gaya (site_data me bhi update).")
            st.rerun()
        except Exception as e:
            st.error(f"Save nahi hua: {e}")


# ============================== PAGE ==============================
with st.container(key="dg_company_nav"):
    for nav_col, (cid, clabel) in zip(st.columns(len(SITE_COMPANIES)), SITE_COMPANIES):
        with nav_col:
            active = st.session_state.site_active_company == cid
            if st.button(clabel, key=f"dg_nav_{cid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.site_active_company = cid
                st.session_state.active_workspace = SITE_COMPANY_WORKSPACE_MAP[cid]
                st.rerun()

ws = st.session_state.active_workspace
st.markdown(f"<div class='dg-banner'><h1>⚡ DG Project</h1>"
            f"<p>{escape(st.session_state.site_active_company)} ki “{PROJECT_MATCH}” sites</p></div>",
            unsafe_allow_html=True)

if "dg_flash" in st.session_state:
    kind, text = st.session_state.pop("dg_flash")
    getattr(st, kind)(text)

top_l, top_r = st.columns([6, 1])
with top_r:
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_dg_sites.clear()
        st.rerun()

try:
    rows = fetch_dg_sites(ws)
except Exception as e:
    st.error(f"site_data load nahi hua: {e}")
    st.stop()

if not rows:
    st.info(f"Is company me “{PROJECT_MATCH}” project ki koi site nahi mili.")
    st.stop()

available_cols = set().union(*(r.keys() for r in rows))
missing = [c for c in NEW_COLS if c not in available_cols]
if missing:
    st.error("site_data me ye columns abhi nahi hain. Supabase SQL Editor me `dg_project_setup.sql` run karein, "
             "phir Refresh dabayein: " + ", ".join(missing))
    st.stop()

raw_by_id = {r["id"]: r for r in rows}
records = []
for r in rows:
    rec = {
        "id": r["id"],
        "created_at": r.get("created_at"),
        "Project Name": _clean(r.get("Project Name")),
        "Site ID": _clean(r.get("Site ID")),
        "Project ID": _clean(r.get("Project ID")),
        "Site Name": _clean(r.get("Site Name")),
        "Cluster": _clean(r.get("Cluster")),
        "Site Status": _clean(r.get("Site Status")),
    }
    for doc in DOCS:
        rec[f"{doc['label']} Status"] = effective_status(r.get(doc["status"]), parse_files(r.get(doc["files"])))
    rec["Remark"] = _clean(r.get(REMARK_COL))
    records.append(rec)

df = pd.DataFrame(records)
if "created_at" in df.columns:
    df["_ts"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("_ts", ascending=False).drop(columns=["_ts"]).reset_index(drop=True)

STATUS_COLS = [f"{d['label']} Status" for d in DOCS]


def is_pending(series):
    return series.str.strip().str.lower() == "pending"


# ---------- Summary ----------
kpis = [("Total Sites", len(df), "#6366f1")] + [
    (f"{d['label']} Pending", int(is_pending(df[f"{d['label']} Status"]).sum()), c)
    for d, c in zip(DOCS, ["#14b8a6", "#f97316", "#ec4899", "#3b82f6", "#10b981"])
]
st.markdown("<div class='dg-kpis'>" + "".join(
    f"<div class='dg-kpi' style='--c:{c}'><div class='l'>{l}</div><div class='v'>{v:,}</div></div>"
    for l, v, c in kpis) + "</div>", unsafe_allow_html=True)

status_counts = df["Site Status"].replace("", "(Blank)").value_counts()
st.markdown("<div class='dg-status-row'>" + "".join(
    f"<span class='dg-chip'>{escape(str(k))}<b>{v}</b></span>" for k, v in status_counts.items()) + "</div>",
    unsafe_allow_html=True)

# ---------- Filters ----------
f1, f2, f3, f4 = st.columns([2.2, 1.5, 1.5, 1.5])
q = f1.text_input("Search", placeholder="Site ID, Site Name ya Project ID")
cl = f2.multiselect("Cluster", sorted(x for x in df["Cluster"].unique() if x))
ssf = f3.multiselect("Site Status", list(status_counts.index))
pend_map = {"All": None, **{f"{d['label']} Pending": f"{d['label']} Status" for d in DOCS}}
pf = f4.selectbox("Pending filter", list(pend_map))

view = df
if q:
    m = view[["Site ID", "Site Name", "Project ID"]].apply(
        lambda c: c.str.contains(q, case=False, regex=False)).any(axis=1)
    view = view[m]
if cl:
    view = view[view["Cluster"].isin(cl)]
if ssf:
    view = view[view["Site Status"].replace("", "(Blank)").isin(ssf)]
if pend_map[pf]:
    view = view[is_pending(view[pend_map[pf]])]
view = view.reset_index(drop=True)

# ---------- Table ----------
DISPLAY_COLS = ["Project Name", "Site ID", "Project ID", "Site Name", "Cluster", "Site Status"] + STATUS_COLS + ["Remark"]


def color_status(v):
    v = str(v).strip().lower()
    if v == "pending":
        return "background-color:#fef9c3;color:#a16207;font-weight:700"
    if v == "available":
        return "background-color:#dcfce7;color:#15803d;font-weight:700"
    if v == "not required":
        return "color:#64748b"
    return ""


table = view[DISPLAY_COLS]
styler = table.style
styler = (getattr(styler, "map", None) or styler.applymap)(color_status, subset=STATUS_COLS)

cap_l, cap_r = st.columns([5, 1])
cap_l.caption(f"{len(view)} of {len(df)} sites. Site kholne ke liye row pe click karein.")
cap_r.download_button("📥 CSV", table.to_csv(index=False).encode("utf-8"),
                      file_name="dg_project.csv", mime="text/csv", use_container_width=True)

if "dg_tbl_ver" not in st.session_state:
    st.session_state.dg_tbl_ver = 0
event = st.dataframe(styler, hide_index=True, use_container_width=True, height=520,
                     on_select="rerun", selection_mode="single-row",
                     key=f"dg_tbl_{st.session_state.dg_tbl_ver}")

sel_rows = event.selection.rows if event and event.selection else []
if sel_rows:
    rid = view.iloc[sel_rows[0]]["id"]
    # selection clear karo taaki dialog band karne ke baad dobara na khule
    st.session_state.dg_tbl_ver += 1
    # purani (stale) dialog state hatao, fresh data se kholo
    for k in [k for k in st.session_state.keys() if str(k).startswith("dg_") and str(k).endswith(f"_{rid}")]:
        del st.session_state[k]
    dg_site_dialog(raw_by_id[rid])
