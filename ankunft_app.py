
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
st.markdown("### 🧭 Wochenlenkzeit festlegen")

vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell eingeben"], index=0)

if vorgabe == "Voll (56h)":
    verfügbare_woche = 3360
else:
    verfügbare_woche_stunden = st.number_input("⏱️ Eigene Eingabe (in Stunden)", min_value=0.0, max_value=56.0, value=36.0, step=0.25)
    verfügbare_woche = int(verfügbare_woche_stunden * 60)

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

zwischenstopps = st.text_area("🧭 Zwischenstopps (ein Ort pro Zeile)", "").split("\n")
zwischenstopps = [s for s in zwischenstopps if s.strip()]

now_local, local_tz = get_local_time(startort)

pause_aktiv = st.checkbox("Ich bin in Pause – Abfahrt um ...")
if pause_aktiv:
    abfahrt_datum = st.date_input("📅 Datum der Abfahrt", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, 4)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, 0)
else:
    st.subheader("🕒 Geplante Abfahrt")
    abfahrt_datum = st.date_input("Datum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)

abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

st.markdown("### 🕓 Wöchentliche Lenkzeit-Ausnahmen")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("10h-Fahrten (max. 2)")
    zehner_1 = st.checkbox("✅ 10h-Fahrt Nr. 1", value=True, key="10h_1")
    zehner_2 = st.checkbox("✅ 10h-Fahrt Nr. 2", value=True, key="10h_2")
with col_b:
    st.subheader("9h-Ruhepausen (max. 3)")
    neuner_1 = st.checkbox("✅ 9h-Ruhepause Nr. 1", value=True, key="9h_1")
    neuner_2 = st.checkbox("✅ 9h-Ruhepause Nr. 2", value=True, key="9h_2")
    neuner_3 = st.checkbox("✅ 9h-Ruhepause Nr. 3", value=True, key="9h_3")

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

if st.button("📦 Berechnen & ETA anzeigen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    if zwischenstopps:
        url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error("❌ Fehler bei der Routenberechnung!")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        total_min = int(km / geschwindigkeit * 60)
        st.success(f"🛣️ Strecke: {km} km – {total_min} min bei {geschwindigkeit} km/h")

        verbleibend_min = verfügbare_woche - total_min
        h, m = divmod(abs(verbleibend_min), 60)

        if verbleibend_min < 0:
            st.error(f"❌ Achtung: Tour überschreitet verfügbare Wochenlenkzeit um –{h} h {m} min!")
        elif verbleibend_min <= 240:
            st.warning(f"⚠️ Achtung: Nur noch {h} h {m} min Wochenlenkzeit übrig!")
        else:
            st.info(f"🧭 Verbleibende Wochenlenkzeit: {h} h {m} min")
