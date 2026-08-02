"""
SEKWAILA OMEGA X v6
Professional Trading Dashboard
"""

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

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
)

# =====================================
# CACHE
# =====================================

@st.cache_data(ttl=300)
def load_prices():
    return get_all_prices()


@st.cache_data(ttl=300)
def load_candles(symbol):
    return get_candles(symbol)


# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.title("⚙ Settings")

    auto_refresh = st.toggle(
        "Auto Refresh",
        True,
    )

    refresh_seconds = st.slider(
        "Refresh Interval",
        300,
        1800,
        300,
    )

    st.success("🟢 Scanner Online")

# =====================================
# HEADER
# =====================================

st.title(f"📈 {APP_NAME}")

st.caption(f"Version {VERSION}")

st.write(
    "Last Refresh:",
    datetime.now().strftime("%d %B %Y %H:%M:%S"),
)

st.divider()

# =====================================
# LIVE MARKET
# =====================================

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

# =====================================
# LIVE SIGNALS
# =====================================

st.subheader("🎯 Live Signals")

for symbol in SYMBOLS:

    df = load_candles(symbol)

    if df.empty:

        st.warning(f"{symbol}: No candle data")

        continue

    signal = engine.generate_signal(df)

    if signal is None:

        st.info(f"{symbol}: No signal")

        continue

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

    st.write(f"**RSI:** {signal['rsi']}")
    st.write(f"**MACD:** {signal['macd']}")
    st.write(f"**ATR:** {signal['atr']}")

    st.divider()

# =====================================
# HISTORY
# =====================================

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

# =====================================
# STATISTICS
# =====================================

st.subheader("📊 Statistics")

if history.empty:

    a, b, c = st.columns(3)

    a.metric("Signals", 0)
    b.metric("BUY", 0)
    c.metric("SELL", 0)

else:

    buys = len(history[history["signal"] == "BUY"])
    sells = len(history[history["signal"] == "SELL"])

    a, b, c = st.columns(3)

    a.metric("Signals", len(history))
    b.metric("BUY", buys)
    c.metric("SELL", sells)

st.divider()

if auto_refresh:

    st.markdown(
        f'<meta http-equiv="refresh" content="{refresh_seconds}">',
        unsafe_allow_html=True,
    )

st.caption(
    f"{APP_NAME} v{VERSION} • Professional Trading Dashboard"
)
