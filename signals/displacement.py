"""
SEKWAILA OMEGA X
Institutional Displacement Engine
Version 2.0
"""

import numpy as np


class Displacement:

    def __init__(self, atr_period=14, multiplier=1.8):
        self.atr_period = atr_period
        self.multiplier = multiplier

    def calculate_atr(self, df):

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift()),
                abs(low - close.shift())
            )
        )

        return tr.rolling(self.atr_period).mean()

    def analyze(self, df):

        if df is None or len(df) < 40:
            return None

        atr = self.calculate_atr(df)

        candle = df.iloc[-2]

        size = candle["high"] - candle["low"]

        average = atr.iloc[-2]

        bullish = False
        bearish = False

        strength = 0

        if size > average * self.multiplier:

            if candle["close"] > candle["open"]:

                bullish = True

            else:

                bearish = True

            strength = round(size / average, 2)

        direction = "NONE"

        if bullish:
            direction = "BULLISH"

        elif bearish:
            direction = "BEARISH"

        confidence = min(
            100,
            int(strength * 30)
        )

        return {

            "direction": direction,

            "bullish": bullish,

            "bearish": bearish,

            "strength": strength,

            "confidence": confidence

        }


displacement = Displacement()
