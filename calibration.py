"""
SEKWAILA OMEGA X — BROKER PRICE CALIBRATION

No free data feed (yfinance included) will ever match a specific broker's
tick-for-tick price. XAUUSD alone can differ across feeds by several
dollars depending on contract type, session, and update latency.

This module does NOT change the engine's analysis — structure, order
blocks, RSI, etc. are all still computed from the engine's own OHLC data,
because those need a consistent historical series to mean anything. It
only shifts the DISPLAYED price levels (entry/stop/TP1-3) by a fixed
offset the user sets per symbol in Settings > Data, so the numbers on
screen can be lined up with what their broker terminal shows right now.

Because entry/stop/TP1/TP2/TP3 all shift by the same amount, R:R and ATR
are unaffected — only the absolute price levels move.
"""


def apply_offset(result: dict, offset: float) -> dict:
    """Return a shallow copy of an engine result with price levels shifted
    by `offset`. Safe to call with offset=0 (no-op) or on a NEUTRAL/failed
    result (nothing to shift)."""
    if not result or not offset:
        return result
    adjusted = dict(result)
    for key in ("entry", "stop", "tp1", "tp2", "tp3"):
        if key in adjusted and adjusted[key] not in (None, 0):
            adjusted[key] = adjusted[key] + offset
    if "vwap_val" in adjusted and adjusted["vwap_val"]:
        adjusted["vwap_val"] = adjusted["vwap_val"] + offset
    return adjusted
