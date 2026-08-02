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
