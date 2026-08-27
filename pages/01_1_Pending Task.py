import streamlit as st
import pandas as pd
import numpy as np
import io
import wave
import base64
from datetime import datetime, date, time as dt_time, timedelta
from supabase import create_client, Client

# --- OPTIONAL: streamlit-autorefresh (pip install streamlit-autorefresh) ---
# Used to periodically re-run the page so reminder times can be checked live,
# even if the user isn't clicking anything. Falls back gracefully if missing.
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Pending Activity", page_icon="🔔", layout="wide")

# --- 2. SESSION STATE INIT ---
if 'pa_sound_enabled' not in st.session_state:
    st.session_state.pa_sound_enabled = True
if 'pa_autocheck_enabled' not in st.session_state:
    st.session_state.pa_autocheck_enabled = True
if 'active_reminder' not in st.session_state:
    st.session_state.active_reminder = None
if 'pa_search' not in st.session_state:
    st.session_state.pa_search = ""
if 'pa_show_form_dialog' not in st.session_state:
    st.session_state.pa_show_form_dialog = False
if 'pa_edit_row' not in st.session_state:
    st.session_state.pa_edit_row = None

# --- 3. LAVISH CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 45%, #1a1035 100%); color: #f8fafc; font-family: 'Inter', sans-serif; }

    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 800 !important;
        padding: 0.55rem 1.1rem;
        transition: all 0.25s ease;
        box-shadow: 0 4px 10px -2px rgba(139, 92, 246, 0.35);
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 12px 20px -6px rgba(139, 92, 246, 0.55); }
    div.stButton > button p, div.stButton > button span, div.stButton > button div { color: #ffffff !important; font-weight: 800 !important; }

    div[data-testid="stDialog"] > div {
        background: rgba(15, 23, 42, 0.97);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 { color:#ffffff !important; font-weight:800 !important; }
    div[data-testid="stDialog"] p, div[data-testid="stDialog"] div[data-testid="stCaptionContainer"] p { color:#e2e8f0 !important; }
    label p, label[data-testid="stWidgetLabel"] p { color:#ffffff !important; font-weight:600 !important; letter-spacing:0.4px; }

    /* ---------- HERO HEADER ---------- */
    .pa-hero {
        background: linear-gradient(90deg, #f43f5e 0%, #8b5cf6 50%, #3b82f6 100%);
        padding: 22px 28px;
        border-radius: 18px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px -8px rgba(139,92,246,0.5);
        border: 1px solid rgba(255,255,255,0.15);
        position: relative;
        overflow: hidden;
    }
    .pa-hero h1 { margin:0; color:#ffffff !important; font-weight:900 !important; letter-spacing:2px; font-size:2.1rem; text-transform:uppercase; }
    .pa-hero p { margin:4px 0 0 0; color:rgba(255,255,255,0.9); font-weight:600; font-size:0.95rem; }

    /* ---------- STAT CARDS ---------- */
    .pa-stat {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 16px 18px;
        text-align: center;
        transition: all 0.25s ease;
    }
    .pa-stat:hover { transform: translateY(-3px); border-color: rgba(139,92,246,0.5); }
    .pa-stat-num { font-size: 2rem; font-weight: 900; margin: 0; }
    .pa-stat-label { font-size: 0.78rem; color: #94a3b8; font-weight:700; letter-spacing:0.6px; text-transform:uppercase; margin-top:4px; }

    /* ---------- LAVISH ACTIVITY CARD (table replacement) ---------- */
    .pa-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.015) 100%);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: all 0.25s ease;
        position: relative;
    }
    .pa-card:hover { border-color: rgba(139,92,246,0.55); box-shadow: 0 12px 26px -10px rgba(139,92,246,0.4); transform: translateY(-2px); }
    .pa-card.important { border: 1px solid rgba(244,63,94,0.55); background: linear-gradient(135deg, rgba(244,63,94,0.10) 0%, rgba(255,255,255,0.02) 100%); }

    .pa-title-row { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px; }
    .pa-activity-name { font-size: 1.15rem; font-weight: 900; color:#ffffff; }

    .pa-badge {
        display:inline-block; padding: 3px 11px; border-radius: 20px;
        font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px; text-transform:uppercase;
    }
    .pa-badge-important { background: rgba(244,63,94,0.20); color:#fb7185; border:1px solid rgba(244,63,94,0.4); animation: pa-pulse 1.6s infinite; }
    .pa-badge-reminder { background: rgba(59,130,246,0.18); color:#60a5fa; border:1px solid rgba(59,130,246,0.35); }
    .pa-badge-days-ok { background: rgba(34,197,94,0.18); color:#4ade80; }
    .pa-badge-days-warn { background: rgba(234,179,8,0.18); color:#facc15; }
    .pa-badge-days-late { background: rgba(239,68,68,0.18); color:#f87171; }

    @keyframes pa-pulse { 0% { box-shadow: 0 0 0 0 rgba(244,63,94,0.55);} 70% { box-shadow: 0 0 0 8px rgba(244,63,94,0);} 100% { box-shadow: 0 0 0 0 rgba(244,63,94,0);} }

    .pa-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px 20px; margin-top: 6px; }
    .pa-field-label { color:#94a3b8; font-size:0.70rem; font-weight:800; letter-spacing:0.6px; text-transform:uppercase; margin-bottom:2px; }
    .pa-field-value { color:#e2e8f0; font-size:0.9rem; font-weight:600; word-break: break-word; }
    .pa-remark-box { margin-top:10px; background: rgba(255,255,255,0.03); border-left: 3px solid #8b5cf6; padding: 8px 12px; border-radius: 6px; color:#cbd5e1; font-size:0.85rem; font-style: italic; }

    /* ---------- CLOSED CARD ---------- */
    .pa-card-closed { background: rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 14px 18px; margin-bottom: 10px; opacity: 0.75; }
    .pa-card-closed .pa-activity-name { text-decoration: line-through; color:#94a3b8; font-size:1.0rem; }

    /* ---------- REMINDER ALARM POPUP ---------- */
    .pa-alarm-wrap { text-align:center; padding: 10px 6px 6px 6px; }
    .pa-alarm-icon { font-size: 3.2rem; animation: pa-shake 0.6s infinite; }
    @keyframes pa-shake { 0%,100%{ transform: rotate(0deg);} 25%{ transform: rotate(-12deg);} 75%{ transform: rotate(12deg);} }
    .pa-alarm-title { font-size: 1.6rem; font-weight: 900; letter-spacing: 1px; background: linear-gradient(90deg,#f43f5e,#facc15); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 8px 0 2px 0; text-transform: uppercase; }
    .pa-alarm-activity { font-size: 2.1rem; font-weight: 900; color: #ffffff; margin: 10px 0; padding: 14px; border-radius: 14px; background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.4); }
    .pa-alarm-info-row { display:flex; justify-content:space-between; padding:6px 4px; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size:0.95rem; }
    .pa-alarm-info-row:last-child { border-bottom:none; }
    .pa-alarm-label { color:#94a3b8; font-weight:700; }
    .pa-alarm-value { color:#f1f5f9; font-weight:700; text-align:right; }

    .pa-toolbar-note { color:#94a3b8; font-size:0.8rem; margin-top:4px; }

    /* =========================================================
       PREMIUM SIDEBAR NAVIGATION BUTTONS (same as other pages)
       ========================================================= */
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

    /* =========================================================
       DATE & TIME PICKER — make Calendar/Clock icons clearly visible
       ========================================================= */
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input {
        color: #ffffff !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(139,92,246,0.45) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stDateInput"] svg,
    div[data-testid="stTimeInput"] svg {
        fill: #a78bfa !important;
        width: 20px !important;
        height: 20px !important;
    }
    div[data-testid="stDateInput"] > div > div,
    div[data-testid="stTimeInput"] > div > div {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 8px !important;
    }
    /* The pop-up calendar / clock panel itself */
    div[data-baseweb="popover"] div[data-baseweb="calendar"],
    div[data-baseweb="popover"] ul {
        background: #1e1b4b !important;
        border: 1px solid rgba(139,92,246,0.5) !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 30px -8px rgba(0,0,0,0.6) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. SUPABASE CONNECTION ---
SUPABASE_URL = "https://bpwcraaasqjgmwpclxfb.supabase.co"
SUPABASE_KEY = "sb_publishable_5NFP7vDScEQfQL-9OY67Xw_0ZcPfgwz"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()
TABLE_NAME = "pending_activity"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# --- 5. IN-MEMORY ALARM BEEP (10s beep-beep pattern, generated on the fly, no external files) ---
@st.cache_data(show_spinner=False)
def generate_beep_base64(duration_sec=10, freq=880, pulse_on=0.35, pulse_off=0.20, sample_rate=22050, volume=0.55):
    n = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    cycle = pulse_on + pulse_off
    phase = np.mod(t, cycle)
    envelope = (phase < pulse_on).astype(np.float32)
    # small fade in/out per pulse to avoid harsh clicks
    wave_data = volume * envelope * np.sin(2 * np.pi * freq * t)
    audio = (wave_data * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def render_alarm_audio():
    """Injects an autoplaying <audio> tag directly into the page DOM (not an iframe),
    so it shares the browser's audio-unlock state with the rest of the app."""
    if not st.session_state.pa_sound_enabled:
        return
    b64_audio = generate_beep_base64()
    st.markdown(f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
        </audio>
    """, unsafe_allow_html=True)


# --- 6. DATA HELPERS ---
# NOTE: This page is intentionally NOT scoped by workspace/company.
# Every login (any company) sees and shares the exact same task list.
def fetch_activities():
    try:
        res = supabase.table(TABLE_NAME).select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        st.toast(f"Database Error: {e}", icon="❌")
        return []


def parse_ddmmyyyy(val):
    try:
        return datetime.strptime(str(val).strip(), "%d/%m/%Y")
    except Exception:
        return datetime.min


def days_pending_badge(raise_date_str):
    d = parse_ddmmyyyy(raise_date_str)
    if d == datetime.min:
        return "-", "pa-badge-days-ok"
    days = (datetime.now() - d).days
    if days <= 2:
        return f"{days}d", "pa-badge-days-ok"
    elif days <= 7:
        return f"{days}d", "pa-badge-days-warn"
    else:
        return f"{days}d", "pa-badge-days-late"


def reminder_summary_text(row):
    r_type = str(row.get("reminder_type", "")).strip()
    r_time = str(row.get("reminder_time", "")).strip()
    if not r_type:
        return "No reminder set"
    if r_type == "Daily":
        return f"Daily @ {r_time}"
    elif r_type == "Weekly":
        return f"Every {row.get('reminder_day','-')} @ {r_time}"
    elif r_type == "Monthly":
        return f"Monthly on {row.get('reminder_date_of_month','-')} @ {r_time}"
    elif r_type == "Specific Date":
        return f"{row.get('reminder_specific_date','-')} @ {r_time}"
    return r_type


# --- 7. REMINDER ENGINE: check all pending activities against current time ---
def check_reminders_and_trigger(pending_records):
    if st.session_state.get("active_reminder"):
        return  # a popup is already showing — don't stack another one

    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")
    current_time_str = now.strftime("%H:%M")
    weekday_name = now.strftime("%A")
    day_of_month = now.day

    for row in pending_records:
        r_type = str(row.get("reminder_type", "")).strip()
        r_time = str(row.get("reminder_time", "")).strip()
        if not r_type or not r_time or r_time != current_time_str:
            continue

        last_notified = str(row.get("last_notified", "")).strip()
        if last_notified == f"{today_str} {current_time_str}":
            continue  # already fired for this exact minute

        should_fire = False
        if r_type == "Daily":
            should_fire = True
        elif r_type == "Weekly":
            should_fire = str(row.get("reminder_day", "")).strip() == weekday_name
        elif r_type == "Monthly":
            try:
                should_fire = int(row.get("reminder_date_of_month", 0)) == day_of_month
            except Exception:
                should_fire = False
        elif r_type == "Specific Date":
            should_fire = str(row.get("reminder_specific_date", "")).strip() == today_str

        if should_fire:
            try:
                supabase.table(TABLE_NAME).update(
                    {"last_notified": f"{today_str} {current_time_str}"}
                ).eq("id", row["id"]).execute()
            except Exception:
                pass
            st.session_state["active_reminder"] = row
            break


# --- 8. ADD / EDIT ACTIVITY DIALOG ---
@st.dialog("➕ Add New Pending Activity", width="large")
def add_activity_dialog(edit_row=None):
    is_edit = edit_row is not None
    st.caption("Fill the details below — every field helps the team track this task properly.")

    activity_name = st.text_input("ACTIVITY NAME *", value=edit_row.get('activity_name', '') if is_edit else "", placeholder="e.g. SMPS Commissioning Follow-up")

    c1, c2 = st.columns(2)
    with c1:
        indus_resp = st.text_input("INDUS RESPONSIBLE *", value=edit_row.get('indus_responsible', '') if is_edit else "")
    with c2:
        vis_resp = st.text_input("VIS RESPONSIBLE *", value=edit_row.get('vis_responsible', '') if is_edit else "")

    c3, c4 = st.columns(2)
    with c3:
        default_raise_date = parse_ddmmyyyy(edit_row.get('raise_date')) if is_edit and edit_row.get('raise_date') else datetime.now()
        if default_raise_date == datetime.min:
            default_raise_date = datetime.now()
        raise_date = st.date_input("RAISE DATE * 📅", value=default_raise_date.date())
    with c4:
        important = st.checkbox("⭐ Mark as IMPORTANT", value=bool(edit_row.get('important', False)) if is_edit else False)

    remark = st.text_area("REMARK", value=edit_row.get('remark', '') if is_edit else "", height=90, placeholder="Any notes about this activity...")

    st.markdown('<div class="modal-section-title" style="color:#94a3b8; font-size:0.85rem; font-weight:700; letter-spacing:1px; margin-top:12px; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:5px;">⏰ REMINDER SETTINGS</div>', unsafe_allow_html=True)

    r_type_opts = ["Daily", "Weekly", "Monthly", "Specific Date"]
    default_r_type_idx = r_type_opts.index(edit_row.get('reminder_type')) if (is_edit and edit_row.get('reminder_type') in r_type_opts) else 0
    r_type = st.selectbox("REMINDER TYPE *", r_type_opts, index=default_r_type_idx)

    rc1, rc2 = st.columns(2)
    reminder_day = ""
    reminder_dom = None
    reminder_sdate = ""

    if r_type == "Weekly":
        with rc1:
            default_day_idx = WEEKDAYS.index(edit_row.get('reminder_day')) if (is_edit and edit_row.get('reminder_day') in WEEKDAYS) else 0
            reminder_day = st.selectbox("DAY OF WEEK *", WEEKDAYS, index=default_day_idx)
    elif r_type == "Monthly":
        with rc1:
            default_dom = int(edit_row.get('reminder_date_of_month')) if (is_edit and str(edit_row.get('reminder_date_of_month', '')).isdigit()) else 1
            reminder_dom = st.number_input("DATE OF MONTH (1–31) *", min_value=1, max_value=31, value=default_dom)
    elif r_type == "Specific Date":
        with rc1:
            default_sdate = parse_ddmmyyyy(edit_row.get('reminder_specific_date')) if is_edit and edit_row.get('reminder_specific_date') else datetime.now()
            if default_sdate == datetime.min:
                default_sdate = datetime.now()
            sdate = st.date_input("SPECIFIC DATE * 📅", value=default_sdate.date())
            reminder_sdate = sdate.strftime("%d/%m/%Y")

    with rc2:
        default_time = dt_time(9, 0)
        if is_edit and edit_row.get('reminder_time'):
            try:
                default_time = datetime.strptime(edit_row.get('reminder_time'), "%H:%M").time()
            except Exception:
                pass
        reminder_time_val = st.time_input("REMINDER TIME * 🕐", value=default_time)
        st.caption("👆 Click karke clock se time set karein")

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn0, col_btn1, col_btn2 = st.columns([6, 2, 2])
    with col_btn0:
        cancelled = st.button("❌ Cancel", use_container_width=True)
    with col_btn2:
        btn_label = "💾 Update" if is_edit else "💾 Save Activity"
        submitted = st.button(btn_label, type="primary", use_container_width=True)

    if cancelled:
        st.session_state.pa_show_form_dialog = False
        st.session_state.pa_edit_row = None
        st.rerun()

    if submitted:
        has_error = False
        if not activity_name.strip():
            st.error("⚠️ Activity Name dalna compulsory hai!")
            has_error = True
        if not indus_resp.strip() or not vis_resp.strip():
            st.error("⚠️ Indus Responsible aur VIS Responsible dono dalna compulsory hai!")
            has_error = True
        if r_type == "Weekly" and not reminder_day:
            st.error("⚠️ Weekly reminder ke liye Day of Week select karein!")
            has_error = True
        if r_type == "Specific Date" and not reminder_sdate:
            st.error("⚠️ Specific Date reminder ke liye date select karein!")
            has_error = True

        if not has_error:
            payload = {
                "activity_name": activity_name.strip(),
                "indus_responsible": indus_resp.strip(),
                "vis_responsible": vis_resp.strip(),
                "raise_date": raise_date.strftime("%d/%m/%Y"),
                "remark": remark,
                "important": bool(important),
                "reminder_type": r_type,
                "reminder_day": reminder_day,
                "reminder_date_of_month": int(reminder_dom) if reminder_dom else None,
                "reminder_specific_date": reminder_sdate,
                "reminder_time": reminder_time_val.strftime("%H:%M"),
                "last_notified": "",
            }
            try:
                if is_edit:
                    supabase.table(TABLE_NAME).update(payload).eq("id", edit_row['id']).execute()
                    st.success("✅ Activity Successfully Updated!")
                else:
                    payload["status"] = "Pending"
                    supabase.table(TABLE_NAME).insert(payload).execute()
                    st.success("✅ Activity Successfully Added!")
                st.session_state.pa_show_form_dialog = False
                st.session_state.pa_edit_row = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Saving Activity: {e}")


# --- 9. REMINDER ALARM POPUP DIALOG ---
@st.dialog("🔔 TASK REMINDER!", width="large")
def reminder_popup_dialog(row):
    render_alarm_audio()

    days_txt, days_cls = days_pending_badge(row.get('raise_date', ''))

    st.markdown(f"""
        <div class="pa-alarm-wrap">
            <div class="pa-alarm-icon">⏰</div>
            <div class="pa-alarm-title">It's Time! Don't Forget This Task</div>
            <div class="pa-alarm-activity">{row.get('activity_name', '')}</div>
            <div class="pa-alarm-info-row"><span class="pa-alarm-label">👷 Indus Responsible</span><span class="pa-alarm-value">{row.get('indus_responsible','') or '-'}</span></div>
            <div class="pa-alarm-info-row"><span class="pa-alarm-label">🏢 VIS Responsible</span><span class="pa-alarm-value">{row.get('vis_responsible','') or '-'}</span></div>
            <div class="pa-alarm-info-row"><span class="pa-alarm-label">📅 Raised On</span><span class="pa-alarm-value">{row.get('raise_date','') or '-'} ({days_txt} ago)</span></div>
            <div class="pa-alarm-info-row"><span class="pa-alarm-label">⭐ Important</span><span class="pa-alarm-value">{"YES 🔥" if row.get('important') else "No"}</span></div>
        </div>
    """, unsafe_allow_html=True)

    if str(row.get('remark', '')).strip():
        st.markdown(f'<div class="pa-remark-box">📝 {row.get("remark","")}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("😴 +5 min", use_container_width=True):
            _snooze_reminder(row, minutes=5)
    with b2:
        if st.button("⏳ +30 min", use_container_width=True):
            _snooze_reminder(row, minutes=30)
    with b3:
        if st.button("🕐 +1 hour", use_container_width=True):
            _snooze_reminder(row, minutes=60)
    with b4:
        if st.button("✅ Close Task", type="primary", use_container_width=True):
            try:
                supabase.table(TABLE_NAME).update({
                    "status": "Closed",
                    "closed_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }).eq("id", row['id']).execute()
                st.session_state["active_reminder"] = None
                st.success("✅ Task Closed!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Closing Task: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙️ Full Reschedule (change reminder type/day/date/time)"):
        r_type_opts = ["Daily", "Weekly", "Monthly", "Specific Date"]
        cur_type_idx = r_type_opts.index(row.get('reminder_type')) if row.get('reminder_type') in r_type_opts else 0
        new_type = st.selectbox("New Reminder Type", r_type_opts, index=cur_type_idx, key="resch_type")

        new_day, new_dom, new_sdate = "", None, ""
        rc1, rc2 = st.columns(2)
        if new_type == "Weekly":
            with rc1:
                cur_day_idx = WEEKDAYS.index(row.get('reminder_day')) if row.get('reminder_day') in WEEKDAYS else 0
                new_day = st.selectbox("Day of Week", WEEKDAYS, index=cur_day_idx, key="resch_day")
        elif new_type == "Monthly":
            with rc1:
                cur_dom = int(row.get('reminder_date_of_month')) if str(row.get('reminder_date_of_month', '')).isdigit() else 1
                new_dom = st.number_input("Date of Month", min_value=1, max_value=31, value=cur_dom, key="resch_dom")
        elif new_type == "Specific Date":
            with rc1:
                new_sdate_val = st.date_input("Specific Date 📅", value=datetime.now().date(), key="resch_sdate")
                new_sdate = new_sdate_val.strftime("%d/%m/%Y")
        with rc2:
            new_time = st.time_input("Reminder Time 🕐", value=dt_time(9, 0), key="resch_time")

        if st.button("🔄 Save New Schedule", use_container_width=True, key="resch_save"):
            try:
                supabase.table(TABLE_NAME).update({
                    "reminder_type": new_type,
                    "reminder_day": new_day,
                    "reminder_date_of_month": int(new_dom) if new_dom else None,
                    "reminder_specific_date": new_sdate,
                    "reminder_time": new_time.strftime("%H:%M"),
                    "last_notified": "",
                }).eq("id", row['id']).execute()
                st.session_state["active_reminder"] = None
                st.success("✅ Reminder Rescheduled!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Rescheduling: {e}")


def _snooze_reminder(row, minutes):
    try:
        new_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")
        supabase.table(TABLE_NAME).update({
            "reminder_time": new_time,
            "last_notified": "",
        }).eq("id", row['id']).execute()
        st.session_state["active_reminder"] = None
        st.toast(f"⏰ Snoozed for {minutes} minutes!", icon="😴")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error Snoozing: {e}")


# ==============================================================
# --- TRIGGER OPEN DIALOG (ONLY ONE AT A TIME — Streamlit does not
#     allow two @st.dialog popups to open in the same run, so the
#     alarm reminder always takes priority over the Add/Edit form).
# ==============================================================
if st.session_state.get("active_reminder"):
    reminder_popup_dialog(st.session_state["active_reminder"])
elif st.session_state.get("pa_show_form_dialog"):
    add_activity_dialog(edit_row=st.session_state.get("pa_edit_row"))

# --- HERO HEADER ---
# This page is shared across ALL companies/workspaces — every login sees the same tasks.
st.markdown("""
    <div class="pa-hero">
        <h1>🔔 Pending Activity Tracker</h1>
        <p>🌐 Shared Across All Companies &nbsp;•&nbsp; Never miss a follow-up again</p>
    </div>
""", unsafe_allow_html=True)

# --- TOP TOOLBAR ---
tc1, tc2, tc3, tc4, tc5 = st.columns([2, 1.3, 1.3, 1.3, 1.3])
with tc1:
    if st.button("➕ Add New Activity", use_container_width=True):
        st.session_state.pa_edit_row = None
        st.session_state.pa_show_form_dialog = True
        st.rerun()
with tc2:
    sound_label = "🔊 Sound: ON" if st.session_state.pa_sound_enabled else "🔇 Sound: OFF"
    if st.button(sound_label, use_container_width=True):
        st.session_state.pa_sound_enabled = not st.session_state.pa_sound_enabled
        st.rerun()
with tc3:
    autocheck_label = "🟢 Auto-Check: ON" if st.session_state.pa_autocheck_enabled else "⏸️ Auto-Check: OFF"
    if st.button(autocheck_label, use_container_width=True):
        st.session_state.pa_autocheck_enabled = not st.session_state.pa_autocheck_enabled
        st.rerun()
with tc4:
    if st.button("🧪 Test Sound", use_container_width=True, help="Sirf sound/popup check karne ke liye — ise time se koi lena dena nahi. Real reminders sirf unke set kiye gaye exact time par hi khulte hain."):
        st.session_state["active_reminder"] = {
            "id": "test",
            "activity_name": "🔔 Manual Test (time-based nahi hai)",
            "indus_responsible": "Demo Indus",
            "vis_responsible": "Demo VIS",
            "raise_date": datetime.now().strftime("%d/%m/%Y"),
            "remark": "Yeh sirf ek MANUAL test hai — sound/popup check karne ke liye. Iska reminder time se koi lena dena nahi. Real activities sirf unke set kiye gaye exact time par hi khulti/bajti hain.",
            "important": True,
            "reminder_type": "Daily",
            "reminder_time": datetime.now().strftime("%H:%M"),
        }
        st.rerun()
with tc5:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

st.markdown('<p class="pa-toolbar-note">💡 Pehli baar page open karte hi "Sound" ya koi bhi button ek baar click karein — isse browser is tab me audio alerts allow kar dega.</p>', unsafe_allow_html=True)

# --- AUTO-REFRESH (so reminders fire even without manual interaction) ---
# Paused automatically while:
#   1) the Add/Edit form is open (so it never interrupts you mid-typing), or
#   2) a reminder alarm popup is already open (so it doesn't keep re-opening
#      and re-beeping every refresh cycle — it should ring ONCE and then wait
#      for you to Close/Snooze/Reschedule).
form_is_open = bool(st.session_state.get("pa_show_form_dialog"))
reminder_is_open = bool(st.session_state.get("active_reminder"))
pause_autocheck = form_is_open or reminder_is_open

if st.session_state.pa_autocheck_enabled and not pause_autocheck:
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=20000, key="pa_autorefresh")
    else:
        st.info("ℹ️ Live auto-check ke liye `pip install streamlit-autorefresh` karein. Abhi ke liye 'Refresh Now' button use karein.")
elif form_is_open:
    st.caption("⏸️ Form khula hone tak auto-check pause hai — aaram se bharo, koi disturbance nahi hoga.")
elif reminder_is_open:
    st.caption("🔔 Reminder popup khula hai — jab tak Close/Snooze na karo, dobara nahi bajega.")

st.markdown("<br>", unsafe_allow_html=True)

# --- FETCH DATA ---
all_records = fetch_activities()
pending_records = [r for r in all_records if str(r.get("status", "Pending")).strip() != "Closed"]
closed_records = [r for r in all_records if str(r.get("status", "Pending")).strip() == "Closed"]

# --- REMINDER CHECK (only when auto-check is on and nothing else is open) ---
if st.session_state.pa_autocheck_enabled and not pause_autocheck:
    check_reminders_and_trigger(pending_records)

# --- STAT CARDS ---
important_count = sum(1 for r in pending_records if r.get("important"))
today_str = datetime.now().strftime("%d/%m/%Y")
closed_today_count = sum(1 for r in closed_records if str(r.get("closed_at", "")).startswith(today_str))

s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f'<div class="pa-stat"><p class="pa-stat-num" style="color:#60a5fa;">{len(pending_records)}</p><p class="pa-stat-label">Pending Activities</p></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="pa-stat"><p class="pa-stat-num" style="color:#fb7185;">{important_count}</p><p class="pa-stat-label">Important</p></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div class="pa-stat"><p class="pa-stat-num" style="color:#4ade80;">{closed_today_count}</p><p class="pa-stat-label">Closed Today</p></div>', unsafe_allow_html=True)
with s4:
    st.markdown(f'<div class="pa-stat"><p class="pa-stat-num" style="color:#facc15;">{len(closed_records)}</p><p class="pa-stat-label">Total Closed</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SEARCH ---
search_query = st.text_input("Search", placeholder="🔍 Search by Activity Name / Indus / VIS Responsible...", label_visibility="collapsed")

if search_query:
    q = search_query.strip().lower()
    pending_records = [
        r for r in pending_records
        if q in str(r.get("activity_name", "")).lower()
        or q in str(r.get("indus_responsible", "")).lower()
        or q in str(r.get("vis_responsible", "")).lower()
    ]

# --- SORT: Important first, then oldest raise date first ---
pending_records.sort(key=lambda r: (not bool(r.get("important")), parse_ddmmyyyy(r.get("raise_date"))))

# --- PENDING ACTIVITIES LIST ---
st.markdown("##### 🗂️ Pending Activities")

if not pending_records:
    st.info("🎉 Koi pending activity nahi hai! Sab kuch caught up hai.")
else:
    for row in pending_records:
        rid = row.get("id")
        is_important = bool(row.get("important"))
        days_txt, days_cls = days_pending_badge(row.get("raise_date", ""))
        card_class = "pa-card important" if is_important else "pa-card"

        st.markdown(f"""
            <div class="{card_class}">
                <div class="pa-title-row">
                    <span class="pa-activity-name">📌 {row.get('activity_name','') or '-'}</span>
                    {'<span class="pa-badge pa-badge-important">⭐ Important</span>' if is_important else ''}
                    <span class="pa-badge {days_cls}">{days_txt} pending</span>
                    <span class="pa-badge pa-badge-reminder">⏰ {reminder_summary_text(row)}</span>
                </div>
                <div class="pa-grid">
                    <div><div class="pa-field-label">Indus Responsible</div><div class="pa-field-value">{row.get('indus_responsible','') or '-'}</div></div>
                    <div><div class="pa-field-label">VIS Responsible</div><div class="pa-field-value">{row.get('vis_responsible','') or '-'}</div></div>
                    <div><div class="pa-field-label">Raise Date</div><div class="pa-field-value">{row.get('raise_date','') or '-'}</div></div>
                </div>
                {f'<div class="pa-remark-box">📝 {row.get("remark","")}</div>' if str(row.get('remark','')).strip() else ''}
            </div>
        """, unsafe_allow_html=True)

        bc1, bc2, bc3, _ = st.columns([1.3, 1.3, 1.3, 5])
        with bc1:
            if st.button("✏️ Edit", key=f"pa_edit_{rid}", use_container_width=True):
                st.session_state.pa_edit_row = row
                st.session_state.pa_show_form_dialog = True
                st.rerun()
        with bc2:
            if st.button("✅ Close", key=f"pa_close_{rid}", use_container_width=True):
                try:
                    supabase.table(TABLE_NAME).update({
                        "status": "Closed",
                        "closed_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    }).eq("id", rid).execute()
                    st.success("✅ Activity Closed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error Closing Activity: {e}")
        with bc3:
            if st.button("🗑️ Delete", key=f"pa_del_{rid}", use_container_width=True):
                st.session_state[f"pa_confirm_del_{rid}"] = True

        if st.session_state.get(f"pa_confirm_del_{rid}"):
            wc1, wc2, wc3 = st.columns([6, 1, 1])
            with wc1:
                st.warning(f"Delete '{row.get('activity_name','')}'? Yeh undo nahi ho sakta.")
            with wc2:
                if st.button("✅ Yes", key=f"pa_del_yes_{rid}", use_container_width=True):
                    try:
                        supabase.table(TABLE_NAME).delete().eq("id", rid).execute()
                        st.session_state[f"pa_confirm_del_{rid}"] = False
                        st.success("✅ Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            with wc3:
                if st.button("❌ No", key=f"pa_del_no_{rid}", use_container_width=True):
                    st.session_state[f"pa_confirm_del_{rid}"] = False
                    st.rerun()

        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- CLOSED ACTIVITIES SECTION ---
with st.expander(f"✅ Closed Activities ({len(closed_records)})", expanded=False):
    if not closed_records:
        st.caption("Koi closed activity nahi hai abhi tak.")
    else:
        closed_records.sort(key=lambda r: parse_ddmmyyyy(r.get("raise_date")), reverse=True)
        for row in closed_records:
            rid = row.get("id")
            st.markdown(f"""
                <div class="pa-card-closed">
                    <div class="pa-title-row">
                        <span class="pa-activity-name">✅ {row.get('activity_name','') or '-'}</span>
                    </div>
                    <div class="pa-grid">
                        <div><div class="pa-field-label">Indus Responsible</div><div class="pa-field-value">{row.get('indus_responsible','') or '-'}</div></div>
                        <div><div class="pa-field-label">VIS Responsible</div><div class="pa-field-value">{row.get('vis_responsible','') or '-'}</div></div>
                        <div><div class="pa-field-label">Raised</div><div class="pa-field-value">{row.get('raise_date','') or '-'}</div></div>
                        <div><div class="pa-field-label">Closed On</div><div class="pa-field-value">{row.get('closed_at','') or '-'}</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            rc1, rc2, _ = st.columns([1.3, 1.3, 6])
            with rc1:
                if st.button("↩️ Reopen", key=f"pa_reopen_{rid}", use_container_width=True):
                    try:
                        supabase.table(TABLE_NAME).update({"status": "Pending", "closed_at": ""}).eq("id", rid).execute()
                        st.success("✅ Reopened!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            with rc2:
                if st.button("🗑️ Delete", key=f"pa_del_closed_{rid}", use_container_width=True):
                    try:
                        supabase.table(TABLE_NAME).delete().eq("id", rid).execute()
                        st.success("✅ Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
