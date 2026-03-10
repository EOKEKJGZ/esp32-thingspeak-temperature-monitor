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
    page_icon="ðŸŒ¡ï¸",
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
    """Returns an accent color from cool blue â†’ amber â†’ red based on temperature."""
    ratio = min(max(val / 50, 0), 1)
    if ratio < 0.5:
        # cool blue â†’ warm amber
        r = int(56  + ratio * 2 * (251 - 56))
        g = int(189 + ratio * 2 * (191 - 189))
        b = int(248 - ratio * 2 * (248 - 36))
    else:
        # amber â†’ red
        r2 = (ratio - 0.5) * 2
        r = int(251 + r2 * (239 - 251))
        g = int(191 - r2 * 191)
        b = int(36  - r2 * 36)
    return f"rgb({r},{g},{b})"

accent = temp_accent(temperature)
alert_mode = temperature > threshold_cloud

# â”€â”€ glow color for alert banner
glow = "rgba(239,68,68,0.35)" if alert_mode else "rgba(34,197,94,0.25)"
banner_bg = "rgba(239,68,68,0.12)" if alert_mode else "rgba(34,197,94,0.08)"
banner_border = "#ef4444" if alert_mode else "#22c55e"
banner_icon = "âš ï¸" if alert_mode else "âœ…"
banner_text = "Temperature exceeds threshold â€” check your environment!" if alert_mode else "All readings within safe operating range."
banner_label = "ALERT" if alert_mode else "NOMINAL"

# â”€â”€ status pill
status_bg   = "rgba(34,197,94,0.15)"  if esp32_online else "rgba(239,68,68,0.15)"
status_dot  = "#22c55e"               if esp32_online else "#ef4444"
status_text = "ONLINE"                if esp32_online else "OFFLINE"

# â”€â”€ threshold ring gradient
thresh_pct = int((st.session_state.threshold_ui / 50) * 100)

# â”€â”€ inject CSS
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@300;400;500;600;700&display=swap');

/* â”€â”€ reset & base â”€â”€ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    background: #080c14 !important;
    color: #e2e8f0;
    font-family: 'Outfit', sans-serif;
}}

/* â”€â”€ hide default streamlit chrome â”€â”€ */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1400px !important;
}}

/* â”€â”€ animated mesh background â”€â”€ */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 10% 15%,  rgba(56,189,248,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 80%,  rgba(168,85,247,0.06) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 55% 50%,  rgba(251,191,36,0.04) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
    animation: meshShift 12s ease-in-out infinite alternate;
}}
@keyframes meshShift {{
    0%   {{ opacity: 0.7; transform: scale(1);   }}
    100% {{ opacity: 1.0; transform: scale(1.04); }}
}}

/* â”€â”€ grid noise texture â”€â”€ */
.stApp::after {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.4;
}}

/* â”€â”€ main content above overlays â”€â”€ */
.main .block-container > * {{ position: relative; z-index: 1; }}

/* â”€â”€ HEADER â”€â”€ */
.dash-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.25rem 0 1.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2rem;
    animation: fadeDown 0.6s ease both;
}}
@keyframes fadeDown {{
    from {{ opacity: 0; transform: translateY(-14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.dash-header-left {{ display: flex; flex-direction: column; gap: 4px; }}
.dash-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 0.55rem;
}}
.dash-title span.accent {{ color: {accent}; transition: color 0.6s ease; }}
.dash-subtitle {{
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

/* â”€â”€ STATUS PILL â”€â”€ */
.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 14px;
    border-radius: 100px;
    background: {status_bg};
    border: 1px solid {status_dot}44;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: {status_dot};
    animation: fadeDown 0.6s 0.2s ease both;
}}
.status-dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: {status_dot};
    box-shadow: 0 0 6px {status_dot};
    animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1);    box-shadow: 0 0 6px {status_dot}; }}
    50%       {{ opacity: 0.6; transform: scale(0.8); box-shadow: 0 0 12px {status_dot}; }}
}}
.last-update {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #475569;
    margin-top: 5px;
    text-align: right;
}}

/* â”€â”€ METRIC CARDS â”€â”€ */
.metric-card {{
    background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 1.5rem 1.6rem 1.35rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    animation: fadeUp 0.55s ease both;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border-color: rgba(255,255,255,0.14);
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--card-accent, {accent});
    opacity: 0.8;
    border-radius: 20px 20px 0 0;
}}
.metric-card::after {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 100px; height: 100px;
    border-radius: 50%;
    background: var(--card-accent, {accent});
    opacity: 0.04;
    filter: blur(20px);
}}
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.card-label {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.card-label .icon {{ font-size: 0.85rem; }}
.card-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
    color: #f1f5f9;
    letter-spacing: -0.03em;
}}
.card-value .unit {{
    font-size: 1rem;
    font-weight: 400;
    color: #64748b;
    margin-left: 3px;
}}
.card-delta {{
    margin-top: 0.55rem;
    font-size: 0.72rem;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
}}

/* â”€â”€ ALERT BANNER â”€â”€ */
.alert-banner {{
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-radius: 14px;
    border: 1px solid {banner_border}55;
    background: {banner_bg};
    margin: 1.5rem 0;
    box-shadow: 0 0 30px {glow};
    animation: fadeUp 0.4s ease both;
    position: relative;
    overflow: hidden;
}}
.alert-banner::before {{
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: {banner_border};
    border-radius: 3px 0 0 3px;
}}
.alert-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    padding: 3px 9px;
    border-radius: 6px;
    background: {banner_border}22;
    color: {banner_border};
    border: 1px solid {banner_border}44;
    white-space: nowrap;
}}
.alert-message {{
    font-size: 0.88rem;
    color: #cbd5e1;
    font-weight: 400;
}}

/* â”€â”€ THRESHOLD SECTION â”€â”€ */
.threshold-section {{
    background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 1.75rem 2rem;
    margin: 1.5rem 0;
    animation: fadeUp 0.5s 0.1s ease both;
    backdrop-filter: blur(12px);
}}
.threshold-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
}}
.threshold-title {{
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    display: flex;
    align-items: center;
    gap: 7px;
}}
.threshold-current {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    color: {accent};
    transition: color 0.5s ease;
}}

/* â”€â”€ CHART SECTION â”€â”€ */
.chart-section {{
    background: linear-gradient(145deg, rgba(255,255,255,0.035), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 1.5rem 1.75rem 1.25rem;
    animation: fadeUp 0.6s 0.2s ease both;
    backdrop-filter: blur(12px);
}}
.chart-title {{
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 7px;
}}
.chart-title .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--dot-color, {accent});
}}

/* â”€â”€ SECTION LABEL â”€â”€ */
.section-label {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #334155;
    margin: 2rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.05);
}}

/* â”€â”€ SLIDER OVERRIDES â”€â”€ */
.stSlider > div > div > div > div {{
    background: {accent} !important;
    transition: background 0.4s ease;
}}
.stSlider [data-testid="stThumbValue"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    background: #1e293b !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #f1f5f9 !important;
    border-radius: 6px !important;
}}

/* â”€â”€ BUTTON OVERRIDE â”€â”€ */
.stButton > button {{
    background: linear-gradient(135deg, {accent}22, {accent}11) !important;
    border: 1px solid {accent}55 !important;
    color: {accent} !important;
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 20px {accent}15 !important;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, {accent}35, {accent}20) !important;
    border-color: {accent}88 !important;
    box-shadow: 0 0 28px {accent}30 !important;
    transform: translateY(-1px) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* â”€â”€ SUCCESS/ERROR overrides â”€â”€ */
.stSuccess, .stError {{ border-radius: 12px !important; }}

/* â”€â”€ line chart colors â”€â”€ */
.stLineChart canvas {{ border-radius: 8px; }}

/* â”€â”€ divider â”€â”€ */
hr {{ border-color: rgba(255,255,255,0.06) !important; }}
</style>
""", unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HEADER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
last_str = last_update.strftime('%H:%M:%S UTC') if last_update else "â€”"

st.markdown(f"""
<div class="dash-header">
  <div class="dash-header-left">
    <div class="dash-title">
      ESP32 <span class="accent">Environment</span> Monitor
    </div>
    <div class="dash-subtitle">Temperature Â· Humidity Â· Threshold Control Â· ThingSpeak</div>
  </div>
  <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
    <div class="status-pill">
      <div class="status-dot"></div>
      ESP32 {status_text}
    </div>
    <div class="last-update">Last sync: {last_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ALERT BANNER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(f"""
<div class="alert-banner">
  <span style="font-size:1.3rem">{banner_icon}</span>
  <span class="alert-badge">{banner_label}</span>
  <span class="alert-message">{banner_text}</span>
</div>
""", unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# METRIC CARDS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown('<div class="section-label">Live Readings</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card" style="--card-accent: {accent}; animation-delay: 0s;">
      <div class="card-label"><span class="icon">ðŸŒ¡ï¸</span> Temperature</div>
      <div class="card-value">{temperature:.1f}<span class="unit">Â°C</span></div>
      <div class="card-delta">Threshold: {threshold_cloud:.1f} Â°C</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="--card-accent: #38bdf8; animation-delay: 0.08s;">
      <div class="card-label"><span class="icon">ðŸ’§</span> Humidity</div>
      <div class="card-value">{humidity:.1f}<span class="unit">%</span></div>
      <div class="card-delta">Relative humidity</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="--card-accent: #a78bfa; animation-delay: 0.16s;">
      <div class="card-label"><span class="icon">ðŸŽšï¸</span> Active Threshold</div>
      <div class="card-value">{threshold_cloud:.1f}<span class="unit">Â°C</span></div>
      <div class="card-delta">Cloud-synced value</div>
    </div>
    """, unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# THRESHOLD CONTROL
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown('<div class="section-label">Threshold Control</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="threshold-section">
  <div class="threshold-header">
    <div class="threshold-title">
      <span>âš™</span> Temperature Alert Threshold
    </div>
    <div class="threshold-current">{st.session_state.threshold_ui} Â°C</div>
  </div>
""", unsafe_allow_html=True)

new_threshold = st.slider(
    "Preview threshold (Â°C)",
    0, 50,
    st.session_state.threshold_ui,
    label_visibility="collapsed"
)

btn_col, _ = st.columns([1, 3])
with btn_col:
    if st.button("âš¡ Apply Threshold", use_container_width=True):
        update_threshold(new_threshold)
        st.session_state.threshold_ui = new_threshold
        st.success(f"Threshold updated â†’ {new_threshold} Â°C")

st.markdown("</div>", unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CHARTS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown('<div class="section-label">Sensor History</div>', unsafe_allow_html=True)

col_t, col_h = st.columns(2)

with col_t:
    st.markdown(f"""
    <div class="chart-section">
      <div class="chart-title">
        <div class="dot" style="--dot-color:{accent}"></div>
        Temperature over time (Â°C)
      </div>
    """, unsafe_allow_html=True)
    try:
        df_t = get_temperature_history()
        st.line_chart(
            df_t.set_index("created_at")["field1"],
            use_container_width=True,
            height=220,
            color=accent
        )
    except:
        st.warning("Temperature history unavailable")
    st.markdown("</div>", unsafe_allow_html=True)

with col_h:
    st.markdown("""
    <div class="chart-section">
      <div class="chart-title">
        <div class="dot" style="--dot-color:#38bdf8"></div>
        Humidity over time (%)
      </div>
    """, unsafe_allow_html=True)
    try:
        df_h = get_humidity_history()
        st.line_chart(
            df_h.set_index("created_at")["field3"],
            use_container_width=True,
            height=220,
            color="#38bdf8"
        )
    except:
        st.warning("Humidity history unavailable")
    st.markdown("</div>", unsafe_allow_html=True)










