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
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
    }
    div[data-testid="stDialog"] > div { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; }
    .modal-section-title { color: #3b82f6; font-size: 1rem; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
    label p, label[data-testid="stWidgetLabel"] p { color: #64748b !important; font-weight: 700 !important; font-size: 0.85rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #6366f1 !important; color: white !important; font-weight: 700 !important; }

    /* PREMIUM SIDEBAR */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); border-right: 1px solid rgba(255, 255, 255, 0.05); }
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
# FIX: Ab hardcoded URL/Key ki jagah st.secrets se liya jaa raha hai — isse
# ek hi jagah (Streamlit Cloud Secrets) update karke sabhi pages naye
# Supabase project se automatically connect ho jaate hain.
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

def fetch_templates():
    try:
        active_ws = st.session_state.get('active_workspace', 'VISPL')
        res = supabase.table("quotation_templates").select("*").eq("workspace", active_ws).execute()
        
        # Fallback if old data doesn't have workspace
        if not res.data:
            res = supabase.table("quotation_templates").select("*").is_("workspace", "null").execute()
            
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        # FIX: Agar database me workspace column nahi hai toh bina workspace ke fetch karega
        error_str = str(e)
        if 'PGRST204' in error_str or 'workspace' in error_str:
            try:
                res_fallback = supabase.table("quotation_templates").select("*").execute()
                if res_fallback.data:
                    return pd.DataFrame(res_fallback.data)
            except Exception:
                pass
    return pd.DataFrame(columns=["id", "Template Name", "Items Data"])

df_items = fetch_item_master()
if not df_items.empty:
    df_items["Description"] = df_items["Description"].fillna("")
    # --- NAYI LINE: Description first, Code inside brackets for dropdown search view ---
    df_items["Display"] = df_items["Description"].astype(str) + "  [" + df_items["Item Code"].astype(str) + "]"
    
    item_display_list = df_items["Display"].tolist()
    item_code_list = df_items["Item Code"].astype(str).tolist()
    combined_item_options = item_display_list + item_code_list 
    
    display_to_code = dict(zip(df_items["Display"], df_items["Item Code"]))
    display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))
    display_to_price = dict(zip(df_items["Display"], df_items["Price"]))
    code_to_display = dict(zip(df_items["Item Code"], df_items["Display"]))
else:
    combined_item_options = []
    display_to_code = {}
    display_to_desc = {}
    display_to_price = {}
    code_to_display = {}

if 'templates_df' not in st.session_state:
    st.session_state.templates_df = fetch_templates()

@st.dialog("📋 Quotation Template Builder", width="large")
def template_dialog(template_data=None):
    st.caption("Configure items for this quotation template")
    is_new = template_data is None
    
    def_name = "" if is_new else template_data.get("Template Name", "")
    t_name = st.text_input("QUOTATION TEMPLATE NAME *", value=def_name)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_t1, col_t2 = st.columns([8, 2])
    with col_t1:
        st.markdown('<div class="modal-section-title" style="margin-top:0;">📚 Template Items</div>', unsafe_allow_html=True)

    t_key = f"t_items_{def_name if not is_new else 'new'}"
    widget_t_key = f"widget_{t_key}"

    if t_key not in st.session_state:
        if is_new:
            st.session_state[t_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price"])
        else:
            try:
                raw_data = template_data.get("Items Data", "[]")
                items_list = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                temp_df = pd.DataFrame(items_list)
                
                # Qty Handle karna agar purane template mein na ho
                if "Qty" not in temp_df.columns:
                    temp_df.insert(2, "Qty", 1)
                    
                # Map code back to Display format for dropdown
                if "Item Code" in temp_df.columns:
                    temp_df["Item Code"] = temp_df["Item Code"].map(code_to_display).fillna(temp_df["Item Code"])
                st.session_state[t_key] = temp_df
            except:
                st.session_state[t_key] = pd.DataFrame(columns=["Item Code", "Description", "Qty", "Price"])

    # --- FAILSAFE: Agar purana Session State without 'Qty' ho, toh zabardasti column dalo ---
    if "Qty" not in st.session_state[t_key].columns:
        st.session_state[t_key].insert(2, "Qty", 1)

    # --- Stable State Editor Engine (Prevents Popup Close Bug) ---
    if widget_t_key in st.session_state:
        w_state = st.session_state[widget_t_key]
        edits = w_state.get("edited_rows", {})
        adds = w_state.get("added_rows", [])
        dels = w_state.get("deleted_rows", [])
        
        if edits or adds or dels:
            curr_df = st.session_state[t_key].copy()
            if dels: curr_df = curr_df.drop(dels).reset_index(drop=True)
            if edits:
                for str_idx, changes in edits.items():
                    idx = int(str_idx)
                    if idx < len(curr_df):
                        for col, val in changes.items():
                            curr_df.at[idx, col] = val
                        if "Item Code" in changes:
                            disp = str(changes["Item Code"])
                            if " | " in disp or "[" in disp:
                                # Extract pure code
                                code_only = display_to_code.get(disp, disp.split("[")[-1].replace("]", "").strip() if "[" in disp else disp)
                                curr_df.at[idx, "Item Code"] = code_only
                                if disp in display_to_desc:
                                    curr_df.at[idx, "Description"] = display_to_desc[disp]
                                    curr_df.at[idx, "Price"] = display_to_price[disp]
                            else:
                                match = df_items[df_items["Item Code"] == disp]
                                if not match.empty:
                                    curr_df.at[idx, "Description"] = match.iloc[0]["Description"]
                                    curr_df.at[idx, "Price"] = match.iloc[0]["Price"]
            if adds:
                for row in adds:
                    new_row = {"Item Code": row.get("Item Code"), "Description": "", "Qty": 1, "Price": 0}
                    if "Item Code" in row and pd.notna(row["Item Code"]):
                        disp = str(row["Item Code"])
                        if "[" in disp or " | " in disp:
                            code_only = display_to_code.get(disp, disp.split("[")[-1].replace("]", "").strip() if "[" in disp else disp)
                            new_row["Item Code"] = code_only
                            if disp in display_to_desc:
                                new_row["Description"] = display_to_desc[disp]
                                new_row["Price"] = display_to_price[disp]
                    curr_df = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state[t_key] = curr_df
            del st.session_state[widget_t_key]

    edited_t_df = st.data_editor(
        st.session_state[t_key],
        key=widget_t_key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=300,
        column_config={
            # --- Column Config Updated to strictly show Qty in middle ---
            "Item Code": st.column_config.SelectboxColumn("MATERIAL ITEM", options=combined_item_options, required=True, width="medium"),
            "Description": st.column_config.TextColumn("DESCRIPTION", disabled=True, width="large"),
            "Qty": st.column_config.NumberColumn("QTY", min_value=1, default=1, alignment="center", width="small"),
            "Price": st.column_config.NumberColumn("PRICE", min_value=0, format="₹ %d", alignment="center", width="small")
        }
    )

    # --- CALCULATE AND DISPLAY GRAND TOTAL FOR TEMPLATE ---
    try:
        qty_series = pd.to_numeric(edited_t_df["Qty"], errors='coerce').fillna(0)
        price_series = pd.to_numeric(edited_t_df["Price"], errors='coerce').fillna(0)
        grand_total = (qty_series * price_series).sum()
    except Exception:
        grand_total = 0

    st.markdown(f"<h3 style='text-align: right; color: #4f46e5; margin-top: 10px; margin-bottom: 20px;'>Grand Total: ₹ {grand_total:,.0f}</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Template", type="primary", use_container_width=True):
        if not t_name.strip():
            st.error("⚠️ Template Name is required!")
            return
        
        clean_items = []
        for _, r in edited_t_df.iterrows():
            if pd.notna(r["Item Code"]) and str(r["Item Code"]).strip() != "":
                disp_val = str(r["Item Code"])
                c_code = display_to_code.get(disp_val, disp_val.split("[")[-1].replace("]", "").strip() if "[" in disp_val else disp_val)
                clean_items.append({
                    "Item Code": c_code,
                    "Description": str(r["Description"]),
                    "Qty": int(r["Qty"]) if "Qty" in r and pd.notna(r["Qty"]) else 1,
                    "Price": int(r["Price"]) if pd.notna(r["Price"]) else 0
                })
        
        payload = {
            "workspace": st.session_state.get('active_workspace', 'VISPL'),
            "Template Name": t_name.strip(),
            "Items Data": json.dumps(clean_items)
        }
        
        try:
            if not is_new and "id" in template_data and pd.notna(template_data["id"]):
                supabase.table("quotation_templates").update(payload).eq("id", template_data["id"]).execute()
            else:
                supabase.table("quotation_templates").insert(payload).execute()
            
            st.session_state.templates_df = fetch_templates()
            st.success("✅ Template Saved Successfully!")
            st.rerun()
        except Exception as e:
            # FIX: Fallback if workspace column is completely missing in database schema
            error_str = str(e)
            if 'PGRST204' in error_str or 'workspace' in error_str:
                payload_fallback = {k: v for k, v in payload.items() if k != "workspace"}
                try:
                    if not is_new and "id" in template_data and pd.notna(template_data["id"]):
                        supabase.table("quotation_templates").update(payload_fallback).eq("id", template_data["id"]).execute()
                    else:
                        supabase.table("quotation_templates").insert(payload_fallback).execute()
                    
                    st.session_state.templates_df = fetch_templates()
                    st.success("✅ Template Saved! (⚠️ DB me 'workspace' column nahi hai isliye use skip kiya gaya)")
                    st.rerun()
                except Exception as fallback_e:
                    st.error(f"Error saving template: {fallback_e}")
            else:
                st.error(f"Error saving template: {e}")

# --- TOP HEADER ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("<h1 style='margin:0; color:#0f172a;'>Quotation Templates</h1>", unsafe_allow_html=True)
with col_h2:
    if st.button("➕ Add Template", type="primary", use_container_width=True):
        # 🌟 NEW LOGIC: Clear all state parameters related to template form
        for key in list(st.session_state.keys()):
            if key.startswith("t_items_") or key.startswith("widget_t_items_"):
                del st.session_state[key]
        template_dialog()

st.markdown("<br>", unsafe_allow_html=True)

df_templates = st.session_state.templates_df.copy()
if not df_templates.empty:
    list_df = df_templates[["Template Name"]].copy()
    list_df.insert(0, "Action", False)
    list_df.insert(0, "Sr. No.", range(1, len(list_df) + 1))
    
    edited_t_list = st.data_editor(list_df, use_container_width=True, hide_index=True, height=450, column_config={"Action": st.column_config.CheckboxColumn("SELECT", width="small")})
    
    sel_rows = edited_t_list[edited_t_list["Action"] == True]
    if not sel_rows.empty:
        st.markdown("---")
        idx = sel_rows.index[0]
        row_dict = df_templates.iloc[idx].to_dict()
        col_b1, col_b2, _ = st.columns([2, 2, 8])
        with col_b1:
            if st.button("👁️ Edit", type="primary", use_container_width=True):
                template_dialog(row_dict)
        with col_b2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                try:
                    supabase.table("quotation_templates").delete().eq("id", row_dict["id"]).execute()
                    st.session_state.templates_df = fetch_templates()
                    st.success("✅ Template Deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    st.info("No Templates found. Click '+ Add Template' to create one.")
