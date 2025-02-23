import random
import geopandas as gpd
import streamlit as st
import folium
import os
import pandas as pd
from shapely.ops import unary_union
from streamlit_folium import folium_static

# Set fullscreen mode if enabled
st.set_page_config(layout="wide")

# URL for GeoJSON world data
geojson_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"

@st.cache_data
def load_data():
    """Load world map data."""
    try:
        world = gpd.read_file(geojson_url)
        world['CONTINENT'] = world['CONTINENT'].astype(str)
        return world
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

# Initialize world data in session state if not already loaded
if "world_data" not in st.session_state:
    st.session_state.world_data = load_data()

world = st.session_state.world_data  # Use session state data

if world is not None:
    # Sidebar selection
    continents = ["World"] + sorted(world['CONTINENT'].dropna().unique().tolist())
    st.sidebar.title("Select Continent")
    selected_continent = st.sidebar.selectbox("Choose a continent:", continents)
    fullscreen = st.sidebar.checkbox("Enable Full-Screen Mode", value=False)

    map_container = st.empty()
    
    # Filter world data based on selected continent
    if selected_continent == "World":
        filtered_world = world.copy()
        zoom_start = 2
        center = [0, 0]
    else:
        filtered_world = world[world['CONTINENT'] == selected_continent].copy()
        if filtered_world.empty:
            st.error("No data available for the selected continent.")
        bounds = filtered_world.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom_start = 4

    m = folium.Map(location=center, zoom_start=zoom_start, tiles="cartodb positron")
    if selected_continent != "World":
        bounds = filtered_world.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Sort countries alphabetically
    sorted_countries = sorted(filtered_world['NAME'].dropna().unique())

    selected_country = st.sidebar.selectbox("Select an attacking country:", [None] + sorted_countries)
    neighbors = []
    merged_geometry = None
    
    if selected_country:
        country_geom = filtered_world[filtered_world['NAME'] == selected_country].geometry.values[0]
        neighbors = filtered_world[filtered_world.intersects(country_geom) & (filtered_world['NAME'] != selected_country)]['NAME'].tolist()
    
        # Highlight selected country in red
        folium.GeoJson(
            filtered_world[filtered_world['NAME'] == selected_country],
            style_function=lambda x: {"fillColor": "red", "color": "black", "weight": 2, "fillOpacity": 0.9},
            tooltip=selected_country
        ).add_to(m)
    
    invaded_country = None
    if selected_country and neighbors:
        invaded_country = st.sidebar.selectbox("Choose a neighboring country to invade:", [None] + sorted(neighbors))
    
    if selected_country and invaded_country:
        selected_country_geom = filtered_world[filtered_world['NAME'] == selected_country].geometry.values[0]
        invaded_country_geom = filtered_world[filtered_world['NAME'] == invaded_country].geometry.values[0]
        
        # Merge the geometries of the selected and invaded country
        merged_geometry = unary_union([selected_country_geom, invaded_country_geom])
        
        # Create a name for the new country
        merged_name = selected_country + "-" + invaded_country
        new_name = st.sidebar.text_input("New country name:", merged_name)
        
        if new_name and st.sidebar.button("Confirm Invasion"):
            # Remove the invaded and selected countries
            st.session_state.world_data = st.session_state.world_data[~st.session_state.world_data['NAME'].isin([selected_country, invaded_country])]
            
            # Add the merged country with the new name
            new_row = gpd.GeoDataFrame({"NAME": [new_name], "geometry": [merged_geometry], "CONTINENT": [selected_continent]})
            st.session_state.world_data = pd.concat([st.session_state.world_data, new_row], ignore_index=True)
            
            st.rerun()  # Refresh the app to reflect changes

    # Redraw the map with updated data
    for _, country in filtered_world.iterrows():
        if country['NAME'] == selected_country or country['NAME'] == invaded_country:
            color = "red"
        else:
            color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

        folium.GeoJson(
            country['geometry'],
            style_function=lambda x, col=color: {
                "fillColor": col, 
                "color": "none" if country['NAME'] in [selected_country, invaded_country] else "black",  # Removes border for merged countries
                "weight": 0 if country['NAME'] in [selected_country, invaded_country] else 1,
                "fillOpacity": 0.7
            },
            tooltip=country['NAME']
        ).add_to(m)
    
    # If invasion happened, display the new merged country
    if merged_geometry is not None and new_name:
        folium.GeoJson(
            merged_geometry,
            style_function=lambda x: {"fillColor": "red", "color": "none", "weight": 0, "fillOpacity": 0.7},
            tooltip=new_name
        ).add_to(m)

    map_container.empty()
    map_container = folium_static(m, width=1600 if fullscreen else 1200, height=900 if fullscreen else 800)
    
    st.sidebar.button("Exit App", on_click=lambda: os._exit(0))
else:
    st.error("Failed to load world data.")

