import streamlit as st
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import OpenCage
import googlemaps

# === API-KEYS ===
OPENCAGE_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

geolocator = OpenCage(OPENCAGE_KEY)
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

st.set_page_config(page_title="DriverRoute ETA", layout="centered")
st.title("🚛 DriverRoute ETA mit Startzeit-Auswahl")

# === ORTSEINGABEN ===
startort = st.text_input("Startort", "Volos, Griechenland")
zielort = st.text_input("Zielort", "Saarlouis, Deutschland")
zwischenziele = []

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("Zwischenstopp hinzufügen"):
    st.session_state.zwischenstopps.append("")

for i in range(len(st.session_state.zwischenstopps)):
    st.session_state.zwischenstopps[i] = st.text_input(f"Zwischenziel {i+1}", st.session_state.zwischenstopps[i])

# === AM/PM STARTZEIT-AUSWAHL ===
st.markdown("### Startzeit wählen")

ampm = st.radio("AM oder PM auswählen:", ["AM", "PM"], horizontal=True)
stunden_labels = [str(i) for i in range(1, 13)]
stunde_12 = st.selectbox("Stunde (1–12):", stunden_labels, index=7)
minuten = st.selectbox("Minuten (in 5er-Schritten):", list(range(0, 60, 5)), index=0)

# Umrechnung
stunde_int = int(stunde_12)
if ampm == "PM" and stunde_int != 12:
    stunde_24 = stunde_int + 12
elif ampm == "AM" and stunde_int == 12:
    stunde_24 = 0
else:
    stunde_24 = stunde_int

# === ROUTENBERECHNUNG ===
alle_orte = [startort] + st.session_state.zwischenstopps + [zielort]

try:
    route = gmaps.directions(alle_orte[0], alle_orte[-1], waypoints=alle_orte[1:-1], mode="driving")
    if route:
        dauer_secs = route[0]['legs'][0]['duration']['value']
        dauer = timedelta(seconds=dauer_secs)

        # Zeit in lokaler Zeitzone des Startorts
        start_zeit = datetime.now().replace(hour=stunde_24, minute=minuten, second=0, microsecond=0)
        arrival_time = start_zeit + dauer

        st.success(f"🔁 Strecke: {round(route[0]['legs'][0]['distance']['value']/1000,1)} km")
        st.success(f"🕒 Ankunftszeit: {arrival_time.strftime('%H:%M')} Uhr")
    else:
        st.error("❌ Route konnte nicht berechnet werden.")
except Exception as e:
    st.error(f"Fehler bei der Routenberechnung: {e}")
