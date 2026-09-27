"""
DG Project page (Streamlit + Supabase)

- site_data me jin sites ka project name "DG Removal" hai, wo yaha dikhti hain
- SRC / DC / E-Way / Photo / POD status + Remark ek alag table (dg_project_tracker) me save hote hain
- SRC / DC / Photo / POD files (PDF / JPG / PNG, multiple) Supabase Storage me upload hoti hain
- Jo field site_data me bhi exist karti hai, uska change site_data me bhi update hota hai

Setup ke liye dg_project_setup.sql Supabase SQL Editor me ek baar run karein.
"""
import mimetypes
import re
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client

try:
    st.set_page_config(page_title="DG Project", page_icon="⚡", layout="wide")
except Exception:
    pass  # main app ne pehle hi set kar diya ho to ignore

# ============================== CONFIG ==============================
SITE_TABLE = "site_data"
TRACKER_TABLE = "dg_project_tracker"
DOCS_TABLE = "dg_project_documents"
BUCKET = "dg-project-docs"
PROJECT_NAME_VALUE = "DG Removal"

# site_data ke actual column names. Aapke table me naam alag hain to sirf right side badlein.
SD = {
    "project_name": "project_name",
    "site_id": "site_id",
    "project_id": "project_id",
    "site_name": "site_name",
    "cluster": "cluster",
    "site_status": "site_status",
}

STATUS_OPTIONS = ["Pending", "Done", "Not Required"]
STATUS_FIELDS = ["src_status", "dc_status", "eway_status", "photo_status", "pod_status"]
TRACK_FIELDS = STATUS_FIELDS + ["remark"]
STATUS_LABELS = {
    "src_status": "SRC", "dc_status": "DC", "eway_status": "E-Way",
    "photo_status": "Photo", "pod_status": "POD",
}
DOC_TYPES = {"SRC": "src_status", "DC": "dc_status", "Photo": "photo_status", "POD": "pod_status"}
ALLOWED_TYPES = ["pdf", "jpg", "jpeg", "png"]
IMAGE_EXT = (".jpg", ".jpeg", ".png")

DISPLAY = {
    "project_name": "Project Name", "site_id": "Site ID", "project_id": "Project ID",
    "site_name": "Site Name", "cluster": "Cluster", "site_status": "Site Status",
    "src_status": "SRC Status", "dc_status": "DC Status", "eway_status": "E-Way Status",
    "photo_status": "Photo Status", "pod_status": "POD Status", "remark": "Remark",
}


# ============================== SUPABASE ==============================
@st.cache_resource
def get_sb():
    # Agar app me pehle se supabase client bana hua hai, to use yaha import kar lein
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = get_sb()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def current_user():
    return str(st.session_state.get("username") or st.session_state.get("user") or "")


def s(v):
    """NaN / None ko '' me badlo."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def fetch_all(build):
    """Supabase ek baar me max 1000 rows deta hai, isliye pagination."""
    rows, start, step = [], 0, 1000
    while True:
        data = build().range(start, start + step - 1).execute().data or []
        rows.extend(data)
        if len(data) < step:
            return rows
        start += step


@st.cache_data(ttl=120, show_spinner=False)
def load_sites():
    return fetch_all(lambda: sb.table(SITE_TABLE).select("*")
                     .ilike(SD["project_name"], PROJECT_NAME_VALUE)
                     .order(SD["site_id"]))


@st.cache_data(ttl=120, show_spinner=False)
def load_tracker():
    return fetch_all(lambda: sb.table(TRACKER_TABLE).select("*").order("id"))


@st.cache_data(ttl=120, show_spinner=False)
def load_docs():
    return fetch_all(lambda: sb.table(DOCS_TABLE).select("*").order("id"))


@st.cache_data(ttl=3000, show_spinner=False)
def signed_url(path):
    try:
        res = sb.storage.from_(BUCKET).create_signed_url(path, 3600)
        return res.get("signedURL") or res.get("signedUrl")
    except Exception:
        return None


def refresh():
    load_sites.clear()
    load_tracker.clear()
    load_docs.clear()


def flash(kind, msg):
    st.session_state["dg_flash"] = (kind, msg)


def check_setup():
    if st.session_state.get("dg_setup_ok"):
        return {}
    problems = {}
    for t in (TRACKER_TABLE, DOCS_TABLE):
        try:
            sb.table(t).select("id").limit(1).execute()
        except Exception as e:
            problems[t] = str(e)
    if not problems:
        st.session_state["dg_setup_ok"] = True
    return problems


# ============================== WRITE HELPERS ==============================
def update_site_data(site_id, payload):
    if not payload:
        return
    (sb.table(SITE_TABLE).update(payload)
       .eq(SD["site_id"], site_id)
       .ilike(SD["project_name"], PROJECT_NAME_VALUE)
       .execute())


def save_tracker(row, changes):
    """Poori tracker row upsert karo (taaki baaki values default 'Pending' se overwrite na hon)."""
    payload = {f: s(row[f]) for f in TRACK_FIELDS}
    payload.update(changes)
    payload.update({"site_id": row["site_id"], "updated_by": current_user(), "updated_at": now_iso()})
    sb.table(TRACKER_TABLE).upsert(payload, on_conflict="site_id").execute()
    # jo tracker field site_data me bhi hai, usme bhi likho
    update_site_data(row["site_id"], {f: v for f, v in changes.items() if f in SITE_COLS})


def upload_doc(site_id, doc_type, f):
    data = f.getvalue()
    mime = f.type or mimetypes.guess_type(f.name)[0] or "application/octet-stream"
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", f.name)
    safe_site = re.sub(r"[^A-Za-z0-9._-]", "_", site_id)
    path = f"{safe_site}/{doc_type}/{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}_{safe_name}"
    sb.storage.from_(BUCKET).upload(path, data, {"content-type": mime})
    try:
        sb.table(DOCS_TABLE).insert({
            "site_id": site_id, "doc_type": doc_type, "file_name": f.name,
            "file_path": path, "mime_type": mime, "file_size": len(data),
            "uploaded_by": current_user(),
        }).execute()
    except Exception:
        sb.storage.from_(BUCKET).remove([path])
        raise


def delete_doc(doc):
    sb.storage.from_(BUCKET).remove([doc["file_path"]])
    sb.table(DOCS_TABLE).delete().eq("id", int(doc["id"])).execute()


# ============================== PAGE ==============================
st.title("⚡ DG Project")
st.caption(f"Site data me Project Name = “{PROJECT_NAME_VALUE}” wali sabhi sites")

if "dg_flash" in st.session_state:
    kind, msg = st.session_state.pop("dg_flash")
    getattr(st, kind)(msg)

problems = check_setup()
if problems:
    st.error("Supabase me DG Project ki tables nahi mili. `dg_project_setup.sql` SQL Editor me run karein, "
             "phir page refresh karein.")
    for t, e in problems.items():
        st.code(f"{t}: {e}")
    st.stop()

with st.spinner("Data load ho raha hai..."):
    sites = load_sites()

if not sites:
    st.info(f"site_data me “{PROJECT_NAME_VALUE}” project ki koi site nahi mili. "
            f"Column `{SD['project_name']}` aur value check karein.")
    st.stop()

SITE_COLS = set().union(*(r.keys() for r in sites))
missing_cols = [v for v in SD.values() if v not in SITE_COLS]
if missing_cols:
    st.warning(f"site_data me ye columns nahi mile: {', '.join(missing_cols)}. Upar `SD` mapping check karein.")

# ---------- site_data + tracker merge ----------
sdf = pd.DataFrame(sites)
sdf = sdf.rename(columns={f: f"sd_{f}" for f in TRACK_FIELDS if f in sdf.columns})
sdf = sdf.rename(columns={v: k for k, v in SD.items() if v in sdf.columns})
for k in SD:
    if k not in sdf.columns:
        sdf[k] = None
sdf["site_id"] = sdf["site_id"].map(s)
if sdf["site_id"].duplicated().any():
    st.warning("Kuch Site ID site_data me ek se zyada baar hain; yaha pehli row dikhayi ja rahi hai.")
    sdf = sdf.drop_duplicates("site_id")

tdf = pd.DataFrame(load_tracker())
if tdf.empty:
    tdf = pd.DataFrame(columns=["site_id"] + TRACK_FIELDS)
tdf["site_id"] = tdf["site_id"].map(s)
df = sdf.merge(tdf[["site_id"] + TRACK_FIELDS], on="site_id", how="left")

for f in TRACK_FIELDS:
    df[f] = df[f].astype(object)
    if f"sd_{f}" in df.columns:  # tracker khali ho to site_data wali value use karo
        blank = df[f].map(s) == ""
        df.loc[blank, f] = df.loc[blank, f"sd_{f}"]
    df[f] = df[f].map(s)
    if f in STATUS_FIELDS:
        df.loc[df[f] == "", f] = "Pending"
df["site_status_clean"] = df["site_status"].map(s).replace("", "(Blank)")

ddf = pd.DataFrame(load_docs())
if ddf.empty:
    ddf = pd.DataFrame(columns=["id", "site_id", "doc_type", "file_name", "file_path",
                                "mime_type", "uploaded_by", "uploaded_at"])
ddf["site_id"] = ddf["site_id"].map(s)

# ---------- Summary ----------
with st.container(border=True):
    cols = st.columns(6)
    cols[0].metric("Total Sites", len(df))
    for c, f in zip(cols[1:], STATUS_FIELDS):
        c.metric(f"{STATUS_LABELS[f]} Pending", int((df[f] == "Pending").sum()))

    st.markdown("**Site status wise**")
    status_counts = df["site_status_clean"].value_counts()
    items = list(status_counts.items())
    for i in range(0, len(items), 6):
        row_cols = st.columns(6)
        for c, (name, cnt) in zip(row_cols, items[i:i + 6]):
            c.metric(name, int(cnt))

# ---------- Filters ----------
f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 1.5])
q = f1.text_input("Search", placeholder="Site ID, Site Name ya Project ID")
cl = f2.multiselect("Cluster", sorted(x for x in df["cluster"].map(s).unique() if x))
ss = f3.multiselect("Site Status", list(status_counts.index))
pend_opts = {"All": None, **{f"{STATUS_LABELS[f]} Pending": f for f in STATUS_FIELDS}}
pf = f4.selectbox("Pending filter", list(pend_opts))

view = df.copy()
if q:
    m = view[["site_id", "site_name", "project_id"]].astype(str).apply(
        lambda col: col.str.contains(q, case=False, regex=False)).any(axis=1)
    view = view[m]
if cl:
    view = view[view["cluster"].map(s).isin(cl)]
if ss:
    view = view[view["site_status_clean"].isin(ss)]
if pend_opts[pf]:
    view = view[view[pend_opts[pf]] == "Pending"]


def color_status(v):
    return {
        "Pending": "background-color:#fde8e8;color:#9b1c1c",
        "Done": "background-color:#def7ec;color:#03543f",
        "Not Required": "color:#6b7280",
    }.get(v, "")


table = view[list(DISPLAY)].rename(columns=DISPLAY)
styler = table.style
styler = (getattr(styler, "map", None) or styler.applymap)(
    color_status, subset=[DISPLAY[f] for f in STATUS_FIELDS])

st.caption(f"{len(view)} of {len(df)} sites")
st.dataframe(styler, hide_index=True, use_container_width=True, height=420)
st.download_button("Download CSV", table.to_csv(index=False).encode("utf-8"),
                   file_name=f"dg_project_{datetime.now():%Y%m%d}.csv", mime="text/csv")

# ============================== SITE DETAIL ==============================
st.divider()
st.subheader("Site open karein")

labels = dict(zip(df["site_id"], df["site_id"] + "  |  " + df["site_name"].map(s)))
sel = st.selectbox("Site select karein", [None] + df["site_id"].tolist(), key="dg_sel_site",
                   format_func=lambda x: "Site ID ya naam type karein..." if x is None else labels.get(x, x))
if sel is None:
    st.stop()

row = df[df["site_id"] == sel].iloc[0]

# ---------- Edit form ----------
with st.form(f"edit_{sel}"):
    st.markdown(f"#### {sel}  |  {s(row['site_name'])}")
    c1, c2, c3 = st.columns(3)
    c1.text_input("Project Name", s(row["project_name"]), disabled=True)
    c2.text_input("Site ID", sel, disabled=True)
    c3.text_input("Project ID", s(row["project_id"]), disabled=True)

    c1, c2, c3 = st.columns(3)
    site_name = c1.text_input("Site Name", s(row["site_name"]))
    cluster = c2.text_input("Cluster", s(row["cluster"]))
    status_list = sorted(x for x in df["site_status"].map(s).unique() if x)
    cur_status = s(row["site_status"])
    if cur_status not in status_list:
        status_list = [cur_status] + status_list
    site_status = c3.selectbox("Site Status", status_list, index=status_list.index(cur_status))

    new_track = {}
    for c, f in zip(st.columns(5), STATUS_FIELDS):
        opts = STATUS_OPTIONS if row[f] in STATUS_OPTIONS else [row[f]] + STATUS_OPTIONS
        new_track[f] = c.selectbox(f"{STATUS_LABELS[f]} Status", opts, index=opts.index(row[f]))
    new_track["remark"] = st.text_area("Remark", row["remark"], height=80)

    if st.form_submit_button("Save changes", type="primary"):
        try:
            # 1) Common fields -> site_data
            sd_payload = {}
            for k, v in {"site_name": site_name, "cluster": cluster, "site_status": site_status}.items():
                if SD[k] in SITE_COLS and v.strip() != s(row[k]):
                    sd_payload[SD[k]] = v.strip()
            update_site_data(sel, sd_payload)
            # 2) Status + remark -> tracker (aur site_data me bhi agar column hai)
            save_tracker(row, {k: v.strip() for k, v in new_track.items()})
            synced = list(sd_payload) + [f for f in new_track if f in SITE_COLS]
            msg = f"{sel} save ho gaya."
            if synced:
                msg += f" site_data me bhi update hua: {', '.join(synced)}"
            flash("success", msg)
            refresh()
            st.rerun()
        except Exception as e:
            st.error(f"Save nahi hua: {e}")

# ---------- Documents ----------
st.markdown("#### Documents")
site_docs = ddf[ddf["site_id"] == sel]
tabs = st.tabs([f"{d} ({int((site_docs['doc_type'] == d).sum())})" for d in DOC_TYPES])

for tab, (doc_type, status_field) in zip(tabs, DOC_TYPES.items()):
    with tab:
        ver_key = f"upver_{sel}_{doc_type}"
        ver = st.session_state.get(ver_key, 0)
        files = st.file_uploader(f"{doc_type} files add karein (PDF, JPG, PNG; multiple allowed)",
                                 type=ALLOWED_TYPES, accept_multiple_files=True,
                                 key=f"up_{sel}_{doc_type}_{ver}")
        if files and st.button(f"Upload {len(files)} file(s)", key=f"btn_{sel}_{doc_type}_{ver}",
                               type="primary"):
            ok, failed = 0, []
            with st.spinner("Upload ho raha hai..."):
                for f in files:
                    try:
                        upload_doc(sel, doc_type, f)
                        ok += 1
                    except Exception as e:
                        failed.append(f"{f.name}: {e}")
                if ok and row[status_field] == "Pending":
                    try:
                        save_tracker(row, {status_field: "Done"})
                    except Exception as e:
                        failed.append(f"Status update: {e}")
            st.session_state[ver_key] = ver + 1
            if failed:
                flash("warning", f"{ok} file upload hui. Fail: " + " | ".join(failed))
            else:
                flash("success", f"{ok} {doc_type} file(s) upload ho gayi, {doc_type} status Done.")
            refresh()
            st.rerun()

        docs = site_docs[site_docs["doc_type"] == doc_type]
        if docs.empty:
            st.caption(f"Abhi koi {doc_type} file nahi hai.")
            continue

        preview = st.toggle("Image preview", key=f"prev_{sel}_{doc_type}")
        for _, d in docs.iterrows():
            is_img = str(d["file_name"]).lower().endswith(IMAGE_EXT)
            c1, c2, c3, c4 = st.columns([5, 3, 1, 1])
            c1.write(("🖼️ " if is_img else "📄 ") + str(d["file_name"]))
            try:
                ts = pd.to_datetime(d["uploaded_at"], utc=True).tz_convert("Asia/Kolkata")
                c2.caption(f"{ts:%d %b %Y, %I:%M %p}  {s(d.get('uploaded_by'))}")
            except Exception:
                c2.caption(s(d.get("uploaded_by")))
            url = signed_url(d["file_path"])
            if url:
                c3.link_button("Open", url)
            with c4.popover("🗑️"):
                st.write(f"{d['file_name']} delete karein?")
                if st.button("Delete", key=f"del_{d['id']}", type="primary"):
                    try:
                        delete_doc(d)
                        remaining = int((docs["id"] != d["id"]).sum())
                        if remaining == 0 and row[status_field] == "Done":
                            save_tracker(row, {status_field: "Pending"})
                        flash("success", f"{d['file_name']} delete ho gayi.")
                        refresh()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete nahi hua: {e}")
            if preview and is_img and url:
                st.image(url, width=260)
