import streamlit as st
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="DriverTime Arrival", layout="wide")

st.title("🚛 DriverTime Arrival – Lenkzeitbasierte Ankunftsberechnung")
st.markdown("Gib deine Abfahrtszeit, Restlenkzeit und Start/Ziel an – die App berechnet deine voraussichtliche Ankunftszeit und zeigt eine Google Maps-Vorschau.")

# Zwei Spalten: Eingabe und Kartenansicht
col1, col2 = st.columns([1, 1.5])

with col1:
    start = st.text_input("📍 Startort", "Köln")
    ziel = st.text_input("🏁 Zielort", "Nürnberg")

    abfahrt_zeit = st.time_input("🕒 Abfahrtszeit", value=datetime.now().time())

    st.markdown("### ⏱ Verbleibende Lenkzeit")
    lenk_h = st.number_input("Stunden", min_value=0, max_value=24, value=4)
    lenk_m = st.number_input("Minuten", min_value=0, max_value=59, value=30)

    anzeigen = st.button("🔍 Ankunftszeit berechnen & Karte anzeigen")

with col2:
    if anzeigen:
        # Schritt 1: Lenkzeit berechnen
        lenkzeit = timedelta(hours=lenk_h, minutes=lenk_m)
        abfahrt_dt = datetime.combine(datetime.today(), abfahrt_zeit)
        ankunft_dt = abfahrt_dt + lenkzeit
        ankunft_str = ankunft_dt.strftime("%H:%M")

        # Schritt 2: Ergebnis anzeigen
        st.subheader("📅 Ergebnis")
        st.success(f"Voraussichtliche Ankunft bei voller Ausnutzung der Lenkzeit: **{ankunft_str} Uhr**")

        # Schritt 3: Hinweis
        if lenkzeit < timedelta(hours=2):
            st.warning("⚠️ Sehr kurze Lenkzeit – realistische Ankunft eventuell später.")
        elif lenkzeit > timedelta(hours=9):
            st.error("❌ Zu lange Lenkzeit – gesetzlicher Maximalwert überschritten.")

        # Schritt 4: Google Maps Vorschau
        gmaps_base = "https://www.google.com/maps/embed/v1/directions"
        params = {
            "origin": start,
            "destination": ziel,
            "mode": "driving",
            "key": "AIzaSyDdXmJxY8pWZKZQyRx-QGm5tfP9MYsU7Z0"  # Demo-Key
        }
        gmaps_url = gmaps_base + "?" + urllib.parse.urlencode(params)
        st.markdown("### 🗺️ Google Maps Vorschau")
        st.components.v1.iframe(gmaps_url, height=500)
