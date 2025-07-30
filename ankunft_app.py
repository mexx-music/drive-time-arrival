import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta

# Google API-Key einsetzen
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

st.set_page_config(page_title="DriverRoute Live", layout="centered")
st.markdown("""
    <style>
    .big-button > button {
        font-size: 1.2em;
        padding: 0.8em 1.5em;
        width: 100%;
        margin-bottom: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 6px;
    }
    .stTextInput > div > input {
        font-size: 1.1em;
        padding: 0.6em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚚 DriverRoute Live – ETA & Lenkzeit")

# 📍 Startort
st.subheader("📍 Startort")
startort = st.text_input("Startort (z. B. Wien)", placeholder="Ort oder Adresse")
start_coords = urllib.parse.quote(startort) if startort else ""

# Zielort
st.subheader("🎯 Ziel")
ziel = st.text_input("Zielort (z. B. Saarlouis)", placeholder="Ort oder Adresse")
ziel_coords = urllib.parse.quote(ziel) if ziel else ""

# Zwischenstopps
st.subheader("🛑 Zwischenstopps")
max_stops = 10
if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

if st.button("➕ Zwischenstopp hinzufügen"):
    if len(st.session_state.zwischenstopps) < max_stops:
        st.session_state.zwischenstopps.append("")
    else:
        st.warning("Maximal 10 Zwischenstopps möglich.")

for i in range(len(st.session_state.zwischenstopps)):
    value = st.text_input(f"Zwischenstopp {i+1}", value=st.session_state.zwischenstopps[i], key=f"stop_{i}")
    st.session_state.zwischenstopps[i] = value

zwischenstopps = [s for s in st.session_state.zwischenstopps if s.strip() != ""]

# Lenkzeit-Eingabe
st.subheader("⏱️ Verbleibende Lenkzeit heute")
col1, col2 = st.columns(2)
with col1:
    lenkzeit_h = st.number_input("Stunden", min_value=0, max_value=15, value=4)
with col2:
    lenkzeit_m = st.number_input("Minuten", min_value=0, max_value=59, value=0)

verbleibende_min = int(lenkzeit_h) * 60 + int(lenkzeit_m)

# Route berechnen
st.subheader("🚀 Route berechnen")
if st.markdown('<div class="big-button">', unsafe_allow_html=True) or True:
    if st.button("📍 Jetzt berechnen"):
        if not start_coords or not ziel_coords:
            st.error("Bitte Start- und Zielort eingeben.")
        else:
            waypoint_string = "|".join([urllib.parse.quote(s) for s in zwischenstopps]) if zwischenstopps else ""
            url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_coords}&destination={ziel_coords}&key={GOOGLE_API_KEY}"
            if waypoint_string:
                url += f"&waypoints={waypoint_string}"

            response = requests.get(url)
            data = response.json()

            if data["status"] == "OK":
                route = data["routes"][0]
                legs = route["legs"]

                total_distance = 0
                total_duration = 0
                for leg in legs:
                    total_distance += leg["distance"]["value"]
                    total_duration += leg["duration"]["value"]

                km = round(total_distance / 1000, 1)
                minuten = int(total_duration / 60)
                st.success(f"📏 Strecke: {km} km ⏱️ Fahrzeit: {minuten} Minuten")

                # ETA-Berechnung
                jetzt = datetime.now()
                if minuten <= verbleibende_min:
                    eta = jetzt + timedelta(minutes=minuten)
                    st.info(f"🕓 Ankunft möglich um {eta.strftime('%H:%M')} Uhr")
                else:
                    rest_differenz = minuten - verbleibende_min
                    st.warning(f"⚠️ Lenkzeit reicht nicht – mindestens {rest_differenz} Minuten zu viel")
            else:
                st.error(f"Fehler bei der Routenberechnung: {data['status']}")

# Karte anzeigen
st.subheader("🗺️ Routenkarte")
if start_coords and ziel_coords:
    embed_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={start_coords}&destination={ziel_coords}"
    if zwischenstopps:
        embed_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"

    st.components.v1.iframe(embed_url, height=450)

    # Optional: Link zu Google Maps
    if zwischenstopps:
        ext_url = f"https://www.google.com/maps/dir/?api=1&origin={start_coords}&destination={ziel_coords}"
        ext_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
        st.markdown(f"[🌐 Google Maps extern öffnen]({ext_url})", unsafe_allow_html=True)
        st.markdown("⬅️ [Zurück zur App](#)", unsafe_allow_html=True)
