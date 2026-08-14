"""
SEKWAILA OMEGA X - Streamlit Dashboard Main Entry Point
"""

import streamlit as st
from signals.signal_engine import analyze_market, get_market_overview
from twelve_data_adapter import TwelveDataClient

# Page Config
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ SEKWAILA OMEGA X — Trading Engine")

# Initialize API Adapter from Secrets or Sidebar
api_key = st.secrets.get("TWELVE_DATA_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Twelve Data API Key", type="password")

client = TwelveDataClient(api_key=api_key)

# Sidebar Control Elements
st.sidebar.header("Navigation & Settings")
symbol = st.sidebar.text_input("Trading Pair / Symbol", value="EUR/USD")
timeframe = st.sidebar.selectbox(
    "Timeframe", ["5m", "15m", "30m", "1h", "4h", "1d"], index=1
)

if st.sidebar.button("Run Analysis", type="primary"):
    if not api_key:
        st.error("Please provide a Twelve Data API Key to proceed.")
    else:
        with st.spinner(f"Analyzing {symbol} on {timeframe}..."):
            result = analyze_market(symbol, timeframe, client)

        if result["ok"]:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Asset", result["symbol"])
            col2.metric("Bias", result["bias"])
            col3.metric("Signal Level", result["signal"])
            col4.metric("Score", f"{result['score']} / 100")

            st.markdown("---")
            st.subheader("Trade Setup & Execution Parameters")
            setup_col1, setup_col2 = st.columns(2)

            with setup_col1:
                st.write(f"**Entry Price:** {result['entry_price']}")
                st.write(f"**Stop Loss:** {result['stop_loss']}")
                st.write(f"**Risk-Reward:** {result['rr']}")

            with setup_col2:
                st.write(f"**Take Profit 1:** {result['tp1']}")
                st.write(f"**Take Profit 2:** {result['tp2']}")
                st.write(f"**Take Profit 3:** {result['tp3']}")

            st.info(f"**Engine Note:** {result['reason']}")
        else:
            st.error(f"Analysis failed: {result['reason']}")

st.markdown("---")
st.subheader("Watchlist Overview")
watchlist = ["EUR/USD", "GBP/USD", "USD/JPY", "BTC/USD"]
if api_key and st.button("Refresh Watchlist"):
    overview_df = get_market_overview(watchlist, client)
    st.dataframe(overview_df, use_container_width=True)
