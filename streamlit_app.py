import os
import sys

# Ensure root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from Signals import signal_engine as engine

st.set_page_config(
    page_title="Sekwaila Omega X - MT5 Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sekwaila Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    .sekwaila-card {
        background-color: #121721;
        border: 1px solid #1e2638;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .buy-badge {
        background-color: #064e3b; color: #34d399; font-weight: bold;
        padding: 6px 14px; border-radius: 20px; border: 1px solid #10b981;
        display: inline-block;
    }
    .buy-now-btn {
        background-color: #059669; color: #ffffff; font-weight: bold;
        text-align: center; padding: 10px; border-radius: 8px; margin-top: 10px;
    }
    .val-green { color: #10b981; font-weight: bold; }
    .val-red { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "symbol_map" not in st.session_state:
    st.session_state.symbol_map = {
        "XAUUSD": "XAUUSDm",
        "US30": "US30.cash",
        "SP500": "US500.cash",
        "BTCUSD": "BTCUSD",
        "EURUSD": "EURUSDm",
        "DXY": "USDX"
    }

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("## ⚡ SEKWAILA")
    st.caption("OMEGA X — MT5 SINGLE SOURCE")
    st.divider()
    
    nav = st.radio("Navigation", ["🏠 Dashboard", "⚙️ MT5 & Symbol Settings", "📲 Telegram Alerts"], label_visibility="collapsed")
    st.divider()
    
    bot_token = st.text_input("Telegram Bot Token", type="password")
    chat_id = st.text_input("Telegram Chat ID")

# ----------------- SETTINGS PAGE -----------------
if nav == "⚙️ MT5 & Symbol Settings":
    st.title("⚙️ Broker Symbol Mapping")
    st.info("Configure exact MT5 broker symbols matching your broker terminal.")
    
    with st.form("symbol_mapping_form"):
        st.subheader("Configure Pair Mapping")
        map_xau = st.text_input("XAUUSD Broker Symbol", value=st.session_state.symbol_map["XAUUSD"])
        map_us30 = st.text_input("US30 Broker Symbol", value=st.session_state.symbol_map["US30"])
        map_sp500 = st.text_input("SP500 Broker Symbol", value=st.session_state.symbol_map["SP500"])
        map_btc = st.text_input("BTCUSD Broker Symbol", value=st.session_state.symbol_map["BTCUSD"])
        map_eur = st.text_input("EURUSD Broker Symbol", value=st.session_state.symbol_map["EURUSD"])
        
        submitted = st.form_submit_button("Save Symbol Map")
        if submitted:
            st.session_state.symbol_map["XAUUSD"] = map_xau
            st.session_state.symbol_map["US30"] = map_us30
            st.session_state.symbol_map["SP500"] = map_sp500
            st.session_state.symbol_map["BTCUSD"] = map_btc
            st.session_state.symbol_map["EURUSD"] = map_eur
            st.success("Symbol mapping saved successfully!")

# ----------------- MAIN DASHBOARD VIEW -----------------
elif nav == "🏠 Dashboard":
    st.title("⚡ Omega Live Signals (MT5 Feed)")
    
    selected_pair = st.selectbox("Select Pair", list(st.session_state.symbol_map.keys()))
    broker_sym = st.session_state.symbol_map[selected_pair]
    
    signal = engine.generate_omega_signal(selected_pair, broker_sym)
    
    if signal["status"] == "ERROR":
        st.error(signal["message"])
        st.warning("If hosted on Streamlit Cloud (Linux), MT5 direct terminal connection is disabled. Run locally on Windows or connect via an MT5 API bridge.")
    else:
        st.markdown(f"""
        <div class="sekwaila-card">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span style="color: #6b7280; font-size: 0.8rem;">MT5 SINGLE SOURCE SIGNAL</span>
                    <h1 style="margin: 0;">{signal['pair']} <small style="font-size: 1rem; color: #6b7280;">({signal['broker_symbol']})</small></h1>
                    <h2 style="margin: 0; color: #10b981;">{signal['entry']}</h2>
                </div>
                <div style="text-align: right;">
                    <span style="color: #6b7280; font-size: 0.8rem;">CONFIDENCE</span>
                    <h1 style="margin: 0; color: #10b981;">{signal['confidence']}%</h1>
                    <span style="color: #f59e0b;">{signal['quality']}</span>
                </div>
            </div>
            <br>
            <div class="buy-badge">{signal['action']} ACTIVE</div>
            <div class="buy-now-btn">🔥 {signal['action']} NOW AT {signal['entry']}</div>
            <br>
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <b>ENTRY:</b> <span class="val-green">{signal['entry']}</span><br>
                    <b>TP1:</b> <span class="val-green">{signal['tp1']}</span><br>
                    <b>TP2:</b> <span class="val-green">{signal['tp2']}</span><br>
                    <b>SL:</b> <span class="val-red">{signal['sl']}</span>
                </div>
                <div>
                    <b>MT5 Spread:</b> {signal['spread']} pts<br>
                    <b>MT5 RSI:</b> {signal['rsi']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📲 Broadcast Signal to Telegram", use_container_width=True):
            success, resp = engine.broadcast_telegram_signal(bot_token, chat_id, signal)
            if success:
                st.success("Signal successfully broadcasted to Telegram!")
            else:
                st.error(f"Failed to send Telegram signal: {resp}")
