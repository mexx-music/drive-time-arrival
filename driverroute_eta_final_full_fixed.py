
# 🚛 DriverRoute ETA – Smart-Fähren-Modul (Norwegen + Griechenland, korrigiert)
import streamlit as st
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="DriverRoute ETA – Smart Fähren", layout="centered")
st.title("🧠 ETA mit Fährenlogik & Ruhezeitprüfung")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

def ferry_eta_block(hafen, eta_vorhafen, fahrten):
    st.markdown(f"### 🚢 Fährenvorschläge ab {hafen}")
    ausgewählt = st.radio(f"Wähle eine Fähre ab {hafen}:", [
        f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" for f in fahrten
    ], key=f"wahl_{hafen}")
    fähre = next(f for f in fahrten if f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" == ausgewählt)
    warte = (datetime.strptime(fähre["abfahrt"], "%H:%M") - datetime.combine(datetime.today(), eta_vorhafen)).seconds / 3600
    gesamt = warte + fähre["dauer"]
    if gesamt >= 11:
        status = "✅ Gilt als vollständige Ruhezeit (≥ 11h)"
    elif gesamt >= 9:
        status = "🟡 Teilweise Ruhezeit (≥ 9h)"
    else:
        status = "⚠️ Nicht ausreichend für Ruhepause"
    ankunft = (datetime.combine(datetime.today(), datetime.strptime(fähre["abfahrt"], "%H:%M").time()) +
               timedelta(hours=fähre["dauer"]))
    st.success(f"Wartezeit: {warte:.1f}h, Fahrt: {fahre['dauer']}h → Gesamt: {gesamt:.1f}h")
    st.info(f"⛴️ Ankunft {fähre['ziel']}: {ankunft.strftime('%H:%M')} Uhr")

st.markdown("## 🇬🇷 Griechenland: Igoumenitsa → Brindisi/Ancona/Venedig")
eta_igou = st.time_input("🕓 ETA Igoumenitsa", value=datetime.strptime("15:00", "%H:%M").time())
faehren_igou = [
    {"ziel": "Brindisi", "abfahrt": "16:00", "dauer": 9},
    {"ziel": "Ancona", "abfahrt": "19:30", "dauer": 20},
    {"ziel": "Venedig", "abfahrt": "23:00", "dauer": 26}
]
ferry_eta_block("Igoumenitsa", eta_igou, faehren_igou)

st.markdown("---")

st.markdown("## 🇳🇴 Norwegen: Hirtshals → Bergen/Stavanger (Fjord Line)")
eta_hirtshals = st.time_input("🕓 ETA Hirtshals", value=datetime.strptime("07:30", "%H:%M").time())
faehren_hirt = [
    {"ziel": "Stavanger", "abfahrt": "11:30", "dauer": 10},
    {"ziel": "Bergen", "abfahrt": "20:00", "dauer": 16}
]
ferry_eta_block("Hirtshals", eta_hirtshals, faehren_hirt)
