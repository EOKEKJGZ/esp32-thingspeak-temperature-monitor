import streamlit as st
import requests
import pandas as pd

# --------- USER CONFIG ----------
CHANNEL_ID = "3254015"
READ_API_KEY = "https://api.thingspeak.com/channels/3254015/fields/1.json?api_key=79SP1MV4ASBVHNBY&results=2"
WRITE_API_KEY = "https://api.thingspeak.com/update?api_key=89Q4XRJ8U1GJGYKF&field1=0"
# --------------------------------

st.set_page_config(
    page_title="ESP32 IoT Temperature Dashboard",
    page_icon="🌡️",
    layout="wide"
)

# --------- HELPER: TEMP → COLOR ----------
def temperature_to_gradient(temp):
    """
    Maps 0–50°C to a vibrant blue → purple → red gradient
    """
    temp = max(0, min(50, temp))
    ratio = temp / 50.0

    # RGB interpolation
    r = int(30 + (220 - 30) * ratio)
    g = int(60 + (20 - 60) * ratio)
    b = int(180 + (60 - 180) * ratio)

    return f"rgb({r},{g},{b})"

# --------- API FUNCTIONS ----------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    return float(requests.get(url, timeout=5).json()["field1"])

def get_current_threshold():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2/last.txt?api_key={READ_API_KEY}"
    return float(requests.get(url, timeout=5).text)

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

# --------- AUTO REFRESH ----------
st.experimental_autorefresh(interval=20000, key="refresh")

# --------- READ CLOUD VALUES ----------
try:
    temperature = get_latest_temperature()
    threshold_cloud = get_current_threshold()
except:
    temperature = 0
    threshold_cloud = 30

# --------- DYNAMIC BACKGROUND ----------
bg_color = temperature_to_gradient(threshold_cloud)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: radial-gradient(
            circle at top,
            {bg_color} 0%,
            #0e1117 70%
        );
        transition: background 1.2s ease-in-out;
    }}

    /* Slider styling */
    div[data-baseweb="slider"] > div {{
        transition: all 0.3s ease;
    }}

    /* Card-like containers */
    .block-container {{
        padding-top: 2rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------- UI ----------
st.title("🌡️ ESP32 IoT Temperature Monitoring")
st.caption("High-end cloud dashboard • ThingSpeak • Streamlit")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Live Status")
    st.metric("Current Temperature", f"{temperature:.1f} °C")
    st.metric("Active Threshold", f"{threshold_cloud:.1f} °C")

    if temperature > threshold_cloud:
        st.error("⚠️ Temperature exceeds threshold")
    else:
        st.success("✅ Temperature within safe range")

with col2:
    st.subheader("🎚️ Set Temperature Threshold")

    new_threshold = st.slider(
        "Threshold (°C)",
        min_value=0,
        max_value=50,
        value=int(threshold_cloud),
        step=1
    )

    if st.button("Update Threshold"):
        update_threshold(new_threshold)
        st.success(f"Threshold updated to {new_threshold} °C")

st.divider()

st.subheader("📈 Temperature History")

try:
    df = get_temperature_history()
    st.line_chart(df.set_index("created_at")["field1"])
except:
    st.warning("Unable to load historical data")

