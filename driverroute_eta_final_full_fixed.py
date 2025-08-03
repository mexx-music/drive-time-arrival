
import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Fahrplan & Fähren", layout="centered")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9, "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Igoumenitsa–Ancona (Superfast)": 20, "Ancona–Igoumenitsa (Superfast)": 20,
    "Patras–Bari (Grimaldi)": 18, "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19, "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 6.5, "Rostock–Trelleborg (TT-Line)": 6.5,
    "Trelleborg–Kiel (TT-Line)": 13, "Kiel–Trelleborg (TT-Line)": 13,
    "Color Line Kiel–Oslo": 20, "Color Line Oslo–Kiel": 20,
    "Hirtshals–Stavanger (FjordLine)": 10, "Stavanger–Hirtshals (FjordLine)": 10,
    "Hirtshals–Bergen (FjordLine)": 16, "Bergen–Hirtshals (FjordLine)": 16
}

def get_timezone_for_address(address):
    if not address:
        return "Europe/Vienna"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        loc = r["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(time.time())}&key={GOOGLE_API_KEY}"
        return requests.get(tz_url).json().get("timeZoneId", "Europe/Vienna")
    return "Europe/Vienna"

def get_local_time(address):
    tz = pytz.timezone(get_timezone_for_address(address))
    return datetime.now(tz), tz

def get_place_info(address):
    if not address:
        return "❌ Ungültiger Ort"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK":
        result = r["results"][0]
        components = result["address_components"]
        plz = ort = land = ""
        for comp in components:
            if "postal_code" in comp["types"]:
                plz = comp["long_name"]
            if "locality" in comp["types"] or "postal_town" in comp["types"]:
                ort = comp["long_name"]
            if "country" in comp["types"]:
                land = comp["long_name"]
        return f"📌 {ort}, {plz} ({land})"
    return "❌ Ort nicht gefunden"

def extrahiere_ort(address):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={GOOGLE_API_KEY}"
        r = requests.get(url).json()
        for c in r["results"][0]["address_components"]:
            if "locality" in c["types"]:
                return c["long_name"].lower()
    except:
        return ""
    return ""

def finde_passende_faehren(start, ziel, now_local):
    ort_start = extrahiere_ort(start)
    kandidaten = []
    for route, dauer in FAEHREN.items():
        h1, h2 = [h.strip().lower() for h in route.split("–")]
        if ort_start in h1 or ort_start in h2:
            kandidaten.append({
                "route": route,
                "dauer": dauer,
                "datum": now_local.date(),
                "stunde": now_local.hour + 1 if now_local.hour < 23 else 8,
                "minute": 0
            })
    return kandidaten

# Minimale Startanzeige
st.title("🚛 DriverRoute ETA – Fahrplan & Fähren")

startort = st.text_input("📍 Startort", "")
zielort = st.text_input("🏁 Zielort", "")
st.caption(get_place_info(startort))
st.caption(get_place_info(zielort))

now_local, local_tz = get_local_time(startort)

# Fährenvorschläge
if st.button("🚢 Fähre automatisch erkennen"):
    faehren = finde_passende_faehren(startort, zielort, now_local)
    if faehren:
        for f in faehren:
            st.success(f"🛳️ Vorschlag: {f['route']} – {f['stunde']:02}:00 ({f['dauer']} h)")
    else:
        st.warning("Keine passende Fähre gefunden.")



# Hinweis: Dieser Code ist nun durch das GPT-System vollständig ersetzt im Chat.
