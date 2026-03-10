import streamlit as st
import requests
import pandas as pd
import random
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

# ============================================================
# DYNAMIC GRADIENT (Blue → Red)
# ============================================================
def temp_gradient(val):
    ratio = min(max(val / 50.0, 0.0), 1.0)
    r1 = int(5   + ratio * 93)
    g1 = int(13  - ratio * 13)
    b1 = int(46  - ratio * 46)
    r2 = int(10  + ratio * 84)
    g2 = int(26  - ratio * 26)
    b2 = int(94  - ratio * 94)
    c1 = f"rgb({r1},{g1},{b1})"
    c2 = f"rgb({r2},{g2},{b2})"
    accent_r = int(30  + ratio * 195)
    accent_g = int(120 - ratio * 120)
    accent_b = int(255 - ratio * 255)
    accent   = f"rgb({accent_r},{accent_g},{accent_b})"
    return c1, c2, accent

slider_val = st.session_state.threshold_ui
bg1, bg2, accent_color = temp_gradient(slider_val)

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
# PARTICLE GENERATOR  (pure CSS — works inside st.markdown)
# ============================================================
def build_particles(val):
    """
    Returns an HTML string of position:fixed animated divs.
    val 0-20  → snowflakes only
    val 20-35 → blend
    val 35-50 → sand only
    Works via st.markdown because it uses only CSS, no <script>.
    """
    rng = random.Random(val)   # deterministic per slider value = no flash on rerun

    if val <= 10:
        snow_n, sand_n = 55, 0       # full snow
    elif val <= 15:
        snow_n, sand_n = 22, 0       # reduced snow
    elif val <= 34:
        snow_n, sand_n = 0, 0        # clear sky — no particles
    elif val <= 40:
        snow_n, sand_n = 0, 30       # light sand
    else:
        snow_n, sand_n = 0, 85       # full sand

    parts = []

    # ── Snowflake keyframes (defined once in CSS) ─────────────
    # ── Snowflakes ────────────────────────────────────────────
    for _ in range(snow_n):
        left     = rng.uniform(0, 100)    # vw
        size     = rng.uniform(10, 22)    # px  (character snowflake)
        dur      = rng.uniform(5, 13)     # s
        delay    = rng.uniform(-12, 0)    # s  (negative = already mid-fall at load)
        alpha    = rng.uniform(0.45, 0.95)
        drift    = rng.uniform(-40, 40)   # px horizontal drift during fall
        # Use a span with the ❄ character; CSS keyframe does the falling
        parts.append(
            f'<span style="'
            f'position:fixed;'
            f'left:{left:.1f}vw;'
            f'top:-30px;'
            f'font-size:{size:.1f}px;'
            f'opacity:{alpha:.2f};'
            f'color:rgba(210,235,255,0.92);'
            f'text-shadow:0 0 6px rgba(150,210,255,0.7);'
            f'pointer-events:none;'
            f'z-index:0;'
            f'user-select:none;'
            f'animation:snowFall {dur:.2f}s {delay:.2f}s linear infinite;'
            f'--drift:{drift:.0f}px;'
            f'will-change:transform;'
            f'">❄</span>'
        )

    # ── Sand grains ───────────────────────────────────────────
    for _ in range(sand_n):
        top      = rng.uniform(25, 100)   # vh
        w        = rng.uniform(6, 18)     # px width of grain
        h        = rng.uniform(2, 5)      # px height
        dur      = rng.uniform(4.5, 9.0)  # s  (slower = more ambient)
        delay    = rng.uniform(-5, 0)     # s
        alpha    = rng.uniform(0.30, 0.75)
        hue      = rng.randint(18, 42)    # warm sandy hue
        sat      = rng.randint(55, 80)
        lum      = rng.randint(60, 78)
        vy       = rng.uniform(-3, 3)     # tiny vertical drift, px
        parts.append(
            f'<div style="'
            f'position:fixed;'
            f'left:-20px;'
            f'top:{top:.1f}vh;'
            f'width:{w:.1f}px;'
            f'height:{h:.1f}px;'
            f'border-radius:50%;'
            f'background:hsla({hue},{sat}%,{lum}%,1);'
            f'filter:blur(0.8px);'
            f'opacity:{alpha:.2f};'
            f'pointer-events:none;'
            f'z-index:0;'
            f'animation:sandBlast {dur:.2f}s {delay:.2f}s linear infinite;'
            f'--vy:{vy:.1f}px;'
            f'will-change:transform;'
            f'"></div>'
        )

    return "\n".join(parts)


particles_html = build_particles(slider_val)

# ============================================================
# GLOBAL CSS  (includes keyframes for particles)
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
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px;
    }}

    /* ── Particle keyframes ─────────────────────────────── */
    @keyframes snowFall {{
        0%   {{ transform: translateY(0px)    translateX(0px)          rotate(0deg);   opacity: 0;   }}
        5%   {{ opacity: 1; }}
        95%  {{ opacity: 0.8; }}
        100% {{ transform: translateY(105vh) translateX(var(--drift)) rotate(360deg); opacity: 0;   }}
    }}
    @keyframes sandBlast {{
        0%   {{ transform: translateX(0px)    translateY(0px);         opacity: 0;   }}
        6%   {{ opacity: 1; }}
        94%  {{ opacity: 0.9; }}
        100% {{ transform: translateX(115vw)  translateY(var(--vy));   opacity: 0;   }}
    }}

    /* ── Animated hero header ───────────────────────────── */
    .hero-header {{
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        animation: fadeSlideDown 0.7s ease both;
        position: relative; z-index: 1;
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
        position: relative; z-index: 1;
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
        position: relative; z-index: 1;
    }}
    .alert-safe {{
        background: linear-gradient(90deg, rgba(76,175,80,0.15), rgba(76,175,80,0.04));
        border: 1px solid rgba(76,175,80,0.30);
        border-left: 4px solid #4caf50;
        border-radius: 12px;
        padding: 1rem 1.4rem;
        color: #a5d6a7;
        font-weight: 600;
        position: relative; z-index: 1;
    }}

    /* ── Section / headings ─────────────────────────────── */
    .section-heading {{
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #e8eaf6;
        margin-bottom: 0.8rem;
        position: relative; z-index: 1;
    }}
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
        position: relative; z-index: 1;
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
    button[kind="primary"]:hover {{ opacity: 0.88 !important; }}

    /* ── Scrollbar ──────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb  {{ background: rgba(255,255,255,0.12); border-radius: 4px; }}

    /* ── Generic keyframes ──────────────────────────────── */
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
# INJECT CSS PARTICLES  (position:fixed spans — visible on page)
# ============================================================
st.markdown(particles_html, unsafe_allow_html=True)

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

# Live update background + particles as slider moves
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
     color:rgba(200,210,255,0.25);letter-spacing:1.5px;text-transform:uppercase;
     position:relative;z-index:1;">
    ESP32 · ThingSpeak · Streamlit &nbsp;|&nbsp; Real-time IoT Monitoring
</div>
""", unsafe_allow_html=True)

