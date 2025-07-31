import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math
import pytz
import time

st.set_page_config(page_title="DriverRoute ETA – AM/PM Uhrzeit", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# ------------------- Hilfsfunktionen ----------------------
def get_timezone_for_latlng(lat, lng):
    timestamp = int(time.time())
    tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={GOOGLE_API_KEY}"
    tz_data = requests.get(tz_url).json()
    if tz_data["status"] == "OK":
        return tz_data["timeZoneId"]
    else:
        return "Europe/Vienna"

def get_timezone_for_address(address):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo_data = requests.get(geocode_url).json()
    if geo_data["status"] == "OK":
        lat = geo_data["results"][0]["geometry"]["location"]["lat"]
        lng = geo_data["results"][0]["geometry"]["location"]["lng"]
        return get_timezone_for_latlng(lat, lng)
    return "Europe/Vienna"

def get_local_time_for_address(address):
    try:
        tz_str = get_timezone_for_address(address)
        tz = pytz.timezone(tz_str)
        return datetime.now(tz), tz
    except:
        return datetime.now(), pytz.timezone("Europe/Vienna")

# ------------------- Uhrzeit Auswahl mit Kästchen ----------------------
def custom_time_picker(label):
    st.markdown(f"**{label}**")

    col1, col2 = st.columns([2, 2])
    with col1:
        st.markdown("Stunde:")
        stunden = [str(i) for i in range(1, 13)]
        stunde = st.radio(" ", stunden, horizontal=True, key="stunden_kästchen", label_visibility="collapsed")
    with col2:
        st.markdown("Minute:")
        minuten = [f"{i:02d}" for i in range(0, 60, 5)]
        minute = st.radio("  ", minuten, horizontal=True, key="minuten_kästchen", label_visibility="collapsed")

    am_pm = st.radio("🕰️ AM oder PM", ["AM", "PM"], horizontal=True)

    stunde_int = int(stunde)
    if am_pm == "PM" and stunde_int < 12:
        stunde_int += 12
    elif am_pm == "AM" and stunde_int == 12:
        stunde_int = 0

    return stunde_int, int(minute)

# ------------------- Benutzeroberfläche ----------------------

st.title("🚛 DriverRoute ETA – AM/PM Uhrzeitwahl")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

now_local, local_tz = get_local_time_for_address(startort)
abfahrt_datum = st.date_input("📅 Datum der Abfahrt", value=now_local.date())

stunde, minute = custom_time_picker("🕓 Abfahrtszeit auswählen:")
abfahrtszeit = datetime.combine(abfahrt_datum, datetime.strptime(f"{stunde}:{minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrtszeit)

# ------------------- Strecke + ETA Berechnung ----------------------

if st.button("📦 Strecke analysieren"):
    start_coords = urllib.parse.quote(startort)
    ziel_coords = urllib.parse.quote(zielort)
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_coords}&destination={ziel_coords}&key={GOOGLE_API_KEY}"

    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error(f"Fehler: {data['status']}")
    else:
        legs = data["routes"][0]["legs"]
        km = round(sum([leg["distance"]["value"] for leg in legs]) / 1000, 1)
        total_sec = sum([leg["duration"]["value"] for leg in legs])
        total_min = total_sec // 60

        st.success(f"🛣️ Strecke: {km} km ⏱️ Google-Fahrzeit: {total_min} min")

        eta = start_time + timedelta(minutes=total_min)
        eta_ziel = eta.astimezone(local_tz)

        st.markdown(f"## 📍 Geplante Ankunft:\n🗓️ {eta_ziel.strftime('%A, %d.%m.%Y')} – 🕒 {eta_ziel.strftime('%H:%M Uhr')} ({local_tz.zone})")

        st.subheader("🗺️ Routenkarte")
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={start_coords}&destination={ziel_coords}"
        st.components.v1.iframe(map_url, height=450)
