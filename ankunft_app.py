import streamlit as st

st.subheader("🕓 Uhrzeit auswählen über Zahlenkreis")

# Zustand merken
if "selected_hour" not in st.session_state:
    st.session_state.selected_hour = 4
if "selected_minute" not in st.session_state:
    st.session_state.selected_minute = 0

st.markdown("### ⏰ Stunde wählen:")
cols_hour = st.columns(6)
for i in range(24):
    if cols_hour[i % 6].button(f"{i:02d}", key=f"hour_{i}"):
        st.session_state.selected_hour = i

st.markdown("### 🕧 Minute wählen:")
cols_min = st.columns(6)
for m in range(0, 60, 5):
    if cols_min[m // 5].button(f"{m:02d}", key=f"min_{m}"):
        st.session_state.selected_minute = m

# Anzeige
st.markdown(f"## ✅ Gewählte Uhrzeit: {st.session_state.selected_hour:02d}:{st.session_state.selected_minute:02d}")
