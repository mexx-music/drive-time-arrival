import streamlit as st

st.set_page_config(page_title="Uhrzeit Auswahl", layout="centered")

st.markdown("## 🕰️ Uhrzeit der Abfahrt (Touch-freundlich)")

st.markdown("### Stunde wählen")
cols_stunde = st.columns(6)
stunden = list(range(0, 24))
selected_hour = None
for i, col in enumerate(cols_stunde):
    with col:
        if st.button(f"{stunden[i]:02d}", key=f"h{i}"):
            selected_hour = stunden[i]

st.markdown("### Minute wählen (in 5er-Schritten)")
cols_minute = st.columns(6)
minuten = list(range(0, 60, 5))
selected_minute = None
for i, col in enumerate(cols_minute):
    with col:
        if st.button(f"{minuten[i]:02d}", key=f"m{i}"):
            selected_minute = minuten[i]

if selected_hour is not None and selected_minute is not None:
    st.success(f"🕓 Gewählte Uhrzeit: {selected_hour:02d}:{selected_minute:02d}")
elif selected_hour is not None or selected_minute is not None:
    st.info("⏳ Bitte beide Werte auswählen: Stunde und Minute.")
