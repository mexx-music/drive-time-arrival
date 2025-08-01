
import streamlit as st
import time

st.set_page_config(page_title="DriverRoute ETA – Debug", layout="centered")
st.title("🔍 DriverRoute ETA – DEBUG MODE")

try:
    st.markdown("✅ App lädt korrekt – erste Elemente werden angezeigt...")
    start_time = time.time()

    # Beispielhafte Abfrage
    auswahl = st.radio("Wähle Testmodus", ["Standard", "PLZ-Check", "Fähre", "Karte"], index=0, key="debug_radio")
    st.success(f"Auswahl getroffen: {auswahl}")

    st.markdown("---")
    st.info(f"Ladezeit bisher: {round(time.time() - start_time, 2)} Sekunden")

except Exception as e:
    st.error(f"❌ Fehler beim Start: {e}")
