import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Wochenstunden", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

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

st.title("🚛 DriverRoute ETA – mit Wochenstunden-Eingabe")

startort = st.text_input("📍 Startort", "Saarlouis, Deutschland")
zielort = st.text_input("🏁 Zielort", "Volos, Griechenland")

now_local, local_tz = get_local_time(startort)
abfahrt_datum = st.date_input("📅 Abfahrtsdatum", value=now_local.date())
abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

geschwindigkeit = st.number_input("🚚 Durchschnittsgeschwindigkeit (km/h)", 60, 120, 80)

if st.button("📦 ETA berechnen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error("❌ Fehler bei der Routenberechnung")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        fahrzeit_min = int(km / geschwindigkeit * 60)
        ende = start_time + timedelta(minutes=fahrzeit_min)

        ziel_tz_str = get_timezone_for_address(zielort)
        ziel_tz = pytz.timezone(ziel_tz_str)
        ende_zielzeit = ende.astimezone(ziel_tz)

        st.markdown(f"""
            ## ✅ Geplante Ankunft:
            **{ende.strftime('%A, %d.%m.%Y – %H:%M')}** ({local_tz.zone})  
            *(Griechenland: {ende_zielzeit.strftime('%H:%M')} Uhr Ortszeit)*
        """)

        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
