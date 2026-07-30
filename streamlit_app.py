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
st.divider()

st.header("🧭 DXY MARKET COMPASS")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("DXY Trend", "WAIT")

with col2:
    st.metric("Bias", "Neutral")

with col3:
    st.metric("Strength", "0%")
   st.divider()

st.header("📊 MARKET SCANNER")

markets = [
    "🥇 XAUUSD",
    "₿ BTCUSD",
    "💶 EURUSD",
    "🇺🇸 US30",
    "🇺🇸 SP500"
]

for market in markets:

    st.subheader(market)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Signal", "WAIT")
    c2.metric("Confidence", "0%")
    c3.metric("Entry", "--")
    c4.metric("SL", "--")
    c5.metric("TP", "--")

    st.info("Waiting for confirmation...")

    st.divider() 
