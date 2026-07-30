import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
.main{
    background-color:#0e1117;
}
h1,h2,h3{
    color:white;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 SEKWAILA OMEGA X")
st.caption("AI Smart Money Trading Assistant")

st.write(f"🕒 {datetime.now().strftime('%d %B %Y  %H:%M:%S')}")

st.divider()

st.sidebar.title("⚙️ CONTROL PANEL")

pair = st.sidebar.selectbox(
    "Select Market",
    [
        "XAUUSD",
        "BTCUSD",
        "EURUSD",
        "US30",
        "SP500"
    ]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    [
        "M5",
        "M15",
        "H1",
        "H4",
        "D1"
    ]
)

risk = st.sidebar.slider(
    "Risk %",
    0.5,
    5.0,
    1.0
)

st.sidebar.success("Omega X Online")
