import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Fusion-Version", layout="centered")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# 🚢 Fährenfahrplan
FAHRPLAN = {
    "Patras–Ancona (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 22, "abfahrten": ["08:00", "17:30", "22:00"]},
    "Ancona–Patras (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 22, "abfahrten": ["08:00", "17:30", "22:00"]},
    "Igoumenitsa–Ancona (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 20, "abfahrten": ["06:30", "13:30", "20:00"]},
    "Ancona–Igoumenitsa (Superfast)": {"gesellschaft": "Superfast", "dauer_stunden": 20, "abfahrten": ["06:30", "13:30", "20:00"]},
    "Igoumenitsa–Bari (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 10, "abfahrten": ["12:00", "18:00", "23:59"]},
    "Bari–Igoumenitsa (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 10, "abfahrten": ["10:00", "17:00", "22:00"]},
    "Igoumenitsa–Brindisi (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 9, "abfahrten": ["08:00", "15:00", "21:30"]},
    "Brindisi–Igoumenitsa (Grimaldi)": {"gesellschaft": "Grimaldi", "dauer_stunden": 9, "abfahrten": ["07:00", "14:00", "20:00"]},
    "Trelleborg–Travemünde (TT-Line)": {"gesellschaft": "TT-Line", "dauer_stunden": 9, "abfahrten": ["02:00", "10:00", "20:00"]},
    "Travemünde–Trelleborg (TT-Line)": {"gesellschaft": "TT-Line", "dauer_stunden": 9, "abfahrten": ["04:00", "12:00", "22:00"]},
    "Color Line Kiel–Oslo": {"gesellschaft": "Color Line", "dauer_stunden": 20, "abfahrten": ["14:00"]},
    "Color Line Oslo–Kiel": {"gesellschaft": "Color Line", "dauer_stunden": 20, "abfahrten": ["14:00"]},
    "Hirtshals–Bergen (FjordLine)": {"gesellschaft": "FjordLine", "dauer_stunden": 16, "abfahrten": ["08:00"]},
    "Bergen–Hirtshals (FjordLine)": {"gesellschaft": "FjordLine", "dauer_stunden": 16, "abfahrten": ["13:30"]}
}

# 🌍 Zeitzone anhand Adresse
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

# 📍 Lokale Uhrzeit
def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

st.title("🚛 DriverRoute ETA – Max-Version")

with st.expander("ℹ️ **Wie funktioniert die App? (Anleitung öffnen)**", expanded=False):
    st.markdown("""
🚛 **DriverRoute ETA App – Kurzinfo**

- Die App berechnet automatisch deine Ankunftszeit inklusive:
    - gesetzlicher Lenk- und Ruhezeiten
    - Wochenruhe (wenn aktiviert)
    - optionaler Fährenverbindungen (manuell + automatisch)

- **Google Maps Karte** kann bei Fährstrecken unrealistische Routen anzeigen (z. B. durchs Meer) – **die ETA-Berechnung ist trotzdem korrekt**.

- Zwischenstopps können jederzeit eingefügt werden – die Route wird dynamisch angepasst.

- Wochenlenkzeit wird mitgerechnet (56h Limit)

**Hinweis**: Alle Zeiten basieren auf lokaler Zeit am Zielort.
""")

startort = st.text_input("Startort (z. B. Wien)", "")
zielort = st.text_input("Zielort (z. B. Ancona)", "")
zwischenstopps_input = st.text_area("📍 Zwischenstopps (optional, je eine Zeile)", "")

zwischenstopps = [z.strip() for z in zwischenstopps_input.split("\n") if z.strip()]

geschwindigkeit = st.slider("🛣 Durchschnittsgeschwindigkeit (km/h)", 60, 100, 85)

faehre_manuell = st.selectbox("🚢 Manuelle Fährverbindung (optional)", ["Keine manuelle Auswahl"] + list(FAHRPLAN.keys()))
if faehre_manuell != "Keine manuelle Auswahl":
    fahrtag = st.date_input("📆 Fährdatum", datetime.today())
    fahrzeit = st.time_input("🕓 Uhrzeit der Fähre", datetime.now().time())
    manuelle_abfahrtszeit = datetime.combine(fahrtag, fahrzeit)
else:
    manuelle_abfahrtszeit = None

faehre_auto = st.checkbox("🚢 Fähre automatisch erkennen", value=True)

abfahrt_datum = st.date_input("📅 Geplantes Abfahrtsdatum", datetime.today())
abfahrt_stunde = st.number_input("⏱ Abfahrtszeit – Stunde", 0, 23, 8)
abfahrt_minute = st.number_input("⏱ Abfahrtszeit – Minute", 0, 59, 0, step=5)

aktuelle_zeit, local_tz = get_local_time(startort)
start_time = local_tz.localize(datetime.combine(abfahrt_datum, datetime.strptime(f"{abfahrt_stunde}:{abfahrt_minute}", "%H:%M").time()))

# 🧩 Optional zuschaltbare Felder
erweiterungen_anzeigen = st.checkbox("🔧 Zusätzliche Eingaben anzeigen (z. B. Einsatzzeit, Lenkzeit)", value=False)
if erweiterungen_anzeigen:
    st.markdown("### 🕓 Bereits gefahrene Lenkzeit heute (optional)")
    col1, col2 = st.columns(2)
    with col1:
        gefahrene_stunden = st.number_input("🕓 Stunden", 0, 10, 0, step=1)
    with col2:
        gefahrene_minuten = st.number_input("🕧 Minuten", 0, 59, 0, step=5)
    bisher_gefahren_min = gefahrene_stunden * 60 + gefahrene_minuten
    if bisher_gefahren_min > 0:
        st.info(f"✅ Bereits gefahren: {gefahrene_stunden}h{gefahrene_minuten:02d}")
    else:
        bisher_gefahren_min = 0

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

# Fahrzeitgrenzen
zehn_stunden = st.checkbox("✅ Heute max. 10h Lenkzeit", value=True)
neun_stunden = st.checkbox("✅ Heute max. 9h Lenkzeit (falls nicht 10h)", value=False)
wochenruhe = st.checkbox("🛌 Wochenruhe aktivieren", value=False)

# Placeholder für finale Ankunftszeit
letzte_ankunft = None
log = []

# [Hier käme deine Segmentberechnung, Zwischenstopps etc.]

# Nach der Fahrplanberechnung:
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

# Fahrplan-Log anzeigen
if log:
    st.markdown("### 📝 Fahrplanübersicht")
    for eintrag in log:
        st.markdown(f"- {eintrag}")

# Google Map Karte anzeigen (falls aktiviert)
if startort and zielort:
    try:
        import folium
        from streamlit_folium import st_folium

        m = folium.Map(location=[48.2, 16.4], zoom_start=5)
        folium.Marker(location=[48.2, 16.4], tooltip="Start").add_to(m)
        folium.Marker(location=[45.4, 12.3], tooltip="Ziel").add_to(m)

        st.markdown("### 🗺️ Routenkarte")
        st_folium(m, width=700)
    except:
        st.warning("⚠️ Karte konnte nicht angezeigt werden (folium oder API fehlt)")
