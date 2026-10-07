import streamlit as st
import pandas as pd
import io
import re
import math
from html import escape
from datetime import date, datetime
from supabase import create_client, Client

# ============================================================
# 1. PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SRN Pending",
    page_icon="📦",
    layout="wide"
)

# ============================================================
# 2. SUPABASE CONNECTION
# ============================================================
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

# ============================================================
# 3. CONSTANTS
# ============================================================
SRN_TABLE = "srn_pending"
ESCALATION_TABLE = "Excalation Matrix"

REQUIRED_UPLOAD_COLUMNS = [
    "Site ID",
    "Project Number",
    "Item Description",
    "BOQ Quantity",
    "Dispatch Date",
    "Item Cat 2",
    "Ageing Date",
    "Ageing Slab",
]

SCREEN_COLUMNS = [
    "Site ID",
    "Site Name",
    "Cluster",
    "Technician Detail",
    "Item Cat 2",
    "Ageing Slab",
    "Project Number",
    "Item Description",
    "BOQ Quantity",
    "Team Name",
    "SRN Status",
    "SRN Date",
    "SRN From",
    "POD Status",
    "Remark",
]

SRN_STATUS_OPTIONS = ["Done", "Pending", "Issue"]
POD_STATUS_OPTIONS = ["Received", "Pending"]
SRN_FROM_OPTIONS = []

# ============================================================
# 4. ACCESS GATE - SAME WORKSPACE RULE AS OLD PAGE
# ============================================================
if st.session_state.get("active_workspace", "VISPL") == "RAJKUMAR KALYA":
    st.error("🚫 Access Restricted!")
    st.warning("Ye module exclusively VISPL / BHAGYASHREE workspaces ke liye available hai.")
    st.stop()

active_ws = st.session_state.get("active_workspace", "VISPL")

# ============================================================
# 5. STYLING
# ============================================================
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important;
        margin: 0.5rem 1rem !important;
        border-radius: 12px !important;
        background: rgba(255,255,255,0.03) !important;
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.02rem !important;
        transition: all 0.25s ease !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,0.10) !important;
        transform: translateX(4px);
        color: #ffffff !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(59,130,246,0.35);
    }

    .srn-banner {
        background: linear-gradient(90deg, #0f172a 0%, #1d4ed8 48%, #7c3aed 100%);
        padding: 16px 22px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(15,23,42,0.20);
    }

    .srn-banner h1 {
        color: white !important;
        margin: 0;
        font-size: 2.05rem;
        font-weight: 900;
        letter-spacing: 1.5px;
    }

    .srn-banner p {
        color: #dbeafe !important;
        margin: 5px 0 0 0;
        font-weight: 600;
    }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 13px;
        padding: 14px 16px;
        box-shadow: 0 4px 12px rgba(15,23,42,0.06);
        min-height: 92px;
    }

    .metric-card.card-blue { background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-color:#93c5fd; }
    .metric-card.card-purple { background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%); border-color:#c4b5fd; }
    .metric-card.card-yellow { background: linear-gradient(135deg, #fef9c3 0%, #fde68a 100%); border-color:#fcd34d; }
    .metric-card.card-green { background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-color:#86efac; }
    .metric-card { transition: transform .18s ease, box-shadow .18s ease; }
    .metric-card:hover { transform: translateY(-2px); box-shadow:0 10px 22px rgba(15,23,42,.12); }

    .metric-title {
        color: #64748b;
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .7px;
    }

    .metric-value {
        color: #0f172a;
        font-size: 1.7rem;
        font-weight: 900;
        margin-top: 5px;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        overflow: hidden;
        background: #ffffff;
        box-shadow: 0 3px 10px rgba(15,23,42,0.05);
        margin-bottom: 10px;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 800 !important;
        color: #0f172a !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
    }

    .small-note {
        color: #64748b;
        font-size: .84rem;
        font-weight: 600;
    }

    .site-meta {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 10px;
        color: #334155;
        font-size: .88rem;
        font-weight: 650;
    }

    .stButton > button {
        font-weight: 800 !important;
        border-radius: 9px !important;
    }

    div[data-testid="stDownloadButton"] button {
        font-weight: 800 !important;
        border-radius: 9px !important;
    }

    .stApp { background: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%); color:#0f172a; font-family:'Inter',sans-serif; }
    div.stButton > button { background:linear-gradient(90deg,#f59e0b 0%,#ec4899 100%) !important; color:#fff !important; border:none !important; border-radius:8px !important; font-weight:800 !important; box-shadow:0 4px 8px rgba(0,0,0,.14); }
    div.stButton > button:hover { transform:translateY(-2px); box-shadow:0 9px 16px rgba(0,0,0,.20); }
    div[data-testid="stDialog"] > div { background:rgba(255,255,255,.99); border-radius:16px; box-shadow:0 25px 50px -12px rgba(0,0,0,.25); }
    .slux-head-bar { display:flex; justify-content:space-between; padding:16px 22px; border-radius:18px 18px 0 0; background:linear-gradient(100deg,#1e1b4b 0%,#312e81 45%,#5b21b6 100%); }
    .slux-title { color:#fff; font-weight:900; font-size:1.05rem; letter-spacing:1.3px; text-transform:uppercase; }
    .slux-title span { color:#c7d2fe; font-size:.8rem; margin-left:8px; text-transform:none; }
    .slux-badge { background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.25); color:#fde68a; padding:5px 12px; border-radius:999px; font-weight:800; }
    .st-key-srn_lux_table { background:#fff; overflow:auto !important; max-height:72vh !important; padding:0 !important; border:1px solid #e0e7ff; }
    .st-key-srn_lux_table [data-testid="stHorizontalBlock"] { min-width:2450px !important; flex-wrap:nowrap !important; gap:0 !important; align-items:center !important; }
    .st-key-srn_lux_table [data-testid="stColumn"] { padding:0 10px !important; min-width:0 !important; border-right:1px solid #f1f5f9; }
    div[class*="st-key-srnhead_"] { position:sticky !important; top:0 !important; z-index:20 !important; background:linear-gradient(90deg,#312e81,#4338ca,#6d28d9) !important; border-bottom:3px solid #f59e0b; padding:13px 0 !important; }
    .slux-th { color:#fff; font-size:.69rem; font-weight:900; letter-spacing:.9px; text-transform:uppercase; white-space:nowrap; }
    div[class*="st-key-srnrow_"] { padding:8px 0 !important; background:#fff; border-bottom:1px solid #f1f5f9; }
    div[class*="st-key-srnrow_odd"] { background:#fafaff; }
    div[class*="st-key-srnrow_"]:hover { background:#eef2ff; box-shadow:inset 4px 0 0 #6366f1; }
    .slux-cell { font-size:.84rem; color:#1e293b; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%; }
    .slux-strong { font-weight:800; color:#0f172a; }
    .slux-muted { color:#cbd5e1; }
    .slux-chip { font-family:ui-monospace,Consolas,monospace; background:#f8fafc; border:1px solid #e2e8f0; color:#334155; padding:3px 7px; border-radius:6px; font-size:.76rem; font-weight:700; }
    .slux-chip.proj { background:#eef2ff; border-color:#c7d2fe; color:#4338ca; }
    .slux-pill { display:inline-block; padding:4px 10px; border-radius:999px; background:linear-gradient(90deg,#e0f2fe,#ede9fe); color:#4338ca; border:1px solid #ddd6fe; font-weight:800; font-size:.68rem; }
    .status-badge { display:inline-flex; padding:4px 10px; border-radius:999px; font-size:.69rem; font-weight:900; border:1px solid transparent; }
    .status-green{background:#dcfce7;color:#15803d;border-color:#bbf7d0}.status-yellow{background:#fef9c3;color:#a16207;border-color:#fde68a}.status-red{background:#fee2e2;color:#b91c1c;border-color:#fecaca}.status-blue{background:#dbeafe;color:#1d4ed8;border-color:#bfdbfe}
    div[class*="st-key-srnedit_"] button { width:38px !important; height:34px !important; padding:0 !important; background:rgba(59,130,246,.15) !important; border:1px solid rgba(59,130,246,.3) !important; color:#1d4ed8 !important; box-shadow:none !important; }
    div[class*="st-key-srnedit_"] button:hover { background:#3b82f6 !important; color:#fff !important; }
    .slux-foot { padding:14px 22px; background:linear-gradient(90deg,#f5f3ff,#eef2ff); border:1px solid #e0e7ff; border-top:2px solid #c7d2fe; border-radius:0 0 18px 18px; font-weight:900; color:#312e81; }

    /* ================= SRN EDIT POPUP — HIGH CONTRAST ================= */
    div[data-testid="stDialog"] > div {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #c7d2fe !important;
    }
    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3 {
        color: #111827 !important;
        font-weight: 900 !important;
    }
    div[data-testid="stDialog"] p,
    div[data-testid="stDialog"] span,
    div[data-testid="stDialog"] label,
    div[data-testid="stDialog"] label p,
    div[data-testid="stDialog"] [data-testid="stWidgetLabel"] p {
        color: #111827 !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p {
        color: #475569 !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] textarea {
        color: #0f172a !important;
        font-weight: 800 !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }
    div[data-testid="stDialog"] input::placeholder,
    div[data-testid="stDialog"] textarea::placeholder {
        color: #64748b !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #64748b !important;
    }
    div[data-testid="stDialog"] input:disabled {
        background: #e2e8f0 !important;
        color: #1e293b !important;
        font-weight: 900 !important;
        -webkit-text-fill-color: #1e293b !important;
        opacity: 1 !important;
    }
    div[data-testid="stDialog"] [data-baseweb="select"] > div,
    div[data-testid="stDialog"] [data-baseweb="input"] > div,
    div[data-testid="stDialog"] [data-baseweb="textarea"] > div {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
    }
    div[data-testid="stDialog"] [data-baseweb="select"] * {
        color: #0f172a !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }
    div[data-testid="stDialog"] svg {
        fill: #0f172a !important;
        color: #0f172a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 6. HELPERS
# ============================================================
def clean_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def normalize_col_name(name):
    return re.sub(r"[^a-z0-9]+", " ", str(name).strip().lower()).strip()


def find_column(columns, candidates):
    normalized = {normalize_col_name(c): c for c in columns}

    # Exact normalized match first
    for candidate in candidates:
        key = normalize_col_name(candidate)
        if key in normalized:
            return normalized[key]

    # Then contains match
    for candidate in candidates:
        key = normalize_col_name(candidate)
        for norm_col, original in normalized.items():
            if key and (key in norm_col or norm_col in key):
                return original

    return None


def safe_date_string(value):
    if value is None or clean_text(value) == "":
        return None

    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def display_date(value):
    if value is None or clean_text(value) == "":
        return ""
    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return clean_text(value)
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return clean_text(value)


def safe_float(value):
    try:
        if value is None or clean_text(value) == "":
            return None
        return float(value)
    except Exception:
        return None


def make_line_key(site_id, project_number, item_description, item_cat_2):
    """
    Upload sheet me line number nahi hai.
    Isliye same pending line ko next upload me identify karne ke liye
    Site ID + Project Number + Item Description + Item Cat 2 use ho raha hai.
    """
    parts = [
        clean_text(site_id).upper(),
        clean_text(project_number).upper(),
        clean_text(item_description).upper(),
        clean_text(item_cat_2).upper(),
    ]
    return "||".join(parts)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_srn_data(workspace):
    try:
        response = (
            supabase.table(SRN_TABLE)
            .select("*")
            .eq("workspace", workspace)
            .order("site_id")
            .execute()
        )
        return response.data or []
    except Exception as e:
        st.error(f"❌ SRN data load error: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_escalation_matrix():
    try:
        response = supabase.table(ESCALATION_TABLE).select("*").execute()
        return response.data or []
    except Exception as e:
        st.error(f"❌ '{ESCALATION_TABLE}' load error: {e}")
        return []


def clear_srn_cache():
    fetch_srn_data.clear()


def prepare_escalation_lookup(records):
    """
    Excalation Matrix ke exact column names alag hone par bhi common
    naming variants se Site ID / Site Name / Cluster / Technician Detail
    identify karne ki koshish karega.
    """
    if not records:
        return {}

    edf = pd.DataFrame(records)
    if edf.empty:
        return {}

    site_col = find_column(
        edf.columns,
        [
            "Site ID",
            "Indus ID",
            "Indus Site ID",
            "Site Id",
            "SiteID",
        ],
    )

    site_name_col = find_column(
        edf.columns,
        [
            "Site Name",
            "SiteName",
            "Indus Site Name",
        ],
    )

    cluster_col = find_column(
        edf.columns,
        [
            "Cluster",
            "Cluster Name",
        ],
    )

    tech_col = find_column(
        edf.columns,
        [
            "Technician Detail",
            "Technician Details",
            "Technician",
            "Technician Name",
            "Technician Name & Number",
            "Technician Name and Number",
            "Technician Contact",
            "Technician Mobile",
            "Technician Number",
        ],
    )

    if not site_col:
        st.warning(
            f"⚠️ '{ESCALATION_TABLE}' me Site ID/Indus ID column auto-detect nahi hua. "
            f"Available columns: {', '.join(map(str, edf.columns))}"
        )
        return {}

    lookup = {}

    for _, row in edf.iterrows():
        sid = clean_text(row.get(site_col)).upper()
        if not sid:
            continue

        # First useful row wins, but blank values can be filled by later duplicate rows.
        if sid not in lookup:
            lookup[sid] = {
                "Site Name": "",
                "Cluster": "",
                "Technician Detail": "",
            }

        if site_name_col and not lookup[sid]["Site Name"]:
            lookup[sid]["Site Name"] = clean_text(row.get(site_name_col))

        if cluster_col and not lookup[sid]["Cluster"]:
            lookup[sid]["Cluster"] = clean_text(row.get(cluster_col))

        if tech_col and not lookup[sid]["Technician Detail"]:
            lookup[sid]["Technician Detail"] = clean_text(row.get(tech_col))

    return lookup


def excel_bytes(df, sheet_name="SRN Pending"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        ws = writer.book[sheet_name[:31]]

        # Useful widths
        widths = {
            "A": 16, "B": 30, "C": 20, "D": 34, "E": 18,
            "F": 16, "G": 24, "H": 55, "I": 14, "J": 24,
            "K": 16, "L": 14, "M": 20, "N": 16, "O": 35,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    return output.getvalue()


def build_display_df(raw_records, escalation_lookup):
    if not raw_records:
        return pd.DataFrame(columns=SCREEN_COLUMNS + ["id", "line_key"])

    rdf = pd.DataFrame(raw_records)

    rename_map = {
        "site_id": "Site ID",
        "item_cat_2": "Item Cat 2",
        "ageing_slab": "Ageing Slab",
        "project_number": "Project Number",
        "item_description": "Item Description",
        "boq_quantity": "BOQ Quantity",
        "dispatch_date": "Dispatch Date",
        "ageing_date": "Ageing Date",
        "team_name": "Team Name",
        "srn_status": "SRN Status",
        "srn_date": "SRN Date",
        "srn_from": "SRN From",
        "pod_status": "POD Status",
        "remark": "Remark",
    }
    rdf = rdf.rename(columns=rename_map)

    for col in [
        "Site ID", "Item Cat 2", "Ageing Slab", "Project Number",
        "Item Description", "BOQ Quantity", "Dispatch Date", "Ageing Date",
        "Team Name", "SRN Status", "SRN Date", "SRN From",
        "POD Status", "Remark", "id", "line_key"
    ]:
        if col not in rdf.columns:
            rdf[col] = ""

    # Enrich from Excalation Matrix
    rdf["Site Name"] = rdf["Site ID"].apply(
        lambda x: escalation_lookup.get(clean_text(x).upper(), {}).get("Site Name", "")
    )
    rdf["Cluster"] = rdf["Site ID"].apply(
        lambda x: escalation_lookup.get(clean_text(x).upper(), {}).get("Cluster", "")
    )
    rdf["Technician Detail"] = rdf["Site ID"].apply(
        lambda x: escalation_lookup.get(clean_text(x).upper(), {}).get("Technician Detail", "")
    )

    # Defaults for operational columns
    rdf["SRN Status"] = rdf["SRN Status"].apply(lambda x: clean_text(x) or "Pending")
    rdf["POD Status"] = rdf["POD Status"].apply(lambda x: clean_text(x) or "Pending")

    # Date display
    rdf["SRN Date"] = rdf["SRN Date"].apply(display_date)

    # Keep internal columns at end
    ordered = SCREEN_COLUMNS + ["Dispatch Date", "Ageing Date", "id", "line_key"]
    return rdf[ordered].copy()


def validate_upload_df(upload_df):
    missing = [c for c in REQUIRED_UPLOAD_COLUMNS if c not in upload_df.columns]
    return missing


def upload_new_srn_data(upload_df, workspace):
    """
    Existing line ko line_key se update karta hai.
    New line insert hoti hai.
    Manual SRN Status / Date / From / POD / Remark / Team Name preserve rehte hain.
    """
    missing = validate_upload_df(upload_df)
    if missing:
        raise ValueError(
            "Excel me ye required columns missing hain: " + ", ".join(missing)
        )

    existing = fetch_srn_data(workspace)
    existing_by_key = {
        clean_text(r.get("line_key")): r
        for r in existing
        if clean_text(r.get("line_key"))
    }

    payload = []
    skipped_blank_site = 0
    line_key_occurrence_counter = {}

    for _, row in upload_df.iterrows():
        site_id = clean_text(row.get("Site ID"))
        if not site_id:
            skipped_blank_site += 1
            continue

        project_number = clean_text(row.get("Project Number"))
        item_description = clean_text(row.get("Item Description"))
        item_cat_2 = clean_text(row.get("Item Cat 2"))

        # Same Site/Project/Item genuine multiple times aa sakta hai.
        # Base key ke saath occurrence number add karte hain so every Excel line
        # is preserved, while re-uploading the same sheet updates the same rows.
        base_line_key = make_line_key(
            site_id,
            project_number,
            item_description,
            item_cat_2,
        )

        occurrence_no = line_key_occurrence_counter.get(base_line_key, 0) + 1
        line_key_occurrence_counter[base_line_key] = occurrence_no
        line_key = f"{base_line_key}||ROW{occurrence_no}"

        old = existing_by_key.get(line_key, {})

        record = {
            "workspace": workspace,
            "line_key": line_key,
            "site_id": site_id,
            "project_number": project_number,
            "item_description": item_description,
            "boq_quantity": safe_float(row.get("BOQ Quantity")),
            "dispatch_date": safe_date_string(row.get("Dispatch Date")),
            "item_cat_2": item_cat_2,
            "ageing_date": safe_date_string(row.get("Ageing Date")),
            "ageing_slab": clean_text(row.get("Ageing Slab")),

            # Preserve manually maintained values on repeat upload
            "team_name": clean_text(old.get("team_name")),
            "srn_status": clean_text(old.get("srn_status")) or "Pending",
            "srn_date": old.get("srn_date") or None,
            "srn_from": clean_text(old.get("srn_from")),
            "pod_status": clean_text(old.get("pod_status")) or "Pending",
            "remark": clean_text(old.get("remark")),
            "updated_at": datetime.now().isoformat(),
        }

        payload.append(record)

    if not payload:
        return 0, skipped_blank_site

    # Upsert in batches
    batch_size = 250
    for start in range(0, len(payload), batch_size):
        batch = payload[start:start + batch_size]
        (
            supabase.table(SRN_TABLE)
            .upsert(batch, on_conflict="workspace,line_key")
            .execute()
        )

    clear_srn_cache()
    return len(payload), skipped_blank_site



@st.cache_data(ttl=60, show_spinner=False)
def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data or []
    except Exception:
        return []

def dropdown_values(category, fallback=None):
    all_dd = get_all_dropdowns()
    vals = []
    for r in all_dd:
        if clean_text(r.get("category")).lower() == category.lower():
            v = clean_text(r.get("option_value"))
            if v and v not in vals:
                vals.append(v)
    if fallback:
        for v in fallback:
            if v not in vals:
                vals.append(v)
    return vals

def add_dropdown_value(category, value):
    value = clean_text(value)
    if not value:
        return False, "Blank value add nahi ho sakti."
    try:
        existing = supabase.table("dropdown_master").select("*").eq("category", category).eq("option_value", value).execute()
        if existing.data:
            return True, "Already available."
        supabase.table("dropdown_master").insert({
            "category": category,
            "option_value": value
        }).execute()
        get_all_dropdowns.clear()
        return True, f"{value} added."
    except Exception as e:
        return False, str(e)

def _muted():
    return "<div class='slux-cell'><span class='slux-muted'>—</span></div>"

def _txt(v, strong=False):
    x=clean_text(v)
    if not x: return _muted()
    cls=" slux-strong" if strong else ""
    return f"<div class='slux-cell{cls}' title='{escape(x)}'>{escape(x)}</div>"

def _chip(v, proj=False):
    x=clean_text(v)
    if not x: return _muted()
    cls=" proj" if proj else ""
    return f"<div class='slux-cell'><span class='slux-chip{cls}'>{escape(x)}</span></div>"

def _pill(v):
    x=clean_text(v)
    if not x: return _muted()
    return f"<div class='slux-cell'><span class='slux-pill'>{escape(x)}</span></div>"

def _status(v):
    x=clean_text(v)
    if not x: return _muted()
    xl=x.lower()
    if xl in ("done","received"): cls="status-green"
    elif xl=="issue": cls="status-red"
    elif xl=="pending": cls="status-yellow"
    else: cls="status-blue"
    return f"<div class='slux-cell'><span class='status-badge {cls}'>{escape(x)}</span></div>"

def _qty(v):
    try:
        n=float(v)
        out=f"{n:g}"
    except:
        out=clean_text(v) or "-"
    return f"<div class='slux-cell slux-strong'>{escape(out)}</div>"

def table_header_row(key, ratios, labels):
    with st.container(key=key):
        cols=st.columns(ratios, vertical_alignment="center")
        for c,label in zip(cols,labels):
            c.markdown(f"<div class='slux-th'>{label}</div>", unsafe_allow_html=True)

@st.dialog("➕ Add New Dropdown Option")
def add_option_dialog():
    category = st.selectbox("Add option in", ["SRN Status", "SRN From", "POD Status"])
    new_value = st.text_input("New Option", placeholder="Type new status / SRN From...")
    if st.button("➕ Add Option", type="primary", use_container_width=True):
        ok,msg=add_dropdown_value(category,new_value)
        if ok:
            st.success("✅ "+msg)
            st.rerun()
        else:
            st.error("❌ "+msg)

@st.dialog("✏️ Edit SRN Record", width="large")
def edit_srn_dialog(row_data):
    rid = row_data.get("id")
    st.caption("Team / SRN / POD details update karein")

    c1,c2,c3,c4=st.columns(4)
    c1.text_input("SITE ID", value=clean_text(row_data.get("Site ID")), disabled=True)
    c2.text_input("SITE NAME", value=clean_text(row_data.get("Site Name")), disabled=True)
    c3.text_input("CLUSTER", value=clean_text(row_data.get("Cluster")), disabled=True)
    c4.text_input("PROJECT NUMBER", value=clean_text(row_data.get("Project Number")), disabled=True)

    team_opts = dropdown_values("Team Name")
    current_team=clean_text(row_data.get("Team Name"))
    if current_team and current_team not in team_opts: team_opts.insert(0,current_team)
    team_opts=["Select"]+team_opts
    team_name=st.selectbox("TEAM NAME", team_opts, index=(team_opts.index(current_team) if current_team in team_opts else 0))

    srn_opts=dropdown_values("SRN Status", ["Done","Pending","Issue"])
    cur_srn=clean_text(row_data.get("SRN Status")) or "Pending"
    if cur_srn not in srn_opts: srn_opts.insert(0,cur_srn)

    from_opts=dropdown_values("SRN From")
    cur_from=clean_text(row_data.get("SRN From"))
    if cur_from and cur_from not in from_opts: from_opts.insert(0,cur_from)
    from_opts=["Manual"] + [x for x in from_opts if x!="Manual"]

    pod_opts=dropdown_values("POD Status", ["Received","Pending"])
    cur_pod=clean_text(row_data.get("POD Status")) or "Pending"
    if cur_pod not in pod_opts: pod_opts.insert(0,cur_pod)

    x1,x2,x3=st.columns(3)
    with x1:
        srn_status=st.selectbox("SRN STATUS", srn_opts, index=srn_opts.index(cur_srn))
    with x2:
        raw_date=pd.to_datetime(row_data.get("SRN Date"), errors="coerce", dayfirst=True)
        date_val=raw_date.date() if not pd.isna(raw_date) else None
        srn_date=st.date_input("SRN DATE", value=date_val, format="DD-MM-YYYY")
    with x3:
        pod_status=st.selectbox("POD STATUS", pod_opts, index=pod_opts.index(cur_pod))

    y1,y2=st.columns([1,2])
    with y1:
        srn_from_choice=st.selectbox("SRN FROM", from_opts, index=(from_opts.index(cur_from) if cur_from in from_opts else 0))
    with y2:
        if srn_from_choice=="Manual":
            srn_from=st.text_input("MANUAL SRN FROM", value=(cur_from if cur_from and cur_from!="Manual" else ""), placeholder="Type SRN From...")
        else:
            srn_from=srn_from_choice

    remark=st.text_area("REMARK", value=clean_text(row_data.get("Remark")), placeholder="Enter remark...", height=90)

    bc1,bc2=st.columns([1,3])
    with bc1:
        if st.button("➕ Add Dropdown Option", use_container_width=True):
            add_option_dialog()
    with bc2:
        if st.button("💾 Save Update", type="primary", use_container_width=True):
            try:
                payload={
                    "team_name": "" if team_name=="Select" else team_name,
                    "srn_status": srn_status,
                    "srn_date": srn_date.isoformat() if srn_date else None,
                    "srn_from": clean_text(srn_from),
                    "pod_status": pod_status,
                    "remark": clean_text(remark),
                    "updated_at": datetime.now().isoformat(),
                }
                supabase.table(SRN_TABLE).update(payload).eq("id",rid).execute()
                clear_srn_cache()
                st.success("✅ SRN record updated.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

# ============================================================
# 7. HEADER
# ============================================================
st.markdown(
    f"""
    <div class="srn-banner">
        <h1>📦 SRN Pending Dashboard</h1>
        <p>Active Workspace: {active_ws} • Excel Upload + Site-wise Group View</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 8. LOAD EXCALATION MATRIX + CURRENT SRN DATA
# ============================================================
escalation_records = fetch_escalation_matrix()
escalation_lookup = prepare_escalation_lookup(escalation_records)

raw_srn_records = fetch_srn_data(active_ws)
df = build_display_df(raw_srn_records, escalation_lookup)

# ============================================================
# 9. UPLOAD NEW DATA
# ============================================================
with st.expander("⬆️ Upload New SRN Pending Data", expanded=(len(df) == 0)):
    st.markdown(
        """
        <div class="small-note">
        Upload Excel file. Existing matching material lines update hongi aur
        manually maintained Team/SRN/POD/Remark details preserve rahengi.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose SRN Pending Excel",
        type=["xlsx", "xls"],
        key="srn_pending_upload",
    )

    if uploaded_file is not None:
        try:
            upload_preview = pd.read_excel(uploaded_file)

            st.write(
                f"**Rows:** {len(upload_preview):,} | "
                f"**Columns:** {len(upload_preview.columns)}"
            )

            missing_cols = validate_upload_df(upload_preview)

            if missing_cols:
                st.error(
                    "❌ Excel format mismatch. Missing columns: "
                    + ", ".join(missing_cols)
                )
            else:
                st.dataframe(
                    upload_preview.head(20),
                    use_container_width=True,
                    hide_index=True,
                )

                if st.button(
                    "🚀 Upload / Update Data",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("SRN pending data upload ho raha hai..."):
                        processed, skipped = upload_new_srn_data(
                            upload_preview,
                            active_ws,
                        )

                    st.success(
                        f"✅ {processed:,} line(s) uploaded/updated successfully."
                    )
                    if skipped:
                        st.warning(
                            f"⚠️ {skipped} row(s) blank Site ID ke karan skip hui."
                        )
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Excel read/upload error: {e}")

# Refresh after possible upload state
raw_srn_records = fetch_srn_data(active_ws)
df = build_display_df(raw_srn_records, escalation_lookup)

# ============================================================
# 10. KPI CARDS
# ============================================================
total_lines = len(df)
total_sites = df["Site ID"].replace("", pd.NA).dropna().nunique() if not df.empty else 0
pending_sites = (
    df.loc[df["SRN Status"].astype(str).str.lower() == "pending", "Site ID"].nunique()
    if not df.empty else 0
)
submitted_sites = (
    df.loc[df["SRN Status"].astype(str).str.lower() == "submitted", "Site ID"].nunique()
    if not df.empty else 0
)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f'<div class="metric-card card-blue"><div class="metric-title">Total Sites</div>'
        f'<div class="metric-value">{total_sites:,}</div></div>',
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f'<div class="metric-card card-purple"><div class="metric-title">Total Material Lines</div>'
        f'<div class="metric-value">{total_lines:,}</div></div>',
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f'<div class="metric-card card-yellow"><div class="metric-title">Pending Sites</div>'
        f'<div class="metric-value">{pending_sites:,}</div></div>',
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f'<div class="metric-card card-green"><div class="metric-title">Submitted Sites</div>'
        f'<div class="metric-value">{submitted_sites:,}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# 11. SEARCH + FILTERS + DOWNLOAD
# ============================================================
if df.empty:
    st.info("ℹ️ Abhi SRN Pending data nahi hai. Upar se Excel upload karein.")
    st.stop()

cluster_options = sorted(
    [x for x in df["Cluster"].dropna().astype(str).unique().tolist() if clean_text(x)]
)
team_options = sorted(
    [x for x in df["Team Name"].dropna().astype(str).unique().tolist() if clean_text(x)]
)

f1, f2, f3, f4 = st.columns([3.2, 1.7, 1.7, 1.6])

with f1:
    search_text = st.text_input(
        "Search",
        placeholder="🔍 Search Site ID, Site Name, Project Number, Item, Technician...",
        key="srn_live_search",
        label_visibility="collapsed",
    )

with f2:
    cluster_filter = st.selectbox(
        "Cluster",
        ["All Cluster"] + cluster_options,
        label_visibility="collapsed",
    )

with f3:
    team_filter = st.selectbox(
        "Team",
        ["All Team"] + team_options,
        label_visibility="collapsed",
    )

filtered_df = df.copy()

if search_text:
    search_cols = [
        "Site ID",
        "Site Name",
        "Cluster",
        "Technician Detail",
        "Item Cat 2",
        "Ageing Slab",
        "Project Number",
        "Item Description",
        "Team Name",
        "SRN Status",
        "SRN From",
        "POD Status",
        "Remark",
    ]
    mask = filtered_df[search_cols].astype(str).apply(
        lambda col: col.str.contains(
            search_text,
            case=False,
            na=False,
            regex=False,
        )
    ).any(axis=1)
    filtered_df = filtered_df[mask]

if cluster_filter != "All Cluster":
    filtered_df = filtered_df[
        filtered_df["Cluster"].astype(str) == cluster_filter
    ]

if team_filter != "All Team":
    filtered_df = filtered_df[
        filtered_df["Team Name"].astype(str) == team_filter
    ]

export_df = filtered_df[SCREEN_COLUMNS].copy()

with f4:
    st.download_button(
        "📥 Download Excel",
        data=excel_bytes(export_df),
        file_name=f"SRN_Pending_{active_ws}_{date.today().isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

filtered_sites = (
    filtered_df["Site ID"].replace("", pd.NA).dropna().nunique()
    if not filtered_df.empty else 0
)

st.caption(
    f"Showing **{filtered_sites:,} Site ID group(s)** / "
    f"**{len(filtered_df):,} material line(s)**"
)

# ============================================================
# 12. LAVISH PROPER TABLE VIEW
# ============================================================
if not filtered_df.empty:
    # Team-wise A-Z sequence; blank Team Name always last.
    filtered_df = filtered_df.copy()
    filtered_df["_team_blank"] = filtered_df["Team Name"].fillna("").astype(str).str.strip().eq("")
    filtered_df["_team_sort"] = filtered_df["Team Name"].fillna("").astype(str).str.strip().str.lower()
    filtered_df["_site_sort"] = filtered_df["Site ID"].fillna("").astype(str).str.strip().str.lower()
    filtered_df["_project_sort"] = filtered_df["Project Number"].fillna("").astype(str).str.strip().str.lower()
    filtered_df = (
        filtered_df.sort_values(
            by=["_team_blank", "_team_sort", "_site_sort", "_project_sort"],
            ascending=[True, True, True, True],
            kind="stable"
        )
        .drop(columns=["_team_blank", "_team_sort", "_site_sort", "_project_sort"])
        .reset_index(drop=True)
    )

if filtered_df.empty:
    st.warning("⚠️ Search/filter ke hisab se koi record nahi mila.")
    st.stop()

# Top Add Option button
ta,tb=st.columns([6,1.4])
with ta:
    st.markdown("<h4 style='margin:0;color:#0f172a;'>📋 SRN Pending Register</h4>", unsafe_allow_html=True)
with tb:
    if st.button("➕ Add Status / From", use_container_width=True):
        add_option_dialog()

rows_per_page=50
total_rows=len(filtered_df)
total_pages=max(1, math.ceil(total_rows/rows_per_page))
if "srn_lux_page" not in st.session_state: st.session_state.srn_lux_page=1
st.session_state.srn_lux_page=min(max(1,st.session_state.srn_lux_page),total_pages)
start_idx=(st.session_state.srn_lux_page-1)*rows_per_page
end_idx=start_idx+rows_per_page
df_page=filtered_df.iloc[start_idx:end_idx].copy()

st.markdown(
    '<div class="slux-head-bar">'
    '<div class="slux-title">📦 SRN Pending Details<span>scroll right for complete details →</span></div>'
    f'<div class="slux-badge">{total_rows:,} Lines</div></div>',
    unsafe_allow_html=True
)

R=[0.45,0.48,1.15,1.45,1.0,1.25,1.0,1.35,2.1,0.8,1.0,1.6,1.0,1.15,1.0,1.6,1.7]
L=["✏️","SR. NO.","SITE ID","SITE NAME","CLUSTER","TEAM NAME","ITEM CAT 2",
   "PROJECT NUMBER","ITEM DESCRIPTION","BOQ QUANTITY","AGEING SLAB","TECHNICIAN DETAIL",
   "SRN STATUS","SRN DATE","SRN FROM","POD STATUS","REMARK"]

with st.container(key="srn_lux_table"):
    table_header_row("srnhead_main",R,L)
    for pos,(_,row) in enumerate(df_page.iterrows()):
        d=row.to_dict()
        serial=start_idx+pos+1
        rid=d.get("id")
        key=rid if clean_text(rid) else f"r{serial}"
        parity="odd" if serial%2 else "even"
        with st.container(key=f"srnrow_{parity}_{key}"):
            c=st.columns(R,vertical_alignment="center")
            with c[0]:
                if st.button("✏️",key=f"srnedit_{key}",help="Edit SRN details"):
                    edit_srn_dialog(d)
            c[1].markdown(f"<div class='slux-cell slux-strong'>{serial}</div>",unsafe_allow_html=True)
            c[2].markdown(_chip(d.get("Site ID")),unsafe_allow_html=True)
            c[3].markdown(_txt(d.get("Site Name"),True),unsafe_allow_html=True)
            c[4].markdown(_pill(d.get("Cluster")),unsafe_allow_html=True)
            c[5].markdown(_txt(d.get("Team Name"),True),unsafe_allow_html=True)
            c[6].markdown(_pill(d.get("Item Cat 2")),unsafe_allow_html=True)
            c[7].markdown(_chip(d.get("Project Number"),True),unsafe_allow_html=True)
            c[8].markdown(_txt(d.get("Item Description")),unsafe_allow_html=True)
            c[9].markdown(_qty(d.get("BOQ Quantity")),unsafe_allow_html=True)
            c[10].markdown(_status(d.get("Ageing Slab")),unsafe_allow_html=True)
            c[11].markdown(_txt(d.get("Technician Detail")),unsafe_allow_html=True)
            c[12].markdown(_status(d.get("SRN Status")),unsafe_allow_html=True)
            c[13].markdown(_txt(d.get("SRN Date")),unsafe_allow_html=True)
            c[14].markdown(_txt(d.get("SRN From")),unsafe_allow_html=True)
            c[15].markdown(_status(d.get("POD Status")),unsafe_allow_html=True)
            c[16].markdown(_txt(d.get("Remark")),unsafe_allow_html=True)

shown_from=start_idx+1 if total_rows else 0
shown_to=min(end_idx,total_rows)
st.markdown(f"<div class='slux-foot'>Total {total_rows:,} material lines &nbsp; • &nbsp; Showing {shown_from}–{shown_to} &nbsp; • &nbsp; Page {st.session_state.srn_lux_page} of {total_pages}</div>",unsafe_allow_html=True)

p1,p2,p3=st.columns([1,2,1])
with p1:
    if st.button("⬅️ Previous",disabled=st.session_state.srn_lux_page==1,use_container_width=True):
        st.session_state.srn_lux_page-=1; st.rerun()
with p2:
    st.markdown(f"<div style='text-align:center;font-weight:800;color:#4338ca;padding-top:10px;'>Page {st.session_state.srn_lux_page} of {total_pages}</div>",unsafe_allow_html=True)
with p3:
    if st.button("Next ➡️",disabled=st.session_state.srn_lux_page==total_pages,use_container_width=True):
        st.session_state.srn_lux_page+=1; st.rerun()

