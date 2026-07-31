from typing import List, Dict


def detect_liquidity_sweeps(
    candles: List[Dict],
    swing_highs: List[Dict],
    swing_lows: List[Dict]
):
    """
    Detect liquidity sweeps.

    A bullish sweep:
        Price wicks below a swing low
        but closes back above it.

    A bearish sweep:
        Price wicks above a swing high
        but closes back below it.
    """

    sweeps = []

    # Bearish Sweep (Buy-side Liquidity Taken)
    for swing in swing_highs:

        level = swing["price"]

        for i in range(swing["index"] + 1, len(candles)):

            candle = candles[i]

            if (
                candle["high"] > level
                and candle["close"] < level
            ):

                sweeps.append({

                    "type": "bearish",

                    "index": i,

                    "level": level,

                    "price": candle["close"]

                })

                break

    # Bullish Sweep (Sell-side Liquidity Taken)
    for swing in swing_lows:

        level = swing["price"]

        for i in range(swing["index"] + 1, len(candles)):

            candle = candles[i]

            if (
                candle["low"] < level
                and candle["close"] > level
            ):

                sweeps.append({

                    "type": "bullish",

                    "index": i,

                    "level": level,

                    "price": candle["close"]

                })

                break

    return sweeps
