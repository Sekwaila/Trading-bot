"""
SEKWAILA OMEGA X — CORE ENGINE

Single source of truth for:
- Streamlit dashboard
- Market scanner
- Telegram worker
- SMC calculations
- ATR / ADX
- BOS / CHoCH
- Order blocks
- FVG
- Liquidity sweeps
- Premium / discount
- Multi-timeframe agreement
- Signal scoring
- R:R enforcement
- Position sizing

The dashboard and worker MUST both import generate_omega_signal()
from this file.
"""

import datetime
import math

import numpy as np
import pandas as pd
import yfinance as yf

try:
    from zoneinfo import ZoneInfo

    _TZ_OK = True
except Exception:
    _TZ_OK = False


from config import (
    ASSETS,
    TF_CONFIG,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
    CONTRACT_SIZE_BY_SYMBOL,
    MINIMUM_DATA_ROWS,
    ATR_PERIOD,
    SWING_WINDOW,
    FVG_LOOKBACK,
    EQUAL_LEVEL_LOOKBACK,
    EQUAL_LEVEL_TOLERANCE,
    STRUCTURE_DISPLACEMENT_MIN,
    ORDER_BLOCK_DISPLACEMENT_MIN,
)

from logger import get_logger


logger = get_logger("ENGINE")


# ==============================================================================
# GENERAL HELPERS
# ==============================================================================


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize yfinance OHLCV data.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        return pd.DataFrame()

    df = df[required].copy()

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].fillna(0)

    df = df[~df.index.duplicated(keep="last")]

    return df


def _closed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove the currently forming candle.

    yfinance generally returns the latest candle, which may still be open.
    """
    if df is None or len(df) < 2:
        return pd.DataFrame()

    return df.iloc[:-1].copy()


def _safe_float(value, default=0.0):
    try:
        value = float(value)

        if math.isfinite(value):
            return value

    except Exception:
        pass

    return float(default)


# ==============================================================================
# INDICATORS
# ==============================================================================


def compute_rsi(
    df_closed: pd.DataFrame,
    period: int = 14,
) -> float:

    if df_closed is None or len(df_closed) < period + 2:
        return 50.0

    close = df_closed["Close"]

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    value = rsi.iloc[-1]

    if pd.isna(value):
        return 50.0

    return float(np.clip(value, 0, 100))


def compute_macd_trend(
    df_closed: pd.DataFrame,
):
    if df_closed is None or len(df_closed) < 35:
        return "NEUTRAL", 0.0, 0.0

    close = df_closed["Close"]

    ema12 = close.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False,
    ).mean()

    macd_line = ema12 - ema26

    signal_line = macd_line.ewm(
        span=9,
        adjust=False,
    ).mean()

    macd_value = _safe_float(macd_line.iloc[-1])
    signal_value = _safe_float(signal_line.iloc[-1])

    if macd_value > signal_value:
        trend = "BULLISH"
    elif macd_value < signal_value:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    return trend, macd_value, signal_value


def compute_vwap_status(
    df_closed: pd.DataFrame,
):
    if df_closed is None or df_closed.empty:
        return "UNKNOWN", 0.0

    typical = (
        df_closed["High"]
        + df_closed["Low"]
        + df_closed["Close"]
    ) / 3.0

    volume = df_closed["Volume"].fillna(0)

    cumulative_volume = volume.cumsum()

    if cumulative_volume.iloc[-1] <= 0:
        vwap_value = float(df_closed["Close"].iloc[-1])

    else:
        vwap = (
            typical * volume
        ).cumsum() / cumulative_volume.replace(0, np.nan)

        vwap_value = _safe_float(
            vwap.iloc[-1],
            df_closed["Close"].iloc[-1],
        )

    close = _safe_float(df_closed["Close"].iloc[-1])

    if close > vwap_value:
        status = "ABOVE"
    elif close < vwap_value:
        status = "BELOW"
    else:
        status = "AT"

    return status, vwap_value


def vol_status_label(vol_ratio: float) -> str:

    if vol_ratio >= 1.40:
        return "HIGH"

    if vol_ratio <= 0.85:
        return "LOW"

    return "NORMAL"


def compute_ema_cross(
    df_closed: pd.DataFrame,
) -> str:

    if df_closed is None or len(df_closed) < 50:
        return "NEUTRAL"

    close = df_closed["Close"]

    ema20 = close.ewm(
        span=20,
        adjust=False,
    ).mean().iloc[-1]

    ema50 = close.ewm(
        span=50,
        adjust=False,
    ).mean().iloc[-1]

    if ema20 > ema50:
        return "BULLISH"

    if ema20 < ema50:
        return "BEARISH"

    return "NEUTRAL"


# ==============================================================================
# DATA
# ==============================================================================


def fetch_mtf_data(ticker: str):

    tf_data = {}
    data_integrity = {}

    for tf_label, (period, interval) in TF_CONFIG.items():

        try:

            raw = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            df = _clean_ohlcv(raw)

            if df.empty:
                raise ValueError("Empty data returned.")

            if len(df) < 30:
                raise ValueError(
                    f"Insufficient data returned ({len(df)} rows)."
                )

            # --------------------------------------------------------------
            # Convert 1H data into 4H candles.
            # --------------------------------------------------------------

            if tf_label == "4H":

                df = (
                    df.resample("4h")
                    .agg(
                        {
                            "Open": "first",
                            "High": "max",
                            "Low": "min",
                            "Close": "last",
                            "Volume": "sum",
                        }
                    )
                    .dropna(
                        subset=[
                            "Open",
                            "High",
                            "Low",
                            "Close",
                        ]
                    )
                )

            if len(df) < 30:
                raise ValueError(
                    f"Insufficient processed {tf_label} candles ({len(df)})."
                )

            tf_data[tf_label] = df
            data_integrity[tf_label] = "LIVE"

        except Exception as exc:

            logger.warning(
                f"{ticker} {tf_label} data failure: {exc}"
            )

            tf_data[tf_label] = None

            data_integrity[tf_label] = (
                f"UNAVAILABLE ({exc})"
            )

    return tf_data, data_integrity


def fetch_usdzar_rate():

    try:

        d = yf.download(
            "ZAR=X",
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        d = _clean_ohlcv(d)

        if d.empty:
            return None

        value = _safe_float(
            d["Close"].iloc[-1],
            0,
        )

        return value if value > 0 else None

    except Exception as exc:

        logger.warning(
            f"USDZAR fetch failed: {exc}"
        )

        return None


def compute_live_correlation_matrix():

    df_closes = pd.DataFrame()

    for name, ticker in ASSETS.items():

        try:

            d = yf.download(
                ticker,
                period="10d",
                interval="1h",
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            d = _clean_ohlcv(d)

            if d.empty:
                continue

            df_closes[name] = d["Close"]

        except Exception as exc:

            logger.warning(
                f"Correlation fetch failed for {name}: {exc}"
            )

    if df_closes.shape[1] < 2:
        return None

    return df_closes.corr().round(2)


# ==============================================================================
# TRUE RANGE / ATR / ADX
# ==============================================================================


def compute_true_range(
    df_closed: pd.DataFrame,
) -> pd.Series:

    if df_closed is None or df_closed.empty:
        return pd.Series(dtype=float)

    high = df_closed["High"]
    low = df_closed["Low"]
    close = df_closed["Close"]

    tr1 = high - low

    tr2 = (
        high - close.shift(1)
    ).abs()

    tr3 = (
        low - close.shift(1)
    ).abs()

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1,
    ).max(axis=1)

    return tr


def compute_atr(
    df_closed: pd.DataFrame,
    period: int = ATR_PERIOD,
) -> float:

    if df_closed is None or len(df_closed) < period + 2:
        return 0.0

    tr = compute_true_range(df_closed)

    atr = tr.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    value = atr.iloc[-1]

    return _safe_float(value, 0.0)


def compute_adx(
    df: pd.DataFrame,
    length: int = 14,
) -> float:

    df_c = _closed(df)

    if df_c is None or len(df_c) < (length * 2 + 5):
        return 20.0

    high = df_c["High"]
    low = df_c["Low"]

    up_move = high.diff()

    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where(
            (up_move > down_move) & (up_move > 0),
            up_move,
            0.0,
        ),
        index=df_c.index,
    )

    minus_dm = pd.Series(
        np.where(
            (down_move > up_move) & (down_move > 0),
            down_move,
            0.0,
        ),
        index=df_c.index,
    )

    tr = compute_true_range(df_c)

    atr = tr.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    plus_dm_s = plus_dm.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    minus_dm_s = minus_dm.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    eps = 1e-9

    plus_di = (
        100
        * plus_dm_s
        / (atr + eps)
    )

    minus_di = (
        100
        * minus_dm_s
        / (atr + eps)
    )

    di_sum = (
        plus_di + minus_di
    ).replace(0, np.nan)

    dx = (
        (plus_di - minus_di).abs()
        / di_sum
        * 100
    )

    adx = dx.ewm(
        alpha=1 / length,
        adjust=False,
        min_periods=length,
    ).mean()

    value = adx.iloc[-1]

    return _safe_float(value, 20.0)


def compute_market_regime(
    df: pd.DataFrame,
) -> dict:

    df_closed = _closed(df)

    if df_closed.empty:
        return {
            "regime": "UNKNOWN",
            "adx": 0.0,
            "vol_ratio": 1.0,
            "slope": 0.0,
        }

    adx_val = compute_adx(df)

    tr = compute_true_range(df_closed)

    atr_fast = (
        tr.rolling(7)
        .mean()
        .iloc[-1]
    )

    atr_slow = (
        tr.rolling(28)
        .mean()
        .iloc[-1]
    )

    if pd.isna(atr_slow) or atr_slow <= 0:
        vol_ratio = 1.0
    else:
        vol_ratio = (
            _safe_float(atr_fast, 0.0)
            / atr_slow
        )

    y = (
        df_closed["Close"]
        .tail(20)
        .values
    )

    if len(y) >= 2:

        x = np.arange(len(y))

        slope, _ = np.polyfit(
            x,
            y,
            1,
        )

    else:
        slope = 0.0

    if adx_val >= 25 and vol_ratio >= 1.10:
        regime = "TRENDING_EXPANSION"

    elif adx_val < 20 and vol_ratio < 0.85:
        regime = "ACCUMULATION_DISTRIBUTION"

    elif vol_ratio >= 1.40:
        regime = "HIGH_VOLATILITY_RANGE"

    else:
        regime = "CHOP_LOW_VOLATILITY"

    return {
        "regime": regime,
        "adx": round(adx_val, 2),
        "vol_ratio": round(vol_ratio, 2),
        "slope": round(_safe_float(slope), 4),
    }


# ==============================================================================
# STRUCTURE
# ==============================================================================


def find_swing_points(
    df_closed: pd.DataFrame,
    window: int = SWING_WINDOW,
):

    if df_closed is None:
        return np.array([], dtype=int), np.array([], dtype=int)

    n = len(df_closed)

    win = (
        2 * window + 1
    )

    if n < win:
        return (
            np.array([], dtype=int),
            np.array([], dtype=int),
        )

    highs = df_closed["High"]
    lows = df_closed["Low"]

    roll_max = highs.rolling(
        win,
        center=True,
    ).max()

    roll_min = lows.rolling(
        win,
        center=True,
    ).min()

    is_sh = (
        (highs == roll_max)
        & roll_max.notna()
    )

    is_sl = (
        (lows == roll_min)
        & roll_min.notna()
    )

    return (
        np.where(is_sh.values)[0],
        np.where(is_sl.values)[0],
    )


def measure_displacement(
    df: pd.DataFrame,
    index: int,
) -> float:

    if (
        df is None
        or index < 0
        or index + 3 >= len(df)
    ):
        return 0.0

    hi = _safe_float(
        df["High"].iloc[index]
    )

    lo = _safe_float(
        df["Low"].iloc[index]
    )

    if hi <= 0 or lo <= 0:
        return 0.0

    future = df.iloc[
        index + 1:index + 4
    ]

    bull_disp = (
        future["High"].max() - hi
    ) / hi

    bear_disp = (
        lo - future["Low"].min()
    ) / lo

    return float(
        max(
            0.0,
            bull_disp,
            bear_disp,
        )
    )


def analyze_market_structure(
    df: pd.DataFrame,
):

    df_c = _closed(df)

    if df_c.empty:
        return (
            "NEUTRAL",
            "NONE",
            None,
            None,
        )

    sh_idx, sl_idx = find_swing_points(
        df_c
    )

    if (
        len(sh_idx) < 2
        or len(sl_idx) < 2
    ):
        return (
            "NEUTRAL",
            "NONE",
            None,
            None,
        )

    last_sh = _safe_float(
        df_c["High"].iloc[sh_idx[-1]]
    )

    prev_sh = _safe_float(
        df_c["High"].iloc[sh_idx[-2]]
    )

    last_sl = _safe_float(
        df_c["Low"].iloc[sl_idx[-1]]
    )

    prev_sl = _safe_float(
        df_c["Low"].iloc[sl_idx[-2]]
    )

    close_val = _safe_float(
        df_c["Close"].iloc[-1]
    )

    prior_trend_bullish = (
        last_sh > prev_sh
        and last_sl > prev_sl
    )

    prior_trend_bearish = (
        last_sh < prev_sh
        and last_sl < prev_sl
    )

    if close_val > last_sh:

        displacement = (
            close_val - last_sh
        ) / max(last_sh, 1e-9)

        base = (
            "BULLISH_CHoCH"
            if prior_trend_bearish
            else "BULLISH_BOS"
        )

        structure = (
            base
            if displacement
            >= STRUCTURE_DISPLACEMENT_MIN
            else f"{base}_WEAK"
        )

        return (
            "BUY",
            structure,
            last_sh,
            last_sl,
        )

    if close_val < last_sl:

        displacement = (
            last_sl - close_val
        ) / max(last_sl, 1e-9)

        base = (
            "BEARISH_CHoCH"
            if prior_trend_bullish
            else "BEARISH_BOS"
        )

        structure = (
            base
            if displacement
            >= STRUCTURE_DISPLACEMENT_MIN
            else f"{base}_WEAK"
        )

        return (
            "SELL",
            structure,
            last_sh,
            last_sl,
        )

    return (
        "NEUTRAL",
        "NONE",
        last_sh,
        last_sl,
    )


def detect_choch(
    df: pd.DataFrame,
) -> dict:

    bias, structure, sh, sl = (
        analyze_market_structure(df)
    )

    return {
        "is_choch": "CHoCH" in structure,
        "bias": bias,
        "swing_high": sh,
        "swing_low": sl,
        "structure": structure,
    }


# ==============================================================================
# ORDER BLOCKS
# ==============================================================================


def find_order_block(
    df: pd.DataFrame,
    bias: str,
):

    df_c = _closed(df)

    if df_c.empty or bias not in ("BUY", "SELL"):
        return (
            "NEUTRAL_DEMAND",
            (
                float(df_c["Low"].iloc[-10:].min())
                if not df_c.empty
                else 0.0,
                float(df_c["High"].iloc[-10:].max())
                if not df_c.empty
                else 0.0,
            ),
            False,
            False,
        )

    n = len(df_c)

    for i in range(
        max(10, n - 100),
        n - 4,
    )[::-1]:

        c_open = _safe_float(
            df_c["Open"].iloc[i]
        )

        c_close = _safe_float(
            df_c["Close"].iloc[i]
        )

        c_high = _safe_float(
            df_c["High"].iloc[i]
        )

        c_low = _safe_float(
            df_c["Low"].iloc[i]
        )

        displacement = measure_displacement(
            df_c,
            i,
        )

        if (
            bias == "BUY"
            and c_close < c_open
            and displacement
            >= ORDER_BLOCK_DISPLACEMENT_MIN
        ):

            zone = (
                c_low,
                c_high,
            )

            after = df_c.iloc[i + 4:]

            mitigated = False
            invalidated = False

            if not after.empty:

                if (
                    after["Low"].min()
                    <= c_high
                ):
                    mitigated = True

                if (
                    after["Close"].min()
                    < c_low
                ):
                    invalidated = True

            return (
                "BULLISH_OB",
                zone,
                mitigated,
                invalidated,
            )

        if (
            bias == "SELL"
            and c_close > c_open
            and displacement
            >= ORDER_BLOCK_DISPLACEMENT_MIN
        ):

            zone = (
                c_low,
                c_high,
            )

            after = df_c.iloc[i + 4:]

            mitigated = False
            invalidated = False

            if not after.empty:

                if (
                    after["High"].max()
                    >= c_low
                ):
                    mitigated = True

                if (
                    after["Close"].max()
                    > c_high
                ):
                    invalidated = True

            return (
                "BEARISH_OB",
                zone,
                mitigated,
                invalidated,
            )

    # No directional OB found.
    recent_low = float(
        df_c["Low"].tail(10).min()
    )

    recent_high = float(
        df_c["High"].tail(10).max()
    )

    return (
        "NEUTRAL_DEMAND",
        (
            recent_low,
            recent_high,
        ),
        False,
        False,
    )


def detect_breaker_block(
    df: pd.DataFrame,
    bias: str,
):

    ob_type, zone, _, invalidated = (
        find_order_block(
            df,
            bias,
        )
    )

    if invalidated:

        if bias == "BUY":
            return (
                "BULLISH_BREAKER",
                zone,
            )

        if bias == "SELL":
            return (
                "BEARISH_BREAKER",
                zone,
            )

    return (
        "NONE",
        None,
    )


# ==============================================================================
# FVG
# ==============================================================================


def detect_fvg(
    df: pd.DataFrame,
    lookback: int = FVG_LOOKBACK,
):

    df_c = _closed(df)

    if len(df_c) < 5:
        return None

    n = len(df_c)

    start = max(
        2,
        n - lookback,
    )

    gaps = []

    for i in range(
        start,
        n - 1,
    ):

        prev_high = _safe_float(
            df_c["High"].iloc[i - 1]
        )

        prev_low = _safe_float(
            df_c["Low"].iloc[i - 1]
        )

        next_high = _safe_float(
            df_c["High"].iloc[i + 1]
        )

        next_low = _safe_float(
            df_c["Low"].iloc[i + 1]
        )

        if next_low > prev_high:

            zone = (
                prev_high,
                next_low,
            )

            gap_type = "BULLISH_FVG"

        elif next_high < prev_low:

            zone = (
                next_high,
                prev_low,
            )

            gap_type = "BEARISH_FVG"

        else:
            continue

        future = df_c.iloc[
            i + 2:
        ]

        filled = False

        if not future.empty:

            filled = bool(
                (
                    (
                        future["Low"]
                        <= zone[1]
                    )
                    &
                    (
                        future["High"]
                        >= zone[0]
                    )
                ).any()
            )

        gaps.append(
            {
                "index": i,
                "type": gap_type,
                "zone": zone,
                "filled": filled,
            }
        )

    unfilled = [
        g
        for g in gaps
        if not g["filled"]
    ]

    return (
        unfilled[-1]
        if unfilled
        else None
    )


# ==============================================================================
# LIQUIDITY
# ==============================================================================


def find_equal_levels(
    df: pd.DataFrame,
    lookback: int = EQUAL_LEVEL_LOOKBACK,
    tolerance: float = EQUAL_LEVEL_TOLERANCE,
):

    if df is None or df.empty:
        return [], []

    r = df.tail(lookback)

    def cluster(values):

        vals = np.sort(
            np.asarray(
                values,
                dtype=float,
            )
        )

        vals = vals[
            np.isfinite(vals)
        ]

        groups = []

        if len(vals) == 0:
            return groups

        current = [vals[0]]

        for value in vals[1:]:

            if (
                abs(
                    value
                    - current[-1]
                )
                / max(
                    abs(current[-1]),
                    1e-9,
                )
                <= tolerance
            ):

                current.append(value)

            else:

                if len(current) >= 2:
                    groups.append(
                        float(
                            np.mean(current)
                        )
                    )

                current = [value]

        if len(current) >= 2:
            groups.append(
                float(
                    np.mean(current)
                )
            )

        return groups

    return (
        cluster(r["High"].values),
        cluster(r["Low"].values),
    )


def analyze_liquidity_sweep(
    df: pd.DataFrame,
):

    df_c = _closed(df)

    if len(df_c) < 20:
        return (
            False,
            "NO_SWEEP",
        )

    recent_low = _safe_float(
        df_c["Low"].iloc[-15:-2].min()
    )

    recent_high = _safe_float(
        df_c["High"].iloc[-15:-2].max()
    )

    curr_low = _safe_float(
        df_c["Low"].iloc[-1]
    )

    curr_high = _safe_float(
        df_c["High"].iloc[-1]
    )

    curr_close = _safe_float(
        df_c["Close"].iloc[-1]
    )

    if (
        curr_low < recent_low
        and curr_close > recent_low
    ):
        return (
            True,
            f"SELL-SIDE SWEEP BELOW {recent_low:.2f}",
        )

    if (
        curr_high > recent_high
        and curr_close < recent_high
    ):
        return (
            True,
            f"BUY-SIDE SWEEP ABOVE {recent_high:.2f}",
        )

    eq_highs, eq_lows = (
        find_equal_levels(df_c)
    )

    tolerance = (
        curr_close
        * EQUAL_LEVEL_TOLERANCE
    )

    for eqh in eq_highs:

        if (
            curr_high
            > eqh + tolerance * 0.2
            and curr_close < eqh
        ):

            return (
                True,
                f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {eqh:.2f}",
            )

    for eql in eq_lows:

        if (
            curr_low
            < eql - tolerance * 0.2
            and curr_close > eql
        ):

            return (
                True,
                f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {eql:.2f}",
            )

    return (
        False,
        "NO_SWEEP",
    )


# ==============================================================================
# PREMIUM / DISCOUNT
# ==============================================================================


def calculate_premium_discount(
    df: pd.DataFrame,
    lookback: int = 50,
):

    df_c = _closed(df)

    if df_c.empty:
        return {
            "zone": "UNKNOWN",
            "equilibrium": 0.0,
            "swing_high": 0.0,
            "swing_low": 0.0,
        }

    df_c = df_c.tail(
        lookback
    )

    swing_high = _safe_float(
        df_c["High"].max()
    )

    swing_low = _safe_float(
        df_c["Low"].min()
    )

    equilibrium = (
        swing_high
        + swing_low
    ) / 2.0

    close = _safe_float(
        df_c["Close"].iloc[-1]
    )

    if close > equilibrium:
        zone = "PREMIUM"
    elif close < equilibrium:
        zone = "DISCOUNT"
    else:
        zone = "EQUILIBRIUM"

    return {
        "zone": zone,
        "equilibrium": float(equilibrium),
        "swing_high": float(swing_high),
        "swing_low": float(swing_low),
    }


# ==============================================================================
# SESSION
# ==============================================================================


def get_session_info():

    now_utc = datetime.datetime.now(
        datetime.timezone.utc
    )

    if not _TZ_OK:
        return (
            "UNKNOWN",
            50.0,
        )

    try:

        london_hour = (
            now_utc
            .astimezone(
                ZoneInfo(
                    "Europe/London"
                )
            )
            .hour
        )

        ny_hour = (
            now_utc
            .astimezone(
                ZoneInfo(
                    "America/New_York"
                )
            )
            .hour
        )

        tokyo_hour = (
            now_utc
            .astimezone(
                ZoneInfo(
                    "Asia/Tokyo"
                )
            )
            .hour
        )

        sydney_hour = (
            now_utc
            .astimezone(
                ZoneInfo(
                    "Australia/Sydney"
                )
            )
            .hour
        )

        in_london = (
            8 <= london_hour <= 16
        )

        in_ny = (
            8 <= ny_hour <= 17
        )

        in_tokyo = (
            9 <= tokyo_hour <= 18
        )

        in_sydney = (
            8 <= sydney_hour <= 17
        )

        if in_london and in_ny:
            return (
                "LONDON / NEW YORK OVERLAP",
                95.0,
            )

        if in_london:
            return (
                "LONDON SESSION",
                80.0,
            )

        if in_ny:
            return (
                "NEW YORK SESSION",
                80.0,
            )

        if in_tokyo:
            return (
                "TOKYO SESSION",
                55.0,
            )

        if in_sydney:
            return (
                "SYDNEY SESSION",
                45.0,
            )

        return (
            "OFF-SESSION / LOW LIQUIDITY",
            20.0,
        )

    except Exception:

        return (
            "UNKNOWN",
            50.0,
        )


# ==============================================================================
# TREND STRENGTH
# ==============================================================================


def evaluate_trend_strength(
    df_closed: pd.DataFrame,
    tf_biases: dict,
    regime_info: dict,
    struct_bias: str,
):

    if df_closed is None or df_closed.empty:
        return (
            False,
            "No closed data",
        )

    close = df_closed["Close"]

    ema20 = close.ewm(
        span=20,
        adjust=False,
    ).mean().iloc[-1]

    ema50 = close.ewm(
        span=50,
        adjust=False,
    ).mean().iloc[-1]

    ema200 = None

    if len(close) >= 200:

        ema200 = close.ewm(
            span=200,
            adjust=False,
        ).mean().iloc[-1]

    last_close = _safe_float(
        close.iloc[-1]
    )

    ema_bull = (
        last_close > ema20 > ema50
        and (
            ema200 is None
            or ema50 > ema200
        )
    )

    ema_bear = (
        last_close < ema20 < ema50
        and (
            ema200 is None
            or ema50 < ema200
        )
    )

    adx_ok = (
        regime_info["adx"] >= 20
    )

    bull_count = sum(
        v == "BUY"
        for v in tf_biases.values()
    )

    bear_count = sum(
        v == "SELL"
        for v in tf_biases.values()
    )

    if (
        ema_bull
        and adx_ok
        and bull_count >= 3
        and struct_bias == "BUY"
    ):
        return (
            True,
            "EMA stack + ADX + 3/4 TF aligned bullish",
        )

    if (
        ema_bear
        and adx_ok
        and bear_count >= 3
        and struct_bias == "SELL"
    ):
        return (
            True,
            "EMA stack + ADX + 3/4 TF aligned bearish",
        )

    return (
        False,
        "Trend strength criteria not met",
    )


# ==============================================================================
# POSITION SIZING
# ==============================================================================


def calculate_position_size(
    account_balance_usd,
    risk_pct,
    entry_price,
    stop_loss_price,
    contract_size=100.0,
):

    account_balance_usd = _safe_float(
        account_balance_usd
    )

    risk_pct = _safe_float(
        risk_pct
    )

    entry_price = _safe_float(
        entry_price
    )

    stop_loss_price = _safe_float(
        stop_loss_price
    )

    contract_size = _safe_float(
        contract_size
    )

    if (
        account_balance_usd <= 0
        or risk_pct <= 0
        or entry_price <= 0
        or stop_loss_price <= 0
        or contract_size <= 0
    ):
        return None

    stop_distance = abs(
        entry_price
        - stop_loss_price
    )

    if stop_distance <= 0:
        return None

    risk_amount_usd = (
        account_balance_usd
        * risk_pct
        / 100.0
    )

    lots = (
        risk_amount_usd
        / (
            stop_distance
            * contract_size
        )
    )

    return {
        "risk_amount_usd": round(
            risk_amount_usd,
            2,
        ),
        "stop_distance": round(
            stop_distance,
            4,
        ),
        "lots": round(
            lots,
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

    contract_size = (
        CONTRACT_SIZE_BY_SYMBOL.get(
            symbol,
            1.0,
        )
    )

    result = calculate_position_size(
        account_balance_usd,
        risk_pct,
        entry_price,
        stop_loss_price,
        contract_size,
    )

    if result is not None:
        result["contract_size"] = contract_size

    return result


# ==============================================================================
# SCORING
# ==============================================================================


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

    bull_count = sum(
        v == "BUY"
        for v in tf_biases.values()
    )

    bear_count = sum(
        v == "SELL"
        for v in tf_biases.values()
    )

    tf_score = (
        max(
            bull_count,
            bear_count,
        )
        / 4.0
        * 25.0
    )

    is_weak = struct_type.endswith(
        "_WEAK"
    )

    base_struct = (
        struct_type[:-5]
        if is_weak
        else struct_type
    )

    if "CHoCH" in base_struct:

        struct_score = (
            12.0
            if is_weak
            else 20.0
        )

    elif "BOS" in base_struct:

        struct_score = (
            8.0
            if is_weak
            else 15.0
        )

    else:
        struct_score = 0.0

    if ob_type in (
        "BULLISH_OB",
        "BEARISH_OB",
    ):

        if invalidated:
            ob_score = -10.0

        elif mitigated:
            ob_score = 7.0

        else:
            ob_score = 15.0

    else:
        ob_score = 0.0

    sweep_score = (
        10.0
        if sweep
        else 0.0
    )

    fvg_score = (
        8.0
        if fvg_present
        else 0.0
    )

    rr_score = min(
        12.0,
        max(
            0.0,
            (rr - 1.0) * 6.0,
        ),
    )

    pd_score = 0.0

    if (
        bias == "BUY"
        and pd_zone == "DISCOUNT"
    ):
        pd_score = 10.0

    elif (
        bias == "SELL"
        and pd_zone == "PREMIUM"
    ):
        pd_score = 10.0

    elif (
        bias == "BUY"
        and pd_zone == "PREMIUM"
    ):
        pd_score = -5.0

    elif (
        bias == "SELL"
        and pd_zone == "DISCOUNT"
    ):
        pd_score = -5.0

    trend_score = (
        10.0
        if trend_strong
        else 0.0
    )

    total = (
        tf_score
        + struct_score
        + ob_score
        + sweep_score
        + fvg_score
        + rr_score
        + pd_score
        + trend_score
    )

    return float(
        min(
            100.0,
            max(
                0.0,
                round(
                    total,
                    1,
                ),
            ),
        )
    )


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

    bull = 0.0
    bear = 0.0

    bull_count = sum(
        v == "BUY"
        for v in tf_biases.values()
    )

    bear_count = sum(
        v == "SELL"
        for v in tf_biases.values()
    )

    bull += (
        bull_count
        / 4.0
        * 25.0
    )

    bear += (
        bear_count
        / 4.0
        * 25.0
    )

    is_weak = struct_type.endswith(
        "_WEAK"
    )

    base_struct = (
        struct_type[:-5]
        if is_weak
        else struct_type
    )

    if "CHoCH" in base_struct:

        struct_points = (
            10.0
            if is_weak
            else 20.0
        )

    elif "BOS" in base_struct:

        struct_points = (
            6.0
            if is_weak
            else 15.0
        )

    else:
        struct_points = 0.0

    if "BULLISH" in base_struct:
        bull += struct_points

    elif "BEARISH" in base_struct:
        bear += struct_points

    if (
        ob_type == "BULLISH_OB"
        and not invalidated
    ):

        bull += (
            7.0
            if mitigated
            else 15.0
        )

    elif (
        ob_type == "BEARISH_OB"
        and not invalidated
    ):

        bear += (
            7.0
            if mitigated
            else 15.0
        )

    if sweep:

        if (
            "SELL-SIDE" in sweep_msg
            or "EQUAL-LOWS" in sweep_msg
        ):

            bull += 12.0

        elif (
            "BUY-SIDE" in sweep_msg
            or "EQUAL-HIGHS" in sweep_msg
        ):

            bear += 12.0

    if fvg is not None:

        if (
            fvg["type"]
            == "BULLISH_FVG"
        ):
            bull += 8.0

        elif (
            fvg["type"]
            == "BEARISH_FVG"
        ):
            bear += 8.0

    if pd_zone == "DISCOUNT":
        bull += 8.0

    elif pd_zone == "PREMIUM":
        bear += 8.0

    if macd_trend == "BULLISH":
        bull += 7.0

    elif macd_trend == "BEARISH":
        bear += 7.0

    if rsi_val >= 55:
        bull += 5.0

    elif rsi_val <= 45:
        bear += 5.0

    if trend_strong:

        if bull > bear:
            bull += 10.0

        elif bear > bull:
            bear += 10.0

    return (
        round(
            min(
                100.0,
                bull,
            ),
            1,
        ),
        round(
            min(
                100.0,
                bear,
            ),
            1,
        ),
    )


# ==============================================================================
# MASTER SIGNAL GENERATOR
# ==============================================================================


def generate_omega_signal(
    symbol: str,
    ticker: str,
    min_tf: int = DEFAULT_MIN_TF_AGREEMENT,
    min_score: float = DEFAULT_MIN_SCORE,
    min_rr: float = DEFAULT_MIN_RR,
):

    data, integrity = fetch_mtf_data(
        ticker
    )

    unavailable = [
        tf
        for tf, df in data.items()
        if df is None
    ]

    if unavailable:

        return {
            "ok": False,
            "symbol": symbol,
            "ticker": ticker,
            "reason": (
                "Required timeframe data unavailable: "
                + ", ".join(unavailable)
            ),
            "data_integrity": integrity,
        }

    # ------------------------------------------------------------------
    # MTF
    # ------------------------------------------------------------------

    biases = {}
    structures = {}

    for tf, df in data.items():

        bias, structure, _, _ = (
            analyze_market_structure(df)
        )

        biases[tf] = bias
        structures[tf] = structure

    # ------------------------------------------------------------------
    # Primary 15M analysis
    # ------------------------------------------------------------------

    primary_df = data["15M"]

    (
        struct_bias,
        struct_type,
        swing_high,
        swing_low,
    ) = analyze_market_structure(
        primary_df
    )

    (
        ob_type,
        ob_zone,
        ob_mitigated,
        ob_invalidated,
    ) = find_order_block(
        primary_df,
        struct_bias,
    )

    fvg = detect_fvg(
        primary_df
    )

    sweep, sweep_detail = (
        analyze_liquidity_sweep(
            primary_df
        )
    )

    pd_info = (
        calculate_premium_discount(
            primary_df
        )
    )

    regime_info = (
        compute_market_regime(
            primary_df
        )
    )

    primary_closed = _closed(
        primary_df
    )

    trend_strong, trend_detail = (
        evaluate_trend_strength(
            primary_closed,
            biases,
            regime_info,
            struct_bias,
        )
    )

    eq_highs, eq_lows = (
        find_equal_levels(
            primary_closed
        )
    )

    # ------------------------------------------------------------------
    # Indicators
    # ------------------------------------------------------------------

    rsi_val = compute_rsi(
        primary_closed
    )

    (
        macd_trend,
        macd_line,
        macd_signal,
    ) = compute_macd_trend(
        primary_closed
    )

    (
        vwap_status,
        vwap_value,
    ) = compute_vwap_status(
        primary_closed
    )

    vol_status = vol_status_label(
        regime_info["vol_ratio"]
    )

    ema_cross = compute_ema_cross(
        primary_closed
    )

    bull_score, bear_score = (
        score_bull_bear(
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
            rsi_val,
        )
    )

    # ------------------------------------------------------------------
    # Entry / ATR
    # ------------------------------------------------------------------

    entry = _safe_float(
        primary_closed["Close"].iloc[-1]
    )

    atr_value = compute_atr(
        primary_closed,
        ATR_PERIOD,
    )

    if atr_value <= 0:

        return {
            "ok": False,
            "symbol": symbol,
            "ticker": ticker,
            "reason": "ATR could not be calculated.",
            "data_integrity": integrity,
        }

    # ------------------------------------------------------------------
    # Structural Stop
    # ------------------------------------------------------------------

    atr_floor = atr_value * 1.0

    buffer = atr_value * 0.15

    if struct_bias == "BUY":

        if (
            ob_type == "BULLISH_OB"
            and not ob_invalidated
        ):
            structural_ref = ob_zone[0]

        else:
            structural_ref = (
                swing_low
            )

        if structural_ref is None:
            structural_ref = (
                entry - atr_value * 1.5
            )

        stop = min(
            structural_ref - buffer,
            entry - atr_floor,
        )

        tp1 = (
            entry
            + 1.5 * atr_value
        )

        tp2 = (
            entry
            + 3.0 * atr_value
        )

        tp3 = (
            entry
            + 5.0 * atr_value
        )

    elif struct_bias == "SELL":

        if (
            ob_type == "BEARISH_OB"
            and not ob_invalidated
        ):
            structural_ref = ob_zone[1]

        else:
            structural_ref = (
                swing_high
            )

        if structural_ref is None:
            structural_ref = (
                entry + atr_value * 1.5
            )

        stop = max(
            structural_ref + buffer,
            entry + atr_floor,
        )

        tp1 = (
            entry
            - 1.5 * atr_value
        )

        tp2 = (
            entry
            - 3.0 * atr_value
        )

        tp3 = (
            entry
            - 5.0 * atr_value
        )

    else:

        # No directional setup.
        # Do NOT present these as actionable trade levels.
        stop = entry
        tp1 = entry
        tp2 = entry
        tp3 = entry

    # ------------------------------------------------------------------
    # R:R
    # ------------------------------------------------------------------

    if (
        struct_bias in (
            "BUY",
            "SELL",
        )
        and abs(
            entry - stop
        ) > 0
    ):

        rr = (
            abs(
                tp2 - entry
            )
            / abs(
                entry - stop
            )
        )

    else:

        rr = 0.0

    # ------------------------------------------------------------------
    # Composite score
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # MTF agreement
    # ------------------------------------------------------------------

    bull_count = sum(
        v == "BUY"
        for v in biases.values()
    )

    bear_count = sum(
        v == "SELL"
        for v in biases.values()
    )

    reason = None

    # ------------------------------------------------------------------
    # Signal decision
    # ------------------------------------------------------------------

    if (
        bull_count >= min_tf
        and score >= min_score
        and struct_bias == "BUY"
    ):

        bias = "BUY"

    elif (
        bear_count >= min_tf
        and score >= min_score
        and struct_bias == "SELL"
    ):

        bias = "SELL"

    else:

        bias = "NEUTRAL"

        reason = (
            "Timeframe agreement or score below threshold "
            f"({max(bull_count, bear_count)}/{min_tf} TF, "
            f"{score}/{min_score} score)"
        )

    # ------------------------------------------------------------------
    # HARD R:R BLOCK
    # ------------------------------------------------------------------

    if (
        bias != "NEUTRAL"
        and rr < min_rr
    ):

        reason = (
            f"R:R {rr:.2f} below minimum "
            f"{min_rr:.2f} — signal downgraded to NEUTRAL"
        )

        bias = "NEUTRAL"

    # ------------------------------------------------------------------
    # Safety: invalidated OB cannot independently create a setup.
    # ------------------------------------------------------------------

    if (
        bias != "NEUTRAL"
        and ob_invalidated
    ):

        reason = (
            "Directional order block is invalidated."
        )

        bias = "NEUTRAL"

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    session, session_quality = (
        get_session_info()
    )

    return {
        "ok": True,

        "symbol": symbol,
        "ticker": ticker,

        "data": data,
        "data_integrity": integrity,

        "bias": bias,
        "score": score,

        "entry": entry,
        "stop": stop,

        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,

        "rr": round(
            rr,
            3,
        ),

        "atr": round(
            atr_value,
            4,
        ),

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

        "regime": regime_info,

        "trend_strong": trend_strong,
        "trend_detail": trend_detail,

        "eq_highs": eq_highs,
        "eq_lows": eq_lows,

        "rsi": round(
            rsi_val,
            2,
        ),

        "macd_trend": macd_trend,
        "macd_line": macd_line,
        "macd_signal": macd_signal,

        "vwap_status": vwap_status,
        "vwap_val": vwap_value,

        "vol_status": vol_status,

        "ema_cross": ema_cross,

        "bull_score": bull_score,
        "bear_score": bear_score,

        "bull_tf_count": bull_count,
        "bear_tf_count": bear_count,

        "reason": reason,
    }


# ==============================================================================
# GRADE
# ==============================================================================


def grade(
    score: float,
) -> str:

    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 65:
        return "B"

    if score >= 50:
        return "C"

    return "D"
