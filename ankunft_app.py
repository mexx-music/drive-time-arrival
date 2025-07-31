import streamlit as st
from datetime import datetime

st.set_page_config(page_title="DriverRoute ETA - Uhrzeitwahl", layout="centered")

st.title("🕰️ Uhrzeit der Abfahrt eingeben")

# AM/PM Auswahl
ampm = st.radio("🕑 Tageshälfte wählen:", ["AM", "PM"], horizontal=True)

# Stundenwahl (1–12)
st.subheader("⏰ Stunde wählen:")
cols_hour = st.columns(4)
selected_hour = None
for i, col in enumerate(cols_hour * 3):  # 3 Zeilen à 4 Spalten = 12 Stunden
    hour_val = i + 1
    if hour_val > 12:
        break
    if col.button(f"{hour_val:02d}", key=f"h{hour_val}"):
        selected_hour = hour_val

# Minutenwahl (00–55 in 5er-Schritten)
st.subheader("🕓 Minute wählen:")
cols_min = st.columns(6)
selected_minute = None
for i, col in enumerate(cols_min * 2):  # 2 Zeilen à 6 Spalten = 12 Buttons
    min_val = i * 5
    if min_val >= 60:
        break
    if col.button(f"{min_val:02d}", key=f"m{min_val}"):
        selected_minute = min_val

# Ergebnisanzeige
if selected_hour is not None and selected_minute is not None:
    hour_24 = selected_hour % 12 + (12 if ampm == "PM" else 0)
    selected_time = f"{hour_24:02d}:{selected_minute:02d}"
    st.success(f"🕒 Gewählte Zeit: {selected_time}")
