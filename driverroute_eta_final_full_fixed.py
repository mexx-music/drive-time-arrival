# 🚛 DriverRoute ETA – Mexx Max-Version (ETA korrigiert)

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="DriverRoute ETA – Mexx-Version", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Ancona (Superfast)": 20, "Ancona–Igoumenitsa (Superfast)": 20,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9, "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Patras–Bari (Grimaldi)": 18, "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19, "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 6.5, "Rostock–Trelleborg (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 13, "Kiel–Trelleborg (TT-Line)": 13,
    "Color Line Kiel–Oslo": 20, "Color Line Oslo–Kiel": 20,
    "Hirtshals–Stavanger (FjordLine)": 10, "Stavanger–Hirtshals (FjordLine)": 10,
    "Hirtshals–Bergen (FjordLine)": 16, "Bergen–Hirtshals (FjordLine)": 16
}

def get_timezone_for_address(address):
    if not address:
        return "Europe/Vienna"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        loc = r["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        tz_data = requests.get(tz_url).json()
        return tz_data.get("timeZoneId", "Europe/Vienna")
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

def entfernung_schaetzung(start, ziel, zwischenstopps=[]):
    try:
        base = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(start)}&destination={urllib.parse.quote(ziel)}"
        if zwischenstopps:
            waypoints = "|".join([urllib.parse.quote(p) for p in zwischenstopps])
            base += f"&waypoints={waypoints}"
        base += f"&key={GOOGLE_API_KEY}"
        data = requests.get(base).json()
        if data["status"] == "OK":
            legs = data["routes"][0]["legs"]
            return round(sum(leg["distance"]["value"] for leg in legs) / 1000, 1)
        else:
            return None
    except:
        return None

# UI-Bereich
st.title("🚛 DriverRoute ETA – Mexx-Version")

col1, col2 = st.columns(2)
startort = col1.text_input("📍 Startort oder PLZ", "")
zielort = col2.text_input("🏁 Zielort oder PLZ", "")

now_local, local_tz = get_local_time(startort)

# Zusatzanzeige PLZ-Ort
def get_place_info(address):
    if not address:
        return "❌ Ungültiger Ort"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        result = r["results"][0]
        components = result["address_components"]
        plz = ort = land = ""
        for comp in components:
            if "postal_code" in comp["types"]:
                plz = comp["long_name"]
            if "locality" in comp["types"] or "postal_town" in comp["types"]:
                ort = comp["long_name"]
            if "country" in comp["types"]:
                land = comp["long_name"]
        return f"📌 {ort}, {plz} ({land})"
    return "❌ Ort nicht gefunden"

st.caption(get_place_info(startort))
st.caption(get_place_info(zielort))

# Abfahrtszeit
st.subheader("🕒 Abfahrtszeit planen")
pause_aktiv = st.checkbox("Ich bin gerade in Pause – Abfahrt folgt:")
if pause_aktiv:
    abfahrt_datum = st.date_input("📅 Datum der Abfahrt", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, 4)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, 0)
else:
    abfahrt_datum = st.date_input("Datum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)

abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

# Zwischenstopps
st.markdown("### ➕ Zwischenstopps")
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

# Fährenoption
st.markdown("### 🛳️ Fährlogik")
col_f1, col_f2 = st.columns([2, 1])
manuelle_faehre = col_f1.selectbox("Manuelle Fährwahl (optional)", ["Keine"] + list(FAEHREN.keys()))
auto_faehre = col_f2.checkbox("🚢 Fähre automatisch erkennen", value=True)

# 10h/9h Optionen
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🟩 10h-Fahrten (max. 2)")
    zehner_1 = st.checkbox("✅ 10h-Fahrt Nr. 1", value=True)
    zehner_2 = st.checkbox("✅ 10h-Fahrt Nr. 2", value=True)
with col_b:
    st.subheader("🟦 9h-Ruhepausen (max. 3)")
    neuner_1 = st.checkbox("✅ 9h-Ruhepause Nr. 1", value=True)
    neuner_2 = st.checkbox("✅ 9h-Ruhepause Nr. 2", value=True)
    neuner_3 = st.checkbox("✅ 9h-Ruhepause Nr. 3", value=True)

zehner_fahrten = [zehner_1, zehner_2]
neuner_ruhen = [neuner_1, neuner_2, neuner_3]

# Wochenruhe
st.markdown("### 🛌 Wochenruhepause (optional)")
wochenruhe_manuell = st.checkbox("Wöchentliche Ruhezeit während der Tour einfügen?")
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

geschwindigkeit = st.number_input("🛻 Durchschnittsgeschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

# Berechnung starten
if st.button("📦 Berechnen & ETA anzeigen"):
    km = entfernung_schaetzung(startort, zielort, zwischenstopps)
    if km is None:
        st.error("❌ Strecke konnte nicht berechnet werden.")
    else:
        st.success(f"🛣️ Strecke: {km} km")
        total_min = int(km / geschwindigkeit * 60)

        current_time = start_time
        remaining = total_min
        log = []
        zehner_index = 0
        neuner_index = 0
        used_tank = False

        aktive_faehren = []
        if manuelle_faehre != "Keine":
            aktive_faehren = [{"route": manuelle_faehre, "dauer": FAEHREN[manuelle_faehre]}]
        elif auto_faehre:
            for name, dauer in FAEHREN.items():
                h1, h2 = name.lower().split("–")
                if h1 in startort.lower() or h2 in startort.lower():
                    aktive_faehren.append({"route": name, "dauer": dauer})

        fähre_index = 0
        letzte_fahrt_ende = None

        while remaining > 0:
            if we_start and we_start <= current_time < we_ende:
                current_time = we_ende
                zehner_index = 0
                neuner_index = 0
                log.append(f"🛌 Wochenruhe von {we_start.strftime('%Y-%m-%d %H:%M')} bis {we_ende.strftime('%Y-%m-%d %H:%M')}")
                continue

            if current_time.weekday() == 0 and current_time.hour >= 2:
                zehner_index = 0
                neuner_index = 0
                log.append("🔄 Wochenreset: Montag ab 02:00")

            if fähre_index < len(aktive_faehren):
                faehre = aktive_faehren[fähre_index]
                dauer = faehre["dauer"]
                ende = current_time + timedelta(hours=dauer)
                log.append(f"🚢 Fähre {faehre['route']} – {dauer} h → Ankunft {ende.strftime('%Y-%m-%d %H:%M')}")
                current_time = ende
                fähre_index += 1
                continue

            max_drive = 600 if zehner_index < 2 and zehner_fahrten[zehner_index] else 540
            gefahren = min(remaining, max_drive)
            pausen = math.floor(gefahren / 270) * 45
            if tankpause and not used_tank:
                pausen += 30
                used_tank = True

            ende = current_time + timedelta(minutes=gefahren + pausen)
            log.append(f"📆 {current_time.strftime('%a %H:%M')} → {gefahren//60}h{gefahren%60:02d} + {pausen} min Pause → {ende.strftime('%H:%M')}")
            remaining -= gefahren
            letzte_fahrt_ende = ende

            if remaining <= 0:
                break

            ruhezeit = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
            current_time = ende + timedelta(minutes=ruhezeit)
            log.append(f"🌙 Ruhezeit {ruhezeit//60}h → Neustart: {current_time.strftime('%Y-%m-%d %H:%M')}")
            if zehner_index < 2: zehner_index += 1
            if neuner_index < 3: neuner_index += 1

        # Fahrplananzeige
        st.markdown("## 📋 Fahrplan")
        for eintrag in log:
            st.markdown(eintrag)

        verbl_10h = max(0, zehner_fahrten.count(True) - zehner_index)
        verbl_9h = max(0, neuner_ruhen.count(True) - neuner_index)
        st.info(f"🧮 Verbleibend: {verbl_10h}× 10h, {verbl_9h}× 9h")

        ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
        letzte_weiterfahrt = None
        letzte_ankunft = letzte_fahrt_ende.astimezone(ziel_tz) if letzte_fahrt_ende else current_time.astimezone(ziel_tz)

        for eintrag in reversed(log):
            if eintrag.startswith("🌙 Ruhezeit") and "Neustart" in eintrag:
                try:
                    ts = eintrag.split("Neustart: ")[1]
                    letzte_weiterfahrt = local_tz.localize(datetime.strptime(ts, "%Y-%m-%d %H:%M")).astimezone(ziel_tz)
                    break
                except:
                    pass

        if not letzte_weiterfahrt:
            letzte_weiterfahrt = letzte_ankunft - timedelta(hours=2)

        st.markdown("## 🕓 Zeitplanübersicht")
        st.markdown(
            f"🟡 <b>Weiterfahrt nach letzter Pause:</b> {letzte_weiterfahrt.strftime('%A, %d.%m.%Y – %H:%M')}<br>"
            f"✅ <b>Endgültige Ankunft:</b> {letzte_ankunft.strftime('%A, %d.%m.%Y – %H:%M')}<br>"
            f"({ziel_tz.zone})",
            unsafe_allow_html=True)

        st.markdown(
            f"<h2 style='text-align: center; color: green;'>✅ <u>Ankunftszeit:</u><br>"
            f"🕓 <b>{letzte_ankunft.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>"
            f"({ziel_tz.zone})</h2>",
            unsafe_allow_html=True)

        # Google Map
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        if zwischenstopps:
            waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
            map_url += f"&waypoints={waypoints_encoded}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
