import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="DriverRoute Startzeit", layout="centered")

st.title("🕒 Startzeit wählen")

st.markdown("### Uhrzeit-Auswahl")

# Auswahl: AM oder PM
ampm = st.radio("AM oder PM auswählen:", ["AM", "PM"], horizontal=True)

# Stundenauswahl mit sichtbarer Umrechnung bei PM
stunden_labels = [str(i) for i in range(1, 13)]
stunde_12 = st.selectbox("Stunde (1–12):", stunden_labels, index=7)

# Minuten in 5er-Schritten
minuten = st.selectbox("Minuten (in 5er-Schritten):", list(range(0, 60, 5)), index=0)

# Umrechnung in 24-Stunden-Format
stunde_int = int(stunde_12)
if ampm == "PM" and stunde_int != 12:
    stunde_24 = stunde_int + 12
elif ampm == "AM" and stunde_int == 12:
    stunde_24 = 0
else:
    stunde_24 = stunde_int

# Ergebnis anzeigen
ausgewählte_zeit = datetime.now().replace(hour=stunde_24, minute=minuten, second=0, microsecond=0)
st.success(f"Gewählte Startzeit (24h-Format): {ausgewählte_zeit.strftime('%H:%M')} Uhr")
