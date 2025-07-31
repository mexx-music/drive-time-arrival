
import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math
import pytz
import time

# Grundkonfiguration
st.set_page_config(page_title="DriverRoute ETA – Wochenstunden", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# Zeitzonenfunktionen
def get_timezone_for_latlng(lat, lng):
    timestamp = int(time.time())
    tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={GOOGLE_API_KEY}"
    tz_data = requests.get(tz_url).json()
    return tz_data["timeZoneId"] if tz_data["status"] == "OK" else "Europe/Vienna"

def get_timezone_for_address(address):
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo_data = requests.get(geo_url).json()
    if geo_data["status"] == "OK":
        loc = geo_data["results"][0]["geometry"]["location"]
        return get_timezone_for_latlng(loc["lat"], loc["lng"])
    return "Europe/Vienna"

def get_local_time(address):
    tz_str = get_timezone_for_address(address)
    tz = pytz.timezone(tz_str)
    return datetime.now(tz), tz

# App-Start
st.title("🚛 DriverRoute ETA – mit Wochenstunden-Eingabe")
st.markdown("### 🕓 Wochenlenkzeit festlegen")

# Wochenlenkzeit-Eingabe
vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Benutzerdefiniert"])
if vorgabe == "Voll (56h)":
    verfügbare_woche = 56 * 60
else:
    verfügbare_woche = st.slider("Verbleibende Wochenlenkzeit (Minuten)", 0, 56 * 60, 450)

# Eingabeorte
startort = st.text_input("Startort", "Saarlouis, Deutschland")
zielort = st.text_input("Zielort", "Volos, Griechenland")
zwischenstopps = []
if st.checkbox("Zwischenstopps hinzufügen"):
    for i in range(5):
        stop = st.text_input(f"Zwischenstopp {i+1}", key=f"stop_{i}")
        if stop:
            zwischenstopps.append(stop)

# Abfahrtszeit
pause_aktiv = st.checkbox("Pause vor Abfahrt (45min)?", value=True)
abfahrt_time = st.time_input("Abfahrtszeit", value=datetime.now().time())
start_time = datetime.combine(datetime.today(), abfahrt_time)

# ETA-Berechnung simulieren
# Hier z. B. mit einfacher Strecke 1500min + Pausenlogik
total_min = 1500
if pause_aktiv:
    total_min += 45
ende = start_time + timedelta(minutes=total_min)

# Aktuelle Zeitzone für Startort
now, local_tz = get_local_time(startort)
ende = ende.replace(tzinfo=local_tz)

# Wochenzeit prüfen
verbl_10h = max(0, 2 - 2)
verbl_9h = max(0, 3 - 2)
st.info(f"📕 Noch übrig: {verbl_10h}× 10h-Fahrt, {verbl_9h}× 9h-Ruhepause")

verbleibend_min = verfügbare_woche - total_min

if verbleibend_min < 0:
    überschuss = abs(verbleibend_min)
    h_m, m_m = divmod(überschuss, 60)
    st.warning(f"⚠️ Achtung: Wochenlenkzeit überschritten um {h_m} h {m_m} min!")
    st.info("📘 Keine verbleibende Wochenlenkzeit – bereits überschritten.")
else:
    h, m = divmod(verbleibend_min, 60)
    st.info(f"🕓 Verbleibende Wochenlenkzeit: {h} h {m} min")

# Ziel-Zeitzone berechnen (letzter Zwischenstopp = Ziel)
ziel_für_zeit = zielort if not zwischenstopps else zwischenstopps[-1]
ziel_tz_str = get_timezone_for_address(ziel_für_zeit)
ziel_tz = pytz.timezone(ziel_tz_str)
ende_in_zielzeit = ende.astimezone(ziel_tz)

# Anzeige der geplanten Ankunft in Start- und Zielzeit
st.markdown(f"""
<h2 style='text-align: center; color: green;'>
✅<u>Geplante Ankunft:</u><br>
🕓 <b>{ende.strftime('%A, %d.%m.%Y – %H:%M')}</b> ({local_tz.zone})<br>
🕓 <b>{ende_in_zielzeit.strftime('%A, %d.%m.%Y – %H:%M')}</b> ({ziel_tz.zone})
</h2>
""", unsafe_allow_html=True)

# Kartenanzeige
map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
if zwischenstopps:
    waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
    map_url += f"&waypoints={waypoints_encoded}"

st.markdown("### 🗺️ Routenkarte:")
st.components.v1.iframe(map_url, height=500)
