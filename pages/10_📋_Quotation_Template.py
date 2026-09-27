import streamlit as st
import pandas as pd
import json
import html
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Quotation Templates", page_icon="📋", layout="wide")

# --- 2. ✨ LAVISH CUSTOM CSS (Quotation / Site Data jaisa) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    button[data-testid="baseButton-primary"], button[data-testid="stBaseButton-primary"], button[kind="primary"] {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important; transition: all .2s ease !important;
    }
    button[kind="primary"] p { color: #ffffff !important; font-weight: 800 !important; }
    button[data-testid="baseButton-secondary"], button[data-testid="stBaseButton-secondary"], button[kind="secondary"] {
        background: #ffffff !important; color: #334155 !important; border: 1.5px solid #cbd5e1 !important; border-radius: 8px !important;
        font-weight: 800 !important; box-shadow: 0 2px 4px rgba(15,23,42,0.05) !important; transition: all .2s ease !important;
    }
    button[kind="secondary"] p { color: #334155 !important; font-weight: 800 !important; }
    button[kind="primary"]:hover, button[kind="secondary"]:hover { transform: translateY(-2px) !important; }

    div[data-testid="stDialog"] > div { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }
    .modal-section-title { color: #4338ca; font-size: 1rem; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #e0e7ff; padding-bottom: 8px; }
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

    /* ================= KPI CARDS ================= */
    .lux-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 4px 0 22px; }
    .lux-kpi {
        position: relative; background: #ffffff; border-radius: 16px; padding: 18px 20px 16px;
        border: 1px solid #e0e7ff; overflow: hidden;
        box-shadow: 0 12px 28px -14px rgba(79, 70, 229, 0.35);
        transition: transform .25s ease, box-shadow .25s ease;
    }
    .lux-kpi:hover { transform: translateY(-3px); box-shadow: 0 18px 34px -14px rgba(79, 70, 229, 0.45); }
    .lux-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--accent); }
    .lux-kpi-icon {
        position: absolute; right: 16px; top: 16px; width: 42px; height: 42px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center; font-size: 1.3rem; background: var(--soft);
    }
    .lux-kpi-label { font-size: .7rem; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #64748b; padding-right: 48px; }
    .lux-kpi-value { font-size: 1.55rem; font-weight: 900; color: #0f172a; margin-top: 8px; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .lux-kpi-value.small { font-size: 1.1rem; }
    .lux-kpi-foot { font-size: .75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }

    /* ================= TABLE ================= */
    .slux-head-bar {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 16px 22px; border-radius: 18px 18px 0 0;
        background: linear-gradient(100deg, #1e1b4b 0%, #312e81 45%, #5b21b6 100%);
    }
    .slux-title { color: #ffffff; font-weight: 900; font-size: 1.05rem; letter-spacing: 1.5px; text-transform: uppercase; }
    .slux-title span { color: #c7d2fe; font-weight: 600; font-size: .8rem; letter-spacing: .5px; text-transform: none; margin-left: 8px; }
    .slux-badge {
        background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25); color: #fde68a;
        padding: 5px 12px; border-radius: 999px; font-weight: 800; font-size: .78rem; letter-spacing: .5px;
    }
    .st-key-tpl_table_wrap {
        background: #ffffff !important; overflow: auto !important; padding: 0 !important;
        border: 1px solid #e0e7ff !important; border-top: none !important; border-bottom: none !important; border-radius: 0 !important;
    }
    .st-key-tpl_table_wrap [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-tpl_table_wrap [data-testid="stHorizontalBlock"],
    .st-key-tpl_table_wrap div[class*="st-key-tplhead"],
    .st-key-tpl_table_wrap div[class*="st-key-tplrow_"] { min-width: 900px !important; }
    .st-key-tpl_table_wrap [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; align-items: center !important; }
    .st-key-tpl_table_wrap [data-testid="stColumn"], .st-key-tpl_table_wrap [data-testid="column"] {
        padding: 0 12px !important; min-width: 0 !important; border-right: 1px solid #f1f5f9;
    }
    div[class*="st-key-tplhead"] {
        position: sticky !important; top: 0 !important; z-index: 5 !important;
        background: #eef2ff !important; border-bottom: 2px solid #c7d2fe !important; padding: 13px 0 !important;
    }
    div[class*="st-key-tplhead"] [data-testid="stColumn"], div[class*="st-key-tplhead"] [data-testid="column"] { border-right: 1px solid #dfe4fb !important; }
    .slux-th { color: #3730a3; font-size: .68rem; font-weight: 800; letter-spacing: 1.1px; text-transform: uppercase; white-space: nowrap; }
    .slux-th.c { text-align: center; }
    .slux-th.r { text-align: right; }
    div[class*="st-key-tplrow_"] {
        padding: 10px 0 !important; background: #ffffff;
        border-bottom: 1px solid #f1f5f9; transition: background .15s ease, box-shadow .15s ease;
    }
    div[class*="st-key-tplrow_odd"] { background: #fafaff; }
    div[class*="st-key-tplrow_"]:hover { background: #eef2ff; box-shadow: inset 4px 0 0 #6366f1; }
    div[class*="st-key-tplrow_"] p { margin: 0 !important; }

    .slux-cell { font-size: .88rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
    .slux-num {
        display: inline-flex; width: 30px; height: 30px; border-radius: 50%;
        align-items: center; justify-content: center;
        background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff;
        font-weight: 800; font-size: .75rem; box-shadow: 0 4px 10px -3px rgba(99,102,241,.6);
    }
    .tpl-name { font-weight: 800; color: #312e81; font-size: .95rem; }
    .tpl-preview { color: #64748b; font-size: .78rem; font-weight: 600; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .tpl-count {
        display: inline-block; min-width: 34px; text-align: center; padding: 4px 10px; border-radius: 8px;
        background: #eef2ff; border: 1px solid #c7d2fe; color: #4338ca; font-weight: 900; font-size: .82rem;
    }
    .tpl-qty {
        display: inline-block; min-width: 34px; text-align: center; padding: 4px 10px; border-radius: 8px;
        background: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; font-weight: 900; font-size: .82rem;
    }
    .tpl-amt { text-align: right; font-weight: 900; color: #4f46e5; font-size: .95rem; font-variant-numeric: tabular-nums; }

    /* Single ⚙️ popover button at row start */
    div[class*="st-key-tplpop_"] button {
        width: 40px !important; max-width: 40px !important; height: 34px !important; min-height: 34px !important;
        padding: 0 !important; margin: 0 auto !important; border-radius: 8px !important;
        background: rgba(59,130,246,0.15) !important; border: 1px solid rgba(59,130,246,0.3) !important;
        box-shadow: none !important; transition: all .2s ease !important;
    }
    div[class*="st-key-tplpop_"] button:hover {
        background: #3b82f6 !important; border-color: #60a5fa !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 14px -4px rgba(59,130,246,.6) !important;
    }
    div[class*="st-key-tplpop_"] button p, div[class*="st-key-tplpop_"] button span { color: #1e293b !important; }
    div[class*="st-key-tplpop_"] button svg { display: none !important; }
    .st-key-tpl_del_yes button { background: linear-gradient(90deg, #ef4444, #dc2626) !important; border: none !important; }
    .st-key-tpl_del_yes button p { color: #ffffff !important; }

    .slux-foot {
        display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
        padding: 14px 22px; background: linear-gradient(90deg, #f5f3ff, #eef2ff);
        border: 1px solid #e0e7ff; border-top: 2px solid #c7d2fe; border-radius: 0 0 18px 18px;
        box-shadow: 0 24px 48px -22px rgba(30, 27, 75, 0.45);
        font-weight: 900; color: #312e81; text-transform: uppercase; letter-spacing: 1px; font-size: .78rem;
    }
    .slux-foot span { text-transform: none; letter-spacing: 0; font-size: .95rem; }
    .slux-empty {
        background: #fff; border: 1px dashed #c7d2fe; border-radius: 18px; padding: 48px 20px;
        text-align: center; color: #64748b; font-weight: 600;
    }
    .slux-empty div { font-size: 2.4rem; margin-bottom: 8px; }
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

# FIX: pehle templates sirf EK BAAR session_state me load hote the — workspace
# badalne par bhi PURANI company ke templates dikhte rehte the (jab tak page
# refresh na ho). Ab har workspace ka apna cache hai; save/delete par clear hota hai.
@st.cache_data(ttl=60, show_spinner=False)
def _fetch_templates_cached(active_ws):
    try:
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

def fetch_templates():
    return _fetch_templates_cached(st.session_state.get('active_workspace', 'VISPL'))
fetch_templates.clear = _fetch_templates_cached.clear

df_items = fetch_item_master()
if not df_items.empty:
    df_items["Description"] = df_items["Description"].fillna("")
    # --- Description first, Code inside brackets for dropdown search view ---
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

    st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin: 10px 0 20px 0;">
            <div style="background:linear-gradient(90deg,#f5f3ff,#eef2ff); border:1px solid #c7d2fe; border-radius:14px; padding:12px 22px; text-align:right;">
                <div style="color:#64748b; font-weight:800; font-size:.72rem; letter-spacing:1px; text-transform:uppercase;">Grand Total</div>
                <div style="color:#4f46e5; font-weight:900; font-size:1.6rem;">₹ {grand_total:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

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
            
            fetch_templates.clear()
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
                    
                    fetch_templates.clear()
                    st.success("✅ Template Saved! (⚠️ DB me 'workspace' column nahi hai isliye use skip kiya gaya)")
                    st.rerun()
                except Exception as fallback_e:
                    st.error(f"Error saving template: {fallback_e}")
            else:
                st.error(f"Error saving template: {e}")


@st.dialog("🗑️ Delete Template")
def delete_template_dialog(row_dict, items_count, value):
    st.markdown(
        f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
<div style="font-weight:900;color:#991b1b;font-size:1rem;">{html.escape(str(row_dict.get('Template Name','') or '-'))}</div>
<div style="color:#7f1d1d;font-size:.85rem;margin-top:4px;">{items_count} item(s) • ₹ {value:,.0f}</div>
</div>
<p style="color:#475569;">Ye template permanently delete ho jayega. Kya aap sure hain?</p>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", key="tpl_del_no", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Yes, Delete", key="tpl_del_yes", use_container_width=True):
            try:
                supabase.table("quotation_templates").delete().eq("id", row_dict["id"]).execute()
                fetch_templates.clear()
                st.success("✅ Template Deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


def _parse_items(raw):
    try:
        items = json.loads(raw) if isinstance(raw, str) else (raw or [])
        return items if isinstance(items, list) else []
    except Exception:
        return []

def _num(v, default=0.0):
    n = pd.to_numeric(v, errors="coerce")
    return default if pd.isna(n) else float(n)


# --- TOP HEADER ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("<h1 style='margin:0; color:#0f172a;'>📋 Quotation Templates</h1>", unsafe_allow_html=True)
with col_h2:
    if st.button("➕ Add Template", type="primary", use_container_width=True):
        # Clear all state parameters related to template form
        for key in list(st.session_state.keys()):
            if key.startswith("t_items_") or key.startswith("widget_t_items_"):
                del st.session_state[key]
        template_dialog()

st.markdown("<br>", unsafe_allow_html=True)

df_templates = fetch_templates().copy().reset_index(drop=True)

# --- Per-template summary (items, qty, value) ---
summaries = []
for _, r in df_templates.iterrows():
    items = _parse_items(r.get("Items Data", "[]"))
    qty_total = sum(_num(it.get("Qty", 1), 1) for it in items)
    value = sum(_num(it.get("Qty", 1), 1) * _num(it.get("Price", 0)) for it in items)
    preview = ", ".join(str(it.get("Description") or it.get("Item Code") or "").strip() for it in items[:3] if (it.get("Description") or it.get("Item Code")))
    if len(items) > 3:
        preview += f" +{len(items) - 3} more"
    summaries.append({"items": len(items), "qty": qty_total, "value": value, "preview": preview})

if not df_templates.empty:
    # --- KPI CARDS ---
    k_count = len(df_templates)
    k_items = sum(s["items"] for s in summaries)
    k_avg = (sum(s["value"] for s in summaries) / k_count) if k_count else 0.0
    top_idx = max(range(k_count), key=lambda i: summaries[i]["value"]) if k_count else None
    top_name = str(df_templates.iloc[top_idx].get("Template Name", "-")) if top_idx is not None else "-"
    top_value = summaries[top_idx]["value"] if top_idx is not None else 0.0

    def _kpi(icon, label, value, foot, accent, soft, value_cls=""):
        return (
            f'<div class="lux-kpi" style="--accent:{accent};--soft:{soft};">'
            f'<div class="lux-kpi-icon">{icon}</div><div class="lux-kpi-label">{label}</div>'
            f'<div class="lux-kpi-value {value_cls}" title="{html.escape(str(value))}">{value}</div><div class="lux-kpi-foot">{foot}</div></div>'
        )

    st.markdown(
        '<div class="lux-kpi-grid">'
        + _kpi("📋", "Templates", f"{k_count:,}", "In this workspace", "linear-gradient(90deg,#6366f1,#8b5cf6)", "#eef2ff")
        + _kpi("📦", "Total Line Items", f"{k_items:,}", "Across all templates", "linear-gradient(90deg,#3b82f6,#06b6d4)", "#eff6ff")
        + _kpi("💰", "Avg Template Value", f"₹ {k_avg:,.0f}", "Qty × Price", "linear-gradient(90deg,#10b981,#14b8a6)", "#ecfdf5")
        + _kpi("🏆", "Highest Value", html.escape(top_name), f"₹ {top_value:,.0f}", "linear-gradient(90deg,#f59e0b,#f97316)", "#fffbeb", "small")
        + '</div>',
        unsafe_allow_html=True,
    )

    # --- ✨ LAVISH TABLE — single ⚙️ button at row start ---
    COL_RATIOS = [0.55, 0.5, 4.2, 1.0, 1.0, 1.5]
    COL_LABELS = ["⚙️", "#", "TEMPLATE NAME", "ITEMS", "TOTAL QTY", "TEMPLATE VALUE"]

    st.markdown(
        '<div class="slux-head-bar">'
        '<div class="slux-title">📋 Template Library<span>click ⚙️ to edit or delete</span></div>'
        f'<div class="slux-badge">{k_count} template{"s" if k_count != 1 else ""}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    table_kwargs = {"height": 520} if k_count > 8 else {}
    with st.container(key="tpl_table_wrap", **table_kwargs):
        with st.container(key="tplhead"):
            h_cols = st.columns(COL_RATIOS, vertical_alignment="center")
            for i, (h_col, label) in enumerate(zip(h_cols, COL_LABELS)):
                cls = " c" if i in (0, 1, 3, 4) else (" r" if i == 5 else "")
                h_col.markdown(f"<div class='slux-th{cls}'>{label}</div>", unsafe_allow_html=True)

        for pos, (_, r) in enumerate(df_templates.iterrows()):
            row_dict = r.to_dict()
            rid = row_dict.get("id")
            rk = rid if rid is not None and str(rid).strip() not in ("", "nan", "None") else f"s{pos}"
            s = summaries[pos]
            parity = "odd" if (pos + 1) % 2 else "even"
            name = str(row_dict.get("Template Name", "") or "-")

            with st.container(key=f"tplrow_{parity}_{rk}"):
                rcols = st.columns(COL_RATIOS, vertical_alignment="center")
                with rcols[0]:
                    with st.container(key=f"tplpop_{rk}"):
                        with st.popover("⚙️"):
                            if st.button("✏️ Edit Template", key=f"tpl_edit_{rk}", use_container_width=True):
                                template_dialog(row_dict)
                            if st.button("🗑️ Delete Template", key=f"tpl_del_{rk}", use_container_width=True):
                                delete_template_dialog(row_dict, s["items"], s["value"])
                rcols[1].markdown(f"<div style='text-align:center;'><span class='slux-num'>{pos + 1}</span></div>", unsafe_allow_html=True)
                rcols[2].markdown(
                    f"<div class='slux-cell'><div class='tpl-name' title='{html.escape(name)}'>📋 {html.escape(name)}</div>"
                    f"<div class='tpl-preview' title='{html.escape(s['preview'])}'>{html.escape(s['preview']) or '—'}</div></div>",
                    unsafe_allow_html=True,
                )
                rcols[3].markdown(f"<div style='text-align:center;'><span class='tpl-count'>{s['items']}</span></div>", unsafe_allow_html=True)
                qty_txt = str(int(s["qty"])) if float(s["qty"]).is_integer() else f"{s['qty']:g}"
                rcols[4].markdown(f"<div style='text-align:center;'><span class='tpl-qty'>{qty_txt}</span></div>", unsafe_allow_html=True)
                rcols[5].markdown(f"<div class='slux-cell tpl-amt'>₹ {s['value']:,.0f}</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="slux-foot"><div>{k_count:,} template{"s" if k_count != 1 else ""}</div>'
        f'<div><span>Total Items: <b style="color:#4338ca;">{k_items:,}</b></span></div></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="slux-empty"><div>📋</div>No Templates found. Click ➕ Add Template to create one.</div>',
        unsafe_allow_html=True,
    )
