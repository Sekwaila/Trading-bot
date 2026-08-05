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
import sqlite3

# Use the recommended autorefresh component
from streamlit_autorefresh import st_autorefresh

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

YFINANCE_MAP = {
    "XAU/USD": ["XAUUSD=X", "GC=F"],
    "BTC/USD": ["BTC-USD"],
    "EUR/USD": ["EURUSD=X"],
}

MAX_FALLBACK_DEVIATION_PCT = 1.0
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

# ------------------------------------------------
# MODIFIED: save_signal now deletes old entries for the symbol
# so we keep only the latest signal per symbol.
# ------------------------------------------------
def save_signal(symbol, signal, confidence, entry, sl, tp1, tp2, tp3, timeframe):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Remove older signals for this symbol
        c.execute("DELETE FROM signals WHERE symbol = ?", (symbol,))
        # Insert the new one
        c.execute("""
            INSERT INTO signals
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

if (
    st.session_state.quota_exceeded
    and st.session_state.quota_reset_time
    and datetime.now() >= st.session_state.quota_reset_time
):
    _clear_quota_exceeded()

# ------------------ TWELVE DATA FETCH ------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_from_twelvedata(symbol, timeframe=TIMEFRAME, bars=200):
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

# ------------------ PRICE SANITY GUARD ------------------
def _is_price_sane(symbol, timeframe, new_price, max_deviation_pct=MAX_FALLBACK_DEVIATION_PCT):
    last_cached = load_cached_candles(symbol, timeframe, bars=1)
    if last_cached.empty:
        return True, None, None
    last_price = float(last_cached["close"].iloc[-1])
    if last_price == 0:
        return True, last_price, None
    deviation_pct = abs(new_price - last_price) / last_price * 100
    return deviation_pct <= max_deviation_pct, last_price, deviation_pct

# ------------------ YAHOO FINANCE FALLBACK ------------------
def _normalize_yf_dataframe(data, timeframe, bars):
    if data is None or data.empty:
        return pd.DataFrame(), "no data returned (empty response from Yahoo)"

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
        return pd.DataFrame(), "all rows dropped (non-numeric OHLC values)"

    if timeframe == "4H":
        df = (
            df.set_index("time")
            .resample("4h")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna()
            .reset_index()
        )
        if df.empty:
            return pd.DataFrame(), "empty after 4H resample"

    df["spread"] = (df["high"] - df["low"]) * 0.001
    df = df.sort_values("time").tail(bars)
    df.index = pd.to_datetime(df["time"])
    return df, None

def _fetch_one_yfinance_ticker(ticker, timeframe, bars):
    yf_interval_map = {"15M": "15m", "30M": "30m", "1H": "60m", "4H": "60m", "1D": "1d"}
    interval = yf_interval_map.get(timeframe, "60m")
    period = "1y" if interval == "1d" else "60d"

    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        df, reason = _normalize_yf_dataframe(data, timeframe, bars)
        if not df.empty:
            return df, None
        download_reason = reason
    except Exception as e:
        download_reason = f"exception: {e}"

    try:
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        df, reason = _normalize_yf_dataframe(data, timeframe, bars)
        if not df.empty:
            return df, None
        return pd.DataFrame(), f"download() failed ({download_reason}); Ticker().history() also failed ({reason})"
    except Exception as e:
        return pd.DataFrame(), f"download() failed ({download_reason}); Ticker().history() raised: {e}"

def fetch_from_yfinance(symbol, timeframe=TIMEFRAME, bars=200):
    if not YFINANCE_AVAILABLE:
        return pd.DataFrame(), None

    candidates = YFINANCE_MAP.get(symbol, [])
    if isinstance(candidates, str):
        candidates = [candidates]

    for ticker in candidates:
        df, reason = _fetch_one_yfinance_ticker(ticker, timeframe, bars)
        if df.empty:
            st.warning(f"{symbol}: Yahoo ticker {ticker} failed — {reason}")
            continue

        candidate_price = float(df["close"].iloc[-1])
        sane, last_price, deviation_pct = _is_price_sane(symbol, timeframe, candidate_price)
        if not sane:
            st.warning(
                f"{symbol}: Yahoo ticker {ticker} price {candidate_price:,.5f} is "
                f"{deviation_pct:.2f}% away from last trusted price {last_price:,.5f} "
                f"(limit {MAX_FALLBACK_DEVIATION_PCT}%) — rejecting, trying next source."
            )
            continue

        return df, ticker

    return pd.DataFrame(), None

# ------------------ COMBINED FETCH ------------------
@st.cache_data(ttl=900)
def fetch_candles(symbol, timeframe=TIMEFRAME, bars=200):
    df = fetch_from_twelvedata(symbol, timeframe, bars)
    if not df.empty:
        cache_candles_to_db(symbol, timeframe, df)
        return df, "Twelve Data"

    df, ticker_used = fetch_from_yfinance(symbol, timeframe, bars)
    if not df.empty:
        cache_candles_to_db(symbol, timeframe, df)
        return df, f"Yahoo Finance ({ticker_used})"

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

# Show data source summary
sources = []
for sym in SYMBOLS:
    _, src = fetch_candles(sym, TIMEFRAME)  # This will hit cache
    sources.append(src)
if all("Twelve Data" in s for s in sources):
    st.info("🟢 **Market Source:** Twelve Data")
elif any("Yahoo Finance" in s for s in sources):
    st.info("🟡 **Market Source:** Yahoo Finance (fallback)")
else:
    st.info("🔴 **Market Source:** Cached (stale)")

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
                if source.startswith("Yahoo Finance"):
                    st.caption(f"🟡 {source}")
                    if "GC=F" in source:
                        st.caption("⚠ Futures price — may differ from your broker's spot quote")
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

    # Check if we already have a signal for this symbol and if it's identical
    existing = history[history["symbol"] == symbol]
    if not existing.empty:
        last = existing.iloc[0]
        same = (
            last["signal"] == signal["signal"]
            and round(last["entry"], 5) == round(signal["entry"], 5)
            and round(last["stop_loss"], 5) == round(signal["sl"], 5)
            and round(last["tp1"], 5) == round(signal["tp1"], 5)
        )
        if same:
            st.info(f"{symbol}: Signal unchanged (skipped save)")
        else:
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
            st.info(f"{symbol}: Signal updated")
    else:
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

    # Display signal card
    c1, c2, c3 = st.columns(3)
    c1.metric(symbol, signal["signal"])
    c2.metric("Entry", signal["entry"])
    c3.metric("Confidence", f"{signal['confidence']}%")

    # Show grade if available
    grade = signal.get("grade", "N/A")
    st.write(f"**Grade:** {grade}")

    st.write(f"**Stop Loss:** {signal['sl']}")
    st.write(f"**TP1:** {signal['tp1']}")
    st.write(f"**TP2:** {signal['tp2']}")
    st.write(f"**TP3:** {signal['tp3']}")
    diag = signal.get("diagnostics", {})
    if diag:
        st.write(f"**RSI:** {diag.get('rsi', 'N/A')}")
        st.write(f"**ATR:** {diag.get('atr', 'N/A')}")
    st.divider()

# ------------------ HISTORY (display unique, latest only) ------------------
st.subheader("📜 Signal History")
if history.empty:
    st.info("No signals saved yet.")
else:
    # Since we keep only one per symbol, we can just show all, but we keep a dedup just in case.
    display_df = history.drop_duplicates(subset=["symbol"], keep="last")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
st.divider()

# ------------------ STATISTICS (fixed counting) ------------------
st.subheader("📊 Statistics")
if history.empty:
    a,b,c = st.columns(3)
    a.metric("Signals", 0); b.metric("BUY", 0); c.metric("SELL", 0)
else:
    # Count unique symbol+signal pairs (as requested)
    unique = history.drop_duplicates(subset=["symbol", "signal"], keep="first")
    buys = len(unique[unique["signal"] == "BUY"])
    sells = len(unique[unique["signal"] == "SELL"])
    total = len(unique)
    a,b,c = st.columns(3)
    a.metric("Unique Signals", total)
    b.metric("BUY", buys)
    c.metric("SELL", sells)

st.divider()

# ------------------ AUTO REFRESH (using st_autorefresh) ------------------
if auto_refresh:
    # st_autorefresh expects milliseconds
    st_autorefresh(interval=refresh_seconds * 1000, key="refresh")

st.caption(f"{APP_NAME} v{VERSION} • Powered by Twelve Data + Yahoo Finance")
