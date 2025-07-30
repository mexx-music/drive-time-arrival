import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="DriverRoute Multiday ETA", layout="centered")

GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

st.title("🚛 DriverRoute Multiday ETA – LKW-konform planen")

# Eingaben: Start, Ziel, Zwischenstopps
startort = st.text_input("📍 Startort", "Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < 10:
        st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    val = st.text_input(f"Zwischenstopp {i+1}", st.session_state.zwischenstopps[i], key=f"stop_{i}")
    st.session_state.zwischenstopps[i] = val

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip() != ""]

# Abfahrtszeit
st.subheader("🕒 Abfahrtszeit")
abfahrtsdatum = st.date_input("Datum", value=datetime.now().date())
abfahrtszeit = st.time_input("Uhrzeit", value=datetime.now().time())
start_time = datetime.combine(abfahrtsdatum, abfahrtszeit)

# Regel-Checkboxen
st.subheader("🔧 Gesetzliche Optionen")

zehner_tage = st.number_input("✅ Verfügbare 10-Stunden-Tage", 0, 2, value=2)
neuner_pausen = st.number_input("🌙 Verfügbare 9-Stunden-Ruhepausen", 0, 3, value=3)
tankpause = st.checkbox("⛽ Tankpause einplanen (30 min einmalig)")

# Anfrage an Google Directions API
if st.button("📦 Route analysieren & ETA berechnen"):
    if not startort or not zielort:
        st.error("Bitte Start- und Zielort eingeben.")
    else:
        start_coords = urllib.parse.quote(startort)
        ziel_coords = urllib.parse.quote(zielort)
        waypoints = "|".join([urllib.parse.quote(s) for s in zwischenstopps]) if zwischenstopps else ""
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_coords}&destination={ziel_coords}&key={GOOGLE_API_KEY}"
        if waypoints:
            url += f"&waypoints={waypoints}"

        r = requests.get(url)
        data = r.json()

        if data["status"] != "OK":
            st.error(f"Fehler: {data['status']}")
        else:
            legs = data["routes"][0]["legs"]
            total_sec = sum([leg["duration"]["value"] for leg in legs])
            total_min = total_sec // 60
            km = round(sum([leg["distance"]["value"] for leg in legs]) / 1000, 1)

            st.success(f"🛣️ Strecke: {km} km ⏱️ Gesamtfahrzeit: {total_min} min")

            # Tageslogik
            result_log = []
            remaining_minutes = total_min
            current_time = start_time
            used_10h = 0
            used_9h_rest = 0
            used_tankpause = False

            while remaining_minutes > 0:
                tag = current_time.strftime("%A")
                start_str = current_time.strftime("%H:%M Uhr")

                # Bestimme verfügbare Tageslenkzeit
                if used_10h < zehner_tage:
                    max_drive = 600
                    used_10h += 1
                    taginfo = "10h-Tag"
                else:
                    max_drive = 540
                    taginfo = "9h-Tag"

                # Wie viel kannst du heute fahren?
                gefahren = min(remaining_minutes, max_drive)

                # Pausen: alle 4.5h (270 min) → +45 min
                pflichtpausen = math.floor(gefahren / 270)
                pausenzeit = pflichtpausen * 45

                # Tankpause?
                if not used_tankpause and tankpause:
                    pausenzeit += 30
                    used_tankpause = True

                # Fahrtzeit + Pause
                etappenzeit = gefahren + pausenzeit
                ankunft = current_time + timedelta(minutes=etappenzeit)
                end_str = ankunft.strftime("%H:%M Uhr")

                # Tagesergebnis
                result_log.append(f"📆 {tag} – Start: {start_str} → {taginfo}, ⏱️ {gefahren} min Fahrt + {pausenzeit} min Pause → Ende: {end_str}")

                remaining_minutes -= gefahren

                # Ruhepause
                if used_9h_rest < neuner_pausen:
                    ruhezeit = 9 * 60
                    used_9h_rest += 1
                    ruheinfo = "9h-Ruhe"
                else:
                    ruhezeit = 11 * 60
                    ruheinfo = "11h-Ruhe"

                current_time = ankunft + timedelta(minutes=ruhezeit)
                result_log.append(f"🌙 Ruhezeit: {ruheinfo} → nächster Fahrtag ab {current_time.strftime('%H:%M Uhr')}")

            st.markdown("## 📅 Tourenplan:")
            for zeile in result_log:
                st.markdown(zeile)

            st.success(f"✅ ETA am Ziel: {current_time.strftime('%A, %H:%M Uhr')}")
