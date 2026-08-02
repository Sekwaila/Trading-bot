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

        st.warning(f"{symbol}: No candle data")

        continue

    signal = engine.generate_signal(df)

    if signal is None:

        st.info(f"{symbol}: No valid signal")

        continue

    history = db.get_signals()

    duplicate = False

    if not history.empty:

        latest = history[history["symbol"] == symbol]

        if not latest.empty:

            row = latest.iloc[0]

            duplicate = (
                row["signal"] == signal["signal"]
                and abs(row["entry"] - signal["entry"]) < 0.00001
            )

    if not duplicate:

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

    a, b, c = st.columns(3)

    a.metric(symbol, signal["signal"])
    b.metric("Entry", signal["entry"])
    c.metric("Confidence", f"{signal['confidence']}%")

    st.write(f"**Stop Loss:** {signal['sl']}")
    st.write(f"**TP1:** {signal['tp1']}")
    st.write(f"**TP2:** {signal['tp2']}")
    st.write(f"**TP3:** {signal['tp3']}")

    st.write(f"**RSI:** {signal['rsi']}")
    st.write(f"**MACD:** {signal['macd']}")
    st.write(f"**ATR:** {signal['atr']}")

    st.divider()

# ==========================================
# HISTORY
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
# STATS
# ==========================================

st.subheader("📊 Statistics")

if history.empty:

    x, y, z = st.columns(3)

    x.metric("Signals", 0)
    y.metric("BUY", 0)
    z.metric("SELL", 0)

else:

    x, y, z = st.columns(3)

    x.metric("Signals", len(history))
    y.metric("BUY", len(history[history.signal == "BUY"]))
    z.metric("SELL", len(history[history.signal == "SELL"]))

st.divider()

st.caption(f"{APP_NAME} v{VERSION}")

# ==========================================
# AUTO REFRESH
# ==========================================

if auto_refresh:

    st.markdown(
        f'<meta http-equiv="refresh" content="{refresh_seconds}">',
        unsafe_allow_html=True,
    )
