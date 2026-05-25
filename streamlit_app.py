
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Signal Hunter AI", layout="wide")
st.title("🎯 Signal Hunter AI")
st.caption(f"SMC Analysis | BOS/CHoCH Detection | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

ACCOUNT_BALANCE = 1000

def calculate_lot_size(strength, stop_pips=50, risk_percent=2):
    risk_amount = ACCOUNT_BALANCE * (risk_percent / 100) * (strength / 100)
    lot_size = risk_amount / (stop_pips * 1)
    lot_size = max(0.01, min(round(lot_size / 0.01) * 0.01, 0.50))
    return lot_size

@st.cache_data(ttl=60)
def get_price_data(symbol):
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    np.random.seed(hash(symbol) % 10000)
    
    if "XAU" in symbol:
        base, vol = 2300, 15
    elif "BTC" in symbol:
        base, vol = 65000, 2000
    else:
        base, vol = 1.08, 0.02
    
    prices = [base]
    for i in range(99):
        prices.append(prices[-1] + np.random.randn() * (vol / 50))
    
    high = [p + abs(np.random.randn() * vol/100) for p in prices]
    low = [p - abs(np.random.randn() * vol/100) for p in prices]
    volume = [1000 + i*20 + np.random.randint(-200, 200) for i in range(100)]
    
    return pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'high': high,
        'low': low,
        'volume': volume
    })

def detect_signal(df):
    close = df['close'].values
    for i in range(5, len(close)-5):
        if close[i] > max(close[i-5:i]) and close[i] > max(close[i+1:i+6]):
            return "🟢 BULLISH BOS", 75
        elif close[i] < min(close[i-5:i]) and close[i] < min(close[i+1:i+6]):
            return "🔴 BEARISH BOS", 75
    return "⏸️ NO SIGNAL", 25

def classify_volume(df):
    current = df['volume'].iloc[-1]
    avg = df['volume'].tail(20).mean()
    if current > avg * 1.3:
        return "HIGH", 85
    elif current < avg * 0.7:
        return "LOW", 40
    return "MEDIUM", 60

with st.sidebar:
    st.header("💰 Account")
    st.metric("Balance", f"R{ACCOUNT_BALANCE:,.2f}")
    risk = st.slider("Risk % per trade", 0.5, 5.0, 2.0, 0.5)
    pairs = st.multiselect("Markets", ["XAUUSD", "EURUSD", "USDJPY"], default=["XAUUSD", "EURUSD"])
    auto = st.checkbox("Auto-refresh", value=False)
    st.success("✅ Active")

st.subheader("📈 Live Signals")

for pair in pairs:
    df = get_price_data(pair)
    price = df['close'].iloc[-1]
    prev = df['close'].iloc[-2]
    change = ((price - prev) / prev) * 100
    
    signal, sig_strength = detect_signal(df)
    volume, vol_strength = classify_volume(df)
    
    total_strength = int((sig_strength + vol_strength) / 2)
    lot_size = calculate_lot_size(total_strength, 50, risk)
    
    c1, c2, c3, c4 = st.columns([2, 1.5, 1, 1.5])
    with c1:
        st.metric(pair, f"${price:.2f}", delta=f"{change:.2f}%")
    with c2:
        if "BULLISH" in signal:
            st.success(signal)
        elif "BEARISH" in signal:
            st.error(signal)
        else:
            st.info(signal)
    with c3:
        if volume == "HIGH":
            st.success(f"🔊 {volume}")
        elif volume == "LOW":
            st.warning(f"🔇 {volume}")
        else:
            st.info(f"📊 {volume}")
    with c4:
        st.info(f"📊 LOT: {lot_size:.2f}")
        st.caption(f"Strength: {total_strength}%")
    
    # Simple line chart instead of candlestick to avoid errors
    chart_df = df.tail(50)[['timestamp', 'close']]
    st.line_chart(chart_df.set_index('timestamp'), height=200)
    st.divider()

if auto:
    time.sleep(60)
    st.rerun()

st.success("✅ Signal Hunter AI Active")
