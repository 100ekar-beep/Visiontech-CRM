"""
Material Dispatch Tracking App (Supabase backend)
---------------------------------------------------
Styled to match the Team & Vendor Billing page exactly:
  - custom nav bar buttons (VISPL / Bhagyashree / Sai Tele) instead of st.tabs
  - custom nav bar buttons (Dispatch Pending / Dispatched) instead of st.tabs
  - round icon action buttons (✏️ edit, 🗑️ delete) in a custom row table
  - Table View / Mobile Card View toggle
  - Add / Edit Entry via st.dialog popup

Requires in .streamlit/secrets.toml (same nested format as other pages):

    [supabase]
    url = "https://xxxxx.supabase.co"
    key = "your-anon-or-service-key"

Tables used:
  - site_data          (ALREADY EXISTS - read only)
        columns used: workspace, "Project ID", "Site ID", "Site Name", "Cluster"
  - item_master         (ALREADY EXISTS - read only)
        columns used: item_code, item_description
  - material_dispatch   (NEW TABLE - this page reads/writes it)
        columns: company, project_id, site_name, site_id, cluster, boq,
                 material, qty, status, dispatch_date, vis_remark
"""

import streamlit as st
import pandas as pd
import io
from datetime import date
from supabase import create_client, Client
from st_keyup import st_keyup

# ----------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ----------------------------------------------------------------------
st.set_page_config(page_title="Material Dispatch", page_icon="📦", layout="wide")

if 'dispatch_active_company' not in st.session_state:
    st.session_state.dispatch_active_company = "VISPL"
if 'dispatch_status_tab' not in st.session_state:
    st.session_state.dispatch_status_tab = "pending"
if 'dispatch_view_mode' not in st.session_state:
    st.session_state.dispatch_view_mode = "table"

COMPANIES = [
    ("VISPL", "VISPL"),
    ("Bhagyashree", "Bhagyashree"),
    ("Sai Tele", "Sai Tele"),
]
COMPANY_WORKSPACE_MAP = {
    "VISPL": "VISPL",
    "Bhagyashree": "BHAGYASHREE",
    "Sai Tele": "SAI TELE SERVICES",
}
STATUS_OPTIONS = ["Dispatch Pending", "Dispatched"]

# ----------------------------------------------------------------------
# 2. PREMIUM CSS (matches Team & Vendor Billing page)
# ----------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

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

    div[data-testid="stDialog"] > div {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2 {
        color: #1e293b !important; font-weight: 800 !important; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px;
    }

    /* =========================================================
       MAIN NAV BAR — Company tabs (VISPL / Bhagyashree / Sai Tele)
       ========================================================= */
    .st-key-dispatch_nav_bar div[data-testid="stHorizontalBlock"] { gap: 12px !important; flex-wrap: wrap !important; }
    .st-key-dispatch_nav_bar button {
        font-size: 1.05rem !important; font-weight: 800 !important; padding: 16px 10px !important;
        height: auto !important; border-radius: 12px !important; transition: all 0.25s ease !important;
        white-space: nowrap !important; box-shadow: none !important;
    }
    .st-key-dispatch_nav_bar button[kind="secondary"] { background: #ffffff !important; color: #475569 !important; border: 1.5px solid #e2e8f0 !important; }
    .st-key-dispatch_nav_bar button[kind="secondary"]:hover { background: #f1f5f9 !important; color: #0f172a !important; border-color: #cbd5e1 !important; transform: translateY(-2px) !important; }
    .st-key-dispatch_nav_bar button[kind="secondary"] p, .st-key-dispatch_nav_bar button[kind="secondary"] span, .st-key-dispatch_nav_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; font-size: 1.05rem !important; }
    .st-key-dispatch_nav_bar button[kind="secondary"]:hover p, .st-key-dispatch_nav_bar button[kind="secondary"]:hover span, .st-key-dispatch_nav_bar button[kind="secondary"]:hover div { color: #0f172a !important; }
    .st-key-dispatch_nav_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important; color: #ffffff !important; border: none !important;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
    }
    .st-key-dispatch_nav_bar button[kind="primary"] p, .st-key-dispatch_nav_bar button[kind="primary"] span, .st-key-dispatch_nav_bar button[kind="primary"] div { color: #ffffff !important; font-weight: 800 !important; font-size: 1.05rem !important; }

    /* =========================================================
       SUB-TAB BAR — Dispatch Pending / Dispatched
       ========================================================= */
    .st-key-dispatch_status_bar div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
    .st-key-dispatch_status_bar button {
        font-size: 0.92rem !important; font-weight: 800 !important; padding: 10px 8px !important;
        height: auto !important; border-radius: 10px !important; box-shadow: none !important;
    }
    .st-key-dispatch_status_bar button[kind="secondary"] { background: #ffffff !important; color: #475569 !important; border: 1.5px solid #e2e8f0 !important; }
    .st-key-dispatch_status_bar button[kind="secondary"] p, .st-key-dispatch_status_bar button[kind="secondary"] span, .st-key-dispatch_status_bar button[kind="secondary"] div { color: #475569 !important; font-weight: 800 !important; }
    .st-key-dispatch_status_bar button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important; color: #ffffff !important; border: none !important;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35) !important;
    }

    /* =========================================================
       ROW-BASED TABLE (Site Data Hub style)
       ========================================================= */
    .st-key-dsp_table_header {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 45%, #8b5cf6 100%) !important;
        border-radius: 14px 14px 0 0 !important; overflow: hidden auto !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10) !important;
    }
    .st-key-dsp_table_header div[data-testid="stHorizontalBlock"] {
        min-width: 1300px !important; align-items: center !important; flex-wrap: nowrap !important; padding: 10px 0 !important;
    }
    .st-key-dsp_table_wrap {
        background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-top: none !important;
        border-radius: 0 0 14px 14px !important; overflow: auto !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.10), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        padding: 4px 0 !important; margin-bottom: 20px !important;
    }
    .st-key-dsp_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1300px !important; align-items: center !important; border-bottom: 1px solid #f1f5f9 !important;
        padding: 7px 0 !important; flex-wrap: nowrap !important;
    }
    .st-key-dsp_table_wrap div[data-testid="stHorizontalBlock"]:hover { background: #eef2ff !important; }
    .st-key-dsp_table_header div[data-testid="column"], .st-key-dsp_table_wrap div[data-testid="column"] {
        padding: 0 12px !important; display: flex; align-items: center; justify-content: flex-start;
    }
    .st-key-dsp_table_header div[data-testid="column"] { border-right: 1px solid rgba(255, 255, 255, 0.15); }
    .st-key-dsp_table_wrap div[data-testid="column"] { border-right: 1px solid #f8fafc; }
    .st-key-dsp_table_header div[data-testid="column"]:last-child, .st-key-dsp_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-dsp_table_header .tbl-head {
        color: #ffffff !important; font-size: 0.72rem !important; font-weight: 800 !important;
        letter-spacing: 0.6px !important; text-transform: uppercase !important; white-space: nowrap !important; padding: 4px 0 !important;
    }
    .st-key-dsp_table_wrap .tbl-cell {
        color: #1e293b !important; font-size: 0.85rem !important; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    .st-key-dsp_table_wrap .tbl-serial { color: #94a3b8 !important; font-weight: 800 !important; font-size: 0.82rem !important; }
    .st-key-dsp_table_wrap button {
        height: 32px !important; width: 100% !important; max-width: 34px !important; padding: 0 !important;
        min-height: 0 !important; border-radius: 8px !important; margin: 0 auto !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        box-shadow: none !important; font-size: 0.95rem !important;
    }
    div[class*="st-key-dsp_edit_"] button { background: rgba(99, 102, 241, 0.14) !important; border: 1px solid rgba(99, 102, 241, 0.35) !important; }
    div[class*="st-key-dsp_edit_"] button:hover { background: #6366f1 !important; transform: translateY(-2px) !important; }
    div[class*="st-key-dsp_del_"] button { background: rgba(239, 68, 68, 0.14) !important; border: 1px solid rgba(239, 68, 68, 0.35) !important; }
    div[class*="st-key-dsp_del_"] button:hover { background: #ef4444 !important; transform: translateY(-2px) !important; }

    /* =========================================================
       MOBILE CARD VIEW
       ========================================================= */
    .billing-card-title { font-size: 1.02rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; }
    .billing-card-sub { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .billing-card-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; font-size: 0.85rem; }
    .billing-card-row:last-child { border-bottom: none; }
    .billing-card-label { color: #64748b; font-weight: 600; }
    .billing-card-value { color: #1e293b; font-weight: 600; text-align: right; }
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

# ----------------------------------------------------------------------
# 3. SUPABASE CONNECTION
# ----------------------------------------------------------------------
@st.cache_resource
def get_supabase_client():
    try:
        url: str = st.secrets["supabase"]["url"]
        url = url.strip().replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
        key: str = st.secrets["supabase"]["key"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"🚨 Supabase connection error: {e}")
        return None


supabase = get_supabase_client()
if supabase is None:
    st.stop()


def cell(val):
    """Safely render a table cell value: None / NaN / 'nan' string all become '-'."""
    if val is None:
        return "-"
    try:
        if isinstance(val, float) and pd.isna(val):
            return "-"
    except Exception:
        pass
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none", "nat"):
        return "-"
    return s


# ----------------------------------------------------------------------
# 4. DATA FETCHING (master data - read only)
# ----------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def load_site_master():
    try:
        res = supabase.table("site_data").select("*").execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        df = pd.DataFrame()
    rename_map = {
        "workspace": "company", "Project ID": "project_id", "Site ID": "site_id",
        "Site Name": "site_name", "Cluster": "cluster",
    }
    df = df.rename(columns=rename_map)
    keep_cols = [c for c in ["company", "project_id", "site_id", "site_name", "cluster"] if c in df.columns]
    return df[keep_cols] if keep_cols else pd.DataFrame(columns=["company", "project_id", "site_id", "site_name", "cluster"])


@st.cache_data(ttl=60, show_spinner=False)
def load_item_master():
    try:
        res = supabase.table("item_master").select("*").execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["item_code", "item_description"])
    except Exception as e:
        st.session_state["_item_master_error"] = str(e)
        df = pd.DataFrame(columns=["item_code", "item_description"])
    return df


@st.cache_data(ttl=30, show_spinner=False)
def fetch_dispatch_cached(company):
    try:
        res = supabase.table("material_dispatch").select("*").eq("company", company).order("id", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def insert_dispatch_rows(rows):
    supabase.table("material_dispatch").insert(rows).execute()


def update_dispatch_row(row_id, payload):
    supabase.table("material_dispatch").update(payload).eq("id", row_id).execute()


def delete_dispatch_row(row_id):
    supabase.table("material_dispatch").delete().eq("id", row_id).execute()


def df_to_excel_bytes(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


site_df = load_site_master()
item_df = load_item_master()

if item_df.empty or "item_description" not in item_df.columns:
    err = st.session_state.get("_item_master_error")
    if err:
        st.warning(f"item_master se data nahi mil paya: {err}")
    else:
        st.warning("item_master table khali dikh raha hai ya 'item_description' column nahi mila — table name/RLS policy check karo.")

# ----------------------------------------------------------------------
# 5. ADD / EDIT ENTRY DIALOG
# ----------------------------------------------------------------------
@st.dialog("📦 New Dispatch Entry", width="large")
def add_entry_dialog(company):
    boq_key = "dsp_new_boq_rows"
    if boq_key not in st.session_state:
        st.session_state[boq_key] = [{"boq": "", "material": "", "qty": 0.0}]

    workspace_value = COMPANY_WORKSPACE_MAP.get(company, company)
    company_sites = site_df[site_df["company"] == workspace_value] if "company" in site_df.columns else pd.DataFrame()

    if company_sites.empty:
        st.warning(f"'{company}' (workspace = '{workspace_value}') ke liye site_data me koi Project ID nahi mila.")
        return

    project_ids = company_sites["project_id"].dropna().unique().tolist()
    project_id = st.selectbox(
        "Project ID *",
        options=["-- Select Project ID --"] + project_ids,
        index=0,
        key="dsp_new_project_id",
    )

    if project_id == "-- Select Project ID --":
        st.info("Project ID select karo form aage badhane ke liye.")
        return

    site_row = company_sites[company_sites["project_id"] == project_id].iloc[0]
    site_name = site_row.get("site_name", "")
    site_id = site_row.get("site_id", "")
    cluster = site_row.get("cluster", "")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**SITE NAME**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{site_name or '-'}</span>", unsafe_allow_html=True)
    c2.markdown(f"**SITE ID**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{site_id or '-'}</span>", unsafe_allow_html=True)
    c3.markdown(f"**CLUSTER**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{cluster or '-'}</span>", unsafe_allow_html=True)

    st.markdown("**BOQ / Material / Qty lines**")
    item_options = item_df["item_description"].dropna().unique().tolist() if "item_description" in item_df.columns else []

    rows_to_remove = None
    for idx, row in enumerate(st.session_state[boq_key]):
        rc1, rc2, rc3, rc4 = st.columns([2, 3, 2, 1])
        row["boq"] = rc1.text_input("BOQ", value=row["boq"], key=f"{boq_key}_boq_{idx}")
        if item_options:
            default_index = item_options.index(row["material"]) if row["material"] in item_options else 0
            row["material"] = rc2.selectbox("Material", options=item_options, index=default_index, key=f"{boq_key}_mat_{idx}")
        else:
            row["material"] = rc2.text_input("Material (item_master empty)", value=row["material"], key=f"{boq_key}_mat_txt_{idx}")
        qty_input = rc3.number_input(
            "Qty", min_value=0.0, value=None, step=1.0, placeholder="0", key=f"{boq_key}_qty_{idx}"
        )
        row["qty"] = qty_input if qty_input is not None else 0.0
        if len(st.session_state[boq_key]) > 1:
            if rc4.button("🗑️", key=f"{boq_key}_del_{idx}"):
                rows_to_remove = idx

    if rows_to_remove is not None:
        st.session_state[boq_key].pop(rows_to_remove)
        st.rerun()

    if st.button("+ Add New BOQ"):
        st.session_state[boq_key].append({"boq": "", "material": "", "qty": 0.0})
        st.rerun()

    st.markdown("---")
    status = st.selectbox("Status *", options=STATUS_OPTIONS, key="dsp_new_status")

    dispatch_date_val = None
    if status == "Dispatched":
        dispatch_date_val = st.date_input("Dispatch Date * (compulsory)", value=date.today(), key="dsp_new_date")

    vis_remark = st.text_input("VIS Remark", value=status, key="dsp_new_remark")

    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        valid_rows = [r for r in st.session_state[boq_key] if r["boq"].strip() and r["material"] and r["qty"] > 0]
        if not valid_rows:
            st.error("Kam se kam ek BOQ line complete bharo (BOQ, Material, Qty).")
        elif status == "Dispatched" and not dispatch_date_val:
            st.error("Status 'Dispatched' hai to Dispatch Date compulsory hai.")
        else:
            dispatch_date_str = dispatch_date_val.strftime("%Y-%m-%d") if dispatch_date_val else None
            rows = [
                {
                    "company": company, "project_id": project_id, "site_name": site_name,
                    "site_id": str(site_id), "cluster": str(cluster), "boq": r["boq"],
                    "material": r["material"], "qty": r["qty"], "status": status,
                    "dispatch_date": dispatch_date_str, "vis_remark": vis_remark,
                }
                for r in valid_rows
            ]
            try:
                insert_dispatch_rows(rows)
                st.session_state[boq_key] = [{"boq": "", "material": "", "qty": 0.0}]
                fetch_dispatch_cached.clear()
                st.success(f"{len(rows)} entry saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")


@st.dialog("✏️ Edit Dispatch Entry", width="large")
def edit_entry_dialog(row_data, company):
    workspace_value = COMPANY_WORKSPACE_MAP.get(company, company)
    company_sites = site_df[site_df["company"] == workspace_value] if "company" in site_df.columns else pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**PROJECT ID**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{row_data.get('project_id', '') or '-'}</span>", unsafe_allow_html=True)
    c2.markdown(f"**SITE NAME**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{row_data.get('site_name', '') or '-'}</span>", unsafe_allow_html=True)
    c3.markdown(f"**CLUSTER**<br><span style='color:#0f172a; font-weight:800; font-size:1rem;'>{row_data.get('cluster', '') or '-'}</span>", unsafe_allow_html=True)

    item_options = item_df["item_description"].dropna().unique().tolist() if "item_description" in item_df.columns else []

    e1, e2, e3 = st.columns(3)
    boq_val = e1.text_input("BOQ", value=row_data.get("boq", ""))
    if item_options:
        default_index = item_options.index(row_data.get("material", "")) if row_data.get("material", "") in item_options else 0
        material_val = e2.selectbox("Material", options=item_options, index=default_index)
    else:
        material_val = e2.text_input("Material", value=row_data.get("material", ""))
    qty_val = e3.number_input("Qty", min_value=0.0, value=float(row_data.get("qty") or 0), step=1.0)

    status_val = st.selectbox(
        "Status", options=STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(row_data.get("status")) if row_data.get("status") in STATUS_OPTIONS else 0,
    )

    dispatch_date_val = None
    if status_val == "Dispatched":
        try:
            default_date = pd.to_datetime(row_data.get("dispatch_date")).date() if row_data.get("dispatch_date") else date.today()
        except Exception:
            default_date = date.today()
        dispatch_date_val = st.date_input("Dispatch Date (compulsory)", value=default_date)

    remark_val = st.text_input("VIS Remark", value=row_data.get("vis_remark", status_val))

    save_col, del_col = st.columns(2)
    if save_col.button("💾 Update Entry", type="primary", use_container_width=True):
        if status_val == "Dispatched" and not dispatch_date_val:
            st.error("Status 'Dispatched' hai to Dispatch Date compulsory hai.")
        else:
            payload = {
                "boq": boq_val, "material": material_val, "qty": qty_val, "status": status_val,
                "dispatch_date": dispatch_date_val.strftime("%Y-%m-%d") if dispatch_date_val else None,
                "vis_remark": remark_val,
            }
            try:
                update_dispatch_row(row_data["id"], payload)
                fetch_dispatch_cached.clear()
                st.success("Entry updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

    if del_col.button("🗑️ Delete Entry", use_container_width=True):
        try:
            delete_dispatch_row(row_data["id"])
            fetch_dispatch_cached.clear()
            st.success("Entry deleted!")
            st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")


# ----------------------------------------------------------------------
# 6. MAIN PAGE NAVIGATION (custom buttons, matches Team & Vendor Billing)
# ----------------------------------------------------------------------
st.markdown("<h1 style='color:#0f172a; margin-bottom: 20px;'>📦 Material Dispatch</h1>", unsafe_allow_html=True)

with st.container(key="dispatch_nav_bar"):
    nav_cols = st.columns(len(COMPANIES))
    for nav_col, (company_id, company_label) in zip(nav_cols, COMPANIES):
        is_active = st.session_state.dispatch_active_company == company_id
        with nav_col:
            if st.button(company_label, key=f"dispatch_nav_{company_id}", use_container_width=True, type=("primary" if is_active else "secondary")):
                st.session_state.dispatch_active_company = company_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

col_viewtoggle_space, col_viewtoggle = st.columns([5, 2])
with col_viewtoggle:
    toggle_label = "📱 Mobile View" if st.session_state.dispatch_view_mode == "table" else "🖥️ Table View"
    if st.button(toggle_label, use_container_width=True, key="dispatch_view_toggle"):
        st.session_state.dispatch_view_mode = "cards" if st.session_state.dispatch_view_mode == "table" else "table"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

active_company = st.session_state.dispatch_active_company

# --- Dispatch Pending / Dispatched sub-tabs ---
STATUS_TABS = [("pending", "🟡 Dispatch Pending"), ("dispatched", "🟢 Dispatched")]
with st.container(key="dispatch_status_bar"):
    sub_cols = st.columns(len(STATUS_TABS))
    for sub_col, (tab_id, tab_label) in zip(sub_cols, STATUS_TABS):
        is_active_sub = st.session_state.dispatch_status_tab == tab_id
        with sub_col:
            if st.button(tab_label, key=f"dispatch_status_{tab_id}", use_container_width=True, type=("primary" if is_active_sub else "secondary")):
                st.session_state.dispatch_status_tab = tab_id
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

active_status = "Dispatch Pending" if st.session_state.dispatch_status_tab == "pending" else "Dispatched"

# --- Search / Add / Download row ---
col_search, col_addbtn, col_dl = st.columns([3.5, 2, 1.5])
with col_search:
    search_term = st_keyup("Search", placeholder="🔍 Search dispatch records...", label_visibility="collapsed", key=f"dispatch_search_{active_company}")
with col_addbtn:
    if st.button("➕ Add New Entry", type="primary", use_container_width=True):
        add_entry_dialog(active_company)
with col_dl:
    pass  # download button placed after data is loaded (needs df)

# --- Load + filter data ---
raw_rows = fetch_dispatch_cached(active_company)
df_all = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame(
    columns=["id", "company", "project_id", "site_name", "site_id", "cluster",
             "boq", "material", "qty", "status", "dispatch_date", "vis_remark", "created_at"]
)

df_status = df_all[df_all["status"] == active_status] if not df_all.empty else df_all

if search_term and not df_status.empty:
    mask = df_status.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False))
    df_filtered = df_status[mask.any(axis=1)]
else:
    df_filtered = df_status

with col_dl:
    st.download_button(
        "⬇️ Download",
        data=df_to_excel_bytes(df_filtered, active_status[:31]),
        file_name=f"{active_company}_{active_status.replace(' ', '_')}.xlsx",
        use_container_width=True,
        key=f"dispatch_download_{active_company}_{st.session_state.dispatch_status_tab}",
    )

st.caption(f"Total: {len(df_filtered)}")

# ----------------------------------------------------------------------
# 7. RENDER TABLE / CARDS
# ----------------------------------------------------------------------
if df_filtered.empty:
    st.info("Koi record nahi mila.")
else:
    df_filtered = df_filtered.reset_index(drop=True)

    if st.session_state.dispatch_view_mode == "cards":
        # -------------------- MOBILE CARD VIEW --------------------
        for pos, (_, row) in enumerate(df_filtered.iterrows()):
            row_dict = row.to_dict()
            rid = row_dict.get("id")
            with st.container(border=True):
                st.markdown(f"""
                    <div class="billing-card-title">#{pos + 1} — {cell(row_dict.get('project_id'))}</div>
                    <div class="billing-card-sub">{cell(row_dict.get('site_name'))} • {cell(row_dict.get('status'))}</div>
                    <div class="billing-card-row"><span class="billing-card-label">Site ID</span><span class="billing-card-value">{cell(row_dict.get('site_id'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">Cluster</span><span class="billing-card-value">{cell(row_dict.get('cluster'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">BOQ</span><span class="billing-card-value">{cell(row_dict.get('boq'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">Material</span><span class="billing-card-value">{cell(row_dict.get('material'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">Qty</span><span class="billing-card-value">{cell(row_dict.get('qty'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">Dispatch Date</span><span class="billing-card-value">{cell(row_dict.get('dispatch_date'))}</span></div>
                    <div class="billing-card-row"><span class="billing-card-label">VIS Remark</span><span class="billing-card-value">{cell(row_dict.get('vis_remark'))}</span></div>
                """, unsafe_allow_html=True)

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("✏️ Edit", key=f"dspc_edit_{rid}", use_container_width=True):
                        edit_entry_dialog(row_dict, active_company)
                with bc2:
                    if st.button("🗑️ Delete", key=f"dspc_del_{rid}", use_container_width=True):
                        try:
                            delete_dispatch_row(rid)
                            fetch_dispatch_cached.clear()
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    else:
        # -------------------- DESKTOP TABLE VIEW --------------------
        COL_RATIOS = [0.35, 0.35, 0.35, 1.0, 1.1, 0.9, 0.9, 1.3, 0.7, 1.0, 1.1, 1.3]
        COL_LABELS = ["#", "✏️", "🗑️", "PROJECT ID", "SITE NAME", "SITE ID", "CLUSTER", "MATERIAL", "QTY", "BOQ", "DISPATCH DATE", "VIS REMARK"]

        with st.container(key="dsp_table_header"):
            h_cols = st.columns(COL_RATIOS)
            for h_col, label in zip(h_cols, COL_LABELS):
                h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

        with st.container(key="dsp_table_wrap", height=500):
            for pos, (_, row) in enumerate(df_filtered.iterrows()):
                row_dict = row.to_dict()
                rid = row_dict.get("id")
                rcols = st.columns(COL_RATIOS)

                rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{pos + 1}</div>", unsafe_allow_html=True)

                with rcols[1]:
                    if st.button("✏️", key=f"dsp_edit_{rid}", help="Edit Entry", use_container_width=True):
                        edit_entry_dialog(row_dict, active_company)
                with rcols[2]:
                    if st.button("🗑️", key=f"dsp_del_{rid}", help="Delete Entry", use_container_width=True):
                        try:
                            delete_dispatch_row(rid)
                            fetch_dispatch_cached.clear()
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                rcols[3].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('project_id'))}</div>", unsafe_allow_html=True)
                rcols[4].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_name'))}</div>", unsafe_allow_html=True)
                rcols[5].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('site_id'))}</div>", unsafe_allow_html=True)
                rcols[6].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('cluster'))}</div>", unsafe_allow_html=True)
                rcols[7].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('material'))}</div>", unsafe_allow_html=True)
                rcols[8].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('qty'))}</div>", unsafe_allow_html=True)
                rcols[9].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('boq'))}</div>", unsafe_allow_html=True)
                rcols[10].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('dispatch_date'))}</div>", unsafe_allow_html=True)
                rcols[11].markdown(f"<div class='tbl-cell'>{cell(row_dict.get('vis_remark'))}</div>", unsafe_allow_html=True)
