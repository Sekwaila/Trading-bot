from typing import List, Dict


def detect_bos(
    candles: List[Dict],
    swing_highs: List[Dict],
    swing_lows: List[Dict]
):
    """
    Detect Break of Structure (BOS).

    Returns a list of bullish and bearish BOS events.
    """

    events = []

    # Bullish BOS
    for swing in swing_highs:

        idx = swing["index"]

        if idx >= len(candles) - 1:
            continue

        level = swing["price"]

        for i in range(idx + 1, len(candles)):

            if candles[i]["close"] > level:

                events.append({

                    "type": "bullish",

                    "index": i,

                    "level": level,

                    "price": candles[i]["close"]

                })

                break

    # Bearish BOS
    for swing in swing_lows:

        idx = swing["index"]

        if idx >= len(candles) - 1:
            continue

        level = swing["price"]

        for i in range(idx + 1, len(candles)):

            if candles[i]["close"] < level:

                events.append({

                    "type": "bearish",

                    "index": i,

                    "level": level,

                    "price": candles[i]["close"]

                })

                break

    return events
