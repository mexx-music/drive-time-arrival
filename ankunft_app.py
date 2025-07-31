
import streamlit as st
from datetime import datetime, timedelta
import googlemaps
import pytz
import math

# API-Key einfügen
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Konfiguration
st.set_page_config(page_title="DriverRoute ETA", layout="centered")
st.title("📦 DriverRoute ETA – Ankunftszeit mit Lenkzeit-Regeln")

# Eingabe: Startzeit (mit 12h AM/PM Auswahl)
col1, col2 = st.columns(2)
with col1:
    start_time_input = st.time_input("Startzeit", value=datetime.now().time())
with col2:
    am_pm = st.radio("AM/PM", ["AM", "PM"], horizontal=True)
    hour = start_time_input.hour
    if am_pm == "PM" and hour < 12:
        hour += 12
    elif am_pm == "AM" and hour == 12:
        hour = 0
start_time = datetime.combine(datetime.today(), datetime.min.time()).replace(hour=hour, minute=start_time_input.minute)

# Start & Ziel
start = st.text_input("Startort", "Volos, Griechenland")
ziel = st.text_input("Zielort", "Saarlouis, Deutschland")

# Optionen
st.markdown("### Fahrzeit-Optionen")
left, right = st.columns(2)
with left:
    verf_10h = st.slider("10h-Fahrten (pro Woche)", 0, 2, 2)
with right:
    verf_9h_pause = st.slider("9h-Tagesruhe (pro Woche)", 0, 3, 3)

tankpause = st.checkbox("30min Tankpause erforderlich", value=False)
verbleibende_lenkzeit = st.slider("Verbleibende Lenkzeit heute (Minuten)", 0, 540, 300)

# Button
if st.button("📦 Route analysieren & ETA berechnen"):
    route = gmaps.directions(start, ziel, mode="driving")
    if route:
        duration = route[0]['legs'][0]['duration']['value'] / 60  # in Minuten
        polyline = route[0]['overview_polyline']['points']
        st.success(f"🕰️ Fahrzeit (Google): {int(duration)} Minuten")

        verbleibend = duration
        tagesplan = []
        aktueller_zeitpunkt = start_time
        lenkzeit_heute = verbleibende_lenkzeit
        zeitzone = pytz.timezone("Europe/Vienna")  # optional: dynamisch per Geoposition
        aktueller_zeitpunkt = zeitzone.localize(aktueller_zeitpunkt)

        while verbleibend > 0:
            if lenkzeit_heute > 0:
                fahrzeit = min(lenkzeit_heute, 540, verbleibend)
                verbleibend -= fahrzeit
                aktueller_zeitpunkt += timedelta(minutes=fahrzeit)
                tagesplan.append(("Fahrt", fahrzeit, aktueller_zeitpunkt.strftime("%a %H:%M")))
                lenkzeit_heute = 0
            else:
                if verf_10h > 0:
                    lenkzeit_heute = 600
                    verf_10h -= 1
                else:
                    lenkzeit_heute = 540
                ruhezeit = 11 if verf_9h_pause <= 0 else 9
                if verf_9h_pause > 0:
                    verf_9h_pause -= 1
                aktueller_zeitpunkt += timedelta(hours=ruhezeit)
                tagesplan.append(("Pause", ruhezeit * 60, aktueller_zeitpunkt.strftime("%a %H:%M")))

        eta = aktueller_zeitpunkt
        st.success(f"📅 ETA (mit allen Regeln): **{eta.strftime('%A, %d.%m.%Y – %H:%M Uhr')}**")

        # Kalender / Tagesübersicht
        st.markdown("### Tagesübersicht")
        for eintrag in tagesplan:
            st.write(f"🟩 {eintrag[0]}: {int(eintrag[1])} Minuten → {eintrag[2]}")

        def zeige_google_karte_mit_polyline(polyline_str):
            base_url = "https://maps.googleapis.com/maps/api/staticmap?"
            size = "640x400"
            path = f"path=enc:{polyline_str}"
            map_url = f"{base_url}size={size}&{path}&key={GOOGLE_API_KEY}"
            st.image(map_url, caption="🗺️ Route-Vorschau (echte Straßenführung)")

        zeige_google_karte_mit_polyline(polyline)
    else:
        st.error("❌ Route konnte nicht berechnet werden.")

