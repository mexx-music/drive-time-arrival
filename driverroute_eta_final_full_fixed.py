
# 🚛 DriverRoute ETA – Smart-Fährenmodul mit Regionentoggle
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="DriverRoute ETA – Smart Fähren", layout="centered")
st.title("🧠 ETA mit optionaler Fährenlogik (modular)")

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Master-Toggle
faehre_aktiv = st.checkbox("🚢 Fähre aktivieren", value=False)

def ferry_eta_block(hafen, eta_vorhafen, fahrten):
    st.markdown(f"### 🚢 Fährenvorschläge ab {hafen}")
    ausgewählt = st.radio(f"Wähle eine Fähre ab {hafen}:", [
        f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" for f in fahrten
    ], key=f"wahl_{hafen}")
    faehre = next(f for f in fahrten if f"{f['abfahrt']} – {f['ziel']} ({f['dauer']}h)" == ausgewählt)
    warte = (datetime.strptime(faehre["abfahrt"], "%H:%M") - datetime.combine(datetime.today(), eta_vorhafen)).seconds / 3600
    gesamt = warte + faehre["dauer"]
    if gesamt >= 11:
        status = "✅ Gilt als vollständige Ruhezeit (≥ 11h)"
    elif gesamt >= 9:
        status = "🟡 Teilweise Ruhezeit (≥ 9h)"
    else:
        status = "⚠️ Nicht ausreichend für Ruhepause"
    ankunft = (datetime.combine(datetime.today(), datetime.strptime(faehre["abfahrt"], "%H:%M").time()) +
               timedelta(hours=faehre["dauer"]))
    st.success(f"Wartezeit: {warte:.1f}h, Fahrt: {faehre['dauer']}h → Gesamt: {gesamt:.1f}h")
    st.info(f"⛴️ Ankunft {faehre['ziel']}: {ankunft.strftime('%H:%M')} Uhr")

if faehre_aktiv:
    col1, col2, col3 = st.columns(3)
    show_gr = col1.checkbox("🇬🇷 Griechenland", value=False)
    show_no = col2.checkbox("🇳🇴 Norwegen", value=False)
    show_se = col3.checkbox("🇸🇪 Nordeuropa", value=False)

    if show_gr:
        st.markdown("### 🇬🇷 Igoumenitsa → Brindisi/Ancona/Venedig")
        eta_igou = st.time_input("🕓 ETA Igoumenitsa", value=datetime.strptime("15:00", "%H:%M").time(), key="eta_gr")
        faehren_igou = [
            {"ziel": "Brindisi", "abfahrt": "16:00", "dauer": 9},
            {"ziel": "Ancona", "abfahrt": "19:30", "dauer": 20},
            {"ziel": "Venedig", "abfahrt": "23:00", "dauer": 26}
        ]
        ferry_eta_block("Igoumenitsa", eta_igou, faehren_igou)

    if show_no:
        st.markdown("### 🇳🇴 Hirtshals → Bergen/Stavanger (Fjord Line)")
        eta_hirt = st.time_input("🕓 ETA Hirtshals", value=datetime.strptime("07:30", "%H:%M").time(), key="eta_no")
        faehren_no = [
            {"ziel": "Stavanger", "abfahrt": "11:30", "dauer": 10},
            {"ziel": "Bergen", "abfahrt": "20:00", "dauer": 16}
        ]
        ferry_eta_block("Hirtshals", eta_hirt, faehren_no)

    if show_se:
        st.markdown("### 🇸🇪 Nordrouten: Kiel/Rostock/Travemünde → Trelleborg/Oslo")
        eta_kiel = st.time_input("🕓 ETA Kiel", value=datetime.strptime("10:00", "%H:%M").time(), key="eta_kiel")
        faehren_kiel = [
            {"ziel": "Oslo", "abfahrt": "14:00", "dauer": 20},
            {"ziel": "Trelleborg", "abfahrt": "22:00", "dauer": 13}
        ]
        ferry_eta_block("Kiel", eta_kiel, faehren_kiel)

        eta_rostock = st.time_input("🕓 ETA Rostock", value=datetime.strptime("16:00", "%H:%M").time(), key="eta_ros")
        faehren_ros = [{"ziel": "Trelleborg", "abfahrt": "18:00", "dauer": 6.5}]
        ferry_eta_block("Rostock", eta_rostock, faehren_ros)

        eta_trave = st.time_input("🕓 ETA Travemünde", value=datetime.strptime("19:00", "%H:%M").time(), key="eta_trav")
        faehren_trave = [{"ziel": "Trelleborg", "abfahrt": "21:00", "dauer": 9}]
        ferry_eta_block("Travemünde", eta_trave, faehren_trave)
else:
    st.info("🚢 Fährenlogik derzeit deaktiviert – nur Start/Ziel-Planung aktiv.")
