import streamlit as st
from datetime import datetime

from config import (
    APP_NAME,
    VERSION,
    SYMBOLS,
)

from data.market_data import (
    get_all_prices,
    get_market_data,
)

from signals.signal_engine import SignalEngine
from database import db


engine = SignalEngine()


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# HEADER
# =====================================================

st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION}")

st.write(
    f"Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}"
)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("⚙ Settings")

    timeframe = st.selectbox(
        "Timeframe",
        [
            "15m",
            "1H",
            "4H"
        ],
        index=0
    )

    refresh = st.slider(
        "Refresh (Seconds)",
        30,
        300,
        60,
        30
    )

    if st.button("🔄 Refresh"):
        st.rerun()

    st.divider()

    st.success("🟢 Scanner Online")

    st.info("Provider: Twelve Data")


# =====================================================
# LIVE MARKET
# =====================================================

st.subheader("📊 Live Market")

prices = get_all_prices()

cols = st.columns(len(SYMBOLS))

for i, symbol in enumerate(SYMBOLS):

    with cols[i]:

        market = next(
            (
                x for x in prices
                if x.get("symbol") == symbol
            ),
            None
        )

        if market and market["success"]:

            st.metric(
                label=symbol,
                value=f"{market['price']:,.2f}"
            )

        else:

            st.metric(
                label=symbol,
                value="N/A"
            )


st.divider()


# =====================================================
# LIVE SIGNALS
# =====================================================

st.subheader("🎯 Live Signals")

for symbol in SYMBOLS:

    try:

        df = get_market_data(symbol)

        signal = engine.generate_signal(df)

        st.success(
            f"{symbol} • {signal['signal']}"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Entry",
            signal["entry"]
        )

        c2.metric(
            "Stop Loss",
            signal["sl"]
        )

        c3.metric(
            "Confidence",
            f"{signal['confidence']}%"
        )

        st.write(
            f"TP1: {signal['tp1']} | "
            f"TP2: {signal['tp2']} | "
            f"TP3: {signal['tp3']}"
        )

        st.divider()

    except Exception as e:

        st.warning(
            f"{symbol}: {e}"
        )


# =====================================================
# ACTIVE TRADES
# =====================================================

st.subheader("📂 Active Trades")

st.info(
    "Trade management will be enabled in the next version."
)


# =====================================================
# TRADE HISTORY
# =====================================================

st.subheader("📜 Trade History")

trades = db.get_trades()

if trades:

    st.dataframe(trades)

else:

    st.info("No trades recorded.")


# =====================================================
# PERFORMANCE
# =====================================================

st.subheader("📈 Performance")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Win Rate",
    f"{db.win_rate()}%"
)

c2.metric(
    "Trades",
    db.total_trades()
)

c3.metric(
    "Profit",
    db.total_profit()
)


st.divider()

st.caption(
    "SEKWAILA OMEGA X • Professional Smart Money Dashboard"
)
