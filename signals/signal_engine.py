"""
SEKWAILA OMEGA X — SIGNAL ENGINE
Twelve Data market-data provider, strict timeframe integrity, no calibration.py.

Provider architecture:
- Twelve Data is the active signal-data provider.
- API key is read from TWELVE_DATA_API_KEY.
- No price offsets/calibration are applied.
- Missing required timeframe data blocks signal generation.
- The engine removes the currently forming candle before calculations.

IMPORTANT:
Twelve Data symbol names are provider symbols, not necessarily broker MT5 symbols.
For true broker-price parity, use an MT5 provider layer later.
"""

import datetime
import math
import os
import time
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests

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
    ORDER_BLOCK_DISPLACEMENT_MIN,
)
from logger import get_logger

logger = get_logger("ENGINE")

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com/time_series"
TWELVE_DATA_TIMEOUT = int(os.getenv("TWELVE_DATA_TIMEOUT", "15"))
TWELVE_DATA_RETRIES = int(os.getenv("TWELVE_DATA_RETRIES", "1"))

# Twelve Data interval names.
_TD_INTERVALS = {
    "1D": "1day",
    "4H": "4h",
    "1H": "1h",
    "15M": "15min",
}

# Twelve Data can return a finite amount of history depending on the plan.
# Keep the request conservative to reduce free-plan usage.
_TD_OUTPUTSIZE = {
    "1D": 180,
    "4H": 60 * 24,       # enough raw bars if the provider supports the request
    "1H": 30 * 24,
    "15M": 7 * 24 * 4,
}

# Provider symbols. These can be overridden through environment variables
# without touching the active signal logic.
TWELVE_DATA_SYMBOLS = {
    "XAUUSD": os.getenv("TWELVE_XAUUSD_SYMBOL", "XAU/USD"),
    "NAS100": os.getenv("TWELVE_NAS100_SYMBOL", "NDX"),
    "US30": os.getenv("TWELVE_US30_SYMBOL", "DJI"),
    "BTCUSD": os.getenv("TWELVE_BTCUSD_SYMBOL", "BTC/USD"),
    "EURUSD": os.getenv("TWELVE_EURUSD_SYMBOL", "EUR/USD"),
    "GBPUSD": os.getenv("TWELVE_GBPUSD_SYMBOL", "GBP/USD"),
    "USDJPY": os.getenv("TWELVE_USDJPY_SYMBOL", "USD/JPY"),
    "SPX500": os.getenv("TWELVE_SPX500_SYMBOL", "SPX"),
    "DXY": os.getenv("TWELVE_DXY_SYMBOL", "DXY"),
}

_SESSION = requests.Session()


def _is_rate_limit_error_text(text: str) -> bool:
    text = str(text).lower()
    return any(x in text for x in (
        "rate limit", "ratelimit", "too many requests", "429",
        "api credits", "credits",
    ))


def _clean_ohlcv(df: Any) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Normalize Twelve Data column names.
    rename = {str(c).lower(): c for c in df.columns}
    required_lower = ["open", "high", "low", "close", "volume"]
    if not all(c in rename for c in required_lower):
        return pd.DataFrame()

    df = df.rename(columns={
        rename["open"]: "Open",
        rename["high"]: "High",
        rename["low"]: "Low",
        rename["close"]: "Close",
        rename["volume"]: "Volume",
    })

    required = ["Open", "High", "Low", "Close", "Volume"]
    df = df[required].copy()

    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")

    df = df[~df.index.isna()]
    return df[~df.index.duplicated(keep="last")].sort_index()


def _twelve_data_symbol(symbol: str, ticker: Optional[str] = None) -> str:
    """
    Resolve the application symbol to the Twelve Data symbol.

    Explicit environment overrides are supported. The ticker argument is
    retained for API compatibility with the existing Streamlit app.
    """
    configured = TWELVE_DATA_SYMBOLS.get(symbol)
    if configured:
        return configured
    return ticker or symbol


def _download_twelve_data(
    symbol: str,
    interval: str,
    outputsize: int,
    retries: int = TWELVE_DATA_RETRIES,
) -> Tuple[pd.DataFrame, str]:
    """
    Fetch OHLCV from Twelve Data.

    Returns:
        (DataFrame, status)
    """
    if not TWELVE_DATA_API_KEY:
        return pd.DataFrame(), "UNAVAILABLE (TWELVE_DATA_API_KEY is not configured)"

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVE_DATA_API_KEY,
        "format": "JSON",
        "order": "ASC",
    }

    last_error = ""

    for attempt in range(retries + 1):
        try:
            response = _SESSION.get(
                TWELVE_DATA_BASE_URL,
                params=params,
                timeout=TWELVE_DATA_TIMEOUT,
            )

            if response.status_code == 429:
                last_error = "Twelve Data rate limit (HTTP 429)"
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                return pd.DataFrame(), f"UNAVAILABLE ({last_error})"

            if response.status_code != 200:
                last_error = f"Twelve Data HTTP {response.status_code}"
                if attempt < retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                return pd.DataFrame(), f"UNAVAILABLE ({last_error})"

            payload = response.json()

            if isinstance(payload, dict) and payload.get("status") == "error":
                message = payload.get("message") or payload.get("code") or "provider error"
                last_error = str(message)

                if _is_rate_limit_error_text(last_error):
                    if attempt < retries:
                        time.sleep(2 * (attempt + 1))
                        continue

                return pd.DataFrame(), f"UNAVAILABLE ({last_error})"

            values = payload.get("values") if isinstance(payload, dict) else None
            if not values:
                return pd.DataFrame(), "UNAVAILABLE (Twelve Data returned no OHLCV values)"

            raw = pd.DataFrame(values)

            if "datetime" not in raw.columns:
                return pd.DataFrame(), "UNAVAILABLE (Twelve Data response has no datetime column)"

            raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce")
            raw = raw.dropna(subset=["datetime"]).set_index("datetime")

            cleaned = _clean_ohlcv(raw)
            if cleaned.empty:
                return pd.DataFrame(), "UNAVAILABLE (Twelve Data OHLCV could not be parsed)"

            return cleaned, "LIVE"

        except requests.RequestException as exc:
            last_error = str(exc)
            logger.warning(
                "Twelve Data request failure %s/%s: %s",
                symbol, interval, exc,
            )
            if attempt < retries:
                time.sleep(1 * (attempt + 1))
                continue

        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Twelve Data parsing failure %s/%s: %s",
                symbol, interval, exc,
            )
            break

    return pd.DataFrame(), f"UNAVAILABLE ({last_error or 'unknown provider error'})"


def _validate_timeframe(tf_label: str, df: pd.DataFrame) -> Tuple[bool, str]:
    if df is None or df.empty:
        return False, "UNAVAILABLE (Twelve Data returned no data)"

    if len(df) < MINIMUM_DATA_ROWS:
        return False, (
            f"UNAVAILABLE (Insufficient data returned: {len(df)} rows; "
            f"minimum {MINIMUM_DATA_ROWS})"
        )

    return True, "LIVE"


def fetch_mtf_data(ticker, symbol: Optional[str] = None):
    """
    Fetch every required timeframe independently.

    The existing app calls fetch_mtf_data(ticker), so ticker remains accepted.
    The symbol argument lets newer callers provide the application symbol.
    """
    app_symbol = symbol or ticker

    # If the caller passes a Yahoo-style ticker, resolve the application symbol
    # by reverse lookup where possible.
    if app_symbol not in TWELVE_DATA_SYMBOLS:
        for name, provider_symbol in TWELVE_DATA_SYMBOLS.items():
            if app_symbol == provider_symbol:
                app_symbol = name
                break

    provider_symbol = _twelve_data_symbol(app_symbol, ticker)

    tf_data: Dict[str, Optional[pd.DataFrame]] = {}
    integrity: Dict[str, str] = {}

    for tf_label in ("1D", "4H", "1H", "15M"):
        interval = _TD_INTERVALS[tf_label]
        outputsize = _TD_OUTPUTSIZE[tf_label]

        try:
            df, provider_status = _download_twelve_data(
                provider_symbol,
                interval,
                outputsize,
            )

            ok, validation_status = _validate_timeframe(tf_label, df)

            if not ok:
                tf_data[tf_label] = None
                integrity[tf_label] = validation_status
                logger.warning(
                    "%s %s data failure: %s",
                    provider_symbol, tf_label, validation_status,
                )
            else:
                tf_data[tf_label] = df
                integrity[tf_label] = "LIVE"

        except Exception as exc:
            tf_data[tf_label] = None
            integrity[tf_label] = f"UNAVAILABLE ({exc})"
            logger.warning(
                "%s %s data failure: %s",
                provider_symbol, tf_label, exc,
            )

    return tf_data, integrity


def fetch_usdzar_rate():
    try:
        d, status = _download_twelve_data("USD/ZAR", "1day", 5, retries=0)
        if d.empty:
            return None
        value = _safe_float(d["Close"].iloc[-1])
        return value if value > 0 else None
    except Exception as exc:
        logger.warning("USD/ZAR fetch failed: %s", exc)
        return None


def compute_live_correlation_matrix():
    closes = {}

    for name in ASSETS:
        provider_symbol = _twelve_data_symbol(name, ASSETS.get(name))
        try:
            d, _ = _download_twelve_data(
                provider_symbol, "1h", 240, retries=0
            )
            if not d.empty:
                closes[name] = d["Close"]
        except Exception as exc:
            logger.warning("Correlation fetch failed for %s: %s", name, exc)

    frame = pd.DataFrame(closes)
    return frame.corr().round(2) if frame.shape[1] >= 2 else None


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
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    ag = gain.ewm(
        alpha=1 / period, adjust=False, min_periods=period
    ).mean()
    al = loss.ewm(
        alpha=1 / period, adjust=False, min_periods=period
    ).mean()

    rs = ag / al.replace(0, np.nan)
    value = (100 - 100 / (1 + rs)).iloc[-1]

    return 50.0 if pd.isna(value) else float(np.clip(value, 0, 100))


def compute_macd_trend(df_closed):
    if df_closed is None or len(df_closed) < 35:
        return "NEUTRAL", 0.0, 0.0

    close = df_closed["Close"]
    line = (
        close.ewm(span=12, adjust=False).mean()
        - close.ewm(span=26, adjust=False).mean()
    )
    sig = line.ewm(span=9, adjust=False).mean()

    lv, sv = _safe_float(line.iloc[-1]), _safe_float(sig.iloc[-1])

    return (
        "BULLISH" if lv > sv
        else "BEARISH" if lv < sv
        else "NEUTRAL"
    ), lv, sv


def compute_vwap_status(df_closed):
    if df_closed is None or df_closed.empty:
        return "UNKNOWN", 0.0

    typical = (
        df_closed["High"]
        + df_closed["Low"]
        + df_closed["Close"]
    ) / 3

    volume = df_closed["Volume"].fillna(0)
    cv = volume.cumsum()

    vwap = (
        _safe_float(df_closed["Close"].iloc[-1])
        if cv.iloc[-1] <= 0
        else _safe_float(
            (typical * volume)
            .cumsum()
            .div(cv.replace(0, np.nan))
            .iloc[-1]
        )
    )

    close = _safe_float(df_closed["Close"].iloc[-1])

    return (
        "ABOVE" if close > vwap
        else "BELOW" if close < vwap
        else "AT"
    ), vwap


def vol_status_label(vol_ratio):
    return (
        "HIGH" if vol_ratio >= 1.40
        else "LOW" if vol_ratio <= 0.85
        else "NORMAL"
    )


def compute_ema_cross(df_closed):
    if df_closed is None or len(df_closed) < 50:
        return "NEUTRAL"

    close = df_closed["Close"]
    e20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    e50 = close.ewm(span=50, adjust=False).mean().iloc[-1]

    return (
        "BULLISH" if e20 > e50
        else "BEARISH" if e20 < e50
        else "NEUTRAL"
    )


def compute_true_range(df_closed):
    if df_closed is None or df_closed.empty:
        return pd.Series(dtype=float)

    h, l, c = (
        df_closed["High"],
        df_closed["Low"],
        df_closed["Close"],
    )

    return pd.concat(
        [
            h - l,
            (h - c.shift(1)).abs(),
            (l - c.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)


def compute_atr(df_closed, period=ATR_PERIOD):
    if df_closed is None or len(df_closed) < period + 2:
        return 0.0

    atr = compute_true_range(df_closed).ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return _safe_float(atr.iloc[-1])


def compute_adx(df, length=14):
    d = _closed(df)

    if d is None or len(d) < length * 2 + 5:
        return 20.0

    h, l = d["High"], d["Low"]
    up, down = h.diff(), -l.diff()

    plus = pd.Series(
        np.where((up > down) & (up > 0), up, 0),
        index=d.index,
    )
    minus = pd.Series(
        np.where((down > up) & (down > 0), down, 0),
        index=d.index,
    )

    tr = compute_true_range(d)
    atr = tr.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    ps = plus.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()
    ms = minus.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    pdi = 100 * ps / (atr + 1e-9)
    mdi = 100 * ms / (atr + 1e-9)

    dx = (
        (pdi - mdi).abs()
        / (pdi + mdi).replace(0, np.nan)
    ) * 100

    return _safe_float(
        dx.ewm(
            alpha=1 / length,
            adjust=False,
            min_periods=length,
        ).mean().iloc[-1],
        20.0,
    )


def compute_market_regime(df):
    d = _closed(df)

    if d.empty:
        return {
            "regime": "UNKNOWN",
            "adx": 0.0,
            "vol_ratio": 1.0,
            "slope": 0.0,
        }

    adx = compute_adx(df)
    tr = compute_true_range(d)

    fast = tr.rolling(7).mean().iloc[-1]
    slow = tr.rolling(28).mean().iloc[-1]

    vol = (
        _safe_float(fast / slow, 1.0)
        if pd.notna(slow) and slow > 0
        else 1.0
    )

    y = d["Close"].tail(20).values
    slope = (
        np.polyfit(np.arange(len(y)), y, 1)[0]
        if len(y) >= 2
        else 0.0
    )

    regime = (
        "TRENDING_EXPANSION"
        if adx >= 25 and vol >= 1.10
        else "ACCUMULATION_DISTRIBUTION"
        if adx < 20 and vol < 0.85
        else "HIGH_VOLATILITY_RANGE"
        if vol >= 1.40
        else "CHOP_LOW_VOLATILITY"
    )

    return {
        "regime": regime,
        "adx": round(adx, 2),
        "vol_ratio": round(vol, 2),
        "slope": round(_safe_float(slope), 4),
    }


def find_swing_points(df_closed, window=SWING_WINDOW):
    if df_closed is None or len(df_closed) < 2 * window + 1:
        return np.array([], dtype=int), np.array([], dtype=int)

    h, l = df_closed["High"], df_closed["Low"]

    mx = h.rolling(
        2 * window + 1,
        center=True,
    ).max()
    mn = l.rolling(
        2 * window + 1,
        center=True,
    ).min()

    return (
        np.where(((h == mx) & mx.notna()).values)[0],
        np.where(((l == mn) & mn.notna()).values)[0],
    )


def measure_displacement(df, index):
    if df is None or index < 0 or index + 3 >= len(df):
        return 0.0

    hi = _safe_float(df["High"].iloc[index])
    lo = _safe_float(df["Low"].iloc[index])

    if hi <= 0 or lo <= 0:
        return 0.0

    future = df.iloc[index + 1:index + 4]

    return max(
        0.0,
        float((future["High"].max() - hi) / hi),
        float((lo - future["Low"].min()) / lo),
    )


def analyze_market_structure(df):
    d = _closed(df)

    if d.empty:
        return "NEUTRAL", "NONE", None, None

    sh, sl = find_swing_points(d)

    if len(sh) < 2 or len(sl) < 2:
        return "NEUTRAL", "NONE", None, None

    last_sh = _safe_float(d["High"].iloc[sh[-1]])
    prev_sh = _safe_float(d["High"].iloc[sh[-2]])
    last_sl = _safe_float(d["Low"].iloc[sl[-1]])
    prev_sl = _safe_float(d["Low"].iloc[sl[-2]])
    close = _safe_float(d["Close"].iloc[-1])

    prior_bull = last_sh > prev_sh and last_sl > prev_sl
    prior_bear = last_sh < prev_sh and last_sl < prev_sl

    if close > last_sh:
        disp = (close - last_sh) / max(last_sh, 1e-9)
        base = "BULLISH_CHoCH" if prior_bear else "BULLISH_BOS"
        return (
            "BUY",
            base if disp >= STRUCTURE_DISPLACEMENT_MIN else base + "_WEAK",
            last_sh,
            last_sl,
        )

    if close < last_sl:
        disp = (last_sl - close) / max(last_sl, 1e-9)
        base = "BEARISH_CHoCH" if prior_bull else "BEARISH_BOS"
        return (
            "SELL",
            base if disp >= STRUCTURE_DISPLACEMENT_MIN else base + "_WEAK",
            last_sh,
            last_sl,
        )

    return "NEUTRAL", "NONE", last_sh, last_sl


def detect_choch(df):
    bias, structure, sh, sl = analyze_market_structure(df)
    return {
        "is_choch": "CHoCH" in structure,
        "bias": bias,
        "swing_high": sh,
        "swing_low": sl,
        "structure": structure,
    }


def find_order_block(df, bias):
    d = _closed(df)

    neutral_zone = (
        (
            float(d["Low"].tail(10).min()),
            float(d["High"].tail(10).max()),
        )
        if not d.empty
        else (0.0, 0.0)
    )

    if d.empty or bias not in ("BUY", "SELL"):
        return "NEUTRAL_DEMAND", neutral_zone, False, False

    n = len(d)

    for i in range(max(10, n - 100), n - 4)[::-1]:
        op, cl, hi, lo = [
            _safe_float(d[c].iloc[i])
            for c in ("Open", "Close", "High", "Low")
        ]

        disp = measure_displacement(d, i)

        if bias == "BUY" and cl < op and disp >= ORDER_BLOCK_DISPLACEMENT_MIN:
            after = d.iloc[i + 4:]
            return (
                "BULLISH_OB",
                (lo, hi),
                not after.empty and bool(after["Low"].min() <= hi),
                not after.empty and bool(after["Close"].min() < lo),
            )

        if bias == "SELL" and cl > op and disp >= ORDER_BLOCK_DISPLACEMENT_MIN:
            after = d.iloc[i + 4:]
            return (
                "BEARISH_OB",
                (lo, hi),
                not after.empty and bool(after["High"].max() >= lo),
                not after.empty and bool(after["Close"].max() > hi),
            )

    return "NEUTRAL_DEMAND", neutral_zone, False, False


def detect_breaker_block(df, bias):
    ob, zone, _, invalidated = find_order_block(df, bias)

    if invalidated and bias == "BUY":
        return "BULLISH_BREAKER", zone

    if invalidated and bias == "SELL":
        return "BEARISH_BREAKER", zone

    return "NONE", None


def detect_fvg(df, lookback=FVG_LOOKBACK):
    d = _closed(df)

    if len(d) < 5:
        return None

    start = max(2, len(d) - lookback)
    gaps = []

    for i in range(start, len(d) - 1):
        ph = _safe_float(d["High"].iloc[i - 1])
        pl = _safe_float(d["Low"].iloc[i - 1])
        nh = _safe_float(d["High"].iloc[i + 1])
        nl = _safe_float(d["Low"].iloc[i + 1])

        if nl > ph:
            typ, zone = "BULLISH_FVG", (ph, nl)
        elif nh < pl:
            typ, zone = "BEARISH_FVG", (nh, pl)
        else:
            continue

        future = d.iloc[i + 2:]
        filled = (
            False
            if future.empty
            else bool(
                (
                    (future["Low"] <= zone[1])
                    & (future["High"] >= zone[0])
                ).any()
            )
        )

        gaps.append({
            "index": i,
            "type": typ,
            "zone": zone,
            "filled": filled,
        })

    unfilled = [g for g in gaps if not g["filled"]]
    return unfilled[-1] if unfilled else None


def find_equal_levels(
    df,
    lookback=EQUAL_LEVEL_LOOKBACK,
    tolerance=EQUAL_LEVEL_TOLERANCE,
):
    if df is None or df.empty:
        return [], []

    r = df.tail(lookback)

    def cluster(values):
        vals = np.sort(np.asarray(values, dtype=float))
        vals = vals[np.isfinite(vals)]
        groups = []

        if len(vals) == 0:
            return groups

        cur = [vals[0]]

        for v in vals[1:]:
            if (
                abs(v - cur[-1])
                / max(abs(cur[-1]), 1e-9)
                <= tolerance
            ):
                cur.append(v)
            else:
                if len(cur) >= 2:
                    groups.append(float(np.mean(cur)))
                cur = [v]

        if len(cur) >= 2:
            groups.append(float(np.mean(cur)))

        return groups

    return (
        cluster(r["High"].values),
        cluster(r["Low"].values),
    )


def analyze_liquidity_sweep(df):
    d = _closed(df)

    if len(d) < 20:
        return False, "NO_SWEEP"

    rl = _safe_float(d["Low"].iloc[-15:-2].min())
    rh = _safe_float(d["High"].iloc[-15:-2].max())

    lo, hi, cl = [
        _safe_float(d[c].iloc[-1])
        for c in ("Low", "High", "Close")
    ]

    if lo < rl and cl > rl:
        return True, f"SELL-SIDE SWEEP BELOW {rl:.2f}"

    if hi > rh and cl < rh:
        return True, f"BUY-SIDE SWEEP ABOVE {rh:.2f}"

    eqh, eql = find_equal_levels(d)
    tol = cl * EQUAL_LEVEL_TOLERANCE

    for x in eqh:
        if hi > x + tol * 0.2 and cl < x:
            return True, f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {x:.2f}"

    for x in eql:
        if lo < x - tol * 0.2 and cl > x:
            return True, f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {x:.2f}"

    return False, "NO_SWEEP"


def calculate_premium_discount(df, lookback=50):
    d = _closed(df)

    if d.empty:
        return {
            "zone": "UNKNOWN",
            "equilibrium": 0.0,
            "swing_high": 0.0,
            "swing_low": 0.0,
        }

    d = d.tail(lookback)
    hi = _safe_float(d["High"].max())
    lo = _safe_float(d["Low"].min())
    eq = (hi + lo) / 2
    cl = _safe_float(d["Close"].iloc[-1])

    return {
        "zone": (
            "PREMIUM" if cl > eq
            else "DISCOUNT" if cl < eq
            else "EQUILIBRIUM"
        ),
        "equilibrium": eq,
        "swing_high": hi,
        "swing_low": lo,
    }


def get_session_info():
    now = datetime.datetime.now(datetime.timezone.utc)

    if not _TZ_OK:
        return "UNKNOWN", 50.0

    try:
        lh = now.astimezone(
            ZoneInfo("Europe/London")
        ).hour
        nh = now.astimezone(
            ZoneInfo("America/New_York")
        ).hour
        th = now.astimezone(
            ZoneInfo("Asia/Tokyo")
        ).hour
        sh = now.astimezone(
            ZoneInfo("Australia/Sydney")
        ).hour

        if 8 <= lh <= 16 and 8 <= nh <= 17:
            return "LONDON / NEW YORK OVERLAP", 95.0

        if 8 <= lh <= 16:
            return "LONDON SESSION", 80.0

        if 8 <= nh <= 17:
            return "NEW YORK SESSION", 80.0

        if 9 <= th <= 18:
            return "TOKYO SESSION", 55.0

        if 8 <= sh <= 17:
            return "SYDNEY SESSION", 45.0

        return "OFF-SESSION / LOW LIQUIDITY", 20.0

    except Exception:
        return "UNKNOWN", 50.0


def evaluate_trend_strength(
    d,
    tf_biases,
    regime_info,
    struct_bias,
):
    if d is None or d.empty:
        return False, "No closed data"

    c = d["Close"]

    e20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
    e50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
    e200 = (
        c.ewm(span=200, adjust=False).mean().iloc[-1]
        if len(c) >= 200
        else None
    )

    last = _safe_float(c.iloc[-1])

    bull = (
        last > e20 > e50
        and (e200 is None or e50 > e200)
    )
    bear = (
        last < e20 < e50
        and (e200 is None or e50 < e200)
    )

    adx_ok = regime_info.get("adx", 0) >= 20
    bc = sum(v == "BUY" for v in tf_biases.values())
    sc = sum(v == "SELL" for v in tf_biases.values())

    available = max(len(tf_biases), 1)
    required = max(2, min(3, available))

    if bull and adx_ok and bc >= required and struct_bias == "BUY":
        return True, (
            f"EMA stack + ADX + {required}/{available} TF aligned bullish"
        )

    if bear and adx_ok and sc >= required and struct_bias == "SELL":
        return True, (
            f"EMA stack + ADX + {required}/{available} TF aligned bearish"
        )

    return False, "Trend strength criteria not met"


def calculate_position_size(
    account_balance_usd,
    risk_pct,
    entry_price,
    stop_loss_price,
    contract_size=100.0,
):
    bal, risk, entry, stop, contract = [
        _safe_float(x)
        for x in (
            account_balance_usd,
            risk_pct,
            entry_price,
            stop_loss_price,
            contract_size,
        )
    ]

    if min(bal, risk, entry, stop, contract) <= 0:
        return None

    dist = abs(entry - stop)

    if dist <= 0:
        return None

    risk_amount = bal * risk / 100

    return {
        "risk_amount_usd": round(risk_amount, 2),
        "stop_distance": round(dist, 4),
        "lots": round(
            risk_amount / (dist * contract),
            4,
        ),
    }


def calculate_position_size_for_symbol(
    symbol,
    account_balance_usd,
    risk_pct,
    entry_price,
    stop_loss_price,
):
    contract = CONTRACT_SIZE_BY_SYMBOL.get(symbol, 1.0)

    result = calculate_position_size(
        account_balance_usd,
        risk_pct,
        entry_price,
        stop_loss_price,
        contract,
    )

    if result is not None:
        result["contract_size"] = contract

    return result


def score_signal(
    tf_biases,
    struct_type,
    ob_type,
    mitigated,
    invalidated,
    sweep,
    fvg_present,
    rr,
    pd_zone,
    bias,
    trend_strong,
):
    bull = sum(v == "BUY" for v in tf_biases.values())
    bear = sum(v == "SELL" for v in tf_biases.values())

    score = max(bull, bear) / max(len(tf_biases), 1) * 25

    weak = struct_type.endswith("_WEAK")
    base = struct_type[:-5] if weak else struct_type

    struct = (
        12 if "CHoCH" in base and weak
        else 20 if "CHoCH" in base
        else 8 if "BOS" in base and weak
        else 15 if "BOS" in base
        else 0
    )

    ob = (
        -10
        if invalidated and ob_type in ("BULLISH_OB", "BEARISH_OB")
        else 7
        if mitigated and ob_type in ("BULLISH_OB", "BEARISH_OB")
        else 15
        if ob_type in ("BULLISH_OB", "BEARISH_OB")
        else 0
    )

    rr_score = min(12, max(0, (rr - 1) * 6))

    pd_score = (
        10
        if (
            (bias == "BUY" and pd_zone == "DISCOUNT")
            or (bias == "SELL" and pd_zone == "PREMIUM")
        )
        else -5
        if (
            (bias == "BUY" and pd_zone == "PREMIUM")
            or (bias == "SELL" and pd_zone == "DISCOUNT")
        )
        else 0
    )

    total = (
        score
        + struct
        + ob
        + (10 if sweep else 0)
        + (8 if fvg_present else 0)
        + rr_score
        + pd_score
        + (10 if trend_strong else 0)
    )

    return round(float(np.clip(total, 0, 100)), 1)


def score_bull_bear(
    tf_biases,
    struct_type,
    ob_type,
    mitigated,
    invalidated,
    sweep,
    sweep_msg,
    fvg,
    pd_zone,
    trend_strong,
    macd_trend,
    rsi_val,
):
    bull = bear = 0.0

    bc = sum(v == "BUY" for v in tf_biases.values())
    sc = sum(v == "SELL" for v in tf_biases.values())
    n = max(len(tf_biases), 1)

    bull += bc / n * 25
    bear += sc / n * 25

    weak = struct_type.endswith("_WEAK")
    base = struct_type[:-5] if weak else struct_type

    pts = (
        10 if "CHoCH" in base and weak
        else 20 if "CHoCH" in base
        else 6 if "BOS" in base and weak
        else 15 if "BOS" in base
        else 0
    )

    if "BULLISH" in base:
        bull += pts
    elif "BEARISH" in base:
        bear += pts

    if ob_type == "BULLISH_OB" and not invalidated:
        bull += 7 if mitigated else 15
    elif ob_type == "BEARISH_OB" and not invalidated:
        bear += 7 if mitigated else 15

    if sweep:
        if "SELL-SIDE" in sweep_msg or "EQUAL-LOWS" in sweep_msg:
            bull += 12
        elif "BUY-SIDE" in sweep_msg or "EQUAL-HIGHS" in sweep_msg:
            bear += 12

    if fvg:
        if fvg["type"] == "BULLISH_FVG":
            bull += 8
        elif fvg["type"] == "BEARISH_FVG":
            bear += 8

    if pd_zone == "DISCOUNT":
        bull += 8
    elif pd_zone == "PREMIUM":
        bear += 8

    if macd_trend == "BULLISH":
        bull += 7
    elif macd_trend == "BEARISH":
        bear += 7

    if rsi_val >= 55:
        bull += 5
    elif rsi_val <= 45:
        bear += 5

    if trend_strong:
        if bull > bear:
            bull += 10
        elif bear > bull:
            bear += 10

    return round(min(100, bull), 1), round(min(100, bear), 1)


def grade(score):
    return (
        "A+" if score >= 85
        else "A" if score >= 75
        else "B" if score >= 65
        else "C" if score >= 50
        else "D"
    )


def _blocked_result(
    symbol,
    ticker,
    data,
    integrity,
    reason,
):
    unavailable = [
        tf for tf in ("1D", "4H", "1H", "15M")
        if data.get(tf) is None or data.get(tf).empty
    ]

    return {
        "ok": False,
        "symbol": symbol,
        "ticker": ticker,
        "data": data,
        "data_integrity": integrity,
        "available_timeframes": [
            tf for tf in ("1D", "4H", "1H", "15M")
            if data.get(tf) is not None and not data.get(tf).empty
        ],
        "unavailable_timeframes": unavailable,
        "bias": "NEUTRAL",
        "score": 0.0,
        "grade": "D",
        "reason": reason,
    }


def generate_omega_signal(
    symbol,
    ticker,
    min_tf=DEFAULT_MIN_TF_AGREEMENT,
    min_score=DEFAULT_MIN_SCORE,
    min_rr=DEFAULT_MIN_RR,
):
    """
    Generate one signal using Twelve Data.

    STRICT DATA RULE:
    All four configured timeframes must be available and pass validation.
    If even one required timeframe is unavailable, signal generation is
    blocked. This prevents partial-data signals from appearing as valid.
    """

    data, integrity = fetch_mtf_data(
        ticker,
        symbol=symbol,
    )

    required_tfs = ("1D", "4H", "1H", "15M")

    unavailable = [
        tf for tf in required_tfs
        if data.get(tf) is None or data.get(tf).empty
    ]

    if unavailable:
        return _blocked_result(
            symbol,
            _twelve_data_symbol(symbol, ticker),
            data,
            integrity,
            "DATA UNAVAILABLE — required timeframe(s) unavailable: "
            + ", ".join(unavailable)
            + ". Signal generation BLOCKED.",
        )

    # Do not trust the presence of a dataframe alone. Require LIVE status.
    non_live = [
        tf for tf in required_tfs
        if not str(integrity.get(tf, "")).upper().startswith("LIVE")
    ]

    if non_live:
        return _blocked_result(
            symbol,
            _twelve_data_symbol(symbol, ticker),
            data,
            integrity,
            "DATA UNAVAILABLE — timeframe provider status is not LIVE: "
            + ", ".join(non_live)
            + ". Signal generation BLOCKED.",
        )

    available = {
        tf: data[tf]
        for tf in required_tfs
    }

    biases = {}
    structures = {}

    for tf, df in available.items():
        b, s, _, _ = analyze_market_structure(df)
        biases[tf] = b
        structures[tf] = s

    primary = available["15M"]

    struct_bias, struct_type, sw_high, sw_low = analyze_market_structure(
        primary
    )

    ob_type, ob_zone, ob_mitigated, ob_invalidated = find_order_block(
        primary,
        struct_bias,
    )

    fvg = detect_fvg(primary)
    sweep, sweep_detail = analyze_liquidity_sweep(primary)
    pd_info = calculate_premium_discount(primary)
    regime = compute_market_regime(primary)
    closed = _closed(primary)

    trend_strong, trend_detail = evaluate_trend_strength(
        closed,
        biases,
        regime,
        struct_bias,
    )

    eq_highs, eq_lows = find_equal_levels(closed)
    rsi = compute_rsi(closed)
    macd_trend, macd_line, macd_signal = compute_macd_trend(closed)
    vwap_status, vwap_value = compute_vwap_status(closed)
    vol_status = vol_status_label(regime["vol_ratio"])
    ema_cross = compute_ema_cross(closed)

    bull_score, bear_score = score_bull_bear(
        biases,
        struct_type,
        ob_type,
        ob_mitigated,
        ob_invalidated,
        sweep,
        sweep_detail,
        fvg,
        pd_info["zone"],
        trend_strong,
        macd_trend,
        rsi,
    )

    if closed.empty:
        return _blocked_result(
            symbol,
            _twelve_data_symbol(symbol, ticker),
            data,
            integrity,
            "DATA UNAVAILABLE — no closed 15M candle available.",
        )

    entry = _safe_float(closed["Close"].iloc[-1])
    atr = compute_atr(closed)

    if atr <= 0:
        return _blocked_result(
            symbol,
            _twelve_data_symbol(symbol, ticker),
            data,
            integrity,
            "DATA UNAVAILABLE — ATR could not be calculated.",
        )

    buffer = atr * 0.15

    if struct_bias == "BUY":
        ref = (
            ob_zone[0]
            if ob_type == "BULLISH_OB" and not ob_invalidated
            else sw_low
        )

        if ref is None:
            ref = entry - atr * 1.5

        stop = min(ref - buffer, entry - atr)
        tp1 = entry + 1.5 * atr
        tp2 = entry + 3 * atr
        tp3 = entry + 5 * atr

    elif struct_bias == "SELL":
        ref = (
            ob_zone[1]
            if ob_type == "BEARISH_OB" and not ob_invalidated
            else sw_high
        )

        if ref is None:
            ref = entry + atr * 1.5

        stop = max(ref + buffer, entry + atr)
        tp1 = entry - 1.5 * atr
        tp2 = entry - 3 * atr
        tp3 = entry - 5 * atr

    else:
        stop = tp1 = tp2 = tp3 = entry

    rr = (
        abs(tp2 - entry) / abs(entry - stop)
        if struct_bias in ("BUY", "SELL")
        and abs(entry - stop) > 0
        else 0.0
    )

    score = score_signal(
        biases,
        struct_type,
        ob_type,
        ob_mitigated,
        ob_invalidated,
        sweep,
        fvg is not None,
        rr,
        pd_info["zone"],
        struct_bias,
        trend_strong,
    )

    bc = sum(v == "BUY" for v in biases.values())
    sc = sum(v == "SELL" for v in biases.values())

    # Four timeframes are mandatory, therefore agreement is always measured
    # against all four available required timeframes.
    effective_min_tf = min(
        max(int(min_tf), 1),
        len(required_tfs),
    )

    reason = None

    if (
        bc >= effective_min_tf
        and score >= min_score
        and struct_bias == "BUY"
    ):
        bias = "BUY"
    elif (
        sc >= effective_min_tf
        and score >= min_score
        and struct_bias == "SELL"
    ):
        bias = "SELL"
    else:
        bias = "NEUTRAL"
        reason = (
            "Timeframe agreement or score below threshold "
            f"({max(bc, sc)}/{effective_min_tf} TF, "
            f"{score}/{min_score} score)"
        )

    if bias != "NEUTRAL" and rr < min_rr:
        bias = "NEUTRAL"
        reason = (
            f"R:R {rr:.2f} below minimum {min_rr:.2f} — "
            "signal downgraded to NEUTRAL"
        )

    if bias != "NEUTRAL" and ob_invalidated:
        bias = "NEUTRAL"
        reason = "Directional order block is invalidated."

    session, session_quality = get_session_info()

    return {
        "ok": True,
        "symbol": symbol,
        "ticker": _twelve_data_symbol(symbol, ticker),
        "data": data,
        "data_integrity": integrity,
        "available_timeframes": list(available),
        "unavailable_timeframes": [],
        "bias": bias,
        "score": score,
        "grade": grade(score),
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "rr": round(rr, 3),
        "atr": round(atr, 4),
        "tf_biases": biases,
        "tf_structures": structures,
        "structure": struct_type,
        "ob_type": ob_type,
        "ob_zone": ob_zone,
        "ob_mitigated": ob_mitigated,
        "ob_invalidated": ob_invalidated,
        "fvg": fvg,
        "sweep": sweep,
        "sweep_detail": sweep_detail,
        "pd_zone": pd_info["zone"],
        "pd_info": pd_info,
        "session": session,
        "session_quality": session_quality,
        "regime": regime,
        "trend_strong": trend_strong,
        "trend_detail": trend_detail,
        "eq_highs": eq_highs,
        "eq_lows": eq_lows,
        "rsi": round(rsi, 2),
        "macd_trend": macd_trend,
        "macd_line": macd_line,
        "macd_signal": macd_signal,
        "vwap_status": vwap_status,
        "vwap_val": vwap_value,
        "vol_status": vol_status,
        "ema_cross": ema_cross,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "bull_tf_count": bc,
        "bear_tf_count": sc,
        "reason": reason,
    }
