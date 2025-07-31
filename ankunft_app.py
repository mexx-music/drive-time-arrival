import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math

# Deine API Keys
GOOGLE_API_KEY = "DEIN_GOOGLE_API_KEY"

st.set_page_config(page_title="DriverRoute ETA", layout="wide")

# Eingabefelder
st.title("🛣️ DriverRoute ETA mit Fahrzeitlogik")

col1, col2 = st.columns(2)
with col1:
    start = st.text_input("Startort", "Volos, Griechenland")
    stops = st.text_area("Zwischenstopps (ein Ort pro Zeile)", "Sofia\nWien")
with col2:
    ziel = st.text_input("Zielort", "Saarlouis, Deutschland")
    abfahrt_zeit = st.time_input("Abfahrt (lokale Zeit)", value=datetime.now().time())

# Kästchen für 10h- und 9h-Regelungen
st.subheader("🕓 Wöchentliche Lenkzeit-Ausnahmen")
col10h, col9h = st.columns(2)
with col10h:
    zehn_stunden_fahrten = st.multiselect("✅ Verfügbare 10h-Fahrten", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"], default=["Montag", "Dienstag"])
with col9h:
    neun_stunden_pausen = st.multiselect("✅ Verfügbare 9h-Ruhepausen", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"], default=["Montag", "Dienstag", "Mittwoch"])

# Routenberechnung vorbereiten
waypoints = stops.strip().split("\n") if stops.strip() else []
route_query = f"origin={urllib.parse.quote(start)}&destination={urllib.parse.quote(ziel)}"

if waypoints:
    joined_waypoints = '|'.join([urllib.parse.quote(wp.strip()) for wp in waypoints])
    route_query += f"&waypoints={joined_waypoints}"

route_query += f"&key={GOOGLE_API_KEY}"

# Google Directions API Request
url = f"https://maps.googleapis.com/maps/api/directions/json?{route_query}&departure_time=now"
response = requests.get(url)
data = response.json()

if data["status"] == "OK":
    route = data["routes"][0]["legs"]
    gesamt_km = sum(leg["distance"]["value"] for leg in route) / 1000
    gesamt_dauer_sec = sum(leg["duration"]["value"] for leg in route)
    eta = (datetime.combine(datetime.today(), abfahrt_zeit) + timedelta(seconds=gesamt_dauer_sec)).strftime("%H:%M")

    st.success(f"🛻 Gesamtstrecke: {gesamt_km:.1f} km — 📍 ETA (ohne Pausen): {eta}")

    # Karte anzeigen
    map_url = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(start)}&destination={urllib.parse.quote(ziel)}"
    if waypoints:
        map_url += f"&waypoints={'|'.join([urllib.parse.quote(wp.strip()) for wp in waypoints])}"
    st.markdown(f"[📍 Route in Google Maps öffnen]({map_url})", unsafe_allow_html=True)

    st.components.v1.iframe(
        f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(start)}&destination={urllib.parse.quote(ziel)}&waypoints={'|'.join([urllib.parse.quote(w) for w in waypoints])}",
        height=500
    )
else:
    st.error(f"Fehler bei der Routenberechnung: {data.get('status')}")
