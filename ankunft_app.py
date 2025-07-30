import streamlit as st
from streamlit_folium import st_folium
import folium
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Ankunftszeit mit GPS", layout="centered")
st.title("🚛 DriveTime Pro – Ankunftszeit mit GPS-Startort")

# GPS-Ortung per Browser (funktioniert auf Mobilgeräten bei Standortfreigabe)
st.markdown("""
<script>
navigator.geolocation.getCurrentPosition(function(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    const form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("style", "display:none;");
    form.innerHTML = `<input name="lat" value="${lat}"><input name="lon" value="${lon}">`;
    document.body.appendChild(form);
    form.submit();
});
</script>
""", unsafe_allow_html=True)

# Standortdaten empfangen
lat = st.experimental_get_query_params().get("lat", [None])[0]
lon = st.experimental_get_query_params().get("lon", [None])[0]

# Karte anzeigen
if lat and lon:
    coords = (float(lat), float(lon))
    st.success(f"📍 Aktueller Standort erkannt: {coords}")
    m = folium.Map(location=coords, zoom_start=13)
    folium.Marker(location=coords, tooltip="Startposition (GPS)").add_to(m)
    st_folium(m, width=700, height=500)
else:
    st.warning("📡 Standort wird abgerufen oder du kannst ihn manuell setzen.")
    m = folium.Map(location=[44.5, 23], zoom_start=5)
    st_folium(m, width=700, height=500)

# Eingabefelder
startort_name = st.text_input("🟢 Startort-Name (optional)", "")
zielort = st.text_input("🔴 Zielort", "Saarlouis, Deutschland")
fahrzeit = st.number_input("⏱️ Geschätzte Fahrzeit (Stunden)", min_value=0.0, step=0.5)
abfahrt = st.time_input("🕓 Abfahrtszeit", value=datetime.now().time())

# Ankunftszeit berechnen
if fahrzeit > 0:
    start_datetime = datetime.now().replace(hour=abfahrt.hour, minute=abfahrt.minute, second=0, microsecond=0)
    ankunft = start_datetime + timedelta(hours=fahrzeit)
    st.markdown(f"📍 **Geplante Ankunft in {zielort}:** {ankunft.strftime('%A %H:%M')} Uhr")
