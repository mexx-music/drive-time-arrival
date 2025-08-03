
# 🚛 DriverRoute ETA – Finalversion (03.08.) mit allen Features

import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta
import pytz
import math
import time

st.set_page_config(page_title="DriverRoute ETA – Fahrplan & Fähren", layout="centered")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

FAEHREN = {
    "Patras–Ancona (Superfast)": 22, "Ancona–Patras (Superfast)": 22,
    "Igoumenitsa–Ancona (Superfast)": 20, "Ancona–Igoumenitsa (Superfast)": 20,
    "Igoumenitsa–Bari (Grimaldi)": 10, "Bari–Igoumenitsa (Grimaldi)": 10,
    "Igoumenitsa–Brindisi (Grimaldi)": 9, "Brindisi–Igoumenitsa (Grimaldi)": 9,
    "Patras–Bari (Grimaldi)": 18, "Bari–Patras (Grimaldi)": 18,
    "Patras–Brindisi (Grimaldi)": 19, "Brindisi–Patras (Grimaldi)": 19,
    "Trelleborg–Travemünde (TT-Line)": 9, "Travemünde–Trelleborg (TT-Line)": 9,
    "Trelleborg–Rostock (TT-Line)": 7, "Rostock–Trelleborg (TT-Line)": 7,
    "Kiel–Oslo (Color Line)": 20, "Oslo–Kiel (Color Line)": 20,
    "Kiel–Trelleborg": 11, "Trelleborg–Kiel": 11,
    "Hirtshals–Bergen (Fjord Line)": 18, "Hirtshals–Stavanger (Fjord Line)": 12
}

st.title("🚛 DriverRoute ETA – Fahrplan mit Lenkzeit & Fähren")

col1, col2 = st.columns(2)
start = col1.text_input("Startort oder PLZ", "München")
ziel = col2.text_input("Zielort oder PLZ", "Patras")

zwischenstopp = st.text_input("Zwischenstopp (optional)", "")

abfahrt_str = st.text_input("Startzeit (Format: YYYY-MM-DD HH:MM)", datetime.now().strftime("%Y-%m-%d %H:%M"))
try:
    abfahrt_time = datetime.strptime(abfahrt_str, "%Y-%m-%d %H:%M")
except:
    st.warning("⚠️ Ungültiges Format. Bitte YYYY-MM-DD HH:MM verwenden.")
    abfahrt_time = datetime.now()

col_f1, col_f2 = st.columns([2, 1])
manuelle_faehre = col_f1.selectbox("🛳️ Manuelle Fährwahl (optional)", ["Keine"] + list(FAEHREN.keys()))
auto_faehre = col_f2.checkbox("🚢 Fähre automatisch erkennen", value=True)

st.markdown("### 🕓 Fahrzeit-Optionen")
fahrten_10h = st.number_input("🟩 Verfügbare 10-Stunden-Fahrten", min_value=0, max_value=2, value=2)
fahrten_9h_pause = st.number_input("🟦 Verfügbare 9-Stunden-Pausen", min_value=0, max_value=3, value=3)

we_pause_start = st.checkbox("🛌 Wöchentliche Ruhezeit in dieser Tour?", value=False)

def ort_plz_anzeigen(ort_input, bezeichnung):
    if not ort_input:
        return None
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(ort_input)}&key={GOOGLE_API_KEY}"
        r = requests.get(url)
        data = r.json()
        if data["status"] == "OK":
            result = data["results"][0]
            formatiert = result["formatted_address"]
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            st.success(f"📍 {bezeichnung}: {formatiert}")
            return lat, lng, formatiert
        else:
            st.warning(f"⚠️ {bezeichnung}: Ort nicht gefunden.")
            return None
    except Exception as e:
        st.warning(f"⚠️ Fehler bei {bezeichnung}: {e}")
        return None

start_info = ort_plz_anzeigen(start, "Start")
ziel_info = ort_plz_anzeigen(ziel, "Ziel")
zwischen_info = ort_plz_anzeigen(zwischenstopp, "Zwischenstopp") if zwischenstopp else None

def berechne_gesamtzeit(fahrzeit_minuten, abfahrt_dt, faehre_dauer_stunden=0, we_pause=False):
    gesamt_min = fahrzeit_minuten + int(faehre_dauer_stunden * 60)
    pausen = 0
    if gesamt_min > 270:
        pausen += 45
    if gesamt_min > 540:
        pausen += 45
    if we_pause:
        pausen += 2700
    eta = abfahrt_dt + timedelta(minutes=gesamt_min + pausen)
    return eta, pausen

def finde_faehre(start, ziel):
    kombi = f"{start}–{ziel}"
    reverse = f"{ziel}–{start}"
    for f in FAEHREN:
        if kombi in f or reverse in f:
            return f, FAEHREN[f]
    return None, 0

def entfernung_schaetzung(start_text, ziel_text, zwischen_text=None):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_text}&destination={ziel_text}&waypoints={zwischen_text}&key={GOOGLE_API_KEY}"
        r = requests.get(url)
        data = r.json()
        if data["status"] == "OK":
            dauer = data["routes"][0]["legs"]
            gesamt = sum([leg["duration"]["value"] for leg in dauer]) // 60
            return gesamt
        else:
            st.error("❌ Route konnte nicht berechnet werden.")
            return None
    except:
        st.error("❌ Fehler bei der Google-Routenabfrage.")
        return None

fahrzeit_min = entfernung_schaetzung(start, ziel, zwischenstopp)
if fahrzeit_min:
    faehre_dauer = 0
    faehre_name = None
    if auto_faehre:
        faehre_name, faehre_dauer = finde_faehre(start, ziel)
    elif manuelle_faehre != "Keine":
        faehre_name = manuelle_faehre
        faehre_dauer = FAEHREN[manuelle_faehre]

    eta, pause_min = berechne_gesamtzeit(fahrzeit_min, abfahrt_time, faehre_dauer, we_pause_start)

    st.markdown("### 📊 Berechnungsergebnis")
    st.success(f"🚚 Fahrzeit (geschätzt): {fahrzeit_min} min")
    st.info(f"⏱️ Pausenzeit automatisch eingerechnet: {pause_min} min")
    if faehre_name:
        st.warning(f"🛳️ Fähre erkannt: {faehre_name} – Dauer {faehre_dauer}h")

    st.markdown(
        f'''
        <h2 style="text-align: center; color: green;">
        ✅ <u>Ankunftszeit:</u><br>
        🕓 <b>{eta.strftime('%A, %d.%m.%Y – %H:%M')}</b>
        </h2>
        ''',
        unsafe_allow_html=True
    )

    from streamlit_folium import st_folium
    import folium

    def zeige_karte(start_info, ziel_info, zwischen_info=None):
        if not (start_info and ziel_info):
            st.warning("❗ Karte kann nicht angezeigt werden – Start oder Ziel fehlt.")
            return

        mittel_lat = (start_info[0] + ziel_info[0]) / 2
        mittel_lng = (start_info[1] + ziel_info[1]) / 2
        karte = folium.Map(location=[mittel_lat, mittel_lng], zoom_start=5)

        folium.Marker([start_info[0], start_info[1]], tooltip="Start", icon=folium.Icon(color='green')).add_to(karte)
        folium.Marker([ziel_info[0], ziel_info[1]], tooltip="Ziel", icon=folium.Icon(color='red')).add_to(karte)

        if zwischen_info:
            folium.Marker([zwischen_info[0], zwischen_info[1]], tooltip="Zwischenstopp", icon=folium.Icon(color='blue')).add_to(karte)

        st.markdown("### 🗺️ Karte mit Route (vereinfacht)")
        st_folium(karte, width=700, height=500)

    zeige_karte(start_info, ziel_info, zwischen_info)
