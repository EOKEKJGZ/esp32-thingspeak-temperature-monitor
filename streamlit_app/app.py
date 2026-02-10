import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# ---------------- CONFIG ----------------
CHANNEL_ID = "3254015"
READ_API_KEY = "79SP1MV4ASBVHNBY"
WRITE_API_KEY = "89Q4XRJ8U1GJGYKF"
# ----------------------------------------

st.set_page_config(
    page_title="ESP32 Temperature Monitor",
    page_icon="🌡️",
    layout="wide"
)

# ---------------- API FUNCTIONS ----------------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5).json()
    return float(r["field1"]), r["created_at"]

def get_threshold():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2/last.txt?api_key={READ_API_KEY}"
    return float(requests.get(url, timeout=5).text)

def update_threshold(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field2={value}"
    requests.get(url, timeout=5)

def get_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1.json?api_key={READ_API_KEY}&results=40"
    feeds = requests.get(url, timeout=5).json()["feeds"]
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field1"] = pd.to_numeric(df["field1"])
    return df

# ---------------- DATA ----------------
try:
    temperature, last_raw = get_latest_temperature()
    threshold_cloud = get_threshold()

    last_update = datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
    esp32_online = (datetime.now(timezone.utc) - last_update).seconds < 60
except:
    temperature = 0
    threshold_cloud = 30
    esp32_online = False
    last_update = None

# ---------------- SESSION ----------------
if "threshold_ui" not in st.session_state:
    st.session_state.threshold_ui = int(threshold_cloud)

# ---------------- BACKGROUND COLOR ----------------
def temp_gradient(val):
    ratio = min(max(val / 50, 0), 1)
    r = int(30 + ratio * 150)
    g = int(70 - ratio * 40)
    b = int(160 - ratio * 90)
    return f"rgb({r},{g},{b})"

bg_color = temp_gradient(st.session_state.threshold_ui)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {bg_color}, #0e1117);
        transition: background 0.1s linear;
    }}

    .card {{
        background: rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.4);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- HEADER ----------------
st.title("🌡️ ESP32 Temperature Dashboard")
st.caption("Preview → Apply → ESP32 updates")

st.divider()

# ---------------- CONTROL ----------------
st.subheader("🎚️ Temperature Threshold")

new_threshold = st.slider(
    "Preview threshold (°C)",
    0, 50,
    st.session_state.threshold_ui
)

st.markdown("")

if st.button("✅ Apply Threshold", use_container_width=True):
    update_threshold(new_threshold)
    st.session_state.threshold_ui = new_threshold
    st.success(f"Threshold set to {new_threshold} °C")

st.divider()

# ---------------- STATUS ----------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.metric("🌡️ Temperature", f"{temperature:.1f} °C")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.metric("🎚️ Active Threshold", f"{threshold_cloud:.1f} °C")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if esp32_online:
        st.success("🟢 ESP32 ONLINE")
    else:
        st.error("🔴 ESP32 OFFLINE")

    if last_update:
        st.caption(f"Last update: {last_update.strftime('%H:%M:%S UTC')}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- STATE ----------------
st.divider()

if temperature > threshold_cloud:
    st.error("⚠️ Temperature exceeds threshold")
else:
    st.success("✅ Temperature within safe range")

# ---------------- CHART ----------------
st.subheader("📈 Temperature History")

try:
    df = get_history()
    st.line_chart(df.set_index("created_at")["field1"])
except:
    st.warning("Unable to load historical data")








