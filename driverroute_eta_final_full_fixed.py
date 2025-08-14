import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Fusion Ultimo", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# ℹ️ App-Anleitung (ein- und ausklappbar)
with st.expander("ℹ️ **Wie funktioniert die App? (Anleitung anzeigen)**", expanded=False):
    st.markdown("""
**🚛 DriverRoute ETA – Kurzanleitung**

Die App berechnet deine **voraussichtliche Ankunftszeit** unter Berücksichtigung von:

- ✅ **Lenkzeiten** (10h/9h-Regeln mit Checkbox)
- 🛌 **Wochenruhezeiten** (optional einplanbar)
- 🛳 **Fährverbindungen** (manuell oder automatisch)
- ⛽ **Tankpausen** (30 min)
- 🕒 **Bereits gefahrene Zeit / Zwischeneinstieg**
- 🗺 **Route & Zwischenstopps** mit Google Maps Karte

> 💡 _Fähren werden automatisch eingebaut, falls aktiv – inkl. Abfahrtszeit, Dauer & gesetzlicher Pause._

""")

# 🚢 Fährenfahrplan (wird im Verlauf genutzt)
FAHRPLAN = {
  "Hirtshals–Kristiansand (Fjord Line)": {
    "gesellschaft": "Fjord Line",
    "dauer_stunden": 2.4167,
    "abfahrten": [
      "09:30",
      "12:10",
      "20:30"
    ]
  },
  "Kristiansand–Hirtshals (Fjord Line)": {
    "gesellschaft": "Fjord Line",
    "dauer_stunden": 2.4167,
    "abfahrten": [
      "08:00",
      "14:20",
      "17:30"
    ]
  },
  "Hirtshals–Kristiansand (Color Line)": {
    "gesellschaft": "Color Line",
    "dauer_stunden": 3.25,
    "abfahrten": [
      "12:15",
      "20:45"
    ]
  },
  "Kristiansand–Hirtshals (Color Line)": {
    "gesellschaft": "Color Line",
    "dauer_stunden": 3.25,
    "abfahrten": [
      "08:00",
      "16:30"
    ]
  },
  "Patras–Ancona (Superfast)": {
    "gesellschaft": "Superfast",
    "dauer_stunden": 22,
    "abfahrten": [
      "08:00",
      "17:30",
      "22:00"
    ]
  },
  "Ancona–Patras (Superfast)": {
    "gesellschaft": "Superfast",
    "dauer_stunden": 22,
    "abfahrten": [
      "08:00",
      "17:30",
      "22:00"
    ]
  },
  "Igoumenitsa–Ancona (Superfast)": {
    "gesellschaft": "Superfast",
    "dauer_stunden": 20,
    "abfahrten": [
      "06:30",
      "13:30",
      "20:00"
    ]
  },
  "Ancona–Igoumenitsa (Superfast)": {
    "gesellschaft": "Superfast",
    "dauer_stunden": 20,
    "abfahrten": [
      "06:30",
      "13:30",
      "20:00"
    ]
  },
  "Igoumenitsa–Bari (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 10,
    "abfahrten": [
      "12:00",
      "18:00",
      "23:59"
    ]
  },
  "Bari–Igoumenitsa (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 10,
    "abfahrten": [
      "10:00",
      "17:00",
      "22:00"
    ]
  },
  "Igoumenitsa–Brindisi (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 9,
    "abfahrten": [
      "08:00",
      "15:00",
      "21:30"
    ]
  },
  "Brindisi–Igoumenitsa (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 9,
    "abfahrten": [
      "07:00",
      "14:00",
      "20:00"
    ]
  },
  "Patras–Bari (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 18,
    "abfahrten": [
      "10:00",
      "19:00"
    ]
  },
  "Bari–Patras (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 18,
    "abfahrten": [
      "08:00",
      "17:00"
    ]
  },
  "Patras–Brindisi (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 19,
    "abfahrten": [
      "07:00",
      "15:00"
    ]
  },
  "Brindisi–Patras (Grimaldi)": {
    "gesellschaft": "Grimaldi",
    "dauer_stunden": 19,
    "abfahrten": [
      "06:00",
      "16:00"
    ]
  },
  "Patras–Venedig (Anek/Superfast)": {
    "gesellschaft": "Anek/Superfast",
    "dauer_stunden": 32,
    "abfahrten": [
      "12:00",
      "19:00"
    ]
  },
  "Venedig–Patras (Anek/Superfast)": {
    "gesellschaft": "Anek/Superfast",
    "dauer_stunden": 32,
    "abfahrten": [
      "12:00",
      "19:00"
    ]
  },
  "Trelleborg–Travemünde (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 9,
    "abfahrten": [
      "02:00",
      "10:00",
      "20:00"
    ]
  },
  "Travemünde–Trelleborg (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 9,
    "abfahrten": [
      "04:00",
      "12:00",
      "22:00"
    ]
  },
  "Travemünde–Trelleborg (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 9,
    "abfahrten": [
      "07:00",
      "22:00"
    ]
  },
  "Trelleborg–Travemünde (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 9,
    "abfahrten": [
      "07:00",
      "22:00"
    ]
  },
  "Trelleborg–Kiel (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 13,
    "abfahrten": [
      "01:00",
      "15:00"
    ]
  },
  "Kiel–Trelleborg (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 13,
    "abfahrten": [
      "05:00",
      "19:00"
    ]
  },
  "Rostock–Trelleborg (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 6.5,
    "abfahrten": [
      "07:00",
      "15:00",
      "23:00"
    ]
  },
  "Trelleborg–Rostock (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 6.5,
    "abfahrten": [
      "07:00",
      "15:00",
      "23:00"
    ]
  },
  "Trelleborg–Swinemünde (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 6.5,
    "abfahrten": [
      "07:00",
      "15:00",
      "23:00"
    ]
  },
  "Swinemünde–Trelleborg (TT-Line)": {
    "gesellschaft": "TT-Line",
    "dauer_stunden": 6.5,
    "abfahrten": [
      "07:00",
      "15:00",
      "23:00"
    ]
  },
  "Grenaa–Halmstad (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 4.5,
    "abfahrten": [
      "08:00",
      "14:00",
      "20:00"
    ]
  },
  "Halmstad–Grenaa (Stena Line)": {
    "gesellschaft": "Stena Line",
    "dauer_stunden": 4.5,
    "abfahrten": [
      "07:00",
      "13:00",
      "19:00"
    ]
  },
  "Color Line Kiel–Oslo": {
    "gesellschaft": "Color Line",
    "dauer_stunden": 20,
    "abfahrten": [
      "14:00"
    ]
  },
  "Color Line Oslo–Kiel": {
    "gesellschaft": "Color Line",
    "dauer_stunden": 20,
    "abfahrten": [
      "14:00"
    ]
  },
  "Hirtshals–Stavanger (FjordLine)": {
    "gesellschaft": "FjordLine",
    "dauer_stunden": 10,
    "abfahrten": [
      "08:00",
      "20:00"
    ]
  },
  "Stavanger–Hirtshals (FjordLine)": {
    "gesellschaft": "FjordLine",
    "dauer_stunden": 10,
    "abfahrten": [
      "09:00",
      "21:00"
    ]
  },
  "Hirtshals–Bergen (FjordLine)": {
    "gesellschaft": "FjordLine",
    "dauer_stunden": 16,
    "abfahrten": [
      "08:00"
    ]
  },
  "Bergen–Hirtshals (FjordLine)": {
    "gesellschaft": "FjordLine",
    "dauer_stunden": 16,
    "abfahrten": [
      "13:30"
    ]
  }
}
# 🌍 Zeitzone holen
def get_timezone_for_address(address):
    if not address: return "Europe/Vienna"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        loc = r["results"][0]["geometry"]["location"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={loc['lat']},{loc['lng']}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        tz_data = requests.get(tz_url).json()
        return tz_data.get("timeZoneId", "Europe/Vienna")
    return "Europe/Vienna"

# 📍 Lokale Zeit
def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

# 📌 PLZ/Ort-Anzeige
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

# ➗ Segmentierung bei Fähre
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
    abschnitt_2 = {"start": h2.title(), "ziel": ziel, "zwischen": post_stops}
    faehre = {"route": faehre_name, "von": h1.title(), "nach": h2.title()}
    return abschnitt_1, faehre, abschnitt_2

# 📍 Start / Ziel Eingabe
st.title("🚛 DriverRoute ETA – Fusion Ultimo")

col1, col2 = st.columns(2)
startort = col1.text_input("📍 Startort oder PLZ", "")
zielort = col2.text_input("🏁 Zielort oder PLZ", "")

now_local, local_tz = get_local_time(startort)
st.caption(get_place_info(startort))
st.caption(get_place_info(zielort))

# ➕ Zwischenstopps
st.markdown("### ➕ Zwischenstopps")
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip()]
for stop in zwischenstopps:
    st.caption(f"Zwischenstopp: {get_place_info(stop)}")

# 🛳️ Fährenlogik (manuell oder automatisch)
st.markdown("### 🛳️ Fährlogik")
manuelle_faehre = st.selectbox("Manuelle Fährwahl (optional)", ["Keine"] + list(FAHRPLAN.keys()))
manuelle_abfahrtszeit = None
if manuelle_faehre != "Keine":
    st.markdown("#### ⏱️ Manuelle Abfahrtszeit der Fähre (optional)")
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

# 🕒 Abfahrt (Pause oder direkt)
st.markdown("### 🕒 Abfahrtszeit planen")
with st.expander("⏳ Pause / Abfahrtszeit einstellen", expanded=False):
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

# 📍 Fahrtzeit & Einsatzzeit in Expander
with st.expander("🕒 Zwischeneinstieg – bereits gefahrene Zeit eingeben"):
    bisher_gefahren_min = st.number_input("Bereits gefahrene Zeit (Minuten)", 0, 600, 0, 15)
    einsatz_bisher_min = st.number_input("Gesamte Einsatzzeit bisher (Minuten)", 0, 720, 0, 15)
    if einsatz_bisher_min > 0:
        start_time -= timedelta(minutes=einsatz_bisher_min)
        st.caption(f"🔁 Startzeit korrigiert: {start_time.strftime('%Y-%m-%d %H:%M')}")

# ⛽ Geschwindigkeit & Tankpause
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

    # ⛴ Fähre segmentieren (wenn vorhanden)
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
        # 📐 Entfernung via Google Maps
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

        km = entfernung_schaetzung(seg["start"], seg["ziel"], seg["zwischen"])
        if km is None:
            st.error(f"❌ Abschnitt {seg['start']} → {seg['ziel']} konnte nicht berechnet werden.")
            st.stop()
        log.append(f"📍 Abschnitt {seg['start']} → {seg['ziel']} ({km} km)")
        fahrzeit_min = int(km / geschwindigkeit * 60)
        remaining = fahrzeit_min

        # 🔁 Bisher gefahrene Zeit berücksichtigen
        if i == 0 and bisher_gefahren_min > 0:
            remaining += bisher_gefahren_min
            log.append(f"🕒 Fahrtzeit bisher: {bisher_gefahren_min} min → wird angerechnet")
# ... (vorheriger Code bleibt unverändert)

        while remaining > 0:
            if we_start and we_start <= aktuelle_zeit < we_ende:
                log.append(f"🛌 Wochenruhe von {we_start.strftime('%Y-%m-%d %H:%M')} bis {we_ende.strftime('%Y-%m-%d %H:%M')}")
                aktuelle_zeit = we_ende
                zehner_index = 0
                neuner_index = 0
                continue

            max_drive = 600 if zehner_index < 2 and zehner_fahrten[zehner_index] else 540
            gefahren = min(remaining, max_drive)

         # 🔹 Neue Pausenlogik: 9h → 45 min, 10h → 90 min
            if gefahren >= 600:       # 10 Stunden Fahrt. 
                pausen = 90
            elif gefahren >= 540:     # 9 Stunden Fahrt
                pausen = 45
            else:
                pausen = (gefahren // 270) * 45

            if tankpause and not used_tank:
                pausen += 30
                used_tank = True

            ende = aktuelle_zeit + timedelta(minutes=gefahren + pausen)
            log.append(f"📆 {aktuelle_zeit.strftime('%a %H:%M')} → {gefahren//60}h{gefahren%60:02d} + {pausen} min → {ende.strftime('%H:%M')}")
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


        # 🛳 Fähre einbauen nach Abschnitt 1
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

    # 📋 Fahrplan anzeigen
    st.markdown("## 📋 Fahrplan:")
    for eintrag in log:
        st.markdown(eintrag)

    # ✅ ETA anzeigen
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
