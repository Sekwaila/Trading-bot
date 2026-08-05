"""
SEKWAILA OMEGA X V7
Fair Value Gap (FVG)
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

        # Scan from newest candles backwards
        for i in range(len(df) - 3, 1, -1):
            c1 = df.iloc[i - 1]
            c2 = df.iloc[i]
            c3 = df.iloc[i + 1]

            # Bullish FVG: c1.high < c3.low
            if c1["high"] < c3["low"]:
                bullish_fvg = True
                bullish_top = float(c3["low"])
                bullish_bottom = float(c1["high"])
                break

            # Bearish FVG: c1.low > c3.high
            if c1["low"] > c3["high"]:
                bearish_fvg = True
                bearish_top = float(c1["low"])
                bearish_bottom = float(c3["high"])
                break

        return {
            "bullish_fvg": bullish_fvg,
            "bearish_fvg": bearish_fvg,
            "bullish_top": bullish_top,
            "bullish_bottom": bullish_bottom,
            "bearish_top": bearish_top,
            "bearish_bottom": bearish_bottom,
        }

    # ----- NEW detect() method -----
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
