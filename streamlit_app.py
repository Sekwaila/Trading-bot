"""
SEKWAILA OMEGA X v5
Professional Trading Dashboard
"""

import time
from datetime import datetime

import streamlit as st

from config import (
    APP_NAME,
    VERSION,
    SYMBOLS,
    TIMEFRAME,
)

from database import db
from data.market_data import (
    get_all_prices,
    get_candles,
)
from signals.signal_engine import SignalEngine


engine = SignalEngine()


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# AUTO REFRESH
# ==========================================

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("⚙ Settings")

    auto_refresh = st.toggle(
        "Auto Refresh",
        value=True,
    )

    refresh_seconds = st.slider(
        "Refresh Interval",
        30,
        300,
        60,
    )

    st.divider()

    st.success("🟢 Scanner Online")

    st.write(f"Timeframe: **{TIMEFRAME}**")
    st.write(f"Symbols: **{len(SYMBOLS)}**")

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

prices = get_all_prices()

if not prices:
    st.warning("No market data available.")
else:
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

st.divider()

# ==========================================
# LIVE SIGNALS
# ==========================================

st.subheader("🎯 Live Signals")

signals_found = 0

for symbol in SYMBOLS:

    df = get_candles(symbol)

    if df.empty:
        st.warning(f"{symbol}: No candle data")
        continue

    signal = engine.generate_signal(df)

    if signal is None:
        st.info(f"{symbol}: No signal")
        continue

    signals_found += 1

    db.save_signal(
        symbol=symbol,
        signal=signal["signal"],
        confidence=signal["confidence"],
        entry=signal["entry"],
        stop_loss=signal["sl"],
        tp1=signal["tp1"],
        tp2=signal["tp2"],
        tp3=signal["tp3"],
        timeframe=TIMEFRAME,
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(symbol, signal["signal"])
    c2.metric("Entry", signal["entry"])
    c3.metric("Confidence", f"{signal['confidence']}%")

    st.write(f"**Stop Loss:** {signal['sl']}")
    st.write(f"**TP1:** {signal['tp1']}")
    st.write(f"**TP2:** {signal['tp2']}")
    st.write(f"**TP3:** {signal['tp3']}")

    st.divider()

if signals_found == 0:
    st.info("No active signals.")
# ==========================================
# SIGNAL HISTORY
# ==========================================

st.subheader("📜 Signal History")

history = db.get_signals()

if history.empty:
    st.info("No signals saved yet.")
else:
    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ==========================================
# PERFORMANCE
# ==========================================

st.subheader("📊 Performance")

if history.empty:

    c1, c2, c3 = st.columns(3)

    c1.metric("Signals", 0)
    c2.metric("Buy", 0)
    c3.metric("Sell", 0)

else:

    total = len(history)

    buys = len(history[history["signal"] == "BUY"])

    sells = len(history[history["signal"] == "SELL"])

    c1, c2, c3 = st.columns(3)

    c1.metric("Signals", total)
    c2.metric("BUY", buys)
    c3.metric("SELL", sells)

st.divider() 
# ==========================================
# AUTO REFRESH
# ==========================================

if auto_refresh:

    now = time.time()

    if now - st.session_state.last_refresh >= refresh_seconds:

        st.session_state.last_refresh = now

        st.rerun()

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    f"{APP_NAME} v{VERSION} • Professional AI Trading Dashboard"
)
