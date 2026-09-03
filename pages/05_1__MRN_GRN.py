import streamlit as st
import pandas as pd
import math
import io
import datetime
import random
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MRN / GRN Desk", page_icon="📦", layout="wide")

# --- INITIALIZE SESSION STATES ---
if 'mrn_current_page' not in st.session_state:
    st.session_state.mrn_current_page = 1
if 'mrn_action' not in st.session_state:
    st.session_state.mrn_action = ""

# --- 2. LAVISH CUSTOM CSS (Imported from your ecosystem) ---
st.markdown("""
    <style>
    /* Dark Premium Theme */
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Primary Action Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Secondary Action Buttons */
    button[data-testid="baseButton-secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }

    button[data-testid="baseButton-primary"]:hover, 
    button[data-testid="baseButton-secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }

    /* Pagination Text & Button Font Color Fix */
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    div.stButton > button p, div.stButton > button span, div.stButton > button div { color: #ffffff !important; font-weight: 800 !important; }
    
    /* Modal/Dialog Glassmorphism */
    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #ffffff !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p { color: #e2e8f0 !important; }
    div[data-testid="stDialog"] button[kind="icon"] svg { fill: #ffffff !important; }

    .modal-section-title {
        color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;
        margin-top: 15px; margin-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 5px;
    }
    
    label p, label[data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px; }

    /* Make disabled/read-only input text strictly BLACK and BOLD */
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important; font-weight: 900 !important; -webkit-text-fill-color: #000000 !important; background: #cbd5e1 !important;
    }

    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebarNav"] a {
        padding: 0.85rem 1.2rem !important; margin: 0.5rem 1rem !important; border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.03) !important; color: #cbd5e1 !important; font-weight: 600 !important;
        display: flex !important; align-items: center !important; gap: 12px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebarNav"] a:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    [data-testid="stSidebarNav"] a span { color: inherit !important; }

    /* FIXED HORIZONTAL SCROLLING DATA TABLE */
    .st-key-site_table_wrap {
        background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px;
        overflow: auto !important; padding: 0px 0 !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 2100px !important; align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important; padding: 6px 0 !important; flex-wrap: nowrap !important;
    }
    .st-key-site_table_wrap div[data-testid="stHorizontalBlock"]:hover { background: rgba(255,255,255,0.04); }
    .st-key-site_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; display: flex; align-items: center; justify-content: flex-start; border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-site_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-site_table_wrap .tbl-head {
        background: transparent; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px;
        color: #94a3b8; text-transform: uppercase; white-space: nowrap !important;
    }
    .st-key-site_table_wrap .tbl-cell {
        color: #e2e8f0; font-size: 0.86rem; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    .st-key-site_table_wrap .tbl-serial { color: #64748b; font-size: 0.85rem; font-weight: 800; }
    
    /* Action Buttons in Table */
    .st-key-site_table_wrap button {
        height: 32px !important; width: 100% !important; padding: 0 !important; min-height: 0 !important;
        border-radius: 6px !important; display: flex !important; align-items: center !important; justify-content: center !important;
        background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important; cursor: pointer !important; font-size: 0.95rem !important; max-width: 34px !important; margin: 0 auto !important;
    }
    .st-key-site_table_wrap button:hover { background: #3b82f6 !important; border-color: #60a5fa !important; transform: translateY(-2px) !important; }
    
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(2),
    .st-key-site_table_wrap div[data-testid="column"]:nth-child(3) { padding: 4px 4px !important; border-right: none !important; }
    
    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; text-transform: uppercase !important; font-size: 0.8rem !important; }
    </style>
""", unsafe_allow_html=True)

# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑
if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':
    st.error("🚫 **Access Restricted!**")
    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")
    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")
    st.stop()

# --- 3. SUPABASE CONNECTION ---
# FIX: Pehle yahan agar secrets nahi milti thi to ek PURANI hardcoded
# URL/key par silently fallback ho jaata tha — ye security risk tha aur
# galti se purane/wrong project se connect karwa sakta tha. Ab sirf
# st.secrets se hi connect karta hai, jaise baaki sabhi pages mein.
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

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_mrn_data():
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("mrn_data").select("*").eq("workspace", ws).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_project_ids():
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("site_data").select("*").eq("workspace", ws).limit(100000).execute()
        if res.data:
            pids = [str(x["Project ID"]).strip() for x in res.data if x.get("Project ID") and str(x.get("Project ID")).strip() != "" and str(x.get("Project ID")).strip().lower() != "nan"]
            return ["Select Project ID"] + list(dict.fromkeys(pids))
    except Exception as e:
        st.error(f"Error fetching Project IDs: {e}")
    return ["Select Project ID"]

@st.cache_data(ttl=60, show_spinner=False)
def fetch_project_details(proj_id):
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("site_data").select("*").eq("Project ID", proj_id).eq("workspace", ws).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return {}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_team_percentage(team_name):
    try:
        if team_name and team_name != "Select":
            tables_to_check = [
                ("team_master", "Team Name"),
                ("Team Master", "Team Name"),
                ("team_registration", "Team Name"),
                ("dropdown_master", "option_value")
            ]
            
            for t_name, c_name in tables_to_check:
                try:
                    res = supabase.table(t_name).select("*").eq(c_name, team_name).execute()
                    if res.data and len(res.data) > 0:
                        row = res.data[0]
                        for key, val in row.items():
                            if val is not None:
                                k_lower = str(key).lower()
                                if "percent" in k_lower or "rate" in k_lower or "%" in k_lower or "margin" in k_lower:
                                    clean_val = str(val).replace('%', '').strip()
                                    if clean_val.replace('.', '', 1).isdigit():
                                        fetched_pct = float(clean_val)
                                        if fetched_pct > 0:
                                            return fetched_pct
                except Exception:
                    continue
    except Exception:
        pass
    return 100.0

# ---> UNLIMITED PAGINATED DATA FETCHER (BYPASSES SUPABASE 1000 ROW LIMIT) <---
@st.cache_data(ttl=300, show_spinner=False)
def get_unlimited_po_working(ws):
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        try:
            res = supabase.table("po_working").select("*").eq("workspace", ws).range(offset, offset + limit - 1).execute()
            if not res.data:
                break
            all_rows.extend(res.data)
            if len(res.data) < limit:
                break
            offset += limit
        except Exception:
            break
    return all_rows


# ---> HELPER: find a column regardless of case / leading-trailing spaces <---
def _find_col(df, target_name):
    target_clean = target_name.strip().lower()
    for c in df.columns:
        if str(c).strip().lower() == target_clean:
            return c
    return None


# ---> HELPER: normalize any numeric-looking value into a clean digit string <---
# Handles "19030484279", "19030484279.0", "1.9030484279e+10", " 19030484279 ",
# "19,030,484,279" etc. so PO Number matching never fails on formatting.
def _clean_number(val):
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none"):
        return ""
    s_no_comma = s.replace(",", "")
    try:
        f = float(s_no_comma)
        if f.is_integer():
            return str(int(f))
        return s_no_comma
    except (ValueError, TypeError):
        # fallback: strip everything except digits
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits if digits else s.strip().lower()


def fetch_po_line_items(po_no, site_id, proj_id):
    try:
        ws = st.session_state.get('active_workspace', 'VISPL')
        
        # Fast Unlimited Fetcher
        all_data = get_unlimited_po_working(ws)
        if not all_data:
            st.warning("⚠️ 'po_working' table is empty for this workspace (or fetch failed).")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)

        # --- Locate columns case/space-insensitively (don't rely on exact spelling) ---
        po_col = _find_col(df, "PO Number")
        site_col = _find_col(df, "Site ID")
        proj_col = _find_col(df, "Project Name")
        item_col = _find_col(df, "Item Num")

        if not po_col:
            st.error(f"⚠️ Couldn't find a 'PO Number' column in po_working. "
                     f"Actual columns found: {list(df.columns)}")
            return pd.DataFrame()

        po_target = _clean_number(po_no)
        df['clean_po'] = df[po_col].apply(_clean_number)
        df_filtered = df[df['clean_po'] == po_target].copy()

        if df_filtered.empty:
            sample_vals = df['clean_po'].unique()[:15].tolist()
            st.warning(
                f"No rows matched PO Number '{po_no}' (normalized as '{po_target}') "
                f"in column '{po_col}'. Sample PO values present in table: {sample_vals}"
            )
            return pd.DataFrame()

        s_target = _clean_number(site_id) if str(site_id).strip() != "" else str(site_id).strip().lower()
        p_target = str(proj_id).strip().lower()

        mask = pd.Series([False] * len(df_filtered), index=df_filtered.index)
        filter_applied = False

        if site_col and str(site_id).strip() != "":
            df_filtered['clean_site'] = df_filtered[site_col].apply(_clean_number)
            mask = mask | (df_filtered['clean_site'] == s_target)
            filter_applied = True

        if proj_col and p_target != "":
            df_filtered['clean_proj'] = df_filtered[proj_col].astype(str).str.strip().str.lower()
            df_filtered['clean_proj'] = df_filtered['clean_proj'].str.replace(r'\.0$', '', regex=True)
            mask = mask | (df_filtered['clean_proj'] == p_target)
            filter_applied = True

        if filter_applied:
            final_df = df_filtered[mask].copy()
            if final_df.empty:
                # ULTIMATE FALLBACK: agar site/project match na ho toh saare PO items dikhao
                final_df = df_filtered.copy()
        else:
            final_df = df_filtered.copy()

        # --- Available Qty Logic ---
        # NOTE: PostgREST requires column names containing spaces to be wrapped
        # in double-quotes inside the select() string, otherwise it silently
        # strips the space and looks for a column like "ItemCode" (which fails).
        res_used = supabase.table("mrn_items").select('"Item Code","User Qty"').eq("PO Number", po_no).execute()
        used_map = {}
        if res_used.data:
            for r in res_used.data:
                ic = str(r.get("Item Code", "")).replace(".0", "").strip().lower()
                uq = int(r.get("User Qty", 0))
                used_map[ic] = used_map.get(ic, 0) + uq

        if item_col:
            final_df["Used Qty"] = final_df[item_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower().map(used_map).fillna(0)
        else:
            final_df["Used Qty"] = 0

        return final_df
    except Exception as e:
        st.error(f"❌ Error in fetch_po_line_items: {e}")
    return pd.DataFrame()


# ---> 🟢 NEW: pull a representative WCC Number / WCC Status for a set of
# already-fetched PO line-item dataframes (po_working now carries
# "wcc_qty" / "wcc_status" / "wcc_number" per line, pushed there by the
# WCC Upload automation). This is DISPLAY-ONLY — it is never written back
# to Supabase from the MRN screen. <---
def _derive_wcc_defaults(po_dfs_dict):
    wcc_number_default, wcc_status_default = "", ""
    for _po, df_po in po_dfs_dict.items():
        if df_po is None or df_po.empty:
            continue
        if "wcc_number" in df_po.columns and not wcc_number_default:
            vals = [str(v).strip() for v in df_po["wcc_number"].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
            if vals:
                wcc_number_default = vals[0]
        if "wcc_status" in df_po.columns and not wcc_status_default:
            vals = [str(v).strip() for v in df_po["wcc_status"].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
            if vals:
                wcc_status_default = vals[0]
        if wcc_number_default and wcc_status_default:
            break
    return wcc_number_default, wcc_status_default

# --- 4. DIALOG FUNCTIONS (ADD, EDIT, DELETE) ---

@st.dialog("🗑️ Confirm Deletion", width="small")
def delete_mrn_dialog(rid, mrn_no):
    st.warning(f"Delete MRN '{mrn_no}'? This will also remove its Pending Auto-Bill and Line Items. This cannot be undone.")
    st.markdown("<br>", unsafe_allow_html=True)
    wc1, wc2 = st.columns(2)
    with wc1:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
    with wc2:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                # Delete Header
                supabase.table("mrn_data").delete().eq("id", rid).execute()
                # Delete Items
                supabase.table("mrn_items").delete().eq("MRN Number", mrn_no).execute()
                # Delete Auto-Bill from Pending Team Billing (and Main just in case)
                supabase.table("pending_billing_invoices").delete().eq("invoice_no", mrn_no).execute()
                supabase.table("billing_invoices").delete().eq("invoice_no", mrn_no).execute()
                
                st.success("✅ MRN & Auto-Bill Deleted Successfully!")
                fetch_mrn_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Deleting Record: {e}")

@st.dialog("✏️ Edit MRN Details", width="large")
def edit_mrn_dialog(row_data):
    mrn_no = row_data.get("MRN Number", "")
    st.caption(f"Editing MRN: {mrn_no} (Amounts & Items are auto-linked with Billing and cannot be changed here)")
    
    st.markdown('<div class="modal-section-title">🏢 MRN HEADER</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("MRN NUMBER", value=mrn_no, disabled=True)
    with c2: st.text_input("PROJECT ID", value=row_data.get("Project ID", ""), disabled=True)
    with c3: st.text_input("SITE ID", value=row_data.get("Site ID", ""), disabled=True)
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("TEAM NAME", value=row_data.get("Team Name", ""), disabled=True)
    with c5: st.text_input("BASIC AMOUNT", value=f"₹ {row_data.get('Basic Amount', 0):,.2f}", disabled=True)
    with c6:
        st.text_input("TEAM RATE %", value=f"{row_data.get('Team Percent', 100)} %", disabled=True)

    c_date, c_desc = st.columns([1, 2])
    with c_date:
        def_date_str = row_data.get("Date", str(datetime.date.today().strftime("%d-%m-%Y")))
        try:
            def_date = pd.to_datetime(def_date_str, format="%d-%m-%Y").date()
        except:
            def_date = datetime.date.today()
        new_date = st.date_input("DATE", value=def_date, format="DD/MM/YYYY")
    with c_desc:
        st.text_area("DESCRIPTION / REMARKS", value=row_data.get("Description", ""), disabled=True, height=68)
        
    st.markdown('<div class="modal-section-title">📦 MRN LINE ITEMS (READ-ONLY)</div>', unsafe_allow_html=True)
    try:
        res = supabase.table("mrn_items").select("*").eq("MRN Number", mrn_no).execute()
        if res.data:
            items_df = pd.DataFrame(res.data)
            display_cols = []
            for col in ['PO Number', 'Item Code', 'Description', 'User Qty', 'Adjusted Price', 'Total']:
                if col in items_df.columns:
                    display_cols.append(col)
            st.dataframe(items_df[display_cols], hide_index=True, use_container_width=True)
        else:
            st.info("No line items found for this MRN.")
    except Exception:
        st.info("Could not fetch line items.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_save1, col_save2 = st.columns([8, 2])
    with col_save2:
        if st.button("💾 Update MRN", type="primary", use_container_width=True):
            new_date_str = new_date.strftime("%d-%m-%Y")
            new_bill_date_str = str(new_date) # YYYY-MM-DD for billing table
            try:
                # Update Date in MRN
                supabase.table("mrn_data").update({"Date": new_date_str}).eq("id", row_data["id"]).execute()
                # Update Date in Auto-Bill (Both Tables just in case)
                supabase.table("pending_billing_invoices").update({"date": new_bill_date_str}).eq("invoice_no", mrn_no).execute()
                supabase.table("billing_invoices").update({"date": new_bill_date_str}).eq("invoice_no", mrn_no).execute()
                
                st.success("✅ MRN Date Updated Successfully!")
                fetch_mrn_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Updating MRN: {e}")

@st.dialog("📦 Create New MRN / GRN", width="large")
def add_mrn_dialog():
    st.caption("Generate Material Receipt Note and adjust pricing based on Team Registration %")
    
    st.markdown('<div class="modal-section-title">🏢 PROJECT & SITE DETAILS</div>', unsafe_allow_html=True)
    
    proj_opts = fetch_project_ids()
    selected_proj = st.selectbox("SEARCH & SELECT PROJECT ID *", proj_opts)
    
    # Show Existing MRNs Box
    if selected_proj != "Select Project ID":
        try:
            # NOTE: same PostgREST quoting rule applies here - space-containing
            # column names must be double-quoted inside the select() string.
            ex_res = supabase.table("mrn_data").select('"MRN Number","Team Name"').eq("Project ID", selected_proj).execute()
            if ex_res.data:
                ex_text = " | ".join([f"{r['MRN Number']} ({r['Team Name']})" for r in ex_res.data])
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 12px; border-radius: 8px; border: 2px solid #10b981; margin-top: 5px; margin-bottom: 15px;'>
                    <span style='color: #0f172a; font-weight: 800; font-size: 0.95rem;'>📌 EXISTING MRNs FOUND FOR THIS PROJECT:</span><br>
                    <span style='color: #ef4444; font-weight: 700; font-size: 0.9rem;'>{ex_text}</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            pass
    
    site_name, site_id, cluster, rfai_status, site_status, team_name = "", "", "", "", "", ""
    po_list = []
    team_percent = 100.0
    
    if selected_proj != "Select Project ID":
        proj_data = fetch_project_details(selected_proj)
        site_name = proj_data.get("Site Name", "")
        site_id = proj_data.get("Site ID", "")
        cluster = proj_data.get("Cluster", "")
        rfai_status = proj_data.get("RFAI Status", "")
        site_status = proj_data.get("Site Status", "")
        team_name = proj_data.get("Team Name", "")
        
        # 1. POs from site_data table EXACT NAME
        po_str = str(proj_data.get("PO No.", ""))
        if po_str and po_str.lower() != "nan":
            po_list = [p.strip() for p in po_str.split(",") if p.strip()]
            
        # 2. Add POs dynamically from po_working EXACT NAMES (Unlimited Fast Fetch)
        ws_act = st.session_state.get('active_workspace', 'VISPL')
        try:
            all_po_data = get_unlimited_po_working(ws_act)
            p_target = str(selected_proj).strip().lower()
            s_target = str(site_id).strip().lower()
            
            for row in all_po_data:
                match = False
                
                # Check EXACT column "Project Name"
                pn_val = str(row.get("Project Name", "")).strip().lower()
                if pn_val.endswith(".0"): pn_val = pn_val[:-2]
                if pn_val == p_target: match = True
                
                # Check EXACT column "Site ID"
                sid_val = str(row.get("Site ID", "")).strip().lower()
                if sid_val.endswith(".0"): sid_val = sid_val[:-2]
                if s_target and sid_val == s_target: match = True
                
                if match:
                    pn = str(row.get("PO Number", "")).strip()
                    if pn.endswith(".0"): pn = pn[:-2]
                    if pn and pn.lower() != "nan" and pn not in po_list:
                        po_list.append(pn)
        except Exception as e:
            pass
        
        team_percent = fetch_team_percentage(team_name)

    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("SITE ID", value=site_id, disabled=True)
    with c2: st.text_input("SITE NAME", value=site_name, disabled=True)
    with c3: st.text_input("CLUSTER", value=cluster, disabled=True)
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("RFAI STATUS", value=rfai_status, disabled=True)
    with c5: st.text_input("SITE STATUS", value=site_status, disabled=True)
    with c6: st.text_input("TEAM NAME *", value=team_name, disabled=True)

    # ---> 🟢 NEW: PO SELECTION widget is declared with a stable key so we
    # can peek at "the PO(s) selected last run" via session_state BEFORE
    # this widget is physically rendered further down. That lets us show
    # WCC Number / WCC Status (derived from those POs' po_working rows)
    # right after the Team Rate row, exactly where it was asked to appear,
    # without changing the on-screen order of the dialog. <---
    PO_MULTISELECT_KEY = "mrn_po_multiselect"
    preview_selected_pos = [p for p in st.session_state.get(PO_MULTISELECT_KEY, []) if p in po_list]

    preview_po_dfs = {}
    for _po in preview_selected_pos:
        _df = fetch_po_line_items(_po, site_id, selected_proj)
        if not _df.empty:
            preview_po_dfs[_po] = _df

    default_wcc_number, default_wcc_status = _derive_wcc_defaults(preview_po_dfs)

    # ---> TEAM RATE % (auto-fetched from Team Master, editable per MRN) <---
    # Example: Team Master has 10% cut for "Pramodkumar Jaju" => box shows 90%.
    # User can change it here (e.g. to 85%) just for this MRN — Adjusted Price
    # below will then use that PO-price % instead of the auto-fetched one.
    fetched_team_percent = team_percent
    c_rate, c_desc = st.columns([1, 2])
    with c_rate:
        team_percent = st.number_input(
            "TEAM RATE % (Editable for this MRN)",
            min_value=0.0, max_value=100.0,
            value=float(team_percent),
            step=0.5,
            help="Auto-fetched from Team Master. Change it here to override the rate only for this MRN — Adjusted Price will use this %."
        )
        st.caption(
            f"📌 Auto Rate: **{fetched_team_percent:g}%** "
            f"(Team Cut: **{100 - fetched_team_percent:g}%**) → "
            f"Currently Applying: **{team_percent:g}%** of PO Price"
        )
    with c_desc:
        mrn_description = st.text_area(
            "DESCRIPTION / REMARKS",
            placeholder="Enter any description / remarks for this MRN...",
            height=68
        )

    # ---> 🟢 NEW: WCC NUMBER & WCC STATUS — display/reference only.
    # Auto-filled from the selected PO's po_working rows (pushed there by
    # the WCC Upload automation) but editable here for convenience. NOT
    # included in the MRN save payload — nothing from these two fields is
    # written to Supabase. <---
    c_wcc1, c_wcc2 = st.columns(2)
    with c_wcc1:
        wcc_number_display = st.text_input(
            "WCC NUMBER (reference only)",
            value=default_wcc_number,
            help="Auto-filled from the selected PO's WCC data. Editable here for reference only — not saved with the MRN."
        )
    with c_wcc2:
        wcc_status_display = st.text_input(
            "WCC STATUS (reference only)",
            value=default_wcc_status,
            help="Auto-filled from the selected PO's WCC data. Editable here for reference only — not saved with the MRN."
        )
    st.caption("ℹ️ WCC Number / WCC Status shown above are for reference only and are **not** saved when this MRN is generated.")

    st.markdown('<div class="modal-section-title">📑 PO SELECTION & LINE ITEMS</div>', unsafe_allow_html=True)
    
    if not po_list and selected_proj != "Select Project ID":
        st.warning("⚠️ No POs found for this Project ID in Site Data.")
        
    selected_pos = st.multiselect("SEARCH & SELECT PO(s)", po_list, placeholder="Choose one or multiple POs", key=PO_MULTISELECT_KEY)
    
    grand_basic_total = 0.0
    all_po_dfs = {}
    
    for po in selected_pos:
        st.markdown(f"<p style='color:#3b82f6; font-weight:700; margin-top:15px;'>🛒 Processing PO: {po}</p>", unsafe_allow_html=True)
        
        # Reuse the already-fetched dataframe from the preview pass above
        # when available, to avoid hitting Supabase twice for the same PO.
        df_po = preview_po_dfs.get(po)
        if df_po is None:
            df_po = fetch_po_line_items(po, site_id, selected_proj)
        
        if df_po.empty:
            st.info(f"No line items found in PO Working for PO: {po}")
            continue
            
        # Using exact column names!
        df_display = pd.DataFrame()
        df_display["PO Line No"] = df_po.get("Line Number", [""]*len(df_po))
        df_display["Item Code"] = df_po.get("Item Num", [""]*len(df_po))
        df_display["Item Description"] = df_po.get("Description", [""]*len(df_po))
        
        raw_po_qty = pd.to_numeric(df_po.get("PO Qty", [0]*len(df_po)), errors='coerce').fillna(0)
        raw_used_qty = pd.to_numeric(df_po.get("Used Qty", [0]*len(df_po)), errors='coerce').fillna(0)
        
        df_display["PO Qty"] = raw_po_qty

        # ---> 🟢 NEW: WCC Qty, shown right after PO Qty (display only,
        # sourced from po_working.wcc_qty for this same line). <---
        raw_wcc_qty = pd.to_numeric(df_po.get("wcc_qty", [0]*len(df_po)), errors='coerce').fillna(0)
        df_display["WCC Qty"] = raw_wcc_qty

        df_display["Available Qty"] = raw_po_qty - raw_used_qty
        df_display["User Qty"] = 0
        
        original_price = pd.to_numeric(df_po.get("Price", [0]*len(df_po)), errors='coerce').fillna(0)
        df_display["Adjusted Price"] = original_price * (team_percent / 100.0)
        df_display["Line Total"] = 0.0
        
        editor_key = f"editor_mrn_{po}"
        
        edited_df = st.data_editor(
            df_display,
            key=editor_key,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PO Line No": st.column_config.TextColumn("LINE NO", disabled=True),
                "Item Code": st.column_config.TextColumn("ITEM CODE", disabled=True),
                "Item Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
                "PO Qty": st.column_config.NumberColumn("PO QTY", disabled=True),
                "WCC Qty": st.column_config.NumberColumn("WCC QTY", disabled=True),
                "Available Qty": st.column_config.NumberColumn("AVAILABLE QTY", disabled=True),
                "User Qty": st.column_config.NumberColumn("USER QTY", min_value=0, required=True),
                "Adjusted Price": st.column_config.NumberColumn(f"PRICE ({team_percent}%)", disabled=True, format="₹ %.2f"),
                "Line Total": st.column_config.NumberColumn("TOTAL", disabled=True, format="₹ %.2f"),
            }
        )
        
        for idx, r in edited_df.iterrows():
            u_qty = pd.to_numeric(r["User Qty"], errors='coerce')
            u_qty = 0 if pd.isna(u_qty) else int(u_qty)
            rate = float(r["Adjusted Price"])
            tot = u_qty * rate
            edited_df.at[idx, "Line Total"] = tot
            grand_basic_total += tot
            
        all_po_dfs[po] = edited_df

    st.markdown('<div class="modal-section-title">💳 BILLING SUMMARY</div>', unsafe_allow_html=True)
    
    final_amount = grand_basic_total
    
    c_b1, c_b3 = st.columns([6, 4])
    with c_b1:
        st.markdown(f"<h4 style='color:#94a3b8; font-size:1.1rem;'>Basic Amount:<br><span style='color:#fff;'>₹ {grand_basic_total:,.2f}</span></h4>", unsafe_allow_html=True)
    with c_b3:
        st.markdown(f"<h3 style='color:#3b82f6; font-size:1.4rem;'>Grand Total:<br>₹ {final_amount:,.2f}</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_save1, col_save2 = st.columns([7, 3])
    with col_save2:
        if st.button("💾 Generate MRN (Send for Approval)", type="primary", use_container_width=True):
            if selected_proj == "Select Project ID":
                st.error("⚠️ Please select a Project ID.")
                return
            
            if not team_name or str(team_name).strip() in ["", "nan", "None", "Select"]:
                st.error("⚠️ Team Name is required! Please assign a team to this project in Site Data before generating MRN.")
                return
                
            if not selected_pos:
                st.error("⚠️ Please select at least one PO.")
                return
            if grand_basic_total <= 0:
                st.error("⚠️ User Qty must be greater than 0 to generate MRN.")
                return
            
            # Strict QTY Validation
            for po, edf in all_po_dfs.items():
                for idx, r in edf.iterrows():
                    u_qty = pd.to_numeric(r["User Qty"], errors='coerce')
                    a_qty = pd.to_numeric(r["Available Qty"], errors='coerce')
                    u_qty = 0 if pd.isna(u_qty) else int(u_qty)
                    a_qty = 0 if pd.isna(a_qty) else int(a_qty)
                    if u_qty > a_qty:
                        st.error(f"❌ Error in PO {po}: User Qty ({u_qty}) cannot be greater than Available Qty ({a_qty}) for Item '{r['Item Code']}'.")
                        return

            while True:
                new_mrn_no = f"MRN-{random.randint(100000, 999999)}"
                try:
                    check_res = supabase.table("mrn_data").select('"MRN Number"').eq("MRN Number", new_mrn_no).execute()
                    if not check_res.data:
                        break 
                except Exception:
                    break 
            
            # 🟢 NOTE: wcc_number_display / wcc_status_display are
            # intentionally NOT included below — WCC Number/Status are
            # display-only on this screen and are never written to Supabase
            # from the MRN flow (they already live on po_working, pushed
            # there by the WCC Upload automation).
            header_data = {
                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                "MRN Number": new_mrn_no,
                "Team Name": team_name,
                "Project ID": selected_proj,
                "Site ID": site_id,
                "Site Name": site_name,
                "Cluster": cluster,
                "Basic Amount": grand_basic_total,
                "Total Amount": final_amount,
                "Team Percent": float(team_percent),
                "Description": mrn_description.strip() if mrn_description else "",
                "Date": datetime.date.today().strftime("%d-%m-%Y")
            }
            
            try:
                # Save Header
                supabase.table("mrn_data").insert(header_data).execute()
                
                # Save Items
                items_to_insert = []
                for po, d_df in all_po_dfs.items():
                    for _, row in d_df.iterrows():
                        u_qty = pd.to_numeric(row["User Qty"], errors='coerce')
                        if pd.notna(u_qty) and u_qty > 0:
                            items_to_insert.append({
                                "workspace": st.session_state.get('active_workspace', 'VISPL'),
                                "MRN Number": new_mrn_no,
                                "PO Number": po,
                                "Item Code": str(row["Item Code"]),
                                "Description": str(row["Item Description"]),
                                "User Qty": int(u_qty),
                                "Adjusted Price": float(row["Adjusted Price"]),
                                "Total": float(row["Line Total"])
                            })
                if items_to_insert:
                    try:
                        supabase.table("mrn_items").insert(items_to_insert).execute()
                    except Exception as e:
                        st.warning(f"⚠️ MRN header saved, but line items failed to save: {e}")
                
                # SEND TO PENDING_BILLING_INVOICES FOR APPROVAL
                billing_payload = {
                    "workspace": st.session_state.get('active_workspace', 'VISPL'),
                    "invoice_type": "Team",
                    "team_name": team_name,
                    "amount": float(grand_basic_total),
                    "basic_amount": float(grand_basic_total),
                    "gst_amount": 0.0,
                    "date": str(datetime.date.today()), 
                    "project_id": selected_proj,
                    "site_id": site_id,
                    "site_name": site_name,
                    "invoice_no": new_mrn_no,
                    "vendor_name": "",
                    "remark": "Data Taken by MRN",
                    "cluster": cluster
                }
                try:
                    supabase.table("pending_billing_invoices").insert(billing_payload).execute()
                    st.success(f"✅ MRN Generated Successfully! ID: {new_mrn_no} (Sent for Approval in Team Billing)")
                except Exception as e:
                    st.warning(
                        f"⚠️ MRN '{new_mrn_no}' saved, but sending it to Pending Team Billing FAILED: {e}\n\n"
                        f"Payload attempted: {billing_payload}"
                    )
                st.session_state.mrn_current_page = 1
                fetch_mrn_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Generating MRN: {e}")

# --- 5. EXPORT DIALOG ---
@st.dialog("📥 Export MRN Data", width="large")
def export_dialog(df_export):
    st.caption("Download your MRN/GRN records as an Excel file.")
    export_df = df_export.copy()
    if "id" in export_df.columns:
        export_df = export_df.drop(columns=["id"])
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='MRN Data')
        
    st.download_button(
        label="📊 Download Excel File",
        data=buffer.getvalue(),
        file_name="MRN_GRN_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- TOP SINGLE WORKSPACE BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            🏢 ACTIVE WORKSPACE : {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 6. TOP ACTION BAR ---
col_title, col_ref, col_add, col_export = st.columns([4, 1, 2, 2])
with col_title:
    st.markdown("<h2 style='margin:0; color:white;'>📦 MRN / GRN Desk</h2>", unsafe_allow_html=True)
with col_ref:
    if st.button("🔄 Refresh", use_container_width=True):
        get_unlimited_po_working.clear()
        fetch_mrn_data.clear()
        fetch_project_ids.clear()
        st.rerun() 
with col_add:
    if st.button("➕ Add New MRN", type="primary", use_container_width=True):
        add_mrn_dialog() 
with col_export:
    if st.button("📥 Export Data", use_container_width=True):
        st.session_state.mrn_action = "export"

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. FETCH & PREPARE MRN DATA ---
df_mrn = fetch_mrn_data()

columns_list = [
    "id", "MRN Number", "Team Name", "Project ID", "Site ID", 
    "Site Name", "Cluster", "Basic Amount", "Total Amount", "Team Percent", "Description", "Date"
]

if not df_mrn.empty:
    if 'id' in df_mrn.columns:
        df_mrn['id_num'] = pd.to_numeric(df_mrn['id'], errors='coerce')
        df_mrn = df_mrn.sort_values(by='id_num', ascending=False).drop(columns=['id_num']).reset_index(drop=True)
    for col in columns_list:
        if col not in df_mrn.columns:
            df_mrn[col] = ""
else:
    df_mrn = pd.DataFrame(columns=columns_list)

# --- EXPORT LOGIC TRIGGER ---
if st.session_state.get('mrn_action') == "export":
    export_dialog(df_mrn)
    st.session_state.mrn_action = "" 

# --- 8. LAVISH UNIVERSAL SEARCH BOX ---
col_table_title, col_search = st.columns([7, 3])
with col_table_title:
    st.markdown("##### 🗄️ Generated MRN Records")
with col_search:
    search_query = st.text_input("Search", placeholder="🔍 Search MRN records...", label_visibility="collapsed")

if search_query and not df_mrn.empty:
    mask = df_mrn.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df_mrn = df_mrn[mask]

# --- 9. PAGINATION LOGIC (10 lines per page) ---
rows_per_page = 10
total_rows = len(df_mrn)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.mrn_current_page > total_pages:
    st.session_state.mrn_current_page = total_pages
elif st.session_state.mrn_current_page < 1:
    st.session_state.mrn_current_page = 1

start_idx = (st.session_state.mrn_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page

df_page = df_mrn.iloc[start_idx:end_idx].copy()

# --- 10. MRN DATA TABLE ---
# 14 Columns total mapping
COL_RATIOS = [0.3, 0.4, 0.4, 1.2, 1.5, 1.2, 1.2, 1.5, 1.0, 1.0, 1.0, 0.8, 1.8, 1.0]
COL_LABELS = ["#", "✏️", "🗑️", "MRN NUMBER", "TEAM NAME", "PROJECT ID", "SITE ID", "SITE NAME", "CLUSTER", "BASIC", "TOTAL", "RATE %", "DESCRIPTION", "DATE"]

with st.container(key="site_table_wrap", height=560):
    if df_page.empty:
        st.info("No MRN records found. Click '+ Add New MRN' to create one.")
    else:
        # HEADER ROW
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label if label else '&nbsp;'}</div>", unsafe_allow_html=True)

        # DATA ROWS
        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            serial_no = start_idx + page_pos + 1
            rid = row_dict.get("id")
            mrn_no = row_dict.get('MRN Number', '')

            rcols = st.columns(COL_RATIOS)
            
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            
            # EDIT BUTTON
            with rcols[1]:
                if st.button("✏️", key=f"edit_{rid}", help="Edit MRN Date & View Details", use_container_width=True):
                    edit_mrn_dialog(row_dict)
                    
            # DELETE BUTTON
            with rcols[2]:
                if st.button("🗑️", key=f"del_{rid}", help="Delete MRN & Auto-Bill", use_container_width=True):
                    delete_mrn_dialog(rid, mrn_no)
                    
            rcols[3].markdown(f"<div class='tbl-cell' style='color:#3b82f6; font-weight:bold;'>{mrn_no or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{row_dict.get('Team Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Project ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[7].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[8].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            
            # Formatting financial data
            basic = pd.to_numeric(row_dict.get('Basic Amount', 0), errors='coerce')
            tot = pd.to_numeric(row_dict.get('Total Amount', 0), errors='coerce')
            
            rcols[9].markdown(f"<div class='tbl-cell'>₹ {basic:,.2f}</div>", unsafe_allow_html=True)
            rcols[10].markdown(f"<div class='tbl-cell' style='color:#10b981; font-weight:bold;'>₹ {tot:,.2f}</div>", unsafe_allow_html=True)

            team_pct = pd.to_numeric(row_dict.get('Team Percent', ''), errors='coerce')
            team_pct_display = f"{team_pct:g}%" if pd.notna(team_pct) else "-"
            rcols[11].markdown(f"<div class='tbl-cell' style='color:#f59e0b; font-weight:bold;'>{team_pct_display}</div>", unsafe_allow_html=True)
            rcols[12].markdown(f"<div class='tbl-cell' title='{row_dict.get('Description','') or ''}'>{row_dict.get('Description','') or '-'}</div>", unsafe_allow_html=True)
            rcols[13].markdown(f"<div class='tbl-cell'>{row_dict.get('Date','') or '-'}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 11. NEXT / PREVIOUS PAGINATION CONTROLS ---
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.mrn_current_page == 1)):
        st.session_state.mrn_current_page -= 1
        st.rerun()

with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.mrn_current_page} of {total_pages} (Total Records: {total_rows})</div>", unsafe_allow_html=True)

with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.mrn_current_page == total_pages)):
        st.session_state.mrn_current_page += 1
        st.rerun()
