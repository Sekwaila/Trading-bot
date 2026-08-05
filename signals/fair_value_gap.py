"""
SEKWAILA OMEGA X V7
Fair Value Gap (FVG) – only unfilled gaps considered
"""

import pandas as pd

class FairValueGap:

    def analyze(self, df):
        if df is None or len(df) < 3:
            return None

        bullish_fvg = False
        bearish_fvg = False
        bullish_top = None
        bullish_bottom = None
        bearish_top = None
        bearish_bottom = None

        # Get current close price for unfilled check
        current_price = float(df.iloc[-1]["close"])

        # Scan from newest to oldest (skip last two candles to have a 3-candle window)
        for i in range(len(df) - 3, 1, -1):
            c1 = df.iloc[i - 1]   # left candle
            c2 = df.iloc[i]       # middle
            c3 = df.iloc[i + 1]   # right candle

            # Bullish FVG: c1.high < c3.low (gap up)
            if c1["high"] < c3["low"]:
                top = float(c3["low"])     # upper boundary (resistance)
                bottom = float(c1["high"]) # lower boundary (support)
                # Unfilled if current price is below the top
                if current_price < top:
                    bullish_fvg = True
                    bullish_top = top
                    bullish_bottom = bottom
                    break   # most recent unfilled bullish FVG found

            # Bearish FVG: c1.low > c3.high (gap down)
            if c1["low"] > c3["high"]:
                top = float(c1["low"])     # upper boundary (resistance)
                bottom = float(c3["high"]) # lower boundary (support)
                # Unfilled if current price is above the bottom
                if current_price > bottom:
                    bearish_fvg = True
                    bearish_top = top
                    bearish_bottom = bottom
                    break   # most recent unfilled bearish FVG found

        return {
            "bullish_fvg": bullish_fvg,
            "bearish_fvg": bearish_fvg,
            "bullish_top": bullish_top,
            "bullish_bottom": bullish_bottom,
            "bearish_top": bearish_top,
            "bearish_bottom": bearish_bottom,
        }

    def detect(self, df):
        result = self.analyze(df)
        if result is None:
            return None
        if result["bullish_fvg"]:
            return "BUY"
        if result["bearish_fvg"]:
            return "SELL"
        return None

fair_value_gap = FairValueGap()
