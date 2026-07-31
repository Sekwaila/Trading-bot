from typing import List, Dict


def detect_order_blocks(
    candles: List[Dict],
    bos_events: List[Dict]
):
    """
    Detect simple bullish and bearish order blocks.

    Bullish OB:
        Last bearish candle before a bullish BOS.

    Bearish OB:
        Last bullish candle before a bearish BOS.
    """

    order_blocks = []

    for bos in bos_events:

        idx = bos["index"]

        if bos["type"] == "bullish":

            for i in range(idx - 1, -1, -1):

                candle = candles[i]

                if candle["close"] < candle["open"]:

                    order_blocks.append({

                        "type": "bullish",

                        "index": i,

                        "high": candle["high"],

                        "low": candle["low"]

                    })

                    break

        else:

            for i in range(idx - 1, -1, -1):

                candle = candles[i]

                if candle["close"] > candle["open"]:

                    order_blocks.append({

                        "type": "bearish",

                        "index": i,

                        "high": candle["high"],

                        "low": candle["low"]

                    })

                    break

    return order_blocks
