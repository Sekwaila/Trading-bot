"""
SEKWAILA OMEGA X v6 – Professional Dashboard
Optimised for minimal API usage, robust duplicate prevention, and auto‑quota reset.
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

SYMBOLS = [
    "XAU/USD",
    "BTC/USD",
    "EUR/USD"
]

SYMBOL_MAP = {
    "XAU/USD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "EUR/USD": "EUR/USD"
}

TIMEFRAME = "1H"

# ------------------ API KEY (safe) ------------------
TWELVE_API_KEY = st.secrets.get("TWELVEDATA_API_KEY", "")
if not TWELVE_API_KEY:
    st.error("🚨 Missing Twelve Data API key. Please add TWELVEDATA_API_KEY in Streamlit Secrets.")
    st.stop()

# ------------------ QUOTA TRACKING with auto‑reset ------------------
if "quota_exceeded" not in st.session_state:
    st.session_state.quota_exceeded = False
if "quota_reset_time" not in st.session_state:
    st.session_state.quota_reset_time = None

# Auto‑reset quota at midnight or after 24 hours
if (
    st.session_state.quota_exceeded
    and st.session_state.quota_reset_time
    and datetime.now() >= st.session_state.quota_reset_time
):
    st.session_state.quota_exceeded = False
    st.session_state.quota_reset_time = None

# ------------------ DATABASE with unique index ------------------
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
    # Unique constraint to prevent duplicates at database level
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_signal
        ON signals (symbol, signal, entry, stop_loss, tp1)
    """)
    conn.commit()
    conn.close()

def save_signal(symbol, signal, confidence, entry, sl, tp1, tp2, tp3, timeframe):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO signals
            (timestamp, symbol, signal, confidence, entry, stop_loss, tp1, tp2, tp3, timeframe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), symbol, signal, confidence, entry, sl, tp1, tp2, tp3, timeframe))
        conn.commit()
    except Exception as e:
        print(f"DB insert error: {e}")
    finally:
        conn.close()

def get_signals():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC", conn)
    conn.close()
    return df

init_db()

# ------------------ TWELVE DATA API (cached, with quota detection) ------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=300)   # 5 minutes
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    if st.session_state.quota_exceeded:
        return pd.DataFrame()

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

        # Robust quota detection
        message = str(data.get("message", "")).lower()
        if (
            data.get("code") == 429
            or "api credits" in message
            or "quota" in message
        ):
            st.session_state.quota_exceeded = True
            st.session_state.quota_reset_time = datetime.now() + timedelta(hours=24)
            st.error("🚫 Twelve Data daily quota exceeded. Resume tomorrow.")
            return pd.DataFrame()

        if data.get("status") == "error":
            st.error(f"Twelve Data error for {symbol}: {data.get('message', 'Unknown')}")
            return pd.DataFrame()

        if "values" not in data:
            st.warning(f"Twelve Data: no values for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={
            "datetime": "time",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        })

        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        else:
            df["volume"] = 0

        df.dropna(subset=["open", "high", "low", "close"], inplace=True)
        if df.empty:
            st.warning(f"All candle data dropped for {symbol}")
            return pd.DataFrame()

        df["spread"] = (df["high"] - df["low"]) * 0.001
        df = df.sort_values("time")
        df.index = pd.to_datetime(df["time"])
        return df

    except Exception as e:
        st.error(f"Twelve Data candle error for {symbol}: {e}")
        return pd.DataFrame()

# ------------------ SIGNAL ENGINE IMPORT ------------------
from signals.signal_engine import engine

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

with st.sidebar:
    st.title("⚙ Settings")
    auto_refresh = st.toggle("Auto Refresh", True)
    refresh_seconds = st.slider("Refresh Interval (s)", 60, 600, 300)
    st.success("🟢 Scanner Online")
    st.info("Data from Twelve Data (cached 5 min)")
    if st.session_state.quota_exceeded:
        st.error("⛔ Quota exceeded. Resume tomorrow.")

st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION} | Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
st.divider()

# ------------------ FETCH ALL DATA ONCE ------------------
market_data = {}
for symbol in SYMBOLS:
    market_data[symbol] = fetch_candles(symbol, TIMEFRAME)

# ------------------ LIVE MARKET ------------------
st.subheader("📊 Live Market")
if market_data:
    cols = st.columns(len(market_data))
    for col, (symbol, df) in zip(cols, market_data.items()):
        with col:
            if not df.empty:
                price = float(df["close"].iloc[-1])
                st.metric(symbol, f"{price:,.2f}")
            else:
                st.metric(symbol, "N/A")
else:
    st.warning("No market data.")
st.divider()

# ------------------ LIVE SIGNALS ------------------
st.subheader("🎯 Live Signals")

history = get_signals()  # load once

for symbol in SYMBOLS:
    df = market_data.get(symbol)
    if df is None or df.empty:
        st.warning(f"{symbol}: No candle data")
        continue

    signal = engine.generate_signal(df, symbol=symbol)
    if signal is None:
        st.info(f"{symbol}: No signal")
        continue

    # Duplicate detection using rounded values (consistent with DB index)
    last = history[history["symbol"] == symbol]
    duplicate = False
    if not last.empty:
        last = last.iloc[0]
        duplicate = (
            last["signal"] == signal["signal"]
            and round(last["entry"], 5) == round(signal["entry"], 5)
            and round(last["stop_loss"], 5) == round(signal["sl"], 5)
            and round(last["tp1"], 5) == round(signal["tp1"], 5)
        )

    if not duplicate:
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
        # Refresh history after saving (only if we actually inserted)
        history = get_signals()
        st.info(f"{symbol}: New signal saved")
    else:
        st.info(f"{symbol}: Duplicate signal (skipped)")

    # Display
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

# ------------------ HISTORY (display unique) ------------------
st.subheader("📜 Signal History")
if history.empty:
    st.info("No signals saved yet.")
else:
    display_df = history.drop_duplicates(
        subset=["symbol", "signal", "entry", "stop_loss", "tp1"],
        keep="first"
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
st.divider()

# ------------------ STATISTICS (consistent with uniqueness) ------------------
st.subheader("📊 Statistics")
if history.empty:
    a,b,c = st.columns(3)
    a.metric("Signals", 0); b.metric("BUY", 0); c.metric("SELL", 0)
else:
    unique = history.drop_duplicates(
        subset=["symbol", "signal", "entry", "stop_loss", "tp1"]
    )
    buys = len(unique[unique["signal"] == "BUY"])
    sells = len(unique[unique["signal"] == "SELL"])
    total = len(unique)
    a,b,c = st.columns(3)
    a.metric("Unique Signals", total)
    b.metric("BUY", buys)
    c.metric("SELL", sells)

st.divider()

# ------------------ AUTO REFRESH ------------------
if auto_refresh and not st.session_state.quota_exceeded:
    time.sleep(refresh_seconds)
    st.rerun()
elif auto_refresh and st.session_state.quota_exceeded:
    st.warning("Refresh paused – quota exceeded. Will resume after reset.")

st.caption(f"{APP_NAME} v{VERSION} • Powered by Twelve Data")
