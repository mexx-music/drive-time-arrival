import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

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

st.set_page_config(page_title="DriverRoute ETA – Vollversion", layout="centered")
st.title("🚛 DriverRoute ETA – Fahrzeit, Kästchen & Karte")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

now_local, local_tz = get_local_time(startort)

pause_aktiv = st.checkbox("Ich bin in Pause – Abfahrt um ...")
if pause_aktiv:
    abfahrt_datum = st.date_input("📅 Datum der Abfahrt", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, 4)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, 0)
    abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
    start_time = local_tz.localize(abfahrt_time)
else:
    st.subheader("🕒 Geplante Abfahrt")
    abfahrt_datum = st.date_input("Datum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
    abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
    start_time = local_tz.localize(abfahrt_time)

# Kästchen statt Auswahllisten
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

zehner_fahrten = [zehner_1, zehner_2]
neuner_ruhen = [neuner_1, neuner_2, neuner_3]

wochenruhe_manuell = st.checkbox("🛌 Wochenruhepause während Tour manuell einfügen?")
if wochenruhe_manuell:
    we_tag = st.date_input("Start der Wochenruhe", value=now_local.date(), key="we_date")
    we_stunde = st.number_input("Stunde", 0, 23, 12, key="we_hour")
    we_minute = st.number_input("Minute", 0, 59, 0, key="we_min")
    we_dauer = st.number_input("Dauer der Pause (h)", 24, 72, 45, key="we_dauer")
    we_start = local_tz.localize(datetime.combine(we_tag, datetime.strptime(f"{we_stunde}:{we_minute}", "%H:%M").time()))
    we_ende = we_start + timedelta(hours=we_dauer)
else:
    we_start = None
    we_ende = None

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

if st.button("📦 Berechnen & ETA anzeigen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    if zwischenstopps:
        url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error("Routenfehler")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        total_min = int(km / geschwindigkeit * 60)
        st.success(f"🛣️ Strecke: {km} km – {total_min} min bei {geschwindigkeit} km/h")

        current_time = start_time
        remaining = total_min
        log = []
        zehner_index = 0
        neuner_index = 0
        used_tank = False

        while remaining > 0:
            if we_start and current_time >= we_start and current_time < we_ende:
                current_time = we_ende
                zehner_index = 0
                neuner_index = 0
                log.append(f"🛌 Wochenruhe von {we_start.strftime('%Y-%m-%d %H:%M')} bis {we_ende.strftime('%Y-%m-%d %H:%M')} – Rücksetzung aktiv")
                continue

            if current_time.weekday() == 0 and current_time.hour >= 2:
                zehner_index = 0
                neuner_index = 0
                log.append(f"🔄 Wochenreset: Montag ab 2:00 → 10h/9h zurückgesetzt")

            max_drive = 600 if zehner_index < 2 and zehner_fahrten[zehner_index] else 540
            gefahren = min(remaining, max_drive)
            pausen = math.floor(gefahren / 270) * 45
            if tankpause and not used_tank:
                pausen += 30
                used_tank = True
            ende = current_time + timedelta(minutes=gefahren + pausen)
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → {int(gefahren)} min + {pausen} min Pause → Ende: {ende.strftime('%H:%M')}")
            remaining -= gefahren

            if remaining <= 0:
                break

            ruhezeit = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
            log.append(f"🌙 Ruhe {ruhezeit//60}h → weiter: {(ende + timedelta(minutes=ruhezeit)).strftime('%Y-%m-%d %H:%M')}")
            current_time = ende + timedelta(minutes=ruhezeit)
            if zehner_index < 2: zehner_index += 1
            if neuner_index < 3: neuner_index += 1

        st.markdown("## 📋 Fahrplan:")
        for eintrag in log:
            st.markdown(eintrag)
        st.markdown("## 📋 Fahrplan:")
for eintrag in log:
    st.markdown(eintrag)

verbl_10h = max(0, zehner_fahrten.count(True) - zehner_index)
verbl_9h = max(0, neuner_ruhen.count(True) - neuner_index)
st.info(f"🧮 Noch übrig: {verbl_10h}× 10h-Fahrt, {verbl_9h}× 9h-Ruhepause")

# 🟢 Groß, grün, korrektes ETA-Ende anzeigen
st.markdown(f"""
<h2 style='text-align: center; color: green;'>
✅ <u>Geplante Ankunft:</u><br>
🕓 <b>{ende.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>
({local_tz.zone})
</h2>
""", unsafe_allow_html=True)
