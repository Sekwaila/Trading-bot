"""
SEKWAILA OMEGA X
Single-file Streamlit dashboard + always-on SMC scanner with Telegram alerts.

Architecture note:
- Railway keeps this process running 24/7 (unlike Replit Autoscale, which sleeps
  between requests and kills background threads).
- st.cache_resource starts ONE background worker thread per container, shared
  across every browser session. That thread scans markets and fires Telegram
  alerts on a timer regardless of whether the dashboard is open in a browser.
- The Streamlit UI thread only reads from SQLite / does live price lookups —
  it never blocks the worker and the worker never blocks the UI.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import sqlite3
import threading
import time
import hashlib
from datetime import datetime, timezone

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(page_title="Sekwaila Omega X", page_icon="📈", layout="wide")

TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

MARKETS = {
    "XAUUSD": "XAUUSD=X",
    "BTCUSD": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "USDJPY": "USDJPY=X",
    "US30":   "^DJI",
    "SP500":  "^GSPC",
}

SCAN_INTERVAL_SECONDS = 300      # worker cadence
SWING_LEFT = 2                   # bars either side for fractal swing detection
SWING_RIGHT = 2
LIQUIDITY_LOOKBACK = 15
OB_LOOKBACK = 10
DB_PATH = "sekwaila_omega_x.db"

# ==========================================================
# DATABASE
# ==========================================================

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            signal_id TEXT PRIMARY KEY,
            symbol TEXT,
            timeframe TEXT,
            direction TEXT,
            score INTEGER,
            notes TEXT,
            price REAL,
            created_at TEXT
        )
    """)
    return conn

def already_alerted(signal_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM signals WHERE signal_id = ?", (signal_id,)).fetchone()
    conn.close()
    return row is not None

def record_signal(signal_id, symbol, timeframe, direction, score, notes, price):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO signals VALUES (?,?,?,?,?,?,?,?)",
        (signal_id, symbol, timeframe, direction, score, notes, price,
         datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def recent_signals(limit=25):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df

# ==========================================================
# DATA FETCHING
# ==========================================================

def fetch_h1(yf_symbol: str) -> pd.DataFrame:
    """H1 candles. yfinance limits intraday 60m history to ~2 years but we only need days."""
    df = yf.Ticker(yf_symbol).history(period="30d", interval="60m")
    if df.empty:
        return df
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index)
    return df

def resample_h4(h1: pd.DataFrame) -> pd.DataFrame:
    if h1.empty:
        return h1
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    h4 = h1.resample("4h").agg(agg).dropna()
    return h4

def get_live_price(yf_symbol: str):
    try:
        df = yf.Ticker(yf_symbol).history(period="1d", interval="1m")
        if df.empty:
            df = yf.Ticker(yf_symbol).history(period="5d", interval="60m")
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None

# ==========================================================
# SMC ENGINE
# ==========================================================

def find_swings(df: pd.DataFrame, left=SWING_LEFT, right=SWING_RIGHT):
    """Fractal swing highs/lows. Returns df with swing_high / swing_low bool columns."""
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)
    for i in range(left, n - right):
        window_h = highs[i - left:i + right + 1]
        window_l = lows[i - left:i + right + 1]
        if highs[i] == window_h.max() and np.argmax(window_h) == left:
            swing_high[i] = True
        if lows[i] == window_l.min() and np.argmin(window_l) == left:
            swing_low[i] = True
    out = df.copy()
    out["swing_high"] = swing_high
    out["swing_low"] = swing_low
    return out

def detect_bos_choch(df: pd.DataFrame):
    """
    Walk the confirmed swings chronologically, tracking structure.
    Returns list of events: dict(idx, type[BOS/CHoCH], direction, price, break_idx)
    """
    events = []
    last_swing_high = None   # (idx, price)
    last_swing_low = None
    trend = None  # "bullish" / "bearish"

    for i in range(len(df)):
        row = df.iloc[i]

        if last_swing_high is not None and row["close"] > last_swing_high[1]:
            etype = "CHoCH" if trend != "bullish" else "BOS"
            events.append({"idx": i, "type": etype, "direction": "bullish",
                            "price": row["close"], "break_idx": i})
            trend = "bullish"
            last_swing_high = None  # require a fresh swing before the next break counts

        if last_swing_low is not None and row["close"] < last_swing_low[1]:
            etype = "CHoCH" if trend != "bearish" else "BOS"
            events.append({"idx": i, "type": etype, "direction": "bearish",
                            "price": row["close"], "break_idx": i})
            trend = "bearish"
            last_swing_low = None

        if row["swing_high"]:
            last_swing_high = (i, row["high"])
        if row["swing_low"]:
            last_swing_low = (i, row["low"])

    return events, trend

def find_order_block(df: pd.DataFrame, break_idx: int, direction: str, lookback=OB_LOOKBACK):
    """Last opposite-colour candle before the impulse leg that caused the break."""
    start = max(0, break_idx - lookback)
    window = df.iloc[start:break_idx]
    if window.empty:
        return None
    if direction == "bullish":
        down_candles = window[window["close"] < window["open"]]
        if down_candles.empty:
            return None
        c = down_candles.iloc[-1]
    else:
        up_candles = window[window["close"] > window["open"]]
        if up_candles.empty:
            return None
        c = up_candles.iloc[-1]
    return {"top": float(c["high"]), "bottom": float(c["low"])}

def detect_fvgs(df: pd.DataFrame):
    """3-candle imbalance. Returns list of dicts with direction, top, bottom, idx."""
    fvgs = []
    highs, lows = df["high"].values, df["low"].values
    for i in range(1, len(df) - 1):
        if lows[i + 1] > highs[i - 1]:
            fvgs.append({"idx": i, "direction": "bullish",
                         "top": float(lows[i + 1]), "bottom": float(highs[i - 1])})
        if highs[i + 1] < lows[i - 1]:
            fvgs.append({"idx": i, "direction": "bearish",
                         "top": float(lows[i - 1]), "bottom": float(highs[i + 1])})
    return fvgs

def detect_recent_liquidity_sweep(df: pd.DataFrame, lookback=LIQUIDITY_LOOKBACK):
    """Wick through a prior swing point that closes back inside = stop-hunt / liquidity grab."""
    recent = df.iloc[-lookback:]
    swing_highs = recent[recent["swing_high"]]["high"]
    swing_lows = recent[recent["swing_low"]]["low"]

    last = df.iloc[-1]
    if not swing_highs.empty:
        prior_high = swing_highs.iloc[:-1].max() if len(swing_highs) > 1 else swing_highs.max()
        if last["high"] > prior_high and last["close"] < prior_high:
            return "bearish"  # buy-side liquidity grabbed, closed back below -> reversal down
    if not swing_lows.empty:
        prior_low = swing_lows.iloc[:-1].min() if len(swing_lows) > 1 else swing_lows.min()
        if last["low"] < prior_low and last["close"] > prior_low:
            return "bullish"  # sell-side liquidity grabbed, closed back above -> reversal up
    return None

def premium_discount_zone(df: pd.DataFrame):
    """Equilibrium of the most recent completed swing leg."""
    swings = df[df["swing_high"] | df["swing_low"]]
    if len(swings) < 2:
        return None, None
    last_two = swings.iloc[-2:]
    hi = max(last_two["high"].max(), last_two["low"].max())
    lo = min(last_two["high"].min(), last_two["low"].min())
    eq = (hi + lo) / 2
    last_close = df["close"].iloc[-1]
    zone = "premium" if last_close > eq else "discount"
    return zone, eq

def analyze(h1: pd.DataFrame, h4: pd.DataFrame):
    """Top-down SMC analysis. Returns None if no valid H4/H1-aligned setup."""
    if h1.empty or h4.empty or len(h1) < 30 or len(h4) < 10:
        return None

    h1 = find_swings(h1)
    h4 = find_swings(h4)

    h1_events, _ = detect_bos_choch(h1)
    h4_events, h4_trend = detect_bos_choch(h4)

    if not h1_events or h4_trend is None:
        return None

    last_h1_event = h1_events[-1]
    direction = last_h1_event["direction"]

    # Mandatory gate: only trade with H4 bias (true top-down SMC)
    if direction != h4_trend:
        return None

    notes = [f"H4 bias: {h4_trend}", f"H1 {last_h1_event['type']}: {direction}"]
    score = 0

    ob = find_order_block(h1, last_h1_event["break_idx"], direction)
    last_price = h1["close"].iloc[-1]
    if ob:
        in_ob = ob["bottom"] <= last_price <= ob["top"]
        if in_ob:
            score += 1
            notes.append(f"price retesting {direction} order block "
                          f"({ob['bottom']:.4f}-{ob['top']:.4f})")

    fvgs = detect_fvgs(h1)
    matching_fvgs = [f for f in fvgs if f["direction"] == direction]
    if matching_fvgs:
        f = matching_fvgs[-1]
        if f["bottom"] <= last_price <= f["top"]:
            score += 1
            notes.append(f"price inside unmitigated {direction} FVG "
                          f"({f['bottom']:.4f}-{f['top']:.4f})")

    zone, eq = premium_discount_zone(h1)
    if zone:
        aligned = (direction == "bullish" and zone == "discount") or \
                  (direction == "bearish" and zone == "premium")
        if aligned:
            score += 1
            notes.append(f"price in {zone} (eq {eq:.4f}) — favours {direction}")

    sweep = detect_recent_liquidity_sweep(h1)
    if sweep == direction:
        score += 1
        notes.append(f"recent liquidity sweep confirming {direction} reversal")

    bar_time = h1.index[-1].isoformat()

    return {
        "direction": direction,
        "event_type": last_h1_event["type"],
        "score": score,
        "notes": "; ".join(notes),
        "price": float(last_price),
        "bar_time": bar_time,
    }

# ==========================================================
# TELEGRAM
# ==========================================================

def send_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] missing bot token / chat id, skipping send")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
                                  "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"[telegram] send failed: {e}")

def format_alert(name, result):
    arrow = "🟢" if result["direction"] == "bullish" else "🔴"
    return (
        f"{arrow} *SEKWAILA OMEGA X* — {name}\n"
        f"{result['event_type']} · {result['direction'].upper()}\n"
        f"Confluence score: {result['score']}/4\n"
        f"Price: {result['price']:.4f}\n"
        f"{result['notes']}"
    )

# ==========================================================
# BACKGROUND WORKER (runs continuously, independent of UI)
# ==========================================================

def scan_once(alert_threshold: int):
    for name, sym in MARKETS.items():
        try:
            h1 = fetch_h1(sym)
            h4 = resample_h4(h1)
            result = analyze(h1, h4)
            if result and result["score"] >= alert_threshold:
                signal_id = hashlib.md5(
                    f"{name}-{result['direction']}-{result['bar_time']}".encode()
                ).hexdigest()
                if not already_alerted(signal_id):
                    send_telegram(format_alert(name, result))
                    record_signal(signal_id, name, "H1/H4", result["direction"],
                                  result["score"], result["notes"], result["price"])
        except Exception as e:
            print(f"[worker] {name} error: {e}")

def worker_loop(alert_threshold: int):
    while True:
        scan_once(alert_threshold)
        time.sleep(SCAN_INTERVAL_SECONDS)

@st.cache_resource
def start_worker(alert_threshold: int):
    t = threading.Thread(target=worker_loop, args=(alert_threshold,), daemon=True)
    t.start()
    return t

# ==========================================================
# UI
# ==========================================================

st.title("📈 Sekwaila Omega X")
st.caption("Institutional Smart Money Trading Assistant — live prices, true SMC, always-on Telegram alerts")
st.write(datetime.now().strftime("%d %B %Y | %H:%M:%S"))

with st.sidebar:
    st.header("⚙️ Settings")
    alert_threshold = st.slider("Alert threshold (confluence factors, out of 4)", 1, 4, 2)
    st.caption(f"Scanner runs every {SCAN_INTERVAL_SECONDS // 60} min, independent of this page being open.")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to Railway/Streamlit secrets to enable alerts.")

start_worker(alert_threshold)

st.header("📊 Live Markets")
cols = st.columns(3)
for i, (name, sym) in enumerate(MARKETS.items()):
    price = get_live_price(sym)
    with cols[i % 3]:
        if price is not None:
            st.metric(name, f"{price:,.2f}")
        else:
            st.error(f"{name} unavailable")

st.header("🧠 SMC Signal Feed")
if st.button("🔍 Run scan now"):
    with st.spinner("Scanning markets..."):
        scan_once(alert_threshold)
    st.success("Scan complete.")

signals_df = recent_signals()
if not signals_df.empty:
    st.dataframe(
        signals_df[["created_at", "symbol", "direction", "score", "price", "notes"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No confluence signals logged yet. The background worker scans every "
            f"{SCAN_INTERVAL_SECONDS // 60} minutes and will populate this feed automatically.")
