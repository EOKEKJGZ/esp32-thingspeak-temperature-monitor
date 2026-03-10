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
    layout="wide"
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

# ---------------- DYNAMIC GRADIENT (Blue → Red) ----------------
def temp_gradient(val):
    """
    Maps 0–50 °C to a smooth blue → red gradient pair.
    Low  = cool deep blue  (#050d2e → #0a1a5e)
    High = fiery red/amber (#5e0a0a → #2e0505)
    """
    ratio = min(max(val / 50.0, 0.0), 1.0)

    # Start colour  (cool dark blue at ratio=0)
    r1 = int(5   + ratio * 93)    # 5  → 98
    g1 = int(13  - ratio * 13)    # 13 → 0
    b1 = int(46  - ratio * 46)    # 46 → 0

    # End colour (slightly lighter tone)
    r2 = int(10  + ratio * 84)    # 10 → 94
    g2 = int(26  - ratio * 26)    # 26 → 0
    b2 = int(94  - ratio * 94)    # 94 → 0

    c1 = f"rgb({r1},{g1},{b1})"
    c2 = f"rgb({r2},{g2},{b2})"

    # Accent glow used on cards etc.
    accent_r = int(30  + ratio * 195)
    accent_g = int(120 - ratio * 120)
    accent_b = int(255 - ratio * 255)
    accent   = f"rgb({accent_r},{accent_g},{accent_b})"

    return c1, c2, accent

slider_val = st.session_state.threshold_ui
bg1, bg2, accent_color = temp_gradient(slider_val)

# Derive a readable "temperature band" label
if slider_val < 15:
    band_label = "❄️ Cool"
    band_color = "#4fc3f7"
elif slider_val < 30:
    band_label = "🌤️ Moderate"
    band_color = "#a5d6a7"
elif slider_val < 40:
    band_label = "☀️ Warm"
    band_color = "#ffb74d"
else:
    band_label = "🔥 Hot"
    band_color = "#ef5350"

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Root & Background ─────────────────────────────── */
    html, body, [class*="stApp"] {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(145deg, {bg1} 0%, {bg2} 60%, #0a0a0a 100%) !important;
        transition: background 0.6s ease;
        color: #e8eaf6;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px;
    }}

    /* ── Animated hero header ───────────────────────────── */
    .hero-header {{
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        animation: fadeSlideDown 0.7s ease both;
    }}
    .hero-title {{
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #b3e5fc, {accent_color}, #ef9a9a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }}
    .hero-sub {{
        font-size: 0.95rem;
        font-weight: 400;
        color: rgba(200,210,255,0.6);
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    /* ── Divider ────────────────────────────────────────── */
    .custom-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {accent_color}44, transparent);
        margin: 1.5rem 0;
        border: none;
    }}

    /* ── Glassmorphism cards ────────────────────────────── */
    .glass-card {{
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 1.6rem 1.4rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.45),
                    inset 0 1px 0 rgba(255,255,255,0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        animation: fadeSlideUp 0.55s ease both;
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 16px 40px rgba(0,0,0,0.55),
                    0 0 0 1px {accent_color}33;
    }}

    /* ── Metric card content ────────────────────────────── */
    .metric-label {{
        font-size: 0.70rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: rgba(200,210,255,0.55);
        margin-bottom: 0.45rem;
    }}
    .metric-value {{
        font-size: 2.3rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 0.3rem;
    }}
    .metric-icon {{
        font-size: 1.4rem;
        opacity: 0.85;
    }}

    /* ── Status pill ────────────────────────────────────── */
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 0.35rem 0.9rem;
        border-radius: 50px;
        margin-top: 0.5rem;
    }}
    .pill-online  {{ background: rgba(76,175,80,0.18);  border: 1px solid #4caf5066; color: #81c784; }}
    .pill-offline {{ background: rgba(244,67,54,0.18);  border: 1px solid #f4433666; color: #e57373; }}

    /* ── Alert banners ──────────────────────────────────── */
    .alert-danger {{
        background: linear-gradient(90deg, rgba(244,67,54,0.18), rgba(244,67,54,0.05));
        border: 1px solid rgba(244,67,54,0.35);
        border-left: 4px solid #f44336;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        color: #ef9a9a;
        font-weight: 600;
        animation: pulse-red 1.8s ease-in-out infinite;
    }}
    .alert-safe {{
        background: linear-gradient(90deg, rgba(76,175,80,0.15), rgba(76,175,80,0.04));
        border: 1px solid rgba(76,175,80,0.30);
        border-left: 4px solid #4caf50;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        color: #a5d6a7;
        font-weight: 600;
    }}

    /* ── Section heading ────────────────────────────────── */
    .section-heading {{
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #e8eaf6;
        margin-bottom: 0.8rem;
    }}

    /* ── Gradient band badge ────────────────────────────── */
    .band-badge {{
        display: inline-block;
        background: {band_color}22;
        border: 1px solid {band_color}66;
        color: {band_color};
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 0.25rem 0.75rem;
        border-radius: 50px;
        vertical-align: middle;
        margin-left: 0.6rem;
    }}

    /* ── Chart wrapper ──────────────────────────────────── */
    .chart-wrap {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.2rem 1rem 0.8rem;
        animation: fadeSlideUp 0.65s ease both;
    }}

    /* ── Streamlit widget overrides ─────────────────────── */
    div[data-testid="stSlider"] > div > div > div {{
        background: linear-gradient(90deg, #4fc3f7, {accent_color}, #ef5350) !important;
    }}
    div[data-testid="stSlider"] label {{
        color: rgba(200,210,255,0.75) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px;
    }}
    button[kind="primary"], button[data-testid="baseButton-primary"] {{
        background: linear-gradient(90deg, #1565c0, {accent_color}88) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: opacity 0.2s;
    }}
    button[kind="primary"]:hover {{
        opacity: 0.88 !important;
    }}

    /* ── Scrollbar ──────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb  {{ background: rgba(255,255,255,0.12); border-radius: 4px; }}

    /* ── Keyframes ──────────────────────────────────────── */
    @keyframes fadeSlideDown {{
        from {{ opacity:0; transform:translateY(-20px); }}
        to   {{ opacity:1; transform:translateY(0);     }}
    }}
    @keyframes fadeSlideUp {{
        from {{ opacity:0; transform:translateY(16px);  }}
        to   {{ opacity:1; transform:translateY(0);     }}
    }}
    @keyframes pulse-red {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(244,67,54,0); }}
        50%       {{ box-shadow: 0 0 10px 3px rgba(244,67,54,0.25); }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🌡️&nbsp; ESP32 Environment Monitor</div>
        <div class="hero-sub">Temperature &nbsp;·&nbsp; Humidity &nbsp;·&nbsp; IoT Dashboard</div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ============================================================
# THRESHOLD CONTROL
# ============================================================
st.markdown(
    f'<div class="section-heading">🎚️ Temperature Threshold'
    f'<span class="band-badge">{band_label}</span></div>',
    unsafe_allow_html=True,
)

new_threshold = st.slider(
    "Drag to preview threshold (°C)",
    0, 50,
    st.session_state.threshold_ui,
    key="slider_main"
)

# Live update background as slider moves
if new_threshold != st.session_state.threshold_ui:
    st.session_state.threshold_ui = new_threshold
    st.rerun()

if st.button("✅ Apply Threshold", use_container_width=True, type="primary"):
    update_threshold(new_threshold)
    st.session_state.threshold_ui = new_threshold
    st.success(f"✅ Threshold updated to **{new_threshold} °C**")

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ============================================================
# STATUS CARDS
# ============================================================
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">🌡️ Temperature</div>
        <div class="metric-value">{temperature:.1f}°<span style="font-size:1.2rem;opacity:0.7">C</span></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">💧 Humidity</div>
        <div class="metric-value">{humidity:.1f}<span style="font-size:1.2rem;opacity:0.7">%</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">🎚️ Active Threshold</div>
        <div class="metric-value">{threshold_cloud:.1f}°<span style="font-size:1.2rem;opacity:0.7">C</span></div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    pill_class = "pill-online" if esp32_online else "pill-offline"
    pill_dot   = "🟢" if esp32_online else "🔴"
    pill_text  = "ONLINE" if esp32_online else "OFFLINE"
    update_str = last_update.strftime('%H:%M:%S UTC') if last_update else "—"
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">📡 Device Status</div>
        <div class="status-pill {pill_class}">{pill_dot} ESP32 {pill_text}</div>
        <div style="margin-top:0.7rem;font-size:0.72rem;color:rgba(200,210,255,0.45);">
            Last ping &nbsp;·&nbsp; {update_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ============================================================
# ALERT BANNER
# ============================================================
if temperature > threshold_cloud:
    st.markdown(f"""
    <div class="alert-danger">
        ⚠️&nbsp; <strong>ALERT</strong> — Live temperature ({temperature:.1f} °C) exceeds the
        active threshold ({threshold_cloud:.1f} °C). Immediate action recommended.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-safe">
        ✅&nbsp; System nominal — Temperature ({temperature:.1f} °C) is within the safe
        threshold ({threshold_cloud:.1f} °C).
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# CHARTS
# ============================================================
st.markdown('<div class="section-heading">📈 Sensor History</div>', unsafe_allow_html=True)

col_t, col_h = st.columns(2, gap="medium")

with col_t:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:1px;'
        'text-transform:uppercase;color:rgba(200,210,255,0.5);margin-bottom:0.5rem;">'
        '🌡️ Temperature — last 40 readings (°C)</div>',
        unsafe_allow_html=True
    )
    try:
        df_t = get_temperature_history()
        st.line_chart(df_t.set_index("created_at")["field1"], color="#ef5350")
    except:
        st.warning("Temperature history unavailable")
    st.markdown('</div>', unsafe_allow_html=True)

with col_h:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:1px;'
        'text-transform:uppercase;color:rgba(200,210,255,0.5);margin-bottom:0.5rem;">'
        '💧 Humidity — last 40 readings (%)</div>',
        unsafe_allow_html=True
    )
    try:
        df_h = get_humidity_history()
        st.line_chart(df_h.set_index("created_at")["field3"], color="#4fc3f7")
    except:
        st.warning("Humidity history unavailable")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align:center;margin-top:3rem;font-size:0.68rem;
     color:rgba(200,210,255,0.25);letter-spacing:1.5px;text-transform:uppercase;">
    ESP32 · ThingSpeak · Streamlit &nbsp;|&nbsp; Real-time IoT Monitoring
</div>
""", unsafe_allow_html=True)
