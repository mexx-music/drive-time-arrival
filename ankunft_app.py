import streamlit as st
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Zeitwahl AM/PM", layout="centered")
st.title("🕓 Zeitwahl mit sichtbarem Wechsel bei PM")

# AM/PM Auswahl
ampm = st.radio("Zeitauswahl", ["AM", "PM"], horizontal=True)

# Stundenanzeige je nach AM/PM
stunden_anzeige = list(range(1, 13)) if ampm == "AM" else list(range(13, 24))
stunde = st.selectbox("Stunde", stunden_anzeige, index=stunden_anzeige.index(13) if ampm == "PM" else 0)

# Minutenanzeige
minute = st.selectbox("Minute", list(range(0, 60)), index=0)

# Ergebnisanzeige
zeit = f"{stunde:02d}:{minute:02d}"
st.success(f"Ausgewählte Uhrzeit: {zeit}")
