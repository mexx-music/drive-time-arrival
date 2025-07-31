import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

# Konfiguration
st.set_page_config(page_title="DriverRoute ETA", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# Zeitzone über Adresse
def get_timezone_for_address(address):
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo_data = requests.get(geo_url).json()
    if geo_data["status"] == "OK":
        loc = geo_data["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        tz_data = requests.get(tz_url).json()
        return tz_data["timeZoneId"] if tz_data["status"] == "OK" else "Europe/Vienna"
    return "Europe/Vienna"

# Lokale Zeit ermitteln
def get_local_time(address):
    tz_str = get_timezone_for_address(address)
    tz = pytz.timezone(tz_str)
    return datetime.now(tz), tz

# Start der App
st.title("🚛 DriverRoute ETA – Zielzeit-Anzeige")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

# Abfahrtszeit
now_local, local_tz = get_local_time(startort)
abfahrt_datum = st.date_input("📅 Abfahrtsdatum", value=now_local.date())
abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)

# Route berechnen
if st.button("📦 Berechnen & ETA anzeigen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error("❌ Fehler bei der Routenberechnung.")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        total_min = int(km / geschwindigkeit * 60)
        st.success(f"🛣️ Strecke: {km} km – {total_min} min bei {geschwindigkeit} km/h")

        ende_utc = start_time + timedelta(minutes=total_min)
        ziel_tz_str = get_timezone_for_address(zielort)
        ziel_tz = pytz.timezone(ziel_tz_str)
        ende_zielzeit = ende_utc.astimezone(ziel_tz)

        st.markdown(f"""
        <h2 style='text-align: center; color: green;'>
        ✅ <u>Geplante Ankunft:</u><br>
        🕓 <b>{ende_zielzeit.strftime('%A, %d.%m.%Y – %H:%M')}</b> ({ziel_tz.zone})
        </h2>
        """, unsafe_allow_html=True)

        # Karte
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
