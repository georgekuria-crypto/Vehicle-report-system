import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# Set page configuration to wide layout for operational monitoring dashboards
st.set_page_config(page_title="Fleet Operational Safety Dashboard", layout="wide")

# --- DATA CLEANING HELPER FUNCTIONS ---
def parse_duration_to_seconds(val):
    """Converts telemetry duration strings (e.g., '16 s', '4 min 56 s') to numerical seconds."""
    if pd.isna(val):
        return 0.0
    val = str(val).lower().strip()
    minutes, seconds = 0, 0
    
    min_match = re.search(r'(\d+)\s*min', val)
    if min_match:
        minutes = int(min_match.group(1))
        
    sec_match = re.search(r'(\d+)\s*s', val)
    if sec_match:
        seconds = int(sec_match.group(1))
    elif not min_match:
        digits = re.findall(r'\d+', val)
        if digits:
            seconds = int(digits[0])
            
    return float((minutes * 60) + seconds)

@st.cache_data(show_spinner="Processing Telemetry Files...")
def process_uploaded_files(uploaded_files):
   
        
    """Ingests, cleans, and consolidates multiple raw Excel telemetry reports."""
    combined_df = []
    
    for file in uploaded_files:
        try:
            # Read excel sheet skipping the title metadata block (header=1)
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
            
            # Data Cleaning Pipeline
            df['Speed_kmh'] = pd.to_numeric(df['Speed'].astype(str).str.replace('km/h', '', regex=False).str.strip(),errors='coerce')
            df['Duration_seconds'] = df['Alert Duration'].apply(parse_duration_to_seconds)
            df['Alert Starting Time'] = pd.to_datetime(df['Alert Starting Time'],errors='coerce')
            df['SUMMARY'] = df['SUMMARY'].astype(str).str.strip().str.title()
            df['Hour'] = df['Alert Starting Time'].dt.hour
            df['DayOfWeek'] = df['Alert Starting Time'].dt.day_name()

            # Separate lat/long telemetry strings
            coords_split = df['Coordinates'].astype(str).str.split('/', n=1, expand=True)

            if coords_split.shape[1] >= 2:
                df['Longitude'] = pd.to_numeric(coords_split[0], errors='coerce')
                df['Latitude'] = pd.to_numeric(coords_split[1], errors='coerce')
            else:
                df['Longitude'] = np.nan
                df['Latitude'] = np.nan
            df['Longitude'] = pd.to_numeric(coords_split[0], errors='coerce')
            df['Latitude'] = pd.to_numeric(coords_split[1], errors='coerce')
            
            combined_df.append(df)
        except Exception as e:
            st.error(f"Error compiling file {file.name}: {e}")
            
    if combined_df:
        return pd.concat(combined_df, ignore_index=True)
    return None

# --- APP UI HEADER ---
st.title("📊 Weekly Fleet Operational Safety Dashboard")
st.markdown("Designed for the Head of Operations to monitor driver behavior, review hardware false alarm triggers, and trace route risk hotspots.")

# --- SIDEBAR CONTROL CONTROL PANEL ---
st.sidebar.header("📥 Ingestion Control Center")
uploaded_files = st.sidebar.file_uploader(
    "Upload Weekly Telemetry Reports (.xlsx)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("👋 Welcome! Please upload one or more vehicle telemetry Excel reports in the sidebar to populate the system diagnostics.")
else:
    # Process files into a centralized master dataframe
    df = process_uploaded_files(uploaded_files)
    st.success(f"Successfully processed {len(uploaded_files)} telemetry report(s).")

    if df is None or df.empty:
        st.error("No valid telemetry data found.")
        st.stop()
    
    if df is not None:
        # Navigation Dropdown
        st.sidebar.markdown("---")
        st.sidebar.header("🎯 Analytics View Profile")
        view_mode = st.sidebar.selectbox(
            "Select Reporting Context:",
            ["🌍 Combined Fleet Overview", "🚗 Individual Vehicle Drill-Down"]
        )
        
        # Prepare Master Context Variables
        df['Hover_Text'] = df.apply(
            lambda r: f"Alert: {r['Alert Type']}<br>Status: {r['SUMMARY']}<br>Speed: {r['Speed']}<br>Time: {r['Alert Starting Time']}", 
            axis=1
        )
        
        # Days ordering to prevent chronological visualization sorting errors
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # =====================================================================
        # CONTEXT 1: COMBINED FLEET OVERVIEW
        # =====================================================================
        if view_mode == "🌍 Combined Fleet Overview":
            st.header("🌍 Fleet-Wide Performance Diagnostics")
            
            # Compute Corporate High-Level Statistics
            total_alerts = len(df)
            false_alarms = (df['SUMMARY'] == 'Invalid').sum()
            true_violations = (df['SUMMARY'] == 'Valid').sum()
            false_alarm_rate = (false_alarms / total_alerts * 100) if total_alerts > 0 else 0
            avg_speed = df['Speed_kmh'].mean()
            
            # Display Corporate Metric Cards
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Raw Alerts Logged", f"{total_alerts:,}")
            m2.metric("True Verified Violations", f"{true_violations:,}", delta=f"-{false_alarm_rate:.1f}% AI Noise", delta_color="inverse")
            m3.metric("System False Alarm Rate", f"{false_alarm_rate:.1f}%")
            m4.metric(
                "Fleet Average Speed",
                f"{avg_speed:.1f} km/h" if pd.notna(avg_speed) else "N/A"
            )
            
            st.markdown("---")
            
            # Fleet Operational Metrics Row
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⏰ Peak Alert Windows (By Hour of Day)")
                hourly_data = df['Hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
                hourly_data.columns = ['Hour of Day', 'Alerts']
                fig_hour = px.bar(hourly_data, x='Hour of Day', y='Alerts', labels={'Hour of Day':'24h Timeline'}, color_discrete_sequence=['#1E88E5'])
                fig_hour.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
                st.plotly_chart(fig_hour, use_container_width=True)
                
            with c2:
                st.subheader("📅 Fleet Alert Dispersion (By Calendar Day)")
                day_data = df['DayOfWeek'].value_counts().reindex(days_order, fill_value=0).reset_index()
                day_data.columns = ['Day of Week', 'Alerts']
                fig_day = px.bar(day_data, x='Day of Week', y='Alerts', color='Day of Week', color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_day, use_container_width=True)
                
            # Fleet In-Depth Leaderboard Profile Table
            st.markdown("---")
            st.subheader("📋 Vehicle Operational Risk Profiles (Leaderboard)")
            
            leaderboard = df.groupby('Device Name').agg(
                Total_Triggers=('Alert Type', 'count'),
                True_Violations=('SUMMARY', lambda x: (x == 'Valid').sum()),
                False_Alarms=('SUMMARY', lambda x: (x == 'Invalid').sum()),
                Avg_Speed_kmh=('Speed_kmh', 'mean'),
                Max_Speed_kmh=('Speed_kmh', 'max')
            ).reset_index()
            leaderboard['False_Alarm_Rate_%'] = (leaderboard['False_Alarms'] / leaderboard['Total_Triggers'] * 100).round(1)
            leaderboard = leaderboard.sort_values(by='True_Violations', ascending=False)
            
            st.dataframe(leaderboard, use_container_width=True, hide_index=True)
            # Download cleaned master fleet dataset
            fleet_csv = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Cleaned Fleet Dataset",
                data=fleet_csv,
                file_name="cleaned_fleet_data.csv",
                mime="text/csv"
            )
                        
            # Regional Geospatial Map Context
            st.markdown("---")
            st.subheader("📍 National Route Infrastructure Hotspot Analysis")
            st.markdown("Zoom and hover over mapping nodes to track systemic operational cluster alerts.")
            
            fig_map = px.scatter_mapbox(
                df, lat="Latitude", lon="Longitude", color="Alert Type",
                hover_name="Device Name", hover_data={"Latitude": False, "Longitude": False, "Hover_Text": True},
                zoom=7, title="Consolidated Fleet Threat Index Map"
            )
            fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(
                fig_map,
                use_container_width=True,
                config={
                    "scrollZoom": True
                }
            )

        # =====================================================================
        # CONTEXT 2: INDIVIDUAL VEHICLE DRILL-DOWN
        # =====================================================================
        elif view_mode == "🚗 Individual Vehicle Drill-Down":
            # Dynamic filter generated based on records extracted from files
            vehicle_list = sorted(df['Device Name'].dropna().unique())
            target_vehicle = st.sidebar.selectbox("Select Target Fleet Assets:", vehicle_list)
            
            # Isolate vehicle dataset
            v_df = df[df['Device Name'] == target_vehicle].copy()
            
            st.header(f"🚗 Telemetry Diagnostic Profiling: {target_vehicle}")
            
            # Compute Unit Specific KPIs
            v_total = len(v_df)
            v_false = (v_df['SUMMARY'] == 'Invalid').sum()
            v_true = (v_df['SUMMARY'] == 'Valid').sum()
            v_false_rate = (v_false / v_total * 100) if v_total > 0 else 0
            v_max_speed = v_df['Speed_kmh'].max()
            
            # Display Asset Performance Metrics
            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Asset Total Triggers", f"{v_total:,}")
            v2.metric("Asset Verified Violations", f"{v_true:,}")
            v3.metric("Hardware False Alarm Rate", f"{v_false_rate:.1f}%")
            v4.metric("Peak Speed Recorded", f"{v_max_speed:.1f} km/h")
            
            st.markdown("---")
            
            # Visual Analysis Row
            r1, r2 = st.columns(2)
            
            with r1:
                st.subheader("⚠️ Behavioral Violations Inundation")
                alert_types = v_df['Alert Type'].value_counts().reset_index()
                alert_types.columns = ['Alert Classification', 'Count']
                fig_pie = px.pie(alert_types, names='Alert Classification', values='Count', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with r2:
                st.subheader("📅 Micro-Temporal Activity Profile")
                v_day = v_df['DayOfWeek'].value_counts().reindex(days_order, fill_value=0).reset_index()
                v_day.columns = ['Day of Week', 'Alert Count']
                fig_v_day = px.bar(v_day, x='Day of Week', y='Alert Count', color_discrete_sequence=['#FF7043'])
                st.plotly_chart(fig_v_day, use_container_width=True)
                
            # Filtered Driver Incidents Inspection Log
            st.markdown("---")
            st.subheader("🔍 True Violations Log (Actionable Remediation Events)")
            st.markdown("This database automatically filters out hardware false alarms so management can execute data-driven driver coaching.")
            
            true_logs = v_df[v_df['SUMMARY'] == 'Valid']
            true_logs = true_logs.sort_values(by='Alert Starting Time', ascending=False)
            
            if len(true_logs) == 0:
                st.success("🎉 Exceptional Compliance Score: No true driving violations verified for this asset period.")
            else:
                st.dataframe(true_logs, use_container_width=True, hide_index=True)
                
            # Asset Specific Trajectory Map
            st.markdown("---")
            st.subheader(f"🗺️ Incident Mapping Trajectory: {target_vehicle}")
            
            fig_v_map = px.scatter_mapbox(
                v_df, lat="Latitude", lon="Longitude", color="Alert Type",
                hover_data={ "Latitude": False, "Longitude": False, "Hover_Text": True},
                zoom=10, title="Asset Geo-Spatial Threat Pinpointing"
            )
            fig_v_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(
                fig_v_map,
                use_container_width=True,
                config={
                    "scrollZoom": True
                }
            )