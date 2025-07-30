import streamlit as st
import requests

# API Keys
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

st.set_page_config(page_title="DriverRoute Live", layout="centered")
st.title("🚛 DriverRoute Live – Ankunftszeit-Tool (PKW-Modus)")

def geocode_location(place):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place}&key={OPENCAGE_API_KEY}&limit=1"
    res = requests.get(url)
    data = res.json()
    if data["results"]:
        coords = data["results"][0]["geometry"]
        return coords["lat"], coords["lng"]
    return None, None

def calculate_route(coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"  # <-- PKW-Profil statt LKW
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": coords, "instructions": False}
    res = requests.post(url, headers=headers, json=body)
    return res.json() if res.status_code == 200 else None

# Eingaben
start = st.text_input("Startort", "Volos")
ziel = st.text_input("Zielort", "Saarlouis")
anzahl = st.number_input("Wie viele Zwischenstopps?", 0, 10, 0)
stops = [st.text_input(f"Zwischenstopp {i+1}") for i in range(anzahl)]

if st.button("🧭 Route berechnen und anzeigen"):
    with st.spinner("⏳ Suche Orte..."):
        lat_start, lon_start = geocode_location(start)
        lat_ziel, lon_ziel = geocode_location(ziel)

        if None in [lat_start, lon_start, lat_ziel, lon_ziel]:
            st.error("❌ Start oder Ziel konnte nicht gefunden werden.")
        else:
            coords = [[lon_start, lat_start]]
            for stop in stops:
                if stop.strip():
                    lat, lon = geocode_location(stop)
                    if lat and lon:
                        coords.append([lon, lat])
                    else:
                        st.warning(f"⚠ Zwischenstopp '{stop}' nicht gefunden.")
            coords.append([lon_ziel, lat_ziel])

            st.write("📍 Koordinaten:", coords)  # Debug-Zeile

            route = calculate_route(coords)
            if route:
                summary = route["features"][0]["properties"]["summary"]
                km = round(summary["distance"] / 1000, 1)
                std = round(summary["duration"] / 3600, 1)
                st.success(f"🛣️ {km} km – ⏱️ {std} Stunden")
                st.map({"lat": [lat_start, lat_ziel], "lon": [lon_start, lon_ziel]})
            else:
                st.error("❌ Route konnte nicht berechnet werden (ORS-Fehler).")
