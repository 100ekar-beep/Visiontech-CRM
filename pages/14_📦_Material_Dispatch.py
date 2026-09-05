"""
Material Dispatch Tracking App (Supabase backend)
---------------------------------------------------
Run with:  streamlit run material_dispatch_app.py

Requires in .streamlit/secrets.toml (same nested format as your other pages):

    [supabase]
    url = "https://xxxxx.supabase.co"
    key = "your-anon-or-service-key"

Ye app 3 Supabase tables use karta hai:

  - site_data          (ALREADY EXISTS - read only)
        columns used: workspace, "Project ID", "Site ID", "Site Name", "Cluster"

  - item_master         (ALREADY EXISTS - read only)
        columns used: item_code, item_description

  - material_dispatch   (NAYA TABLE - is app se bharega)
        columns: company, project_id, site_name, site_id, cluster, boq,
                 material, qty, status, dispatch_date, vis_remark
"""

import streamlit as st
import pandas as pd
import io
from datetime import date
from supabase import create_client, Client

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
st.set_page_config(page_title="Material Dispatch", page_icon="📦", layout="wide")

# --- PREMIUM THEME (same look as the rest of the app) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    button[data-baseweb="tab"] { font-weight: 700 !important; font-size: 1.1rem !important; }
    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"],
    button[kind="primary"], button[kind="primaryFormSubmit"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
    }
    button[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"],
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {
        background: #ef4444 !important; color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border-radius: 16px !important; overflow: hidden !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12), 0 4px 6px -2px rgba(15, 23, 42, 0.05) !important;
        border: 1px solid #e2e8f0 !important; background: #ffffff !important;
    }
    [data-testid="stDataFrame"] th, [data-testid="stDataEditor"] th,
    [data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataEditor"] [role="columnheader"] {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        color: #ffffff !important; font-weight: 800 !important; font-size: 0.8rem !important;
        letter-spacing: 0.4px !important; text-transform: uppercase !important; border: none !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    div[data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; border-color: transparent !important;
    }
    div[data-testid="stSidebarNav"] a span { color: inherit !important; }
    </style>
""", unsafe_allow_html=True)

# --- TOP SINGLE WORKSPACE BANNER (same as rest of app) ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

COMPANIES = ["VISPL", "Bhagyashree", "Sai Tele"]
STATUS_OPTIONS = ["Dispatch Pending", "Dispatched"]

# Display name (used as tab label and stored in material_dispatch.company)
# -> actual value stored in site_data.workspace
COMPANY_WORKSPACE_MAP = {
    "VISPL": "VISPL",
    "Bhagyashree": "BHAGYASHREE",
    "Sai Tele": "SAI TELE SERVICES",
}

DISPLAY_RENAME = {
    "id": "ID",
    "company": "Company",
    "project_id": "Project ID",
    "site_name": "Site Name",
    "site_id": "Site ID",
    "cluster": "Cluster",
    "boq": "BOQ",
    "material": "Material",
    "qty": "Qty",
    "status": "Status",
    "dispatch_date": "Dispatch Date",
    "vis_remark": "VIS Remark",
    "created_at": "Created At",
}


# ----------------------------------------------------------------------
# SUPABASE CLIENT
# ----------------------------------------------------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["supabase"]["url"]
    url = url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


supabase = get_supabase_client()


# ----------------------------------------------------------------------
# DATA HELPERS - MASTER DATA (READ ONLY, existing tables)
# ----------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_site_master() -> pd.DataFrame:
    """Reads from the existing `site_data` table and standardizes column names."""
    res = supabase.table("site_data").select("*").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame(
        columns=["workspace", "Project ID", "Site ID", "Site Name", "Cluster"]
    )
    rename_map = {
        "workspace": "company",
        "Project ID": "project_id",
        "Site ID": "site_id",
        "Site Name": "site_name",
        "Cluster": "cluster",
    }
    df = df.rename(columns=rename_map)
    keep_cols = [c for c in ["company", "project_id", "site_id", "site_name", "cluster"] if c in df.columns]
    return df[keep_cols]


@st.cache_data(ttl=60)
def load_item_master() -> pd.DataFrame:
    """Reads from the existing `item_master` table."""
    res = supabase.table("item_master").select("item_code, item_description").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["item_code", "item_description"])
    return df


# ----------------------------------------------------------------------
# DATA HELPERS - DISPATCH ENTRIES (new table: material_dispatch)
# ----------------------------------------------------------------------
def load_dispatch(company: str) -> pd.DataFrame:
    res = (
        supabase.table("material_dispatch")
        .select("*")
        .eq("company", company)
        .order("id", desc=True)
        .execute()
    )
    cols = ["id", "company", "project_id", "site_name", "site_id", "cluster",
            "boq", "material", "qty", "status", "dispatch_date", "vis_remark", "created_at"]
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=cols)


def insert_dispatch_rows(rows: list[dict]):
    supabase.table("material_dispatch").insert(rows).execute()


def delete_dispatch_row(row_id: int):
    supabase.table("material_dispatch").delete().eq("id", row_id).execute()


def df_to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


# ----------------------------------------------------------------------
# ADD NEW ENTRY FORM
# ----------------------------------------------------------------------
def render_add_entry_form(company: str, site_df: pd.DataFrame, item_df: pd.DataFrame):
    boq_key = f"boq_rows_{company}"
    if boq_key not in st.session_state:
        st.session_state[boq_key] = [{"boq": "", "material": "", "qty": 0.0}]

    workspace_value = COMPANY_WORKSPACE_MAP.get(company, company)
    company_sites = site_df[site_df["company"] == workspace_value] if "company" in site_df.columns else pd.DataFrame()

    with st.container(border=True):
        st.subheader(f"➕ New Dispatch Entry — {company}")

        if company_sites.empty:
            st.warning(
                f"'{company}' (workspace = '{workspace_value}') ke liye site_data table me "
                "koi Project ID nahi mila. workspace column ki value check karo."
            )
            if st.button("Close", key=f"close_empty_{company}"):
                st.session_state[f"show_form_{company}"] = False
                st.rerun()
            return

        project_ids = company_sites["project_id"].dropna().unique().tolist()
        project_id = st.selectbox("Project ID", options=project_ids, key=f"project_id_{company}")

        site_row = company_sites[company_sites["project_id"] == project_id].iloc[0]
        site_name = site_row.get("site_name", "")
        site_id = site_row.get("site_id", "")
        cluster = site_row.get("cluster", "")

        c1, c2, c3 = st.columns(3)
        c1.text_input("Site Name", value=site_name, disabled=True, key=f"site_name_disp_{company}")
        c2.text_input("Site ID", value=str(site_id), disabled=True, key=f"site_id_disp_{company}")
        c3.text_input("Cluster", value=str(cluster), disabled=True, key=f"cluster_disp_{company}")

        st.markdown("**BOQ / Material / Qty lines**")
        item_options = item_df["item_description"].dropna().unique().tolist() if "item_description" in item_df.columns else []

        rows_to_remove = None
        for idx, row in enumerate(st.session_state[boq_key]):
            rc1, rc2, rc3, rc4 = st.columns([2, 3, 2, 1])
            row["boq"] = rc1.text_input("BOQ", value=row["boq"], key=f"{boq_key}_boq_{idx}")
            if item_options:
                default_index = item_options.index(row["material"]) if row["material"] in item_options else 0
                row["material"] = rc2.selectbox(
                    "Material", options=item_options, index=default_index, key=f"{boq_key}_mat_{idx}"
                )
            else:
                row["material"] = rc2.text_input(
                    "Material (item_master empty)", value=row["material"], key=f"{boq_key}_mat_txt_{idx}"
                )
            row["qty"] = rc3.number_input(
                "Qty", min_value=0.0, value=float(row["qty"]), step=1.0, key=f"{boq_key}_qty_{idx}"
            )
            if len(st.session_state[boq_key]) > 1:
                if rc4.button("🗑️", key=f"{boq_key}_del_{idx}"):
                    rows_to_remove = idx

        if rows_to_remove is not None:
            st.session_state[boq_key].pop(rows_to_remove)
            st.rerun()

        if st.button("+ Add New BOQ", key=f"add_boq_{company}"):
            st.session_state[boq_key].append({"boq": "", "material": "", "qty": 0.0})
            st.rerun()

        st.markdown("---")
        status = st.selectbox("Status", options=STATUS_OPTIONS, key=f"status_{company}")

        dispatch_date_val = None
        if status == "Dispatched":
            dispatch_date_val = st.date_input(
                "Dispatch Date (compulsory)", value=date.today(), key=f"dispatch_date_{company}"
            )

        vis_remark = st.text_input("VIS Remark", value=status, key=f"vis_remark_{company}")

        save_col, cancel_col = st.columns(2)
        if save_col.button("💾 Save Entry", type="primary", key=f"save_{company}"):
            valid_rows = [r for r in st.session_state[boq_key] if r["boq"].strip() and r["material"] and r["qty"] > 0]
            if not valid_rows:
                st.error("Kam se kam ek BOQ line complete bharo (BOQ, Material, Qty).")
            elif status == "Dispatched" and not dispatch_date_val:
                st.error("Status 'Dispatched' hai to Dispatch Date compulsory hai.")
            else:
                dispatch_date_str = dispatch_date_val.strftime("%Y-%m-%d") if dispatch_date_val else None
                rows = [
                    {
                        "company": company,
                        "project_id": project_id,
                        "site_name": site_name,
                        "site_id": str(site_id),
                        "cluster": str(cluster),
                        "boq": r["boq"],
                        "material": r["material"],
                        "qty": r["qty"],
                        "status": status,
                        "dispatch_date": dispatch_date_str,
                        "vis_remark": vis_remark,
                    }
                    for r in valid_rows
                ]
                try:
                    insert_dispatch_rows(rows)
                    st.session_state[boq_key] = [{"boq": "", "material": "", "qty": 0.0}]
                    st.session_state[f"show_form_{company}"] = False
                    st.success(f"{len(rows)} entry saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Save failed: {e}")

        if cancel_col.button("Cancel", key=f"cancel_{company}"):
            st.session_state[boq_key] = [{"boq": "", "material": "", "qty": 0.0}]
            st.session_state[f"show_form_{company}"] = False
            st.rerun()


# ----------------------------------------------------------------------
# COMPANY TAB RENDERING
# ----------------------------------------------------------------------
def render_company_tab(company: str, site_df: pd.DataFrame, item_df: pd.DataFrame):
    show_key = f"show_form_{company}"
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    top1, top2, top3 = st.columns([1.2, 3, 1])
    if top1.button("+ Add New Entry", key=f"add_btn_{company}"):
        st.session_state[show_key] = True
        st.rerun()

    search_term = top2.text_input("🔍 Search", key=f"search_{company}", placeholder="Search in table...")

    df = load_dispatch(company)

    if search_term and not df.empty:
        mask = df.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False))
        df_filtered = df[mask.any(axis=1)]
    else:
        df_filtered = df

    display_df = df_filtered.rename(columns=DISPLAY_RENAME)
    top3.download_button(
        "⬇️ Download",
        data=df_to_excel_bytes(display_df, company[:31]),
        file_name=f"{company}_dispatch.xlsx",
        key=f"download_{company}",
    )

    if st.session_state[show_key]:
        render_add_entry_form(company, site_df, item_df)

    st.markdown("### 📋 Dispatch Records")
    pending_tab, dispatched_tab = st.tabs(["🟡 Dispatch Pending", "🟢 Dispatched"])

    with pending_tab:
        pending_df = df_filtered[df_filtered["status"] == "Dispatch Pending"] if not df_filtered.empty else df_filtered
        st.caption(f"Total: {len(pending_df)}")
        st.dataframe(pending_df.rename(columns=DISPLAY_RENAME), use_container_width=True, hide_index=True)

    with dispatched_tab:
        dispatched_df = df_filtered[df_filtered["status"] == "Dispatched"] if not df_filtered.empty else df_filtered
        st.caption(f"Total: {len(dispatched_df)}")
        st.dataframe(dispatched_df.rename(columns=DISPLAY_RENAME), use_container_width=True, hide_index=True)

    with st.expander("🗑️ Delete an entry (by ID)"):
        if not df.empty:
            del_id = st.selectbox("Select ID to delete", options=df["id"].tolist(), key=f"del_select_{company}")
            if st.button("Delete", key=f"del_btn_{company}"):
                delete_dispatch_row(int(del_id))
                st.success(f"Entry {del_id} deleted.")
                st.rerun()
        else:
            st.caption("No entries yet.")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
st.title("📦 Material Dispatch Tracker")

with st.sidebar:
    st.caption("Site data `site_data` aur item data `item_master` tables se auto-load hota hai.")
    if st.button("🔄 Refresh master data"):
        st.cache_data.clear()
        st.rerun()

site_df = load_site_master()
item_df = load_item_master()

if site_df.empty:
    st.warning("site_data table se koi data nahi mila — 'workspace' column me VISPL/Bhagyashree/Sai Tele values check karo.")

tabs = st.tabs(COMPANIES)
for tab, company in zip(tabs, COMPANIES):
    with tab:
        render_company_tab(company, site_df, item_df)
