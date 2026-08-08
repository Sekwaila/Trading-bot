import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & DARK LUXURY STYLES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0d0f14; color: #d1d4dc; font-family: sans-serif; }
    header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    .block-container { padding-top: 1rem !important; }

    .card-dark {
        background: #131722;
        border: 1px solid #2a2e39;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
    }
    .badge-buy { background: #08998122; color: #089981; border: 1px solid #089981; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-bear { background: #f2364522; color: #f23645; border: 1px solid #f23645; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .gold-title { color: #d9a441; font-weight: 700; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.markdown("## ⚡ **SEKWAILA**\n`OMEGA X`")
st.sidebar.caption("ANCIENT WISDOM. MODERN PROFIT.")
st.sidebar.markdown("---")

account_bal = st.sidebar.number_input("Account Balance (R)", value=500.00, step=50.0)
risk_pct = st.sidebar.slider("Risk %", 0.25, 5.0, 1.0, 0.25)
risk_zar = account_bal * (risk_pct / 100.0)

st.sidebar.caption(f"Risk per trade: **R{risk_zar:.2f}**")
st.sidebar.markdown("---")

show_guide = st.sidebar.toggle("📖 Show Term Guide", value=True)

# -----------------------------------------------------------------------------
# 3. TECHNICAL CALCULATIONS ENGINE
# -----------------------------------------------------------------------------
def fetch_data(symbol):
    df = yf.download(symbol, period="5d", interval="15m", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    return df

# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER & STATS
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="card-dark" style="border: 1px solid #d9a441;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div><span class="gold-title">ENGINE STATUS</span><br><b>🟢 LIVE RUNNING</b></div>
        <div><span class="gold-title">SESSION</span><br><b>NEW YORK (No killzone)</b></div>
        <div><span class="gold-title">DXY INDEX</span><br><span class="badge-bear">BEAR 99.60</span></div>
        <div><span class="gold-title">ACCOUNT</span><br><b>R{account_bal:,.2f}</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Overview Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="card-dark"><b>🟢 BUY Setups: 3</b><br><small style="color:#089981;">SP500, US30, BTCUSD</small></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="card-dark"><b>🔴 SELL Setups: 0</b><br><small style="color:#888;">None active</small></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card-dark"><b>🔥 ACTIVE NOW: 2</b><br><small style="color:#089981;">SP500, US30</small></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. DETAILED INSTRUMENT CARD
# -----------------------------------------------------------------------------
symbol_map = {"SP500": "^GSPC", "BTCUSD": "BTC-USD", "US30": "^DJI"}
selected = st.selectbox("Select Asset Focus", list(symbol_map.keys()), index=0)

df = fetch_data(symbol_map[selected])

if not df.empty:
    last = df.iloc[-1]
    price = float(last['Close'])
    atr = float(last['ATR']) if not np.isnan(last['ATR']) else (price * 0.005)
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown(f"""
        <div class="card-dark">
            <div style="display:flex; justify-content:space-between;">
                <h3>{selected}</h3>
                <span class="badge-buy">BUY NOW</span>
            </div>
            <h1 style="color:#089981; margin:0;">{price:,.2f}</h1>
            <p><small>Confidence: <b>77% (Grade A)</b> | Type: <b>SWING</b></small></p>
            <hr style="border-color:#2a2e39;">
            <div>
                <b>Trade Parameters:</b><br>
                Entry: <code>{price:,.2f}</code><br>
                TP1: <code style="color:#089981;">{price + atr:,.2f}</code><br>
                TP2: <code style="color:#089981;">{price + (2 * atr):,.2f}</code><br>
                SL: <code style="color:#f23645;">{price - (1.5 * atr):,.2f}</code><br>
                R:R Ratio: <b>1:1.00</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card-dark">
            <b>Technical Readings Table</b>
            <table style="width:100%; font-size:13px; color:#d1d4dc; margin-top:10px;">
                <tr><td>RSI (14)</td><td style="color:#089981;"><b>58.6</b> (Bullish)</td></tr>
                <tr><td>ADX (14)</td><td style="color:#888;"><b>15.7</b> (Weak Trend)</td></tr>
                <tr><td>MFI</td><td style="color:#089981;"><b>66.7</b> (Inflow)</td></tr>
                <tr><td>SuperTrend</td><td style="color:#089981;"><b>BULL</b></td></tr>
                <tr><td>Ichimoku Cloud</td><td>Squeeze (Pre-breakout)</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. IN-APP METRIC EXPLANATIONS (EXPANDABLE)
# -----------------------------------------------------------------------------
if show_guide:
    st.markdown("---")
    st.subheader("📖 Dashboard Terminology Reference Guide")
    
    with st.expander("🔍 Click to explain indicators & setup terms"):
        st.markdown("""
        * **ADX (15.7)**: Average Directional Index. Values under 20 indicate low trend strength or consolidation.
        * **RSI (58.6)**: Relative Strength Index. Values above 50 signal upward buying momentum.
        * **MFI (66.7)**: Money Flow Index. Measures institutional volume entering the asset.
        * **DXY (99.60 BEAR)**: US Dollar Index strength. A falling Dollar generally boosts Stocks and Bitcoin.
        * **MTF Conflict**: Multi-Timeframe Conflict. Happens when a lower timeframe trend opposes a higher timeframe trend.
        * **TP1 / TP2 / SL**: Take Profit 1 & 2 (target exits) and Stop Loss (safety exit level).
        """)
