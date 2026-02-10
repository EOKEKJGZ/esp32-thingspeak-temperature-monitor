import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

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

st.title("🌡️ ESP32 IoT Temperature Monitoring")
st.caption("Live IoT dashboard • ThingSpeak • Streamlit")

# ---------------- API FUNCTIONS ----------------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5)
    return float(r.json()["field1"])

def get_current_threshold():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2/last.txt?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5)
    return float(r.text)

def update_threshold(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field2={value}"
    requests.get(url, timeout=5)

def get_temperature_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1.json?api_key={READ_API_KEY}&results=30"
    data = requests.get(url, timeout=5).json()["feeds"]
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field1"] = pd.to_numeric(df["field1"])
    return df

# ---------------- READ CLOUD DATA ----------------
try:
    temperature = get_latest_temperature()
    threshold_cloud = get_current_threshold()
except:
    temperature = 0
    threshold_cloud = 30

# ---------------- SESSION STATE ----------------
if "ui_threshold" not in st.session_state:
    st.session_state.ui_threshold = int(threshold_cloud)

# ---------------- LIVE DRAGGING SLIDER ----------------
components.html(
    f"""
    <style>
      .slider-container {{
        width: 100%;
        padding: 40px;
        border-radius: 18px;
        background: linear-gradient(135deg, rgb(30,60,180), #121826);
        transition: background 0.15s linear;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      }}

      input[type=range] {{
        width: 100%;
        -webkit-appearance: none;
        height: 10px;
        border-radius: 5px;
        background: #ddd;
        outline: none;
      }}

      input[type=range]::-webkit-slider-thumb {{
        -webkit-appearance: none;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: white;
        border: 3px solid #333;
        cursor: pointer;
      }}

      .value {{
        margin-top: 18px;
        font-size: 20px;
        font-weight: 600;
        color: white;
      }}
    </style>

    <div class="slider-container" id="bg">
      <input type="range" min="0" max="50" value="{st.session_state.ui_threshold}" id="tempSlider">
      <div class="value">
        Threshold: <span id="val">{st.session_state.ui_threshold}</span> °C
      </div>
    </div>

    <script>
      const slider = document.getElementById("tempSlider");
      const bg = document.getElementById("bg");
      const val = document.getElementById("val");

      function tempToColor(t) {{
        const ratio = t / 50;
        const r = Math.round(30 + (220 - 30) * ratio);
        const g = Math.round(60 + (20 - 60) * ratio);
        const b = Math.round(180 + (60 - 180) * ratio);
        return `rgb(${{r}}, ${{g}}, ${{b}})`;
      }}

      slider.addEventListener("input", () => {{
        const temp = slider.value;
        val.textContent = temp;
        const color = tempToColor(temp);
        bg.style.background = `linear-gradient(135deg, ${{color}}, #121826)`;
      }});
    </script>
    """,
    height=260,
)

# ---------------- MANUAL THRESHOLD SYNC ----------------
st.subheader("☁️ Sync Threshold to ThingSpeak")

new_threshold = st.number_input(
    "Confirm threshold value (°C)",
    min_value=0,
    max_value=50,
    value=st.session_state.ui_threshold,
    step=1
)

if st.button("Update Threshold in Cloud"):
    update_threshold(new_threshold)
    st.session_state.ui_threshold = new_threshold
    st.success(f"Threshold updated to {new_threshold} °C")

# ---------------- STATUS ----------------
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Live Status")
    st.metric("Current Temperature", f"{temperature:.1f} °C")
    st.metric("Cloud Threshold", f"{threshold_cloud:.1f} °C")

    if temperature > threshold_cloud:
        st.error("⚠️ Temperature exceeds threshold")
    else:
        st.success("✅ Temperature within safe range")

with col2:
    st.subheader("📈 Temperature History")
    try:
        df = get_temperature_history()
        st.line_chart(df.set_index("created_at")["field1"])
    except:
        st.warning("Unable to load historical data")


