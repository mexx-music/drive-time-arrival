import streamlit as st
import datetime

st.title("🕰️ Uhrzeit der Abfahrt eingeben")

# Session-Variablen
if "selected_hour_12" not in st.session_state:
    st.session_state.selected_hour_12 = 8
if "selected_minute" not in st.session_state:
    st.session_state.selected_minute = 0
if "selected_ampm" not in st.session_state:
    st.session_state.selected_ampm = "AM"

# AM/PM-Umschalter
st.subheader("☀️ AM oder 🌙 PM auswählen:")
col1, col2 = st.columns(2)
with col1:
    if st.button("☀️ AM"):
        st.session_state.selected_ampm = "AM"
with col2:
    if st.button("🌙 PM"):
        st.session_state.selected_ampm = "PM"

# Stunde (1–12)
st.subheader("⏰ Stunde wählen:")
cols_hr = st.columns(4)
for h in range(1, 13):
    if cols_hr[(h - 1) % 4].button(f"{h:02d}", key=f"hour12_{h}"):
        st.session_state.selected_hour_12 = h

# Minute (00–55 in 5er-Schritten)
st.subheader("🕓 Minute wählen:")
cols_min = st.columns(6)
for m in range(0, 60, 5):
    if cols_min[m // 10].button(f"{m:02d}", key=f"min_{m}"):
        st.session_state.selected_minute = m

# Umrechnung in 24-Stunden-Format
h = st.session_state.selected_hour_12
if st.session_state.selected_ampm == "PM" and h != 12:
    h += 12
elif st.session_state.selected_ampm == "AM" and h == 12:
    h = 0
m = st.session_state.selected_minute
gewählte_zeit = datetime.time(h, m)

# Anzeige
st.success(f"⏱️ Gewählte Zeit: {gewählte_zeit.strftime('%H:%M')} ({st.session_state.selected_hour_12:02d}:{m:02d} {st.session_state.selected_ampm})")
