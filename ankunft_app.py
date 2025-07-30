import streamlit as st
import urllib.parse

st.set_page_config(page_title="DriverRoute – Google Maps Version", layout="centered")
st.title("🚛 DriverRoute – Google Maps Fallback")

st.markdown("Diese Version funktioniert ohne API-Key und öffnet direkt Google Maps – ideal für iPad & Mobilgeräte.")

# Eingabefelder
start = st.text_input("Startort", "Köln")
ziel = st.text_input("Zielort", "Nürnberg")
etappen = st.text_area("Zwischenstopps (ein Ort pro Zeile)", "Würzburg\nSaarlouis")

# Button
if st.button("🗺️ Route in Google Maps öffnen"):
    waypoints = [line.strip() for line in etappen.splitlines() if line.strip()]
    url_base = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": start,
        "destination": ziel,
        "travelmode": "driving"
    }
    if waypoints:
        params["waypoints"] = "|".join(waypoints)

    full_url = url_base + "&" + urllib.parse.urlencode(params)

    st.success("✅ Route wurde erstellt. Unten findest du den Link:")

    st.markdown(f"""
    <a href="{full_url}" target="_blank" style="font-size: 20px; color: green; font-weight: bold;">
    📍 Route jetzt in Google Maps öffnen
    </a>
    <br><br>
    <small>💡 <b>Tipp für iPhone/iPad:</b> Lange tippen → „In neuem Tab öffnen“</small>
    """, unsafe_allow_html=True)
