
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import re

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Fleet Operational Intelligence Center",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DESIGN SYSTEM — TOKENS
# =========================================================
st.sidebar.markdown("### Appearance")
theme_mode = st.sidebar.radio("Theme Mode", ["Dark", "Light"], horizontal=True)

THEMES = {
    "Dark": {
        "bg":            "#0A0E14",
        "bg_alt":        "#0F141B",
        "surface":       "#131A23",
        "surface_2":     "#1A222D",
        "border":        "#1F2A37",
        "border_strong": "#2A3645",
        "text":          "#E6EDF3",
        "text_muted":    "#8B98A9",
        "text_dim":      "#5B6776",
        "primary":       "#3DA9FC",
        "accent":        "#7C5CFF",
        "success":       "#22C55E",
        "warning":       "#F59E0B",
        "danger":        "#EF4444",
        "critical":      "#FF3D71",
        "grad_1":        "rgba(124,92,255,0.10)",
        "grad_2":        "rgba(61,169,252,0.08)",
        "sidebar_grad1": "#0C1218",
        "sidebar_grad2": "#0A0E14",
        "hero_grad1":    "rgba(124,92,255,0.12)",
        "hero_grad2":    "rgba(61,169,252,0.08)",
        "status_bg":     "rgba(34,197,94,0.10)",
        "status_border": "rgba(34,197,94,0.30)",
        "status_text":   "#4ADE80",
        "shadow":        "rgba(0,0,0,0.25)",
        "shadow_hover":  "rgba(0,0,0,0.35)",
        "primary_shadow": "rgba(61,169,252,0.35)",
        "plotly_template": "plotly_dark",
    },
    "Light": {
        "bg":            "#F9FAFB",
        "bg_alt":        "#FFFFFF",
        "surface":       "#FFFFFF",
        "surface_2":     "#F3F4F6",
        "border":        "#E5E7EB",
        "border_strong": "#D1D5DB",
        "text":          "#111827",
        "text_muted":    "#4B5563",
        "text_dim":      "#6B7280",
        "primary":       "#0284C7",
        "accent":        "#6366F1",
        "success":       "#16A34A",
        "warning":       "#D97706",
        "danger":        "#DC2626",
        "critical":      "#E11D48",
        "grad_1":        "rgba(99,102,241,0.05)",
        "grad_2":        "rgba(2,132,199,0.05)",
        "sidebar_grad1": "#F8FAFC",
        "sidebar_grad2": "#F1F5F9",
        "hero_grad1":    "rgba(99,102,241,0.08)",
        "hero_grad2":    "rgba(2,132,199,0.05)",
        "status_bg":     "rgba(22,163,74,0.10)",
        "status_border": "rgba(22,163,74,0.30)",
        "status_text":   "#16A34A",
        "shadow":        "rgba(0,0,0,0.05)",
        "shadow_hover":  "rgba(0,0,0,0.10)",
        "primary_shadow": "rgba(2,132,199,0.25)",
        "plotly_template": "plotly_white",
    }
}

THEME = THEMES[theme_mode]

SEVERITY_COLORS = {
    "Critical": "#FF3D71",
    "High":     "#F59E0B",
    "Moderate": "#3DA9FC",
    "Low":      "#22C55E",
    "Unknown":  "#5B6776",
}

CHART_SEQUENCE = ["#3DA9FC", "#7C5CFF", "#22C55E", "#F59E0B",
                  "#EF4444", "#06B6D4", "#EC4899", "#A78BFA"]

# =========================================================
# GLOBAL CSS — ENTERPRISE DARK SYSTEM
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: radial-gradient(1200px 600px at 10% -10%, {THEME['grad_1']}, transparent 60%),
                radial-gradient(1000px 500px at 110% 10%, {THEME['grad_2']}, transparent 60%),
                {THEME['bg']} !important;
    color: {THEME['text']} !important;
}}

.block-container {{
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1600px;
}}

/* ---------- Headings ---------- */
h1, h2, h3, h4 {{
    color: {THEME['text']} !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}}
h1 {{ font-size: 2rem !important; }}
h2 {{ font-size: 1.4rem !important; }}
h3 {{ font-size: 1.1rem !important; }}

p, span, label, li {{ color: {THEME['text']}; }}

hr {{
    border: none !important;
    border-top: 1px solid {THEME['border']} !important;
    margin: 1.25rem 0 !important;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {THEME['sidebar_grad1']} 0%, {THEME['sidebar_grad2']} 100%) !important;
    border-right: 1px solid {THEME['border']} !important;
}}
section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {THEME['text_muted']} !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
}}
section[data-testid="stSidebar"] label {{
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: {THEME['text_muted']} !important;
}}

/* ---------- Inputs ---------- */
.stSelectbox > div > div,
.stMultiSelect > div > div,
div[data-baseweb="select"] > div {{
    background: {THEME['surface']} !important;
    border: 1px solid {THEME['border_strong']} !important;
    border-radius: 10px !important;
    color: {THEME['text']} !important;
}}
.stSlider [data-baseweb="slider"] > div > div {{
    background: linear-gradient(90deg, {THEME['primary']}, {THEME['accent']}) !important;
}}
.stRadio label, .stCheckbox label {{ color: {THEME['text']} !important; }}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] section {{
    background: {THEME['surface']} !important;
    border: 1.5px dashed {THEME['border_strong']} !important;
    border-radius: 12px !important;
    transition: all .2s ease;
}}
[data-testid="stFileUploader"] section:hover {{
    border-color: {THEME['primary']} !important;
    background: {THEME['surface_2']} !important;
}}

/* ---------- Native st.metric (fallback) ---------- */
[data-testid="stMetric"] {{
    background: linear-gradient(145deg, {THEME['surface']}, {THEME['surface_2']});
    padding: 18px 20px !important;
    border-radius: 14px !important;
    border: 1px solid {THEME['border']};
    box-shadow: 0 4px 20px {THEME['shadow']};
}}
[data-testid="stMetricLabel"] {{
    color: {THEME['text_muted']} !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600 !important;
}}
[data-testid="stMetricValue"] {{
    color: {THEME['text']} !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}}

/* ---------- KPI Cards (custom) ---------- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
    margin: 0.5rem 0 1.25rem;
}}
.kpi-card {{
    position: relative;
    background: linear-gradient(145deg, {THEME['surface']} 0%, {THEME['surface_2']} 100%);
    border: 1px solid {THEME['border']};
    border-radius: 16px;
    padding: 18px 20px;
    overflow: hidden;
    transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    box-shadow: 0 4px 20px {THEME['shadow']};
}}
.kpi-card:hover {{
    transform: translateY(-2px);
    border-color: {THEME['border_strong']};
    box-shadow: 0 12px 30px {THEME['shadow_hover']};
}}
.kpi-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent-bar, {THEME['primary']});
    opacity: 0.9;
}}
.kpi-head {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 8px;
}}
.kpi-label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {THEME['text_muted']};
    font-weight: 600;
}}
.kpi-icon {{
    width: 32px; height: 32px;
    display: grid; place-items: center;
    border-radius: 9px;
    background: rgba(255,255,255,0.04);
    font-size: 1rem;
}}
.kpi-value {{
    font-family: 'Inter', sans-serif;
    font-size: 1.85rem;
    font-weight: 700;
    color: {THEME['text']};
    line-height: 1.1;
    letter-spacing: -0.02em;
}}
.kpi-sub {{
    margin-top: 6px;
    font-size: 0.75rem;
    color: {THEME['text_dim']};
}}
.kpi-badge {{
    display: inline-block;
    margin-top: 8px;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

/* ---------- Section header ---------- */
.section-header {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px;
    background: linear-gradient(90deg, {THEME['surface']}, transparent);
    border-left: 3px solid {THEME['primary']};
    border-radius: 0 12px 12px 0;
    margin: 1rem 0 1rem;
}}
.section-header .dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {THEME['primary']};
    box-shadow: 0 0 12px {THEME['primary']};
}}
.section-header h2 {{
    margin: 0 !important; font-size: 1.15rem !important;
}}
.section-header .sub {{
    margin-left: auto;
    font-size: 0.78rem;
    color: {THEME['text_muted']};
}}

/* ---------- Hero header ---------- */
.hero {{
    background: linear-gradient(135deg, {THEME['hero_grad1']}, {THEME['hero_grad2']});
    border: 1px solid {THEME['border']};
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 18px;
    display: flex; align-items: center; justify-content: space-between;
    gap: 20px;
}}
.hero-title {{
    font-size: 1.6rem; font-weight: 800;
    letter-spacing: -0.02em; color: {THEME['text']};
    margin: 0;
}}
.hero-sub {{
    color: {THEME['text_muted']};
    font-size: 0.88rem; margin-top: 4px;
}}
.hero-status {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 14px;
    background: {THEME['status_bg']};
    border: 1px solid {THEME['status_border']};
    border-radius: 999px;
    font-size: 0.78rem; color: {THEME['status_text']}; font-weight: 600;
}}
.hero-status .pulse {{
    width: 8px; height: 8px; border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 0 0 rgba(34,197,94,0.7);
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }}
    70% {{ box-shadow: 0 0 0 10px rgba(34,197,94,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0); }}
}}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background: {THEME['surface']};
    padding: 6px;
    border-radius: 12px;
    border: 1px solid {THEME['border']};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 9px !important;
    padding: 10px 18px !important;
    color: {THEME['text_muted']} !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border: none !important;
    transition: all .15s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: {THEME['surface_2']} !important;
    color: {THEME['text']} !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {THEME['primary']}, {THEME['accent']}) !important;
    color: #fff !important;
    box-shadow: 0 4px 14px {THEME['primary_shadow']};
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

/* ---------- DataFrame ---------- */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    border: 1px solid {THEME['border']};
    overflow: hidden;
}}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {{
    background: linear-gradient(135deg, {THEME['primary']}, {THEME['accent']}) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    transition: transform .15s ease, box-shadow .15s ease;
    box-shadow: 0 4px 14px {THEME['primary_shadow']};
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 8px 22px {THEME['primary_shadow']};
}}

/* ---------- Alerts ---------- */
.stAlert {{
    border-radius: 12px !important;
    border: 1px solid {THEME['border']} !important;
}}

/* ---------- Plotly container ---------- */
.js-plotly-plot, .plot-container {{
    border-radius: 14px;
    overflow: hidden;
}}
.chart-wrap {{
    background: linear-gradient(145deg, {THEME['surface']}, {THEME['surface_2']});
    border: 1px solid {THEME['border']};
    border-radius: 16px;
    padding: 14px 14px 8px;
    box-shadow: 0 4px 20px {THEME['shadow']};
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {THEME['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {THEME['border_strong']}; border-radius: 6px; }}
::-webkit-scrollbar-thumb:hover {{ background: #3a4858; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# PLOTLY THEME
# =========================================================
def apply_chart_theme(fig, height=None, show_legend=True, title=None):
    fig.update_layout(
        template=THEME["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=THEME["text"], size=12),
        title=dict(
            text=title if title else (fig.layout.title.text if fig.layout.title else None),
            font=dict(size=15, color=THEME["text"], family="Inter"),
            x=0.01, xanchor="left", y=0.97,
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        hoverlabel=dict(
            bgcolor=THEME["surface_2"],
            bordercolor=THEME["border_strong"],
            font=dict(color=THEME["text"], family="Inter", size=12),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=THEME["border"],
            font=dict(color=THEME["text_muted"], size=11),
            orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
        ),
        xaxis=dict(
            gridcolor=THEME["border"], zerolinecolor=THEME["border"],
            linecolor=THEME["border_strong"], tickfont=dict(color=THEME["text_muted"]),
            title_font=dict(color=THEME["text_muted"], size=11),
        ),
        yaxis=dict(
            gridcolor=THEME["border"], zerolinecolor=THEME["border"],
            linecolor=THEME["border_strong"], tickfont=dict(color=THEME["text_muted"]),
            title_font=dict(color=THEME["text_muted"], size=11),
        ),
    )
    if height:
        fig.update_layout(height=height)
    if not show_legend:
        fig.update_layout(showlegend=False)
    return fig

# =========================================================
# UI HELPERS
# =========================================================
def kpi_card(label, value, icon="📊", accent=None, sub=None, badge=None, badge_color=None):
    accent = accent or THEME["primary"]
    badge_html = ""
    if badge:
        bc = badge_color or THEME["primary"]
        badge_html = (
            f'<div class="kpi-badge" style="background:{bc}22;color:{bc};'
            f'border:1px solid {bc}55;">{badge}</div>'
        )
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card" style="--accent-bar:{accent};">
      <div class="kpi-head">
        <div class="kpi-label">{label}</div>
        <div class="kpi-icon">{icon}</div>
      </div>
      <div class="kpi-value">{value}</div>
      {sub_html}
      {badge_html}
    </div>
    """, unsafe_allow_html=True)

def section_header(title, subtitle=None):
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
      <div class="dot"></div>
      <h2>{title}</h2>
      {sub}
    </div>
    """, unsafe_allow_html=True)

def render_kpi_row(cards):
    """cards: list of dicts with kpi_card kwargs"""
    cols = st.columns(len(cards))
    for col, c in zip(cols, cards):
        with col:
            kpi_card(**c)

# =========================================================
# HELPER FUNCTIONS  (LOGIC UNCHANGED)
# =========================================================
def parse_duration_to_seconds(val):
    if pd.isna(val):
        return 0.0

    val = str(val).lower().strip()

    minutes = 0
    seconds = 0

    min_match = re.search(r'(\d+)\s*min', val)
    sec_match = re.search(r'(\d+)\s*s', val)

    if min_match:
        minutes = int(min_match.group(1))

    if sec_match:
        seconds = int(sec_match.group(1))

    elif not min_match:
        digits = re.findall(r'\d+', val)
        if digits:
            seconds = int(digits[0])

    return float((minutes * 60) + seconds)


def classify_severity(speed):
    if pd.isna(speed):
        return "Unknown"

    if speed >= 120:
        return "Critical"
    elif speed >= 100:
        return "High"
    elif speed >= 80:
        return "Moderate"
    else:
        return "Low"


# =========================================================
# FILE PROCESSING  (LOGIC UNCHANGED)
# =========================================================
@st.cache_data(show_spinner="Processing telemetry reports...")
def process_uploaded_files(uploaded_files):

    combined_df = []

    for file in uploaded_files:

        try:
            df = pd.read_excel(file, header=1)

            df.columns = df.columns.str.strip()

            if df.empty:
                st.warning(f"{file.name} is empty.")
                continue

            required_columns = [
                'Speed',
                'Alert Duration',
                'Alert Starting Time',
                'Coordinates',
                'SUMMARY',
                'Alert Type',
                'Device Name'
            ]

            missing_cols = [c for c in required_columns if c not in df.columns]

            if missing_cols:
                st.warning(f"{file.name} missing columns: {missing_cols}")
                continue

            df['Source_File'] = file.name

            df['Speed_kmh'] = pd.to_numeric(
                df['Speed']
                .astype(str)
                .str.replace('km/h', '', regex=False)
                .str.strip(),
                errors='coerce'
            )

            df['Duration_seconds'] = df['Alert Duration'].apply(
                parse_duration_to_seconds
            )

            df['Alert Starting Time'] = pd.to_datetime(
                df['Alert Starting Time'],
                errors='coerce'
            )

            df['SUMMARY'] = (
                df['SUMMARY']
                .astype(str)
                .str.strip()
                .str.title()
            )

            df['Hour'] = df['Alert Starting Time'].dt.hour
            df['DayOfWeek'] = df['Alert Starting Time'].dt.day_name()
            df['Date'] = df['Alert Starting Time'].dt.date

            coords_split = (
                df['Coordinates']
                .astype(str)
                .str.split('/', n=1, expand=True)
            )

            if coords_split.shape[1] >= 2:
                df['Longitude'] = pd.to_numeric(coords_split[0], errors='coerce')
                df['Latitude']  = pd.to_numeric(coords_split[1], errors='coerce')
            else:
                df['Longitude'] = np.nan
                df['Latitude']  = np.nan

            df = df.dropna(subset=['Latitude', 'Longitude'])

            df['Severity'] = df['Speed_kmh'].apply(classify_severity)

            df['Critical_Risk'] = np.where(
                (df['Speed_kmh'] > 100) &
                (df['SUMMARY'] == 'Valid'),
                'Critical',
                'Normal'
            )

            combined_df.append(df)

        except Exception as e:
            st.exception(e)

    if combined_df:
        return pd.concat(combined_df, ignore_index=True)

    return None


# =========================================================
# HERO HEADER
# =========================================================
st.markdown(f"""
<div class="hero">
  <div>
    <h1 class="hero-title">🚛 Fleet Operational Intelligence Center</h1>
    <div class="hero-sub">Real-time telemetry · Driver behavior · Risk scoring · Hotspot mapping</div>
  </div>
  <div class="hero-status">
    <span class="pulse"></span> System Online
  </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR — CONTROL PANEL
# =========================================================
st.sidebar.markdown("### Data Ingestion")
uploaded_files = st.sidebar.file_uploader(
    "Upload Telemetry Excel Reports",
    type=["xlsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("📂 Upload telemetry reports from the sidebar to begin analysis.")
    st.stop()

df = process_uploaded_files(uploaded_files)

if df is None or df.empty:
    st.error("No valid telemetry records found.")
    st.stop()

st.sidebar.success(f"✓ Loaded {len(uploaded_files)} report(s)")

st.sidebar.markdown("---")
st.sidebar.markdown("### Operational Filters")

alert_filter = st.sidebar.multiselect(
    "Alert Types",
    sorted(df['Alert Type'].dropna().unique()),
    default=sorted(df['Alert Type'].dropna().unique())
)

severity_filter = st.sidebar.multiselect(
    "Severity Levels",
    sorted(df['Severity'].dropna().unique()),
    default=sorted(df['Severity'].dropna().unique())
)

summary_filter = st.sidebar.multiselect(
    "Alert Validation",
    sorted(df['SUMMARY'].dropna().unique()),
    default=sorted(df['SUMMARY'].dropna().unique())
)

speed_threshold = st.sidebar.slider(
    "Minimum Speed Threshold (km/h)",
    min_value=0, max_value=160, value=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Visualization")

map_style = st.sidebar.selectbox(
    "Map Theme",
    ["carto-darkmatter", "open-street-map", "carto-positron"]
)

view_mode = st.sidebar.radio(
    "Analytics Context",
    ["🌍 Fleet Overview", "🚗 Vehicle Drill-Down"]
)

# =========================================================
# APPLY FILTERS (LOGIC UNCHANGED)
# =========================================================
df = df[
    (df['Alert Type'].isin(alert_filter)) &
    (df['Severity'].isin(severity_filter)) &
    (df['SUMMARY'].isin(summary_filter)) &
    (df['Speed_kmh'] >= speed_threshold)
]

days_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

df['Hover_Text'] = df.apply(
    lambda r: f"""
    Device: {r['Device Name']}<br>
    Alert: {r['Alert Type']}<br>
    Severity: {r['Severity']}<br>
    Speed: {r['Speed_kmh']} km/h<br>
    Status: {r['SUMMARY']}<br>
    Time: {r['Alert Starting Time']}
    """,
    axis=1
)

# =========================================================
# FLEET OVERVIEW
# =========================================================
if view_mode == "🌍 Fleet Overview":

    section_header("Fleet-Wide Operational Intelligence",
                   f"{len(df):,} alerts across {df['Device Name'].nunique()} vehicles")

    total_alerts     = len(df)
    false_alarms     = (df['SUMMARY'] == 'Invalid').sum()
    true_violations  = (df['SUMMARY'] == 'Valid').sum()
    false_alarm_rate = (false_alarms / total_alerts * 100) if total_alerts > 0 else 0
    avg_speed        = df['Speed_kmh'].mean()
    max_speed        = df['Speed_kmh'].max()

    # ---- KPI ROW ----
    far_color = THEME["danger"] if false_alarm_rate > 40 else (THEME["warning"] if false_alarm_rate > 20 else THEME["success"])
    speed_color = THEME["critical"] if max_speed > 140 else (THEME["warning"] if max_speed > 120 else THEME["primary"])

    render_kpi_row([
        dict(label="Total Alerts",        value=f"{total_alerts:,}",      icon="🚨",
             accent=THEME["primary"], sub="All ingested events"),
        dict(label="Verified Violations", value=f"{true_violations:,}",   icon="✅",
             accent=THEME["success"], sub=f"{(true_violations/total_alerts*100 if total_alerts else 0):.1f}% of total"),
        dict(label="False Alarm Rate",    value=f"{false_alarm_rate:.1f}%", icon="❌",
             accent=far_color,
             badge=("HIGH" if false_alarm_rate > 40 else "NOMINAL"),
             badge_color=far_color),
        dict(label="Avg Fleet Speed",     value=f"{avg_speed:.1f} km/h",  icon="⚡",
             accent=THEME["accent"]),
        dict(label="Peak Speed",          value=f"{max_speed:.1f} km/h",  icon="🔥",
             accent=speed_color,
             badge=("CRITICAL" if max_speed > 140 else "OBSERVED"),
             badge_color=speed_color),
    ])

    if false_alarm_rate > 40:
        st.error("⚠️ Excessive false alarm rate detected — review hardware calibration.")
    if max_speed > 140:
        st.warning("🚨 Critical speeding incidents detected in the fleet.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends", "🗺️ Maps", "🔥 Heatmaps", "📋 Leaderboards", "📥 Export"
    ])

    # ----- TRENDS -----
    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            hourly_data = (
                df['Hour'].value_counts()
                .reindex(range(24), fill_value=0).reset_index()
            )
            hourly_data.columns = ['Hour', 'Alerts']

            fig_hour = px.bar(
                hourly_data, x='Hour', y='Alerts',
                color='Alerts', color_continuous_scale=["#1A222D","#3DA9FC","#7C5CFF","#FF3D71"],
                title="Peak Alert Hours"
            )
            fig_hour.update_traces(marker_line_width=0)
            apply_chart_theme(fig_hour, height=420, show_legend=False)
            fig_hour.update_layout(coloraxis_showscale=False, xaxis=dict(dtick=1))
            st.plotly_chart(fig_hour, use_container_width=True)

        with c2:
            day_data = (
                df['DayOfWeek'].value_counts()
                .reindex(days_order, fill_value=0).reset_index()
            )
            day_data.columns = ['Day', 'Alerts']

            fig_day = px.bar(
                day_data, x='Day', y='Alerts',
                color='Day', color_discrete_sequence=CHART_SEQUENCE,
                title="Alert Distribution by Day"
            )
            fig_day.update_traces(marker_line_width=0)
            apply_chart_theme(fig_day, height=420, show_legend=False)
            st.plotly_chart(fig_day, use_container_width=True)

        trend = df.groupby('Date').size().reset_index(name='Alerts')

        fig_trend = px.area(
            trend, x='Date', y='Alerts', markers=True,
            title="Operational Alert Trend",
            color_discrete_sequence=[THEME["primary"]]
        )
        fig_trend.update_traces(
            line=dict(width=2.5, color=THEME["primary"]),
            fillcolor="rgba(61,169,252,0.18)",
            marker=dict(size=6, color=THEME["primary"],
                        line=dict(width=2, color=THEME["bg"]))
        )
        apply_chart_theme(fig_trend, height=480, show_legend=False)
        st.plotly_chart(fig_trend, use_container_width=True)

    # ----- MAPS -----
    with tab2:
        section_header("National Risk Hotspot Mapping",
                       f"{len(df):,} geolocated events")

        fig_map = px.scatter_mapbox(
            df, lat="Latitude", lon="Longitude",
            color="Severity", size="Speed_kmh",
            color_discrete_map=SEVERITY_COLORS,
            hover_name="Device Name",
            hover_data={"Latitude": False, "Longitude": False, "Hover_Text": True},
            zoom=6, height=700
        )
        fig_map.update_traces(cluster=dict(enabled=True, color=THEME["primary"]))
        fig_map.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=THEME["text"]),
            hoverlabel=dict(bgcolor=THEME["surface_2"],
                            bordercolor=THEME["border_strong"],
                            font=dict(color=THEME["text"])),
            legend=dict(bgcolor="rgba(19,26,35,0.85)",
                        bordercolor=THEME["border"], borderwidth=1,
                        font=dict(color=THEME["text"])),
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": True})

        st.markdown("---")
        section_header("Density Risk Heatmap", "Speed-weighted incident density")

        fig_density = px.density_mapbox(
            df, lat='Latitude', lon='Longitude', z='Speed_kmh',
            radius=20, zoom=6, height=700,
            color_continuous_scale=["#0A0E14","#3DA9FC","#7C5CFF","#F59E0B","#FF3D71"],
        )
        fig_density.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(
                title=dict(text="Speed", font=dict(color=THEME["text_muted"])),
                tickfont=dict(color=THEME["text_muted"]),
                outlinewidth=0, thickness=12, len=0.5,
            ),
        )
        st.plotly_chart(fig_density, use_container_width=True, config={"scrollZoom": True})

    # ----- HEATMAPS -----
    with tab3:
        section_header("Operational Heat Intelligence",
                       "Alert frequency by day × hour")

        heatmap_data = df.pivot_table(
            index='DayOfWeek', columns='Hour',
            values='Alert Type', aggfunc='count'
        ).reindex(days_order)

        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Hour", y="Day", color="Alerts"),
            aspect="auto",
            color_continuous_scale=["#0F141B","#1A4E7A","#3DA9FC","#7C5CFF","#FF3D71"],
            title="Alert Frequency Heatmap"
        )
        apply_chart_theme(fig_heat, height=560, show_legend=False)
        fig_heat.update_layout(
            xaxis=dict(dtick=1, gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            coloraxis_colorbar=dict(
                tickfont=dict(color=THEME["text_muted"]),
                outlinewidth=0, thickness=12,
            ),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ----- LEADERBOARDS -----
    with tab4:
        section_header("Fleet Risk Leaderboard",
                       "Ranked by composite risk score")

        leaderboard = df.groupby('Device Name').agg(
            Total_Triggers=('Alert Type', 'count'),
            True_Violations=('SUMMARY', lambda x: (x == 'Valid').sum()),
            False_Alarms=('SUMMARY', lambda x: (x == 'Invalid').sum()),
            Avg_Speed=('Speed_kmh', 'mean'),
            Max_Speed=('Speed_kmh', 'max')
        ).reset_index()

        leaderboard['False_Alarm_Rate_%'] = (
            leaderboard['False_Alarms'] / leaderboard['Total_Triggers'] * 100
        ).round(1)

        leaderboard['Risk_Score'] = (
            leaderboard['True_Violations'] * 5
            + leaderboard['Max_Speed'] * 0.2
            - leaderboard['False_Alarms'] * 0.5
        )

        leaderboard = leaderboard.sort_values(by='Risk_Score', ascending=False)

        styled = (
            leaderboard.style
            .background_gradient(subset=['Risk_Score'], cmap='Reds')
            .background_gradient(subset=['Max_Speed'], cmap='Oranges')
            .format({
                'Avg_Speed': '{:.1f}',
                'Max_Speed': '{:.1f}',
                'Risk_Score': '{:.1f}',
            })
        )

        st.dataframe(styled, use_container_width=True, hide_index=True, height=560)

    # ----- EXPORT -----
    with tab5:
        section_header("Export Operational Dataset",
                       "Download the cleaned, filtered fleet dataset")

        col1, col2 = st.columns([1, 2])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Cleaned Fleet Dataset",
                data=csv,
                file_name="fleet_operational_data.csv",
                mime="text/csv"
            )
        with col2:
            st.markdown(f"""
            <div class="chart-wrap" style="padding:18px;">
              <div class="kpi-label">DATASET SUMMARY</div>
              <div style="margin-top:8px;color:{THEME['text']};font-size:0.9rem;line-height:1.7;">
                • <b>{len(df):,}</b> records<br>
                • <b>{df['Device Name'].nunique()}</b> unique vehicles<br>
                • <b>{df['Alert Type'].nunique()}</b> alert categories<br>
                • Date range: <b>{df['Date'].min()} → {df['Date'].max()}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# VEHICLE DRILL-DOWN
# =========================================================
elif view_mode == "🚗 Vehicle Drill-Down":

    vehicle_list = sorted(df['Device Name'].dropna().unique())
    selected_vehicle = st.sidebar.selectbox("Select Fleet Asset", vehicle_list)

    v_df = df[df['Device Name'] == selected_vehicle]

    section_header(f"Vehicle Intelligence Profile · {selected_vehicle}",
                   f"{len(v_df):,} events")

    total     = len(v_df)
    false     = (v_df['SUMMARY'] == 'Invalid').sum()
    true      = (v_df['SUMMARY'] == 'Valid').sum()
    false_rate= (false / total * 100) if total > 0 else 0
    max_speed = v_df['Speed_kmh'].max()
    avg_speed = v_df['Speed_kmh'].mean()

    far_color = THEME["danger"] if false_rate > 40 else (THEME["warning"] if false_rate > 20 else THEME["success"])
    speed_color = THEME["critical"] if max_speed > 140 else (THEME["warning"] if max_speed > 120 else THEME["primary"])

    render_kpi_row([
        dict(label="Total Alerts",    value=f"{total:,}",            icon="🚨", accent=THEME["primary"]),
        dict(label="Verified",        value=f"{true:,}",             icon="✅", accent=THEME["success"]),
        dict(label="False Alarm %",   value=f"{false_rate:.1f}%",    icon="❌", accent=far_color),
        dict(label="Avg Speed",       value=f"{avg_speed:.1f} km/h", icon="⚡", accent=THEME["accent"]),
        dict(label="Max Speed",       value=f"{max_speed:.1f} km/h", icon="🔥", accent=speed_color),
    ])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Trends", "🗺️ Maps", "📋 Violations", "🔥 Severity"
    ])

    with tab1:
        left, right = st.columns(2)
        with left:
            alert_types = v_df['Alert Type'].value_counts().reset_index()
            alert_types.columns = ['Alert', 'Count']
            fig_pie = px.pie(
                alert_types, names='Alert', values='Count', hole=0.6,
                title="Violation Distribution",
                color_discrete_sequence=CHART_SEQUENCE
            )
            fig_pie.update_traces(
                textposition='outside', textinfo='percent+label',
                marker=dict(line=dict(color=THEME["bg"], width=2))
            )
            apply_chart_theme(fig_pie, height=440)
            st.plotly_chart(fig_pie, use_container_width=True)

        with right:
            v_day = (
                v_df['DayOfWeek'].value_counts()
                .reindex(days_order, fill_value=0).reset_index()
            )
            v_day.columns = ['Day', 'Alerts']
            fig_day = px.bar(
                v_day, x='Day', y='Alerts', color='Alerts',
                color_continuous_scale=["#1A222D","#3DA9FC","#7C5CFF","#FF3D71"],
                title="Weekly Alert Activity"
            )
            fig_day.update_traces(marker_line_width=0)
            apply_chart_theme(fig_day, height=440, show_legend=False)
            fig_day.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_day, use_container_width=True)

    with tab2:
        fig_vehicle_map = px.scatter_mapbox(
            v_df, lat="Latitude", lon="Longitude",
            color="Severity", size="Speed_kmh",
            color_discrete_map=SEVERITY_COLORS,
            hover_name="Device Name", zoom=9, height=700
        )
        fig_vehicle_map.update_traces(cluster=dict(enabled=True, color=THEME["primary"]))
        fig_vehicle_map.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color=THEME["text"]),
            hoverlabel=dict(bgcolor=THEME["surface_2"],
                            bordercolor=THEME["border_strong"],
                            font=dict(color=THEME["text"])),
            legend=dict(bgcolor="rgba(19,26,35,0.85)",
                        bordercolor=THEME["border"], borderwidth=1,
                        font=dict(color=THEME["text"])),
        )
        st.plotly_chart(fig_vehicle_map, use_container_width=True, config={"scrollZoom": True})

    with tab3:
        true_logs = v_df[v_df['SUMMARY'] == 'Valid'].sort_values(
            by='Alert Starting Time', ascending=False
        )
        if true_logs.empty:
            st.success("✓ No verified violations detected for this vehicle.")
        else:
            st.dataframe(true_logs, use_container_width=True, hide_index=True, height=560)

    with tab4:
        severity_counts = v_df['Severity'].value_counts().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        fig_severity = px.bar(
            severity_counts, x='Severity', y='Count',
            color='Severity', color_discrete_map=SEVERITY_COLORS,
            title="Severity Distribution"
        )
        fig_severity.update_traces(marker_line_width=0)
        apply_chart_theme(fig_severity, height=480, show_legend=False)
        st.plotly_chart(fig_severity, use_container_width=True)
