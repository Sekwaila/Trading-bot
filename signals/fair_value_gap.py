"""
SEKWAILA OMEGA X
Institutional Fair Value Gap Engine
Version 2.0
"""


class FairValueGap:

    def __init__(self, min_gap_percent=0.0005):
        self.min_gap_percent = min_gap_percent

    def analyze(self, df):

        if df is None or len(df) < 30:
            return None

        highs = df["high"].values
        lows = df["low"].values

        bullish_fvg = None
        bearish_fvg = None

        bullish_found = False
        bearish_found = False

        # Search newest confirmed FVG first
        for i in range(len(df) - 3, 2, -1):

            # -----------------------------
            # Bullish FVG
            # Candle1 High < Candle3 Low
            # -----------------------------
            gap = lows[i] - highs[i - 2]

            if gap > 0:

                gap_percent = gap / highs[i - 2]

                if gap_percent >= self.min_gap_percent:

                    bullish_fvg = {
                        "top": float(lows[i]),
                        "bottom": float(highs[i - 2]),
                        "index": i
                    }

                    bullish_found = True
                    break

        # Search newest bearish FVG
        for i in range(len(df) - 3, 2, -1):

            # -----------------------------
            # Bearish FVG
            # Candle1 Low > Candle3 High
            # -----------------------------
            gap = lows[i - 2] - highs[i]

            if gap > 0:

                gap_percent = gap / lows[i - 2]

                if gap_percent >= self.min_gap_percent:

                    bearish_fvg = {
                        "top": float(lows[i - 2]),
                        "bottom": float(highs[i]),
                        "index": i
                    }

                    bearish_found = True
                    break

        active = "NONE"

        if bullish_found:
            active = "BULLISH"

        elif bearish_found:
            active = "BEARISH"

        confidence = 50

        if active != "NONE":
            confidence = 85

        return {

            "active": active,

            "bullish": bullish_fvg,

            "bearish": bearish_fvg,

            "bullish_found": bullish_found,

            "bearish_found": bearish_found,

            "confidence": confidence

        }


fair_value_gap = FairValueGap()
