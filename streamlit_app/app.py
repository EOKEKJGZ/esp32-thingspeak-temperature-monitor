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
    page_title="Antigravity Environment Monitor",
    page_icon="💠",
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

# ---------------- DYNAMIC ACCENT & BACKGROUND COLOR ----------------
def compute_gradient(val):
    ratio = min(max(val / 50, 0), 1)
    
    # Text Accent Color (Soft Teal -> Soft Peach -> Muted Coral)
    if ratio < 0.5:
        r_acc = int(94 + ratio * 2 * (255 - 94))
        g_acc = int(234 + ratio * 2 * (218 - 234))
        b_acc = int(212 + ratio * 2 * (185 - 212))
    else:
        r2 = (ratio - 0.5) * 2
        r_acc = int(255 + r2 * (248 - 255))
        g_acc = int(218 - r2 * (113 - 218))
        b_acc = int(185 - r2 * (113 - 185))
        
    accent_hex = f"#{r_acc:02x}{g_acc:02x}{b_acc:02x}"
    
    # Premium Soothing Background Base (Deep Navy / Midnight Space)
    bg_color = "#080b12"
        
    return accent_hex, bg_color

current_ui_temp = st.session_state.threshold_ui
accent, bg_color = compute_gradient(current_ui_temp)

alert_mode = temperature > threshold_cloud

glow = "rgba(248, 113, 113, 0.4)" if alert_mode else "rgba(94, 234, 212, 0.3)"
banner_bg = "rgba(248, 113, 113, 0.12)" if alert_mode else "rgba(94, 234, 212, 0.08)"
banner_border = "#f87171" if alert_mode else "#5eead4"
banner_icon = "⚠️" if alert_mode else "✨"
banner_text = "Critical Environment Alert: Threshold Exceeded." if alert_mode else "Environment is operating seamlessly."

status_bg = "rgba(94, 234, 212, 0.15)" if esp32_online else "rgba(248, 113, 113, 0.15)"
status_dot = "#5eead4" if esp32_online else "#f87171"
status_text = "ONLINE" if esp32_online else "OFFLINE"

# ---------------- INJECT CSS ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Reset */
* {{ box-sizing: border-box; }}

/* 
  PREMIUM SOOTHING BACKGROUND 
  Soft, glowing orbs on a deep midnight canvas.
*/
html, body, .stApp {{
    background-color: {bg_color} !important;
    background-image: 
        radial-gradient(circle at 10% 40%, rgba(45, 212, 191, 0.05), transparent 45%),
        radial-gradient(circle at 90% 20%, rgba(139, 92, 246, 0.06), transparent 50%),
        radial-gradient(circle at 50% 90%, rgba(56, 189, 248, 0.04), transparent 60%);
    background-attachment: fixed;
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
}}

/* Elegant light noise */
.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    opacity: 0.025;
    z-index: 0;
    pointer-events: none;
    background: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}}

/* Hide default streamlit */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding: 3rem 4rem !important;
    max-width: 1400px !important;
    z-index: 1;
    position: relative;
}}

/* Typography */
.mono-font {{ font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }}

/* Animations */
@keyframes fadeClipIn {{
    0% {{ opacity: 0; clip-path: polygon(0 100%, 100% 100%, 100% 100%, 0 100%); transform: translateY(20px); }}
    100% {{ opacity: 1; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%); transform: translateY(0); }}
}}
@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 10px {status_dot}40; }}
    50% {{ box-shadow: 0 0 25px {status_dot}90; }}
    100% {{ box-shadow: 0 0 10px {status_dot}40; }}
}}

/* Premium Glass Cards */
.ag-card {{
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(20px) saturate(120%);
    -webkit-backdrop-filter: blur(20px) saturate(120%);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease, border-color 0.4s ease;
    animation: fadeClipIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    opacity: 0;
}}
.ag-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    border-color: rgba(255, 255, 255, 0.1);
}}

/* Header */
.dashboard-header {{
    position: relative;
    padding-bottom: 2.5rem;
    margin-bottom: 3rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    animation: fadeClipIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
.header-title-wrapper {{ display: flex; flex-direction: column; gap: 8px; }}
.header-title {{
    font-size: 2.5rem;
    font-weight: 500;
    letter-spacing: -0.04em;
    color: #ffffff;
    line-height: 1.1;
}}
.header-title span {{
    color: {accent};
    font-weight: 600;
    transition: color 0.8s ease;
}}
.header-subtitle {{
    font-size: 0.95rem;
    color: #a1a1aa;
    font-weight: 400;
    letter-spacing: 0.02em;
    font-family: 'JetBrains Mono', monospace;
}}

/* Status */
.header-status-wrapper {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
}}
.status-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 0.6rem 1.4rem;
    border-radius: 99px;
    background: {status_bg};
    border: 1px solid {status_dot}40;
    font-size: 0.85rem;
    font-weight: 500;
    color: #fff;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}}
.status-dot-inner {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: {status_dot};
    box-shadow: 0 0 12px {status_dot};
    animation: pulseGlow 2s infinite;
}}
.sync-time {{
    font-size: 0.75rem;
    color: #71717a;
    font-family: 'JetBrains Mono', monospace;
}}

/* Metrics */
.metric-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9rem;
    font-weight: 500;
    color: #a1a1aa;
    letter-spacing: 0.01em;
    margin-bottom: 1.5rem;
}}
.metric-header .icon {{ font-size: 1.2rem; }}
.metric-value {{
    font-size: 3.8rem;
    font-weight: 300;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 1rem;
    display: flex;
    align-items: baseline;
    gap: 8px;
    letter-spacing: -0.05em;
}}
.metric-unit {{
    font-size: 1.25rem;
    font-weight: 400;
    color: #71717a;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0;
}}
.metric-footer {{
    font-size: 0.85rem;
    color: #52525b;
    font-family: 'JetBrains Mono', monospace;
}}

/* Alert Banner */
.alert-container {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.25rem 2rem;
    border-radius: 100px;
    background: {banner_bg};
    border: 1px solid {banner_border}50;
    margin-bottom: 3.5rem;
    box-shadow: 0 8px 30px {glow};
    animation: fadeClipIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    backdrop-filter: blur(12px);
}}
.alert-icon {{
    font-size: 1.2rem;
    background: {banner_border}20;
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
}}
.alert-text {{
    font-size: 0.95rem;
    font-weight: 500;
    color: #fff;
    letter-spacing: 0.02em;
}}

/* Slider overrides */
.stSlider > div > div > div > div {{
    background: {accent} !important;
    transition: background-color 0.8s ease;
}}
.stSlider [data-testid="stThumbValue"] {{
    font-family: 'JetBrains Mono', monospace !important;
    color: #fff !important;
    background: rgba(255,255,255,0.1) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    font-size: 0.85rem !important;
    border-radius: 6px !important;
}}

/* Button overrides */
.stButton > button {{
    background: {accent} !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #000 !important;
    border-radius: 100px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    padding: 0.75rem 2rem !important;
    box-shadow: 0 8px 25px {accent}40 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 12px 35px {accent}60, inset 0 0 0 1px rgba(255,255,255,0.4) !important;
    filter: brightness(1.1);
}}
.stButton > button:active {{
    transform: translateY(1px) scale(0.98) !important;
    box-shadow: 0 4px 15px {accent}20 !important;
}}

/* Section Titles */
.section-title {{
    font-size: 1rem;
    font-weight: 500;
    color: #fff;
    margin: 4rem 0 2rem 0;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    animation: fadeClipIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    opacity: 0;
}}
.section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
}}
</style>
""", unsafe_allow_html=True)


# ---------------- LAYOUT ----------------

last_str = last_update.strftime('%H:%M:%S UTC') if last_update else "—"

# Header
st.markdown(f"""
<div class="dashboard-header">
  <div class="header-title-wrapper">
    <div class="header-title">Antigravity <span>Nexus</span></div>
    <div class="header-subtitle">// SENSOR ANALYTICS NODE V2</div>
  </div>
  <div class="header-status-wrapper">
    <div class="status-indicator">
      <div class="status-dot-inner"></div>
      SYS.{status_text}
    </div>
    <div class="sync-time">REF: {last_str}</div>
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
<div class="section-title" style="animation-delay: 0.1s;">Live Telemetry</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="ag-card" style="animation-delay: 0.15s; position: relative; overflow: hidden;">
      <div style="position: absolute; top:0; left:0; right:0; height: 3px; background: {accent};"></div>
      <div class="metric-header"><span class="icon">🌡️</span> Core Temperature</div>
      <div class="metric-value mono-font">{temperature:.1f} <span class="metric-unit">°C</span></div>
      <div class="metric-footer">Alarm Setpoint: {threshold_cloud:.1f}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="ag-card" style="animation-delay: 0.25s; position: relative; overflow: hidden;">
      <div style="position: absolute; top:0; left:0; right:0; height: 3px; background: #4895ef;"></div>
      <div class="metric-header"><span class="icon">💧</span> Ambient Humidity</div>
      <div class="metric-value mono-font">{humidity:.1f} <span class="metric-unit">%</span></div>
      <div class="metric-footer">Relative Saturation</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="ag-card" style="animation-delay: 0.35s; position: relative; overflow: hidden;">
      <div style="position: absolute; top:0; left:0; right:0; height: 3px; background: #a1a1aa;"></div>
      <div class="metric-header"><span class="icon">⚙️</span> Configured Threshold</div>
      <div class="metric-value mono-font">{threshold_cloud:.1f} <span class="metric-unit">°C</span></div>
      <div class="metric-footer">Cloud Sync Registry</div>
    </div>
    """, unsafe_allow_html=True)


# Configuration Section
st.markdown("""
<div class="section-title" style="animation-delay: 0.45s;">System Configuration</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="ag-card" style="animation-delay: 0.55s; padding-bottom: 2.5rem;">
      <div class="metric-header" style="margin-bottom: 2.5rem; font-size: 1rem;"><span class="icon">🎛️</span> Dynamic Threshold Control</div>
    """, unsafe_allow_html=True)
    
    new_threshold = st.slider(
        "Temperature Threshold (°C)",
        0, 50,
        st.session_state.threshold_ui,
        label_visibility="collapsed"
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    btn_col, _ = st.columns([1, 4])
    with btn_col:
        # We hook directly to the rerender to trigger the background!
        if st.button("Initialize Sync", use_container_width=True):
            update_threshold(new_threshold)
            st.session_state.threshold_ui = new_threshold
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)


# Historical Data Section
st.markdown("""
<div class="section-title" style="animation-delay: 0.65s;">Historical Telemetry</div>
""", unsafe_allow_html=True)

col_t, col_h = st.columns(2)

with col_t:
    st.markdown(f"""
    <div class="ag-card" style="animation-delay: 0.75s;">
      <div class="metric-header" style="color: {accent};"><span class="icon">📈</span> Thermal History</div>
    """, unsafe_allow_html=True)
    try:
        df_t = get_temperature_history()
        st.line_chart(
            df_t.set_index("created_at")["field1"],
            use_container_width=True,
            height=300,
            color=accent
        )
    except:
        st.warning("Telemetry stream unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_h:
    st.markdown("""
    <div class="ag-card" style="animation-delay: 0.85s;">
      <div class="metric-header" style="color: #4895ef;"><span class="icon">📈</span> Humidity History</div>
    """, unsafe_allow_html=True)
    try:
        df_h = get_humidity_history()
        st.line_chart(
            df_h.set_index("created_at")["field3"],
            use_container_width=True,
            height=300,
            color="#4895ef"
        )
    except:
        st.warning("Telemetry stream unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)
