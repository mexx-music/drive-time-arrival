
import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Modularisiert", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# 🚢 Fährdaten mit echten Fahrplänen
FAEHREN = {
    "Patras–Ancona (Superfast)": {"dauer": 22, "abfahrten": ["17:30", "23:00"]},
    "Ancona–Patras (Superfast)": {"dauer": 22, "abfahrten": ["18:00"]},
    "Igoumenitsa–Ancona (Superfast)": {"dauer": 20, "abfahrten": ["21:00"]},
    "Igoumenitsa–Bari (Grimaldi)": {"dauer": 10, "abfahrten": ["12:00", "20:00"]},
    "Trelleborg–Rostock (TT-Line)": {"dauer": 6.5, "abfahrten": ["07:00", "11:00", "15:00", "23:30"]},
    "Rostock–Trelleborg (TT-Line)": {"dauer": 6.5, "abfahrten": ["09:00", "15:00", "22:00"]},
    "Color Line Kiel–Oslo": {"dauer": 20, "abfahrten": ["14:00"]},
    "Hirtshals–Bergen (FjordLine)": {"dauer": 16, "abfahrten": ["20:00"]}
}

# 🌍 Zeitzonen-Handling
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

# ⏳ Nächste Fährabfahrt finden
def finde_naechste_abfahrt(faehre_name, aktuelle_zeit):
    daten = FAEHREN.get(faehre_name)
    if not daten:
        return aktuelle_zeit, 0
    abfahrtszeiten = daten["abfahrten"]
    aktuelle_datum = aktuelle_zeit.date()
    aktuelle_uhrzeit = aktuelle_zeit.time()
    for abf in abfahrtszeiten:
        abfahrt_dt = datetime.combine(aktuelle_datum, datetime.strptime(abf, "%H:%M").time())
        if aktuelle_uhrzeit < abfahrt_dt.time():
            warte = (abfahrt_dt - aktuelle_zeit).total_seconds() / 60
            return abfahrt_dt, int(warte)
    morgen = aktuelle_zeit + timedelta(days=1)
    erste_abfahrt = datetime.combine(morgen.date(), datetime.strptime(abfahrtszeiten[0], "%H:%M").time())
    warte = (erste_abfahrt - aktuelle_zeit).total_seconds() / 60
    return erste_abfahrt, int(warte)

# 🧮 Fahrblock berechnen (1 Etappe)
def berechne_fahrblock(startzeit, km, geschwindigkeit, zehner=True, tankpause=False):
    log = []
    dauer_min = int(km / geschwindigkeit * 60)
    max_fahrt = 600 if zehner else 540
    gefahren = min(dauer_min, max_fahrt)
    pause_min = (gefahren // 270) * 45
    if tankpause:
        pause_min += 30
    ende = startzeit + timedelta(minutes=gefahren + pause_min)
    log.append(f"📆 Fahrtblock: {gefahren} min + {pause_min} min → {ende.strftime('%Y-%m-%d %H:%M')}")
    return log, ende, dauer_min - gefahren

# 🌙 Ruhezeit berechnen
def berechne_ruhesegment(startzeit, neuner=True):
    ruhe = 540 if neuner else 660
    ende = startzeit + timedelta(minutes=ruhe)
    log = f"🌙 Ruhezeit {ruhe//60}h → weiter: {ende.strftime('%Y-%m-%d %H:%M')}"
    return [log], ende

# 🎛️ UI
st.title("🚛 DriverRoute ETA – Modularisiert")

startort = st.text_input("📍 Startort", "Patras, Griechenland")
zielort = st.text_input("🏁 Zielort", "Ancona, Italien")
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

now_local, local_tz = get_local_time(startort)
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

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")
faehre_name = st.selectbox("🛳️ Fähre (optional)", ["Keine"] + list(FAEHREN.keys()))
zehner_1 = st.checkbox("✅ 10h-Fahrt möglich", value=True)
neuner_1 = st.checkbox("✅ 9h-Ruhepause erlaubt", value=True)

# ▶️ Berechnung starten
if st.button("📦 Berechnung starten"):
    log = []
    aktuelle_zeit = start_time

    # Fähre einbauen
    if faehre_name != "Keine":
        abfahrt, warte = finde_naechste_abfahrt(faehre_name, aktuelle_zeit)
        if warte > 0:
            log.append(f"⏳ Wartezeit auf Fähre **{faehre_name}** bis {abfahrt.strftime('%Y-%m-%d %H:%M')} ({warte} min)")
            aktuelle_zeit = abfahrt
        dauer = FAEHREN[faehre_name]["dauer"]
        aktuelle_zeit += timedelta(hours=dauer)
        log.append(f"🚢 Fähre {faehre_name} – {dauer} h → Ankunft: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
        if dauer * 60 >= 540:
            log.append("✅ Ruhezeit vollständig während Fähre erfüllt")

    # Fahrt & Ruheblöcke
    fahr_log, neue_zeit, rest = berechne_fahrblock(aktuelle_zeit, 500, geschwindigkeit, zehner_1, tankpause)
    log.extend(fahr_log)
    aktuelle_zeit = neue_zeit

    if rest > 0:
        ruhe_log, aktuelle_zeit = berechne_ruhesegment(aktuelle_zeit, neuner_1)
        log.extend(ruhe_log)

    ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
    letzte_zeit = aktuelle_zeit.astimezone(ziel_tz)

    st.markdown("## 📋 Fahrplan:")
    for eintrag in log:
        st.markdown(eintrag)

    st.markdown(f"<h2 style='text-align: center; color: green;'>✅ Ankunft: {letzte_zeit.strftime('%A, %d.%m.%Y – %H:%M')}</h2>", unsafe_allow_html=True)

    # 🗺️ Karte anzeigen
    map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
    if zwischenstopps:
        waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
        map_url += f"&waypoints={waypoints_encoded}"
    st.markdown("### 🗺️ Routenkarte:")
    st.components.v1.iframe(map_url, height=500)
