# DriverRoute ETA MAX-Version 04.08 – mit segmentierter Fährlogik

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – MAX 04.08", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

FAEHREN = {
    "Hirtshals–Bergen (FjordLine)": 16,
    "Bergen–Hirtshals (FjordLine)": 16,
    "Patras–Ancona (Superfast)": 22,
    "Igoumenitsa–Ancona (Superfast)": 20,
    "Ancona–Igoumenitsa (Superfast)": 20,
    "Trelleborg–Travemünde (TT-Line)": 9,
    "Travemünde–Trelleborg (TT-Line)": 9,
    "Color Line Kiel–Oslo": 20,
    "Color Line Oslo–Kiel": 20
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

def format_minutes_to_hm(minutes):
    h, m = divmod(int(minutes), 60)
    if h > 0 and m > 0:
        return f"{h}h{m:02d}"
    elif h > 0:
        return f"{h}h"
    else:
        return f"{m}min"

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
    faehre = {"route": faehre_name, "von": h1.title(), "nach": h2.title(), "dauer": FAEHREN[faehre_name]}
    abschnitt_2 = {"start": h2.title(), "ziel": ziel, "zwischen": post_stops}
    return abschnitt_1, faehre, abschnitt_2

# === UI START ===
st.title("🚛 DriverRoute ETA – MAX 04.08")
col1, col2 = st.columns(2)
startort = col1.text_input("📍 Startort", "")
zielort = col2.text_input("🏁 Zielort", "")
now_local, local_tz = get_local_time(startort)
st.caption(get_place_info(startort))
st.caption(get_place_info(zielort))

st.markdown("### ➕ Zwischenstopps")
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

# Fährenwahl
st.markdown("### 🛳️ Fähre")
manuelle_faehre = st.selectbox("Fährverbindung wählen (optional)", ["Keine"] + list(FAEHREN.keys()))
aktive_faehre = None
if manuelle_faehre != "Keine":
    aktive_faehre = {"route": manuelle_faehre, "dauer": FAEHREN[manuelle_faehre]}

# Abfahrtszeit
st.markdown("### 🕓 Abfahrtszeit")
pause_aktiv = st.checkbox("Ich bin in Pause – Abfahrt folgt später")
if pause_aktiv:
    abfahrt_datum = st.date_input("📅 Abfahrtsdatum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, 4)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, 0)
else:
    abfahrt_datum = st.date_input("Datum", value=now_local.date())
    abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
    abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

# Optionen
geschwindigkeit = st.number_input("🛻 Durchschnittsgeschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30min)?")

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

# Wochenruhe optional
st.markdown("### 🛌 Wochenruhepause (optional)")
wochenruhe_manuell = st.checkbox("Wöchentliche Ruhezeit einfügen?")
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

if st.button("📦 Berechnen & ETA anzeigen"):
    log = []
    if not aktive_faehre:
        st.warning("Bitte zuerst eine Fähre auswählen.")
    else:
        abschnitt1, faehre, abschnitt2 = segmentiere_route(startort, zielort, zwischenstopps, aktive_faehre["route"])
        zehner_index = 0
        neuner_index = 0
        used_tank = False
        aktuelle_zeit = start_time

        for i, seg in enumerate([abschnitt1, abschnitt2]):
            km = entfernung_schaetzung(seg["start"], seg["ziel"], seg["zwischen"])
            if km is None:
                st.error(f"❌ Abschnitt {i+1} konnte nicht berechnet werden.")
                break
            log.append(f"🛣️ Abschnitt {i+1}: {seg['start']} → {seg['ziel']} ({km} km)")
            fahrzeit_min = int(km / geschwindigkeit * 60)
            remaining = fahrzeit_min

            while remaining > 0:
                if we_start and we_start <= aktuelle_zeit < we_ende:
                    log.append(f"🛌 Wochenruhe von {we_start.strftime('%Y-%m-%d %H:%M')} bis {we_ende.strftime('%Y-%m-%d %H:%M')}")
                    aktuelle_zeit = we_ende
                    zehner_index = 0
                    neuner_index = 0
                    continue

                if aktuelle_zeit.weekday() == 0 and aktuelle_zeit.hour >= 2:
                    log.append("🔄 Wochenreset: Montag ab 02:00")
                    zehner_index = 0
                    neuner_index = 0

                max_drive = 600 if zehner_index < 2 and zehner_fahrten[zehner_index] else 540
                gefahren = min(remaining, max_drive)
                pausen = math.floor(gefahren / 270) * 45
                if tankpause and not used_tank:
                    pausen += 30
                    used_tank = True
                ende = aktuelle_zeit + timedelta(minutes=gefahren + pausen)
                log.append(f"📆 {aktuelle_zeit.strftime('%a %H:%M')} → {gefahren//60}h{gefahren%60:02d} + {pausen}min Pause → {ende.strftime('%H:%M')}")
                aktuelle_zeit = ende
                remaining -= gefahren

                if remaining <= 0:
                    break

                ruhe = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
                aktuelle_zeit += timedelta(minutes=ruhe)
                log.append(f"🌙 Ruhezeit {ruhe//60}h → Neustart: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
                if zehner_index < 2: zehner_index += 1
                if neuner_index < 3: neuner_index += 1

            # Fähre nach Abschnitt 1
            if i == 0:
                log.append(f"📍 Ankunft Hafen {faehre['von']} um {aktuelle_zeit.strftime('%H:%M')}")
                # Beispielhafte feste Abfahrten: alle 17:30, 21:30 (vereinfacht auf alle 4h)
                stunde = aktuelle_zeit.hour
                abfahrt_stunde = ((stunde // 4) + 1) * 4
                abfahrt_zeit = aktuelle_zeit.replace(minute=0, second=0, microsecond=0) + timedelta(hours=(abfahrt_stunde - stunde))
                wartezeit_min = (abfahrt_zeit - aktuelle_zeit).total_seconds() / 60
                log.append(f"⏱ Wartezeit bis Fähre: {format_minutes_to_hm(wartezeit_min)} → Abfahrt: {abfahrt_zeit.strftime('%H:%M')}")
                aktuelle_zeit = abfahrt_zeit + timedelta(hours=faehre["dauer"])
                log.append(f"🚢 Fähre {faehre['route']} {faehre['dauer']}h → Ankunft: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
                if faehre["dauer"] * 60 >= 540:
                    log.append("✅ Pause vollständig während Fähre erfüllt")
                    zehner_index = 0
                    neuner_index = 0

        # Ausgabe
        st.markdown("## 📋 Fahrplan")
        for eintrag in log:
            st.markdown(eintrag)

        ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
        letzte_ankunft = aktuelle_zeit.astimezone(ziel_tz)
        st.markdown(
            f"<h2 style='text-align: center; color: green;'>✅ <u>Ankunftszeit:</u><br>"
            f"🕓 <b>{letzte_ankunft.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>"
            f"({ziel_tz.zone})</h2>",
            unsafe_allow_html=True)

        # Karte
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        if zwischenstopps:
            waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
            map_url += f"&waypoints={waypoints_encoded}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
