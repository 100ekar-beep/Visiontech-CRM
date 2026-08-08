import streamlit as st
import pandas as pd
import json
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Quotation Templates", page_icon="📋", layout="wide")

# --- 2. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
    }
    button[data-testid="baseButton-secondary"] {
        background: #ef4444 !important; color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important;
    }
    
    div[data-testid="stDialog"] > div {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    .modal-section-title {
        color: #3b82f6; font-size: 1rem; font-weight: 800; letter-spacing: 0.5px;
        margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase;
    }

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

# --- 4. FETCH DATA ---
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

def fetch_templates():
    try:
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("quotation_templates").select("*").eq("workspace", active_ws).execute()
        if not res.data:
            res = supabase.table("quotation_templates").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except:
        pass
    return pd.DataFrame(columns=["id", "Template Name", "Items Data"])

df_items = fetch_item_master()
if not df_items.empty:
    df_items["Item Code"] = df_items["Item Code"].astype(str).str.strip()
    df_items["Description"] = df_items["Description"].fillna("").astype(str).str.strip()
    df_items["Display"] = df_items["Item Code"] + " | " + df_items["Description"]
    
    item_display_list = df_items["Display"].tolist()
    item_code_list = df_items["Item Code"].tolist()
    # PREVENT DISAPPEARING BUG: Add empty string as valid option
    combined_item_options = [""] + list(dict.fromkeys(item_display_list + item_code_list))
    
    display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))
    display_to_price = dict(zip(df_items["Display"], df_items["Price"]))
    code_to_desc = dict(zip(df_items["Item Code"], df_items["Description"]))
    code_to_price = dict(zip(df_items["Item Code"], df_items["Price"]))
else:
    combined_item_options = [""]
    display_to_desc = {}
    display_to_price = {}
    code_to_desc = {}
    code_to_price = {}

if 'templates_df' not in st.session_state:
    st.session_state.templates_df = fetch_templates()

# --- 5. TEMPLATE DIALOG (FIXED FOR DISAPPEARING ROWS) ---
@st.dialog("📋 Quotation Template Builder", width="large")
def template_dialog(template_data=None):
    st.caption("Configure items for this quotation template")
    
    is_new = template_data is None
    
    # 🌟 FIX: Clean session keys when creating a brand new template so it appears blank
    if is_new:
        if "builder_items_df" in st.session_state:
            del st.session_state["builder_items_df"]
        if "template_name_input" in st.session_state:
            del st.session_state["template_name_input"]

    default_name = template_data.get("Template Name", "") if not is_new else ""
    
    tpl_name = st.text_input("QUOTATION TEMPLATE NAME *", value=default_name, key="template_name_input")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="modal-section-title">📂 Template Items</div>', unsafe_allow_html=True)
    
    if "builder_items_df" not in st.session_state:
        if is_new:
            # FIX: Initialize with empty string to force correct dtypes and prevent None/NaN inference
            st.session_state.builder_items_df = pd.DataFrame([{"Item Code": "", "Description": "", "Qty": 1, "Price": 0}])
        else:
            try:
                raw_items = json.loads(template_data["Items Data"]) if isinstance(template_data["Items Data"], str) else template_data["Items Data"]
                loaded_rows = []
                for ri in raw_items:
                    code_val = str(ri.get("Item Code", "")).strip()
                    desc_val = str(ri.get("Description", "")).strip()
                    qty_val = int(ri.get("Qty", 1))
                    price_val = int(ri.get("Price", 0))
                    
                    # Ensure full display string loads so dropdown doesn't blank out
                    disp_str = code_val
                    if code_val in code_to_desc:
                        disp_str = f"{code_val} | {code_to_desc[code_val]}"
                    elif desc_val:
                        disp_str = f"{code_val} | {desc_val}"
                        
                    loaded_rows.append({
                        "Item Code": disp_str,
                        "Description": desc_val,
                        "Qty": qty_val,
                        "Price": price_val
                    })
                st.session_state.builder_items_df = pd.DataFrame(loaded_rows)
            except:
                st.session_state.builder_items_df = pd.DataFrame([{"Item Code": "", "Description": "", "Qty": 1, "Price": 0}])

    editor_widget_key = "builder_data_editor_widget"
    if editor_widget_key in st.session_state:
        w_state = st.session_state[editor_widget_key]
        edits = w_state.get("edited_rows", {})
        adds = w_state.get("added_rows", [])
        dels = w_state.get("deleted_rows", [])
        
        if edits or adds or dels:
            curr_df = st.session_state.builder_items_df.copy()
            if dels: curr_df = curr_df.drop(dels).reset_index(drop=True)
            if edits:
                for str_idx, changes in edits.items():
                    idx = int(str_idx)
                    if idx < len(curr_df):
                        for col, val in changes.items():
                            curr_df.at[idx, col] = val
                        
                        # 🌟 FIX: DO NOT .strip() the value from 'changes'. Store it exactly as it matches the options list!
                        if "Item Code" in changes:
                            disp = changes["Item Code"]
                            if pd.notna(disp) and disp != "":
                                curr_df.at[idx, "Item Code"] = disp
                                if disp in display_to_desc:
                                    curr_df.at[idx, "Description"] = display_to_desc[disp]
                                    curr_df.at[idx, "Price"] = display_to_price[disp]
                                elif disp in code_to_desc:
                                    curr_df.at[idx, "Description"] = code_to_desc[disp]
                                    curr_df.at[idx, "Price"] = code_to_price[disp]
            if adds:
                for row in adds:
                    # FIX: Use empty string "" instead of None to prevent pandas dtype conversion issues
                    new_row = {"Item Code": "", "Description": "", "Qty": 1, "Price": 0}
                    if "Item Code" in row and pd.notna(row["Item Code"]):
                        disp = row["Item Code"]
                        if disp != "":
                            new_row["Item Code"] = disp
                            if disp in display_to_desc:
                                new_row["Description"] = display_to_desc[disp]
                                new_row["Price"] = display_to_price[disp]
                            elif disp in code_to_desc:
                                new_row["Description"] = code_to_desc[disp]
                                new_row["Price"] = code_to_price[disp]
                    curr_df = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.builder_items_df = curr_df
            del st.session_state[editor_widget_key]

    edited_df = st.data_editor(
        st.session_state.builder_items_df,
        key=editor_widget_key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=350,
        column_config={
            "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=combined_item_options, required=True, width="medium"),
            "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
            "Qty": st.column_config.NumberColumn("QTY", min_value=0, default=1, format="%d", alignment="center", width="small"),
            "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d", alignment="center", width="small")
        }
    )

    with col_add_btn:
        if st.button("➕ Add New Row", use_container_width=True):
            # FIX: Initialize with empty string "" instead of None
            new_item = pd.DataFrame([{"Item Code": "", "Description": "", "Qty": 1, "Price": 0}])
            st.session_state.builder_items_df = pd.concat([st.session_state.builder_items_df, new_item], ignore_index=True)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Template", type="primary", use_container_width=True):
        final_tpl_name = st.session_state.get('template_name_input', tpl_name).strip()
        if not final_tpl_name:
            st.error("⚠️ Template Name is required!")
            return
            
        items_list = []
        for _, r in edited_df.iterrows():
            if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip() != "":
                # 🌟 ONLY STRIP THE DISPLAY NAME INTO ACTUAL ITEM CODE WHEN SAVING TO DB
                clean_code = str(r["Item Code"]).split(" | ")[0].strip()
                items_list.append({
                    "Item Code": clean_code,
                    "Description": str(r["Description"]),
                    "Qty": int(r["Qty"]) if pd.notna(r["Qty"]) else 1,
                    "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0
                })
                
        payload = {
            "workspace": st.session_state.get('active_workspace', 'VISPL'),
            "Template Name": final_tpl_name,
            "Items Data": json.dumps(items_list)
        }
        
        try:
            if not is_new and "id" in template_data and pd.notna(template_data["id"]):
                supabase.table("quotation_templates").update(payload).eq("id", template_data["id"]).execute()
            else:
                supabase.table("quotation_templates").insert(payload).execute()
                
            st.session_state.templates_df = fetch_templates()
            if "builder_items_df" in st.session_state:
                del st.session_state["builder_items_df"]
            if "template_name_input" in st.session_state:
                del st.session_state["template_name_input"]
            st.success("✅ Template Saved Successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Database Error: {e}")

# --- 6. TOP HEADER & LIST ---
col_head1, col_head2, col_head3 = st.columns([5, 2, 2])
with col_head1:
    st.markdown("<h1 style='color:#0f172a; margin:0;'>Quotation Templates</h1>", unsafe_allow_html=True)
with col_head2:
    search_q = st.text_input("Search", placeholder="🔍 Search templates...", label_visibility="collapsed")
with col_head3:
    if st.button("➕ Add Template", type="primary", use_container_width=True):
        template_dialog()

st.markdown("<br>", unsafe_allow_html=True)

df_disp = st.session_state.templates_df.copy()
if not df_disp.empty and search_q:
    mask = df_disp.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)
    df_disp = df_disp[mask]

if not df_disp.empty:
    df_list = df_disp[["Template Name"]].copy()
    df_list.insert(0, "Action", False)
    df_list.insert(0, "#", range(1, len(df_list) + 1))
else:
    df_list = pd.DataFrame(columns=["Action", "#", "Template Name"])

edited_tbl = st.data_editor(
    df_list,
    use_container_width=True,
    hide_index=True,
    height=450,
    column_config={
        "Action": st.column_config.CheckboxColumn("SELECT", width="small", default=False),
        "#": st.column_config.NumberColumn("#", width="small", alignment="center"),
        "Template Name": st.column_config.TextColumn("QUOTATION TEMPLATE NAME")
    }
)

sel_rows = edited_tbl[edited_tbl["Action"] == True]
if not sel_rows.empty:
    st.markdown("---")
    c_act1, c_act2, _ = st.columns([2, 2, 8])
    sel_idx = sel_rows.index[0]
    if sel_idx < len(df_disp):
        row_dict = df_disp.iloc[sel_idx].to_dict()
        with c_act1:
            if st.button("👁️ View / Edit", type="primary", use_container_width=True):
                if "builder_items_df" in st.session_state:
                    del st.session_state["builder_items_df"]
                template_dialog(row_dict)
        with c_act2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                try:
                    supabase.table("quotation_templates").delete().eq("id", row_dict["id"]).execute()
                    st.session_state.templates_df = fetch_templates()
                    st.success("✅ Template Deleted Successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
