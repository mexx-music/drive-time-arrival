import streamlit as st
import requests

# Funktionierende API-Keys
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "5b3ce3597851110001cf6248986f9fdc37b4a50d80edbfb889e"

def geocode_location(place):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place}&key={OPENCAGE_API_KEY}&limit=1"
    res = requests.get(url)
    data = res.json()
    if data["results"]:
        coords = data["results"][0]["geometry"]
        return [coords["lng"], coords["lat"]]
    return None

def calculate_route(coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": coords, "instructions": False}
    res = requests.post(url, headers=headers, json=body)
    return res.json() if res.status_code == 200 else None

# UI
st.set_page_config(page_title="Test: Köln → Nürnberg", layout="centered")
st.title("🧪 ORS Kurztest")
st.markdown("Test: Route von Köln nach Nürnberg mit funktionierendem API-Key.")

if st.button("➡️ Route starten"):
    with st.spinner("📍 Lade Koordinaten..."):
        start = geocode_location("Köln")
        ziel = geocode_location("Nürnberg")

        if not start or not ziel:
            st.error("❌ Ort nicht gefunden.")
        else:
            coords = [start, ziel]
            st.write("📍 Koordinaten:", coords)
            route = calculate_route(coords)

            if route:
                summary = route["features"][0]["properties"]["summary"]
                km = round(summary["distance"] / 1000, 1)
                std = round(summary["duration"] / 3600, 1)
                st.success(f"🛣️ {km} km – ⏱️ {std} Stunden")
                st.map({
                    "lat": [start[1], ziel[1]],
                    "lon": [start[0], ziel[0]]
                })
            else:
                st.error("❌ Route konnte nicht berechnet werden (ORS-Fehler).")
