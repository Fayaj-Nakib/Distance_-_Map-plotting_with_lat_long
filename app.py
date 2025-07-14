import streamlit as st
import pandas as pd
import folium
from math import radians, sin, cos, sqrt, atan2
from streamlit_folium import st_folium

# Page config
st.set_page_config(page_title="GPS Distance & Map Plotter", layout="wide")

st.title("GPS Distance Calculator & Map Plot")

# File Upload
uploaded_file = st.file_uploader("Upload your CSV file with Latitude and Longitude", type=["csv"])

if uploaded_file:
    # Read CSV
    df = pd.read_csv(uploaded_file)

    if "Latitude" in df.columns and "Longitude" in df.columns:
        # Calculate total distance
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371 * 1000  # Earth radius in meters
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        total_distance = 0
        for i in range(1, len(df)):
            total_distance += haversine(
                df.iloc[i-1]['Latitude'], df.iloc[i-1]['Longitude'],
                df.iloc[i]['Latitude'], df.iloc[i]['Longitude']
            )

        st.success(f"Total Distance Covered: {total_distance / 1000:.3f} km")

        # Plot on map
        start_coords = [df.iloc[0]['Latitude'], df.iloc[0]['Longitude']]
        m = folium.Map(location=start_coords, zoom_start=15)

        # Route
        points = list(zip(df['Latitude'], df['Longitude']))
        folium.PolyLine(points, color='blue', weight=3).add_to(m)
        folium.Marker(points[0], tooltip='Start', icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(points[-1], tooltip='End', icon=folium.Icon(color='red')).add_to(m)

        # Show map
        st.subheader("Map Preview")
        st_data = st_folium(m, width=700, height=500)
    else:
        st.error("Your file must contain 'Latitude' and 'Longitude' columns.")
else:
    st.info("Upload a CSV file to begin.")