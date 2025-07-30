import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# API-KEYS
OPENCAGE_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

st.set_page_config(page_title="DriverRoute Live", layout="wide")
st.title("🚛 DriverRoute Live – echte LKW-Route mit Zwischenstopps")

# Adresse → Koordinaten (OpenCage)
def geocode_place(place_name):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place_name}&key={OPENCAGE_KEY}&limit=1&no_annotations=1&language=de"
    r = requests.get(url)
    if r.status_code == 200 and r.json()["results"]:
        result = r.json()["results"][0]
        return [result["geometry"]["lng"], result["geometry"]["lat"]]  # ORS benötigt [lon, lat]
    return None

# Routing über OpenRouteService
def get_route(coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
    headers = {
        'Authorization': ORS_KEY,
        'Content-Type': 'application/json'
    }
    body = {"coordinates": coords}
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# UI Eingabe
start = st.text_input("🟢 Startort", "Volos, Griechenland")

# Etappen dynamisch
if "waypoints" not in st.session_state:
    st.session_state.waypoints = [""]
if st.button("➕ Zwischenstopp hinzufügen"):
    st.session_state.waypoints.append("")

for i in range(len(st.session_state.waypoints)):
    st.session_state.waypoints[i] = st.text_input(f"🟡 Zwischenstopp {i+1}", st.session_state.waypoints[i], key=f"wp_{i}")

ziel = st.text_input("🔴 Zielort", "Saarlouis, Deutschland")

# Button zum Starten
if st.button("📍 Route berechnen & anzeigen"):
    locations = [start] + st.session_state.waypoints + [ziel]
    coords = []
    errors = []

    # Alle Orte geocodieren
    for loc in locations:
        loc = loc.strip()
        if loc:
            geo = geocode_place(loc)
            if geo:
                coords.append(geo)
            else:
                errors.append(loc)

    if errors:
        st.warning(f"Diese Orte konnten nicht gefunden werden: {', '.join(errors)}")

    # Route abrufen
    if len(coords) >= 2:
        route = get_route(coords)
        if route:
            m = folium.Map(location=coords[0][::-1], zoom_start=6)
            folium.GeoJson(route, name="Route").add_to(m)

            # Marker setzen
            for idx, point in enumerate(coords):
                folium.Marker(
                    location=point[::-1],
                    tooltip=f"{idx+1}: {locations[idx]}",
                    icon=folium.Icon(color="green" if idx == 0 else ("red" if idx == len(coords)-1 else "orange"))
                ).add_to(m)

            st.markdown("### 🗺️ Straßenkarte mit Route")
            st_folium(m, width=900, height=500)
        else:
            st.error("Fehler bei der Routenberechnung – bitte Key oder Eingabe prüfen.")
