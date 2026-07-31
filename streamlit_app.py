import streamlit as st

from market_data import get_price
from market_data import get_h1

from smc_engine import detect_signal
from signal_engine import calculate_signal

st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Sekwaila Omega X")
st.caption("Professional Smart Money Dashboard")

symbols = [
    "BTCUSD",
    "XAUUSD",
    "EURUSD",
    "US30"
]

for symbol in symbols:

    st.divider()

    st.subheader(symbol)

    price = get_price(symbol)

    if price is None:
        st.error("Price unavailable")
        continue

    st.metric("Live Price", f"{price:,.2f}")

    df = get_h1(symbol)

    if len(df) < 50:
        st.warning("Not enough market data")
        continue

    result = detect_signal(df)

    direction = "BUY" if "BUY" in result["signal"] else "SELL"

    stop = (
        price * 0.995
        if direction == "BUY"
        else price * 1.005
    )

    trade = calculate_signal(
        direction,
        price,
        stop,
        result["confidence"],
        result["reason"],
        symbol
    )

    if "AGGRESSIVE" in trade.signal:
        st.error(trade.signal)

    elif "STRONG" in trade.signal:
        st.success(trade.signal)

    elif trade.signal == "WAIT":
        st.warning("WAIT")

    else:
        st.info(trade.signal)

    c1, c2, c3 = st.columns(3)

    c1.metric("Entry", f"{trade.entry:.2f}")
    c2.metric("Stop Loss", f"{trade.stop_loss:.2f}")
    c3.metric("Confidence", f"{trade.confidence}%")

    a, b, c = st.columns(3)

    a.metric("TP1", f"{trade.tp1:.2f}")
    b.metric("TP2", f"{trade.tp2:.2f}")
    c.metric("TP3", f"{trade.tp3:.2f}")

    st.write("Reason")

    st.info(trade.reason)
