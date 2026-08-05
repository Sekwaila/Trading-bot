"""
SEKWAILA OMEGA X v6 – Professional Dashboard
Optimised for minimal API usage, robust duplicate prevention, and auto‑quota reset.
Now with a Yahoo Finance fallback and a persistent SQLite candle cache so the
dashboard degrades gracefully instead of going fully dark when Twelve Data
caps out.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time
import sqlite3

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ------------------ CONFIG ------------------
APP_NAME = "SEKWAILA OMEGA X"
VERSION = "6.1"

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

# Yahoo Finance uses different tickers entirely. "XAUUSD=X" (the forex-style
# spot proxy) turned out unreliable for intraday data in practice — confirmed
# empirically (returned no candles while BTC-USD/EURUSD=X worked fine in the
# same fetch cycle). Using "GC=F" (COMEX gold futures) instead, which Yahoo
# populates far more consistently for 60m/15m intervals. Futures prices track
# spot gold closely enough for signal-generation purposes, though they can
# diverge slightly (contango/backwardation, contract rollover dates) — worth
# knowing if entry prices look a few dollars off from your broker's spot feed.
YFINANCE_MAP = {
    "XAU/USD": "GC=F",
    "BTC/USD": "BTC-USD",
    "EUR/USD": "EURUSD=X",
}

TIMEFRAME = "1H"

# ------------------ API KEY (safe) ------------------
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
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_signal
        ON signals (symbol, signal, entry, stop_loss, tp1)
    """)

    # Persistent candle cache — survives app restarts, used as a last-resort
    # fallback if both Twelve Data and Yahoo Finance fail on a given cycle.
    c.execute("""
        CREATE TABLE IF NOT EXISTS candle_cache (
            symbol TEXT,
            timeframe TEXT,
            time TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            fetched_at TEXT,
            PRIMARY KEY (symbol, timeframe, time)
        )
    """)

    # Small key/value table for state that needs to survive a full app
    # restart, not just a rerun within the same session — quota_exceeded
    # in st.session_state alone resets if the browser session is lost,
    # which could cause Twelve Data to get hit again before it should.
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_meta(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM app_meta WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_meta(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def cache_candles_to_db(symbol, timeframe, df):
    if df is None or df.empty:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fetched_at = datetime.now().isoformat()
    rows = [
        (
            symbol, timeframe, pd.Timestamp(idx).isoformat(),
            float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]),
            float(row.get("volume", 0)), fetched_at,
        )
        for idx, row in df.iterrows()
    ]
    c.executemany("""
        INSERT OR REPLACE INTO candle_cache
        (symbol, timeframe, time, open, high, low, close, volume, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()

def load_cached_candles(symbol, timeframe, bars=200):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT time, open, high, low, close, volume FROM candle_cache
        WHERE symbol = ? AND timeframe = ?
        ORDER BY time DESC LIMIT ?
    """, conn, params=(symbol, timeframe, bars))
    conn.close()
    if df.empty:
        return df
    df = df.sort_values("time")
    df["spread"] = (df["high"] - df["low"]) * 0.001
    df.index = pd.to_datetime(df["time"])
    return df

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

# ------------------ QUOTA TRACKING with auto‑reset (session + persisted) ------------------
if "quota_exceeded" not in st.session_state:
    # Seed from DB, not just a bare default, so a fresh session doesn't
    # immediately re-hit Twelve Data if a prior session already tripped
    # the quota within the last 24h.
    st.session_state.quota_exceeded = get_meta("quota_exceeded", "0") == "1"
if "quota_reset_time" not in st.session_state:
    stored_reset = get_meta("quota_reset_time", "")
    st.session_state.quota_reset_time = datetime.fromisoformat(stored_reset) if stored_reset else None

def _set_quota_exceeded():
    st.session_state.quota_exceeded = True
    st.session_state.quota_reset_time = datetime.now() + timedelta(hours=24)
    set_meta("quota_exceeded", "1")
    set_meta("quota_reset_time", st.session_state.quota_reset_time.isoformat())

def _clear_quota_exceeded():
    st.session_state.quota_exceeded = False
    st.session_state.quota_reset_time = None
    set_meta("quota_exceeded", "0")
    set_meta("quota_reset_time", "")

# Auto‑reset quota after 24 hours, whether the flag came from this session
# or was seeded from a previous one via the DB.
if (
    st.session_state.quota_exceeded
    and st.session_state.quota_reset_time
    and datetime.now() >= st.session_state.quota_reset_time
):
    _clear_quota_exceeded()

# ------------------ TWELVE DATA FETCH ------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_from_twelvedata(symbol, timeframe=TIMEFRAME, bars=200):
    """Returns a DataFrame, or an empty DataFrame on any failure. Sets the
    quota-exceeded state as a side effect if that's what happened."""
    if st.session_state.quota_exceeded:
        return pd.DataFrame()

    td_symbol = SYMBOL_MAP.get(symbol, symbol)
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
            "symbol": td_symbol,
            "interval": interval,
            "outputsize": bars,
            "apikey": TWELVE_API_KEY
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()

        message = str(data.get("message", "")).lower()
        if (
            data.get("code") == 429
            or "api credits" in message
            or "quota" in message
        ):
            _set_quota_exceeded()
            return pd.DataFrame()

        if data.get("status") == "error":
            st.warning(f"Twelve Data error for {symbol}: {data.get('message', 'Unknown')}")
            return pd.DataFrame()

        if "values" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "time"})

        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        else:
            df["volume"] = 0

        df.dropna(subset=["open", "high", "low", "close"], inplace=True)
        if df.empty:
            return pd.DataFrame()

        df["spread"] = (df["high"] - df["low"]) * 0.001
        df = df.sort_values("time")
        df.index = pd.to_datetime(df["time"])
        return df

    except Exception as e:
        st.warning(f"Twelve Data candle error for {symbol}: {e}")
        return pd.DataFrame()

# ------------------ YAHOO FINANCE FALLBACK ------------------
def fetch_from_yfinance(symbol, timeframe=TIMEFRAME, bars=200):
    """Best-effort fallback when Twelve Data is unavailable. Returns an
    empty DataFrame on any failure — never raises, since this already IS
    the fallback path."""
    if not YFINANCE_AVAILABLE:
        return pd.DataFrame()

    ticker = YFINANCE_MAP.get(symbol)
    if not ticker:
        return pd.DataFrame()

    # yfinance has no native 4H interval — same constraint as the rest of
    # this project's data handling. Pull 60m and resample.
    yf_interval_map = {"15M": "15m", "30M": "30m", "1H": "60m", "4H": "60m", "1D": "1d"}
    interval = yf_interval_map.get(timeframe, "60m")
    period = "1y" if interval == "1d" else "60d"

    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data is None or data.empty:
            return pd.DataFrame()

        # yfinance sometimes returns MultiIndex columns for a single ticker
        # depending on version — flatten defensively.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        data = data.rename(columns={
            "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
        })
        df = data[["open", "high", "low", "close", "volume"]].copy()
        df.index.name = "time"
        df = df.reset_index()

        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df.dropna(subset=["open", "high", "low", "close"], inplace=True)
        if df.empty:
            return pd.DataFrame()

        if timeframe == "4H":
            df = (
                df.set_index("time")
                .resample("4h")
                .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
                .dropna()
                .reset_index()
            )

        df["spread"] = (df["high"] - df["low"]) * 0.001
        df = df.sort_values("time").tail(bars)
        df.index = pd.to_datetime(df["time"])
        return df

    except Exception as e:
        st.warning(f"Yahoo Finance fallback failed for {symbol}: {e}")
        return pd.DataFrame()

# ------------------ COMBINED FETCH (Twelve Data -> Yahoo -> stale cache) ------------------
# TTL raised from 5 min to 15 min — cuts Twelve Data call volume by ~3x for
# the same auto-refresh behavior. Combined with the slower default refresh
# interval below, this is the main lever on daily quota burn.
@st.cache_data(ttl=900)
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    df = fetch_from_twelvedata(symbol, timeframe, bars)
    if not df.empty:
        cache_candles_to_db(symbol, timeframe, df)
        return df, "Twelve Data"

    df = fetch_from_yfinance(symbol, timeframe, bars)
    if not df.empty:
        cache_candles_to_db(symbol, timeframe, df)
        return df, "Yahoo Finance (fallback)"

    df = load_cached_candles(symbol, timeframe, bars)
    if not df.empty:
        return df, "Cached (stale)"

    return pd.DataFrame(), "None"

# ------------------ SIGNAL ENGINE IMPORT ------------------
from signals.signal_engine import engine

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

with st.sidebar:
    st.title("⚙ Settings")
    auto_refresh = st.toggle("Auto Refresh", True)
    # Raised the floor and default — 60s was aggressive enough on its own
    # to burn through a free-tier daily quota well before the trading day
    # was over, even before accounting for multiple symbols per cycle.
    refresh_seconds = st.slider("Refresh Interval (s)", 300, 1800, 600, step=60)
    st.success("🟢 Scanner Online")
    st.info(f"Data cached {900 // 60} min | Twelve Data → Yahoo Finance fallback")
    if not YFINANCE_AVAILABLE:
        st.warning("yfinance not installed — fallback disabled. `pip install yfinance`.")
    if st.session_state.quota_exceeded:
        reset_str = st.session_state.quota_reset_time.strftime("%H:%M:%S") if st.session_state.quota_reset_time else "unknown"
        st.error(f"⛔ Twelve Data quota exceeded. Auto-resumes ~{reset_str}. Running on Yahoo Finance / cache until then.")

st.title(f"📈 {APP_NAME}")
st.caption(f"Version {VERSION} | Last Refresh: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
st.divider()

# ------------------ FETCH ALL DATA ONCE ------------------
market_data = {}
data_sources = {}
for symbol in SYMBOLS:
    df, source = fetch_candles(symbol, TIMEFRAME)
    market_data[symbol] = df
    data_sources[symbol] = source

# ------------------ LIVE MARKET ------------------
st.subheader("📊 Live Market")
if market_data:
    cols = st.columns(len(market_data))
    for col, (symbol, df) in zip(cols, market_data.items()):
        with col:
            if not df.empty:
                price = float(df["close"].iloc[-1])
                st.metric(symbol, f"{price:,.2f}")
                source = data_sources.get(symbol, "")
                if source == "Yahoo Finance (fallback)":
                    st.caption("🟡 Yahoo Finance (fallback)")
                elif source == "Cached (stale)":
                    st.caption("🔴 Cached — stale data")
                else:
                    st.caption("🟢 Twelve Data")
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
        history = get_signals()
        st.info(f"{symbol}: New signal saved")
    else:
        st.info(f"{symbol}: Duplicate signal (skipped)")

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
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

st.caption(f"{APP_NAME} v{VERSION} • Powered by Twelve Data + Yahoo Finance")
