"""
SEKWAILA OMEGA X V7
Smart Money Order Blocks
"""

import pandas as pd

class OrderBlocks:

    def analyze(self, df):
        if df is None or len(df) < 10:
            return None

        bullish_block = None
        bearish_block = None

        # Search for the most recent bullish order block
        # (bearish candle that is immediately followed by a bullish breakout)
        for i in range(len(df) - 2, 1, -1):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]
            if (
                prev["close"] < prev["open"] and          # bearish candle
                curr["close"] > prev["high"]             # bullish breakout above its high
            ):
                bullish_block = {
                    "high": float(prev["high"]),
                    "low": float(prev["low"]),
                    "index": i - 1,                       # index of the block candle
                }
                break

        # Search for the most recent bearish order block
        # (bullish candle that is immediately followed by a bearish breakdown)
        for i in range(len(df) - 2, 1, -1):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]
            if (
                prev["close"] > prev["open"] and          # bullish candle
                curr["close"] < prev["low"]              # bearish breakdown below its low
            ):
                bearish_block = {
                    "high": float(prev["high"]),
                    "low": float(prev["low"]),
                    "index": i - 1,
                }
                break

        # Determine which block is more recent (higher index) and use it as the dominant signal
        bullish = bullish_block is not None
        bearish = bearish_block is not None
        signal = None
        if bullish and bearish:
            if bullish_block["index"] > bearish_block["index"]:
                signal = "BUY"
            else:
                signal = "SELL"
        elif bullish:
            signal = "BUY"
        elif bearish:
            signal = "SELL"

        return {
            "bullish_ob": bullish,
            "bearish_ob": bearish,
            "bullish_zone": bullish_block,
            "bearish_zone": bearish_block,
            "signal": signal,                     # dominant signal based on recency
        }

    def detect(self, df):
        result = self.analyze(df)
        if result is None:
            return None
        return result.get("signal")

order_blocks = OrderBlocks()
