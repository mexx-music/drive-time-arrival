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
st.title("🚛 DriverRoute ETA – mit realistischer LKW-Zeit & Wochenruhezeit")

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

# Neue Funktion: Wochenruhezeit
st.subheader("🛌 Wochenruhezeit einfügen (optional)")
we_aktiv = st.checkbox("➕ Wochenruhezeit einplanen")
if we_aktiv:
    we_startdatum = st.date_input("Startdatum der Pause", value=now_local.date(), key="we_date")
    we_stunde = st.number_input("Beginn Stunde", 0, 23, 18)
    we_minute = st.number_input("Beginn Minute", 0, 59, 0)
    we_beginn = datetime.combine(we_startdatum, datetime.strptime(f"{we_stunde}:{we_minute}", "%H:%M").time())
    we_typ = st.selectbox("Dauer", ["24h", "45h", "66h", "Benutzerdefiniert"])
    if we_typ == "Benutzerdefiniert":
        we_dauer_std = st.number_input("Dauer in Stunden", 12, 96, 33)
    else:
        we_dauer_std = int(we_typ.replace("h", ""))
else:
    we_beginn = None
    we_dauer_std = 0

# Hinweis: der restliche Code zur Berechnung wird separat ergänzt
st.info("✅ WE-Pause-Eingabe vorbereitet. ETA-Berechnung folgt im nächsten Schritt.")
