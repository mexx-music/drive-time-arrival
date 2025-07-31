import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import time
import pytz

st.set_page_config(page_title="DriverRoute ETA – Zeitzonen korrekt", layout="centered")
GOOGLE_API_KEY = "DEIN_GOOGLE_KEY_HIER"  # ❗️Eintragen

# 👉 Zeitzone per Koordinaten holen
def get_timezone_for_latlng(lat, lng):
    timestamp = int(time.time())
    url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    return r["timeZoneId"] if r["status"] == "OK" else "Europe/Vienna"

# 👉 Koordinaten per Adresse holen
def get_latlng_for_address(address):
    encoded = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        location = r["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        return None, None

# 🎯 Zieladresse eingeben
zielort = st.text_input("Zielort eingeben (z. B. Volos, Griechenland):", "Volos, Griechenland")

if zielort:
    lat, lng = get_latlng_for_address(zielort)
    if lat and lng:
        timezone_id = get_timezone_for_latlng(lat, lng)
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        local_time = now_utc.astimezone(pytz.timezone(timezone_id))
        st.success(f"🕒 Aktuelle Zielzeit in {zielort}: {local_time.strftime('%A, %d.%m.%Y – %H:%M')} ({timezone_id})")
    else:
        st.error("Zielort konnte nicht gefunden werden.")
