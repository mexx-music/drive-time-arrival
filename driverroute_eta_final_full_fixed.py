
import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="API-Diagnose", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

st.title("🔍 Diagnose: Google Geocoding API")

ort = st.text_input("📍 Ort eingeben", "Volos, Griechenland")

if st.button("🔎 Test starten"):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(ort)}&key={GOOGLE_API_KEY}"
    st.write("📤 Anfrage-URL:", url)

    try:
        response = requests.get(url)
        st.write("📥 Statuscode:", response.status_code)
        data = response.json()
        st.write("📄 Antwort (gekürzt):", data.get("status"), data.get("results")[0] if data.get("results") else "Keine Ergebnisse")
    except Exception as e:
        st.error(f"❌ Fehler bei Anfrage: {e}")
