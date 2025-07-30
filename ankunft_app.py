import streamlit as st
from geopy.geocoders import OpenCage
from streamlit_folium import st_folium
import folium
import requests

# OpenCage API-Key (Testversion)
API_KEY = "d338be0be2d34c9697b70cbfb9b2383d"
geolocator = OpenCage(api_key=API_KEY)

st.set_page_config(page_title="DriverRoute Live", layout="centered")
st.title("🚛 DriverRoute Live – Automatischer Startort & Manuelle Routenplanung")

# GPS Startort (automatisch)
st.subheader("📍 Startort (automatisch erkannt)")
start_coords = st.experimental_get_query_params().get("coords")

if start_coords:
    lat, lon = map(float, start_coords[0].split(","))
    start_location = geolocator.reverse((lat, lon), language='de')
    start_name = start_location.address if start_location else "Unbekannt"
else:
    start_name = "Standort wird ermittelt …"
    lat, lon = None, None

st.markdown(f"**Startort**: {start_name}")

# Zwischenstopps und Ziel
st.subheader("📌 Zwischenstopps (ein Ort pro Zeile)")
raw_stops = st.text_area("Zwischenziele eingeben (z. B. Kulata, Sofia)", height=120)
stop_list = [line.strip() for line in raw_stops.split("\n") if line.strip()]

zielort = st.text_input("🏁 Zielort (z. B. Saarlouis, Deutschland)")

# Geocoding
def geocode_place(place):
    try:
        location = geolocator.geocode(place)
        if location:
            return location.latitude, location.longitude
    except:
        return None

# Karte & Route anzeigen
if st.button("🗺️ Karte anzeigen"):
    coords = []

    if lat and lon:
        coords.append((lat, lon))
    else:
        st.warning("Startort nicht verfügbar – bitte GPS-Verbindung prüfen.")
        st.stop()

    for ort in stop_list:
        pos = geocode_place(ort)
        if pos:
            coords.append(pos)
        else:
            st.error(f"❌ Ort nicht gefunden: {ort}")
            st.stop()

    ziel_coords = geocode_place(zielort)
    if ziel_coords:
        coords.append(ziel_coords)
    else:
        st.error("❌ Zielort nicht gefunden.")
        st.stop()

    # Karte generieren
    m = folium.Map(location=coords[0], zoom_start=6)
    for idx, (lat, lon) in enumerate(coords):
        icon = "green" if idx == 0 else ("red" if idx == len(coords)-1 else "orange")
        folium.Marker(location=(lat, lon), tooltip=f"Stopp {idx+1}", icon=folium.Icon(color=icon)).add_to(m)
        if idx > 0:
            folium.PolyLine([coords[idx-1], coords[idx]], color="blue").add_to(m)

    st_folium(m, width=700, height=500)
