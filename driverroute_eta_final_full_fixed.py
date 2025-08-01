
import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time
import os

st.set_page_config(page_title="DriverRoute ETA – mit Fähren", layout="centered")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def get_place_info(ort):
    if not ort:
        return "❌ Ungültiger Ort"
    adresse = str(ort)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(adresse)}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            place = data["results"][0]
            components = place.get("address_components", [])
            formatted = ", ".join(c["long_name"] for c in components if "political" in c["types"])
            return f"📍 {formatted}"
        else:
            return f"⚠️ Geocoding-Fehler: {data['status']}"
    return "❌ Fehler bei der Anfrage"

st.title("Zwischenstopp-Test")

if "zwischenstopps" not in st.session_state:
    st.session_state.zwischenstopps = []

st.session_state.zwischenstopps.append("Bergen, Norway")
for i in range(len(st.session_state.zwischenstopps)):
    st.caption(get_place_info(st.session_state.zwischenstopps[i]))
