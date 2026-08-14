"""
SEKWAILA OMEGA X
Signal Engine

Self-contained technical signal engine.

It does not execute trades.
It does not depend on the other SMC modules.

It calculates:
- trend
- momentum
- structure
- liquidity sweep
- ATR
- support/resistance
- entry
- stop loss
- TP1
- TP2
- TP3
- risk/reward
- score
- grade
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from data.market_data import get_candles


def _empty_result(
    symbol: str,
    reason: str,
) -> Dict[str, Any]:

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
        "reason": reason,
        "data_integrity": {
            "candles_loaded": 0,
        },
    }


def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:

    previous_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(
        period,
        min_periods=1,
    ).mean()


def _calculate_ema(
    series: pd.Series,
    period: int,
) -> pd.Series:

    return series.ewm(
        span=period,
        adjust=False,
    ).mean()


def _calculate_rsi(
    close: pd.Series,
    period: int = 14,
) -> pd.Series:

    delta = close.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(
        period,
        min_periods=period,
    ).mean()

    avg_loss = losses.rolling(
        period,
        min_periods=period,
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi.fillna(50.0)


def _grade(score: float) -> str:

    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 65:
        return "B"

    if score >= 55:
        return "C"

    return "D"


def generate_omega_signal(
    symbol: str,
    ticker_info: dict | None = None,
    min_tf: int = 2,
    min_score: float = 60.0,
    min_rr: float = 1.5,
) -> Dict[str, Any]:

    del ticker_info
    del min_tf

    df = get_candles(
        symbol,
        interval="5min",
        limit=150,
    )

    if df.empty:
        return _empty_result(
            symbol,
            "No market data retrieved.",
        )

    if len(df) < 30:
        return _empty_result(
            symbol,
            f"Insufficient candles: {len(df)}.",
        )

    df = df.copy()

    df["ema20"] = _calculate_ema(
        df["close"],
        20,
    )

    df["ema50"] = _calculate_ema(
        df["close"],
        50,
    )

    df["rsi"] = _calculate_rsi(
        df["close"],
        14,
    )

    df["atr"] = _calculate_atr(
        df,
        14,
    )

    latest = df.iloc[-1]

    entry = float(latest["close"])
    ema20 = float(latest["ema20"])
    ema50 = float(latest["ema50"])
    rsi = float(latest["rsi"])
    atr = float(latest["atr"])

    if not np.isfinite(atr) or atr <= 0:
        atr = max(
            entry * 0.001,
            0.00001,
        )

    score = 50.0
    reasons = []

    # ----------------------------------------------------------
    # TREND
    # ----------------------------------------------------------

    if ema20 > ema50:
        score += 15
        reasons.append("EMA trend bullish")

    elif ema20 < ema50:
        score -= 15
        reasons.append("EMA trend bearish")

    # ----------------------------------------------------------
    # MOMENTUM
    # ----------------------------------------------------------

    if rsi >= 55:
        score += 10
        reasons.append("RSI bullish momentum")

    elif rsi <= 45:
        score -= 10
        reasons.append("RSI bearish momentum")

    # ----------------------------------------------------------
    # RECENT STRUCTURE
    # ----------------------------------------------------------

    recent = df.tail(20)

    recent_high = float(
        recent["high"].iloc[:-1].max()
    )

    recent_low = float(
        recent["low"].iloc[:-1].min()
    )

    if entry > recent_high:
        score += 15
        reasons.append("Bullish structure breakout")

    elif entry < recent_low:
        score -= 15
        reasons.append("Bearish structure breakout")

    # ----------------------------------------------------------
    # LIQUIDITY SWEEP
    # ----------------------------------------------------------

    previous_high = float(
        df["high"].iloc[-3]
    )

    previous_low = float(
        df["low"].iloc[-3]
    )

    current_high = float(
        df["high"].iloc[-1]
    )

    current_low = float(
        df["low"].iloc[-1]
    )

    current_close = float(
        df["close"].iloc[-1]
    )

    # Sweep high then close lower = bearish.
    if (
        current_high > previous_high
        and current_close < previous_high
    ):
        score -= 10
        reasons.append("High liquidity sweep")

    # Sweep low then close higher = bullish.
    elif (
        current_low < previous_low
        and current_close > previous_low
    ):
        score += 10
        reasons.append("Low liquidity sweep")

    # ----------------------------------------------------------
    # CLAMP
    # ----------------------------------------------------------

    score = max(
        0.0,
        min(100.0, score),
    )

    # ----------------------------------------------------------
    # BIAS
    # ----------------------------------------------------------

    if score >= min_score:
        bias = "BUY"

    elif score <= (100.0 - min_score):
        bias = "SELL"

    else:
        bias = "NEUTRAL"

    # ----------------------------------------------------------
    # TRADE LEVELS
    # ----------------------------------------------------------

    if bias == "BUY":

        stop = entry - (
            atr * 1.5
        )

        risk = entry - stop

        tp1 = entry + (
            risk * 1.5
        )

        tp2 = entry + (
            risk * min_rr
        )

        tp3 = entry + (
            risk * 3.0
        )

    elif bias == "SELL":

        stop = entry + (
            atr * 1.5
        )

        risk = stop - entry

        tp1 = entry - (
            risk * 1.5
        )

        tp2 = entry - (
            risk * min_rr
        )

        tp3 = entry - (
            risk * 3.0
        )

    else:

        stop = 0.0
        tp1 = 0.0
        tp2 = 0.0
        tp3 = 0.0
        risk = 0.0

    rr = 0.0

    if risk > 0 and bias in ("BUY", "SELL"):
        rr = abs(tp2 - entry) / risk

    return {
        "ok": True,
        "symbol": symbol,
        "bias": bias,
        "score": round(score, 1),
        "grade": _grade(score),
        "entry_price": round(entry, 5),
        "stop_loss": round(stop, 5),
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
        "rr": round(rr, 2),
        "reason": (
            " + ".join(reasons)
            if reasons
            else "Market consolidation"
        ),
        "data_integrity": {
            "candles_loaded": len(df),
            "timeframe": "5min",
        },
    }


__all__ = [
    "generate_omega_signal",
]
