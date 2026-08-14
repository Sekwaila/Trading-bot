"""
SEKWAILA OMEGA X — SIGNAL ENGINE

Central signal-generation engine.

Responsibilities:
    1. Load market candles.
    2. Run SMC analysis.
    3. Combine structure, liquidity, FVG and order-block signals.
    4. Produce BUY / SELL / NEUTRAL.
    5. Calculate entry, SL, TP1, TP2, TP3.
    6. Calculate risk/reward.
    7. Return a consistent signal dictionary.

Expected project structure:

    signals/
        __init__.py
        signal_engine.py
        order_blocks.py
        fair_value_gap.py
        choch.py
        liquidity.py
        ...

    data/
        market_data.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from data.market_data import get_candles

from signals.order_blocks import detect_order_blocks
from signals.fair_value_gap import detect_fvg
from signals.choch import detect_choch
from signals.liquidity import detect_liquidity_sweep


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_INTERVAL = "5min"
DEFAULT_LIMIT = 150

DEFAULT_MIN_SCORE = 65.0
DEFAULT_MIN_RR = 1.5

TP1_RR = 1.5
TP2_RR = 2.0
TP3_RR = 2.8

# Maximum percentage fallback distance for SL when an
# order-block level cannot be obtained.
DEFAULT_SL_PERCENT = 0.005


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value: Any, default: float = 0.0) -> float:
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


def _normalise_text(value: Any) -> str:
    """Safely convert a value to uppercase text."""

    if value is None:
        return ""

    return str(value).strip().upper()


def _safe_dict(value: Any) -> Dict[str, Any]:
    """Return a dictionary or an empty dictionary."""

    return value if isinstance(value, dict) else {}


def _get_latest_price(df: pd.DataFrame) -> Optional[float]:
    """Extract the latest close price."""

    if df is None or df.empty:
        return None

    if "close" not in df.columns:
        return None

    try:
        price = float(df["close"].iloc[-1])

        if pd.isna(price) or price <= 0:
            return None

        return price

    except (TypeError, ValueError, IndexError):
        return None


def _calculate_rr(
    entry: float,
    stop: float,
    target: float,
) -> float:
    """Calculate risk/reward ratio."""

    risk = abs(entry - stop)

    if risk <= 0:
        return 0.0

    reward = abs(target - entry)

    return round(reward / risk, 2)


def _normalise_signal_score(score: float) -> float:
    """
    Convert an internal signed score to display strength.

    Example:
        +82 -> 82
        -82 -> 82
    """

    return round(min(abs(score), 100.0), 1)


# ============================================================
# SMC ANALYSIS
# ============================================================

def _analyse_smc(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run all available SMC detectors.

    Each detector is isolated so one broken/missing module
    does not crash the entire Streamlit application.
    """

    result: Dict[str, Any] = {
        "choch": "",
        "order_blocks": {},
        "fvg": {},
        "liquidity": "",
        "errors": [],
    }

    # --------------------------------------------------------
    # CHoCH
    # --------------------------------------------------------

    try:
        result["choch"] = _normalise_text(
            detect_choch(df)
        )

    except Exception as exc:
        result["errors"].append(
            f"CHoCH: {exc}"
        )

    # --------------------------------------------------------
    # ORDER BLOCKS
    # --------------------------------------------------------

    try:
        result["order_blocks"] = _safe_dict(
            detect_order_blocks(df)
        )

    except Exception as exc:
        result["errors"].append(
            f"Order Blocks: {exc}"
        )

    # --------------------------------------------------------
    # FAIR VALUE GAP
    # --------------------------------------------------------

    try:
        result["fvg"] = _safe_dict(
            detect_fvg(df)
        )

    except Exception as exc:
        result["errors"].append(
            f"FVG: {exc}"
        )

    # --------------------------------------------------------
    # LIQUIDITY SWEEP
    # --------------------------------------------------------

    try:
        result["liquidity"] = _normalise_text(
            detect_liquidity_sweep(df)
        )

    except Exception as exc:
        result["errors"].append(
            f"Liquidity: {exc}"
        )

    return result


# ============================================================
# SCORE ENGINE
# ============================================================

def _calculate_signal_score(
    analysis: Dict[str, Any],
) -> tuple[float, list[str]]:
    """
    Calculate directional SMC score.

    Positive = bullish
    Negative = bearish
    """

    score = 0.0
    reasons: list[str] = []

    choch = _normalise_text(
        analysis.get("choch")
    )

    liquidity = _normalise_text(
        analysis.get("liquidity")
    )

    fvg = _safe_dict(
        analysis.get("fvg")
    )

    order_blocks = _safe_dict(
        analysis.get("order_blocks")
    )

    # ========================================================
    # CHoCH
    # ========================================================

    if choch == "BULLISH":
        score += 30
        reasons.append("Bullish CHoCH")

    elif choch == "BEARISH":
        score -= 30
        reasons.append("Bearish CHoCH")

    # ========================================================
    # LIQUIDITY
    # ========================================================

    if liquidity in {
        "LIQUIDITY_TAKEN_LOW",
        "BULLISH",
        "LOW_SWEPT",
    }:
        score += 25
        reasons.append("Liquidity Sweep Low")

    elif liquidity in {
        "LIQUIDITY_TAKEN_HIGH",
        "BEARISH",
        "HIGH_SWEPT",
    }:
        score -= 25
        reasons.append("Liquidity Sweep High")

    # ========================================================
    # FAIR VALUE GAP
    # ========================================================

    bullish_fvg = bool(
        fvg.get("bullish_fvg")
        or fvg.get("bullish")
        or fvg.get("bullish_fvg_mitigated")
    )

    bearish_fvg = bool(
        fvg.get("bearish_fvg")
        or fvg.get("bearish")
        or fvg.get("bearish_fvg_mitigated")
    )

    if bullish_fvg:
        score += 20
        reasons.append("Bullish FVG")

    if bearish_fvg:
        score -= 20
        reasons.append("Bearish FVG")

    # ========================================================
    # ORDER BLOCK CONFIRMATION
    # ========================================================

    bullish_ob = (
        order_blocks.get("bullish_ob_low") is not None
        or order_blocks.get("bullish_ob_high") is not None
        or order_blocks.get("bullish_ob") is not None
    )

    bearish_ob = (
        order_blocks.get("bearish_ob_low") is not None
        or order_blocks.get("bearish_ob_high") is not None
        or order_blocks.get("bearish_ob") is not None
    )

    if bullish_ob:
        score += 15
        reasons.append("Bullish Order Block")

    if bearish_ob:
        score -= 15
        reasons.append("Bearish Order Block")

    # ========================================================
    # LIMIT SCORE
    # ========================================================

    score = max(-100.0, min(100.0, score))

    return score, reasons


# ============================================================
# STOP-LOSS CALCULATION
# ============================================================

def _get_buy_stop(
    entry: float,
    order_blocks: Dict[str, Any],
) -> float:
    """Find the best available bullish SL."""

    candidates = []

    for key in (
        "bullish_ob_low",
        "bullish_ob",
        "ob_low",
    ):
        value = order_blocks.get(key)

        if isinstance(value, (int, float)):
            value = float(value)

            if 0 < value < entry:
                candidates.append(value)

    if candidates:
        return min(candidates)

    # Fallback
    return entry * (1.0 - DEFAULT_SL_PERCENT)


def _get_sell_stop(
    entry: float,
    order_blocks: Dict[str, Any],
) -> float:
    """Find the best available bearish SL."""

    candidates = []

    for key in (
        "bearish_ob_high",
        "bearish_ob",
        "ob_high",
    ):
        value = order_blocks.get(key)

        if isinstance(value, (int, float)):
            value = float(value)

            if value > entry:
                candidates.append(value)

    if candidates:
        return max(candidates)

    # Fallback
    return entry * (1.0 + DEFAULT_SL_PERCENT)


# ============================================================
# TARGET CALCULATION
# ============================================================

def _calculate_targets(
    entry: float,
    stop: float,
    direction: str,
) -> Dict[str, float]:
    """
    Calculate TP1, TP2 and TP3 using fixed R multiples.
    """

    risk = abs(entry - stop)

    if risk <= 0:
        return {
            "tp1": 0.0,
            "tp2": 0.0,
            "tp3": 0.0,
        }

    if direction == "BUY":

        tp1 = entry + (risk * TP1_RR)
        tp2 = entry + (risk * TP2_RR)
        tp3 = entry + (risk * TP3_RR)

    else:

        tp1 = entry - (risk * TP1_RR)
        tp2 = entry - (risk * TP2_RR)
        tp3 = entry - (risk * TP3_RR)

    return {
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
    }


# ============================================================
# MAIN SIGNAL GENERATOR
# ============================================================

def generate_omega_signal(
    symbol: str,
    ticker_info: Optional[dict] = None,
    min_tf: int = 2,
    min_score: float = DEFAULT_MIN_SCORE,
    min_rr: float = DEFAULT_MIN_RR,
) -> Dict[str, Any]:
    """
    Generate the primary OMEGA X trading signal.

    Parameters
    ----------
    symbol:
        Trading symbol such as XAUUSD, EURUSD, BTCUSD.

    ticker_info:
        Optional live ticker information.

    min_tf:
        Reserved for multi-timeframe confirmation.

    min_score:
        Minimum absolute score required for BUY/SELL.

    min_rr:
        Minimum acceptable risk/reward.

    Returns
    -------
    dict
        Standardized signal object.
    """

    symbol = str(symbol).strip().upper()

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not symbol:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "reason": "Symbol was not provided.",
        }

    # ========================================================
    # LOAD CANDLES
    # ========================================================

    try:

        df = get_candles(
            symbol,
            interval=DEFAULT_INTERVAL,
            limit=DEFAULT_LIMIT,
        )

    except Exception as exc:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "reason": f"Market data error: {exc}",
        }

    if df is None or df.empty:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "reason": "No market data retrieved.",
            "data_integrity": {
                "candles_loaded": 0,
            },
        }

    # ========================================================
    # VALIDATE OHLC DATA
    # ========================================================

    required_columns = {
        "open",
        "high",
        "low",
        "close",
    }

    missing_columns = required_columns.difference(
        set(df.columns)
    )

    if missing_columns:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "reason": (
                "Market data is missing columns: "
                + ", ".join(sorted(missing_columns))
            ),
            "data_integrity": {
                "candles_loaded": len(df),
            },
        }

    latest_price = _get_latest_price(df)

    if latest_price is None:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "reason": "Latest candle has no valid close price.",
            "data_integrity": {
                "candles_loaded": len(df),
            },
        }

    # ========================================================
    # RUN SMC
    # ========================================================

    analysis = _analyse_smc(df)

    raw_score, reasons = _calculate_signal_score(
        analysis
    )

    display_score = _normalise_signal_score(
        raw_score
    )

    # ========================================================
    # DETERMINE BIAS
    # ========================================================

    if raw_score >= min_score:

        bias = "BUY"

    elif raw_score <= -min_score:

        bias = "SELL"

    else:

        bias = "NEUTRAL"

    # ========================================================
    # DEFAULT OUTPUT
    # ========================================================

    result: Dict[str, Any] = {
        "ok": True,
        "symbol": symbol,
        "bias": bias,
        "score": display_score,
        "raw_score": round(raw_score, 1),
        "entry_price": round(latest_price, 5),
        "stop_loss": 0.0,
        "tp1": 0.0,
        "tp2": 0.0,
        "tp3": 0.0,
        "rr": 0.0,
        "risk": 0.0,
        "reward": 0.0,
        "grade": "C",
        "reason": (
            " + ".join(reasons)
            if reasons
            else "Market Consolidation"
        ),
        "data_integrity": {
            "candles_loaded": len(df),
            "timeframe": DEFAULT_INTERVAL,
            "min_tf": min_tf,
            "smc_errors": analysis.get(
                "errors",
                [],
            ),
        },
        "analysis": {
            "choch": analysis.get(
                "choch",
                "",
            ),
            "liquidity": analysis.get(
                "liquidity",
                "",
            ),
            "fvg": analysis.get(
                "fvg",
                {},
            ),
            "order_blocks": analysis.get(
                "order_blocks",
                {},
            ),
        },
    }

    # ========================================================
    # NEUTRAL
    # ========================================================

    if bias == "NEUTRAL":

        result["grade"] = (
            "B"
            if display_score >= 50
            else "C"
        )

        return result

    # ========================================================
    # CALCULATE STOP
    # ========================================================

    order_blocks = _safe_dict(
        analysis.get("order_blocks")
    )

    if bias == "BUY":

        stop_loss = _get_buy_stop(
            latest_price,
            order_blocks,
        )

    else:

        stop_loss = _get_sell_stop(
            latest_price,
            order_blocks,
        )

    # Safety validation
    if bias == "BUY" and stop_loss >= latest_price:

        stop_loss = latest_price * (
            1.0 - DEFAULT_SL_PERCENT
        )

    if bias == "SELL" and stop_loss <= latest_price:

        stop_loss = latest_price * (
            1.0 + DEFAULT_SL_PERCENT
        )

    risk = abs(
        latest_price - stop_loss
    )

    # ========================================================
    # CALCULATE TARGETS
    # ========================================================

    targets = _calculate_targets(
        latest_price,
        stop_loss,
        bias,
    )

    tp1 = targets["tp1"]
    tp2 = targets["tp2"]
    tp3 = targets["tp3"]

    rr = _calculate_rr(
        latest_price,
        stop_loss,
        tp3,
    )

    # ========================================================
    # RR VALIDATION
    # ========================================================

    if rr < min_rr:

        result.update({
            "bias": "NEUTRAL",
            "reason": (
                f"Signal rejected: RR {rr:.2f} "
                f"is below minimum {min_rr:.2f}."
            ),
            "stop_loss": round(stop_loss, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "rr": rr,
            "risk": round(risk, 5),
        })

        return result

    # ========================================================
    # GRADE
    # ========================================================

    if display_score >= 80 and rr >= 2.5:

        grade = "A"

    elif display_score >= 70 and rr >= 2.0:

        grade = "B"

    elif display_score >= min_score:

        grade = "C"

    else:

        grade = "D"

    # ========================================================
    # FINALIZE RESULT
    # ========================================================

    reward = abs(
        tp3 - latest_price
    )

    result.update({
        "grade": grade,
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
        "rr": rr,
        "risk": round(
            risk,
            5,
        ),
        "reward": round(
            reward,
            5,
        ),
    })

    return result


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def generate_signal(
    symbol: str,
    ticker_info: Optional[dict] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility wrapper.

    Allows older parts of the application to call:

        generate_signal("XAUUSD")

    while using the new OMEGA engine.
    """

    return generate_omega_signal(
        symbol=symbol,
        ticker_info=ticker_info,
        **kwargs,
    )


__all__ = [
    "generate_omega_signal",
    "generate_signal",
]
