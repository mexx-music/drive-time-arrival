import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="DriverRoute – Manuell", layout="centered")
st.title("🚛 DriverRoute Pro – Manuelle Orts-Eingabe mit Karte")

geolocator = Nominatim(user_agent="driver_route_app")

start = st.text_input("🟢 Startort", "Volos, Griechenland")
zwischen = st.text_area("🟡 Zwischenstopps (ein Ort pro Zeile)", "Kulata\nSofia\nCalafat\nNadlac\nWien")
ziel = st.text_input("🔴 Zielort", "Saarlouis, Deutschland")

orte = [start] + [x.strip() for x in zwischen.split("\n") if x.strip()] + [ziel]

koordinaten = []
etappen_namen = []

for ort in orte:
    try:
        location = geolocator.geocode(ort)
        if location:
            koordinaten.append((location.latitude, location.longitude))
            etappen_namen.append(location.address)
        else:
            koordinaten.append((None, None))
            etappen_namen.append(f"❌ Nicht gefunden: {ort}")
    except:
        koordinaten.append((None, None))
        etappen_namen.append(f"❌ Fehler: {ort}")

if all(k != (None, None) for k in koordinaten):
    m = folium.Map(location=koordinaten[0], zoom_start=5)
    for i, coord in enumerate(koordinaten):
        folium.Marker(coord, tooltip=f"{i+1}. {orte[i]}").add_to(m)
    folium.PolyLine(koordinaten, color="blue").add_to(m)
    st_folium(m, width=700, height=500)

    st.subheader("⏱️ Etappen-Zeiten (geschätzt)")
    etappen = []
    for i in range(len(orte) - 1):
        zeit = st.number_input(f"Fahrzeit von **{orte[i]}** → **{orte[i+1]}** (in Stunden)", min_value=0.0, step=0.5, key=f"zeit_{i}")
        etappen.append({
            "Von": orte[i],
            "Nach": orte[i+1],
            "Fahrzeit (h)": zeit
        })

    gesamtzeit = sum(e["Fahrzeit (h)"] for e in etappen)
    st.markdown(f"**🧮 Gesamte Fahrzeit:** {gesamtzeit} Stunden")

    abfahrt = st.time_input("🕓 Abfahrtszeit", value=datetime.now().time())
    start_datetime = datetime.now().replace(hour=abfahrt.hour, minute=abfahrt.minute, second=0, microsecond=0)
    ankunft = start_datetime + timedelta(hours=gesamtzeit)

    st.markdown(f"📍 **Geplante Ankunftszeit:** {ankunft.strftime('%A %H:%M')} Uhr")
    st.dataframe(pd.DataFrame(etappen))
else:
    st.warning("⚠️ Einer oder mehrere Orte konnten nicht gefunden werden.")
