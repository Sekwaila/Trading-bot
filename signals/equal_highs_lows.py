"""
SEKWAILA OMEGA X
Institutional Equal Highs / Equal Lows Engine
Version 3.0
"""


class EqualHighsLows:

    def __init__(self, tolerance=0.0005):
        self.tolerance = tolerance

    def analyze(self, df):

        if df is None or len(df) < 30:
            return None

        highs = df["high"].values
        lows = df["low"].values

        equal_highs = False
        equal_lows = False

        high_level = None
        low_level = None

        confidence = 0

        # -------------------------
        # Equal Highs
        # -------------------------

        for i in range(len(df) - 10, 5, -1):

            if abs(highs[i] - highs[i - 1]) / highs[i] <= self.tolerance:

                equal_highs = True
                high_level = float((highs[i] + highs[i - 1]) / 2)
                confidence = 90
                break

        # -------------------------
        # Equal Lows
        # -------------------------

        for i in range(len(df) - 10, 5, -1):

            if abs(lows[i] - lows[i - 1]) / lows[i] <= self.tolerance:

                equal_lows = True
                low_level = float((lows[i] + lows[i - 1]) / 2)
                confidence = max(confidence, 90)
                break

        return {

            "equal_highs": equal_highs,

            "equal_lows": equal_lows,

            "high_level": high_level,

            "low_level": low_level,

            "confidence": confidence

        }


equal_highs_lows = EqualHighsLows()
