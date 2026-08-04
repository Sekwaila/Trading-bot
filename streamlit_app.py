"""
streamlit_app.py – SEKWAILA OMEGA X V6
Professional Dashboard – No Auto‑Execution
Uses yfinance + SQLite for history.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import time
import yfinance as yf

# Import the signal engine (must be in the same folder)
from signal_engine import engine, Config

# ------------------ CONFIG ------------------
APP_NAME = "SEKWAILA OMEGA X"
VERSION = "6.0"
SYMBOLS = ["BTCUSD", "XAUUSD", "EURUSD"]
TIMEFRAME = "1H"  # can be changed via sidebar

# ------------------ DATABASE (SQLite) ------------------
DB_PATH = "signals.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            signal TEXT,
            confidence REAL,
            entry REAL,
            stop_loss REAL,
            tp1 REAL,
            tp2 REAL,
            tp3 REAL,
            timeframe TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_signal(symbol, signal, confidence, entry, sl, tp1, tp2, tp3, timeframe):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (timestamp, symbol, signal, confidence, entry, stop_loss, tp1, tp2, tp3, timeframe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), symbol, signal, confidence, entry, sl, tp1, tp2, tp3, timeframe))
    conn.commit()
    conn.close()

def get_signals():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC", conn)
    conn.close()
    return df

init_db()

# ------------------ DATA FETCHING (yfinance) ------------------
def fetch_live_data(symbol, timeframe="1H", bars=200):
    ticker_map = {
        "EURUSD": "EURUSD=X",
        "XAUUSD": "GC=F",
        "BTCUSD": "BTC-USD",
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
        st.warning(f"Yahoo Finance error: {e}. Using demo data.")
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

def get_current_price(df):
    if df is not None and len(df) > 0:
        return df['close'].iloc[-1]
    return None

# ------------------ SIGNAL PROCESSING ------------------
def process_symbol(symbol, timeframe, account_balance=10000):
    df = fetch_live_data(symbol, timeframe)
    if df is None or len(df) < 50:
        return None, None, "Insufficient data"

    config = Config({
        "account_balance": account_balance,
        "symbol_metadata": {
            symbol: {
                "pip_value": 1.0 if symbol not in ["XAUUSD", "BTCUSD"] else 0.01,
                "tick_size": 0.0001 if symbol not in ["XAUUSD", "BTCUSD"] else 0.01,
                "contract_size": 100000 if symbol not in ["XAUUSD", "BTCUSD"] else 100,
                "lot_step": 0.01,
                "min_lot": 0.01
            }
        }
    })
    from signal_engine import SignalEngine
    local_engine = SignalEngine(config)
    try:
        signal = local_engine.generate_signal(df, symbol=symbol, timeframe=timeframe)
        return df, signal, None
    except Exception as e:
        return df, None, str(e)

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #FFD700, #FF6B00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1rem 0; }
    .signal-buy { background: #00FF88; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; display: inline-block; }
    .signal-sell { background: #FF4444; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; display: inline-block; }
    .grade-Aplus { color: #FFD700; font-weight: 700; }
    .grade-A { color: #00FF88; font-weight: 700; }
    .grade-B { color: #00BFFF; font-weight: 700; }
    .grade-C { color: #FFA500; font-weight: 700; }
    .grade-D { color: #FF4444; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙ Settings")
    auto_refresh = st.toggle("Auto Refresh", True)
    refresh_seconds = st.slider("Refresh Interval (s)", 5, 300, 30)
    timeframe = st.selectbox("Timeframe", ["1M","5M","15M","30M","1H","4H","1D"], index=4)
    account_balance = st.number_input("Account Balance ($)", 1000, 1000000, 10000, 1000)
    st.success("🟢 Scanner Online")

# Header
st.markdown(f'<div class="main-header">📈 {APP_NAME}</div>', unsafe_allow_html=True)
st.caption(f"Version {VERSION} | Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")

# Live Market Prices
st.subheader("📊 Live Market")
price_data = {}
signal_data = {}
cols = st.columns(len(SYMBOLS))
for idx, symbol in enumerate(SYMBOLS):
    with cols[idx]:
        df, signal, error = process_symbol(symbol, timeframe, account_balance)
        price_data[symbol] = df
        signal_data[symbol] = signal
        price = get_current_price(df)
        if price:
            st.metric(label=symbol, value=f"{price:.2f}" if symbol != "BTCUSD" else f"{price:,.0f}")
        else:
            st.metric(label=symbol, value="N/A")

# Live Signals
st.subheader("🎯 Live Signals")
cols = st.columns(len(SYMBOLS))
for idx, symbol in enumerate(SYMBOLS):
    with cols[idx]:
        signal = signal_data.get(symbol)
        if signal:
            direction = signal.get('signal', 'N/A')
            confidence = signal.get('confidence', 0)
            grade = signal.get('grade', 'D')
            entry = signal.get('entry', 0)
            sl = signal.get('sl', 0)
            tp1 = signal.get('tp1', 0)
            tp2 = signal.get('tp2', 0)
            tp3 = signal.get('tp3', 0)
            st.markdown(f"""
            <div style="background:#1E1E2E; border-radius:10px; padding:1rem; border:1px solid #333;">
                <div style="font-size:1.2rem; font-weight:600;">{symbol}</div>
                <div style="font-size:2rem; margin:0.5rem 0;">
                    <span class="{'signal-buy' if direction == 'BUY' else 'signal-sell'}">{direction}</span>
                </div>
                <div>Confidence: {confidence:.1f}%</div>
                <div>Grade: <span class="grade-{grade}">{grade}</span></div>
                <div style="font-size:0.8rem; color:#888; margin-top:0.5rem;">
                    Entry: {entry:.5f}<br>SL: {sl:.5f}<br>TP1: {tp1:.5f}<br>TP2: {tp2:.5f}<br>TP3: {tp3:.5f}
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Save to database
            save_signal(symbol, direction, confidence, entry, sl, tp1, tp2, tp3, timeframe)
        else:
            st.markdown(f"""
            <div style="background:#1E1E2E; border-radius:10px; padding:1rem; border:1px solid #333; text-align:center; color:#666;">
                <div style="font-size:1.2rem; font-weight:600;">{symbol}</div>
                <div style="font-size:1rem; margin:0.5rem 0;">No signal</div>
            </div>
            """, unsafe_allow_html=True)

# Signal History
st.subheader("📜 Signal History")
history = get_signals()
if history.empty:
    st.info("No signals saved yet.")
else:
    st.dataframe(history.drop('id', axis=1), use_container_width=True, hide_index=True)

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

# Auto-refresh (polling)
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

st.caption(f"{APP_NAME} v{VERSION} • Professional Trading Dashboard")
