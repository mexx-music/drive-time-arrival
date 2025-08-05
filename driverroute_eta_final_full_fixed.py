import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(page_title="DriverRoute ETA – Bereinigte Version", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.title("🚛 DriverRoute ETA – Bereinigte Version")

with st.expander("ℹ️ **Wie funktioniert die App? (Anleitung anzeigen)**", expanded=False):
    st.markdown("""
🚛 **DriverRoute ETA – Kurzanleitung**

- Die App berechnet deine **Ankunftszeit (ETA)** basierend auf:
    - gesetzlicher **Lenk- und Ruhezeit** (inkl. 10h/9h-Regeln)
    - **Wochenruhezeit**, wenn aktiviert
    - **Fährverbindungen** (manuell oder automatisch erkannt)
    - individuellen **Zwischenstopps**

🛳️ **Hinweis zu Fähren**:
- Google Maps zeigt bei Fährverbindungen oft **unrealistische Linien durch das Meer**.
- Die **berechnete Zeit stimmt trotzdem**, da die App den **echten Fahrplan** und die **gesetzliche Ruhezeit** berücksichtigt.
""")

FAHRPLAN = {
    "Patras–Ancona (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 22, "abfahrten": ["08:00", "17:30", "22:00"]},
    "Ancona–Patras (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 22, "abfahrten": ["08:00", "17:30", "22:00"]},
    "Igoumenitsa–Ancona (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 20, "abfahrten": ["06:30", "13:30", "20:00"]},
    "Ancona–Igoumenitsa (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 20, "abfahrten": ["06:30", "13:30", "20:00"]},
    "Igoumenitsa–Bari (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 10, "abfahrten": ["12:00", "18:00", "23:59"]},
    "Bari–Igoumenitsa (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 10, "abfahrten": ["10:00", "17:00", "22:00"]},
    "Trelleborg–Travemünde (TT-Line)": {"gesellschaft": "TT-Line", "dauer_stunden": 9, "abfahrten": ["02:00", "10:00", "20:00"]},
    "Travemünde–Trelleborg (TT-Line)": {"gesellschaft": "TT-Line", "dauer_stunden": 9, "abfahrten": ["04:00", "12:00", "22:00"]},
}

def get_timezone_for_address(address):
    if not address:
        return "Europe/Vienna"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        loc = r["results"][0]["geometry"]["location"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={loc['lat']},{loc['lng']}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        tz_data = requests.get(tz_url).json()
        return tz_data.get("timeZoneId", "Europe/Vienna")
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

# 🛳 Fährenlogik – manuell oder automatisch
st.markdown("### 🛳️ Fährlogik")
manuelle_faehre = st.selectbox("Manuelle Fährwahl (optional)", ["Keine"] + list(FAHRPLAN.keys()))
manuelle_abfahrtszeit = None

if manuelle_faehre != "Keine":
    st.markdown("#### ⏱️ Manuelle Abfahrtszeit (optional)")
    fae_datum = st.date_input("📆 Datum", value=now_local.date(), key="fae_datum")
    fae_std = st.number_input("🕓 Stunde", 0, 23, 20, key="fae_std")
    fae_min = st.number_input("🕧 Minute", 0, 59, 0, key="fae_min")
    manuelle_abfahrtszeit = datetime.combine(fae_datum, datetime.strptime(f"{fae_std}:{fae_min}", "%H:%M").time())
    manuelle_abfahrtszeit = local_tz.localize(manuelle_abfahrtszeit)

auto_faehre = st.checkbox("🚢 Automatische Fährenerkennung aktivieren", value=True)

aktive_faehren = []
if manuelle_faehre != "Keine":
    f = FAHRPLAN[manuelle_faehre]
    aktive_faehren.append({
        "route": manuelle_faehre,
        "dauer": f["dauer_stunden"],
        "abfahrten": f["abfahrten"]
    })
elif auto_faehre:
    for name, daten in FAHRPLAN.items():
        h1, h2 = name.lower().split("–")
        route_orte = [startort] + zwischenstopps + [zielort]
        if any(h1 in ort.lower() or h2 in ort.lower() for ort in route_orte):
            if st.checkbox(f"{name} ({daten['dauer_stunden']} h)", key=f"chk_{name}"):
                aktive_faehren.append({
                    "route": name,
                    "dauer": daten["dauer_stunden"],
                    "abfahrten": daten["abfahrten"]
                })

# 🕒 Abfahrtszeit
st.markdown("### 🕒 Abfahrtszeit planen")
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

# 🔁 Zusatz: Bisherige Fahrzeit & Einsatzzeit
st.markdown("### 📍 Zwischeneinstieg – bisherige Fahrt erfassen")

st.markdown("### 🕓 Bereits gefahrene Lenkzeit heute (optional)")
col_b1, col_b2 = st.columns(2)
with col_b1:
    gefahrene_stunden = st.number_input("🕓 Stunden", 0, 10, 0, step=1)
with col_b2:
    gefahrene_minuten = st.number_input("🕧 Minuten", 0, 59, 0, step=5)

bisher_gefahren_min = gefahrene_stunden * 60 + gefahrene_minuten
if bisher_gefahren_min > 0:
    st.info(f"✅ Bereits gefahren: {gefahrene_stunden}h{gefahrene_minuten:02d}")

st.markdown("### ⏱ Gesamteinsatzzeit bisher (optional)")
col_e1, col_e2 = st.columns(2)
with col_e1:
    einsatz_stunden = st.number_input("⏱ Stunden", 0, 12, 0, step=1)
with col_e2:
    einsatz_minuten = st.number_input("Minuten", 0, 59, 0, step=5)

einsatz_bisher_min = einsatz_stunden * 60 + einsatz_minuten
if einsatz_bisher_min > 0:
    start_time -= timedelta(minutes=einsatz_bisher_min)
    st.caption(f"🔁 Neue Startzeit durch Rückrechnung: {start_time.strftime('%Y-%m-%d %H:%M')}")

# ⛽ Geschwindigkeit + Tankpause
geschwindigkeit = st.number_input("🛻 Durchschnittsgeschwindigkeit (km/h)", 60, 120, 80)
tankpause = st.checkbox("⛽ Tankpause (30 min)?")

# 🛌 Wochenruhepause
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

# 🟩 10h / 9h-Kästchen
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

# 🚦 Start der Berechnung
if st.button("📦 Berechnen & ETA anzeigen"):
    log = []
    aktuelle_zeit = start_time
    letzte_ankunft = None
    used_tank = False
    zehner_index = 0
    neuner_index = 0

    # Fährenlogik vorbereiten
    if aktive_faehren:
        f = aktive_faehren[0]
        abschnitt1, faehre, abschnitt2 = segmentiere_route(startort, zielort, zwischenstopps, f["route"])
        segmente = [abschnitt1, abschnitt2]
        fährblock = {
            "route": f["route"],
            "von": faehre["von"],
            "nach": faehre["nach"],
            "dauer": f["dauer"],
            "abfahrten": f["abfahrten"]
        }
    else:
        segmente = [{"start": startort, "ziel": zielort, "zwischen": zwischenstopps}]
        fährblock = None

    for i, seg in enumerate(segmente):
        km = entfernung_schaetzung(seg["start"], seg["ziel"], seg["zwischen"])
        if km is None:
            st.error(f"❌ Abschnitt {seg['start']} → {seg['ziel']} konnte nicht berechnet werden.")
            st.stop()
        log.append(f"📍 Abschnitt {seg['start']} → {seg['ziel']} ({km} km)")
        fahrzeit_min = int(km / geschwindigkeit * 60)
        remaining = fahrzeit_min

        # 🔁 Bisher gefahrene Zeit einrechnen
        if i == 0 and bisher_gefahren_min > 0:
            remaining += bisher_gefahren_min
            log.append(f"🕒 Fahrtzeit bisher: {bisher_gefahren_min} min → wird angerechnet")

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
            pausen = 45 if gefahren >= 270 else 0
            if tankpause and not used_tank:
                pausen += 30
                used_tank = True

            ende = aktuelle_zeit + timedelta(minutes=gefahren + pausen)
            log.append(f"📆 {aktuelle_zeit.strftime('%a %H:%M')} → {gefahren//60}h{gefahren%60:02d} + {pausen} min → {ende.strftime('%H:%M')}")
            aktuelle_zeit = ende
            remaining -= gefahren
            letzte_ankunft = ende

            if remaining <= 0:
                break

            ruhe = 540 if neuner_index < 3 and neuner_ruhen[neuner_index] else 660
            aktuelle_zeit += timedelta(minutes=ruhe)
            log.append(f"🌙 Ruhezeit {ruhe//60}h → Neustart: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
            if zehner_index < 2: zehner_index += 1
            if neuner_index < 3: neuner_index += 1

        # 🛳 Fähre einbauen
        if fährblock and i == 0:
            log.append(f"📍 Ankunft Hafen {fährblock['von']} um {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")
            abfahrtszeiten = fährblock.get("abfahrten", [])
            naechste_abfahrt = None
            for abf in abfahrtszeiten:
                h, m = map(int, abf.split(":"))
                geplante_abfahrt = aktuelle_zeit.replace(hour=h, minute=m, second=0, microsecond=0)
                if geplante_abfahrt >= aktuelle_zeit:
                    naechste_abfahrt = geplante_abfahrt
                    break
            if not naechste_abfahrt and abfahrtszeiten:
                h, m = map(int, abfahrtszeiten[0].split(":"))
                naechste_abfahrt = aktuelle_zeit.replace(hour=h, minute=m) + timedelta(days=1)

            if manuelle_abfahrtszeit:
                aktuelle_zeit = manuelle_abfahrtszeit
                log.append(f"🕓 Manuelle Abfahrt der Fähre: {manuelle_abfahrtszeit.strftime('%Y-%m-%d %H:%M')}")
            elif naechste_abfahrt:
                wartezeit = int((naechste_abfahrt - aktuelle_zeit).total_seconds() / 60)
                log.append(f"⏱ Wartezeit bis Fähre: {wartezeit//60}h{wartezeit%60:02d} → Abfahrt: {naechste_abfahrt.strftime('%H:%M')}")
                aktuelle_zeit = naechste_abfahrt

            aktuelle_zeit += timedelta(hours=fährblock["dauer"])
            letzte_ankunft = aktuelle_zeit
            log.append(f"🚢 Fähre {fährblock['route']} {fährblock['dauer']}h → Ankunft: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')}")

            if fährblock["dauer"] * 60 >= 540:
                log.append("✅ Pause vollständig während Fähre erfüllt")
                zehner_index = 0
                neuner_index = 0

    # 📋 Ausgabe
    st.markdown("## 📋 Fahrplan:")
    for eintrag in log:
        st.markdown(eintrag)

    # ✅ ETA-Anzeige
    ziel_tz = pytz.timezone(get_timezone_for_address(zielort))
    if letzte_ankunft:
        letzte_ankunft = letzte_ankunft.astimezone(ziel_tz)
        st.markdown(
            f"<h2 style='text-align: center; color: green;'>✅ <u>Ankunftszeit:</u><br>"
            f"🕓 <b>{letzte_ankunft.strftime('%A, %d.%m.%Y – %H:%M')}</b></h2>",
            unsafe_allow_html=True
        )
    else:
        st.error("❌ Ankunftszeit konnte nicht berechnet werden – bitte Eingaben prüfen.")

    # 🗺️ Google Maps Karte
    map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
    if zwischenstopps:
        waypoints_encoded = '|'.join([urllib.parse.quote(s) for s in zwischenstopps])
        map_url += f"&waypoints={waypoints_encoded}"
    st.markdown("### 🗺️ Routenkarte:")
    st.components.v1.iframe(map_url, height=500)
