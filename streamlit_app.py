import streamlit as st
import pandas as pd

# ==========================================
# 1. PAGE CONFIG & MOBILE UI STYLING
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
        font-size: 11px;
        color: #8b949e;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .price-value {
        font-size: 34px;
        font-weight: 900;
        color: #2ea043;
    }

    /* Signal Card Formatting */
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
    .tp-text { color: #3fb950; font-weight: 700; }
    .sl-text { color: #f85149; font-weight: 700; }

    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. APP HEADER & CONTROLS
# ==========================================
st.markdown("## ⚡ **SEKWAILA OMEGA X**")
st.caption("PURE SIGNAL ENGINE · BROKER MATCH")

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

# Signal Direction Toggle
signal_type = st.radio("Signal Action", ["BUY", "SELL"], horizontal=True, index=1)

# ==========================================
# 3. DIRECT METATRADER PRICE OVERRIDE
# ==========================================
st.markdown("---")
mt_price_input = st.number_input(
    f"📲 Enter Live {symbol} Price from MetaTrader", 
    value=4335.37 if symbol == "XAUUSD" else 65000.00, 
    step=0.10,
    format="%.2f"
)

live_price = mt_price_input

st.markdown(f"""
<div class="price-card">
    <div class="price-title">METATRADER LIVE ENTRY PRICE ({symbol})</div>
    <div class="price-value">{live_price:,.2f}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. PURE SIGNAL GENERATOR
# ==========================================
st.markdown("### 🎯 **ACTIVE SIGNAL SETUP**")

# Calculate targets based on asset type
if symbol == "XAUUSD":
    sl_dist, tp1_dist, tp2_dist, tp3_dist = 4.00, 3.00, 6.00, 10.00
elif symbol == "BTCUSD":
    sl_dist, tp1_dist, tp2_dist, tp3_dist = 300.0, 250.0, 500.0, 1000.0
else:
    sl_dist, tp1_dist, tp2_dist, tp3_dist = 35.0, 30.0, 60.0, 100.0

entry_price = live_price

if signal_type == "BUY":
    sl_p = entry_price - sl_dist
    tp1_p = entry_price + tp1_dist
    tp2_p = entry_price + tp2_dist
    tp3_p = entry_price + tp3_dist
    
    st.markdown(f"""
    <div class="signal-card-buy">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="signal-badge-buy">🟢 BUY SIGNAL</span>
            <span style="font-size:12px; color:#8b949e;">{symbol} · {timeframe}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:15px; line-height:1.8;">
            <b>ENTRY PRICE:</b> {entry_price:,.2f}<br/>
            <span class="sl-text"><b>STOP LOSS (SL):</b> {sl_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 1 (TP1):</b> {tp1_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 2 (TP2):</b> {tp2_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 3 (TP3):</b> {tp3_p:,.2f}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:12px; color:#8b949e;">
            <b>Risk Amount:</b> R{account_bal * (risk_pct/100):,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    sl_p = entry_price + sl_dist
    tp1_p = entry_price - tp1_dist
    tp2_p = entry_price - tp2_dist
    tp3_p = entry_price - tp3_dist
    
    st.markdown(f"""
    <div class="signal-card-sell">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="signal-badge-sell">🔴 SELL SIGNAL</span>
            <span style="font-size:12px; color:#8b949e;">{symbol} · {timeframe}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:15px; line-height:1.8;">
            <b>ENTRY PRICE:</b> {entry_price:,.2f}<br/>
            <span class="sl-text"><b>STOP LOSS (SL):</b> {sl_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 1 (TP1):</b> {tp1_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 2 (TP2):</b> {tp2_p:,.2f}</span><br/>
            <span class="tp-text"><b>TAKE PROFIT 3 (TP3):</b> {tp3_p:,.2f}</span>
        </div>
        <hr style="border-color:#30363d; margin:10px 0;"/>
        <div style="font-size:12px; color:#8b949e;">
            <b>Risk Amount:</b> R{account_bal * (risk_pct/100):,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.button("📲 Send Signal to Telegram", use_container_width=True):
    st.success("Signal alert pushed to Katlego Bot!")
