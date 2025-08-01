import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – mit Fähren", layout="centered")
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# Fähren-Datenbank
FAEHREN = {
    "Patras–Ancona (Superfast)": 22,
    "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Bari (Grimaldi)": 10,
    "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9,
    "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Igoumenitsa–Ancona (Superfast)": 20,
    "Ancona–Igoumenitsa (Superfast)": 20,
    "Patras–Bari (Grimaldi)": 18,
    "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19,
    "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9,
    "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 6.5,
    "Rostock–Trelleborg (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 10,
    "Kiel–Trelleborg (TT-Line)": 10,
    "Kiel–Oslo (Color Line)": 20,
    "Oslo–Kiel (Color Line)": 20,
    "Hirtshals–Stavanger (Color Line)": 11,
    "Stavanger–Hirtshals (Color Line)": 11,
    "Hirtshals–Bergen (Color Line)": 15,
    "Bergen–Hirtshals (Color Line)": 15,
    "Gothenburg–Kiel (Stena Line)": 14,
    "Kiel–Gothenburg (Stena Line)": 14
}

def get_timezone_for_latlng(lat, lng):
    timestamp = int(time.time())
    tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={GOOGLE_API_KEY}"
    tz_data = requests.get(tz_url).json()
    return tz_data["timeZoneId"] if tz_data["status"] == "OK" else "Europe/Vienna"

def get_timezone_for_address(address):
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    geo_data = requests.get(geo_url).json()
    if geo_data["status"] == "OK":
        loc = geo_data["results"][0]["geometry"]["location"]
        return get_timezone_for_latlng(loc["lat"], loc["lng"])
    return "Europe/Vienna"

def get_local_time(address):
    tz_str = get_timezone_for_address(address)
    tz = pytz.timezone(tz_str)
    return datetime.now(tz), tz

def get_plz_info(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    resp = requests.get(url).json()
    if resp["status"] != "OK":
        return None
    components = resp["results"][0]["address_components"]
    plz = ort = land = bundesland = ""
    for comp in components:
        if "postal_code" in comp["types"]:
            plz = comp["long_name"]
        if "locality" in comp["types"] or "postal_town" in comp["types"]:
            ort = comp["long_name"]
        if "country" in comp["types"]:
            land = comp["long_name"]
        if "administrative_area_level_1" in comp["types"]:
            bundesland = comp["long_name"]
    return {"plz": plz, "ort": ort, "land": land, "bundesland": bundesland}

def show_plz_info(label, address):
    info = get_plz_info(address)
    if info:
        text = f"📍 <b>{label}:</b> {info['plz']} {info['ort']} ({info['land']})"
        if info['bundesland']:
            text += f" – {info['bundesland']}"
        st.markdown(text, unsafe_allow_html=True)
    else:
        st.warning(f"{label}: Adresse nicht gefunden oder ungültig.")

def format_minutes_to_hm(minutes):
    if minutes >= 60:
        h, m = divmod(minutes, 60)
        return f"{h}h{m}" if m > 0 else f"{h}h"
    else:
        return f"{minutes} min"

# App UI beginnt
st.title("🚛 DriverRoute ETA – mit Fähren & Wochenlenkzeit")

vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell eingeben"], index=0)
verfügbare_woche = 3360 if vorgabe == "Voll (56h)" else int(st.number_input("⏱️ Eigene Eingabe (in Stunden)", 0.0, 56.0, 36.0, 0.25) * 60)

startort = st.text_input("📍 Startort", "Volos, Griechenland")
show_plz_info("Startort", startort)

zielort = st.text_input("🏁 Zielort", "Saarlouis, Deutschland")
show_plz_info("Zielort", zielort)

# (Rest des Codes unverändert – siehe deine bestehende Version ab hier)
