import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from datetime import datetime, timedelta

# Koordinaten
start_coords = (39.3664, 22.9425)   # Volos
ziel_coords = (49.3134, 6.7486)     # Saarlouis

# Entfernung (Luftlinie)
distanz_km = round(geodesic(start_coords, ziel_coords).km, 1)

# UI
st.set_page_config(page_title="Ankunftszeit-Rechner", layout="centered")
st.title("🚛 LKW-Ankunftszeit-Rechner")
st.markdown("**Beispielroute:** Volos 🇬🇷 → Saarlouis 🇩🇪")

# Geschwindigkeit wählen
geschwindigkeit = st.slider("Ø Geschwindigkeit (km/h)", 60, 100, 75)

# Fahrzeit berechnen
fahrzeit_stunden = round(distanz_km / geschwindigkeit, 1)

# Abfahrtszeit eingeben
abfahrt = st.time_input("Abfahrt (Uhrzeit)", value=None)

# Ausgabe
st.markdown(f"**Entfernung:** {distanz_km} km")
st.markdown(f"**Fahrzeit (geschätzt):** {fahrzeit_stunden} Stunden")

if abfahrt:
    now = datetime.now().replace(hour=abfahrt.hour, minute=abfahrt.minute, second=0, microsecond=0)
    ankunft = now + timedelta(hours=fahrzeit_stunden)
    st.markdown(f"**Voraussichtliche Ankunft:** {ankunft.strftime('%A %H:%M')} Uhr")

# Karte anzeigen
m = folium.Map(location=[(start_coords[0] + ziel_coords[0]) / 2,
                         (start_coords[1] + ziel_coords[1]) / 2],
               zoom_start=5)
folium.Marker(start_coords, tooltip="Start: Volos").add_to(m)
folium.Marker(ziel_coords, tooltip="Ziel: Saarlouis").add_to(m)
folium.PolyLine([start_coords, ziel_coords], color="blue").add_to(m)

st_folium(m, width=700, height=500)
