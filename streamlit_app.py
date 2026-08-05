"""
SEKWAILA OMEGA X v6 – Professional Dashboard
Uses Twelve Data for real forex & metals prices.
Caching applied to reduce API calls.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import sqlite3

# ------------------ CONFIG ------------------
APP_NAME = "SEKWAILA OMEGA X"
VERSION = "6.0"

# Twelve Data symbols (they use the same format)
SYMBOLS = [
    "XAU/USD",
    "BTC/USD",
    "EUR/USD"
]

# Optional mapping if you need to translate (here it's identity)
SYMBOL_MAP = {
    "XAU/USD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "EUR/USD": "EUR/USD"
}

TIMEFRAME = "1H"

# ------------------ API KEY (using your actual secret name) ------------------
TWELVE_API_KEY = st.secrets.get("TWELVEDATA_API_KEY", "")

if not TWELVE_API_KEY:
    st.error("🚨 Missing Twelve Data API key. Please add TWELVEDATA_API_KEY in Streamlit Secrets.")
    st.stop()

# ------------------ DATABASE ------------------
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

# ------------------ TWELVE DATA API (with caching & error handling) ------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=30)
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    """
    Fetch OHLCV candles from Twelve Data.
    """
    # Use mapped symbol (if needed)
    symbol = SYMBOL_MAP.get(symbol, symbol)

    interval_map = {
        "1H": "1h",
        "4H": "4h",
        "1D": "1day",
        "15M": "15min",
        "30M": "30min"
    }
    interval = interval_map.get(timeframe, "1h")

    try:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": bars,
            "apikey": TWELVE_API_KEY
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()

        # Check for API error
        if data.get("status") == "error":
            st.error(f"Twelve Data error for {symbol}: {data.get('message', 'Unknown error')}")
            return pd.DataFrame()

        if "values" not in data:
            st.warning(f"Twelve Data: no values for {symbol}")
            return generate_demo_data(symbol, bars)

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={
            "datetime": "time",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        })

        # Convert to numeric
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Force float types
        df = df.astype({
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float
        })

        # Add spread column (needed by some engines)
        df["spread"] = (df["high"] - df["low"]) * 0.001

        df = df.sort_values("time")
        df.index = pd.to_datetime(df["time"])
        return df

    except Exception as e:
        st.warning(f"Twelve Data candle error for {symbol}: {e}. Using demo data.")
        return generate_demo_data(symbol, bars)

@st.cache_data(ttl=10)
def get_current_price(symbol):
    """
    Fetch the latest price from Twelve Data.
    """
    symbol = SYMBOL_MAP.get(symbol, symbol)

    try:
        url = "https://api.twelvedata.com/price"
        params = {
            "symbol": symbol,
            "apikey": TWELVE_API_KEY
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()

        if data.get("status") == "error":
            st.error(f"Price error for {symbol}: {data.get('message', 'Unknown error')}")
            return None

        if "price" in data:
            return float(data["price"])
    except Exception as e:
        st.warning(f"Twelve Data price error: {e}")
    return None

# ------------------ DEMO DATA FALLBACK ------------------
def generate_demo_data(symbol, bars=200):
    """Generate synthetic OHLCV data when API fails."""
    np.random.seed(42 if symbol == "EUR/USD" else 43 if symbol == "XAU/USD" else 44)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=bars)
    dates = pd.date_range(start=start_time, end=end_time, periods=bars)
    volatility = {"EUR/USD": 0.0008, "XAU/USD": 3.0, "BTC/USD": 200.0}.get(symbol, 0.001)
    base_price = {"EUR/USD": 1.1000, "XAU/USD": 2400.0, "BTC/USD": 60000.0}.get(symbol, 100.0)
    returns = np.random.randn(bars) * volatility
    price = base_price * np.exp(np.cumsum(returns))
    price = np.maximum(price, base_price * 0.9)
    open_price = price * (1 + np.random.randn(bars) * 0.0002)
    close_price = price * (1 + np.random.randn(bars) * 0.0002)
    high_price = np.maximum(open_price, close_price) + np.abs(np.random.randn(bars) * volatility * 0.5)
    low_price = np.minimum(open_price, close_price) - np.abs(np.random.randn(bars) * volatility * 0.5)
    volume = np.random.randint(100, 1000, bars)
    df = pd.DataFrame({
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': volume,
        'spread': (high_price - low_price) * 0.001
    }, index=dates)
    return df

# ------------------ SIGNAL ENGINE IMPORT ------------------
from signals.signal_engine import engine

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

with st.sidebar:
    st.title("⚙ Settings")
    auto_refresh = st.toggle("Auto Refresh", True)
    refresh_seconds = st.slider("Refresh Interval (s)", 5, 300, 30)
    st.success("🟢 Scanner Online")
    st.info("Data from Twelve Data")

st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION} | Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
st.divider()

# ------------------ LIVE MARKET ------------------
st.subheader("📊 Live Market")
prices = []
for symbol in SYMBOLS:
    price = get_current_price(symbol)
    prices.append({"symbol": symbol, "price": price, "success": price is not None})

if prices:
    cols = st.columns(len(prices))
    for col, item in zip(cols, prices):
        with col:
            if item["success"] and item["price"] is not None:
                st.metric(item["symbol"], f"{item['price']:,.2f}")
            else:
                st.metric(item["symbol"], "N/A")
else:
    st.warning("No market data.")
st.divider()

# ------------------ LIVE SIGNALS ------------------
st.subheader("🎯 Live Signals")

# Get existing signals to avoid duplicate inserts
history = get_signals()

for symbol in SYMBOLS:
    df = fetch_candles(symbol, TIMEFRAME)
    if df.empty:
        st.warning(f"{symbol}: No candle data")
        continue

    signal = engine.generate_signal(df, symbol=symbol)
    if signal is None:
        st.info(f"{symbol}: No signal")
        continue

    # Prevent duplicate identical signals
    if history.empty or \
       history.iloc[0]["symbol"] != symbol or \
       history.iloc[0]["signal"] != signal["signal"]:

        save_signal(
            symbol=symbol,
            signal=signal["signal"],
            confidence=signal["confidence"],
            entry=signal["entry"],
            sl=signal["sl"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            tp3=signal["tp3"],
            timeframe=TIMEFRAME,
        )
        # Update history after insert
        history = get_signals()
    else:
        st.info(f"{symbol}: Duplicate signal, not saved")

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
        st.write(f"**RSI:** {diag.get('rsi', 'N/A')}")
        st.write(f"**ATR:** {diag.get('atr', 'N/A')}")
    st.divider()

# ------------------ HISTORY ------------------
st.subheader("📜 Signal History")
history = get_signals()
if history.empty:
    st.info("No signals saved yet.")
else:
    st.dataframe(history, use_container_width=True, hide_index=True)
st.divider()

# ------------------ STATISTICS ------------------
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

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

st.caption(f"{APP_NAME} v{VERSION} • Powered by Twelve Data")
