
import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time
import os

st.set_page_config(page_title="DriverRoute ETA – mit Fähren", layout="centered")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Fähren-Datenbank (inkl. auto-relevant Fähren)
FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9, "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Igoumenitsa–Ancona (Superfast)": 20, "Ancona–Igoumenitsa (Superfast)": 20,
    "Patras–Bari (Grimaldi)": 18, "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19, "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 6.5, "Rostock–Trelleborg (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 13, "Kiel–Trelleborg (TT-Line)": 13,
    "Color Line Kiel–Oslo": 20, "Color Line Oslo–Kiel": 20,
    "Hirtshals–Stavanger (FjordLine)": 10, "Stavanger–Hirtshals (FjordLine)": 10,
    "Hirtshals–Bergen (FjordLine)": 16, "Bergen–Hirtshals (FjordLine)": 16
}

RELEVANTE_FAHRSTRECKEN = ["Patras", "Ancona", "Igoumenitsa", "Bari", "Brindisi",
                          "Trelleborg", "Travemünde", "Rostock", "Kiel", "Oslo",
                          "Hirtshals", "Stavanger", "Bergen"]

def get_timezone_for_latlng(lat, lng):
    timestamp = int(time.time())
    tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={GOOGLE_API_KEY}"
    tz_data = requests.get(tz_url).json()
    return tz_data["timeZoneId"] if tz_data["status"] == "OK" else "Europe/Vienna"

def get_timezone_for_address(address):
    if not address:
        return "Europe/Vienna"
    address = str(address)
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

def ort_enthaelt_faehre(start, ziel):
    return any(hafen in start for hafen in RELEVANTE_FAHRSTRECKEN) and any(hafen in ziel for hafen in RELEVANTE_FAHRSTRECKEN)

def format_minutes_to_hm(minutes):
    if minutes >= 60:
        h, m = divmod(minutes, 60)
        return f"{h}h{m}" if m > 0 else f"{h}h"
    else:
        return f"{minutes} min"

# --- UI START ---

st.title("🚛 DriverRoute ETA – intelligent mit Fähren")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")
now_local, local_tz = get_local_time(startort)

auto_faehre = ort_enthaelt_faehre(startort, zielort)
manuell_aktiv = st.checkbox("🚢 Fähre automatisch erkennen", value=auto_faehre)



def finde_passende_faehre(start, ziel):
    start = start.lower()
    ziel = ziel.lower()
    for route, dauer in FAEHREN.items():
        hafen1, hafen2 = route.lower().split("–")
        if (hafen1 in start and hafen2 in ziel) or (hafen2 in start and hafen1 in ziel):
            return {
                "route": route,
                "datum": now_local.date(),
                "stunde": now_local.hour + 1 if now_local.hour < 23 else 8,
                "minute": 0
            }
    return None

if manuell_aktiv:
    vorschlag = finde_passende_faehre(startort, zielort)
    if "faehren" not in st.session_state:
        st.session_state.faehren = []
    if vorschlag and len(st.session_state.faehren) == 0:
        st.session_state.faehren.append(vorschlag)
        st.success("🚢 Automatisch erkannte Fähre: " + vorschlag["route"])
    st.info("🛳 Fährenrelevante Route erkannt – bitte Fähre(n) anpassen oder ergänzen:")

    st.info("🛳 Fährenrelevante Route erkannt – bitte Fähre(n) angeben:")
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

st.success("🧠 Automatik-Modul Fähre & Pausenlogik wird aktiv berechnet – volle Kontrolle!")



# Eingabe für Abfahrt
abfahrt_datum = st.date_input("📅 Datum der Abfahrt", value=now_local.date())
abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)

if st.button("📦 Berechnen & ETA anzeigen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
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
        fähre_index = 0

        while remaining > 0:
            # Fähre vorrangig behandeln
            if manuell_aktiv and fähre_index < len(st.session_state.faehren):
                f = st.session_state.faehren[fähre_index]
                f_start = local_tz.localize(datetime.combine(f["datum"], datetime.strptime(f"{f['stunde']}:{f['minute']}", "%H:%M").time()))
                f_dauer = FAEHREN.get(f["route"], 0)
                if current_time >= f_start:
                    f_ende = f_start + timedelta(hours=f_dauer)
                    log.append(f"🚢 Fähre {f['route']}: {f_dauer} h → Ankunft {f_ende.strftime('%Y-%m-%d %H:%M')}")
                    current_time = f_ende
                    fähre_index += 1
                    continue

            # Fahrzeitblöcke + Pausenlogik
            block = min(remaining, 540)
            pause = 0
            if block > 270:
                pause = 45  # nur eine 45min Pause ab 4.5h Fahrt

            ende = current_time + timedelta(minutes=block + pause)
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → {format_minutes_to_hm(block)} + {format_minutes_to_hm(pause)} Pause → Ende: {ende.strftime('%H:%M')}")
            current_time = ende
            remaining -= block

            if remaining <= 0:
                break

            # Standardruhezeit
            ruhezeit = 540
            log.append(f"🌙 Ruhe {ruhezeit//60}h → weiter: {(current_time + timedelta(minutes=ruhezeit)).strftime('%Y-%m-%d %H:%M')}")
            current_time += timedelta(minutes=ruhezeit)

        st.markdown("## 📋 Fahrplan:")
        for eintrag in log:
            st.markdown(eintrag)

        ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
        letzte_zeit = current_time.astimezone(ziel_tz)

        st.markdown(f"""
        <h2 style='text-align: center; color: green;'>
        ✅ <u>Ankunftszeit:</u><br>
        🕓 <b>{letzte_zeit.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>
        ({ziel_tz.zone})
        </h2>
        """, unsafe_allow_html=True)

        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
