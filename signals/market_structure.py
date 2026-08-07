"""
SEKWAILA OMEGA X
Institutional Market Structure Engine
Version 1.0
"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str


class MarketStructure:

    def __init__(self, lookback: int = 3):
        self.lookback = lookback

    # ----------------------------------------------------
    # Detect confirmed (non-repainting) swing highs/lows
    # ----------------------------------------------------
    def detect_swings(self, df):

        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        lb = self.lookback

        for i in range(lb, len(df) - lb):

            # Swing High
            if highs[i] == max(highs[i-lb:i+lb+1]):
                swing_highs.append(
                    SwingPoint(
                        index=i,
                        price=float(highs[i]),
                        kind="HIGH"
                    )
                )

            # Swing Low
            if lows[i] == min(lows[i-lb:i+lb+1]):
                swing_lows.append(
                    SwingPoint(
                        index=i,
                        price=float(lows[i]),
                        kind="LOW"
                    )
                )

        return swing_highs, swing_lows

    # ----------------------------------------------------
    # Build Market Structure
    # ----------------------------------------------------
    def analyze(self, df):

        if df is None:
            return None

        if len(df) < 60:
            return None

        df = df.copy()

        swing_highs, swing_lows = self.detect_swings(df)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None

        last_high = swing_highs[-1]
        previous_high = swing_highs[-2]

        last_low = swing_lows[-1]
        previous_low = swing_lows[-2]

        close = float(df["close"].iloc[-2])

        higher_high = last_high.price > previous_high.price
        lower_high = last_high.price < previous_high.price

        higher_low = last_low.price > previous_low.price
        lower_low = last_low.price < previous_low.price

        trend = "RANGE"

        if higher_high and higher_low:
            trend = "BULLISH"

        elif lower_high and lower_low:
            trend = "BEARISH"

        structure = "NONE"
        bias = "NEUTRAL"

        if close > last_high.price:

            bias = "BUY"

            if trend == "BEARISH":
                structure = "BULLISH_CHOCH"
            else:
                structure = "BULLISH_BOS"

        elif close < last_low.price:

            bias = "SELL"

            if trend == "BULLISH":
                structure = "BEARISH_CHOCH"
            else:
                structure = "BEARISH_BOS"

        confidence = 50

        if trend != "RANGE":
            confidence += 20

        if structure != "NONE":
            confidence += 20

        if bias != "NEUTRAL":
            confidence += 10

        return {

            "trend": trend,

            "bias": bias,

            "structure": structure,

            "last_high": last_high.price,

            "last_low": last_low.price,

            "previous_high": previous_high.price,

            "previous_low": previous_low.price,

            "confidence": confidence,

            "swing_highs": swing_highs,

            "swing_lows": swing_lows

        }


market_structure = MarketStructure()
