
# 🚛 DriverRoute ETA – Smart-Fähren-Modul (Vorschau, gekürzt)
# Hinweis: vollständige Integration folgt als kompletter Block

import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="DriverRoute ETA – Smart Fähren", layout="centered")
st.title("🧠 ETA mit Fährenlogik & Ruhezeitprüfung")

st.markdown("### 🚢 Fährenvorschlag: Igoumenitsa → Brindisi/Ancona")

ankunft_igou = st.time_input("🕓 ETA Igoumenitsa", value=datetime.now().time())
moegl_faehr = [
    {"ziel": "Brindisi", "abfahrt": "16:00", "dauer": 9},
    {"ziel": "Ancona", "abfahrt": "19:30", "dauer": 20},
    {"ziel": "Venedig", "abfahrt": "23:00", "dauer": 26},
]

selected = st.radio("Wähle mögliche Fähre:", [f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" for f in moegl_faehr])

# Ruhezeitprüfung
sel = next(f for f in moegl_faehr if f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" == selected)
wartezeit = (datetime.strptime(sel["abfahrt"], "%H:%M") - datetime.combine(datetime.today(), ankunft_igou)).seconds / 3600
gesamt = wartezeit + sel["dauer"]
if gesamt >= 11:
    pauseinfo = "✅ Gilt als vollständige Ruhezeit (≥ 11h)"
elif gesamt >= 9:
    pauseinfo = "🟡 Teilweise Ruhezeit (≥ 9h)"
else:
    pauseinfo = "⚠️ Nicht ausreichend für Ruhepause"
st.success(f"Wartezeit: {wartezeit:.1f}h → Gesamt: {gesamt:.1f}h – {pauseinfo}")
