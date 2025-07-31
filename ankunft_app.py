import streamlit as st
import datetime

st.title("🕰️ Uhrzeit der Abfahrt eingeben")

# Uhrzeit-Voreinstellung
if "selected_hour" not in st.session_state:
    st.session_state.selected_hour = 8
if "selected_minute" not in st.session_state:
    st.session_state.selected_minute = 0

# 🕑 Stunde wählen
st.subheader("⏰ Stunde wählen:")
cols_hr = st.columns(6)
for h in range(24):
    if cols_hr[h % 6].button(f"{h:02d}", key=f"hour_{h}"):
        st.session_state.selected_hour = h

# 🕗 Minute wählen
st.subheader("🕓 Minute wählen:")
cols_min = st.columns(12)
for m in range(0, 60, 5):
    if cols_min[m // 5].button(f"{m:02d}", key=f"min_{m}"):
        st.session_state.selected_minute = m

# Ergebnis anzeigen
gewählte_zeit = datetime.time(st.session_state.selected_hour, st.session_state.selected_minute)
st.success(f"⏱️ Gewählte Zeit: {gewählte_zeit.strftime('%H:%M')}")
