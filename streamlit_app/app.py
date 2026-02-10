import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime, timezone

# ---------------- CONFIG ----------------
CHANNEL_ID = "3254015"
READ_API_KEY = "79SP1MV4ASBVHNBY"
WRITE_API_KEY = "89Q4XRJ8U1GJGYKF"
# ----------------------------------------

st.set_page_config(
    page_title="ESP32 IoT Temperature Dashboard",
    page_icon="🌡️",
    layout="wide"
)

# ---------------- API FUNCTIONS ----------------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5).json()
    return float(r["field1"]), r["created_at"]

def get_current_threshold():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2/last.txt?api_key={READ_API_KEY}"
    return float(requests.get(url, timeout=5).text)

def update_threshold(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field2={value}"
    requests.get(url, timeout=5)

def get_temperature_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1.json?api_key={READ_API_KEY}&results=30"
    feeds = requests.get(url, timeout=5).json()["feeds"]
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field1"] = pd.to_numeric(df["field1"])
    return df

# ---------------- DATA FETCH ----------------
try:
    temperature, last_update_raw = get_latest_temperature()
    threshold_cloud = get_current_threshold()

    last_update = datetime.fromisoformat(
        last_update_raw.replace("Z", "+00:00")
    )
    now = datetime.now(timezone.utc)
    esp32_online = (now - last_update).seconds < 60
except:
    temperature = 0
    threshold_cloud = 30
    esp32_online = False
    last_update = None

# ---------------- SESSION STATE ----------------
if "ui_threshold" not in st.session_state:
    st.session_state.ui_threshold = int(threshold_cloud)

# ---------------- FULL BACKGROUND STYLE ----------------
st.markdown(
    """
    <style>
    .stApp {
        transition: background 0.25s linear;
    }

    .glass-card {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(14px);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.35);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- LIVE SLIDER (FULL PAGE COLOR) ----------------
components.html(
    f"""
    <style>
      input[type=range] {{
        width: 100%;
        -webkit-appearance: none;
        height: 10px;
        border-radius: 5px;
        background: #eee;
        outline: none;
      }}

      input[type=range]::-webkit-slider-thumb {{
        -webkit-appearance: none;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: white;
        border: 3px solid #222;
        cursor: pointer;
      }}

      .label {{
        color: white;
        font-size: 22px;
        font-weight: 600;
        margin-top: 12px;
      }}
    </style>

    <div class="glass-card">
      <input type="range" min="0" max="50" value="{st.session_state.ui_threshold}" id="slider">
      <div class="label">
        Threshold: <span id="val">{st.session_state.ui_threshold}</span> °C
      </div>
    </div>

    <script>
      const slider = document.getElementById("slider");
      const val = document.getElementById("val");

      function tempToColor(t) {{
        const r = Math.round(30 + (220 - 30) * (t / 50));
        const g = Math.round(60 + (20 - 60) * (t / 50));
        const b = Math.round(180 + (60 - 180) * (t / 50));
        return `rgb(${{r}},${{g}},${{b}})`;
      }}

      function applyBackground(temp) {{
        const color = tempToColor(temp);
        document.body.style.background =
          `linear-gradient(135deg, ${{color}}, #0e1117)`;
      }}

      applyBackground(slider.value);

      slider.addEventListener("input", () => {{
        val.textContent = slider.value;
        applyBackground(slider.value);
      }});

      slider.addEventListener("change", () => {{
        window.parent.postMessage(
          {{ threshold: slider.value }},
          "*"
        );
      }});
    </script>
    """,
    height=200,
)

# ---------------- AUTO SYNC (AFTER DRAG) ----------------
if "threshold" in st.query_params:
    st.session_state.ui_threshold = int(st.query_params["threshold"])
    update_threshold(st.session_state.ui_threshold)

# ---------------- DASHBOARD CONTENT ----------------
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.metric("🌡️ Temperature", f"{temperature:.1f} °C")
    st.metric("🎚️ Threshold", f"{threshold_cloud:.1f} °C")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if esp32_online:
        st.success("🟢 ESP32 ONLINE")
    else:
        st.error("🔴 ESP32 OFFLINE")

    if last_update:
        st.caption(f"Last update: {last_update.strftime('%H:%M:%S UTC')}")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if temperature > threshold_cloud:
        st.error("⚠️ Over Temperature")
    else:
        st.success("✅ Normal Operation")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

st.subheader("📈 Temperature History")
try:
    df = get_temperature_history()
    st.line_chart(df.set_index("created_at")["field1"])
except:
    st.warning("Unable to load data")



