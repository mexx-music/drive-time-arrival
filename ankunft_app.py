import streamlit as st

st.markdown(
    """
    <style>
    .time-selectbox select {
        font-size: 28px !important;
        height: 60px !important;
        padding: 8px;
    }
    .time-label {
        font-size: 24px !important;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="time-label">⏰ Uhrzeit der Abfahrt eingeben:</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    hour = st.selectbox("Stunde", [f"{i:02d}" for i in range(0, 24)], index=8, key="stunde")
    st.markdown('<style>div[data-baseweb="select"]{font-size: 28px;}</style>', unsafe_allow_html=True)

with col2:
    minute = st.selectbox("Minute", [f"{i:02d}" for i in range(0, 60)], index=0, key="minute")
    st.markdown('<style>div[data-baseweb="select"]{font-size: 28px;}</style>', unsafe_allow_html=True)

st.success(f"⏱️ Gewählte Zeit: {hour}:{minute}")
