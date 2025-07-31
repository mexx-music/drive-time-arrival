
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
    try:
        tz_str = get_timezone_for_address(address)
        tz = pytz.timezone(tz_str)
        return datetime.now(tz), tz
    except:
        return datetime.now(), pytz.timezone("Europe/Vienna")

st.set_page_config(page_title="DriverRoute ETA – mit WE-Pause", layout="centered")

st.title("🚛 DriverRoute ETA – mit realistischer LKW-Zeit & WE-Pause")

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
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, 4)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, 0)
    abfahrt_uhrzeit = datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time()
    abfahrt_pause = datetime.combine(abfahrt_datum, abfahrt_uhrzeit)
    start_time = local_tz.localize(abfahrt_pause)
else:
    st.subheader("🕒 Geplante Abfahrtszeit")
    abfahrtsdatum = st.date_input("Datum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
    abfahrtszeit = datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time()
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

tankpause = st.checkbox("⛽ Zusätzliche Tankpause einplanen (30 min)")

# Wochenendpause hinzufügen
st.subheader("🛌 Wochenruhezeit")
we_aktiv = st.checkbox("🕓 Wochenendpause aktivieren")
if we_aktiv:
    we_typ = st.selectbox("Dauer der Wochenruhezeit", ["24h", "45h", "66h"])
    we_beginn_datum = st.date_input("📅 Startdatum der Wochenruhezeit", value=now_local.date())
    we_beginn_stunde = st.number_input("🕓 Start-Stunde", 0, 23, 22)
    we_beginn_minute = st.number_input("🕧 Start-Minute", 0, 59, 0)
    we_beginn = datetime.combine(we_beginn_datum, datetime.strptime(f"{we_beginn_stunde}:{we_beginn_minute}", "%H:%M").time())
    we_beginn = local_tz.localize(we_beginn)
    we_dauer = {"24h": 1440, "45h": 2700, "66h": 3960}.get(we_typ, 1440)
    we_ende = we_beginn + timedelta(minutes=we_dauer)
else:
    we_beginn = we_ende = None

# Dummy Button für ETA
st.button("📦 Route analysieren & ETA berechnen")
