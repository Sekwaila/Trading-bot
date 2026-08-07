"""
SEKWAILA OMEGA X
Swing Point Detection
Institutional Swing Highs & Swing Lows
"""

import numpy as np


class SwingPoints:

    def __init__(self, lookback=3):
        self.lookback = lookback

    def analyze(self, df):

        if df is None or len(df) < (self.lookback * 2 + 10):
            return None

        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        for i in range(self.lookback, len(df) - self.lookback):

            # Swing High
            if highs[i] == max(highs[i-self.lookback:i+self.lookback+1]):
                swing_highs.append({
                    "index": i,
                    "price": float(highs[i])
                })

            # Swing Low
            if lows[i] == min(lows[i-self.lookback:i+self.lookback+1]):
                swing_lows.append({
                    "index": i,
                    "price": float(lows[i])
                })

        return {
            "swing_highs": swing_highs,
            "swing_lows": swing_lows
        }


swing_points = SwingPoints()
