import streamlit as st
import pandas as pd
import folium
from math import radians, sin, cos, sqrt, atan2
from streamlit_folium import st_folium
import tempfile
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Page config
st.set_page_config(page_title="GPS Distance & Map Plotter", layout="wide")

st.title("📍 GPS Distance Calculator & Speed Analysis")

# File Upload
uploaded_file = st.file_uploader("Upload your CSV file with Latitude and Longitude", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    expected_cols = ['SL', 'LengthGps', 'SatellitesGps', 'Latitude', 'Longitude', 'Speed', 'Course', 'DateTime']
    if list(df.columns[:8]) == expected_cols:
        st.info("Detected raw GPS format. Extracting required columns...")
    else:
        st.warning("Columns do not exactly match expected format. Proceeding anyway.")

    if "Latitude" in df.columns and "Longitude" in df.columns:
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371 * 1000
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        total_distance = 0
        idle_points = 0
        idle_duration = pd.Timedelta(0)

        df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        df['is_idle'] = df['Speed'] == 0

        for i in range(1, len(df)):
            total_distance += haversine(
                df.iloc[i-1]['Latitude'], df.iloc[i-1]['Longitude'],
                df.iloc[i]['Latitude'], df.iloc[i]['Longitude']
            )
            if df.iloc[i]['is_idle'] and pd.notnull(df.iloc[i]['DateTime']) and pd.notnull(df.iloc[i-1]['DateTime']):
                idle_duration += (df.iloc[i]['DateTime'] - df.iloc[i-1]['DateTime'])

        idle_points = df['is_idle'].sum()

        st.success(f"📏 Total Distance Covered: {total_distance / 1000:.3f} km")
        st.info(f"🕒 Idle Points: {idle_points} | Total Idle Duration: {idle_duration}")

        col1, col2 = st.columns([3, 1])

        with col1:
            start_coords = [df.iloc[0]['Latitude'], df.iloc[0]['Longitude']]
            m = folium.Map(location=start_coords, zoom_start=15)

            for _, row in df.iterrows():
                tooltip = f"Lat: {row['Latitude']}, Lon: {row['Longitude']}"
                if 'DateTime' in row:
                    tooltip += f"<br>Time: {row['DateTime']}"
                if 'Speed' in row:
                    tooltip += f"<br>Speed: {row['Speed']} km/h"
                if 'SatellitesGps' in row:
                    tooltip += f"<br>Satellites: {row['SatellitesGps']}"

                speed = row['Speed'] if 'Speed' in row and pd.notnull(row['Speed']) else 0
                if speed == 0:
                    color = 'gray'
                elif speed < 10:
                    color = 'green'
                elif speed < 20:
                    color = 'orange'
                else:
                    color = 'red'

                folium.CircleMarker(
                    location=(row['Latitude'], row['Longitude']),
                    radius=4,
                    color=color,
                    fill=True,
                    fill_opacity=0.8,
                    tooltip=folium.Tooltip(tooltip, sticky=True)
                ).add_to(m)

            for i in range(1, len(df)):
                latlon1 = (df.iloc[i-1]['Latitude'], df.iloc[i-1]['Longitude'])
                latlon2 = (df.iloc[i]['Latitude'], df.iloc[i]['Longitude'])
                speed = df.iloc[i]['Speed'] if pd.notnull(df.iloc[i]['Speed']) else 0
                if speed == 0:
                    color = 'gray'
                elif speed < 10:
                    color = 'green'
                elif speed < 20:
                    color = 'orange'
                else:
                    color = 'red'
                folium.PolyLine([latlon1, latlon2], color=color, weight=4).add_to(m)

            folium.Marker([df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], tooltip='Start', icon=folium.Icon(color='green')).add_to(m)
            folium.Marker([df.iloc[-1]['Latitude'], df.iloc[-1]['Longitude']], tooltip='End', icon=folium.Icon(color='red')).add_to(m)

            st.subheader("Map Preview")
            st_data = st_folium(m, width=700, height=500)

            temp_dir = tempfile.mkdtemp()
            html_path = os.path.join(temp_dir, "map_output.html")
            m.save(html_path)
            with open(html_path, "rb") as f:
                st.download_button("📥 Download Map as HTML", f, file_name="gps_map.html")

        with col2:
            st.subheader("Legend")
            st.markdown("""
            <div style='line-height: 1.6'>
                <span style='color: green;'>🟢 Slow (&lt;10 km/h)</span><br>
                <span style='color: orange;'>🟠 Moderate (10–19 km/h)</span><br>
                <span style='color: red;'>🔴 Fast (≥20 km/h)</span><br>
                <span style='color: gray;'>⚪ Idle (0 km/h)</span><br>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("📊 Speed Over Time")
            if 'DateTime' in df.columns:
                fig, ax = plt.subplots(figsize=(4,3))
                sns.lineplot(data=df, x='DateTime', y='Speed', ax=ax)
                ax.set_title("Speed vs. Time")
                ax.set_ylabel("Speed (km/h)")
                ax.set_xlabel("Time")
                st.pyplot(fig)
            else:
                st.warning("DateTime column is not valid for plotting speed.")

    else:
        st.error("Your file must contain 'Latitude' and 'Longitude' columns.")
else:
    st.info("Upload a CSV file to begin.")