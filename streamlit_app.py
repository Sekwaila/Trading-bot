"""
SEKWAILA OMEGA X v6 – Professional Dashboard (Self‑contained)
Handles both slash and dash symbols for Yahoo Finance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import sqlite3

# ------------------ CONFIG ------------------
APP_NAME = "SEKWAILA OMEGA X"
VERSION = "6.0"
# Use display symbols (with slashes) – they will be mapped to Yahoo tickers
SYMBOLS = ["BTC/USD", "XAU/USD", "EUR/USD"]
TIMEFRAME = "1H"

# ------------------ TICKER MAPPING ------------------
# Maps display symbol → Yahoo Finance ticker
TICKER_MAP = {
    "BTC/USD": "BTC-USD",
    "BTCUSD": "BTC-USD",
    "XAU/USD": "GC=F",
    "XAUUSD": "GC=F",
    "EUR/USD": "EURUSD=X",
    "EURUSD": "EURUSD=X",
}

def get_yahoo_ticker(display_symbol):
    """Return the Yahoo ticker for a given display symbol."""
    return TICKER_MAP.get(display_symbol, display_symbol)

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

# ------------------ DATA FETCHING ------------------
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    ticker = get_yahoo_ticker(symbol)
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
        ticker = get_yahoo_ticker(symbol)
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return None

# ------------------ SIGNAL ENGINE (embedded) ------------------
class SignalEngine:
    def __init__(self):
        pass

    def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):
        if len(df) < 50:
            return None

        df = df.copy()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['rsi'] = self._rsi(df['close'], 14)
        df['atr'] = self._atr(df, 14)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Direction from EMA crossover
        if last['ema20'] > last['ema50'] and prev['ema20'] <= prev['ema50']:
            direction = "BUY"
        elif last['ema20'] < last['ema50'] and prev['ema20'] >= prev['ema50']:
            direction = "SELL"
        else:
            # Use RSI
            if last['rsi'] < 30:
                direction = "BUY"
            elif last['rsi'] > 70:
                direction = "SELL"
            else:
                return None

        price = last['close']
        atr = last['atr']

        if direction == "BUY":
            sl = price - atr * 1.5
            tp1 = price + atr * 1.5
            tp2 = price + atr * 2.5
            tp3 = price + atr * 4.0
        else:
            sl = price + atr * 1.5
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4.0

        buffer = 0.01
        if direction == "BUY":
            entry = price - atr * buffer
        else:
            entry = price + atr * buffer

        confidence = 60 + (abs(last['rsi'] - 50) / 50) * 20
        if abs(last['ema20'] - last['ema50']) / last['ema50'] > 0.001:
            confidence += 10
        confidence = min(95, confidence)

        if confidence >= 85:
            grade = "A"
        elif confidence >= 70:
            grade = "B"
        elif confidence >= 60:
            grade = "C"
        else:
            grade = "D"

        lot = 0.01
        risk = lot * abs(entry - sl) * 10000

        signal = {
            "signal": direction,
            "confidence": confidence,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "grade": grade,
            "lot": lot,
            "risk": risk,
            "diagnostics": {
                "rsi": round(last['rsi'], 2),
                "atr": round(atr, 5),
                "ema20": round(last['ema20'], 5),
                "ema50": round(last['ema50'], 5),
            },
            "reasons": [f"EMA crossover {direction}", f"RSI {last['rsi']:.1f}"]
        }
        return signal

    @staticmethod
    def _rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
        return rsi

    @staticmethod
    def _atr(df, period=14):
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean()

engine = SignalEngine()

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
        st.write(f"**RSI:** {diag.get('rsi', 'N/A')}")
        st.write(f"**ATR:** {diag.get('atr', 'N/A')}")
    st.divider()

# History
st.subheader("📜 Signal History")
history = get_signals()
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
