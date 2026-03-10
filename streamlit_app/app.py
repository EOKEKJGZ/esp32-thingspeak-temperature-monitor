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
    page_title="ESP32 Environment Monitor",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- API FUNCTIONS ----------------
def get_latest_temperature():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1/last.json?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5).json()
    return float(r["field1"]), r["created_at"]

def get_latest_humidity():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/3/last.json?api_key={READ_API_KEY}"
    r = requests.get(url, timeout=5).json()
    return float(r["field3"])

def get_threshold():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2/last.txt?api_key={READ_API_KEY}"
    return float(requests.get(url, timeout=5).text)

def update_threshold(value):
    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field2={value}"
    requests.get(url, timeout=5)

def get_temperature_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/1.json?api_key={READ_API_KEY}&results=40"
    feeds = requests.get(url, timeout=5).json()["feeds"]
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field1"] = pd.to_numeric(df["field1"])
    return df

def get_humidity_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/3.json?api_key={READ_API_KEY}&results=40"
    feeds = requests.get(url, timeout=5).json()["feeds"]
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["field3"] = pd.to_numeric(df["field3"])
    return df

# ---------------- DATA ----------------
try:
    temperature, last_raw = get_latest_temperature()
    humidity = get_latest_humidity()
    threshold_cloud = get_threshold()

    last_update = datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
    esp32_online = (datetime.now(timezone.utc) - last_update).seconds < 60
except:
    temperature = 0.0
    humidity = 0.0
    threshold_cloud = 30.0
    esp32_online = False
    last_update = None

# ---------------- SESSION ----------------
if "threshold_ui" not in st.session_state:
    st.session_state.threshold_ui = int(threshold_cloud)

# ---------------- DYNAMIC ACCENT COLOR ----------------
def temp_accent(val):
    """Returns an accent color from cool blue -> amber -> red based on temperature."""
    ratio = min(max(val / 50, 0), 1)
    if ratio < 0.5:
        # cool blue -> warm amber
        r = int(56  + ratio * 2 * (251 - 56))
        g = int(189 + ratio * 2 * (191 - 189))
        b = int(248 - ratio * 2 * (248 - 36))
    else:
        # amber -> red
        r2 = (ratio - 0.5) * 2
        r = int(251 + r2 * (239 - 251))
        g = int(191 - r2 * 191)
        b = int(36  - r2 * 36)
    return f"rgb({r},{g},{b})"

accent = temp_accent(temperature)
alert_mode = temperature > threshold_cloud

glow = "rgba(239,68,68,0.4)" if alert_mode else "rgba(34,197,94,0.3)"
banner_bg = "rgba(239,68,68,0.15)" if alert_mode else "rgba(34,197,94,0.1)"
banner_border = "#ef4444" if alert_mode else "#22c55e"
banner_icon = "⚠️" if alert_mode else "✅"
banner_text = "Temperature exceeds threshold — check environment!" if alert_mode else "All readings within safe operating range."

status_bg = "rgba(34,197,94,0.15)" if esp32_online else "rgba(239,68,68,0.15)"
status_dot = "#22c55e" if esp32_online else "#ef4444"
status_text = "ONLINE" if esp32_online else "OFFLINE"

# ---------------- INJECT CSS ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

/* Reset */
* {{ box-sizing: border-box; }}

html, body, .stApp {{
    background-color: #06090e !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(251, 191, 36, 0.05) 0px, transparent 50%),
        radial-gradient(at 0% 100%, rgba(56, 189, 248, 0.04) 0px, transparent 50%);
    background-attachment: fixed;
    color: #f8fafc;
    font-family: 'Plus Jakarta Sans', sans-serif;
}}

/* Hide default streamlit */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding: 2.5rem !important;
    max-width: 1200px !important;
}}

/* Typography */
.space-font {{ font-family: 'Space Grotesk', sans-serif; }}

/* Animations */
@keyframes fadeInUp {{
    0% {{ opacity: 0; transform: translateY(15px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 10px {status_dot}40; }}
    50% {{ box-shadow: 0 0 20px {status_dot}80; }}
    100% {{ box-shadow: 0 0 10px {status_dot}40; }}
}}

/* Card Details */
.glass-card {{
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    animation: fadeInUp 0.6s ease-out forwards;
    opacity: 0;
}}
.glass-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    border-color: rgba(255, 255, 255, 0.1);
}}

/* Header */
.dashboard-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    background: rgba(10, 15, 28, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    margin-bottom: 2rem;
    backdrop-filter: blur(20px);
    animation: fadeInUp 0.4s ease-out forwards;
}}
.header-title-wrapper {{ display: flex; flex-direction: column; gap: 4px; }}
.header-title {{
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #f8fafc, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}}
.header-subtitle {{
    font-size: 0.85rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}

/* Status */
.header-status-wrapper {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}}
.status-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0.5rem 1.2rem;
    border-radius: 99px;
    background: {status_bg};
    border: 1px solid {status_dot}33;
    font-size: 0.8rem;
    font-weight: 600;
    color: {status_dot};
    letter-spacing: 0.05em;
}}
.status-dot-inner {{
    width: 8px; height: 8px;
    border-radius: 50%;
    background: {status_dot};
    animation: pulseGlow 2s infinite;
}}
.sync-time {{
    font-size: 0.75rem;
    color: #64748b;
    font-family: 'Space Grotesk', sans-serif;
}}

/* Metrics */
.metric-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1.2rem;
}}
.metric-value {{
    font-size: 3.2rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: baseline;
    gap: 6px;
}}
.metric-unit {{
    font-size: 1.2rem;
    font-weight: 500;
    color: #64748b;
}}
.metric-footer {{
    font-size: 0.8rem;
    color: #475569;
}}

/* Alert Banner */
.alert-container {{
    display: flex;
    align-items: center;
    gap: 1.2rem;
    padding: 1.2rem 1.5rem;
    border-radius: 16px;
    background: {banner_bg};
    border: 1px solid {banner_border}40;
    margin-bottom: 2.5rem;
    box-shadow: 0 4px 20px {glow};
    animation: fadeInUp 0.5s ease-out forwards;
}}
.alert-icon {{
    font-size: 1.4rem;
}}
.alert-text {{
    font-size: 0.95rem;
    font-weight: 500;
    color: {banner_border};
}}

/* Slider overrides */
.stSlider > div > div > div > div {{
    background: {accent} !important;
}}
.stSlider [data-testid="stThumbValue"], .stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: #f8fafc !important;
    font-size: 0.85rem !important;
}}

/* Button overrides */
.stButton > button {{
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #f8fafc !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    padding: 0.6rem 1.5rem !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}}
.stButton > button:hover {{
    background: {accent}22 !important;
    border-color: {accent}88 !important;
    color: {accent} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px {accent}30 !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* Divider */
.section-divider {{
    margin: 3rem 0 1.5rem 0;
    display: flex;
    align-items: center;
    gap: 1rem;
    animation: fadeInUp 0.7s ease-out forwards;
    opacity: 0;
}}
.section-divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
}}
.section-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
</style>
""", unsafe_allow_html=True)


# ---------------- LAYOUT ----------------

last_str = last_update.strftime('%H:%M:%S UTC') if last_update else "—"

# Header
st.markdown(f"""
<div class="dashboard-header">
  <div class="header-title-wrapper">
    <div class="header-title">ESP32 <span style="color: {accent};">Environment</span></div>
    <div class="header-subtitle">Live Sensor Analytics Dashboard</div>
  </div>
  <div class="header-status-wrapper">
    <div class="status-indicator">
      <div class="status-dot-inner"></div>
      {status_text}
    </div>
    <div class="sync-time">Last Sync: {last_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Alert Banner
st.markdown(f"""
<div class="alert-container">
  <div class="alert-icon">{banner_icon}</div>
  <div class="alert-text">{banner_text}</div>
</div>
""", unsafe_allow_html=True)

# Metrics Section
st.markdown("""
<div class="section-divider" style="animation-delay: 0.1s;">
  <span class="section-title">Live Metrics</span>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="glass-card" style="animation-delay: 0.2s; border-top: 3px solid {accent};">
      <div class="metric-header">🌡️ Temperature</div>
      <div class="metric-value space-font">{temperature:.1f} <span class="metric-unit">°C</span></div>
      <div class="metric-footer">Alarm Threshold: {threshold_cloud:.1f} °C</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="glass-card" style="animation-delay: 0.3s; border-top: 3px solid #38bdf8;">
      <div class="metric-header">💧 Humidity</div>
      <div class="metric-value space-font">{humidity:.1f} <span class="metric-unit">%</span></div>
      <div class="metric-footer">Relative Humidity</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="glass-card" style="animation-delay: 0.4s; border-top: 3px solid #a78bfa;">
      <div class="metric-header">⚙️ Active Threshold</div>
      <div class="metric-value space-font">{threshold_cloud:.1f} <span class="metric-unit">°C</span></div>
      <div class="metric-footer">ThingSpeak Cloud Value</div>
    </div>
    """, unsafe_allow_html=True)


# Configuration Section
st.markdown("""
<div class="section-divider" style="animation-delay: 0.5s;">
  <span class="section-title">Device Configuration</span>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="glass-card" style="animation-delay: 0.6s; padding-bottom: 2rem;">
      <div class="metric-header" style="margin-bottom: 2rem;">🎛️ Adjust Alert Threshold</div>
    """, unsafe_allow_html=True)
    
    new_threshold = st.slider(
        "Temperature Threshold (°C)",
        0, 50,
        st.session_state.threshold_ui,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_col, _ = st.columns([1, 4])
    with btn_col:
        if st.button("⚡ Sync to Cloud", use_container_width=True):
            update_threshold(new_threshold)
            st.session_state.threshold_ui = new_threshold
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)


# Historical Data Section
st.markdown("""
<div class="section-divider" style="animation-delay: 0.7s;">
  <span class="section-title">Historical Trends</span>
</div>
""", unsafe_allow_html=True)

col_t, col_h = st.columns(2)

with col_t:
    st.markdown(f"""
    <div class="glass-card" style="animation-delay: 0.8s;">
      <div class="metric-header" style="color: {accent};">📈 Temperature History</div>
    """, unsafe_allow_html=True)
    try:
        df_t = get_temperature_history()
        st.line_chart(
            df_t.set_index("created_at")["field1"],
            use_container_width=True,
            height=280,
            color=accent
        )
    except:
        st.warning("Temperature history unavailable")
    st.markdown("</div>", unsafe_allow_html=True)

with col_h:
    st.markdown("""
    <div class="glass-card" style="animation-delay: 0.9s;">
      <div class="metric-header" style="color: #38bdf8;">📈 Humidity History</div>
    """, unsafe_allow_html=True)
    try:
        df_h = get_humidity_history()
        st.line_chart(
            df_h.set_index("created_at")["field3"],
            use_container_width=True,
            height=280,
            color="#38bdf8"
        )
    except:
        st.warning("Humidity history unavailable")
    st.markdown("</div>", unsafe_allow_html=True)











