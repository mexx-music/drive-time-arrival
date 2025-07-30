import streamlit as st
import requests

# API-Keys
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

# --- Geocoding (OpenCage) ---
def geocode_location(place):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place}&key={OPENCAGE_API_KEY}&limit=1"
    res = requests.get(url)
    data = res.json()
    if data["results"]:
        coords = data["results"][0]["geometry"]
        return [coords["lng"], coords["lat"]]
    return None

# --- Routenberechnung (ORS) ---
def calculate_route(coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": coords, "instructions": False}
    res = requests.post(url, headers=headers, json=body)
    return res.json() if res.status_code == 200 else None

# --- Streamlit UI ---
st.set_page_config(page_title="DriverRoute Live – Etappenroute", layout="centered")
st.title("🚛 DriverRoute Live")
st.markdown("Berechne deine Etappenroute von Volos nach Saarlouis mit festen Zwischenstopps.")

if st.button("🧭 Volos → Saarlouis mit Etappen laden"):
    with st.spinner("Suche Koordinaten für die Route..."):
        orte = ["Volos", "Kulata", "Calafat", "Nadlac", "Wien", "Nürnberg", "Saarlouis"]
        koordinaten = []
        for ort in orte:
            coords = geocode_location(ort)
            if coords:
                koordinaten.append(coords)
            else:
                st.error(f"❌ Ort nicht gefunden: {ort}")
                st.stop()

        st.write("📍 Koordinaten:", koordinaten)

        route = calculate_route(koordinaten)
        if route:
            summary = route["features"][0]["properties"]["summary"]
            distanz_km = round(summary["distance"] / 1000, 1)
            dauer_std = round(summary["duration"] / 3600, 1)
            st.success(f"🛣️ Entfernung: {distanz_km} km – ⏱️ Fahrzeit: {dauer_std} Stunden")

            # Kartenansicht Start und Ziel
            st.map({
                "lat": [koordinaten[0][1], koordinaten[-1][1]],
                "lon": [koordinaten[0][0], koordinaten[-1][0]]
            })
        else:
            st.error("❌ Route konnte nicht berechnet werden. Bitte später erneut versuchen.")
