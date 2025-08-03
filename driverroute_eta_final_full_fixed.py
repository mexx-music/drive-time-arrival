
# 🚛 DriverRoute ETA – Final Kombiversion (Stabil + NextGen)
# Funktionen: Zwischenstopps, PLZ, Wochenzeit, manuelle/automatische Fähren, Dropdown-Auswahl, ETA, Karte etc.

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Kombiversion", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Fährenliste
FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Igoumenitsa–Ancona (Superfast)": 20,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Igoumenitsa–Brindisi (Grimaldi)": 9,
    "Patras–Bari (Grimaldi)": 18, "Patras–Brindisi (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Trelleborg–Rostock (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 13, "Color Line Kiel–Oslo": 20,
    "Hirtshals–Bergen (FjordLine)": 16
}

# Zeitzonenlogik
def get_timezone_for_address(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        loc = r["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        return requests.get(tz_url).json().get("timeZoneId", "Europe/Vienna")
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

# PLZ-Anzeige
def get_place_info(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        components = r["results"][0]["address_components"]
        plz = ort = land = ""
        for c in components:
            if "postal_code" in c["types"]: plz = c["long_name"]
            if "locality" in c["types"]: ort = c["long_name"]
            if "country" in c["types"]: land = c["long_name"]
        return f"📌 {ort}, {plz} ({land})"
    return "❌ Ort nicht gefunden"

def extrahiere_ort(address):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
        r = requests.get(url).json()
        for c in r["results"][0]["address_components"]:
            if "locality" in c["types"]: return c["long_name"].lower()
    except: return ""
    return ""

def finde_passende_faehren(start, ziel, now_local):
    ort_start = extrahiere_ort(start)
    kandidaten = []
    for route, dauer in FAEHREN.items():
        h1, h2 = [h.strip().lower() for h in route.split("–")]
        if ort_start in h1 or ort_start in h2:
            kandidaten.append({
                "route": route,
                "dauer": dauer,
                "datum": now_local.date(),
                "stunde": now_local.hour + 1 if now_local.hour < 23 else 8,
                "minute": 0
            })
    return kandidaten

def format_minutes_to_hm(mins):
    h, m = divmod(int(mins), 60)
    return f"{h}h{m:02d}" if h else f"{m} min"

# UI START
st.title("🚛 DriverRoute ETA – Final Kombiversion")

startort = st.text_input("📍 Startort", "Igoumenitsa")
zielort = st.text_input("🏁 Zielort", "Ancona")
st.caption(get_place_info(startort))
st.caption(get_place_info(zielort))

now_local, local_tz = get_local_time(startort)

# Zwischenstopps
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []
if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")
for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
    st.caption(get_place_info(st.session_state.zwischenstopps[i]))

# Wochenlenkzeit
vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell"], index=0)
verfuegbar = 3360 if vorgabe == "Voll (56h)" else int(st.number_input("⏱️ Eingabe (h)", 0.0, 56.0, 36.0, 0.25) * 60)

# Abfahrt
abfahrt_datum = st.date_input("📅 Abfahrtstag", now_local.date())
abfahrt_stunde = st.number_input("🕓 Stunde", 0, 23, now_local.hour)
abfahrt_minute = st.number_input("🕧 Minute", 0, 59, now_local.minute)
abfahrt_time = datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time())
start_time = local_tz.localize(abfahrt_time)

# 10h / 9h Optionen
st.subheader("Fahrerzeiten")
zehner = [st.checkbox(f"✅ 10h-Fahrt Nr. {i+1}", value=True) for i in range(2)]
neuner = [st.checkbox(f"✅ 9h-Ruhepause Nr. {i+1}", value=True) for i in range(3)]

# Wochenruhe
we_pause = st.checkbox("🛌 Wochenruhe während Tour manuell einfügen?")
if we_pause:
    tag = st.date_input("Start der Wochenruhe", value=now_local.date(), key="we_datum")
    stunde = st.number_input("Stunde", 0, 23, 12, key="we_stunde")
    minute = st.number_input("Minute", 0, 59, 0, key="we_minute")
    dauer = st.number_input("Dauer der Pause (h)", 24, 72, 45, key="we_dauer")
    we_start = local_tz.localize(datetime.combine(tag, datetime.strptime(f"{stunde}:{minute}", "%H:%M").time()))
    we_ende = we_start + timedelta(hours=dauer)
else:
    we_start = we_ende = None

# Fähre manuell oder automatisch
auto_faehre = st.checkbox("🚢 Fähre automatisch erkennen", value=True)
faehren = []
if auto_faehre:
    vorschlaege = finde_passende_faehren(startort, zielort, now_local)
    if vorschlaege and st.button("🛳 Fähre erkannt – Vorschläge anzeigen"):
        with st.expander("Passende Fähren"):
            auswahl = st.selectbox("Fähre wählen:", [f"{v['route']} – {v['stunde']}:00 ({v['dauer']}h)" for v in vorschlaege])
            for v in vorschlaege:
                if auswahl.startswith(v["route"]):
                    faehren.append(v)
                    st.success(f"✅ Fähre übernommen: {v['route']}")
else:
    if st.checkbox("✚ Fähre manuell hinzufügen"):
        faehren.append({
            "route": list(FAEHREN.keys())[0],
            "datum": now_local.date(),
            "stunde": 12,
            "minute": 0
        })

# Tankpause & Geschwindigkeit
tankpause = st.checkbox("⛽ Tankpause (30 min)?")
geschwindigkeit = st.number_input("🛻 Geschwindigkeit (km/h)", 60, 120, 80)

# Berechnung
if st.button("📦 Berechnen & ETA anzeigen"):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}&key={GOOGLE_API_KEY}"
    if st.session_state.zwischenstopps:
        url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in st.session_state.zwischenstopps])}"
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        st.error("Routenfehler")
    else:
        km = round(sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000, 1)
        total_min = int(km / geschwindigkeit * 60)
        st.success(f"🛣️ Strecke: {km} km – {total_min}min bei {geschwindigkeit} km/h")

        current_time = start_time
        remaining = total_min
        log, z_i, n_i, used_tank, f_i = [], 0, 0, False, 0

        while remaining > 0:
            if f_i < len(faehren):
                f = faehren[f_i]
                f_start = local_tz.localize(datetime.combine(f["datum"], datetime.strptime(f"{f['stunde']}:{f['minute']}", "%H:%M").time()))
                if current_time >= f_start:
                    f_dauer = FAEHREN[f["route"]]
                    f_ende = f_start + timedelta(hours=f_dauer)
                    log.append(f"🚢 Fähre {f['route']}: {f_dauer}h → Ankunft {f_ende.strftime('%Y-%m-%d %H:%M')}")
                    current_time = f_ende
                    f_i += 1
                    continue

            if we_start and we_start <= current_time < we_ende:
                current_time = we_ende
                z_i = n_i = 0
                log.append(f"🛌 Wochenruhe {we_start.strftime('%Y-%m-%d %H:%M')} – {we_ende.strftime('%Y-%m-%d %H:%M')}")
                continue

            max_drive = 600 if z_i < 2 and zehner[z_i] else 540
            block = min(remaining, max_drive)
            pause = 45 if block >= 270 else 0
            if tankpause and not used_tank:
                pause += 30
                used_tank = True

            ende = current_time + timedelta(minutes=block + pause)
            log.append(f"📆 {current_time.strftime('%A %H:%M')} → {format_minutes_to_hm(block)} + {pause}min → {ende.strftime('%H:%M')}")
            remaining -= block
            if remaining <= 0: break

            ruhe = 540 if n_i < 3 and neuner[n_i] else 660
            log.append(f"🌙 Ruhe {ruhe//60}h → weiter: {(ende + timedelta(minutes=ruhe)).strftime('%Y-%m-%d %H:%M')}")
            current_time = ende + timedelta(minutes=ruhe)
            if z_i < 2: z_i += 1
            if n_i < 3: n_i += 1

        st.markdown("## 📋 Fahrplan:")
        for eintrag in log: st.markdown(eintrag)
        st.markdown(f"<h2 style='text-align: center;'>🕓 Ankunft: <b>{current_time.strftime('%A, %d.%m.%Y – %H:%M')}</b></h2>", unsafe_allow_html=True)

        # Karte anzeigen
        map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"
        if st.session_state.zwischenstopps:
            map_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in st.session_state.zwischenstopps])}"
        st.markdown("### 🗺️ Routenkarte:")
        st.components.v1.iframe(map_url, height=500)
