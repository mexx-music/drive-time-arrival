import streamlit as st
import datetime
import urllib.parse

st.set_page_config(page_title="DriverTime Arrival – mit Routenoptionen", layout="centered")
st.title("🚛 DriverTime Arrival – mit Routenoptionen")

# Eingabefelder
startort = st.text_input("📍 Startort", "Volos")
zielort = st.text_input("🏁 Zielort", "Saarlouis")

# Zwischenstopps manuell als Liste
zwischenstopps = st.text_area("➕ Zwischenstopps (einen Ort pro Zeile)", "Sofia\nCalafat\nNadlac")

# Zeitangaben
abfahrtszeit = st.time_input("🕒 Abfahrtszeit", datetime.datetime.now().time())
stunden = st.number_input("🕓 Lenkzeit – Stunden", 0, 9, 4)
minuten = st.number_input("🕔 Minuten", 0, 59, 30)

# Routing-Option
routing_option = st.radio("🗺️ Routenansicht wählen", ["Nur Berechnung", "Google Maps extern öffnen"])

# Berechnen & Anzeigen
if st.button("🔍 Ankunft berechnen & Route anzeigen"):
    abfahrt = datetime.datetime.combine(datetime.date.today(), abfahrtszeit)
    lenkzeit = datetime.timedelta(hours=stunden, minutes=minuten)
    ankunft = abfahrt + lenkzeit

    st.success(f"🕒 Voraussichtliche Ankunft bei voller Lenkzeit: **{ankunft.strftime('%H:%M Uhr')}**")

    # Route öffnen – Google Maps Direktlink generieren
    if routing_option == "Google Maps extern öffnen":
        stops = [startort] + [s.strip() for s in zwischenstopps.split("\n") if s.strip()] + [zielort]
        url_teile = [urllib.parse.quote(s) for s in stops]
        gmaps_link = f"https://www.google.com/maps/dir/" + "/".join(url_teile)

        st.markdown("### 🌍 Route mit Zwischenzielen")
        st.markdown(f"[➡️ Route in Google Maps öffnen]({gmaps_link})")
        st.info("📲 Die Route öffnet sich in einem neuen Tab. Kehre danach einfach hierher zurück.")
