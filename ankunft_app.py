import streamlit as st
import requests

# API Keys
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

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

# Streamlit UI
st.set_page_config(page_title="DriverRoute Test – Deutschland extra", layout="centered")
st.title("🚛 DriverRoute Test")
st.markdown("Testet Route von Volos bis Köln – mit Etappen durch Deutschland.")

if st.button("🧭 Route mit Köln & Nürnberg berechnen"):
    with st.spinner("📍 Geokodierung..."):
        orte = ["Volos", "Kulata", "Nadlac", "Wien", "Nürnberg", "Saarlouis", "Köln"]
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
            km = round(summary["distance"] / 1000, 1)
            std = round(summary["duration"] / 3600, 1)
            st.success(f"🛣️ Gesamt: {km} km – ⏱️ {std} Stunden")
            st.map({
                "lat": [koordinaten[0][1], koordinaten[-1][1]],
                "lon": [koordinaten[0][0], koordinaten[-1][0]]
            })
        else:
            st.error("❌ Route konnte nicht berechnet werden (ORS-Fehler).")
