import streamlit as st
import datetime
import urllib.parse

st.set_page_config(page_title="DriverTime Arrival – Pro Version", layout="centered")

st.title("🚛 DriverTime Arrival – Pro Version mit Etappen")

# Start- und Zielort (größere Eingabefelder)
startort = st.text_input("📍 Startort", "Volos", key="startort", placeholder="z. B. Volos, Griechenland")
zielort = st.text_input("🏁 Zielort", "Saarlouis", key="zielort", placeholder="z. B. Saarlouis, Deutschland")

# Dynamisch erweiterbare Zwischenstopps
st.markdown("### ➕ Zwischenstopps (optional)")
st.session_state.stops = st.session_state.get("stops", [""])

def add_stop():
    st.session_state.stops.append("")

if st.button("➕ Zwischenstopp hinzufügen"):
    add_stop()

for i, stop in enumerate(st.session_state.stops):
    st.session_state.stops[i] = st.text_input(f"➡️ Zwischenziel {i+1}", value=stop, key=f"stop_{i}")

# Abfahrtszeit und Lenkzeit
abfahrtszeit = st.time_input("🕒 Abfahrtszeit", datetime.datetime.now().time())
stunden = st.number_input("🕓 Verbleibende Lenkzeit – Stunden", 0, 9, 4)
minuten = st.number_input("🕔 Minuten", 0, 59, 30)

# Berechnung
if st.button("🔍 Ankunft berechnen & Route anzeigen"):
    abfahrt = datetime.datetime.combine(datetime.date.today(), abfahrtszeit)
    lenkzeit = datetime.timedelta(hours=int(stunden), minutes=int(minuten))
    ankunft = abfahrt + lenkzeit
    st.success(f"🕒 Voraussichtliche Ankunft bei voller Lenkzeit: **{ankunft.strftime('%H:%M Uhr')}**")

    # Google Maps Vorschau (ohne Zwischenziele – technisch nicht unterstützt)
    google_maps_key = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"
    base_url = "https://www.google.com/maps/embed/v1/directions"
    params = {
        "key": google_maps_key,
        "origin": startort,
        "destination": zielort,
        "mode": "driving"
    }
    embed_url = base_url + "?" + urllib.parse.urlencode(params)

    if any(w.strip() for w in st.session_state.stops):
        st.warning("⚠️ Zwischenstopps werden in dieser Karte nicht angezeigt – Google Embed API erlaubt keine Wegpunkte. Bitte ggf. externe Routenansicht nutzen.")

    st.markdown("### 🗺️ Routen-Vorschau (Google Maps)")
    st.components.v1.iframe(embed_url, height=500)
