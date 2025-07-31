import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import time
import math

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
    try:
        tz_str = get_timezone_for_address(address)
        tz = pytz.timezone(tz_str)
        return datetime.now(tz), tz
    except:
        return datetime.now(), pytz.timezone("Europe/Vienna")

st.set_page_config(page_title="DriverRoute ETA", layout="centered")
st.title("🚛 DriverRoute ETA")

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

pause_aktiv = st.checkbox("Ich bin in Pause – Abfahrt um ...")
if pause_aktiv:
    abfahrt_datum = st.date_input("📅 Datum der Abfahrt nach Pause", value=now_local.date())
    ampm = st.radio("Zeitauswahl", ["AM", "PM"], horizontal=True)
    stunden_liste = list(range(1, 13)) if ampm == "AM" else list(range(13, 24))
    stunde = st.selectbox("🕓 Stunde", stunden_liste)
    minute = st.selectbox("🕧 Minute", [f"{i:02d}" for i in range(0, 60, 5)])
    abfahrt_time = datetime.strptime(f"{stunde}:{minute}", "%H:%M").time()
    abfahrt_pause = datetime.combine(abfahrt_datum, abfahrt_time)
    start_time = local_tz.localize(abfahrt_pause)
else:
    abfahrtsdatum = st.date_input("📅 Geplante Abfahrt", value=now_local.date())
    ampm = st.radio("Zeitauswahl", ["AM", "PM"], horizontal=True, key="normal_ampm")
    stunden_liste = list(range(1, 13)) if ampm == "AM" else list(range(13, 24))
    stunde = st.selectbox("🕓 Stunde", stunden_liste, key="normal_stunde")
    minute = st.selectbox("🕧 Minute", [f"{i:02d}" for i in range(0, 60, 5)], key="normal_minute")
    abfahrtszeit = datetime.strptime(f"{stunde}:{minute}", "%H:%M").time()
    start_time = local_tz.localize(datetime.combine(abfahrtsdatum, abfahrtszeit))

verbleibend_heute = 0
if not pause_aktiv:
    st.subheader("🔄 Verbleibende Lenkzeit HEUTE")
    col1, col2 = st.columns(2)
    with col1:
        lenk_h = st.number_input("Stunden übrig", 0, 10, value=9)
    with col2:
        lenk_m = st.number_input("Minuten übrig", 0, 59, value=0)
    verbleibend_heute = lenk_h * 60 + lenk_m

st.subheader("🛻 Durchschnittliche LKW-Geschwindigkeit")
geschwindigkeit = st.number_input("Geschwindigkeit (km/h)", min_value=60, max_value=120, value=80)

st.subheader("🟦 10-Stunden-Fahrten (max. 2/Woche)")
zehner_fahrten = []
for i in range(2):
    zehner_fahrten.append(st.checkbox(f"10h-Fahrt nutzen (Tag {i+1})", value=True, key=f"10h_{i}"))

st.subheader("🌙 9-Stunden-Ruhepausen (max. 3/Woche)")
neuner_ruhen = []
for i in range(3):
    neuner_ruhen.append(st.checkbox(f"9h-Ruhe erlaubt (Nacht {i+1})", value=True, key=f"9h_{i}"))

st.subheader("🛌 Wochenruhezeit")
wochenruhe_aktiv = st.checkbox("🕒 Wochenruhezeit einplanen")
if wochenruhe_aktiv:
    pause_typ = st.radio("Wähle Dauer:", ["24h", "45h", "66h", "eigene Dauer"])
    if pause_typ == "eigene Dauer":
        eigene_stunden = st.number_input("Eigene Pausenlänge (in Stunden)", min_value=1, max_value=120, value=45)
        wochenruhe_min = eigene_stunden * 60
    else:
        wochenruhe_min = int(pause_typ.replace("h", "")) * 60
else:
    wochenruhe_min = 0

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
        km = round(sum([leg["distance"]["value"] for leg in legs]) / 1000, 1)
        total_min = km / geschwindigkeit * 60

        st.success(f"🛣️ Strecke: {km} km ⏱️ Fahrzeit: {round(total_min)} min bei {geschwindigkeit} km/h")

        remaining_minutes = total_min
        current_time = start_time
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
                if pause_aktiv:
                    max_drive = 600 if zehner_fahrten[0] else 540
                    if zehner_fahrten[0]:
                        used_10h += 1
                        zehner_index += 1
                else:
                    max_drive = verbleibend_heute
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
            log.append(f"📆 {tag} – Start: {start_str} → Fahrt: {int(gefahren)} min + Pause: {pause_min} min → Ende: {tages_ende.strftime('%H:%M')}")

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

        if wochenruhe_aktiv:
            log.append(f"🛌 Wochenruhezeit {wochenruhe_min//60}h → weiter ab {(current_time + timedelta(minutes=wochenruhe_min)).strftime('%Y-%m-%d %H:%M')}")
            current_time += timedelta(minutes=wochenruhe_min)

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
