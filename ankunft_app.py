import streamlit as st
import openrouteservice
from openrouteservice import convert
import folium
from streamlit_folium import st_folium

# OpenRouteService API-Key (bereits korrekt)
ORS_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=ORS_KEY)

st.set_page_config(layout="wide")
st.title("🚛 DriverRoute Live")
st.markdown("### Internationale LKW-Route mit echten Straßen und Zwischenstopps")

# 🔹 Eingabefelder für Start, Ziel und dynamische Zwischenstopps
start = st.text_input("Startort", placeholder="z. B. Volos, Griechenland", key="start", label_visibility="visible")
ziel = st.text_input("Zielort", placeholder="z. B. Saarlouis, Deutschland", key="ziel", label_visibility="visible")

# 🔹 Etappen dynamisch hinzufügen
st.markdown("#### Zwischenstopps hinzufügen")
stopps = []
anzahl_stopps = st.number_input("Wie viele Zwischenstopps?", min_value=0, max_value=10, value=0, step=1)
for i in range(anzahl_stopps):
    stop = st.text_input(f"Stopp {i+1}", placeholder="z. B. Calafat, Rumänien", key=f"stopp_{i}")
    stopps.append(stop)

if st.button("🗺 Route berechnen und anzeigen"):
    try:
        # 🔹 Geocoding aller Punkte
        def geocode(ort):
            result = client.pelias_search(text=ort)
            coords = result['features'][0]['geometry']['coordinates']
            return coords

        route_punkte = [geocode(start)] + [geocode(s) for s in stopps if s.strip()] + [geocode(ziel)]

        # 🔹 Routing mit OpenRouteService (echte Straßen)
        route = client.directions(
            coordinates=route_punkte,
            profile='driving-hgv',
            format='geojson'
        )

        # 🔹 Karte erstellen
        center = route_punkte[len(route_punkte)//2]
        m = folium.Map(location=[center[1], center[0]], zoom_start=6)

        # Marker hinzufügen
        folium.Marker(location=[route_punkte[0][1], route_punkte[0][0]],
                      popup="Start", icon=folium.Icon(color='green')).add_to(m)
        for i, coord in enumerate(route_punkte[1:-1]):
            folium.Marker(location=[coord[1], coord[0]],
                          popup=f"Stopp {i+1}", icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker(location=[route_punkte[-1][1], route_punkte[-1][0]],
                      popup="Ziel", icon=folium.Icon(color='red')).add_to(m)

        # Route zeichnen
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in route['features'][0]['geometry']['coordinates']],
            color='blue', weight=4
        ).add_to(m)

        st_folium(m, width=700, height=500)

        # 🔹 Fahrzeit und Entfernung anzeigen
        dauer_sec = route['features'][0]['properties']['summary']['duration']
        dist_km = route['features'][0]['properties']['summary']['distance'] / 1000
        st.success(f"Gesamtdistanz: **{dist_km:.1f} km**, Fahrzeit: **{dauer_sec/3600:.2f} Stunden**")

    except Exception as e:
        st.error(f"Fehler bei der Routenberechnung: {e}")

# 🔽 Scroll-Button (Mobilfreundlich)
st.markdown("""
    <style>
    #scroll-btn {
        position: fixed;
        right: 10px;
        bottom: 80px;
        background-color: #ff4b4b;
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        font-size: 18px;
        z-index: 9999;
        cursor: pointer;
    }
    </style>
    <div id="scroll-btn" onclick="window.scrollTo({ top: 0, behavior: 'smooth' })">
        🔼 Zurück nach oben
    </div>
""", unsafe_allow_html=True)
