import streamlit as st

st.markdown(
    """
    <style>
    .big-selectbox select {
        font-size: 26px !important;
        height: 50px !important;
    }
    .big-label {
        font-size: 24px !important;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="big-label">⏰ Uhrzeit der Abfahrt eingeben:</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    hour = st.selectbox("Stunde", list(range(0, 24)), index=8, key="hour", format_func=lambda x: f"{x:02d}")
    st.markdown('<style>[id^="hour"] select {font-size: 26px; height: 50px;}</style>', unsafe_allow_html=True)

with col2:
    minute = st.selectbox("Minute", list(range(0, 60, 1)), index=0, key="minute", format_func=lambda x: f"{x:02d}")
    st.markdown('<style>[id^="minute"] select {font-size: 26px; height: 50px;}</style>', unsafe_allow_html=True)

st.success(f"⏱️ Gewählte Zeit: {hour:02d}:{minute:02d}")
