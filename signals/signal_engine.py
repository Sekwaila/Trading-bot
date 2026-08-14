"""
SEKWAILA OMEGA X
Signal Engine

Generates BUY / SELL / NEUTRAL signals using the SMC modules.

IMPORTANT:
This file ONLY generates signals.
It does NOT place live trades.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data.market_data import get_candles

from signals.order_blocks import detect_order_blocks
from signals.fair_value_gap import detect_fvg
from signals.choch import detect_choch
from signals.liquidity import detect_liquidity_sweep


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_INTERVAL = "5min"
DEFAULT_CANDLE_LIMIT = 100

DEFAULT_MIN_SCORE = 65.0
DEFAULT_MIN_RR = 1.5

BUY_SL_PERCENT = 0.005
SELL_SL_PERCENT = 0.005


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    try:
        if value is None:
            return default

        result = float(value)

        if pd.isna(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def safe_dict(value: Any) -> dict:
    """Return an empty dictionary if detector output is invalid."""

    if isinstance(value, dict):
        return value

    return {}


def normalise_symbol(symbol: str) -> str:
    """Normalise a trading symbol."""

    return (
        str(symbol)
        .replace("/", "")
        .replace(" ", "")
        .upper()
        .strip()
    )


def get_latest_price(df: pd.DataFrame) -> float:
    """Get the latest valid closing price."""

    if df is None or df.empty:
        return 0.0

    if "close" not in df.columns:
        return 0.0

    closes = pd.to_numeric(
        df["close"],
        errors="coerce"
    ).dropna()

    if closes.empty:
        return 0.0

    return float(closes.iloc[-1])


def valid_stop_loss(
    entry: float,
    stop: float,
    direction: str
) -> bool:
    """Check whether stop loss is on the correct side."""

    if entry <= 0 or stop <= 0:
        return False

    if direction == "BUY":
        return stop < entry

    if direction == "SELL":
        return stop > entry

    return False


# ============================================================
# SIGNAL ENGINE
# ============================================================

def generate_omega_signal(
    symbol: str,
    ticker_info: dict | None = None,
    min_tf: int = 2,
    min_score: float = DEFAULT_MIN_SCORE,
    min_rr: float = DEFAULT_MIN_RR,
    interval: str = DEFAULT_INTERVAL,
    limit: int = DEFAULT_CANDLE_LIMIT,
) -> dict:
    """
    Generate a SEKWAILA OMEGA X signal.

    Returns:
        BUY
        SELL
        NEUTRAL

    This function NEVER executes a trade.
    """

    symbol = normalise_symbol(symbol)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not symbol:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "Invalid symbol.",
        }

    if min_score <= 0:
        min_score = DEFAULT_MIN_SCORE

    if min_rr <= 0:
        min_rr = DEFAULT_MIN_RR

    if limit < 20:
        limit = 20

    # --------------------------------------------------------
    # MARKET DATA
    # --------------------------------------------------------

    try:

        df = get_candles(
            symbol,
            interval=interval,
            limit=limit,
        )

    except Exception as exc:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": f"Market-data error: {exc}",
        }

    # --------------------------------------------------------
    # DATA VALIDATION
    # --------------------------------------------------------

    if df is None:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "Market data returned None.",
        }

    if not isinstance(df, pd.DataFrame):

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "Market data is not a DataFrame.",
        }

    if df.empty:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "No market data retrieved.",
        }

    # --------------------------------------------------------
    # NORMALISE COLUMNS
    # --------------------------------------------------------

    df = df.copy()

    df.columns = [
        str(column).lower().strip()
        for column in df.columns
    ]

    required = {
        "open",
        "high",
        "low",
        "close",
    }

    missing = required - set(df.columns)

    if missing:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": (
                "Missing candle columns: "
                + ", ".join(sorted(missing))
            ),
        }

    for column in required:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "open",
            "high",
            "low",
            "close",
        ]
    )

    if df.empty:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "No valid OHLC candles.",
        }

    # --------------------------------------------------------
    # ENTRY PRICE
    # --------------------------------------------------------

    entry_price = get_latest_price(df)

    if entry_price <= 0:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "signal": "WAIT",
            "reason": "Invalid market price.",
        }

    # --------------------------------------------------------
    # SMC ANALYSIS
    # --------------------------------------------------------

    try:
        choch = detect_choch(df)
    except Exception as exc:
        print(f"[OMEGA] CHoCH error: {exc}")
        choch = "UNKNOWN"

    try:
        order_blocks = safe_dict(
            detect_order_blocks(df)
        )
    except Exception as exc:
        print(f"[OMEGA] Order Block error: {exc}")
        order_blocks = {}

    try:
        fvg = safe_dict(
            detect_fvg(df)
        )
    except Exception as exc:
        print(f"[OMEGA] FVG error: {exc}")
        fvg = {}

    try:
        liquidity = detect_liquidity_sweep(df)
    except Exception as exc:
        print(f"[OMEGA] Liquidity error: {exc}")
        liquidity = "UNKNOWN"

    choch = str(
        choch
    ).upper().strip()

    liquidity = str(
        liquidity
    ).upper().strip()

    # --------------------------------------------------------
    # SCORING
    # --------------------------------------------------------

    score = 0.0

    reasons = []

    # ========================================================
    # BULLISH
    # ========================================================

    if choch == "BULLISH":

        score += 30

        reasons.append(
            "Bullish CHoCH"
        )

    if liquidity in (
        "LIQUIDITY_TAKEN_LOW",
        "BULLISH_SWEEP",
        "BULLISH",
    ):

        score += 30

        reasons.append(
            "Liquidity Sweep Low"
        )

    if bool(
        fvg.get("bullish_fvg")
    ):

        score += 25

        reasons.append(
            "Bullish FVG"
        )

    # ========================================================
    # BEARISH
    # ========================================================

    if choch == "BEARISH":

        score -= 30

        reasons.append(
            "Bearish CHoCH"
        )

    if liquidity in (
        "LIQUIDITY_TAKEN_HIGH",
        "BEARISH_SWEEP",
        "BEARISH",
    ):

        score -= 30

        reasons.append(
            "Liquidity Sweep High"
        )

    if bool(
        fvg.get("bearish_fvg")
    ):

        score -= 25

        reasons.append(
            "Bearish FVG"
        )

    # --------------------------------------------------------
    # DETERMINE BIAS
    # --------------------------------------------------------

    if score >= min_score:

        bias = "BUY"

    elif score <= -min_score:

        bias = "SELL"

    else:

        bias = "NEUTRAL"

    # --------------------------------------------------------
    # STOP LOSS / TARGETS
    # --------------------------------------------------------

    stop_loss = 0.0
    tp1 = 0.0
    tp2 = 0.0
    tp3 = 0.0

    risk_distance = 0.0

    # ========================================================
    # BUY
    # ========================================================

    if bias == "BUY":

        candidates = [
            order_blocks.get(
                "bullish_ob_low"
            ),

            order_blocks.get(
                "bullish_ob"
            ),

            order_blocks.get(
                "ob_low"
            ),
        ]

        for value in candidates:

            candidate = safe_float(value)

            if candidate > 0:

                stop_loss = candidate

                break

        # Fallback SL
        if not valid_stop_loss(
            entry_price,
            stop_loss,
            "BUY",
        ):

            stop_loss = (
                entry_price
                * (1 - BUY_SL_PERCENT)
            )

        risk_distance = (
            entry_price - stop_loss
        )

        if risk_distance > 0:

            tp1 = (
                entry_price
                + risk_distance * 1.5
            )

            tp2 = (
                entry_price
                + risk_distance * min_rr
            )

            tp3 = (
                entry_price
                + risk_distance * 3.0
            )

    # ========================================================
    # SELL
    # ========================================================

    elif bias == "SELL":

        candidates = [
            order_blocks.get(
                "bearish_ob_high"
            ),

            order_blocks.get(
                "bearish_ob"
            ),

            order_blocks.get(
                "ob_high"
            ),
        ]

        for value in candidates:

            candidate = safe_float(value)

            if candidate > 0:

                stop_loss = candidate

                break

        # Fallback SL
        if not valid_stop_loss(
            entry_price,
            stop_loss,
            "SELL",
        ):

            stop_loss = (
                entry_price
                * (1 + SELL_SL_PERCENT)
            )

        risk_distance = (
            stop_loss - entry_price
        )

        if risk_distance > 0:

            tp1 = (
                entry_price
                - risk_distance * 1.5
            )

            tp2 = (
                entry_price
                - risk_distance * min_rr
            )

            tp3 = (
                entry_price
                - risk_distance * 3.0
            )

    # --------------------------------------------------------
    # RISK / REWARD
    # --------------------------------------------------------

    risk_reward = 0.0

    if risk_distance > 0:

        if bias == "BUY":

            reward = (
                tp2 - entry_price
            )

            risk_reward = (
                reward / risk_distance
            )

        elif bias == "SELL":

            reward = (
                entry_price - tp2
            )

            risk_reward = (
                reward / risk_distance
            )

    # --------------------------------------------------------
    # GRADE
    # --------------------------------------------------------

    absolute_score = abs(score)

    if absolute_score >= 85:

        grade = "A+"

    elif absolute_score >= 75:

        grade = "A"

    elif absolute_score >= 65:

        grade = "B"

    elif absolute_score >= 50:

        grade = "C"

    else:

        grade = "D"

    # --------------------------------------------------------
    # SIGNAL NAME
    # --------------------------------------------------------

    if bias == "BUY":

        signal = "STRONG BUY"

    elif bias == "SELL":

        signal = "STRONG SELL"

    else:

        signal = "WAIT"

    # --------------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------------

    current_price = entry_price

    if isinstance(
        ticker_info,
        dict
    ):

        ticker_value = (
            ticker_info.get("price")
            or ticker_info.get("current_price")
            or ticker_info.get("quote")
        )

        ticker_value = safe_float(
            ticker_value
        )

        if ticker_value > 0:

            current_price = ticker_value

    # --------------------------------------------------------
    # REASON
    # --------------------------------------------------------

    if reasons:

        reason = " + ".join(
            reasons
        )

    else:

        reason = (
            "Market Consolidation"
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {

        "ok": True,

        "symbol": symbol,

        "bias": bias,

        "signal": signal,

        "score": round(
            absolute_score,
            2,
        ),

        "grade": grade,

        "entry_price": round(
            entry_price,
            5,
        ),

        "current_price": round(
            current_price,
            5,
        ),

        "stop_loss": round(
            stop_loss,
            5,
        ),

        "tp1": round(
            tp1,
            5,
        ),

        "tp2": round(
            tp2,
            5,
        ),

        "tp3": round(
            tp3,
            5,
        ),

        "risk_distance": round(
            risk_distance,
            5,
        ),

        "risk_reward": round(
            risk_reward,
            2,
        ),

        "reason": reason,

        "smc": {

            "choch": choch,

            "liquidity_sweep": liquidity,

            "bullish_fvg": bool(
                fvg.get(
                    "bullish_fvg"
                )
            ),

            "bearish_fvg": bool(
                fvg.get(
                    "bearish_fvg"
                )
            ),

            "order_blocks": order_blocks,
        },

        "data_integrity": {

            "candles_loaded": int(
                len(df)
            ),

            "interval": interval,

            "min_tf": min_tf,
        },

        # This is deliberately FALSE.
        # The signal engine must never place a trade.
        "execution": {

            "executed": False,

            "mode": "SIGNAL_ONLY",
        },
    }


__all__ = [
    "generate_omega_signal",
]
