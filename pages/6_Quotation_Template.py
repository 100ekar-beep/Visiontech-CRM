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

# --- 3. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"      
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"   

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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
        res = supabase.table("quotation_templates").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "Template Name", "Items Data"])

df_items = fetch_item_master()
if not df_items.empty:
    df_items["Description"] = df_items["Description"].fillna("")
    df_items["Display"] = df_items["Item Code"].astype(str) + " | " + df_items["Description"].astype(str)
    item_display_list = df_items["Display"].tolist()
    display_to_code = dict(zip(df_items["Display"], df_items["Item Code"]))
    display_to_desc = dict(zip(df_items["Display"], df_items["Description"]))
    display_to_price = dict(zip(df_items["Display"], df_items["Price"]))
else:
    item_display_list = []
    display_to_code = {}
    display_to_desc = {}
    display_to_price = {}

if 'templates_df' not in st.session_state:
    st.session_state.templates_df = fetch_templates()

@st.dialog("📋 Quotation Template Builder", width="large")
def template_dialog(template_data=None):
    st.caption("Configure items for this quotation template")
    is_new = template_data is None
    
    def_name = "" if is_new else template_data.get("Template Name", "")
    t_name = st.text_input("QUOTATION TEMPLATE NAME *", value=def_name, key="input_template_name")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="modal-section-title" style="margin-top:0;">📚 Template Items</div>', unsafe_allow_html=True)

    # Initialize session state list for rows inside popup
    session_key_rows = f"popup_rows_{def_name if not is_new else 'new'}"
    if session_key_rows not in st.session_state:
        if is_new:
            st.session_state[session_key_rows] = [{"item": item_display_list[0] if item_display_list else "", "desc": "", "price": 0}]
        else:
            try:
                raw_data = template_data.get("Items Data", "[]")
                items_list = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                loaded = []
                for itm in items_list:
                    c = itm.get("Item Code", "")
                    # Find matching display string
                    matched_disp = next((d for d in item_display_list if d.startswith(c)), item_display_list[0] if item_display_list else "")
                    loaded.append({
                        "item": matched_disp,
                        "desc": itm.get("Description", ""),
                        "price": int(itm.get("Price", 0))
                    })
                st.session_state[session_key_rows] = loaded if loaded else [{"item": "", "desc": "", "price": 0}]
            except:
                st.session_state[session_key_rows] = [{"item": "", "desc": "", "price": 0}]

    # Render stable rows using form/container approach (No popup closing bug)
    with st.form(key="template_items_form", clear_on_submit=False):
        # Table Headers
        h1, h2, h3, h4 = st.columns([3, 4, 2, 1])
        with h1: st.markdown("**MATERIAL ITEM**")
        with h2: st.markdown("**DESCRIPTION**")
        with h3: st.markdown("**PRICE (₹)**")
        with h4: st.markdown("**ACTION**")

        updated_rows = []
        rows_to_delete = []

        for i, row_data in enumerate(st.session_state[session_key_rows]):
            c1, c2, c3, c4 = st.columns([3, 4, 2, 1])
            with c1:
                curr_item = row_data.get("item", "")
                idx_sel = item_display_list.index(curr_item) if curr_item in item_display_list else 0
                selected_val = st.selectbox(f"Item {i}", options=item_display_list, index=idx_sel, key=f"sel_item_{i}", label_visibility="collapsed")
            
            with c2:
                # Auto update description & price based on selection
                auto_desc = display_to_desc.get(selected_val, "")
                auto_price = display_to_price.get(selected_val, 0)
                st.text_input(f"Desc {i}", value=auto_desc, disabled=True, key=f"txt_desc_{i}", label_visibility="collapsed")
            
            with c3:
                p_val = st.number_input(f"Price {i}", value=int(auto_price), step=1, key=f"num_price_{i}", label_visibility="collapsed")
            
            with c4:
                if st.form_submit_button("🗑️", key=f"del_btn_{i}"):
                    rows_to_delete.append(i)

            updated_rows.append({
                "item": selected_val,
                "desc": auto_desc,
                "price": p_val
            })

        # Handle row deletion from list
        if rows_to_delete:
            for idx in sorted(rows_to_delete, reverse=True):
                st.session_state[session_key_rows].pop(idx)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        col_f1, col_f2 = st.columns([2, 8])
        with col_f1:
            add_clicked = st.form_submit_button("➕ Add Row", use_container_width=True)
        with col_f2:
            save_clicked = st.form_submit_button("💾 Save Template", type="primary", use_container_width=True)

        if add_clicked:
            st.session_state[session_key_rows].append({"item": item_display_list[0] if item_display_list else "", "desc": "", "price": 0})
            st.rerun()

        if save_clicked:
            if not t_name.strip():
                st.error("⚠️ Template Name is required!")
            else:
                clean_items = []
                for r in updated_rows:
                    disp_val = r["item"]
                    if disp_val:
                        code_clean = display_to_code.get(disp_val, disp_val.split(" | ")[0].strip())
                        clean_items.append({
                            "Item Code": code_clean,
                            "Description": r["desc"],
                            "Price": int(r["price"])
                        })
                
                payload = {
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
                    st.error(f"Error saving template: {e}")

# --- TOP HEADER ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("<h1 style='margin:0; color:#0f172a;'>Quotation Templates</h1>", unsafe_allow_html=True)
with col_h2:
    if st.button("➕ Add Template", type="primary", use_container_width=True):
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
