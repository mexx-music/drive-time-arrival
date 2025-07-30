import streamlit as st
import openrouteservice
from openrouteservice import convert
import folium
from streamlit_folium import st_folium

# Bereinigter ORS-Key
ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=ORS_KEY)

st.title("DriverRoute Live")
st.subheader("🚚 Volos → Saarlouis (Test ohne Zwischenstopp)")

# Adressen (fix)
start_ort = "Volos, Griechenland"
ziel_ort = "Saarlouis, Deutschland"

# Geokodierung
def geocode(ort):
    geocode_result = client.pelias_search(text=ort)
    coords = geocode_result['features'][0]['geometry']['coordinates']
    return coords

try:
    coords_start = geocode(start_ort)
    coords_ziel = geocode(ziel_ort)

    # Routenberechnung
    route = client.directions(
        coordinates=[coords_start, coords_ziel],
        profile='driving-hgv',
        format='geojson'
    )

    # Karte erstellen
    m = folium.Map(location=[(coords_start[1] + coords_ziel[1]) / 2,
                             (coords_start[0] + coords_ziel[0]) / 2],
                   zoom_start=5)

    folium.Marker(
        location=[coords_start[1], coords_start[0]],
        popup="Start: Volos",
        icon=folium.Icon(color='green')
    ).add_to(m)

    folium.Marker(
        location=[coords_ziel[1], coords_ziel[0]],
        popup="Ziel: Saarlouis",
        icon=folium.Icon(color='red')
    ).add_to(m)

    folium.PolyLine(
        locations=[(lat, lon) for lon, lat in route['features'][0]['geometry']['coordinates']],
        color='blue',
        weight=4
    ).add_to(m)

    st_folium(m, width=700, height=500)

except Exception as e:
    st.error(f"Fehler bei der Routenberechnung: {e}")
