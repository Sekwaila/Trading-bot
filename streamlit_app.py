import streamlit as st
from datetime import datetime

from config import (
    APP_NAME,
    VERSION,
    SYMBOLS,
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===============================
# HEADER
# ===============================

st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION}")

st.write(
    f"Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}"
)


# ===============================
# SIDEBAR
# ===============================

with st.sidebar:

    st.header("⚙ Settings")

    timeframe = st.selectbox(
        "Timeframe",
        [
            "15m",
            "1H",
            "4H",
            "1D"
        ],
        index=0
    )

    auto_refresh = st.checkbox(
        "Auto Refresh",
        value=True
    )

    refresh_seconds = st.slider(
        "Refresh Every (seconds)",
        min_value=30,
        max_value=300,
        value=60,
        step=30
    )

    st.divider()

    st.success("Scanner Status")

    st.write("🟢 ONLINE")


# ===============================
# DASHBOARD
# ===============================

st.subheader("📊 Market Overview")

cols = st.columns(len(SYMBOLS))

for i, symbol in enumerate(SYMBOLS):

    with cols[i]:

        st.metric(

            label=symbol,

            value="Loading...",

            delta="--"

        )


st.divider()


# ===============================
# SIGNAL PANEL
# ===============================

st.subheader("🎯 Live Signals")

st.info(
    "No signals available yet.\n\n"
    "The Signal Engine will populate this table automatically."
)


# ===============================
# ACTIVE TRADES
# ===============================

st.subheader("📂 Active Trades")

st.info(
    "No active trades."
)


# ===============================
# TRADE HISTORY
# ===============================

st.subheader("📜 Recent Signals")

st.info(
    "Database not connected."
)


# ===============================
# PERFORMANCE
# ===============================

st.subheader("📈 Performance")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Win Rate", "--")

with c2:
    st.metric("Total Trades", "--")

with c3:
    st.metric("Profit", "--")

with c4:
    st.metric("Drawdown", "--")


st.divider()

st.caption(
    "SEKWAILA OMEGA X • Professional Smart Money Dashboard"
)
