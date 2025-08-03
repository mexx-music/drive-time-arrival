# 🚛 DriverRoute ETA – Kombiversion (Wiederhergestellt)
# Inklusive: Zwischenstopps, PLZ, Wochenlenkzeit, automatische & manuelle Fähren, ETA, Karte, Kalender-Farbmarkierung

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import time
import math

st.set_page_config(page_title="DriverRoute ETA – mit Fähren & Kalender", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Igoumenitsa–Ancona (Superfast)": 20,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Igoumenitsa–Brindisi (Grimaldi)": 9,
    "Patras–Bari (Grimaldi)": 18, "Patras–Brindisi (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Trelleborg–Rostock (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 13, "Color Line Kiel–Oslo": 20,
    "Hirtshals–Bergen (FjordLine)": 16
}

def get_timezone_for_address(address):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
        r = requests.get(url).json()
        if r["status"] == "OK":
            loc = r["results"][0]["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]
            tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
            tz_data = requests.get(tz_url).json()
            return tz_data.get("timeZoneId", "Europe/Vienna")
    except:
        return "Europe/Vienna"
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

def format_minutes_to_hm(mins):
    h, m = divmod(int(mins), 60)
    return f"{h}h{m:02d}" if h else f"{m} min"

st.title("🚛 DriverRoute ETA – mit Fähren, Kalender & Karte")

startort = st.text_input("📍 Startort", "")
zielort = st.text_input("🏁 Zielort", "")
zwischenstopps = []

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

now_local, local_tz = get_local_time(startort or "Vienna")

abfahrt_datum = st.date_input("📅 Startdatum", now_local.date())
abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

if "faehren" not in st.session_state:
    st.session_state.faehren = []

st.markdown("### 🛳 Fährenübersicht (farblich markiert im Fahrplan):")
if st.button("➕ Fähre hinzufügen"):
    st.session_state.faehren.append({
        "route": list(FAEHREN.keys())[0],
        "datum": now_local.date(),
        "stunde": 12,
        "minute": 0
    })
for i, f in enumerate(st.session_state.faehren):
    with st.expander(f"Fähre {i+1}"):
        f["route"] = st.selectbox("Route", list(FAEHREN.keys()), index=list(FAEHREN.keys()).index(f["route"]), key=f"route_{i}")
        f["datum"] = st.date_input("📅 Datum", value=f["datum"], key=f"date_{i}")
        f["stunde"] = st.number_input("🕓 Stunde", 0, 23, f["stunde"], key=f"hour_{i}")
        f["minute"] = st.number_input("🕧 Minute", 0, 59, f["minute"], key=f"minute_{i}")

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

if st.button("📦 ETA & Fahrplan berechnen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    if zwischenstopps:
        url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
    r = requests.get(url)
    data = r.json()
    if data["status"] != "OK":
        st.error("❌ Route konnte nicht berechnet werden.")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        total_min = int(km / geschwindigkeit * 60)
        st.success(f"🛣️ Strecke: {km} km – {total_min}min bei {geschwindigkeit} km/h")

        current_time = start_time
        remaining = total_min
        log = []
        f_i = 0
        used_tank = False

        while remaining > 0:
            if f_i < len(st.session_state.faehren):
                f = st.session_state.faehren[f_i]
                f_start = local_tz.localize(datetime.combine(f["datum"], datetime.strptime(f"{f["stunde"]}:{f["minute"]}", "%H:%M").time()))
                f_dauer = FAEHREN[f["route"]]
                if current_time <= f_start:
                    warte = int((f_start - current_time).total_seconds() / 60)
                    log.append(f"<div style='background-color:#ffffe0;padding:10px;border-left:5px solid orange;'>⏳ <b>Wartezeit auf Fähre:</b> {warte} min</div>")
                    current_time = f_start
                f_ende = current_time + timedelta(hours=f_dauer)
                log.append(f"<div style='background-color:#e6f2ff;padding:10px;border-left:5px solid #3399ff;'>🛳️ <b>Fähre {f['route']}</b> – Dauer: {f_dauer}h → Ankunft: <b>{f_ende.strftime('%d.%m.%Y %H:%M')}</b></div>")
                current_time = f_ende
                f_i += 1
                continue

            block = min(remaining, 270)
            pause = 45
            if tankpause and not used_tank:
                pause += 30
                used_tank = True
            ende = current_time + timedelta(minutes=block + pause)
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → Fahrt: {block} min + Pause: {pause} min → {ende.strftime('%H:%M')}")
            current_time = ende
            remaining -= block

        st.markdown("## 📋 Fahrplan:")
        for eintrag in log:
            st.markdown(eintrag, unsafe_allow_html=True)

        ziel_tz = pytz.timezone(get_timezone_for_address(zielort or "Vienna"))
        letzte_zeit = current_time.astimezone(ziel_tz)
        st.markdown(f"<h2 style='text-align:center;color:green;'>🕓 ETA: <b>{letzte_zeit.strftime('%A, %d.%m.%Y – %H:%M')}</b> ({ziel_tz.zone})</h2>", unsafe_allow_html=True)

        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        if zwischenstopps:
            map_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
        st.markdown("### 🗺️ Karte:")
        st.components.v1.iframe(map_url, height=500)
