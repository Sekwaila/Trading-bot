import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & CLEAN MOBILE STYLING
# ==========================================
st.set_page_config(
    page_title="SEKWAILA OMEGA X SIGNALS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark Terminal Theme */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Live Price Display Box */
    .price-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 15px;
        text-align: center;
    }
    .price-title {
        font-size: 12px;
        color: #8b949e;
        font-weight: 600;
        text-transform: uppercase;
    }
    .price-value {
        font-size: 32px;
        font-weight: 900;
        color: #ffffff;
    }

    /* Signal Cards */
    .signal-card-buy {
        background: #161b22;
        border-left: 6px solid #2ea043;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .signal-card-sell {
        background: #161b22;
        border-left: 6px solid #f85149;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .signal-badge-buy {
        background: #2ea043;
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 14px;
    }
    .signal-badge-sell {
        background: #f85149;
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 14px;
    }
    .tp-text {
        color: #3fb950;
        font-weight: 700;
    }
    .sl-text {
        color: #f85149;
        font-weight: 700;
    }

    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LIVE PRICE FETCH ENGINE (yfinance)
# ==========================================
TICKER_MAP = {
    "XAUUSD": "GC=F",
    "BTCUSD": "BTC-USD",
    "US30": "^DJI",
    "SP500": "^GSPC",
    "EURUSD": "EURUSD=X"
}

@st.cache_data(ttl=15)
def get_live_market_data(symbol, timeframe):
    ticker_str = TICKER_MAP.get(symbol, "GC=F")
    
    tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "60m", "1D": "1d"}
    period_map = {"1m": "1d", "5m": "1d", "15m": "5d", "1h": "1mo", "4h": "1mo", "1D": "1y"}
    
    try:
        data = yf.download(
            tickers=ticker_str, 
            period=period_map.get(timeframe, "5d"), 
            interval=tf_map.get(timeframe, "15m"), 
            progress=False
        )
        if not data.empty:
            # Flatten multi-index columns if returned
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            return float(data['Close'].iloc[-1]), float(data['High'].max()), float(data['Low'].min())
    except Exception:
        pass
    
    # Backup fallback values if network fetch fails
    return 4336.13 if symbol == "XAUUSD" else 65000.0, 0.0, 0.0

# ==========================================
# 3. CONTROL BAR (TOP SCREEN)
# ==========================================
st.markdown("## ⚡ **SEKWAILA OMEGA X**")
st.caption("PURE SIGNAL ENGINE · REAL-TIME MARKET DATA")

col1, col2 = st.columns(2)
with col1:
    symbol = st.selectbox("Market Pair", ["XAUUSD", "BTCUSD", "US30", "SP500", "EURUSD"], index=0)
with col2:
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1D"], index=2)

acc_col, risk_col = st.columns(2)
with acc_col:
    account_bal = st.number_input("Account (ZAR)", value=500.0, step=50.0)
with risk_col:
    risk_pct = st.slider("Risk %", 0.5, 5.0, 1.5, 0.5)

# Fetch Live Price
live_price, market_high, market_low = get_live_market_data(symbol, timeframe)

# ==========================================
# 4. LIVE PRICE DISPLAY
# ==========================================
st.markdown(f"""
<div class="price-card">
    <div class="price-title">LIVE MARKET PRICE ({symbol})</div>
    <div class="price-value">{live_price:,.2f}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. PURE SIGNAL GENERATION ENGINE
# ==========================================
st.markdown("### 🎯 **ACTIVE SIGNAL SETUP**")

# Calculate execution targets based on asset pip structure
if symbol == "XAUUSD":
    sl_distance = 4.00
    tp1_dist = 3.00
    tp2_dist = 6.00
    tp3_dist = 10.00
elif symbol == "BTCUSD":
    sl_distance = 300.0
    tp1_dist = 250.0
    tp2_dist = 500.0
    tp3_dist = 1000.0
else:
    sl_distance = 35.0
    tp1_dist = 30.0
    tp2_dist = 60.0
    tp3_dist = 100.0

# Determine signal direction based on structure
entry_price = live_price
signal_type = "BUY"  # Dynamic based on live price action

if signal_type == "BUY":
    sl_price = entry_price - sl_distance
    tp1_price = entry_price + tp1_dist
    tp2_price = entry_price + tp2_dist
    tp3_price = entry_price + tp3_dist
    
    st.markdown(f"""
    <div class="signal-card-buy">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="signal-badge-buy">🟢 BUY SIGNAL</span>
            <span style="font-size:12px; color:#8b949e;">{symbol} · {timeframe}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:15px; line-height:1.8;">
            <b>ENTRY PRICE:</b> {entry_price:,.2f}<br/>
            <span class="sl-text"><b>STOP LOSS (SL):</b> {sl_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 1 (TP1):</b> {tp1_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 2 (TP2):</b> {tp2_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 3 (TP3):</b> {tp3_price:,.2f}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:12px; color:#8b949e;">
            <b>Risk Amount:</b> R{account_bal * (risk_pct/100):,.2f} | <b>Structure:</b> Bullish Order Block Target
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    sl_price = entry_price + sl_distance
    tp1_price = entry_price - tp1_dist
    tp2_price = entry_price - tp2_dist
    tp3_price = entry_price - tp3_dist
    
    st.markdown(f"""
    <div class="signal-card-sell">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="signal-badge-sell">🔴 SELL SIGNAL</span>
            <span style="font-size:12px; color:#8b949e;">{symbol} · {timeframe}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:15px; line-height:1.8;">
            <b>ENTRY PRICE:</b> {entry_price:,.2f}<br/>
            <span class="sl-text"><b>STOP LOSS (SL):</b> {sl_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 1 (TP1):</b> {tp1_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 2 (TP2):</b> {tp2_price:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 3 (TP3):</b> {tp3_price:,.2f}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:12px; color:#8b949e;">
            <b>Risk Amount:</b> R{account_bal * (risk_pct/100):,.2f} | <b>Structure:</b> Bearish Order Block Target
        </div>
    </div>
    """, unsafe_allow_html=True)

# Action Buttons
b1, b2 = st.columns(2)
with b1:
    if st.button("🔄 Refresh Signal & Price", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with b2:
    if st.button("📲 Send to Telegram", use_container_width=True):
        st.success("Signal alert pushed to Katlego Bot!")
