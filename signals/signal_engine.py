"""
SEKWAILA OMEGA X — CORE ENGINE

Single source of truth for the Streamlit dashboard and any worker.
"""

import asyncio
import datetime
import json
import math
import numpy as np
import pandas as pd
import yfinance as yf  # kept only for USD/ZAR conversion + correlation matrix (secondary features)

try:
    import websockets
except ImportError:
    websockets = None

try:
    from zoneinfo import ZoneInfo
    _TZ_OK = True
except Exception:
    _TZ_OK = False

from config import (
    ASSETS, TF_CONFIG, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR, CONTRACT_SIZE_BY_SYMBOL, MINIMUM_DATA_ROWS,
    ATR_PERIOD, SWING_WINDOW, FVG_LOOKBACK, EQUAL_LEVEL_LOOKBACK,
    EQUAL_LEVEL_TOLERANCE, STRUCTURE_DISPLACEMENT_MIN,
    ORDER_BLOCK_DISPLACEMENT_MIN, DERIV_APP_ID, DERIV_API_TOKEN,
    DERIV_SYMBOL_MAP, DERIV_GRANULARITY, DERIV_CANDLE_COUNT,
)
from logger import get_logger

logger = get_logger("ENGINE")

# Keep a simple in-memory last-success record so the UI can show recent health
LAST_SUCCESS = {}  # symbol -> { 'timestamp': datetime, 'tf': list_of_tfs }


def _clean_ohlcv(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in df.columns for c in required):
        return pd.DataFrame()
    df = df[required].copy()
    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _closed(df):
    if df is None or len(df) < 2:
        return pd.DataFrame()
    return df.iloc[:-1].copy()


def _safe_float(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else float(default)
    except Exception:
        return float(default)


def compute_rsi(df_closed, period=14):
    if df_closed is None or len(df_closed) < period + 2:
        return 50.0
    delta = df_closed["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    al = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = ag / al.replace(0, np.nan)
    value = (100 - 100/(1+rs)).iloc[-1]
    return 50.0 if pd.isna(value) else float(np.clip(value, 0, 100))


def compute_macd_trend(df_closed):
    if df_closed is None or len(df_closed) < 35:
        return "NEUTRAL", 0.0, 0.0
    close = df_closed["Close"]
    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    line = e12 - e26
    sig = line.ewm(span=9, adjust=False).mean()
    lv, sv = _safe_float(line.iloc[-1]), _safe_float(sig.iloc[-1])
    return ("BULLISH" if lv > sv else "BEARISH" if lv < sv else "NEUTRAL"), lv, sv


def compute_vwap_status(df_closed):
    if df_closed is None or df_closed.empty:
        return "UNKNOWN", 0.0
    typical = (df_closed["High"] + df_closed["Low"] + df_closed["Close"]) / 3
    volume = df_closed["Volume"].fillna(0)
    cv = volume.cumsum()
    if cv.iloc[-1] <= 0:
        vwap = _safe_float(df_closed["Close"].iloc[-1])
    else:
        vwap = _safe_float((typical * volume).cumsum().div(cv.replace(0, np.nan)).iloc[-1])
    close = _safe_float(df_closed["Close"].iloc[-1])
    return ("ABOVE" if close > vwap else "BELOW" if close < vwap else "AT"), vwap


def vol_status_label(vol_ratio):
    return "HIGH" if vol_ratio >= 1.40 else "LOW" if vol_ratio <= 0.85 else "NORMAL"


def compute_ema_cross(df_closed):
    if df_closed is None or len(df_closed) < 50:
        return "NEUTRAL"
    close = df_closed["Close"]
    e20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    e50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    return "BULLISH" if e20 > e50 else "BEARISH" if e20 < e50 else "NEUTRAL"


DERIV_WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"


async def _deriv_fetch_candles(symbol_code, granularity, count):
    async with websockets.connect(DERIV_WS_URL, ping_interval=20, ping_timeout=10) as ws:
        if DERIV_API_TOKEN:
            await ws.send(json.dumps({"authorize": DERIV_API_TOKEN}))
            await ws.recv()  # discard the authorize response, we just need the connection authed
        request = {
            "ticks_history": symbol_code,
            "style": "candles",
            "granularity": granularity,
            "count": count,
            "end": "latest",
        }
        await ws.send(json.dumps(request))
        response = json.loads(await ws.recv())
        if "error" in response:
            raise ValueError(response["error"].get("message", "Deriv API error"))
        return response.get("candles", [])


def _deriv_candles_to_df(candles):
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["epoch"] = pd.to_datetime(df["epoch"], unit="s", utc=True)
    df = df.set_index("epoch").rename(columns={
        "open": "Open", "high": "High", "low": "Low", "close": "Close"
    })
    for c in ["Open", "High", "Low", "Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Deriv doesn't report volume for forex/index feeds. Downstream code
    # (VWAP, liquidity sweep) already falls back gracefully when Volume==0.
    df["Volume"] = 0.0
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open","High","Low","Close"])


def _yf_fetch_candles_for_symbol(symbol):
    """Fallback to yfinance for symbols that don't have a Deriv mapping.
    Returns a dict of timeframe -> DataFrame, and an integrity dict.
    """
    tf_data = {}
    integrity = {}
    ticker = ASSETS.get(symbol)
    if not ticker:
        reason = f"UNAVAILABLE (no ticker in ASSETS for {symbol})"
        logger.error(reason)
        return {tf: None for tf in DERIV_GRANULARITY}, {tf: reason for tf in DERIV_GRANULARITY}

    for tf_label, granularity in DERIV_GRANULARITY.items():
        yf_period, yf_interval = TF_CONFIG.get(tf_label, ("7d", "15m"))
        try:
            d = _clean_ohlcv(yf.download(ticker, period=yf_period, interval=yf_interval, progress=False, auto_adjust=False, threads=False))
            if d.empty or len(d) < MINIMUM_DATA_ROWS:
                logger.warning("yfinance insufficient data for %s %s: %s rows", symbol, tf_label, len(d))
                tf_data[tf_label] = None
n                integrity[tf_label] = f"UNAVAILABLE (yfinance insufficient data: {len(d)} rows)"
            else:
                tf_data[tf_label] = d
                integrity[tf_label] = "LIVE (yfinance)"
                # record last success
                LAST_SUCCESS.setdefault(symbol, {})
                LAST_SUCCESS[symbol][tf_label] = datetime.datetime.now(datetime.timezone.utc)
        except Exception as exc:
            logger.warning("yfinance fetch failed for %s %s: %s", symbol, tf_label, exc)
            tf_data[tf_label] = None
            integrity[tf_label] = f"UNAVAILABLE (yfinance error: {exc})"
    return tf_data, integrity


def fetch_mtf_data(symbol):
    """
    Fetches live multi-timeframe candles from Deriv's free WebSocket API.
    `symbol` is SEKWAILA's internal name (e.g. "XAUUSD"), resolved through
    DERIV_SYMBOL_MAP to Deriv's own symbol code.
    """
    tf_data, integrity = {}, {}

    # If websockets package is not available, fallback immediately to yfinance
    if websockets is None:
        logger.warning("websockets package not installed; falling back to yfinance for %s", symbol)
        return _yf_fetch_candles_for_symbol(symbol)

    symbol_code = DERIV_SYMBOL_MAP.get(symbol)
    if not symbol_code:
        logger.info("No Deriv symbol mapped for %s; attempting yfinance fallback", symbol)
        return _yf_fetch_candles_for_symbol(symbol)

    for tf_label, granularity in DERIV_GRANULARITY.items():
        count = DERIV_CANDLE_COUNT.get(tf_label, 300)
        try:
            candles = asyncio.run(_deriv_fetch_candles(symbol_code, granularity, count))
            df = _deriv_candles_to_df(candles)
            if df.empty or len(df) < MINIMUM_DATA_ROWS:
                raise ValueError(f"Insufficient data returned ({len(df)} rows)")
            tf_data[tf_label] = df
            integrity[tf_label] = "LIVE (Deriv)"
            # update last-success
            LAST_SUCCESS.setdefault(symbol, {})
            LAST_SUCCESS[symbol][tf_label] = datetime.datetime.now(datetime.timezone.utc)
        except Exception as exc:
            logger.warning("%s %s Deriv fetch failure: %s", symbol, tf_label, exc)
            tf_data[tf_label] = None
            integrity[tf_label] = f"UNAVAILABLE ({exc})"
    return tf_data, integrity

# ... rest of file unchanged (compute_usdzar_rate, correlation, analysis functions etc.)
