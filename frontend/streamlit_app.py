import data
import requests
import streamlit as st
from datetime import date, timedelta

API = "http://127.0.0.1:8001"  # Backend

st.set_page_config(page_title="SmartPTO", page_icon="🗓️", layout="centered")
st.title("🗓️ SmartPTO — Demo")

# --- Health ---
with st.expander("Server status", expanded=True):
    try:
        r = requests.get(f"{API}/health", timeout=5)
        st.success(f"API OK: {r.json()}")
    except Exception as e:
        st.error(f"API not reachable: {e}")
        st.stop()

# --- Sidebar controls ---
employees = [
    ("u1", "Ryan"),
    ("u2", "Alex"),
    ("u3", "Priya"),
]

with st.sidebar:
    st.header("Inputs")
    emp_id = st.selectbox("Employee", employees, index=0, format_func=lambda x: x[1])[0]
    desired_len = st.slider("Desired PTO length (days)", 1, 14, 3)
    horizon = st.slider("Planning horizon (days)", 7, 90, 60)
    max_cov = st.slider("Max coverage ratio", 0.0, 1.0, 0.3)

# --- Balance ---
st.subheader("Accrual balance")
balance_data = {}
try:
    r = requests.get(f"{API}/balance", params={"employee_id": emp_id}, timeout=5)
    balance_data = r.json()
    if "error" in balance_data:
        st.warning(balance_data["error"])
    else:
        st.metric(
            label=f"{balance_data['name']}'s PTO balance",
            value=balance_data["accrual_days"]
        )
except Exception as e:
    st.error(f"Error fetching balance: {e}")
    balance_data = {}

# --- Recommendations ---
st.subheader("Recommendations")

def make_ics(start, end, name):
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:PTO for {name}
DTSTART;VALUE=DATE:{start.strftime("%Y%m%d")}
DTEND;VALUE=DATE:{(end+timedelta(days=1)).strftime("%Y%m%d")}
DESCRIPTION:SmartPTO suggested leave
END:VEVENT
END:VCALENDAR"""

start = end = None
reason = None

try:
    params = {
        "employee_id": emp_id,
        "desired_len_days": desired_len,
    }
    r = requests.get(f"{API}/recommend", params=params, timeout=5)
    if r.status_code == 200:
        recs = r.json()
        if isinstance(recs, list) and recs:
            rec = recs[0]
            start = date.fromisoformat(rec["window_start"])
            end = date.fromisoformat(rec["window_end"])
            reason = rec.get("reason", "coverage OK")
        else:
            st.info("No suitable windows found from API.")
    else:
        st.warning(f"/recommend returned HTTP {r.status_code}. Using fallback.")
except Exception as e:
    st.warning(f"Could not fetch recommendations: {e}")

# --- Always show something (fallback if API failed) ---
if start is None:
    start = date.today() + timedelta(days=3)
    end = start + timedelta(days=desired_len - 1)
    reason = "naive fallback"

# --- Compare against accrual balance ---
accrual = float(balance_data.get("accrual_days", 0))
if desired_len > accrual:
    st.warning(
        f"Requested {desired_len} day(s) but balance is only {accrual}. "
        "Window is shown anyway."
    )

st.success(f"Suggested window ({reason}): {start} → {end}")


# Calendar download
if start and end:
    ics = make_ics(start, end, emp_id)
    st.download_button("📅 Add to Calendar", data=ics, file_name="pto.ics", mime="text/calendar")

# --- Request PTO form ---
st.subheader("Submit PTO Request")
with st.form("request_pto"):
    note = st.text_input("Optional note to manager", "")
    submitted = st.form_submit_button("Request PTO")
    if submitted and start and end:
        payload = {
            "employee_id": emp_id,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "note": note,
        }
        # For now, just show payload (no backend endpoint yet)
        st.json(payload)
        st.success("PTO request (demo) submitted!")












# --- Gmail Scanning ---
st.subheader("📧 Scan Gmail for holiday hints")
limit = st.number_input("Max emails", min_value=5, max_value=100, value=20, step=5, key="limit1")
if st.button("Scan Gmail"):
    try:
        r = requests.get(f"{API}/gmail/holiday-suggestions", params={"max_results": int(limit)}, timeout=10)
        data = r.json()
        items = data.get("items", [])
        if not items:
            st.info("No recent Gmail subjects matched holiday/PTO terms.")
        else:
            for it in items:
                st.write(f"**{it.get('subject','(no subject)')}**")
                st.caption(f"{it.get('from')} — {it.get('date')}")
    except Exception as e:
        st.error(f"Gmail request failed: {e}")

st.subheader("🤖 AI-assisted Gmail PTO scan")
limit_ai = st.number_input("Max messages to scan (AI)", min_value=5, max_value=200, value=50, step=5, key="limit2")
if st.button("Analyze Gmail for PTO hints"):
    with st.spinner("Scanning Gmail..."):
        try:
            r = requests.get(f"{API}/gmail/analyze", params={"max_results": int(limit_ai)}, timeout=20)
            data = r.json()
            st.info(f"Scanned {data.get('count_messages',0)} messages")
            for s in data.get("suggestions", []):
                st.success(f"{s['window_start']} → {s['window_end']} — {s['reason']} "
                           f"(confidence {s.get('confidence',0):.2f})")
        except Exception as e:
            st.error(f"AI Gmail analysis failed: {e}")
