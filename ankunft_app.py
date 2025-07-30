import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math
import pytz
import time

GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

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
    tz_str = get_timezone_for_address(address)
    tz = pytz.timezone(tz_str)
    return datetime.now(tz), tz

st.set_page_config(page_title="DriverRoute Multiday ETA", layout="centered")

st.title("🚛 DriverRoute Multiday ETA – Version 2.1")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    val = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
    st.session_state.zwischenstopps[i] = val

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip() != ""]

now_local, local_tz = get_local_time_for_address(startort)

st.subheader("🕒 Geplante Abfahrtszeit")
abfahrtsdatum = st.date_input("Datum", value=now_local.date())
abfahrtszeit = st.time_input("Uhrzeit", value=now_local.time())
geplante_abfahrt = local_tz.localize(datetime.combine(abfahrtsdatum, abfahrtszeit))

st.subheader("🚦 Fahrtbeginn heute?")
heute_fahren = st.checkbox("Ich fahre heute noch", value=True)

verbleibend_heute = 0
if heute_fahren:
    st.subheader("🔄 Verbleibende Lenkzeit HEUTE")
    col1, col2 = st.columns(2)
    with col1:
        lenk_h = st.number_input("Stunden übrig", 0, 10, value=9)
    with col2:
        lenk_m = st.number_input("Minuten übrig", 0, 59, value=0)
    verbleibend_heute = lenk_h * 60 + lenk_m

st.subheader("🟦 10-Stunden-Fahrten (max. 2/Woche)")
zehner_fahrten = []
for i in range(2):
    zehner_fahrten.append(st.checkbox(f"10h-Fahrt nutzen (Tag {i+1})", value=True, key=f"10h_{i}"))

st.subheader("🌙 9-Stunden-Ruhepausen (max. 3/Woche)")
neuner_ruhen = []
for i in range(3):
    neuner_ruhen.append(st.checkbox(f"9h-Ruhe erlaubt (Nacht {i+1})", value=True, key=f"9h_{i}"))

tankpause = st.checkbox("⛽ Zusätzliche Tankpause einplanen (30 min)")

if st.button("📦 Route analysieren & ETA berechnen"):
    start_coords = urllib.parse.quote(startort)
    ziel_coords = urllib.parse.quote(zielort)
    waypoints = "|".join([urllib.parse.quote(s) for s in zwischenstopps]) if zwischenstopps else ""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_coords}&destination={ziel_coords}&key={GOOGLE_API_KEY}"
    if waypoints:
        url += f"&waypoints={waypoints}"

    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error(f"Fehler: {data['status']}")
    else:
        legs = data["routes"][0]["legs"]
        total_sec = sum([leg["duration"]["value"] for leg in legs])
        total_min = total_sec // 60
        km = round(sum([leg["distance"]["value"] for leg in legs]) / 1000, 1)

        st.success(f"🛣️ Strecke: {km} km ⏱️ Google-Fahrzeit: {total_min} min")

        remaining_minutes = total_min
        current_time = geplante_abfahrt
        log = []
        used_10h = 0
        used_9h_rest = 0
        used_tankpause = False
        zehner_index = 0
        neuner_index = 0
        first_day = True

        while remaining_minutes > 0:
            tag = current_time.strftime("%A")
            start_str = current_time.strftime("%Y-%m-%d %H:%M")

            if first_day:
                if heute_fahren and verbleibend_heute > 0:
                    max_drive = verbleibend_heute
                else:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=8, minute=0)
                    max_drive = 540
                first_day = False
            elif zehner_index < len(zehner_fahrten) and zehner_fahrten[zehner_index]:
                max_drive = 600
                used_10h += 1
                zehner_index += 1
            else:
                max_drive = 540

            gefahren = min(remaining_minutes, max_drive)
            pflichtpausen = math.floor(gefahren / 270)
            pause_min = pflichtpausen * 45

            if tankpause and not used_tankpause:
                pause_min += 30
                used_tankpause = True

            tages_ende = current_time + timedelta(minutes=gefahren + pause_min)
            log.append(f"📆 {tag} – Start: {start_str} → Fahrt: {gefahren} min + Pause: {pause_min} min → Ende: {tages_ende.strftime('%H:%M')}")

            remaining_minutes -= gefahren

            if remaining_minutes > 0:
                if neuner_index < len(neuner_ruhen) and neuner_ruhen[neuner_index]:
                    rest = 540
                    neuner_index += 1
                    ruhetyp = "9h-Ruhe"
                else:
                    rest = 660
                    ruhetyp = "11h-Ruhe"
                log.append(f"🌙 Ruhezeit: {ruhetyp} ({rest//60}h) → weiter ab {(tages_ende + timedelta(minutes=rest)).strftime('%Y-%m-%d %H:%M')}")
                current_time = tages_ende + timedelta(minutes=rest)
            else:
                current_time = tages_ende

        eta_ziel = current_time.astimezone(local_tz)
        st.markdown("## 📋 Fahrplan:")
        for eintrag in log:
            st.markdown(eintrag)

        st.success(f"✅ ETA am Ziel: {eta_ziel.strftime('%A, %H:%M Uhr')} ({local_tz.zone})")

        st.subheader("🗺️ Routenkarte")
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={start_coords}&destination={ziel_coords}"
        if zwischenstopps:
            map_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
        st.components.v1.iframe(map_url, height=450)
