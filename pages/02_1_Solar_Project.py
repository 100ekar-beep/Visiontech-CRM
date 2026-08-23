import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client
from st_keyup import st_keyup

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Solar Project Hub", page_icon="☀️", layout="wide")

# --- INIT SESSION STATE ---
if 'solar_current_page' not in st.session_state:
    st.session_state.solar_current_page = 1

# --- 2. CSS (same premium dark theme as Site Data Hub) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 800 !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .page-count { text-align: center; font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-top: 10px; }
    div.stButton > button p, div.stButton > button span, div.stButton > button div {
        color: #ffffff !important; font-weight: 800 !important;
    }

    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        color: #ffffff !important; font-weight: 800 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p, div[data-testid="stDialog"] p {
        color: #e2e8f0 !important;
    }
    .modal-section-title {
        color: #94a3b8; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;
        margin-top: 15px; margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 5px;
    }
    label p, label[data-testid="stWidgetLabel"] p {
        color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px;
    }
    div[data-testid="stTextInput"] input:disabled {
        color: #000000 !important; font-weight: 700 !important; -webkit-text-fill-color: #000000 !important;
    }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS
       ========================================================= */

    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Individual Sidebar Links / Buttons */
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

    /* Hover Effect for Sidebar Links */
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }

    /* Active/Selected Page Button */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(90deg, #f59e0b 0%, #ec4899 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
    }

    /* Clean up the default Streamlit styling overrides */
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* Summary cards */
    .solar-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px 18px;
        text-align: center;
    }
    .solar-card .label { color: #94a3b8; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; }
    .solar-card .value { color: #ffffff; font-size: 1.5rem; font-weight: 900; margin-top: 6px; }

    /* Table wrap */
    .st-key-solar_table_wrap {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto !important;
    }
    .st-key-solar_table_wrap div[data-testid="stHorizontalBlock"] {
        min-width: 1600px !important;
        align-items: center !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        padding: 6px 0 !important;
        flex-wrap: nowrap !important;
    }
    .st-key-solar_table_wrap div[data-testid="stHorizontalBlock"]:hover { background: rgba(255,255,255,0.04); }
    .st-key-solar_table_wrap div[data-testid="column"] {
        padding: 0 15px !important; display: flex; align-items: center; justify-content: flex-start;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .st-key-solar_table_wrap div[data-testid="column"]:last-child { border-right: none; }
    .st-key-solar_table_wrap .tbl-head {
        background: transparent; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.8px;
        color: #94a3b8; text-transform: uppercase; white-space: nowrap !important;
    }
    .st-key-solar_table_wrap .tbl-cell {
        color: #e2e8f0; font-size: 0.86rem; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; width: 100%;
    }
    .st-key-solar_table_wrap .tbl-serial { color: #64748b; font-size: 0.85rem; font-weight: 800; }

    .st-key-solar_table_wrap button {
        height: 32px !important; width: 100% !important; max-width: 40px !important; padding: 0 !important;
        min-height: 0 !important; border-radius: 6px !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
        background: rgba(245,158,11,0.15) !important; border: 1px solid rgba(245,158,11,0.35) !important;
        margin: 0 auto !important; box-shadow: none !important; cursor: pointer !important;
    }
    .st-key-solar_table_wrap button:hover {
        background: #f59e0b !important; border-color: #fbbf24 !important; transform: translateY(-2px) !important;
    }

    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem;
        font-weight: 800; letter-spacing: 0.4px; white-space: nowrap !important; text-align: center;
    }
    .status-green  { background: rgba(34,197,94,0.18);  color: #4ade80; }
    .status-yellow { background: rgba(234,179,8,0.18);  color: #facc15; }
    .status-grey   { background: rgba(148,163,184,0.15); color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CONNECTION (same creds as main app) ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

def get_all_dropdowns():
    try:
        res = supabase.table("dropdown_master").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_opts(category, all_data):
    opts = [row["option_value"] for row in all_data if row["category"] == category]
    return ["Select"] + opts

def pay_badge(val):
    v = str(val).strip()
    if v == "Paid":
        return "<span class='status-badge status-green'>Paid</span>"
    elif v == "Pending":
        return "<span class='status-badge status-yellow'>Pending</span>"
    return "<span class='status-badge status-grey'>-</span>"

def num(v):
    try:
        return float(v) if v not in (None, "", "None") else 0.0
    except Exception:
        return 0.0

# --- 4. MANAGE TEAMS DIALOG ---
@st.dialog("⚙️ Manage Solar Teams & Charges", width="large")
def manage_solar_teams_dialog(site_row, alloc_row):
    st.caption("Civil / Electrical / Transporter teams ke charges aur payment status yahan manage karein")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.text_input("PROJECT ID", value=site_row.get("Project ID", ""), disabled=True)
    with c2: st.text_input("SITE ID", value=site_row.get("Site ID", ""), disabled=True)
    with c3: st.text_input("SITE NAME", value=site_row.get("Site Name", ""), disabled=True)
    with c4: st.text_input("CLUSTER", value=site_row.get("Cluster", ""), disabled=True)

    all_dd = get_all_dropdowns()
    team_opts = get_opts("Team Name", all_dd)

    def get_idx(val, opt_list):
        return opt_list.index(val) if val in opt_list else 0

    def team_section(label, key_prefix, alloc):
        st.markdown(f'<div class="modal-section-title">👷 {label} TEAM</div>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_name = st.selectbox(
                f"{label} TEAM NAME", team_opts,
                index=get_idx(alloc.get(f"{key_prefix}_team_name", ""), team_opts),
                key=f"solar_{key_prefix}_team"
            )
        with tc2:
            t_charge = st.number_input(
                f"{label} CHARGE AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_charge_amount", 0)),
                key=f"solar_{key_prefix}_charge"
            )
        with tc3:
            t_pay = st.selectbox(
                f"{label} PAYMENT STATUS", ["Pending", "Paid"],
                index=(1 if alloc.get(f"{key_prefix}_payment_status") == "Paid" else 0),
                key=f"solar_{key_prefix}_paystatus"
            )
        tc4, tc5 = st.columns(2)
        with tc4:
            t_appr_amt = st.number_input(
                f"{label} EXTRA APPROVAL AMOUNT (₹)", min_value=0.0, step=100.0,
                value=num(alloc.get(f"{key_prefix}_extra_approval_amount", 0)),
                key=f"solar_{key_prefix}_apprvamt"
            )
        with tc5:
            t_appr_stat = st.selectbox(
                f"{label} EXTRA APPROVAL STATUS", ["Pending", "Paid"],
                index=(1 if alloc.get(f"{key_prefix}_extra_approval_status") == "Paid" else 0),
                key=f"solar_{key_prefix}_apprvstat"
            )
        return {
            f"{key_prefix}_team_name": t_name if t_name != "Select" else "",
            f"{key_prefix}_charge_amount": t_charge,
            f"{key_prefix}_payment_status": t_pay,
            f"{key_prefix}_extra_approval_amount": t_appr_amt,
            f"{key_prefix}_extra_approval_status": t_appr_stat,
        }

    civil_data = team_section("CIVIL", "civil", alloc_row)
    electrical_data = team_section("ELECTRICAL", "electrical", alloc_row)
    transport_data = team_section("TRANSPORTER", "transport", alloc_row)

    st.markdown('<div class="modal-section-title">📝 REMARKS</div>', unsafe_allow_html=True)
    remarks = st.text_area("REMARKS", value=alloc_row.get("remarks", ""), key="solar_remarks", height=80)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        save_clicked = st.button("💾 Save Allocation", type="primary", use_container_width=True)

    if save_clicked:
        payload = {
            "workspace": st.session_state.get('active_workspace', 'VISPL'),
            "Project ID": site_row.get("Project ID", ""),
            "Site ID": site_row.get("Site ID", ""),
            "Site Name": site_row.get("Site Name", ""),
            "Cluster": site_row.get("Cluster", ""),
            "remarks": remarks,
        }
        payload.update(civil_data)
        payload.update(electrical_data)
        payload.update(transport_data)

        try:
            existing = supabase.table("solar_team_allocation") \
                .select("id") \
                .eq("workspace", payload["workspace"]) \
                .eq("Project ID", payload["Project ID"]) \
                .execute()
            if existing.data:
                supabase.table("solar_team_allocation").update(payload).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("solar_team_allocation").insert(payload).execute()
            st.success("✅ Solar Team Allocation Saved!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error saving allocation: {e}")

# --- TOP BANNER ---
active_ws_display = st.session_state.get('active_workspace', 'VISPL')
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #f59e0b 0%, #ec4899 50%, #8b5cf6 100%); padding: 15px 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);">
        <h1 style="margin: 0; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 3px; font-size: 2.5rem; text-transform: uppercase;">
            ☀️ SOLAR PROJECT — {active_ws_display}
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 5. FETCH SOLAR SITES (Project Name = Solar) FROM site_data ---
# Using ilike (case-insensitive) + client-side strip check so existing records match
# even if Project Name was saved as "SOLAR", " Solar ", "solar", etc.
active_ws = st.session_state.get('active_workspace', 'VISPL')
try:
    site_res = supabase.table("site_data").select("*").eq("workspace", active_ws).ilike("Project Name", "%solar%").execute()
    site_data = site_res.data if site_res.data else []
    # Extra safety: exact-ish match client side (trim + case-insensitive), so partial
    # matches from ilike don't wrongly slip in, only true "Solar" values pass.
    site_data = [
        r for r in site_data
        if str(r.get("Project Name", "")).strip().lower() == "solar"
    ]
except Exception:
    site_data = []

# --- DEBUG HELPER: agar phir bhi blank aaye, yeh dikhayega Project Name column mein
# actually kya values save hain, taaki pata chale spelling kya hai ---
if not site_data:
    try:
        all_ws_res = supabase.table("site_data").select("Project Name").eq("workspace", active_ws).execute()
        distinct_pn = sorted(set(str(r.get("Project Name", "")).strip() for r in (all_ws_res.data or []) if str(r.get("Project Name", "")).strip()))
        if distinct_pn:
            st.info(f"ℹ️ Koi 'Solar' site nahi mili. Aapke workspace mein 'Project Name' column ki actual values hain: {', '.join(distinct_pn)}")
    except Exception:
        pass

try:
    alloc_res = supabase.table("solar_team_allocation").select("*").eq("workspace", active_ws).execute()
    alloc_data = alloc_res.data if alloc_res.data else []
except Exception:
    alloc_data = []

alloc_map = {row.get("Project ID", ""): row for row in alloc_data}

df = pd.DataFrame(site_data) if site_data else pd.DataFrame(
    columns=["id", "Project ID", "Site ID", "Site Name", "Cluster", "Site Status"]
)

if 'created_at' in df.columns and not df.empty:
    df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.sort_values(by='created_at_dt', ascending=False).drop(columns=['created_at_dt']).reset_index(drop=True)
elif not df.empty:
    df = df.iloc[::-1].reset_index(drop=True)

# --- 5.5 SUMMARY CARDS ---
total_sites = len(df)
civil_total = sum(num(a.get("civil_charge_amount")) for a in alloc_data)
electrical_total = sum(num(a.get("electrical_charge_amount")) for a in alloc_data)
transport_total = sum(num(a.get("transport_charge_amount")) for a in alloc_data)
approval_total = sum(
    num(a.get("civil_extra_approval_amount")) + num(a.get("electrical_extra_approval_amount")) + num(a.get("transport_extra_approval_amount"))
    for a in alloc_data
)
pending_count = 0
for a in alloc_data:
    for k in ["civil_payment_status", "electrical_payment_status", "transport_payment_status"]:
        if a.get(k, "Pending") != "Paid":
            pending_count += 1

s1, s2, s3, s4, s5 = st.columns(5)
with s1: st.markdown(f'<div class="solar-card"><div class="label">Total Solar Sites</div><div class="value">{total_sites}</div></div>', unsafe_allow_html=True)
with s2: st.markdown(f'<div class="solar-card"><div class="label">Civil Charges (₹)</div><div class="value">{civil_total:,.0f}</div></div>', unsafe_allow_html=True)
with s3: st.markdown(f'<div class="solar-card"><div class="label">Electrical Charges (₹)</div><div class="value">{electrical_total:,.0f}</div></div>', unsafe_allow_html=True)
with s4: st.markdown(f'<div class="solar-card"><div class="label">Transport Charges (₹)</div><div class="value">{transport_total:,.0f}</div></div>', unsafe_allow_html=True)
with s5: st.markdown(f'<div class="solar-card"><div class="label">Pending Payments</div><div class="value">{pending_count}</div></div>', unsafe_allow_html=True)

st.markdown(f"<p style='color:#94a3b8; margin-top:10px;'>💰 Total Extra Approval Charges (all teams): <b style='color:#f59e0b;'>₹ {approval_total:,.0f}</b></p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. SEARCH + EXPORT ---
col_title, col_search, col_export = st.columns([5, 3, 1.5])
with col_title:
    st.markdown("##### 🗄️ Solar Project Sites")
with col_search:
    search_query = st_keyup("Search", placeholder="🔍 Search solar sites...", label_visibility="collapsed", key="solar_search")
with col_export:
    export_clicked = st.button("📥 Export", use_container_width=True)

if search_query and not df.empty:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df = df[mask]

if export_clicked and not df.empty:
    rows = []
    for _, r in df.iterrows():
        a = alloc_map.get(r.get("Project ID", ""), {})
        rows.append({
            "Project ID": r.get("Project ID", ""),
            "Site ID": r.get("Site ID", ""),
            "Site Name": r.get("Site Name", ""),
            "Cluster": r.get("Cluster", ""),
            "Site Status": r.get("Site Status", ""),
            "Civil Team": a.get("civil_team_name", ""),
            "Civil Charge": num(a.get("civil_charge_amount")),
            "Civil Payment": a.get("civil_payment_status", ""),
            "Civil Extra Approval": num(a.get("civil_extra_approval_amount")),
            "Civil Approval Status": a.get("civil_extra_approval_status", ""),
            "Electrical Team": a.get("electrical_team_name", ""),
            "Electrical Charge": num(a.get("electrical_charge_amount")),
            "Electrical Payment": a.get("electrical_payment_status", ""),
            "Electrical Extra Approval": num(a.get("electrical_extra_approval_amount")),
            "Electrical Approval Status": a.get("electrical_extra_approval_status", ""),
            "Transport Team": a.get("transport_team_name", ""),
            "Transport Charge": num(a.get("transport_charge_amount")),
            "Transport Payment": a.get("transport_payment_status", ""),
            "Transport Extra Approval": num(a.get("transport_extra_approval_amount")),
            "Transport Approval Status": a.get("transport_extra_approval_status", ""),
            "Remarks": a.get("remarks", ""),
        })
    export_df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Solar Project')
    st.download_button(
        label="📊 Download Solar_Project_Export.xlsx",
        data=buffer.getvalue(),
        file_name="Solar_Project_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )

# --- 7. PAGINATION ---
rows_per_page = 10
total_rows = len(df)
total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1

if st.session_state.solar_current_page > total_pages:
    st.session_state.solar_current_page = total_pages
elif st.session_state.solar_current_page < 1:
    st.session_state.solar_current_page = 1

start_idx = (st.session_state.solar_current_page - 1) * rows_per_page
end_idx = start_idx + rows_per_page
df_page = df.iloc[start_idx:end_idx].copy()

COL_RATIOS = [0.4, 1.2, 1.5, 1.0, 1.2, 1.0, 1.2, 1.2, 1.2, 1.1, 1.1, 0.6]
COL_LABELS = ["#", "SITE ID", "SITE NAME", "CLUSTER", "PROJECT ID", "SITE STATUS",
              "CIVIL", "ELECTRICAL", "TRANSPORT", "TOTAL CHARGE (₹)", "TOTAL APPROVAL (₹)", "⚙️"]

with st.container(key="solar_table_wrap", height=560):
    if df_page.empty:
        st.info("Koi Solar site nahi mili. Site Data Hub mein 'Operator' = Solar select karke site add karein.")
    else:
        h_cols = st.columns(COL_RATIOS)
        for h_col, label in zip(h_cols, COL_LABELS):
            h_col.markdown(f"<div class='tbl-cell tbl-head'>{label}</div>", unsafe_allow_html=True)

        for page_pos, (_, row) in enumerate(df_page.iterrows()):
            row_dict = row.to_dict()
            proj_id = str(row_dict.get("Project ID", ""))
            alloc = alloc_map.get(proj_id, {})
            serial_no = start_idx + page_pos + 1

            civil_charge = num(alloc.get("civil_charge_amount"))
            electrical_charge = num(alloc.get("electrical_charge_amount"))
            transport_charge = num(alloc.get("transport_charge_amount"))
            total_charge = civil_charge + electrical_charge + transport_charge

            total_approval = (
                num(alloc.get("civil_extra_approval_amount")) +
                num(alloc.get("electrical_extra_approval_amount")) +
                num(alloc.get("transport_extra_approval_amount"))
            )

            rcols = st.columns(COL_RATIOS)
            rcols[0].markdown(f"<div class='tbl-cell tbl-serial'>{serial_no}</div>", unsafe_allow_html=True)
            rcols[1].markdown(f"<div class='tbl-cell'>{row_dict.get('Site ID','') or '-'}</div>", unsafe_allow_html=True)
            rcols[2].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Name','') or '-'}</div>", unsafe_allow_html=True)
            rcols[3].markdown(f"<div class='tbl-cell'>{row_dict.get('Cluster','') or '-'}</div>", unsafe_allow_html=True)
            rcols[4].markdown(f"<div class='tbl-cell'>{proj_id or '-'}</div>", unsafe_allow_html=True)
            rcols[5].markdown(f"<div class='tbl-cell'>{row_dict.get('Site Status','') or '-'}</div>", unsafe_allow_html=True)
            rcols[6].markdown(pay_badge(alloc.get("civil_payment_status", "")), unsafe_allow_html=True)
            rcols[7].markdown(pay_badge(alloc.get("electrical_payment_status", "")), unsafe_allow_html=True)
            rcols[8].markdown(pay_badge(alloc.get("transport_payment_status", "")), unsafe_allow_html=True)
            rcols[9].markdown(f"<div class='tbl-cell'>{total_charge:,.0f}</div>", unsafe_allow_html=True)
            rcols[10].markdown(f"<div class='tbl-cell'>{total_approval:,.0f}</div>", unsafe_allow_html=True)
            with rcols[11]:
                if st.button("⚙️", key=f"solar_mgr_{row_dict.get('id')}", help="Manage Teams", use_container_width=True):
                    manage_solar_teams_dialog(row_dict, alloc)

st.markdown("<br>", unsafe_allow_html=True)

col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
with col_p1:
    if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.solar_current_page == 1), key="solar_prev"):
        st.session_state.solar_current_page -= 1
        st.rerun()
with col_p2:
    st.markdown(f"<div class='page-count'>Page {st.session_state.solar_current_page} of {total_pages} (Total Solar Sites: {total_rows})</div>", unsafe_allow_html=True)
with col_p3:
    if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.solar_current_page == total_pages), key="solar_next"):
        st.session_state.solar_current_page += 1
        st.rerun()
