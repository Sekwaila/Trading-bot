"""
SEKWAILA OMEGA X v6 – Professional Dashboard
Uses yfinance and the self-contained signal engine.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

from config import APP_NAME, VERSION, SYMBOLS, TIMEFRAME
from database import db
from signal_engine import engine

# ------------------ DATA FETCHING ------------------
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    ticker_map = {
        "EURUSD": "EURUSD=X",
        "XAUUSD": "GC=F",
        "BTCUSD": "BTC-USD",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
    }
    ticker = ticker_map.get(symbol, symbol)
    interval_map = {
        "1M": "1m", "5M": "5m", "15M": "15m", "30M": "30m",
        "1H": "1h", "4H": "4h", "1D": "1d"
    }
    interval = interval_map.get(timeframe, "1h")
    duration_per_bar = {
        "1m": 1/1440, "5m": 5/1440, "15m": 15/1440, "30m": 30/1440,
        "1h": 1/24, "4h": 4/24, "1d": 1
    }.get(interval, 1/24)
    period_days = max(bars * duration_per_bar * 1.5, 1)

    try:
        df = yf.download(ticker, period=f"{period_days:.1f}d", interval=interval, progress=False)
        if df.empty:
            return generate_demo_data(symbol, bars)
        df = df.tail(bars)
        df.index = pd.to_datetime(df.index)
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        df['spread'] = (df['high'] - df['low']) * 0.001
        return df
    except Exception as e:
        st.warning(f"Yahoo Finance error for {symbol}: {e}. Using demo data.")
        return generate_demo_data(symbol, bars)

def generate_demo_data(symbol, bars=200):
    np.random.seed(42 if symbol == "EURUSD" else 43 if symbol == "XAUUSD" else 44)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=bars)
    dates = pd.date_range(start=start_time, end=end_time, periods=bars)
    volatility = {"EURUSD": 0.0008, "XAUUSD": 3.0, "BTCUSD": 200.0}.get(symbol, 0.001)
    base_price = {"EURUSD": 1.1000, "XAUUSD": 2400.0, "BTCUSD": 60000.0}.get(symbol, 100.0)
    returns = np.random.randn(bars) * volatility
    price = base_price * np.exp(np.cumsum(returns))
    price = np.maximum(price, base_price * 0.9)
    open_price = price * (1 + np.random.randn(bars) * 0.0002)
    close_price = price * (1 + np.random.randn(bars) * 0.0002)
    high_price = np.maximum(open_price, close_price) + np.abs(np.random.randn(bars) * volatility * 0.5)
    low_price = np.minimum(open_price, close_price) - np.abs(np.random.randn(bars) * volatility * 0.5)
    volume = np.random.randint(100, 1000, bars)
    spread = volatility * 0.2 + np.random.rand(bars) * volatility * 0.1
    return pd.DataFrame({
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': volume,
        'spread': spread
    }, index=dates)

def get_current_price(symbol):
    try:
        ticker = {"EURUSD": "EURUSD=X", "XAUUSD": "GC=F", "BTCUSD": "BTC-USD"}.get(symbol, symbol)
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return None

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

# Sidebar
with st.sidebar:
    st.title("⚙ Settings")
    auto_refresh = st.toggle("Auto Refresh", True)
    refresh_seconds = st.slider("Refresh Interval (s)", 5, 300, 30)
    st.success("🟢 Scanner Online")

# Header
st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION} | Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
st.divider()

# Live Market
st.subheader("📊 Live Market")
prices = []
for symbol in SYMBOLS:
    price = get_current_price(symbol)
    prices.append({"symbol": symbol, "price": price, "success": price is not None})
if prices:
    cols = st.columns(len(prices))
    for col, item in zip(cols, prices):
        with col:
            if item["success"]:
                st.metric(item["symbol"], f"{item['price']:,.2f}")
            else:
                st.metric(item["symbol"], "N/A")
else:
    st.warning("No market data.")
st.divider()

# Live Signals
st.subheader("🎯 Live Signals")
for symbol in SYMBOLS:
    df = fetch_candles(symbol, TIMEFRAME)
    if df.empty:
        st.warning(f"{symbol}: No candle data")
        continue
    signal = engine.generate_signal(df, symbol=symbol)
    if signal is None:
        st.info(f"{symbol}: No signal")
        continue

    # Save to database
    db.save_signal(
        symbol=symbol,
        signal=signal["signal"],
        confidence=signal["confidence"],
        entry=signal["entry"],
        stop_loss=signal["sl"],
        tp1=signal["tp1"],
        tp2=signal["tp2"],
        tp3=signal["tp3"],
        timeframe=TIMEFRAME,
    )

    # Display card
    c1, c2, c3 = st.columns(3)
    c1.metric(symbol, signal["signal"])
    c2.metric("Entry", signal["entry"])
    c3.metric("Confidence", f"{signal['confidence']}%")
    st.write(f"**Stop Loss:** {signal['sl']}")
    st.write(f"**TP1:** {signal['tp1']}")
    st.write(f"**TP2:** {signal['tp2']}")
    st.write(f"**TP3:** {signal['tp3']}")
    diag = signal.get("diagnostics", {})
    if diag:
        st.write(f"**Regime:** {diag.get('regime', 'N/A')}")
        st.write(f"**ATR:** {diag.get('atr', 'N/A')}")
        st.write(f"**RSI:** {diag.get('rsi', 'N/A')}")
        st.write(f"**ADX:** {diag.get('adx', 'N/A')}")
    st.divider()

# History
st.subheader("📜 Signal History")
history = db.get_signals()
if history.empty:
    st.info("No signals saved yet.")
else:
    st.dataframe(history, use_container_width=True, hide_index=True)
st.divider()

# Statistics
st.subheader("📊 Statistics")
if history.empty:
    a,b,c = st.columns(3)
    a.metric("Signals", 0); b.metric("BUY", 0); c.metric("SELL", 0)
else:
    buys = len(history[history["signal"] == "BUY"])
    sells = len(history[history["signal"] == "SELL"])
    a,b,c = st.columns(3)
    a.metric("Signals", len(history))
    b.metric("BUY", buys)
    c.metric("SELL", sells)

st.divider()

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

st.caption(f"{APP_NAME} v{VERSION} • Professional Trading Dashboard")
