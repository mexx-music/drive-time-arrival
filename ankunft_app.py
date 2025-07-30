import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math

GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

st.set_page_config(page_title="DriverRoute Pro – ETA + Lenkzeit", layout="centered")
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

st.title("🚛 DriverRoute Live – Lenkzeit + ETA Vorschau")

# 🕒 Abfahrtszeit
st.subheader("🕒 Abfahrtszeit")
abfahrtsdatum = st.date_input("Datum", value=datetime.now().date())
abfahrtszeit = st.time_input("Uhrzeit", value=datetime.now().time())
abfahrt_datetime = datetime.combine(abfahrtsdatum, abfahrtszeit)

# 📍 Start und Ziel
st.subheader("📍 Start & Ziel")
startort = st.text_input("Startort", placeholder="z. B. Volos")
zielort = st.text_input("Zielort", placeholder="z. B. Saarlouis")
start_coords = urllib.parse.quote(startort) if startort else ""
ziel_coords = urllib.parse.quote(zielort) if zielort else ""

# 🛑 Zwischenstopps
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

# ⏱️ Lenkzeitoptionen
st.subheader("⏱️ Lenkzeit-Regelung")
heute_10h = st.radio("Lenkzeit heute erlaubt:", ["9 Stunden", "10 Stunden"]) == "10 Stunden"

col1, col2 = st.columns(2)
with col1:
    verbleibend_h = st.number_input("Verbleibende Lenkzeit – Stunden", 0, 10, value=4)
with col2:
    verbleibend_m = st.number_input("Verbleibende Lenkzeit – Minuten", 0, 59, value=0)

verbleibend_total_min = verbleibend_h * 60 + verbleibend_m
max_legal = 10*60 if heute_10h else 9*60
if verbleibend_total_min > max_legal:
    st.warning(f"⚠️ Du hast mehr eingegeben als heute erlaubt: Max {max_legal} min")
    verbleibend_total_min = max_legal

tankpause = st.checkbox("🛢️ Zusätzliche Tankpause einplanen (30 min)")

# 🚀 Berechnung
st.subheader("📦 Route berechnen")
if st.markdown('<div class="big-button">', unsafe_allow_html=True) or True:
    if st.button("📍 Jetzt berechnen"):
        if not start_coords or not ziel_coords:
            st.error("Start und Ziel müssen ausgefüllt sein.")
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

                fahrzeit_min = int(total_duration / 60)
                km = round(total_distance / 1000, 1)
                st.success(f"📏 Strecke: {km} km ⏱️ Reine Fahrzeit: {fahrzeit_min} Min.")

                # Pflichtpausen: alle 4,5h → 270 min → +45 min
                pflichtpausen = math.floor(fahrzeit_min / 270)
                pause_min = pflichtpausen * 45
                if tankpause:
                    pause_min += 30

                gesamt_benoetigt = fahrzeit_min + pause_min

                if gesamt_benoetigt > verbleibend_total_min:
                    st.warning(f"⚠️ Ziel nicht erreichbar heute – Du brauchst {gesamt_benoetigt} min, hast aber nur {verbleibend_total_min} min verfügbar.")
                else:
                    eta = abfahrt_datetime + timedelta(minutes=gesamt_benoetigt)
                    st.info(f"🕓 Ankunft: {eta.strftime('%A, %H:%M Uhr')} (Pausen: {pause_min} min)")

            else:
                st.error(f"Routenfehler: {data['status']}")

# 🗺️ Karte
st.subheader("🗺️ Routenkarte")
if start_coords and ziel_coords:
    embed_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={start_coords}&destination={ziel_coords}"
    if zwischenstopps:
        embed_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
    st.components.v1.iframe(embed_url, height=450)
