
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Test: Uhrzeitwahl", layout="centered")

st.title("🕒 Komfortable Uhrzeitwahl (mobilfreundlich)")

# Zeitwahl mit st.time_input – ohne Spalten, ohne Fokusstörung
st.markdown("### ⏰ Wähle eine Uhrzeit (Zeiger-Uhr bei Touchgeräten):")
abfahrtszeit = st.time_input("Abfahrtszeit wählen", value=datetime.now().time(), label_visibility="collapsed")

# Ergebnis anzeigen
st.success(f"Gewählte Zeit: {abfahrtszeit.strftime('%H:%M')} Uhr")
