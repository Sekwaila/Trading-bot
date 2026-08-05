"""
SEKWAILA OMEGA X V7
Smart Money Market Structure
"""

import pandas as pd

class MarketStructure:

    def analyze(self, df, lookback=3):
        if df is None or df.empty:
            return None

        df = df.copy()
        df["swing_high"] = False
        df["swing_low"] = False

        for i in range(lookback, len(df) - lookback):
            high = df["high"].iloc[i]
            low = df["low"].iloc[i]

            if high == max(df["high"].iloc[i - lookback:i + lookback + 1]):
                df.loc[df.index[i], "swing_high"] = True

            if low == min(df["low"].iloc[i - lookback:i + lookback + 1]):
                df.loc[df.index[i], "swing_low"] = True

        swing_highs = df[df["swing_high"]]
        swing_lows = df[df["swing_low"]]

        last_high = None
        last_low = None
        if not swing_highs.empty:
            last_high = float(swing_highs.iloc[-1]["high"])
        if not swing_lows.empty:
            last_low = float(swing_lows.iloc[-1]["low"])

        price = float(df.iloc[-1]["close"])
        bullish_bos = (last_high is not None and price > last_high)
        bearish_bos = (last_low is not None and price < last_low)

        return {
            "price": price,
            "last_high": last_high,
            "last_low": last_low,
            "bullish_bos": bullish_bos,
            "bearish_bos": bearish_bos,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
        }

    # ----- NEW detect() method -----
    def detect(self, df):
        result = self.analyze(df)
        if result is None:
            return None
        if result["bullish_bos"]:
            return "BUY"
        if result["bearish_bos"]:
            return "SELL"
        return None

market_structure = MarketStructure()
