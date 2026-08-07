"""
SEKWAILA OMEGA X
Institutional Market Structure Engine

Detects:
- Swing Highs
- Swing Lows
- BOS
- CHoCH
- Trend Bias

Version 8.0
"""

import pandas as pd
import numpy as np


class MarketStructure:

    def __init__(self, swing_length=5):
        self.swing_length = swing_length
    def _is_swing_high(self, highs, index):

        left = self.swing_length
        right = self.swing_length

        if index < left or index >= len(highs) - right:
            return False

        current = highs[index]

        return (
            current == max(highs[index-left:index+right+1])
            and list(highs[index-left:index+right+1]).count(current) == 1
        )

    def _is_swing_low(self, lows, index):

        left = self.swing_length
        right = self.swing_length

        if index < left or index >= len(lows) - right:
            return False

        current = lows[index]

        return (
            current == min(lows[index-left:index+right+1])
            and list(lows[index-left:index+right+1]).count(current) == 1
        )

    def _find_swings(self, df):

        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        for i in range(len(df)):

            if self._is_swing_high(highs, i):

                swing_highs.append(
                    {
                        "index": i,
                        "price": float(highs[i])
                    }
                )

            if self._is_swing_low(lows, i):

                swing_lows.append(
                    {
                        "index": i,
                        "price": float(lows[i])
                    }
                )

        return swing_highs, swing_lows
            def analyze(self, df):

        if df is None or len(df) < (self.swing_length * 4):
            return None

        swing_highs, swing_lows = self._find_swings(df)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None

        last_high = swing_highs[-1]
        previous_high = swing_highs[-2]

        last_low = swing_lows[-1]
        previous_low = swing_lows[-2]

        close = float(df["close"].iloc[-1])

        trend = "RANGE"

        if (
            last_high["price"] > previous_high["price"]
            and last_low["price"] > previous_low["price"]
        ):
            trend = "BULLISH"

        elif (
            last_high["price"] < previous_high["price"]
            and last_low["price"] < previous_low["price"]
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
            confidence += 20

        confidence = min(confidence, 100)

        return {

            "direction": direction,

            "trend": trend,

            "bos": bos,

            "choch": choch,

            "confidence": confidence,

            "last_high": last_high,

            "last_low": last_low,

            "previous_high": previous_high,

            "previous_low": previous_low,

            "swing_highs": swing_highs,

            "swing_lows": swing_lows

        }
