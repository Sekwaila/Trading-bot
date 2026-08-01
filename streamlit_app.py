import streamlit as st
from datetime import datetime

from config import (
    APP_NAME,
    VERSION,
    SYMBOLS,
)

from data.market_data import get_all_prices


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

st.info(
    "No signals available yet.\n\n"
    "The Signal Engine will populate this section automatically."
)


# =====================================================
# ACTIVE TRADES
# =====================================================

st.subheader("📂 Active Trades")

st.info("No active trades.")


# =====================================================
# HISTORY
# =====================================================

st.subheader("📜 Trade History")

st.info("No trades recorded.")


# =====================================================
# PERFORMANCE
# =====================================================

st.subheader("📈 Performance")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Win Rate",
        "--"
    )

with c2:
    st.metric(
        "Trades",
        "0"
    )

with c3:
    st.metric(
        "Profit",
        "0.00"
    )

with c4:
    st.metric(
        "Drawdown",
        "0.00%"
    )


st.divider()

st.caption(
    "SEKWAILA OMEGA X • Professional Smart Money Dashboard"
)
