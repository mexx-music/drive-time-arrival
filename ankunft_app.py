import streamlit as st

st.title("🕒 ETA mit besserer Uhrzeiteingabe")

col1, col2 = st.columns(2)
with col1:
    stunde = st.selectbox("🕓 Stunde", list(range(0, 24)), index=8)
with col2:
    minute = st.selectbox("🕧 Minute", list(range(0, 60, 5)), index=0)

st.write(f"Gewählte Uhrzeit: {stunde:02d}:{minute:02d}")
