import streamlit as st
import pandas as pd
import numpy as np
import io
import wave
import base64
import textwrap
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
if 'pa_quiet_hours_enabled' not in st.session_state:
    st.session_state.pa_quiet_hours_enabled = True
if 'active_reminder' not in st.session_state:
    st.session_state.active_reminder = None
if 'pa_search' not in st.session_state:
    st.session_state.pa_search = ""
if 'pa_show_form_dialog' not in st.session_state:
    st.session_state.pa_show_form_dialog = False
if 'pa_edit_row' not in st.session_state:
    st.session_state.pa_edit_row = None

# --- CLEAN WHITE BUSINESS THEME ---
st.markdown("""<style>
.stApp, [data-testid="stAppViewContainer"] {background:#f7f9fc!important;color:#17243b!important;}
.block-container {padding-top:1.15rem!important;max-width:1600px!important;}
h1,h2,h3,h4,p,label,div[data-testid="stWidgetLabel"] p {color:#17243b;}
[data-testid="stSidebar"] {background:#ffffff!important;}
[data-testid="stSidebarNav"] a {color:#253451!important;}
div.stButton>button[kind="primary"] {background:#2563eb!important;color:white!important;border:0!important;}
div.stButton>button {border-radius:8px!important;font-weight:800!important; color:#14243b!important; border:1px solid #b9c7d9!important;}
div.stButton>button p, div.stButton>button span {font-weight:800!important;}
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label, [data-testid="stAppViewContainer"] input, [data-testid="stAppViewContainer"] [data-baseweb="select"] {font-weight:700!important;color:#15243a!important;}
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] {font-weight:800!important;}
[class*="st-key-task_high_"] {background:#ffe0e1!important;border:1px solid #f7a5a9!important;border-left:6px solid #e11d48!important; border-radius:9px!important;padding:7px 10px!important;margin-bottom:5px!important;}
[class*="st-key-task_medium_"] {background:#ffedd5!important;border:1px solid #fdba74!important;border-left:6px solid #f97316!important;border-radius:9px!important;padding:7px 10px!important;margin-bottom:5px!important;}
[class*="st-key-task_normal_"] {background:#dbeafe!important;border:1px solid #93c5fd!important;border-left:6px solid #2563eb!important;border-radius:9px!important;padding:7px 10px!important;margin-bottom:5px!important;}
[class*="st-key-task_completed_"] {background:#e2f7e9!important;border:1px solid #86efac!important;border-left:6px solid #16a34a!important;border-radius:9px!important;padding:7px 10px!important;margin-bottom:5px!important;}
.st-key-tab_all button {background:#2563eb!important;color:white!important;border:0!important;border-radius:9px!important;font-weight:900!important;padding:12px!important;}
.st-key-tab_done button {background:#16a34a!important;color:white!important;border:0!important;border-radius:9px!important;font-weight:900!important;padding:12px!important;}
.st-key-tab_all button p,.st-key-tab_done button p {color:white!important;font-weight:900!important;}
.st-key-add_task button {background:#2563eb!important;color:white!important;}
.st-key-refresh_tasks button {background:#0d9488!important;color:white!important;}
.st-key-test_alarm button {background:#d97706!important;color:white!important;}
.st-key-add_task button p,.st-key-refresh_tasks button p,.st-key-test_alarm button p {color:white!important;}

div[data-testid="stMetric"] {background:white;border:1px solid #e2e8f0;border-radius:9px;padding:14px 18px;}
[data-testid="stTabs"] button {font-weight:700!important;}
[data-testid="stDataFrame"] {border:1px solid #e2e8f0;border-radius:9px;}
[data-testid="stDialog"] {color:#17243b!important;}
</style>""", unsafe_allow_html=True)

# --- 4. SUPABASE CONNECTION ---
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
TABLE_NAME = "pending_activity"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- QUIET HOURS (Do Not Disturb): no popup, no sound during this window ---
QUIET_HOURS_START = dt_time(23, 0)  # 11:00 PM
QUIET_HOURS_END = dt_time(10, 0)    # 10:00 AM (next day)


def is_quiet_hours(now=None):
    """Window spans midnight (23:00 -> 10:00 next day)."""
    if now is None:
        now = datetime.now()
    t = now.time()
    return t >= QUIET_HOURS_START or t < QUIET_HOURS_END


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
    st.markdown(
        f'<audio autoplay><source src="data:audio/wav;base64,{b64_audio}" type="audio/wav"></audio>',
        unsafe_allow_html=True,
    )


# --- 6. DATA HELPERS ---
# NOTE: This page is intentionally NOT scoped by workspace/company.
# Every login (any company) sees and shares the exact same task list.
# Cached for 15s (just under the 20s auto-refresh cycle) so incidental
# reruns (sound toggle, opening a dialog) reuse the same fetch, while the
# scheduled auto-refresh still gets live data every ~20s as intended.
@st.cache_data(ttl=15, show_spinner=False)
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


def format_time_12hr(r_time_str):
    """Converts a stored 24-hour 'HH:MM' string into a 12-hour 'hh:MM AM/PM' display string."""
    try:
        t = datetime.strptime(str(r_time_str).strip(), "%H:%M")
        return t.strftime("%I:%M %p")
    except Exception:
        return r_time_str


def reminder_summary_text(row):
    r_type = str(row.get("reminder_type", "")).strip()
    r_time = format_time_12hr(row.get("reminder_time", ""))
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


def time_picker(label, key_prefix, default_time=dt_time(9, 0)):
    """
    A reliable, always-visible 12-hour Hour/Minute/AM-PM clock picker built
    from plain Streamlit selectboxes — guaranteed to render and open the
    same way in every browser (unlike the native HTML clock widget, which
    renders inconsistently and can be nearly invisible on dark themes).
    """
    st.markdown(f'<div class="pa-field-label" style="margin-top:6px;">{label}</div>', unsafe_allow_html=True)
    hc1, hc2, hc3, hc4 = st.columns([1, 1, 1, 1.6])

    hour_opts = [f"{h:02d}" for h in range(1, 13)]          # 01–12
    minute_opts = [f"{m:02d}" for m in range(0, 60, 5)]      # 00,05,...,55
    ampm_opts = ["AM", "PM"]

    # Convert incoming 24-hour default_time -> 12-hour + AM/PM
    default_ampm = "AM" if default_time.hour < 12 else "PM"
    default_hour_24 = default_time.hour % 12
    default_hour_12 = 12 if default_hour_24 == 0 else default_hour_24
    default_hour = f"{default_hour_12:02d}"
    default_minute = f"{(default_time.minute // 5) * 5:02d}"

    with hc1:
        sel_hour = st.selectbox(
            "Hour", hour_opts,
            index=hour_opts.index(default_hour) if default_hour in hour_opts else 8,
            key=f"{key_prefix}_hour",
        )
    with hc2:
        sel_min = st.selectbox(
            "Min", minute_opts,
            index=minute_opts.index(default_minute) if default_minute in minute_opts else 0,
            key=f"{key_prefix}_min",
        )
    with hc3:
        sel_ampm = st.selectbox(
            "AM/PM", ampm_opts,
            index=ampm_opts.index(default_ampm),
            key=f"{key_prefix}_ampm",
        )
    with hc4:
        st.markdown(
            f'<div style="margin-top:26px; background:rgba(139,92,246,0.15); border:1px solid rgba(139,92,246,0.45); '
            f'border-radius:8px; padding:9px 14px; text-align:center; font-size:1.25rem; font-weight:900; '
            f'color:#c4b5fd; font-family:monospace; letter-spacing:1px;">🕐 {sel_hour}:{sel_min} {sel_ampm}</div>',
            unsafe_allow_html=True,
        )

    # Convert 12-hour + AM/PM selection back to 24-hour for storage
    hour_12 = int(sel_hour)
    if sel_ampm == "AM":
        hour_24 = 0 if hour_12 == 12 else hour_12
    else:
        hour_24 = 12 if hour_12 == 12 else hour_12 + 12

    return dt_time(hour_24, int(sel_min))


# --- 7. REMINDER ENGINE: check all pending activities against current time ---
def check_reminders_and_trigger(pending_records):
    if st.session_state.get("active_reminder"):
        return  # a popup is already showing — don't stack another one

    now = datetime.now()

    # --- QUIET HOURS: 11 PM – 10 AM => absolutely no popup, no sound ---
    if st.session_state.get("pa_quiet_hours_enabled", True) and is_quiet_hours(now):
        return

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

    rc1 = st.columns(1)[0]
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

    default_time = dt_time(9, 0)
    if is_edit and edit_row.get('reminder_time'):
        try:
            default_time = datetime.strptime(edit_row.get('reminder_time'), "%H:%M").time()
        except Exception:
            pass
    reminder_time_val = time_picker("REMINDER TIME * 🕐", key_prefix=f"add_time_{edit_row.get('id') if is_edit else 'new'}", default_time=default_time)

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
                fetch_activities.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error Saving Activity: {e}")


# --- 9. REMINDER ALARM POPUP DIALOG ---
@st.dialog("🔔 TASK REMINDER!", width="large")
def reminder_popup_dialog(row):
    render_alarm_audio()

    days_txt, days_cls = days_pending_badge(row.get('raise_date', ''))

    alarm_html = (
        '<div class="pa-alarm-wrap">'
        '<div class="pa-alarm-icon">⏰</div>'
        '<div class="pa-alarm-title">It\'s Time! Don\'t Forget This Task</div>'
        f'<div class="pa-alarm-activity">{row.get("activity_name", "")}</div>'
        f'<div class="pa-alarm-info-row"><span class="pa-alarm-label">👷 Indus Responsible</span><span class="pa-alarm-value">{row.get("indus_responsible","") or "-"}</span></div>'
        f'<div class="pa-alarm-info-row"><span class="pa-alarm-label">🏢 VIS Responsible</span><span class="pa-alarm-value">{row.get("vis_responsible","") or "-"}</span></div>'
        f'<div class="pa-alarm-info-row"><span class="pa-alarm-label">📅 Raised On</span><span class="pa-alarm-value">{row.get("raise_date","") or "-"} ({days_txt} ago)</span></div>'
        f'<div class="pa-alarm-info-row"><span class="pa-alarm-label">⭐ Important</span><span class="pa-alarm-value">{"YES 🔥" if row.get("important") else "No"}</span></div>'
        '</div>'
    )
    st.markdown(alarm_html, unsafe_allow_html=True)

    if str(row.get('remark', '')).strip():
        st.markdown(f'<div class="pa-remark-box">📝 {row.get("remark","")}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    is_test_reminder = (row.get('id') == 'test')
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
            # Only touch the database for REAL activities. A test reminder
            # (id == "test") has no matching database row — trying to update
            # it would fail and (before this fix) left the popup stuck open.
            if not is_test_reminder:
                try:
                    supabase.table(TABLE_NAME).update({
                        "status": "Closed",
                        "closed_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    }).eq("id", row['id']).execute()
                except Exception as e:
                    st.warning(f"⚠️ Popup band ho gaya, lekin database update fail hua: {e}")
            st.session_state["active_reminder"] = None
            st.success("✅ Task Closed!")
            fetch_activities.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙️ Full Reschedule (change reminder type/day/date/time)"):
        r_type_opts = ["Daily", "Weekly", "Monthly", "Specific Date"]
        cur_type_idx = r_type_opts.index(row.get('reminder_type')) if row.get('reminder_type') in r_type_opts else 0
        new_type = st.selectbox("New Reminder Type", r_type_opts, index=cur_type_idx, key="resch_type")

        new_day, new_dom, new_sdate = "", None, ""
        rc1 = st.columns(1)[0]
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

        current_r_time = dt_time(9, 0)
        try:
            current_r_time = datetime.strptime(str(row.get('reminder_time', '09:00')), "%H:%M").time()
        except Exception:
            pass
        new_time = time_picker("Reminder Time 🕐", key_prefix=f"resch_time_{row.get('id')}", default_time=current_r_time)

        if st.button("🔄 Save New Schedule", use_container_width=True, key="resch_save"):
            if is_test_reminder:
                st.session_state["active_reminder"] = None
                st.success("✅ Test popup closed (test reminders aren't saved to the database).")
                st.rerun()
            else:
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
                    fetch_activities.clear()
                    st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ Popup band ho gaya, lekin database update fail hua: {e}")
                    st.session_state["active_reminder"] = None
                    st.rerun()


def _snooze_reminder(row, minutes):
    is_test_reminder = (row.get('id') == 'test')
    try:
        if not is_test_reminder:
            new_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")
            supabase.table(TABLE_NAME).update({
                "reminder_time": new_time,
                "last_notified": "",
            }).eq("id", row['id']).execute()
        st.session_state["active_reminder"] = None
        st.toast(f"⏰ Snoozed for {minutes} minutes!", icon="😴")
        fetch_activities.clear()
        st.rerun()
    except Exception as e:
        st.warning(f"⚠️ Popup band ho gaya, lekin database update fail hua: {e}")
        st.session_state["active_reminder"] = None
        st.rerun()


# ----------------- CLEAN TWO-TAB TASK DESK -----------------
from html import escape

if st.session_state.get("active_reminder"):
    reminder_popup_dialog(st.session_state["active_reminder"])
elif st.session_state.get("pa_show_form_dialog"):
    add_activity_dialog(edit_row=st.session_state.get("pa_edit_row"))

st.markdown("## Daily Task & EOD Report Tool")
st.caption("Task management  /  All companies  /  Live Supabase data")

if st.session_state.pa_autocheck_enabled and AUTOREFRESH_AVAILABLE and not st.session_state.get("active_reminder") and not st.session_state.get("pa_show_form_dialog"):
    st_autorefresh(interval=20000, key="white_task_refresh")

all_records = fetch_activities() if supabase is not None else []
pending = [r for r in all_records if str(r.get("status") or "Pending").lower() != "closed"]
completed = [r for r in all_records if str(r.get("status") or "Pending").lower() == "closed"]
if st.session_state.pa_autocheck_enabled and not st.session_state.get("active_reminder") and not st.session_state.get("pa_show_form_dialog"):
    check_reminders_and_trigger(pending)

today = datetime.now().strftime("%d/%m/%Y")
counts = [len(all_records), len(completed), len(pending), sum(bool(r.get("important")) for r in pending)]
metrics = st.columns(4)
for col, title, count in zip(metrics,["Total Tasks","Completed","Pending","High Priority"],counts):
    col.metric(title,count)

b1,b2,b3,b4=st.columns([1.7,1.3,1.3,5])
with b1:
    if st.button("＋ Add New Task",type="primary",use_container_width=True,key="add_task"):
        st.session_state.pa_edit_row=None
        st.session_state.pa_show_form_dialog=True
        st.rerun()
with b2:
    if st.button("↻ Refresh",use_container_width=True,key="refresh_tasks"):
        fetch_activities.clear();st.rerun()
with b3:
    if st.button("🔔 Test Alarm",use_container_width=True,key="test_alarm"):
        st.session_state["active_reminder"]={"id":"test","activity_name":"Test Reminder","indus_responsible":"-","vis_responsible":"-","raise_date":today,"remark":"Test alarm","important":False,"reminder_type":"Daily","reminder_time":datetime.now().strftime("%H:%M")}
        st.rerun()

search=st.text_input("Search Tasks",placeholder="Search task, responsible person, remark...",label_visibility="collapsed")

def save_row(row,changes):
    try:
        supabase.table(TABLE_NAME).update(changes).eq("id",row["id"]).execute()
        fetch_activities.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Save failed: {e}")

def matches(row):
    q=search.strip().lower()
    return not q or any(q in str(row.get(k) or "").lower() for k in ["activity_name","indus_responsible","vis_responsible","remark"])

def task_sort(row):
    return ({"High":0,"Medium":1,"Normal":2}.get(str(row.get("priority") or ("High" if row.get("important") else "Normal")),2), parse_ddmmyyyy(row.get("raise_date")))

# Render compact spreadsheet-like table with editable remark/status and per-row actions.
def render_tasks(rows,done=False):
    rows=[r for r in rows if matches(r)]
    rows.sort(key=task_sort if not done else lambda r: str(r.get("closed_at") or ""),reverse=done)
    if not rows:
        st.info("No tasks found in this tab.")
        return
    header=st.columns([0.5,3.3,1.5,1.5,1.3,1.3,3,1.5,1.3,1.3])
    for col,label in zip(header,["#","Task","Indus Resp.","VIS Resp.","Priority","Raised","Remark","Status","Edit","Delete"]):
        col.markdown(f"**{label}**")
    st.divider()
    for i,row in enumerate(rows,1):
        rid=str(row.get("id"))
        current_priority=str(row.get("priority") or ("High" if row.get("important") else "Normal"))
        if current_priority not in ["High","Medium","Normal"]: current_priority="Normal"
        row_color="completed" if done else current_priority.lower()
        with st.container(key=f"task_{row_color}_{rid}"):
            cols=st.columns([0.5,3.3,1.5,1.5,1.3,1.3,3,1.5,1.3,1.3],vertical_alignment="center")
            cols[0].markdown(f"**{i}**")
            title=escape(str(row.get("activity_name") or "Untitled"))
            cols[1].markdown(f"**{title}**")
            cols[2].markdown(f"**{escape(str(row.get('indus_responsible') or '—'))}**")
            cols[3].markdown(f"**{escape(str(row.get('vis_responsible') or '—'))}**")
            with cols[4]:
                priority=st.selectbox("Priority",["High","Medium","Normal"],index=["High","Medium","Normal"].index(current_priority),key=f"priority_{rid}",label_visibility="collapsed")
                if priority != current_priority:
                    save_row(row,{"priority":priority,"important":priority=="High"})
            cols[5].markdown(f"**{escape(str(row.get('raise_date') or '—'))}**")
            with cols[6]:
                # Blank on first display; old remark is preserved until a new one is saved.
                new_remark=st.text_input("New remark",value="",key=f"remark_entry_{rid}",label_visibility="collapsed",placeholder="Write remark...")
                if new_remark.strip():
                    if st.button("💾 Save",key=f"remark_save_{rid}"):
                        save_row(row,{"remark":new_remark.strip()})
                old_remark=str(row.get("remark") or "").strip()
                if old_remark:
                    st.caption("Saved: " + old_remark)
            with cols[7]:
                status=st.selectbox("Status",["Completed","Pending"] if done else ["Pending","Completed"],key=f"status_{rid}",label_visibility="collapsed")
                if (done and status=="Pending") or (not done and status=="Completed"):
                    save_row(row,{"status":"Pending" if status=="Pending" else "Closed","closed_at":"" if status=="Pending" else datetime.now().strftime("%d/%m/%Y %H:%M")})
            with cols[8]:
                if st.button("✏️ Edit",key=f"edit_{rid}",use_container_width=True):
                    st.session_state.pa_edit_row=row
                    st.session_state.pa_show_form_dialog=True
                    st.rerun()
            with cols[9]:
                if st.button("🗑️ Delete",key=f"delete_{rid}",use_container_width=True):
                    st.session_state[f"confirm_{rid}"]=True
            if st.session_state.get(f"confirm_{rid}"):
                st.warning(f"Delete task '{row.get('activity_name','')}' permanently?")
                yes,no=st.columns([1,7])
                with yes:
                    if st.button("Yes, delete",key=f"yes_{rid}"):
                        try:
                            supabase.table(TABLE_NAME).delete().eq("id",row["id"]).execute()
                            fetch_activities.clear();st.rerun()
                        except Exception as e:
                            st.error(str(e))
                with no:
                    if st.button("Cancel",key=f"no_{rid}"):
                        st.session_state[f"confirm_{rid}"]=False;st.rerun()

nav1,nav2,_=st.columns([1.4,1.7,6])
with nav1:
    if st.button(f"📋 All Tasks ({len(pending)})",key="tab_all",use_container_width=True):
        st.session_state["task_tab"]="all"
with nav2:
    if st.button(f"✅ Completed Tasks ({len(completed)})",key="tab_done",use_container_width=True):
        st.session_state["task_tab"]="done"
if "task_tab" not in st.session_state: st.session_state["task_tab"]="all"
if st.session_state["task_tab"]=="all":
    st.caption("High priority tasks appear first. Change status to Completed to move a task to the second tab.")
    render_tasks(pending)
else:
    st.caption("Completed tasks are stored here. Change status to Pending to reopen.")
    render_tasks(completed,done=True)
