"""
SEKWAILA OMEGA X v4
Dashboard
"""

import streamlit as st
from datetime import datetime

from config import (
    APP_NAME,
    VERSION,
    SYMBOLS,
)

from database import db
from data.market_data import (
    get_all_prices,
    get_candles,
)
from signals.signal_engine import SignalEngine


engine = SignalEngine()


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide"
)


# =====================================================
# HEADER
# =====================================================

st.title(f"📈 {APP_NAME}")

st.caption(f"Version {VERSION}")

st.write(
    "Last Refresh:",
    datetime.now().strftime("%d %B %Y %H:%M:%S")
)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("⚙ Settings")

    auto_refresh = st.checkbox(
        "Auto Refresh",
        value=True
    )

    refresh_seconds = st.slider(
        "Refresh Every (Seconds)",
        30,
        300,
        60
    )

    st.success("🟢 Scanner Online")


# =====================================================
# LIVE MARKET
# =====================================================

st.subheader("📊 Live Market")

prices = get_all_prices()

cols = st.columns(len(prices))

for i, item in enumerate(prices):

    with cols[i]:

        if item["success"]:

            st.metric(

                item["symbol"],

                f"{item['price']:,.2f}"

            )

        else:

            st.metric(

                item["symbol"],

                "N/A"

            )


st.divider()


# =====================================================
# LIVE SIGNALS
# =====================================================

st.subheader("🎯 Live Signals")

for symbol in SYMBOLS:

    df = get_candles(symbol)

    if df.empty:

        st.warning(f"{symbol}: No candle data")

        continue

    signal = engine.generate_signal(df)

    if signal is None:

        st.info(f"{symbol}: Waiting for more candles")

        continue
# Save signal to database
db.save_signal(
    symbol=symbol,
    signal=signal["signal"],
    confidence=signal["confidence"],
    entry=signal["entry"],
    stop_loss=signal["sl"],
    tp1=signal["tp1"],
    tp2=signal["tp2"],
    tp3=signal["tp3"],
    timeframe="15min"
)
    c1, c2, c3 = st.columns(3)

    c1.metric(
        f"{symbol}",
        signal["signal"]
    )

    c2.metric(
        "Entry",
        signal["entry"]
    )

    c3.metric(
        "Confidence",
        f"{signal['confidence']}%"
    )

    st.write(
        f"SL: {signal['sl']}"
    )

    st.write(
        f"TP1: {signal['tp1']}"
    )

    st.write(
        f"TP2: {signal['tp2']}"
    )

    st.write(
        f"TP3: {signal['tp3']}"
    )

    st.divider()


# =====================================================
# SIGNAL HISTORY
# =====================================================

st.subheader("📜 Signal History")

signals = db.get_signals()

if len(signals):

    st.dataframe(

        signals,

        use_container_width=True

    )

else:

    st.info("No signals saved yet.")


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "SEKWAILA OMEGA X v4 • Professional Trading Dashboard"
)
