"""
SEKWAILA OMEGA X — STREAMLIT DASHBOARD
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import ASSETS
from signals.signal_engine import generate_omega_signal
from database import load_journal, save_journal_entry
from trade_manager import calculate_position_size
from telegram_bot import send_telegram_message

# Page Configuration
st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide")

# Custom Dark Theme & Gold Custom Styling Injection
st.markdown("""
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #070604 !important;
        color: #EEE8DC !important;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #100C08 !important;
        border-right: 1px solid #2a2115 !important;
    }
    /* Custom Header Color */
    h1, h2, h3 {
        color: #D9A441 !important;
    }
    /* Metric Card Styling */
    [data-testid="stMetricValue"] {
        color: #D9A441 !important;
        font-weight: bold;
    }
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #D9A441 0%, #B8860B 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("👑 SEKWAILA OMEGA X — SMC DASHBOARD")

# Sidebar Controls & Navigation
st.sidebar.markdown("### 🧭 Navigation")
page = st.sidebar.radio(
    "Select View", 
    ["Dashboard", "Market Scanner", "AI Narrator", "Trade Journal", "Calculator"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Market Settings")

# Fallback pair dictionary if ASSETS from config is missing standard pairs
SUPPORTED_PAIRS = list(ASSETS.keys()) if ASSETS else [
    "BTCUSD", "XAUUSD", "US30", "EURUSD", "GBPUSD", "DXY", "SPX500", "NAS100"
]

sidebar_asset = st.sidebar.selectbox("Select Asset", SUPPORTED_PAIRS)
min_tf = st.sidebar.slider("Min Timeframe Agreement", 2, 4, 3)

# Main Navigation Router
if page == "Dashboard":
    res = generate_omega_signal(sidebar_asset, ASSETS.get(sidebar_asset, sidebar_asset), min_tf)

    if res and res.get("ok"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("BIAS", res["bias"])
        col2.metric("OMEGA SCORE", f"{res['score']}/100")
        col3.metric("ENTRY", f"{res['entry']:.2f}")
        col4.metric("R:R", f"{res['rr']:.2f}R")
        
        if "data" in res and "15M" in res["data"]:
            df_15m = res["data"]["15M"].tail(100)
            fig = go.Figure(data=[go.Candlestick(
                x=df_15m.index, open=df_15m["Open"], high=df_15m["High"],
                low=df_15m["Low"], close=df_15m["Close"]
            )])
            fig.update_layout(template="plotly_dark", height=500, title=f"{sidebar_asset} — 15M Chart Structure")
            st.plotly_chart(fig, use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Save Signal to Journal"):
                save_journal_entry({
                    "asset": res["symbol"], "bias": res["bias"],
                    "score": res["score"], "entry": res["entry"]
                })
                st.success("Entry saved!")
        with col_btn2:
            if st.button("📲 Send Telegram Alert"):
                msg = f"👑 *SEKWAILA OMEGA X SIGNAL*\nAsset: {res['symbol']}\nBias: {res['bias']}\nScore: {res['score']}/100\nEntry: {res['entry']:.2f}"
                send_telegram_message(msg)
                st.info("Telegram notification sent!")
    else:
        st.error(f"Error generating signal: {res.get('reason') if res else 'Unable to fetch data'}")

elif page == "Trade Journal":
    st.header("📖 Trade Journal")
    journal_entries = load_journal()
    if journal_entries:
        st.dataframe(pd.DataFrame(journal_entries))
    else:
        st.info("No saved trade entries found.")

elif page == "Calculator":
    st.header("🧮 Position Size Calculator")
    acc_size = st.number_input("Account Balance ($)", value=1000.0)
    risk_pct = st.slider("Risk Percentage (%)", 0.5, 5.0, 1.0)
    stop_pips = st.number_input("Stop Loss (Pips)", value=20.0)
    
    if st.button("Calculate Position Size"):
        pos_size = calculate_position_size(acc_size, risk_pct, stop_pips)
        st.success(f"Calculated Position Size: {pos_size}")

else:
    st.header(f"📌 {page}")
    st.info("Module active. Data stream initializing...")
