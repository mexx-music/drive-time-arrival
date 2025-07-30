import streamlit as st
import requests
import urllib.parse

# Google API-Key einfügen
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

st.set_page_config(page_title="DriverRoute Live", layout="centered")
st.title("🚚 DriverRoute Live – Ankunftszeit mit Zwischenstopps")

# 📍 Startort manuell
st.subheader("📍 Startort eingeben")
startort = st.text_input("Startort (z. B. Volos, Griechenland)", placeholder="Ort oder Adresse")
start_coords = urllib.parse.quote(startort) if startort else ""

# 🛣️ Ziel und Zwischenstopps
st.subheader("🧭 Ziel und Route")

ziel = st.text_input("Zielort", placeholder="z. B. Saarlouis, Deutschland", key="ziel")

zwischenstopps = []
max_stops = 10
if 'stoppanzahl' not in st.session_state:
    st.session_state.stoppanzahl = 0

if st.button("➕ Zwischenstopp hinzufügen"):
    if st.session_state.stoppanzahl < max_stops:
        st.session_state.stoppanzahl += 1
    else:
        st.warning("Maximal 10 Zwischenstopps möglich.")

for i in range(st.session_state.stoppanzahl):
    stop = st.text_input(f"Zwischenstopp {i+1}", key=f"stop_{i}")
    zwischenstopps.append(stop)

# 🚀 Route berechnen
if st.button("🚀 Route berechnen"):
    if not start_coords or not ziel:
        st.error("Bitte Start- und Zielort eingeben.")
    else:
        waypoints = "|".join([urllib.parse.quote(s) for s in zwischenstopps]) if zwischenstopps else ""
        destination = urllib.parse.quote(ziel)

        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_coords}&destination={destination}&key={GOOGLE_API_KEY}"
        if waypoints:
            url += f"&waypoints={waypoints}"

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
            st.success(f"📏 Strecke: {km} km\n⏱️ Fahrzeit: {minuten} Minuten")
        else:
            st.error(f"Fehler bei der Routenberechnung: {data['status']}")

# 🗺️ Karte einbetten
st.subheader("🗺️ Routenkarte")

if start_coords and ziel:
    embed_base = "https://www.google.com/maps/embed/v1/directions"
    map_url = f"{embed_base}?key={GOOGLE_API_KEY}&origin={start_coords}&destination={urllib.parse.quote(ziel)}"
    if zwischenstopps:
        map_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"

    st.components.v1.iframe(map_url, height=450)

    # Link zu Google Maps (extern)
    if zwischenstopps:
        ext_url = f"https://www.google.com/maps/dir/?api=1&origin={start_coords}&destination={urllib.parse.quote(ziel)}"
        ext_url += f"&waypoints={'|'.join([urllib.parse.quote(s) for s in zwischenstopps])}"
        st.markdown(f"[🌐 Google Maps extern öffnen]({ext_url})", unsafe_allow_html=True)
        st.markdown("⬅️ [Zurück zur App](#)", unsafe_allow_html=True)
