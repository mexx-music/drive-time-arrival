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

def format_minutes_to_hm(minutes):
    if minutes >= 60:
        h, m = divmod(minutes, 60)
        return f"{h}h{m}" if m > 0 else f"{h}h"
    else:
        return f"{minutes} min"

st.title("🚛 DriverRoute ETA – mit Fähren & Wochenlenkzeit")

vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell eingeben"], index=0)
if vorgabe == "Voll (56h)":
    verfügbare_woche = 3360
else:
    verfügbare_woche_stunden = st.number_input("⏱️ Eigene Eingabe (in Stunden)", min_value=0.0, max_value=56.0, value=36.0, step=0.25)
    verfügbare_woche = int(verfügbare_woche_stunden * 60)


def get_full_address(address):
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo_data = requests.get(geo_url).json()
    if geo_data["status"] == "OK":
        return geo_data["results"][0]["formatted_address"]
    return "Adresse nicht gefunden"


startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

if startort:
    full_start = get_full_address(startort)
    st.caption(f"✅ Startadresse erkannt: **{full_start}**")

if zielort:
    full_ziel = get_full_address(zielort)
    st.caption(f"✅ Zieladresse erkannt: **{full_ziel}**")


if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
    if st.session_state.zwischenstopps[i]:
        full = get_full_address(st.session_state.zwischenstopps[i])
        st.caption(f"📌 Adresse {i+1}: **{full}**")

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]
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
        fähre_index = 0

        while remaining > 0:
            if faehren_anzeigen and fähre_index < len(st.session_state.faehren):
                f = st.session_state.faehren[fähre_index]
                f_start = local_tz.localize(datetime.combine(f["datum"], datetime.strptime(f"{f['stunde']}:{f['minute']}", "%H:%M").time()))
                f_dauer = FAEHREN.get(f["route"], 0)
                if current_time >= f_start:
                    f_ende = f_start + timedelta(hours=f_dauer)
                    log.append(f"🚢 Fähre {f['route']}: {f_dauer} h → Ankunft {f_ende.strftime('%Y-%m-%d %H:%M')}")
                    current_time = f_ende
                    fähre_index += 1
                    continue

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
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → {format_minutes_to_hm(gefahren)} + {format_minutes_to_hm(pausen)} Pause → Ende: {ende.strftime('%H:%M')}")
            remaining -= gefahren

            if remaining <= 0:
                break

            ruhezeit = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
            log.append(f"🌙 Ruhe {ruhezeit//60}h → weiter: {(ende + timedelta(minutes=ruhezeit)).strftime('%Y-%m-%d %H:%M')}")
            current_time = ende + timedelta(minutes=ruhezeit)
            if zehner_index < 2: zehner_index += 1
            if neuner_index < 3: neuner_index += 1

        st.markdown("## 📋 Fahrplan:")
        for i, eintrag in enumerate(log):
            if "→ Ende:" in eintrag and i == len(log) - 2:
                time_part = eintrag.split("→ Ende:")[-1].strip()
                eintrag = eintrag.replace(time_part, f"<b><span style='color: green'>{time_part}</span></b>")
                st.markdown(eintrag, unsafe_allow_html=True)
            else:
                st.markdown(eintrag)
        verbl_10h = max(0, zehner_fahrten.count(True) - zehner_index)
        verbl_9h = max(0, neuner_ruhen.count(True) - neuner_index)
        st.info(f"🧮 Verbleibend: {verbl_10h}× 10h, {verbl_9h}× 9h")

        verbleibend_min = verfügbare_woche - total_min
        if verbleibend_min < 0:
            überschuss = abs(verbleibend_min)
            h_m, m_m = divmod(überschuss, 60)
            st.warning(f"⚠️ Achtung: Wochenlenkzeit überschritten um {h_m} h {m_m} min!")
        else:
            h, m = divmod(verbleibend_min, 60)
            st.info(f"🧭 Verbleibende Wochenlenkzeit: {h}h {m}min")

        ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
        letzte_zeit = ende.astimezone(ziel_tz)

        st.markdown(f"""
        <h2 style='text-align: center; color: green;'>
        ✅ <u>Ankunftszeit:</u><br>
        🕓 <b>{letzte_zeit.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>
        ({ziel_tz.zone})
        </h2>
        """, unsafe_allow_html=True)

        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        if zwischenstopps:
            waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
            map_url += f"&waypoints={waypoints_encoded}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
