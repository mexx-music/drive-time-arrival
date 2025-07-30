import streamlit as st
import requests

# --- API Keys ---
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

# --- App Layout ---
st.set_page_config(page_title="DriverRoute Live", layout="centered")
st.title("🚛 DriverRoute Live – Ankunftszeit-Tool")

st.markdown("Gib Start- und Zielort ein – Zwischenstopps optional. Die Route wird über OpenRouteService berechnet.")

# --- Ortssuche (OpenCage) ---
def geocode_location(place):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place}&key={OPENCAGE_API_KEY}&limit=1"
    res = requests.get(url)
    data = res.json()
    if data["results"]:
        loc = data["results"][0]["geometry"]
        return loc["lat"], loc["lng"]
    return None, None

# --- Routenberechnung (ORS) ---
def calculate_route(start_coords, end_coords, waypoints=[]):
    coordinates = [start_coords] + waypoints + [end_coords]
    url = "https://api.openrouteservice.org/v2/directions/driving-hgv"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": coordinates, "instructions": False}
    r = requests.post(url, headers=headers, json=body)
    if r.status_code == 200:
        return r.json()
    return None

# --- Eingabe: Start & Ziel ---
start = st.text_input("Startort")
ziel = st.text_input("Zielort")

# --- Eingabe: Zwischenstopps ---
anzahl_stopps = st.number_input("Wie viele Zwischenstopps?", min_value=0, max_value=10, step=1)
zwischenstopps = [st.text_input(f"Zwischenstopp {i+1}") for i in range(anzahl_stopps)]

# --- Button ---
if st.button("🧭 Route berechnen und anzeigen"):
    if not start or not ziel:
        st.error("❗ Bitte Start- und Zielort eingeben.")
    else:
        with st.spinner("🔎 Suche nach Koordinaten..."):
            lat_start, lon_start = geocode_location(start)
            lat_ziel, lon_ziel = geocode_location(ziel)
            waypoints = []
            for stop in zwischenstopps:
                if stop.strip():
                    lat, lon = geocode_location(stop)
                    if lat and lon:
                        waypoints.append([lon, lat])
                    else:
                        st.warning(f"⚠ Zwischenstopp nicht gefunden: {stop}")

        if None in [lat_start, lon_start, lat_ziel, lon_ziel]:
            st.error("❌ Ein Ort konnte nicht gefunden werden.")
        else:
            route = calculate_route([lon_start, lat_start], [lon_ziel, lat_ziel], waypoints)
            if route:
                summary = route["features"][0]["properties"]["summary"]
                km = round(summary["distance"] / 1000, 1)
                std = round(summary["duration"] / 3600, 1)
                st.success(f"📍 Entfernung: {km} km – ⏱️ Dauer: {std} Stunden")
                st.map({"lat": [lat_start, lat_ziel], "lon": [lon_start, lon_ziel]})
            else:
                st.error("❌ Routenberechnung fehlgeschlagen. Bitte Eingaben prüfen.")
