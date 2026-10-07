import streamlit as st
import pandas as pd
import io
import re
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

SRN_STATUS_OPTIONS = [
    "Pending",
    "In Process",
    "Submitted",
    "Not Required",
]

POD_STATUS_OPTIONS = [
    "Pending",
    "Available",
    "Submitted",
    "Not Required",
]

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


@st.dialog("✏️ Update SRN Site", width="large")
def edit_site_dialog(site_id, site_df):
    first = site_df.iloc[0].to_dict()

    st.caption(
        "Ye update selected Site ID ki sabhi current material lines par apply hoga."
    )

    c1, c2 = st.columns(2)
    with c1:
        team_name = st.text_input(
            "Team Name",
            value=clean_text(first.get("Team Name")),
            placeholder="Enter / select team name",
        )
    with c2:
        current_status = clean_text(first.get("SRN Status")) or "Pending"
        status_index = (
            SRN_STATUS_OPTIONS.index(current_status)
            if current_status in SRN_STATUS_OPTIONS
            else 0
        )
        srn_status = st.selectbox(
            "SRN Status",
            SRN_STATUS_OPTIONS,
            index=status_index,
        )

    c3, c4 = st.columns(2)
    with c3:
        existing_date = pd.to_datetime(
            first.get("SRN Date"), errors="coerce", dayfirst=True
        )
        default_date = (
            existing_date.date()
            if not pd.isna(existing_date)
            else None
        )
        srn_date = st.date_input(
            "SRN Date",
            value=default_date,
            format="DD-MM-YYYY",
        )
    with c4:
        srn_from = st.text_input(
            "SRN From",
            value=clean_text(first.get("SRN From")),
            placeholder="SRN received/from detail",
        )

    c5, c6 = st.columns(2)
    with c5:
        current_pod = clean_text(first.get("POD Status")) or "Pending"
        pod_index = (
            POD_STATUS_OPTIONS.index(current_pod)
            if current_pod in POD_STATUS_OPTIONS
            else 0
        )
        pod_status = st.selectbox(
            "POD Status",
            POD_STATUS_OPTIONS,
            index=pod_index,
        )
    with c6:
        remark = st.text_area(
            "Remark",
            value=clean_text(first.get("Remark")),
            height=100,
        )

    st.markdown("#### Material lines in this Site ID")
    preview_cols = [
        "Project Number",
        "Item Cat 2",
        "Item Description",
        "BOQ Quantity",
        "Ageing Slab",
    ]
    st.dataframe(
        site_df[preview_cols],
        use_container_width=True,
        hide_index=True,
        height=min(300, 75 + len(site_df) * 35),
    )

    if st.button(
        "💾 Save Site Update",
        type="primary",
        use_container_width=True,
    ):
        try:
            update_dict = {
                "team_name": clean_text(team_name),
                "srn_status": srn_status,
                "srn_date": srn_date.isoformat() if srn_date else None,
                "srn_from": clean_text(srn_from),
                "pod_status": pod_status,
                "remark": clean_text(remark),
                "updated_at": datetime.now().isoformat(),
            }

            (
                supabase.table(SRN_TABLE)
                .update(update_dict)
                .eq("workspace", active_ws)
                .eq("site_id", site_id)
                .execute()
            )

            clear_srn_cache()
            st.success("✅ Site SRN details updated successfully.")
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
        f'<div class="metric-card"><div class="metric-title">Total Sites</div>'
        f'<div class="metric-value">{total_sites:,}</div></div>',
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Total Material Lines</div>'
        f'<div class="metric-value">{total_lines:,}</div></div>',
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Pending Sites</div>'
        f'<div class="metric-value">{pending_sites:,}</div></div>',
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Submitted Sites</div>'
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
# 12. PROPER CONTINUOUS TABLE VIEW
# ============================================================
if filtered_df.empty:
    st.warning("⚠️ Search/filter ke hisab se koi record nahi mila.")
    st.stop()

st.markdown("### 📋 SRN Pending Details")

# User-requested exact screen order
table_columns = [
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

table_df = filtered_df[table_columns].copy()

# Proper row numbering
table_df.index = range(1, len(table_df) + 1)
table_df.index.name = "Sr No"

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=False,
    height=650,
    column_config={
        "Site ID": st.column_config.TextColumn(
            "Site ID",
            width="medium",
        ),
        "Site Name": st.column_config.TextColumn(
            "Site Name",
            width="medium",
        ),
        "Cluster": st.column_config.TextColumn(
            "Cluster",
            width="medium",
        ),
        "Technician Detail": st.column_config.TextColumn(
            "Technician Detail",
            width="large",
        ),
        "Item Cat 2": st.column_config.TextColumn(
            "Item Cat 2",
            width="medium",
        ),
        "Ageing Slab": st.column_config.TextColumn(
            "Ageing Slab",
            width="medium",
        ),
        "Project Number": st.column_config.TextColumn(
            "Project Number",
            width="medium",
        ),
        "Item Description": st.column_config.TextColumn(
            "Item Description",
            width="large",
        ),
        "BOQ Quantity": st.column_config.NumberColumn(
            "BOQ Quantity",
            format="%.4f",
            width="small",
        ),
        "Team Name": st.column_config.TextColumn(
            "Team Name",
            width="medium",
        ),
        "SRN Status": st.column_config.TextColumn(
            "SRN Status",
            width="medium",
        ),
        "SRN Date": st.column_config.TextColumn(
            "SRN Date",
            width="medium",
        ),
        "SRN From": st.column_config.TextColumn(
            "SRN From",
            width="medium",
        ),
        "POD Status": st.column_config.TextColumn(
            "POD Status",
            width="medium",
        ),
        "Remark": st.column_config.TextColumn(
            "Remark",
            width="large",
        ),
    },
)

st.caption(
    f"Total: {len(table_df):,} material line(s) • "
    f"{filtered_df['Site ID'].replace('', pd.NA).dropna().nunique():,} unique Site ID(s)"
)

