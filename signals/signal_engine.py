"""
SEKWAILA OMEGA X
Smart Money Concepts signal engine.

The engine:
- loads current candles
- evaluates SMC modules
- calculates BUY / SELL / NEUTRAL
- calculates dynamic SL
- calculates TP1 / TP2 / TP3
- calculates RR
- never uses hard-coded XAUUSD prices
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from data.market_data import get_candles


from .order_blocks import detect_order_blocks
from .fair_value_gap import detect_fvg
from .choch import detect_choch
from .liquidity import detect_liquidity_sweep


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _atr(
    df: pd.DataFrame,
    period: int = 14,
) -> float:

    if len(df) < 2:
        return 0.0

    high = df["high"]
    low = df["low"]
    close = df["close"]

    previous_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    value = tr.rolling(
        period,
        min_periods=3,
    ).mean().iloc[-1]

    return _safe_float(value)


def _normalize_fvg(
    fvg: Any,
) -> dict:

    if isinstance(fvg, dict):
        return fvg

    return {}


def _normalize_ob(
    ob: Any,
) -> dict:

    if isinstance(ob, dict):
        return ob

    return {}


def _build_levels(
    df: pd.DataFrame,
    bias: str,
    entry: float,
    ob: dict,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
]:

    atr = _atr(df)

    if atr <= 0:
        atr = abs(entry) * 0.002

    recent_low = _safe_float(
        df["low"].tail(20).min(),
        entry - atr,
    )

    recent_high = _safe_float(
        df["high"].tail(20).max(),
        entry + atr,
    )

    if bias == "BUY":

        ob_low = _safe_float(
            ob.get("bullish_ob_low"),
            0.0,
        )

        # Prefer structure, but never allow SL above entry.
        candidates = [
            x
            for x in (
                ob_low,
                recent_low,
            )
            if 0 < x < entry
        ]

        if candidates:
            sl = min(candidates)
        else:
            sl = entry - atr * 1.2

        # Ensure enough room for a meaningful trade.
        risk = entry - sl

        minimum_risk = atr * 0.8

        if risk < minimum_risk:
            risk = minimum_risk
            sl = entry - risk

        tp1 = entry + risk * 1.5
        tp2 = entry + risk * 2.0
        tp3 = entry + risk * 3.0

        rr = (
            (tp2 - entry) / risk
            if risk > 0
            else 0.0
        )

        return (
            sl,
            tp1,
            tp2,
            tp3,
            rr,
        )

    if bias == "SELL":

        ob_high = _safe_float(
            ob.get("bearish_ob_high"),
            0.0,
        )

        candidates = [
            x
            for x in (
                ob_high,
                recent_high,
            )
            if x > entry
        ]

        if candidates:
            sl = max(candidates)
        else:
            sl = entry + atr * 1.2

        risk = sl - entry

        minimum_risk = atr * 0.8

        if risk < minimum_risk:
            risk = minimum_risk
            sl = entry + risk

        tp1 = entry - risk * 1.5
        tp2 = entry - risk * 2.0
        tp3 = entry - risk * 3.0

        rr = (
            (entry - tp2) / risk
            if risk > 0
            else 0.0
        )

        return (
            sl,
            tp1,
            tp2,
            tp3,
            rr,
        )

    return (
        entry,
        entry,
        entry,
        entry,
        0.0,
    )


def generate_omega_signal(
    symbol: str,
    ticker_info: dict | None = None,
    min_tf: int = 2,
    min_score: float = 65.0,
    min_rr: float = 1.5,
) -> Dict[str, Any]:
    """
    Generate a complete Omega signal.

    Returns:
        {
            ok,
            symbol,
            bias,
            score,
            grade,
            entry_price,
            stop_loss,
            tp1,
            tp2,
            tp3,
            rr,
            reason,
            data_integrity
        }
    """

    symbol = (
        str(symbol)
        .upper()
        .replace("/", "")
        .strip()
    )

    # --------------------------------------------------------
    # LOAD MARKET DATA
    # --------------------------------------------------------

    df = get_candles(
        symbol,
        interval="5min",
        limit=150,
    )

    if df.empty or len(df) < 30:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "grade": "N/A",
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "tp1": 0.0,
            "tp2": 0.0,
            "tp3": 0.0,
            "rr": 0.0,
            "reason": (
                "Insufficient market data."
            ),
            "data_integrity": {
                "candles_loaded": len(df),
            },
        }

    # --------------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------------

    latest_price = _safe_float(
        df["close"].iloc[-1]
    )

    if latest_price <= 0:

        return {
            "ok": False,
            "symbol": symbol,
            "bias": "NEUTRAL",
            "score": 0.0,
            "grade": "N/A",
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "tp1": 0.0,
            "tp2": 0.0,
            "tp3": 0.0,
            "rr": 0.0,
            "reason": "Invalid latest price.",
            "data_integrity": {
                "candles_loaded": len(df),
            },
        }

    # --------------------------------------------------------
    # SMC ANALYSIS
    # --------------------------------------------------------

    try:
        choch = detect_choch(df)
    except Exception as exc:
        print(f"[CHoCH] {exc}")
        choch = "NEUTRAL"

    try:
        ob = _normalize_ob(
            detect_order_blocks(df)
        )
    except Exception as exc:
        print(f"[Order Block] {exc}")
        ob = {}

    try:
        fvg = _normalize_fvg(
            detect_fvg(df)
        )
    except Exception as exc:
        print(f"[FVG] {exc}")
        fvg = {}

    try:
        sweep = detect_liquidity_sweep(df)
    except Exception as exc:
        print(f"[Liquidity] {exc}")
        sweep = "NONE"

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0.0
    reasons = []

    choch = str(choch).upper()
    sweep = str(sweep).upper()

    # Bullish.
    if choch == "BULLISH":
        score += 30
        reasons.append(
            "Bullish CHoCH"
        )

    if sweep == "LIQUIDITY_TAKEN_LOW":
        score += 30
        reasons.append(
            "Liquidity sweep low"
        )

    if fvg.get("bullish_fvg"):
        score += 25
        reasons.append(
            "Bullish FVG"
        )

    # Bearish.
    if choch == "BEARISH":
        score -= 30
        reasons.append(
            "Bearish CHoCH"
        )

    if sweep == "LIQUIDITY_TAKEN_HIGH":
        score -= 30
        reasons.append(
            "Liquidity sweep high"
        )

    if fvg.get("bearish_fvg"):
        score -= 25
        reasons.append(
            "Bearish FVG"
        )

    # --------------------------------------------------------
    # BIAS
    # --------------------------------------------------------

    if score >= min_score:
        bias = "BUY"

    elif score <= -min_score:
        bias = "SELL"

    else:
        bias = "NEUTRAL"

    absolute_score = min(
        abs(score),
        100.0,
    )

    # --------------------------------------------------------
    # LEVELS
    # --------------------------------------------------------

    (
        sl,
        tp1,
        tp2,
        tp3,
        rr,
    ) = _build_levels(
        df,
        bias,
        latest_price,
        ob,
    )

    # A signal should not claim a qualifying RR when it doesn't.
    qualified = (
        bias in {"BUY", "SELL"}
        and rr >= min_rr
    )

    if bias != "NEUTRAL" and not qualified:

        reasons.append(
            f"RR below minimum {min_rr:.1f}"
        )

    # --------------------------------------------------------
    # GRADE
    # --------------------------------------------------------

    if absolute_score >= 85:
        grade = "A+"

    elif absolute_score >= 75:
        grade = "A"

    elif absolute_score >= 65:
        grade = "B"

    elif absolute_score >= 55:
        grade = "C"

    else:
        grade = "D"

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "ok": True,
        "symbol": symbol,
        "bias": bias if qualified else "NEUTRAL",
        "score": round(
            absolute_score,
            1,
        ),
        "grade": grade,
        "entry_price": round(
            latest_price,
            5,
        ),
        "stop_loss": round(
            sl,
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
        "rr": round(
            rr,
            2,
        ),
        "reason": (
            " + ".join(reasons)
            if reasons
            else "Market consolidation"
        ),
        "data_integrity": {
            "candles_loaded": len(df),
            "interval": "5min",
            "latest_candle": (
                str(df["datetime"].iloc[-1])
                if "datetime" in df.columns
                else ""
            ),
        },
    }


__all__ = [
    "generate_omega_signal",
]
