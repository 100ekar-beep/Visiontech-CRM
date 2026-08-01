import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client, Client

# --- 1. CONNECTION ---
URL = "https://sckyflvukpmdqmdzjzhs.supabase.co"
KEY = "sb_publishable_rAiegSkKYvM0Z9n7sUAI1w_WTgm1S4I" 
supabase: Client = create_client(URL, KEY)

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Indus Site Data", page_icon="📊", layout="wide")

# --- 3. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Inputs & Labels */
    label p, label[data-testid="stWidgetLabel"] p { color: #475569 !important; font-weight: 700 !important; font-size: 0.9rem !important; text-transform: uppercase; }
    [data-testid="stDataFrame"] th { background-color: #1E3A8A !important; color: white !important; font-weight: 700 !important; }

    /* Expanders */
    [data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }
    
    /* Custom Info Cards */
    .info-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }

    /* PREMIUM SIDEBAR NAVIGATION BUTTONS */
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
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important; color: #ffffff !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; border-color: transparent !important;
    }
    div[data-testid="stSidebarNav"] a span { color: inherit !important; }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# 📊 INDUS BASIC DATA
# =====================================================================

st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 30px;'>📊 Indus Site Data</h1>", unsafe_allow_html=True)

with st.form("ind_form_v5"):
    i1, i2, i3 = st.columns(3)
    with i1: in_id = st.text_input("📍 Site ID Search")
    with i2: in_nm = st.text_input("🏢 Site Name Search")
    with i3: 
        st.write("")
        sub_ind = st.form_submit_button("🔍 Search Indus")
    
if sub_ind:
    # --- Bulletproof Search Logic (Will not crash on API Errors) ---
    search_success = False
    res_data = None
    
    tables_to_try = ["Excalation Matrix", "Escalation Matrix", "Indus Data"]
    id_cols_to_try = ["Indus ID", "Site ID", "indus_id", "site_id"]
    name_cols_to_try = ["Site Name", "site_name"]
    
    for t in tables_to_try:
        if search_success: break
        for id_col in id_cols_to_try:
            if search_success: break
            for nm_col in name_cols_to_try:
                try:
                    query = supabase.table(t).select("*")
                    if in_id: query = query.ilike(id_col, f"%{in_id.strip()}%")
                    if in_nm: query = query.ilike(nm_col, f"%{in_nm.strip()}%")
                    res_ind = query.execute()
                    
                    if res_ind.data:
                        res_data = res_ind.data
                        search_success = True
                        break
                    elif not in_id and not in_nm:
                        search_success = True
                        break
                except Exception:
                    pass

    if search_success and res_data:
        df_ind = pd.DataFrame(res_data)
        st.dataframe(df_ind, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("📌 Vertical Site Details")
        row_in = res_data[0]
        
        # Mapping Data Safely for multiple possible column names
        site_id_val = row_in.get('Indus ID', row_in.get('Site ID', row_in.get('indus_id', '-')))
        site_name_val = row_in.get('Site Name', row_in.get('site_name', '-'))
        area_val = row_in.get('Area', row_in.get('Area Name', row_in.get('Site Address', '-')))
        cluster_val = row_in.get('Cluster', '-')
        
        tech_name = row_in.get('Technician Detail', row_in.get('Tech Name', '-'))
        tech_num = row_in.get('Technician Number', row_in.get('Tech Number', '-'))
        
        fse_name = row_in.get('FSE Detail', row_in.get('FSE Name', row_in.get('FSE', '-')))
        fse_num = row_in.get('FSE Number', '-')
        
        aom_name = row_in.get('AOM Detail', row_in.get('AOM Name', '-'))
        aom_num = row_in.get('AOM Number', '-')
        
        lat = row_in.get('Lat', row_in.get('Latitude', row_in.get('latitude', '')))
        lon = row_in.get('Long', row_in.get('longitude', row_in.get('Longitude', '')))
        
        def call_html(label, name, num):
            if num and str(num).strip() not in ['-', '', 'None', 'nan']:
                return f'{label}: **{name}** ({num}) <a href="tel:{num}"><button style="background-color:#3b82f6;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);">📞 Call</button></a>'
            return f'{label}: **{name}** (-)'
        
        # Displaying Only Requested Columns
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        v1, v2 = st.columns(2)
        with v1:
            st.markdown(f"🛰️ **Area** :- {area_val}")
            st.markdown(call_html("👨‍🔧 **Technician Detail**", tech_name, tech_num), unsafe_allow_html=True)
            st.markdown(call_html("👨‍💼 **AOM Detail**", aom_name, aom_num), unsafe_allow_html=True)
        with v2:
            st.markdown(f"📍 **Cluster** :- {cluster_val}")
            st.markdown(call_html("👷 **FSE Detail**", fse_name, fse_num), unsafe_allow_html=True)
            if lat and lon and str(lat).strip() not in ['-', '', 'None', 'nan']:
                maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.markdown(f"📍 **Lat/Long** :- {lat} / {lon} <a href='{maps_url}' target='_blank'><button style='background-color:#ef4444;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>📍 View Map</button></a>", unsafe_allow_html=True)
            else: 
                st.markdown(f"📍 **Lat/Long** :- {lat if lat else '-'} / {lon if lon else '-'}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # --- NEW LOGIC: Team Dropdown & WhatsApp Button ---
        st.markdown("### 💬 Send Details via WhatsApp")
        
        # Fetching Teams from Dropdown Master (Crash-Proof API: is_active filter removed)
        team_res = None
        try:
            team_res = supabase.table("dropdown_master").select("option_value, mobile").eq("category", "Team Name").execute()
        except Exception as e:
            st.error(f"Team Database Error: {e}")
            
        team_dict = {r['option_value']: r['mobile'] for r in team_res.data} if team_res and team_res.data else {}
        
        t_col1, t_col2 = st.columns([3, 2])
        sel_team = t_col1.selectbox("Select Team", ["-- Select Team --"] + list(team_dict.keys()), label_visibility="collapsed")
        
        if sel_team != "-- Select Team --":
            mob = team_dict.get(sel_team, "")
            if mob:
                clean_mob = str(mob).replace("+91", "").replace(" ", "").strip()
                if len(clean_mob) >= 10:
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "N/A"
                    wa_msg = f"Site Details:\n\n*Site ID:* {site_id_val}\n*Site Name:* {site_name_val}\n*Lat:* {lat}\n*Long:* {lon}\n\n*Location Map:*\n{maps_link}"
                    wa_encoded = urllib.parse.quote(wa_msg)
                    wa_url = f"https://wa.me/91{clean_mob}?text={wa_encoded}"
                    
                    t_col2.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:8px 15px; border-radius:8px; font-weight:800; font-size:16px; cursor:pointer; box-shadow: 0 4px 6px -1px rgba(37, 211, 102, 0.4);">💬 Send WhatsApp</button></a>', unsafe_allow_html=True)
                else:
                    t_col2.error("Invalid Mobile Number in Database.")
            else:
                t_col2.warning("Mobile number not found for this team.")
                
    else: 
        st.info("No data found matching your search in the Database. Kripya Site ID theek se check karein.")

st.divider()

# =====================================================================
# 🧭 ROUTE PLAN
# =====================================================================

st.subheader("🧭 Route Plan")
if 'route_list' not in st.session_state: st.session_state.route_list = []

with st.expander("🛠️ Add Sites to Route", expanded=True):
    c1, c2 = st.columns(2)
    with c1: start_coords = st.text_input("🏠 Start Location", value="Lonikand, Pune")
    with c2: end_coords = st.text_input("🏁 End Location", placeholder="e.g. Mumbai")
    
    with st.form("add_site_form", clear_on_submit=True):
        add_sid = st.text_input("📍 Add Site ID")
        if st.form_submit_button("➕ Add to List"):
            if add_sid:
                # --- Crash-proof Route add logic ---
                s_data = None
                tables_to_try = ["Excalation Matrix", "Escalation Matrix", "Indus Data"]
                id_cols_to_try = ["Indus ID", "Site ID", "indus_id", "site_id"]
                
                for t in tables_to_try:
                    if s_data: break
                    for id_col in id_cols_to_try:
                        try:
                            s_res = supabase.table(t).select("*").ilike(id_col, f"%{add_sid.strip()}%").execute()
                            if s_res.data: 
                                s_data = s_res.data[0]
                                break
                        except: pass

                if s_data: 
                    # Data normalization for route table
                    norm_data = {
                        'Site ID': s_data.get('Site ID', s_data.get('Indus ID', s_data.get('indus_id', '-'))),
                        'Site Name': s_data.get('Site Name', s_data.get('site_name', '-')),
                        'Lat': s_data.get('Lat', s_data.get('Latitude', s_data.get('latitude', ''))),
                        'Long': s_data.get('Long', s_data.get('longitude', s_data.get('Longitude', '')))
                    }
                    st.session_state.route_list.append(norm_data)
                    st.success(f"Site {add_sid} added!")
                    st.rerun()
                else: st.error("Site ID not found or Database Error!")

    # --- Current Added Sites List ---
    if st.session_state.route_list:
        st.write("### 📋 Added Sites:")
        temp_df = pd.DataFrame(st.session_state.route_list)[['Site ID', 'Site Name', 'Lat', 'Long']]
        st.dataframe(temp_df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear All Sites", use_container_width=True):
            st.session_state.route_list = []
            st.rerun()

if st.button("🚀 Calculate Best Route (Point-wise)", use_container_width=True, type="primary"):
    if not start_coords or not end_coords or not st.session_state.route_list: 
        st.warning("Please add Start, End and at least one Site!")
    else:
        try:
            # Importing locally to prevent crash if not in requirements.txt
            from geopy.geocoders import Nominatim
            from geopy.distance import geodesic
            
            geolocator = Nominatim(user_agent="vis_route_planner")
            def get_lat_lon(loc):
                if ',' in loc and any(c.isdigit() for c in loc): return [float(x.strip()) for x in loc.split(',')]
                l = geolocator.geocode(loc); return [l.latitude, l.longitude] if l else None
            
            curr_p, end_p = get_lat_lon(start_coords), get_lat_lon(end_coords)
            if not curr_p or not end_p: st.error("Invalid Start or End Location.")
            else:
                unvisited = [s for s in st.session_state.route_list if s.get('Lat') and s.get('Long')]
                final_path = []
                while unvisited:
                    next_s = min(unvisited, key=lambda x: geodesic(curr_p, (float(x['Lat']), float(x['Long']))).km)
                    final_path.append(next_s)
                    curr_p = (float(next_s['Lat']), float(next_s['Long']))
                    unvisited.remove(next_s)
                
                # Showing Sequential Table
                route_results = []
                for i, s in enumerate(final_path, 1):
                    route_results.append({"Stop No": i, "Site ID": s.get('Site ID', '-'), "Name": s.get('Site Name','-')})
                st.table(pd.DataFrame(route_results))
                
                # Point-wise Google Maps Link
                stops = "/".join([f"{s['Lat']},{s['Long']}" for s in final_path])
                gmaps_route = f"https://www.google.com/maps/dir/{start_coords}/{stops}/{end_coords}"
                st.markdown(f'<a href="{gmaps_route}" target="_blank"><button style="width:100%; background-color:#10b981; color:white; border:none; padding:12px; border-radius:8px; font-weight:800; font-size:16px; cursor:pointer; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.4);">🗺️ Open Sequential Route (1-2-3-4)</button></a>', unsafe_allow_html=True)
        except Exception as e: st.error(f"Error: {e} | Ensure 'geopy' is added to requirements.txt file on GitHub.")
