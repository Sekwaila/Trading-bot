"""
SEKWAILA OMEGA X
Institutional Market Structure Engine

Version 9.0
"""

import numpy as np


class MarketStructure:

    def __init__(self, swing_length=5):
        self.swing_length = swing_length

    def _find_swings(self, df):
        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        w = self.swing_length

        for i in range(w, len(df) - w):

            if highs[i] == max(highs[i-w:i+w+1]):
                if list(highs[i-w:i+w+1]).count(highs[i]) == 1:
                    swing_highs.append(
                        {
                            "index": i,
                            "price": float(highs[i])
                        }
                    )

            if lows[i] == min(lows[i-w:i+w+1]):
                if list(lows[i-w:i+w+1]).count(lows[i]) == 1:
                    swing_lows.append(
                        {
                            "index": i,
                            "price": float(lows[i])
                        }
                    )

        return swing_highs, swing_lows

    def analyze(self, df):

        if df is None:
            return None

        if len(df) < (self.swing_length * 4):
            return None

        swing_highs, swing_lows = self._find_swings(df)

        if len(swing_highs) < 2:
            return None

        if len(swing_lows) < 2:
            return None

        last_high = swing_highs[-1]
        previous_high = swing_highs[-2]

        last_low = swing_lows[-1]
        previous_low = swing_lows[-2]

        close = float(df["close"].iloc[-1])

        trend = "RANGE"

        if (
            last_high["price"] > previous_high["price"]
            and
            last_low["price"] > previous_low["price"]
        ):
            trend = "BULLISH"

        elif (
            last_high["price"] < previous_high["price"]
            and
            last_low["price"] < previous_low["price"]
        ):
            trend = "BEARISH"

        bos = False
        choch = False
        direction = "NEUTRAL"

        if close > last_high["price"]:

            bos = True
            direction = "BUY"

            if trend == "BEARISH":
                choch = True

        elif close < last_low["price"]:

            bos = True
            direction = "SELL"

            if trend == "BULLISH":
                choch = True

        confidence = 50

        if bos:
            confidence += 25

        if choch:
            confidence += 25

        confidence = min(confidence, 100)

        return {

            "direction": direction,
            "trend": trend,
            "bos": bos,
            "choch": choch,
            "confidence": confidence,

            "last_high": last_high,
            "previous_high": previous_high,

            "last_low": last_low,
            "previous_low": previous_low,

            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
        }


market_structure = MarketStructure()
