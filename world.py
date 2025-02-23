import random
import matplotlib.pyplot as plt
import geopandas as gpd
import streamlit as st
import numpy as np
import os
import folium
from shapely.geometry import MultiPolygon, unary_union
from streamlit_folium import folium_static

try:
    import cartopy.crs as ccrs
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    st.warning("Cartopy is not installed. Some map features may not work correctly.")

# Set fullscreen mode if enabled
st.set_page_config(layout="wide")

# URL for GeoJSON world data
geojson_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"

@st.cache_data
def load_data():
    try:
        world = gpd.read_file(geojson_url)
        world['CONTINENT'] = world['CONTINENT'].astype(str)
        return world
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

world = load_data()

if world is not None:
    continents = ["World"] + sorted(world['CONTINENT'].dropna().unique().tolist())
    st.sidebar.title("Select Continent")
    selected_continent = st.sidebar.selectbox("Choose a continent:", continents)
    fullscreen = st.sidebar.checkbox("Enable Full-Screen Mode", value=False)

    map_container = st.empty()
    
    if selected_continent == "World":
        filtered_world = world
        zoom_start = 2
        center = [0, 0]
    else:
        filtered_world = world[world['CONTINENT'] == selected_continent]
        if filtered_world.empty:
            st.error("No data available for the selected continent.")
        bounds = filtered_world.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom_start = 4

    m = folium.Map(location=center, zoom_start=zoom_start, tiles="cartodb positron")
    if selected_continent != "World":
        bounds = filtered_world.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    selected_country = st.sidebar.selectbox("Select a country to invade:", [None] + filtered_world['NAME'].tolist())
    neighbors = []
    
    if selected_country:
        country_geom = filtered_world[filtered_world['NAME'] == selected_country].geometry.values[0]
        neighbors = filtered_world[filtered_world.geometry.touches(country_geom)]['NAME'].tolist()
        invade_button = st.sidebar.button("Invade")
    
    if selected_country and neighbors and invade_button:
        invaded_country = st.sidebar.selectbox("Choose a neighboring country to invade:", neighbors)
        if invaded_country:
            st.session_state['merged_country'] = selected_country + "-" + invaded_country
            st.session_state['merged_geometry'] = unary_union([
                filtered_world[filtered_world['NAME'] == selected_country].geometry.values[0],
                filtered_world[filtered_world['NAME'] == invaded_country].geometry.values[0]
            ])
            new_name = st.sidebar.text_input("New country name:", st.session_state['merged_country'])
            if st.sidebar.button("Confirm Invasion"):
                world = world[~world['NAME'].isin([selected_country, invaded_country])]
                new_row = {"NAME": new_name, "geometry": st.session_state['merged_geometry'], "CONTINENT": selected_continent}
                world = world.append(new_row, ignore_index=True)
                st.rerun()
    
    for _, country in filtered_world.iterrows():
        color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        folium.GeoJson(
            country['geometry'],
            style_function=lambda x, col=color: {"fillColor": col, "color": "black", "weight": 1, "fillOpacity": 0.7},
            tooltip=country['NAME']
        ).add_to(m)

    map_container.empty()
    map_container = folium_static(m, width=1600 if fullscreen else 1200, height=900 if fullscreen else 800)
    
    st.sidebar.button("Exit App", on_click=lambda: os._exit(0))
else:
    st.error("Failed to load world data.")
