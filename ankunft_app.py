import streamlit as st
from streamlit_folium import st_folium
import folium
from datetime import datetime, timedelta
import pandas as pd

# Titel
st.set_page_config(page_title="LKW-Routenplaner Prototyp")
st.title("🚛 DriverRoute Pro – Manuelle Etappen-Planung")

# Karte vorbereiten
m = folium.Map(location=[44.5, 23], zoom_start=5)
folium.TileLayer('cartodbpositron').add_to(m)
st.markdown("📍 **Klicke auf der Karte, um Wegpunkte zu setzen (Start, Etappen, Ziel).**")

# Karteninteraktion
map_data = st_folium(m, width=700, height=500)

# Punkte sammeln
if map_data and map_data.get("last_clicked"):
    if "waypoints" not in st.session_state:
        st.session_state.waypoints = []
    coords = map_data["last_clicked"]
    st.session_state.waypoints.append((coords["lat"], coords["lng"]))

# Wegpunkte anzeigen und Zeit definieren
if "waypoints" in st.session_state and st.session_state.waypoints:
    st.subheader("🛣️ Etappen definieren")
    etappen = []
    for i, (lat, lng) in enumerate(st.session_state.waypoints):
        name = st.text_input(f"🗺️ Punkt {i+1} – Beschreibung", value=f"Etappe {i+1}", key=f"name_{i}")
        zeit = st.number_input(f"⏱️ Zeit für Etappe {i+1} (in Stunden)", min_value=0.0, step=0.5, key=f"zeit_{i}")
        etappen.append({"Name": name, "Lat": lat, "Lon": lng, "Dauer (h)": zeit})

    gesamtzeit = sum(e["Dauer (h)"] for e in etappen)
    st.markdown(f"**🧮 Gesamte Fahrzeit:** {gesamtzeit} Stunden")

    abfahrt = st.time_input("🕓 Abfahrtszeit", value=datetime.now().time())
    start_datetime = datetime.now().replace(hour=abfahrt.hour, minute=abfahrt.minute, second=0, microsecond=0)
    ankunft = start_datetime + timedelta(hours=gesamtzeit)

    st.markdown(f"📍 **Geplante Ankunftszeit:** {ankunft.strftime('%A %H:%M')} Uhr")

    # Tabelle anzeigen
    df = pd.DataFrame(etappen)
    st.dataframe(df)
