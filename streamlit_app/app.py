import streamlit as st
import requests
import pandas as pd

# --------- USER CONFIG ----------
CHANNEL_ID = "3254015"
READ_API_KEY = "https://api.thingspeak.com/channels/3254015/fields/1.json?api_key=79SP1MV4ASBVHNBY&results=2"
WRITE_API_KEY = "https://api.thingspeak.com/update?api_key=89Q4XRJ8U1GJGYKF&field1=0"
# --------------------------------

st.set_page_config(
    page_title="ESP32 Temperature Dashboard",
    page_icon="🌡️",
    layout="centered"
)

st.title("🌡️ ESP32 Temperature Monitoring")
st.caption("Cloud-based IoT dashboard using ThingSpeak")

# --------- Read Latest Temperature ----------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return float(data["field1"])

# --------- Read Temperature History ----------
def get_temperature_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1.json?api_key={READ_API_KEY}&results=20"
    response = requests.get(url)
    data = response.json()

    feeds = data["feeds"]
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field1"] = pd.to_numeric(df["field1"])
    return df

# --------- Write Threshold ----------
def update_threshold(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field2={value}"
    requests.get(url)

# --------- UI ----------
try:
    temperature = get_latest_temperature()
    st.metric("Current Temperature", f"{temperature:.1f} °C")
except:
    st.error("Unable to fetch temperature data")

st.divider()

st.subheader("🎚️ Set Temperature Threshold")

threshold = st.slider(
    "Threshold (°C)",
    min_value=20,
    max_value=50,
    value=30
)

if st.button("Update Threshold"):
    update_threshold(threshold)
    st.success(f"Threshold updated to {threshold} °C")

st.divider()

st.subheader("📈 Temperature History")

try:
    df = get_temperature_history()
    st.line_chart(df.set_index("created_at")["field1"])
except:
    st.warning("Unable to load historical data")

