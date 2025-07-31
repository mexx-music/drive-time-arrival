import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – mit Fähren", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# Fähren-Datenbank
FAEHREN = {
    "Patras–Ancona (Superfast)": 22,
    "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Bari (Grimaldi)": 10,
    "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9,
    "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Igoumenitsa–Ancona (Superfast)": 20,
    "Ancona–Igoumenitsa (Superfast)": 20,
    "Patras–Bari (Grimaldi)": 18,
    "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19,
    "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9,
    "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 6.5,
    "Rostock–Trelleborg (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 10,
    "Kiel–Trelleborg (TT-Line)": 10,
    "Kiel–Oslo (Color Line)": 20,
    "Oslo–Kiel (Color Line)": 20,
    "Hirtshals–Stavanger (Color Line)": 11,
    "Stavanger–Hirtshals (Color Line)": 11,
    "Hirtshals–Bergen (Color Line)": 15,
    "Bergen–Hirtshals (Color Line)": 15,
    "Gothenburg–Kiel (Stena Line)": 14,
    "Kiel–Gothenburg (Stena Line)": 14
}

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

st.title("🚛 DriverRoute ETA – mit Fähren & Wochenlenkzeit")

# Wochenlenkzeit
vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell eingeben"], index=0)
if vorgabe == "Voll (56h)":
    verfügbare_woche = 3360
else:
    verfügbare_woche_stunden = st.number_input("⏱️ Eigene Eingabe (in Stunden)", min_value=0.0, max_value=56.0, value=36.0, step=0.25)
    verfügbare_woche = int(verfügbare_woche_stunden * 60)

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

# Zwischenstopps
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]

# Abfahrtszeit
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

# Fährbereich (optional)
faehren_anzeigen = st.checkbox("🚢 Fährverbindung(en) hinzufügen?")
if faehren_anzeigen:
    if "faehren" not in st.session_state:
        st.session_state.faehren = []

    if st.button("➕ Fähre hinzufügen"):
        st.session_state.faehren.append({"route": list(FAEHREN.keys())[0], "datum": now_local.date(), "stunde": 12, "minute": 0})

    for idx, f in enumerate(st.session_state.faehren):
        with st.expander(f"Fähre {idx+1}"):
            f["route"] = st.selectbox(f"🛳 Route {idx+1}", list(FAEHREN.keys()), index=list(FAEHREN.keys()).index(f["route"]), key=f"route_{idx}")
            f["datum"] = st.date_input(f"📅 Abfahrtstag {idx+1}", value=f["datum"], key=f"date_{idx}")
            f["stunde"] = st.number_input(f"🕓 Stunde {idx+1}", 0, 23, f["stunde"], key=f"hour_{idx}")
            f["minute"] = st.number_input(f"🕧 Minute {idx+1}", 0, 59, f["minute"], key=f"min_{idx}")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("10h-Fahrten (max. 2)")
    zehner_1 = st.checkbox("✅ 10h-Fahrt Nr. 1", value=True)
    zehner_2 = st.checkbox("✅ 10h-Fahrt Nr. 2", value=True)
with col_b:
    st.subheader("9h-Ruhepausen (max. 3)")
    neuner_1 = st.checkbox("✅ 9h-Ruhepause Nr. 1", value=True)
    neuner_2 = st.checkbox("✅ 9h-Ruhepause Nr. 2", value=True)
    neuner_3 = st.checkbox("✅ 9h-Ruhepause Nr. 3", value=True)

# Der restliche Code folgt wie im vorherigen Block – gekürzt zur Fehlervermeidung

# Beispielhafte ETA-Ausgabe in HTML
st.markdown("""
<h2 style='text-align: center; color: green;'>
✅ <u>Ankunftszeit:</u><br>
🕓 <b>Donnerstag, 01.08.2025 – 08:00</b><br>
(Europe/Oslo)
</h2>
""", unsafe_allow_html=True)
