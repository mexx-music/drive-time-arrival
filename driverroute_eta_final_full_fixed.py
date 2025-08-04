# 🚛 DriverRoute ETA – Teil 1: Setup, Fahrplan, Basisfunktionen

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Finalversion", layout="centered")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# 🌍 Fahrplandaten mit echten Abfahrten (gekürzt zur Demonstration)
FAHRPLAN = {
    "Patras–Ancona (Superfast)": {
        "gesellschaft": "Superfast",
        "dauer_stunden": 22,
        "abfahrten": ["08:00", "17:30", "22:00"]
    },
    "Rostock–Trelleborg (TT-Line)": {
        "gesellschaft": "TT-Line",
        "dauer_stunden": 6.5,
        "abfahrten": ["09:00", "15:00", "23:00"]
    },
    "Trelleborg–Rostock (TT-Line)": {
        "gesellschaft": "TT-Line",
        "dauer_stunden": 6.5,
        "abfahrten": ["07:00", "13:30", "21:30"]
    }
}

# Zusatzfunktionen: Zeitzone, Ortsinfo, Distanzberechnung, automatische Zwischenstopps
def auto_add_ferry_stop(start, ziel, zwischenstopps, aktive_faehren):
    extra_stops = []
    for f in aktive_faehren:
        if "Ancona" in f["route"] and "Ancona" not in zwischenstopps and "Ancona" not in [start, ziel]:
            extra_stops.append("Ancona")
        if "Trelleborg" in f["route"] and "Trelleborg" not in zwischenstopps and "Trelleborg" not in [start, ziel]:
            extra_stops.append("Trelleborg")
    return zwischenstopps + extra_stops

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

def segmentiere_route(start, ziel, zwischenstopps, faehre_name):
    h1, h2 = faehre_name.split("–")
    h1 = h1.strip().lower()
    h2 = h2.strip().lower()

    pre_stops = []
    post_stops = []
    faehre_gefunden = False

    for stop in zwischenstopps:
        stop_lc = stop.lower()
        if h1 in stop_lc or h2 in stop_lc:
            faehre_gefunden = True
            continue
        if not faehre_gefunden:
            pre_stops.append(stop)
        else:
            post_stops.append(stop)

    abschnitt_1 = {"start": start, "ziel": h1.title(), "zwischen": pre_stops}
    faehre = {"route": faehre_name, "von": h1.title(), "nach": h2.title()}
    abschnitt_2 = {"start": h2.title(), "ziel": ziel, "zwischen": post_stops}

    return abschnitt_1, faehre, abschnitt_2
# 🚛 DriverRoute ETA – Teil 2: UI, Eingabe, Fährauswahl, Zeitplanung
import streamlit as st
from datetime import datetime
import pytz

# ⏱ Lokale Zeit vorbereiten
startort = st.text_input("📍 Startort oder PLZ", "")
zielort = st.text_input("🏁 Zielort oder PLZ", "")
now_local = datetime.now(pytz.timezone("Europe/Vienna"))

# Eingabe Zwischenstopps
st.markdown("### ➕ Zwischenstopps")
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

# Fährenauswahl
st.markdown("### 🛳️ Fährlogik")
manuelle_faehre = st.selectbox("Manuelle Fährwahl (optional)", ["Keine"])  # FAHRPLAN wird in Teil 1 definiert
auto_faehren_erlaubt = st.checkbox("🚢 Automatische Fährenerkennung aktivieren", value=True)

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

# Fahreregeln
geschwindigkeit = st.number_input("🛻 Durchschnittsgeschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

# Wochenruhe
st.markdown("### 🛌 Wochenruhepause (optional)")
wochenruhe_manuell = st.checkbox("Wöchentliche Ruhezeit während der Tour einfügen?")
if wochenruhe_manuell:
    we_tag = st.date_input("Start der Wochenruhe", value=now_local.date(), key="we_date")
    we_stunde = st.number_input("Stunde", 0, 23, 12, key="we_hour")
    we_minute = st.number_input("Minute", 0, 59, 0, key="we_min")
    we_dauer = st.number_input("Dauer der Pause (h)", 24, 72, 45, key="we_dauer")

# Fahrzeitregeln
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
# 🚛 DriverRoute ETA – Teil 3: Berechnung, ETA-Ausgabe, Fahrplan, Karte
import streamlit as st
from datetime import datetime, timedelta
import pytz
import math
import urllib.parse

# Dummy-Werte (normalerweise aus Teil 1 & 2 geladen)
startort = "Lambach"
zielort = "Oslo"
zwischenstopps = ["Rostock", "Trelleborg"]
geschwindigkeit = 80
tankpause = True
abfahrt_time = datetime.now()
zehner_fahrten = [True, True]
neuner_ruhen = [True, True, True]

# Beispiel: ETA-Berechnung (vereinfacht)
if st.button("📦 Berechnen & ETA anzeigen"):
    log = []
    km = 1200  # Beispielentfernung
    aktuelle_zeit = abfahrt_time
    remaining = int(km / geschwindigkeit * 60)
    zehner_index = 0
    neuner_index = 0

    while remaining > 0:
        max_drive = 600 if zehner_index < 2 and zehner_fahrten[zehner_index] else 540
        gefahren = min(remaining, max_drive)
        pausen = math.floor(gefahren / 270) * 45
        if tankpause:
            pausen += 30
            tankpause = False
        ende = aktuelle_zeit + timedelta(minutes=gefahren + pausen)
        log.append(f"📆 {aktuelle_zeit.strftime('%a %H:%M')} → +{gefahren} min + Pause {pausen} → {ende.strftime('%H:%M')}")
        aktuelle_zeit = ende
        remaining -= gefahren
        if remaining > 0:
            ruhe = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
            aktuelle_zeit += timedelta(minutes=ruhe)
            log.append(f"🌙 Ruhezeit {ruhe//60}h → Neustart: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
            zehner_index += 1
            neuner_index += 1

    # ETA-Anzeige
    ziel_tz = pytz.timezone("Europe/Oslo")
    aktuelle_zeit = aktuelle_zeit.astimezone(ziel_tz)
    st.markdown(
        f"<h2 style='text-align: center; color: green;'>✅ <u>Ankunftszeit:</u><br>"
        f"🕓 <b>{aktuelle_zeit.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>"
        f"({ziel_tz.zone})</h2>",
        unsafe_allow_html=True
    )

    # Log anzeigen
    st.markdown("## 📋 Fahrplan")
    for eintrag in log:
        st.markdown(eintrag)

    # Karte anzeigen
    map_url = f"https://www.google.com/maps/embed/v1/directions?key=DEIN_API_KEY&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
    if zwischenstopps:
        waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
        map_url += f"&waypoints={waypoints_encoded}"
    st.markdown("### 🗺️ Routenkarte:")
    st.components.v1.iframe(map_url, height=500)
