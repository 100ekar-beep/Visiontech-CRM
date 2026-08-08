import streamlit as st

import pandas as pd

import datetime

import io

import json

from supabase import create_client, Client



# --- 1. PAGE CONFIGURATION ---

st.set_page_config(page_title="Quotation List", page_icon="📄", layout="wide")



# --- 2. LAVISH CUSTOM CSS (Matches Screenshots & Sidebar) ---

st.markdown("""

    <style>

    /* Dark Premium Theme & Backgrounds */

    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }

    

    /* Primary Action Buttons */

    button[data-testid="baseButton-primary"] {

        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;

        color: white !important;

        border: none !important;

        border-radius: 8px !important;

        font-weight: 800 !important;

        padding: 0.6rem 1.2rem !important;

        transition: all 0.3s ease !important;

        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;

    }

    button[data-testid="baseButton-secondary"] {

        background: #10b981 !important;

        color: white !important;

        border: none !important;

        border-radius: 8px !important;

        font-weight: 800 !important;

        padding: 0.6rem 1.2rem !important;

        transition: all 0.3s ease !important;

        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4) !important;

    }

    button[data-testid="baseButton-primary"]:hover, 

    button[data-testid="baseButton-secondary"]:hover {

        transform: translateY(-2px) !important;

        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;

    }



    /* Dialog/Popup Glassmorphism for Quotation View */

    div[data-testid="stDialog"] > div {

        background: #ffffff;

        border: 1px solid #cbd5e1;

        border-radius: 16px;

        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

    }

    div[data-testid="stDialog"] h1, 

    div[data-testid="stDialog"] h2, 

    div[data-testid="stDialog"] h3 {

        color: #1e293b !important;

        font-weight: 800 !important;

        letter-spacing: 0.5px;

    }

    div[data-testid="stDialog"] p {

        color: #475569 !important; 

    }

    div[data-testid="stDialog"] button[kind="icon"] svg {

        fill: #64748b !important; 

    }



    /* Modal Section Title */

    .modal-section-title {

        color: #3b82f6;

        font-size: 1rem;

        font-weight: 800;

        letter-spacing: 0.5px;

        margin-bottom: 15px;

        border-bottom: 2px solid #e2e8f0;

        padding-bottom: 8px;

        display: flex;

        align-items: center;

        gap: 8px;

    }

    

    /* Input Labels */

    label p, label[data-testid="stWidgetLabel"] p {

        color: #64748b !important;

        font-weight: 700 !important;

        font-size: 0.85rem !important;

        letter-spacing: 0.5px;

        text-transform: uppercase;

    }



    input:disabled, div[data-baseweb="input"] input:disabled, textarea:disabled {

        color: #000000 !important;

        -webkit-text-fill-color: #000000 !important;

        font-weight: 900 !important;

        opacity: 1 !important;

    }



    /* Data Editor Table Header */

    [data-testid="stDataFrame"] th {

        background-color: #6366f1 !important;

        color: white !important;

        font-weight: 700 !important;

        text-transform: uppercase !important;

        font-size: 0.8rem !important;

    }



    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */

    [data-testid="stSidebar"] {

        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);

        border-right: 1px solid rgba(255, 255, 255, 0.05);

    }

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

    [data-testid="stSidebarNav"] a:hover {

        background: rgba(255, 255, 255, 0.1) !important;

        transform: translateX(4px) !important;

        border-color: rgba(255, 255, 255, 0.2) !important;

        color: #ffffff !important;

    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {

        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;

        color: #ffffff !important;

        border-color: transparent !important;

        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;

    }

    [data-testid="stSidebarNav"] a span {

        color: inherit !important;

    }

    </style>

""", unsafe_allow_html=True)



# 🛑 --- STRICT SECURITY GATE FOR VISPL / BHAGYASHREE ONLY --- 🛑

if st.session_state.get('active_workspace', 'VISPL') == 'RAJKUMAR KALYA':

    st.error("🚫 **Access Restricted!**")

    st.warning("Ye module exclusively **VISPL** aur **BHAGYASHREE** workspaces ke liye available hai.")

    st.info("💡 Kripya 'Home' page (app.py) par ja kar apna Master Workspace change karein.")

    st.stop()



# --- TOP SINGLE WORKSPACE BANNER ---

active_ws_display = st.session_state.get('active_workspace', 'VISPL')

st.markdown(f"""

    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">

        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">

            🏢 ACTIVE WORKSPACE : {active_ws_display}

        </h1>

    </div>

""", unsafe_allow_html=True)



# --- 3. SUPABASE CONNECTION ---

SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"        

SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   



@st.cache_resource

def init_connection():

    return create_client(SUPABASE_URL, SUPABASE_KEY)



supabase: Client = init_connection()



# --- 4. DATA FETCHING FUNCTIONS ---

@st.cache_data(ttl=60)

def fetch_quotation_projects(workspace_name):

    try:

        res = supabase.table("site_data").select("*").eq("workspace", workspace_name).execute()

        if res.data:

            df = pd.DataFrame(res.data)

            if "Operator" in df.columns:

                mask = df["Operator"].astype(str).str.contains("uotat", case=False, na=False)

                return df[mask]

            return df

    except Exception:

        pass

    return pd.DataFrame(columns=["Project ID", "Site ID", "Site Name", "Cluster", "KM", "Project Name"])



@st.cache_data(ttl=60)

def fetch_item_master():

    tables_to_try = ["Item Code", "item_master", "items", "Item_Code"]

    for t in tables_to_try:

        try:

            res = supabase.table(t).select("*").limit(10000).execute()

            if res.data and len(res.data) > 0:

                df = pd.DataFrame(res.data)

                col_map = {}

                for c in df.columns:

                    cl = str(c).strip().lower()

                    if cl in ['item code', 'item_code', 'itemcode', 'code', 'material item']: col_map[c] = 'Item Code'

                    if cl in ['description', 'desc', 'item description', 'item_description']: col_map[c] = 'Description'

                    if cl in ['price', 'rate', 'amount', 'unit price']: col_map[c] = 'Price'

                df = df.rename(columns=col_map)

                if 'Item Code' in df.columns:

                    return df

        except Exception:

            continue

    return pd.DataFrame(columns=["Item Code", "Description", "Price"])



@st.cache_data(ttl=30)

def fetch_quotation_templates():

    try:

        res = supabase.table("quotation_templates").select("*").execute()

        if res.data:

            return res.data

    except:

        pass

    return []



# Load Master Data First so cluster mapping is ready

df_projects = fetch_quotation_projects(st.session_state.get('active_workspace', 'VISPL'))

project_list = df_projects["Project ID"].dropna().unique().tolist() if not df_projects.empty else []



def fetch_quotations():

    try:

        active_ws = st.session_state.get('active_workspace', 'VISPL')

        

        # STRICT WORKSPACE FILTERING (No cross-contamination)

        res = supabase.table("quotations").select("*").eq("workspace", active_ws).execute()

            

        if res.data:

            df = pd.DataFrame(res.data)

            # --- Robust Cluster mapping from site_data using Project ID ---

            if not df.empty and "Project ID" in df.columns and not df_projects.empty:

                proj_cluster_map = dict(zip(df_projects["Project ID"], df_projects["Cluster"]))

                df["Cluster"] = df["Project ID"].map(proj_cluster_map).fillna("")

            else:

                df["Cluster"] = ""

            return df

    except Exception:

        pass

    return pd.DataFrame(columns=["id", "Quotation Name", "Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project Name", "Quotation Amount", "Status"])



df_items = fetch_item_master()

if not df_items.empty:

    df_items["Description"] = df_items["Description"].fillna("")

    df_items["Display"] = df_items["Item Code"].astype(str) + " | " + df_items["Description"].astype(str)

    

    item_display_list = df_items["Display"].tolist()

    item_code_list = df_items["Item Code"].astype(str).tolist()

    combined_item_options = item_display_list + item_code_list 

    

    display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))

    display_to_price = dict(zip(df_items["Display"], df_items["Price"]))

else:

    combined_item_options = []

    display_to_desc = {}

    display_to_price = {}



templates_data = fetch_quotation_templates()

template_names = [t["Template Name"] for t in templates_data]



# --- 5. INITIALIZE SESSION STATE ---

st.session_state.quotations_df = fetch_quotations()



# --- 6. DIALOG FOR ADD/VIEW QUOTATION ---

@st.dialog("📄 Update Quotation", width="large")

def quotation_dialog(quotation_data=None):

    st.caption("Details and items for project estimation")

    

    is_new = quotation_data is None

    

    quo_id = None

    default_name = f"Quotation {len(st.session_state.quotations_df) + 100}" if is_new else quotation_data.get("Quotation Name", "")

    default_date = datetime.date.today() if is_new else pd.to_datetime(quotation_data.get("Date", datetime.date.today())).date()

    

    # --- MODIFIED LOGIC: Default blank for new, filter out already used Project IDs ---

    default_proj = quotation_data.get("Project ID", "") if quotation_data else ""

    

    used_projs = []

    if not st.session_state.quotations_df.empty and "Project ID" in st.session_state.quotations_df.columns:

        used_projs = st.session_state.quotations_df["Project ID"].dropna().unique().tolist()

        

    available_opts = [p for p in project_list if p not in used_projs]

    if not is_new and default_proj and default_proj not in available_opts:

        available_opts.append(default_proj)

        

    dynamic_options = [""] + available_opts

    

    # Top Section

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        quo_name = st.text_input("QUOTATION *", value=default_name)

    with col2:

        quo_date = st.date_input("QUOTATION DATE *", value=default_date)

    with col3:

        sel_idx = dynamic_options.index(default_proj) if default_proj in dynamic_options else 0

        sel_proj = st.selectbox("PROJECT ID *", options=dynamic_options, index=sel_idx)

    

    auto_site_id = ""

    auto_site_name = ""

    auto_cluster = ""

    auto_km = "" 

    auto_proj_name = ""

    if sel_proj:

        proj_row = df_projects[df_projects["Project ID"] == sel_proj]

        if not proj_row.empty:

            auto_site_id = str(proj_row.iloc[0].get("Site ID", ""))

            auto_site_name = str(proj_row.iloc[0].get("Site Name", ""))

            auto_cluster = str(proj_row.iloc[0].get("Cluster", ""))

            

            if auto_site_id:

                try:

                    res_exc = supabase.table("Excalation Matrix").select("KM").eq("Site ID", auto_site_id).execute()

                    if res_exc.data and len(res_exc.data) > 0:

                        km_val = res_exc.data[0].get("KM", "")

                        auto_km = "" if pd.isna(km_val) else str(km_val)

                except Exception:

                    pass

            auto_proj_name = str(proj_row.iloc[0].get("Project Name", ""))

            

    with col4:

        st.text_input("SITE ID *", value=auto_site_id, disabled=True)

        

    col5, col6, col_km, col7, col8 = st.columns(5)

    with col5:

        st.text_input("SITE NAME", value=auto_site_name, disabled=True)

    with col6:

        st.text_input("CLUSTER", value=auto_cluster, disabled=True)

    with col_km:

        st.text_input("KM", value=auto_km, disabled=True) 

    with col7:

        st.text_input("PROJECT NAME", value=auto_proj_name, disabled=True)

    with col8:

        selected_template = st.selectbox("QUOTATION TEMPLATE", options=["-- Select Template --"] + template_names)

        

    st.markdown("<br>", unsafe_allow_html=True)

    col_list_title, col_add_btn = st.columns([8, 2])

    with col_list_title:

        st.markdown('<div class="modal-section-title" style="margin-top:0;">📚 Listing Premium Items <span style="font-size:0.8rem; color:#64748b; font-weight:500;">(Use plus (+) icon below to add lines)</span></div>', unsafe_allow_html=True)

    

    editor_key = f"quo_items_{quo_name}_{sel_proj}"

    widget_key = f"widget_{editor_key}"

    

    saved_proj = quotation_data.get("Project ID", "") if quotation_data else ""

    

    if editor_key not in st.session_state:

        if is_new or sel_proj != saved_proj:

            st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])

        else:

            try:

                res_items = supabase.table("quotation_items").select("*").eq("Quotation Name", quo_name).execute()

                if res_items.data and len(res_items.data) > 0:

                    temp_df = pd.DataFrame(res_items.data)[["Item Code", "Description", "Qty", "Price", "Total"]]

                    st.session_state[editor_key] = temp_df

                else:

                    st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])

            except:

                st.session_state[editor_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price", "Total"])



    if selected_template and selected_template != "-- Select Template --":

        for t in templates_data:

            if t["Template Name"] == selected_template:

                try:

                    raw_items = json.loads(t["Items Data"]) if isinstance(t["Items Data"], str) else t["Items Data"]

                    loaded_rows = []

                    for ri in raw_items:

                        qty_val = int(ri.get("Qty", 1))

                        price_val = int(ri.get("Price", 0))

                        loaded_rows.append({

                            "Item Code": ri.get("Item Code", ""),

                            "Description": ri.get("Description", ""),

                            "Qty": qty_val,

                            "Price": price_val,

                            "Total": price_val * qty_val

                        })

                    if loaded_rows:

                        st.session_state[editor_key] = pd.DataFrame(loaded_rows)

                except:

                    pass



    with col_add_btn:

        if st.button("➕ Add New Row", use_container_width=True):

            new_item = pd.DataFrame([{"Item Code": None, "Description": "", "Qty": 1, "Price": 0, "Total": 0}])

            st.session_state[editor_key] = pd.concat([st.session_state[editor_key], new_item], ignore_index=True)



    if widget_key in st.session_state:

        w_state = st.session_state[widget_key]

        edits = w_state.get("edited_rows", {})

        adds = w_state.get("added_rows", [])

        dels = w_state.get("deleted_rows", [])

        

        if edits or adds or dels:

            curr_df = st.session_state[editor_key].copy()

            if dels: curr_df = curr_df.drop(dels).reset_index(drop=True)

            if edits:

                for str_idx, changes in edits.items():

                    idx = int(str_idx)

                    if idx < len(curr_df):

                        for col, val in changes.items():

                            curr_df.at[idx, col] = val

                        if "Item Code" in changes:

                            disp = str(changes["Item Code"])

                            if " | " in disp:

                                code_only = disp.split(" | ")[0].strip()

                                curr_df.at[idx, "Item Code"] = code_only

                                if disp in display_to_desc:

                                    curr_df.at[idx, "Description"] = display_to_desc[disp]

                                    curr_df.at[idx, "Price"] = display_to_price[disp]

                            else:

                                match = df_items[df_items["Item Code"] == disp]

                                if not match.empty:

                                    curr_df.at[idx, "Description"] = match.iloc[0]["Description"]

                                    curr_df.at[idx, "Price"] = match.iloc[0]["Price"]

                        qty = pd.to_numeric(curr_df.at[idx, "Qty"], errors='coerce')

                        price = pd.to_numeric(curr_df.at[idx, "Price"], errors='coerce')

                        curr_df.at[idx, "Total"] = (0 if pd.isna(qty) else int(qty)) * (0 if pd.isna(price) else int(price))

            if adds:

                for row in adds:

                    new_row = {"Item Code": row.get("Item Code"), "Description": "", "Qty": 1, "Price": 0, "Total": 0}

                    if "Item Code" in row and pd.notna(row["Item Code"]):

                        disp = str(row["Item Code"])

                        if " | " in disp:

                            code_only = disp.split(" | ")[0].strip()

                            new_row["Item Code"] = code_only

                            if disp in display_to_desc:

                                new_row["Description"] = display_to_desc[disp]

                                new_row["Price"] = display_to_price[disp]

                                new_row["Total"] = display_to_price[disp] * 1

                    curr_df = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)

            st.session_state[editor_key] = curr_df

            del st.session_state[widget_key]



    edited_items_df = st.data_editor(

        st.session_state[editor_key],

        key=widget_key,

        num_rows="dynamic",

        use_container_width=True,

        hide_index=True,

        height=300,

        column_config={

            "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=combined_item_options, required=True, width="medium"),

            "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),

            "Qty": st.column_config.NumberColumn("QTY", min_value=0, default=1, format="%d", alignment="center", width="small"),

            "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d", alignment="center", width="small"),

            "Total": st.column_config.NumberColumn("TOTAL", disabled=True, format="₹ %d", alignment="center", width="medium")

        }

    )



    grand_total = edited_items_df["Total"].sum() if not edited_items_df.empty else 0

    

    st.markdown(f"<h4 style='text-align: right; color: #4f46e5;'>Grand Total: ₹ {grand_total:,}</h4>", unsafe_allow_html=True)

    

    st.markdown("<br>", unsafe_allow_html=True)

    col_dl, _, col_save = st.columns([2, 6, 2])

    

    with col_dl:

        st.button("📥 Download PDF", use_container_width=True)

        

    with col_save:

        if st.button("💾 Save Quotation", type="primary", use_container_width=True):

            if not sel_proj:

                st.error("⚠️ Project ID is required!")

                return

                

            header_data = {

                "workspace": st.session_state.get('active_workspace', 'VISPL'),

                "Quotation Name": quo_name,

                "Date": str(quo_date),

                "Project ID": sel_proj,

                "Site ID": auto_site_id,

                "Site Name": auto_site_name,

                "Project Name": auto_proj_name,

                "Quotation Amount": int(grand_total),

                "Status": "Manual"

            }

            

            try:

                if not is_new and "id" in quotation_data and pd.notna(quotation_data["id"]):

                    supabase.table("quotations").update(header_data).eq("id", quotation_data["id"]).execute()

                else:

                    supabase.table("quotations").insert(header_data).execute()

                

                supabase.table("quotation_items").delete().eq("Quotation Name", quo_name).execute()

                

                if not edited_items_df.empty:

                    items_to_insert = []

                    for _, r in edited_items_df.iterrows():

                        if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip() != "":

                            clean_code = str(r["Item Code"]).split(" | ")[0].strip()

                            items_to_insert.append({

                                "workspace": st.session_state.get('active_workspace', 'VISPL'),

                                "Quotation Name": quo_name,

                                "Item Code": clean_code,

                                "Description": str(r["Description"]),

                                "Qty": int(r["Qty"]) if pd.notna(r["Qty"]) else 0,

                                "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0,

                                "Total": int(r["Total"]) if pd.notna(r["Total"]) else 0

                            })

                    if items_to_insert:

                        supabase.table("quotation_items").insert(items_to_insert).execute()

                

                st.session_state.quotations_df = fetch_quotations()

                st.success("✅ Quotation Saved Successfully!")

                st.rerun()

                

            except Exception as e:

                st.error(f"Database Error: {e}")



# --- 7. TOP HEADER & FILTERS ---

col_head1, col_head2, col_head3, col_head4 = st.columns([4, 2, 2, 2])

with col_head1:

    st.markdown("<h1 style='margin:0; color:#0f172a;'>Quotation List</h1>", unsafe_allow_html=True)

with col_head2:

    search_q = st.text_input("Search", placeholder="🔍 Search records...", label_visibility="collapsed")

with col_head3:

    if st.button("➕ Add Record", type="primary", use_container_width=True):

        quotation_dialog()

with col_head4:

    with st.popover("📥 Download Options", use_container_width=True):

        st.markdown("##### Filter by Date Range")

        d_from = st.date_input("From Date", value=datetime.date.today() - datetime.timedelta(days=30))

        d_to = st.date_input("To Date", value=datetime.date.today())

        

        if st.button("📊 Generate Excel", type="primary", use_container_width=True):

            try:

                df_base = st.session_state.quotations_df.copy()

                if search_q:

                    mask = df_base.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)

                    df_base = df_base[mask]

                

                df_base['Date_Parsed'] = pd.to_datetime(df_base['Date'], errors='coerce').dt.date

                df_filtered = df_base[(df_base['Date_Parsed'] >= d_from) & (df_base['Date_Parsed'] <= d_to)]

                

                if df_filtered.empty:

                    df_filtered = df_base

                

                sheet1_df = df_filtered[["Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project Name", "Quotation Amount"]].copy()

                sheet1_df.columns = ["Date", "Project ID", "Cluster", "Site ID", "Site Name", "Project", "Grand Total"]

                

                line_rows = []

                quotation_names = df_filtered["Quotation Name"].tolist()

                

                if quotation_names:

                    res_items = supabase.table("quotation_items").select("*").in_("Quotation Name", quotation_names).execute()

                    if res_items.data:

                        items_df = pd.DataFrame(res_items.data)

                        merged_df = pd.merge(items_df, df_filtered, on="Quotation Name", how="inner")

                        

                        for _, row in merged_df.iterrows():

                            p_id = row.get("Project ID", "")

                            clust = row.get("Cluster", "")

                            if not clust and not df_projects.empty:

                                match_proj = df_projects[df_projects["Project ID"] == p_id]

                                if not match_proj.empty:

                                    clust = match_proj.iloc[0].get("Cluster", "")



                            line_rows.append({

                                "Project ID": p_id,

                                "Site ID": row.get("Site ID", ""),

                                "Site Name": row.get("Site Name", ""),

                                "Cluster": clust,

                                "Project": row.get("Project Name", ""),

                                "Item Code": row.get("Item Code", ""),

                                "Item Description": row.get("Description", ""),

                                "Qty": row.get("Qty", 0),

                                "Price": row.get("Price", 0),

                                "Total": row.get("Total", 0)

                            })

                

                sheet2_df = pd.DataFrame(line_rows)

                if sheet2_df.empty:

                    sheet2_df = pd.DataFrame(columns=["Project ID", "Site ID", "Site Name", "Cluster", "Project", "Item Code", "Item Description", "Qty", "Price", "Total"])

                else:

                    sheet2_df = sheet2_df[["Project ID", "Site ID", "Site Name", "Cluster", "Project", "Item Code", "Item Description", "Qty", "Price", "Total"]]

                

                buffer = io.BytesIO()

                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:

                    sheet1_df.to_excel(writer, index=False, sheet_name='Site Details')

                    sheet2_df.to_excel(writer, index=False, sheet_name='Line Wise Items')

                

                st.download_button(

                    label="⬇️ Click Here to Download",

                    data=buffer.getvalue(),

                    file_name=f"Quotation_Export_{d_from}_to_{d_to}.xlsx",

                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

                    type="primary"

                )

            except Exception as e:

                st.error(f"Export Error: {e}")



st.markdown("<br>", unsafe_allow_html=True)



# --- 8. MAIN SCREEN QUOTATION LIST ---

df_display = st.session_state.quotations_df.copy()



if not df_display.empty and search_q:

    mask = df_display.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)

    df_display = df_display[mask]



# --- Exact columns requested for Main Screen ---

disp_cols = ["Date", "Project ID", "Site ID", "Site Name", "Cluster", "Project Name", "Quotation Amount"]



if not df_display.empty:

    for c in disp_cols:

        if c not in df_display.columns:

            df_display[c] = ""

            

    df_list = df_display[disp_cols].copy()

    df_list.insert(0, "Action", False)

    df_list.insert(0, "#", range(1, len(df_list) + 1))

else:

    df_list = pd.DataFrame(columns=["Action", "#"] + disp_cols)



edited_list = st.data_editor(

    df_list,

    use_container_width=True,

    hide_index=True,

    height=500,

    column_config={

        "Action": st.column_config.CheckboxColumn("SELECT", width="small", default=False),

        "#": st.column_config.NumberColumn("#", width="small", alignment="center"),

        "Quotation Amount": st.column_config.NumberColumn("GRAND GRAND TOTAL", format="₹ %d"),

        "Project Name": st.column_config.TextColumn("PROJECT"),

        "Site ID": st.column_config.TextColumn("SITE CODE"),

        "Cluster": st.column_config.TextColumn("CLUSTER")

    }

)



selected_rows = edited_list[edited_list["Action"] == True]

if not selected_rows.empty:

    st.markdown("---")

    col_act1, col_act2, _ = st.columns([2, 2, 8])

    

    selected_index = selected_rows.index[0]

    if selected_index < len(df_display):

        actual_data = df_display.iloc[selected_index].to_dict()

        

        with col_act1:

            if st.button("👁️ View / Edit", type="primary", use_container_width=True):

                quotation_dialog(actual_data)

                

        with col_act2:

            if st.button("🗑️ Delete", type="secondary", use_container_width=True):

                try:

                    q_name = actual_data["Quotation Name"]

                    supabase.table("quotations").delete().eq("Quotation Name", q_name).execute()

                    supabase.table("quotation_items").delete().eq("Quotation Name", q_name).execute()

                    st.session_state.quotations_df = fetch_quotations()

                    st.success(f"✅ Deleted {q_name}")

                    st.rerun()

                except Exception as e:

                    st.error(f"Error deleting: {e}")
