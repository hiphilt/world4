@echo off
cd c:\world
python -m venv venv
call venv\Scripts\activate
pip install folium geopandas ipywidgets matplotlib
python world.py
deactivate