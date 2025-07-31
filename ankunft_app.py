import streamlit as st
import datetime

st.title("🕰️ Uhrzeit der Abfahrt eingeben")

# Initialwerte speichern
if "selected_hour" not in st.session_state:
    st.session_state.selected_hour = 8
if "selected_minute" not in st.session_state:
    st.session_state.selected_minute = 0
if "ampm_mode" not in st.session_state:
    st.session_state.ampm_mode = "AM"

# Umschalter AM/PM
st.subheader("☀️ AM oder 🌙 PM auswählen:")
col1, col2 = st.columns(2)
with col1:
    if st.button("☀️ AM"):
        st.session_state.ampm_mode = "AM"
with col2:
    if st.button("🌙 PM"):
        st.session_state.ampm_mode = "PM"

# Dynamische Stunden je nach AM/PM
st.subheader("⏰ Stunde wählen:")
cols_hr = st.columns(4)
if st.session_state.ampm_mode == "AM":
    hour_range = range(1, 13)  # 01–12
else:
    hour_range = range(13, 25)  # 13–24

for i, h in enumerate(hour_range):
    if cols_hr[i % 4].button(f"{h:02d}", key=f"hour_{h}"):
        st.session_state.selected_hour = h

# Minuten
st.subheader("🕓 Minute wählen:")
cols_min = st.columns(6)
for i, m in enumerate(range(0, 60, 5)):
    if cols_min[i % 6].button(f"{m:02d}", key=f"min_{m}"):
        st.session_state.selected_minute = m

# Anzeige
h = st.session_state.selected_hour
m = st.session_state.selected_minute
gewählte_zeit = datetime.time(h % 24, m)
st.success(f"⏱️ Gewählte Zeit: {gewählte_zeit.strftime('%H:%M')}")
