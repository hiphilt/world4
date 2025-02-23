import folium
import geopandas as gpd
import random
import requests
import signal
import sys
from io import BytesIO

# URL for the GeoJSON file
geojson_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"

# Download the GeoJSON data
try:
    response = requests.get(geojson_url)
    response.raise_for_status()  # Ensure request was successful
    world = gpd.read_file(BytesIO(response.content))  # Load into GeoPandas from bytes
except Exception as e:
    print(f"Error loading GeoJSON: {e}")
    sys.exit(1)

# Function to assign random color patterns
def get_random_pattern():
    patterns = ['solid', 'stripes', 'spots']
    return random.choice(patterns)

def create_pattern_map(country_name, pattern_type):
    """Assign colors based on pattern type"""
    colors = {'solid': 'blue', 'stripes': 'red', 'spots': 'green'}
    return colors.get(pattern_type, 'gray')

# Create a folium world map
m = folium.Map(location=[20, 0], zoom_start=2)

# Add countries to map with hover tooltip
for _, country in world.iterrows():
    pattern = get_random_pattern()
    color = create_pattern_map(country['ADMIN'], pattern)  # 'ADMIN' column holds country names

    folium.GeoJson(
        country['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        },
        tooltip=country['ADMIN']
    ).add_to(m)

# Save and display the map
m.save("world_map.html")
print("Map saved as world_map.html. Open it in a browser.")

# Handle Ctrl+C exit
def handle_exit_signal(sig, frame):
    print("\nApplication closed.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit_signal)