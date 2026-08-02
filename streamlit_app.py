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

# How long fetched data stays cached before a rerun triggers a fresh pull.
# Kept fixed (independent of the refresh slider) since cache TTL is set at
# decoration time and can't read a widget value.
DATA_CACHE_TTL = 60


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
# CACHED DATA FETCHERS
# ==========================================
# Wrapping the raw imports so every symbol in the loop below isn't hitting
# the live API on every single rerun (autorefresh included).

@st.cache_data(ttl=DATA_CACHE_TTL, show_spinner=False)
def cached_get_all_prices():
    return get_all_prices()


@st.cache_data(ttl=DATA_CACHE_TTL, show_spinner=False)
def cached_get_candles(symbol):
    return get_candles(symbol)


# ==========================================
# SESSION STATE
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
        60,
        600,
        120,
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

try:
    prices = cached_get_all_prices()
except Exception as e:
    prices = []
    st.error(f"Live market data unavailable: {e}")

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
# SIGNAL HISTORY (fetched early so we can dedupe against it below)
# ==========================================

try:
    history = db.get_signals()
except Exception as e:
    history = None
    st.error(f"Could not load signal history: {e}")

# ==========================================
# LIVE SIGNALS
# ==========================================

st.subheader("🎯 Live Signals")

signals_found = 0

for symbol in SYMBOLS:

    try:
        df = cached_get_candles(symbol)
    except Exception as e:
        st.warning(f"{symbol}: candle fetch failed ({e})")
        continue

    if df is None or df.empty:
        st.warning(f"{symbol}: No candle data")
        continue

    try:
        signal = engine.generate_signal(df)
    except Exception as e:
        st.warning(f"{symbol}: signal engine error ({e})")
        continue

    if signal is None:
        st.info(f"{symbol}: No signal")
        continue

    signals_found += 1

    # --- Dedup: only log if this differs from the last saved signal for
    # this symbol. Without this, an unchanging signal gets re-saved on
    # every autorefresh cycle and floods the history table.
    is_new_signal = True

    if history is not None and not history.empty and "symbol" in history.columns:
        symbol_rows = history[history["symbol"] == symbol]

        if not symbol_rows.empty:
            last_row = symbol_rows.iloc[0]  # assumes get_signals() is newest-first

            same_direction = last_row.get("signal") == signal["signal"]
            same_entry = False

            try:
                same_entry = abs(float(last_row.get("entry", 0)) - float(signal["entry"])) < 1e-6
            except (TypeError, ValueError):
                same_entry = False

            if same_direction and same_entry:
                is_new_signal = False

    if is_new_signal:
        try:
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
        except Exception as e:
            st.warning(f"{symbol}: could not save signal ({e})")

    c1, c2, c3 = st.columns(3)

    c1.metric(symbol, signal["signal"])
    c2.metric("Entry", signal["entry"])
    c3.metric("Confidence", f"{signal['confidence']}%")

    st.write(f"**Stop Loss:** {signal['sl']}")
    st.write(f"**TP1:** {signal['tp1']}")
    st.write(f"**TP2:** {signal['tp2']}")
    st.write(f"**TP3:** {signal['tp3']}")

    if not is_new_signal:
        st.caption("↳ unchanged since last save, not re-logged")

    st.divider()

if signals_found == 0:
    st.info("No active signals.")

# ==========================================
# SIGNAL HISTORY (display)
# ==========================================

st.subheader("📜 Signal History")

if history is None or history.empty:
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

if history is None or history.empty:

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
# st.rerun() alone never fires on its own — nothing schedules the rerun
# that would re-check this condition. A browser-level meta refresh
# actually reloads the page on a timer, which is what drives the rerun.

if auto_refresh:
    st.session_state.last_refresh = time.time()
    st.markdown(
        f'<meta http-equiv="refresh" content="{refresh_seconds}">',
        unsafe_allow_html=True,
    )

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    f"{APP_NAME} v{VERSION} • Professional AI Trading Dashboard"
)
