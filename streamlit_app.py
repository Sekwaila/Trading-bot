"""
SEKWAILA OMEGA X v6
Professional Trading Dashboard
"""

import time
from datetime import datetime

import streamlit as st

from config import APP_NAME, VERSION, SYMBOLS, TIMEFRAME
from database import db
from data.market_data import get_all_prices, get_candles
from signals.signal_engine import SignalEngine

engine = SignalEngine()

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
)

# ==========================================
# CACHE
# ==========================================

@st.cache_data(ttl=300)
def load_prices():
    return get_all_prices()

@st.cache_data(ttl=300)
def load_candles(symbol):
    return get_candles(symbol)

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("⚙ Settings")

    auto_refresh = st.toggle("Auto Refresh", True)

    refresh_seconds = st.slider(
        "Refresh Interval (Seconds)",
        300,
        1800,
        300,
    )

    st.success("🟢 Scanner Online")

# ==========================================
# HEADER
# ==========================================

st.title(f"📈 {APP_NAME}")

st.caption(f"Version {VERSION}")

st.write(
    "Last Refresh:",
    datetime.now().strftime("%d %B %Y %H:%M:%S"),
)

st.divider()

# ==========================================
# LIVE MARKET
# ==========================================

st.subheader("📊 Live Market")

prices = load_prices()

if prices:

    cols = st.columns(len(prices))

    for col, item in zip(cols, prices):

        with col:

            if item["success"]:

                st.metric(
                    item["symbol"],
                    f"{item['price']:,.2f}",
                )

            else:

                st.metric(
                    item["symbol"],
                    "N/A",
                )

else:

    st.warning("No market data.")

st.divider()

# ==========================================
# LIVE SIGNALS
# ==========================================

st.subheader("🎯 Live Signals")

for symbol in SYMBOLS:

    df = load_candles(symbol)

    if df.empty:

        st.warning(f"{symbol}: No candle
