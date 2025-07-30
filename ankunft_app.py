import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# OpenCage API-Key (NEU)
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"

st.set_page_config(page_title="DriverRoute Live", layout="wide")

st.title("🚛 DriverRoute Live – LKW Ankunftszeit-Planer")

st.markdown("Gib Start und Ziel ein – dein aktueller Standort kann automatisch erkannt werden (GPS folgt bald).")

# Eingabefelder mit größerer Schrift
st.markdown("### 📍 Startort eingeben")
start_ort = st.text_input("Start", key="start_input", placeholder="z. B. Volos, Griechenland")

st.markdown("### 🎯 Zielort eingeben")
ziel_ort = st.text_input("Ziel", key="ziel_input", placeholder="z. B. Saarlouis, Deutschland")

# Funktion zur Umwandlung von Ortsnamen in Koordinaten
def get_coordinates(location):
    if not location:
        return None
    url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={OPENCAGE_API_KEY}&language=de"
    response = requests.get(url)
    data = response.json()
    if data["results"]:
        return data["results"][0]["geometry"]
    return None

# Koordinaten abrufen
start_coords = get_coordinates(start_ort)
ziel_coords = get_coordinates(ziel_ort)

# Karte anzeigen
m = folium.Map(location=[42.0, 20.0], zoom_start=5)

if start_coords:
    folium.Marker([start_coords["lat"], start_coords["lng"]],
                  tooltip="Start",
                  icon=folium.Icon(color='green')).add_to(m)

if ziel_coords:
    folium.Marker([ziel_coords["lat"], ziel_coords["lng"]],
                  tooltip="Ziel",
                  icon=folium.Icon(color='red')).add_to(m)

if start_coords and ziel_coords:
    folium.PolyLine([[start_coords["lat"], start_coords["lng"]],
                     [ziel_coords["lat"], ziel_coords["lng"]]],
                    color="blue", weight=3).add_to(m)

st.markdown("### 🗺️ Karte der gewählten Route")
st_data = st_folium(m, width=900, height=500)
