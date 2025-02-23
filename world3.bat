@echo off
cd c:\world
python -m venv venv
call venv\Scripts\activate
pip install geopandas ipywidgets matplotlib streamlit cartopy streamlit_folium
streamlit run world3.py
deactivate