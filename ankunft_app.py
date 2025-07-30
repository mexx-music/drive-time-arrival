import streamlit as st
import urllib.parse

st.set_page_config(page_title="DriverRoute Fallback – Google Maps", layout="centered")
st.title("🚛 DriverRoute (Google Maps Fallback)")
st.markdown("Diese Version verwendet Google Maps direkt – ohne API-Key, sofort einsatzbereit.")

# Eingabefelder
start = st.text_input("Startort", "Köln")
ziel = st.text_input("Zielort", "Nürnberg")
etappen = st.text_area("Zwischenstopps (ein Ort pro Zeile)", "Würzburg\nSaarlouis")

# Button
if st.button("🗺️ Google Maps Route öffnen"):
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
    st.success("✅ Route erstellt – klicke unten, um sie in Google Maps zu öffnen:")
    st.markdown(f"[📍 Route in Google Maps öffnen]({full_url})", unsafe_allow_html=True)
