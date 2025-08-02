
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

def get_timezone_for_address(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo = requests.get(url).json()
    if geo["status"] == "OK":
        loc = geo["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        tz_data = requests.get(tz_url).json()
        return tz_data["timeZoneId"] if tz_data["status"] == "OK" else "Europe/Vienna"
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

def extrahiere_ort(address):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
        response = requests.get(url).json()
        if response["status"] == "OK":
            for comp in response["results"][0]["address_components"]:
                if "locality" in comp["types"] or "postal_town" in comp["types"]:
                    return comp["long_name"].lower()
        return ""
    except:
        return ""

def finde_passende_faehren(start, ziel, now_local):
    ort_start = extrahiere_ort(start)
    ort_ziel = extrahiere_ort(ziel)
    kandidaten = []
    for route, dauer in FAEHREN.items():
        hafen1, hafen2 = [h.strip().lower() for h in route.split("–")]
        if (hafen1 in ort_start and hafen2 in ort_ziel) or (hafen2 in ort_start and hafen1 in ort_ziel):
            kandidaten.append({
                "route": route,
                "dauer": dauer,
                "datum": now_local.date(),
                "stunde": now_local.hour + 1 if now_local.hour < 23 else 8,
                "minute": 0
            })
    return kandidaten

def format_minutes_to_hm(minutes):
    h, m = divmod(int(minutes), 60)
    return f"{h}h{m:02d}min" if h > 0 else f"{m}min"

# --- UI ---
st.title("🚛 DriverRoute ETA – mit intelligenter Fährenauswahl")

startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")
now_local, local_tz = get_local_time(startort)

manuell_aktiv = st.checkbox("🚢 Fähre automatisch erkennen")

if manuell_aktiv:
    vorschlaege = finde_passende_faehren(startort, zielort, now_local)
    if vorschlaege:
        if "faehren" not in st.session_state:
            st.session_state.faehren = []
        if st.button("🛳 Fähre erkannt – Vorschläge anzeigen"):
            with st.expander("Passende Fährverbindungen"):
                auswahl = st.radio(
                    "Bitte Fähre auswählen:",
                    [f"{v['route']} – {v['stunde']}:00 Uhr ({v['dauer']}h)" for v in vorschlaege],
                    index=0
                )
                for v in vorschlaege:
                    bezeichnung = f"{v['route']} – {v['stunde']}:00 Uhr ({v['dauer']}h)"
                    if auswahl == bezeichnung:
                        st.session_state.faehren = [{
                            "route": v["route"],
                            "datum": v["datum"],
                            "stunde": v["stunde"],
                            "minute": v["minute"]
                        }]
                        st.success(f"✅ Fähre übernommen: {v['route']}")

abfahrt_datum = st.date_input("📅 Abfahrtstag", now_local.date())
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
        km = sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000
        total_min = km / geschwindigkeit * 60
        st.success(f"🛣️ Strecke: {round(km,1)} km – {format_minutes_to_hm(total_min)} bei {geschwindigkeit} km/h")

        current_time = start_time
        remaining = total_min
        log = []
        fähre_index = 0

        while remaining > 0:
            if manuell_aktiv and fähre_index < len(st.session_state.get("faehren", [])):
                f = st.session_state["faehren"][fähre_index]
                f_start = local_tz.localize(datetime.combine(f["datum"], datetime.strptime(f"{f['stunde']}:{f['minute']}", "%H:%M").time()))
                f_dauer = FAEHREN.get(f["route"], 0)
                if current_time >= f_start:
                    f_ende = f_start + timedelta(hours=f_dauer)
                    log.append(f"🚢 Fähre {f['route']}: {f_dauer}h → Ankunft {f_ende.strftime('%Y-%m-%d %H:%M')}")
                    current_time = f_ende
                    fähre_index += 1
                    continue

            block = min(remaining, 540)
            pause = 45 if block > 270 else 0
            ende = current_time + timedelta(minutes=block + pause)
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → {format_minutes_to_hm(block)} + {pause}min Pause → Ende: {ende.strftime('%H:%M')}")
            current_time = ende
            remaining -= block

            if remaining <= 0: break
            ruhe = 540
            log.append(f"🌙 Ruhe {ruhe//60}h → weiter: {(current_time + timedelta(minutes=ruhe)).strftime('%Y-%m-%d %H:%M')}")
            current_time += timedelta(minutes=ruhe)

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
