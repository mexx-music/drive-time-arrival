import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# -------------------------------
# OpenCage API-Key (nur einsetzen)
OPENCAGE_API_KEY = "d338be0be2d34c9697b70cbfb9b2383d"
# -------------------------------

st.set_page_config(page_title="DriverRoute Pro", layout="wide")

st.title("🚛 DriverRoute Pro – Manuelle Ortseingabe mit Karte")

# Ortssuche
def geocode_place(place_name):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place_name}&key={OPENCAGE_API_KEY}&limit=1&no_annotations=1&language=de"
    response = requests.get(url)
    if response.status_code == 200 and response.json()["results"]:
        result = response.json()["results"][0]
        return {
            "name": result["formatted"],
            "lat": result["geometry"]["lat"],
            "lon": result["geometry"]["lng"]
        }
    return None

# Eingabe-Felder
start_input = st.text_input("🟢 Startort", placeholder="z. B. Volos, Griechenland")
waypoints_input = st.text_area("🟡 Zwischenstopps (ein Ort pro Zeile)", placeholder="Kulata\nSofia\nCalafat\nNadlac")
end_input = st.text_input("🔴 Zielort", placeholder="z. B. Saarlouis, Deutschland")

if st.button("📍 Orte auf Karte anzeigen"):
    # Verarbeitung der Orte
    all_places = []
    for raw_place in [start_input] + waypoints_input.split("\n") + [end_input]:
        place = raw_place.strip()
        if place:
            location = geocode_place(place)
            if location:
                all_places.append(location)
            else:
                st.warning(f"Ort nicht gefunden: {place}")
    
    # Karte anzeigen, wenn alles okay
    if all_places:
        # Initialisiere Karte bei erstem Ort
        m = folium.Map(location=[all_places[0]["lat"], all_places[0]["lon"]], zoom_start=6)
        
        # Marker & Linie
        coords = []
        for idx, loc in enumerate(all_places):
            popup_text = f"{idx+1}. {loc['name']}"
            folium.Marker(location=[loc["lat"], loc["lon"]], popup=popup_text).add_to(m)
            coords.append([loc["lat"], loc["lon"]])
        
        folium.PolyLine(coords, color="blue", weight=4.5, opacity=0.7).add_to(m)
        st_folium(m, width=900, height=500)
