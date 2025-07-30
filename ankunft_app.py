import streamlit as st
import datetime
import urllib.parse

st.set_page_config(page_title="DriverTime Arrival", layout="centered")

st.title("🛣️ DriverTime Arrival")

# Eingabefelder
startort = st.text_input("📍 Startort", "Volos")
zielort = st.text_input("🏁 Zielort", "Saarlouis")
abfahrtszeit = st.time_input("🕓 Abfahrtszeit", datetime.datetime.now().time())

st.markdown("### 🕰️ Verbleibende Lenkzeit")
stunden = st.number_input("Stunden", min_value=0, max_value=9, value=4, step=1)
minuten = st.number_input("Minuten", min_value=0, max_value=59, value=30, step=1)

# Berechnung
if st.button("🔍 Ankunftszeit berechnen & Karte anzeigen"):
    abfahrt = datetime.datetime.combine(datetime.date.today(), abfahrtszeit)
    gesamtminuten = int(stunden) * 60 + int(minuten)
    ankunft = abfahrt + datetime.timedelta(minutes=gesamtminuten)

    st.markdown("### ✅ Ergebnis")
    st.success(f"Voraussichtliche Ankunft bei voller Ausnutzung der Lenkzeit: **{ankunft.strftime('%H:%M Uhr')}**")

    # Google Maps Vorschau
    st.markdown("### 🌍 Google Maps Vorschau")

    # Key hier einfügen
    google_maps_key = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

    # Eingabe auf URL-Format bringen
    start_encoded = urllib.parse.quote(startort)
    ziel_encoded = urllib.parse.quote(zielort)

    iframe_code = f'''
    <iframe width="100%" height="450" style="border:0"
    loading="lazy" allowfullscreen
    src="https://www.google.com/maps/embed/v1/directions?key={google_maps_key}&origin={start_encoded}&destination={ziel_encoded}">
    </iframe>
    '''

    st.components.v1.html(iframe_code, height=450)
