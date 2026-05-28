
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
# CUSTOM STYLING
# =========================================================
st.markdown("""
<style>
.main {
    background-color: #0E1117;
}

.stMetric {
    background-color: #161B22;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #30363D;
}

h1, h2, h3 {
    color: #FAFAFA;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
}

.block-container {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS
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
# FILE PROCESSING
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

            # =====================================================
            # CLEANING
            # =====================================================

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

            # =====================================================
            # COORDINATE PROCESSING
            # =====================================================

            coords_split = (
                df['Coordinates']
                .astype(str)
                .str.split('/', n=1, expand=True)
            )

            if coords_split.shape[1] >= 2:
                df['Longitude'] = pd.to_numeric(
                    coords_split[0],
                    errors='coerce'
                )

                df['Latitude'] = pd.to_numeric(
                    coords_split[1],
                    errors='coerce'
                )

            else:
                df['Longitude'] = np.nan
                df['Latitude'] = np.nan

            # Remove invalid coordinates
            df = df.dropna(subset=['Latitude', 'Longitude'])

            # =====================================================
            # ENGINEERED FEATURES
            # =====================================================

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
# APP HEADER
# =========================================================

st.title("🚛 Fleet Operational Intelligence Center")

st.markdown("""
Real-time fleet operational analytics platform for:
- Driver behavior intelligence
- Route risk analysis
- Hardware false alarm diagnostics
- Operational hotspot mapping
- Safety performance monitoring
""")

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📥 Data Ingestion")

uploaded_files = st.sidebar.file_uploader(
    "Upload Telemetry Excel Reports",
    type=["xlsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload telemetry reports to begin analysis.")
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================

df = process_uploaded_files(uploaded_files)

if df is None or df.empty:
    st.error("No valid telemetry records found.")
    st.stop()

st.success(f"Successfully processed {len(uploaded_files)} telemetry report(s).")

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.markdown("---")
st.sidebar.header("🎯 Operational Filters")

# Alert Type Filter
alert_filter = st.sidebar.multiselect(
    "Alert Types",
    sorted(df['Alert Type'].dropna().unique()),
    default=sorted(df['Alert Type'].dropna().unique())
)

# Severity Filter
severity_filter = st.sidebar.multiselect(
    "Severity Levels",
    sorted(df['Severity'].dropna().unique()),
    default=sorted(df['Severity'].dropna().unique())
)

# Validation Filter
summary_filter = st.sidebar.multiselect(
    "Alert Validation",
    sorted(df['SUMMARY'].dropna().unique()),
    default=sorted(df['SUMMARY'].dropna().unique())
)

# Speed Filter
speed_threshold = st.sidebar.slider(
    "Minimum Speed Threshold",
    min_value=0,
    max_value=160,
    value=0
)

# Map Theme
map_style = st.sidebar.selectbox(
    "Map Theme",
    [
        "open-street-map",
        "carto-darkmatter",
        "carto-positron"
    ]
)

# View Mode
view_mode = st.sidebar.radio(
    "Analytics Context",
    [
        "🌍 Fleet Overview",
        "🚗 Vehicle Drill-Down"
    ]
)

# =========================================================
# APPLY FILTERS
# =========================================================

df = df[
    (df['Alert Type'].isin(alert_filter)) &
    (df['Severity'].isin(severity_filter)) &
    (df['SUMMARY'].isin(summary_filter)) &
    (df['Speed_kmh'] >= speed_threshold)
]

# =========================================================
# COMMON VARIABLES
# =========================================================

days_order = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]

df['Hover_Text'] = df.apply(
    lambda r:
    f"""
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

    st.header("🌍 Fleet-Wide Operational Intelligence")

    # =====================================================
    # KPIs
    # =====================================================

    total_alerts = len(df)
    false_alarms = (df['SUMMARY'] == 'Invalid').sum()
    true_violations = (df['SUMMARY'] == 'Valid').sum()

    false_alarm_rate = (
        false_alarms / total_alerts * 100
        if total_alerts > 0 else 0
    )

    avg_speed = df['Speed_kmh'].mean()
    max_speed = df['Speed_kmh'].max()

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("🚨 Total Alerts", f"{total_alerts:,}")
    k2.metric("✅ Verified Violations", f"{true_violations:,}")
    k3.metric("❌ False Alarm Rate", f"{false_alarm_rate:.1f}%")
    k4.metric("⚡ Avg Fleet Speed", f"{avg_speed:.1f} km/h")
    k5.metric("🔥 Peak Speed", f"{max_speed:.1f} km/h")

    # =====================================================
    # ALERT BANNERS
    # =====================================================

    if false_alarm_rate > 40:
        st.error("⚠️ Excessive false alarm rate detected.")

    if max_speed > 140:
        st.warning("🚨 Critical speeding incidents detected.")

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends",
        "🗺️ Maps",
        "🔥 Heatmaps",
        "📋 Leaderboards",
        "📥 Export"
    ])

    # =====================================================
    # TAB 1 - TRENDS
    # =====================================================

    with tab1:

        c1, c2 = st.columns(2)

        with c1:

            hourly_data = (
                df['Hour']
                .value_counts()
                .reindex(range(24), fill_value=0)
                .reset_index()
            )

            hourly_data.columns = ['Hour', 'Alerts']

            fig_hour = px.bar(
                hourly_data,
                x='Hour',
                y='Alerts',
                title="Peak Alert Hours",
                color='Alerts'
            )

            fig_hour.update_layout(height=450)

            st.plotly_chart(fig_hour, use_container_width=True)

        with c2:

            day_data = (
                df['DayOfWeek']
                .value_counts()
                .reindex(days_order, fill_value=0)
                .reset_index()
            )

            day_data.columns = ['Day', 'Alerts']

            fig_day = px.bar(
                day_data,
                x='Day',
                y='Alerts',
                color='Day',
                title="Alert Distribution by Day"
            )

            fig_day.update_layout(height=450)

            st.plotly_chart(fig_day, use_container_width=True)

        # Daily Trend Line
        trend = df.groupby('Date').size().reset_index(name='Alerts')

        fig_trend = px.line(
            trend,
            x='Date',
            y='Alerts',
            markers=True,
            title="Operational Alert Trend"
        )

        fig_trend.update_layout(height=500)

        st.plotly_chart(fig_trend, use_container_width=True)

    # =====================================================
    # TAB 2 - MAPS
    # =====================================================

    with tab2:

        st.subheader("📍 National Risk Hotspot Mapping")

        # Scatter Map
        fig_map = px.scatter_mapbox(
            df,
            lat="Latitude",
            lon="Longitude",
            color="Severity",
            size="Speed_kmh",
            hover_name="Device Name",
            hover_data={
                "Latitude": False,
                "Longitude": False,
                "Hover_Text": True
            },
            zoom=6,
            height=700
        )

        fig_map.update_traces(
            cluster=dict(enabled=True)
        )

        fig_map.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            config={"scrollZoom": True}
        )

        st.markdown("---")

        st.subheader("🔥 Density Risk Heatmap")

        fig_density = px.density_mapbox(
            df,
            lat='Latitude',
            lon='Longitude',
            z='Speed_kmh',
            radius=18,
            zoom=6,
            height=700
        )

        fig_density.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        st.plotly_chart(
            fig_density,
            use_container_width=True,
            config={"scrollZoom": True}
        )

    # =====================================================
    # TAB 3 - HEATMAPS
    # =====================================================

    with tab3:

        st.subheader("🔥 Operational Heat Intelligence")

        heatmap_data = df.pivot_table(
            index='DayOfWeek',
            columns='Hour',
            values='Alert Type',
            aggfunc='count'
        ).reindex(days_order)

        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(
                x="Hour",
                y="Day",
                color="Alerts"
            ),
            aspect="auto",
            title="Alert Frequency Heatmap"
        )

        fig_heat.update_layout(height=600)

        st.plotly_chart(fig_heat, use_container_width=True)

    # =====================================================
    # TAB 4 - LEADERBOARDS
    # =====================================================

    with tab4:

        st.subheader("📋 Fleet Risk Leaderboard")

        leaderboard = df.groupby('Device Name').agg(
            Total_Triggers=('Alert Type', 'count'),
            True_Violations=('SUMMARY',
                             lambda x: (x == 'Valid').sum()),
            False_Alarms=('SUMMARY',
                          lambda x: (x == 'Invalid').sum()),
            Avg_Speed=('Speed_kmh', 'mean'),
            Max_Speed=('Speed_kmh', 'max')
        ).reset_index()

        leaderboard['False_Alarm_Rate_%'] = (
            leaderboard['False_Alarms']
            / leaderboard['Total_Triggers']
            * 100
        ).round(1)

        leaderboard['Risk_Score'] = (
            leaderboard['True_Violations'] * 5
            + leaderboard['Max_Speed'] * 0.2
            - leaderboard['False_Alarms'] * 0.5
        )

        leaderboard = leaderboard.sort_values(
            by='Risk_Score',
            ascending=False
        )

        styled = leaderboard.style.background_gradient(
            subset=['Risk_Score'],
            cmap='Reds'
        )

        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True
        )

    # =====================================================
    # TAB 5 - EXPORTS
    # =====================================================

    with tab5:

        st.subheader("📥 Export Operational Dataset")

        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="📥 Download Cleaned Fleet Dataset",
            data=csv,
            file_name="fleet_operational_data.csv",
            mime="text/csv"
        )

# =========================================================
# VEHICLE DRILL-DOWN
# =========================================================

elif view_mode == "🚗 Vehicle Drill-Down":

    vehicle_list = sorted(df['Device Name'].dropna().unique())

    selected_vehicle = st.sidebar.selectbox(
        "Select Fleet Asset",
        vehicle_list
    )

    v_df = df[df['Device Name'] == selected_vehicle]

    st.header(f"🚗 Vehicle Intelligence Profile: {selected_vehicle}")

    # =====================================================
    # KPIs
    # =====================================================

    total = len(v_df)

    false = (v_df['SUMMARY'] == 'Invalid').sum()

    true = (v_df['SUMMARY'] == 'Valid').sum()

    false_rate = (
        false / total * 100
        if total > 0 else 0
    )

    max_speed = v_df['Speed_kmh'].max()

    avg_speed = v_df['Speed_kmh'].mean()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("🚨 Total Alerts", total)
    c2.metric("✅ Verified", true)
    c3.metric("❌ False Alarm %", f"{false_rate:.1f}%")
    c4.metric("⚡ Avg Speed", f"{avg_speed:.1f} km/h")
    c5.metric("🔥 Max Speed", f"{max_speed:.1f} km/h")

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Trends",
        "🗺️ Maps",
        "📋 Violations",
        "🔥 Severity"
    ])

    # =====================================================
    # TRENDS
    # =====================================================

    with tab1:

        left, right = st.columns(2)

        with left:

            alert_types = (
                v_df['Alert Type']
                .value_counts()
                .reset_index()
            )

            alert_types.columns = ['Alert', 'Count']

            fig_pie = px.pie(
                alert_types,
                names='Alert',
                values='Count',
                hole=0.5,
                title="Violation Distribution"
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        with right:

            v_day = (
                v_df['DayOfWeek']
                .value_counts()
                .reindex(days_order, fill_value=0)
                .reset_index()
            )

            v_day.columns = ['Day', 'Alerts']

            fig_day = px.bar(
                v_day,
                x='Day',
                y='Alerts',
                color='Alerts',
                title="Weekly Alert Activity"
            )

            st.plotly_chart(fig_day, use_container_width=True)

    # =====================================================
    # MAPS
    # =====================================================

    with tab2:

        fig_vehicle_map = px.scatter_mapbox(
            v_df,
            lat="Latitude",
            lon="Longitude",
            color="Severity",
            size="Speed_kmh",
            hover_name="Device Name",
            zoom=9,
            height=700
        )

        fig_vehicle_map.update_traces(
            cluster=dict(enabled=True)
        )

        fig_vehicle_map.update_layout(
            mapbox_style=map_style,
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        st.plotly_chart(
            fig_vehicle_map,
            use_container_width=True,
            config={"scrollZoom": True}
        )

    # =====================================================
    # VIOLATIONS
    # =====================================================

    with tab3:

        true_logs = v_df[v_df['SUMMARY'] == 'Valid']

        true_logs = true_logs.sort_values(
            by='Alert Starting Time',
            ascending=False
        )

        if true_logs.empty:
            st.success("No verified violations detected.")

        else:
            st.dataframe(
                true_logs,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # SEVERITY
    # =====================================================

    with tab4:

        severity_counts = (
            v_df['Severity']
            .value_counts()
            .reset_index()
        )

        severity_counts.columns = ['Severity', 'Count']

        fig_severity = px.bar(
            severity_counts,
            x='Severity',
            y='Count',
            color='Severity',
            title="Severity Distribution"
        )

        st.plotly_chart(
            fig_severity,
            use_container_width=True
        )

