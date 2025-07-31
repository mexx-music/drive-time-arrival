import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import math
import pytz

st.set_page_config(page_title="DriverRoute ETA – Wochenstunden", layout="centered")

def divmod(minutes, divisor):
    return divmod(int(minutes), divisor)

st.title("🚛 DriverRoute ETA – Wochenlenkzeit")

startort = st.text_input("Startort")
zielort = st.text_input("Zielort")
abfahrt = st.time_input("Abfahrtszeit", value=datetime.now().time())
datum = st.date_input("Startdatum", value=datetime.now().date())

verfügbare_woche = st.number_input("Verfügbare Wochenlenkzeit (in Minuten)", min_value=0, max_value=3780, value=2700, step=15)

zehner_fahrten = st.multiselect("✅ Verfügbare 10h-Fahrten (max. 2)", ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"])
neuner_ruhen = st.multiselect("🟦 Verfügbare 9h-Ruhepausen (max. 3)", ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"])

dauer_gesamt = st.number_input("Gesamte Fahrtzeit (in Minuten)", min_value=1, max_value=6000, value=1200)
pausen = st.number_input("Gesamtpausenzeit (in Minuten)", min_value=0, max_value=1000, value=135)

total_min = dauer_gesamt + pausen
verbl_10h = max(0, 2 - len(zehner_fahrten))
verbl_9h = max(0, 3 - len(neuner_ruhen))
st.info(f"🧾 Noch übrig: {verbl_10h}× 10h-Fahrt, {verbl_9h}× 9h-Ruhepause")

verbleibend_min = max(0, verfügbare_woche - total_min)
h, m = divmod(verbleibend_min, 60)

if verfügbare_woche - total_min < 0:
    überschuss = abs(verfügbare_woche - total_min)
    h_m, m_m = divmod(überschuss, 60)
    st.warning(f"⚠️ Achtung: Wochenlenkzeit überschritten um {h_m} h {m_m} min!")

st.info(f"🧭 Verbleibende Wochenlenkzeit: {h} h {m} min")

# ETA-Anzeige
local_tz = pytz.timezone("Europe/Vienna")
start_datetime = local_tz.localize(datetime.combine(datum, abfahrt))
ankunft = start_datetime + timedelta(minutes=total_min)

st.markdown(f"""
<h2 style='text-align: center; color: green;'>
✅ <u>Geplante Ankunft:</u><br>
<b>🕓 {ankunft.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>
({local_tz.zone})
</h2>
""", unsafe_allow_html=True)

# Kartenanzeige
GOOGLE_API_KEY = "DEIN_KEY_HIER"
map_url = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={urllib.parse.quote(startort)}&destination={urllib.parse.quote(zielort)}"

st.markdown("### 🗺️ Routenkarte:")
st.components.v1.iframe(map_url, height=500)
