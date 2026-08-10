"""
SEKWAILA OMEGA X — SIGNAL CLASSIFICATION LAYER

This module NEVER changes what the engine (signals/signal_engine.py) decided.
It only labels an already-decided BUY/SELL/NEUTRAL bias with a strength tier
(EXTREME / STRONG / plain / WEAK) for display and sorting purposes, using the
engine's own score + timeframe agreement + trend_strong output.

If the engine says NEUTRAL, this always returns NEUTRAL. It cannot invent a
directional signal the engine did not produce.
"""

from config import (
    EXTREME_SCORE_MIN, STRONG_SCORE_MIN, WEAK_SCORE_MAX, EXTREME_MIN_TF_AGREEMENT,
)

# Sort rank — lower number renders first (top of the dashboard).
LEVEL_RANK = {
    "EXTREME BUY": 0,
    "EXTREME SELL": 1,
    "STRONG BUY": 2,
    "STRONG SELL": 3,
    "BUY": 4,
    "SELL": 5,
    "WEAK BUY": 6,
    "WEAK SELL": 7,
    "NEUTRAL": 8,
    "DATA UNAVAILABLE": 9,
}


def classify_signal(result: dict) -> str:
    """Return one of the LEVEL_RANK keys for a generate_omega_signal() result."""
    if not result or not result.get("ok"):
        return "DATA UNAVAILABLE"

    bias = result.get("bias", "NEUTRAL")
    if bias not in ("BUY", "SELL"):
        return "NEUTRAL"

    score = float(result.get("score", 0) or 0)
    agreement = max(int(result.get("bull_tf_count", 0)), int(result.get("bear_tf_count", 0)))
    tf_count = len(result.get("tf_biases", {})) or 4
    trend_strong = bool(result.get("trend_strong"))

    if score >= EXTREME_SCORE_MIN and agreement >= min(EXTREME_MIN_TF_AGREEMENT, tf_count) and trend_strong:
        tier = "EXTREME"
    elif score >= STRONG_SCORE_MIN or (trend_strong and score >= STRONG_SCORE_MIN - 8):
        tier = "STRONG"
    elif score <= WEAK_SCORE_MAX:
        tier = "WEAK"
    else:
        tier = ""

    label = f"{tier} {bias}".strip()
    return label


def level_rank(level: str) -> int:
    return LEVEL_RANK.get(level, 8)


def glow_class(level: str) -> str:
    """Map a classification label to a CSS class suffix used in theme.py."""
    if "EXTREME BUY" == level: return "extreme-buy"
    if "EXTREME SELL" == level: return "extreme-sell"
    if "STRONG BUY" == level: return "strong-buy"
    if "STRONG SELL" == level: return "strong-sell"
    if level == "BUY": return "buy"
    if level == "SELL": return "sell"
    if "WEAK BUY" == level: return "weak-buy"
    if "WEAK SELL" == level: return "weak-sell"
    if level == "DATA UNAVAILABLE": return "unavailable"
    return "neutral"
