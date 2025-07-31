import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ✅ Dein funktionierender Google API Key
GOOGLE_API_KEY = "AIzaSyDz4Fi--qUWvy7OhG1nZhnEWQgtmubCy8g"

# 🌍 Funktion zur Streckenabfrage
def get_route_info(origin, destination):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "OK":
        route = data["routes"][0]["legs"][0]
        distance_km = route["distance"]["value"] / 1000
        duration_min = route["duration"]["value"] / 60
        return distance_km, duration_min
    else:
        return None, None

# 🕓 AM/PM → 24h Format
def convert_to_24h(hour, minute, am_pm):
    if am_pm == "PM" and hour < 12:
        hour += 12
    if am_pm == "AM" and hour == 12:
        hour = 0
    return hour, minute

# 🎛️ Benutzeroberfläche
st.title("🚛 DriverRoute ETA mit Lenkzeit-Regeln")

col1, col2 = st.columns(2)
with col1:
    hour = st.selectbox("Startzeit (Stunde)", list(range(1, 13)), index=9)
with col2:
    minute = st.selectbox("Startzeit (Minuten)", list(range(0, 60, 5)), index=8)

am_pm = st.radio("AM oder PM", ["AM", "PM"], horizontal=True)

startort = st.text_input("Startort", "Volos, Griechenland")
zielort = st.text_input("Zielort", "Saarlouis, Deutschland")

st.subheader("Fahrzeit-Optionen")
zehn_stunden = st.slider("10h-Fahrten (pro Woche)", 0, 2, 2)
neun_stunden = st.slider("9h-Ruhepausen (pro Woche)", 0, 3, 3)
tankpause = st.checkbox("30min Tankpause erforderlich")
verbleibende_min = st.slider("Verbleibende Lenkzeit heute (Minuten)", 0, 540, 300)

# 🕰️ Startzeit setzen
start_hour, start_minute = convert_to_24h(hour, minute, am_pm)
tz = pytz.timezone("Europe/Vienna")
startzeit = tz.localize(datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0))

# ▶️ Start-Button
if st.button("Route analysieren & ETA berechnen"):
    distance_km, raw_duration = get_route_info(startort, zielort)
    if distance_km:
        st.success(f"🛣️ Strecke: {round(distance_km,1)} km – theoretische Fahrtzeit: {int(raw_duration)} min")

        real_fahrzeit = int(raw_duration)
        restzeit = verbleibende_min
        tageslimit = 540
        fahrplan = []
        pause_standard = 45
        tankpause_dauer = 30 if tankpause else 0
        tag = 0
        aktuelle_zeit = startzeit

        while real_fahrzeit > 0:
            tag += 1
            max_fahrt = 600 if zehn_stunden > 0 else 540
            heute_fahrt = min(real_fahrzeit, restzeit if tag == 1 else max_fahrt)
            pause = pause_standard + (tankpause_dauer if tag == 1 and tankpause else 0)
            real_fahrzeit -= heute_fahrt
            restzeit = 0
            ende = aktuelle_zeit + timedelta(minutes=heute_fahrt + pause)
            fahrplan.append(f"📅 Tag {tag}: Start: {aktuelle_zeit.strftime('%Y-%m-%d %H:%M')} – Fahrt: {heute_fahrt} min + Pause: {pause} min → Ende: {ende.strftime('%H:%M')}")
            aktuelle_zeit = ende + timedelta(hours=9 if neun_stunden > 0 else 11)
            if zehn_stunden > 0:
                zehn_stunden -= 1
            if neun_stunden > 0:
                neun_stunden -= 1

        eta = aktuelle_zeit.strftime("%A, %H:%M Uhr (%Z)")
        st.success(f"✅ ETA am Ziel: {eta}")

        st.markdown("### 📋 Fahrplan:")
        for eintrag in fahrplan:
            st.write(eintrag)

        # 🗺️ Karte
        map_url = f"https://www.google.com/maps/dir/?api=1&origin={startort}&destination={zielort}"
        st.markdown(f"[🗺️ Route in Google Maps öffnen]({map_url})", unsafe_allow_html=True)
    else:
        st.error("⚠️ Route konnte nicht berechnet werden. Bitte Eingaben prüfen.")
