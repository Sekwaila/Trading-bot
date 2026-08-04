"""
SEKWAILA OMEGA X
Inducement
"""


class Inducement:

    def analyze(self, df):

        if df is None or len(df) < 20:
            return None

        bullish_inducement = False
        bearish_inducement = False

        bullish_level = None
        bearish_level = None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        # Scan from newest candle backwards
        for i in range(len(df) - 3, 10, -1):

            # ==========================
            # Bullish Inducement
            # ==========================

            swing_low = min(lows[i - 5:i])

            if (
                lows[i] < swing_low
                and closes[i + 1] > lows[i]
            ):

                bullish_inducement = True
                bullish_level = float(lows[i])
                break

            # ==========================
            # Bearish Inducement
            # ==========================

            swing_high = max(highs[i - 5:i])

            if (
                highs[i] > swing_high
                and closes[i + 1] < highs[i]
            ):

                bearish_inducement = True
                bearish_level = float(highs[i])
                break

        return {

            "bullish_inducement": bullish_inducement,
            "bearish_inducement": bearish_inducement,

            "bullish_level": bullish_level,
            "bearish_level": bearish_level,

        }


inducement = Inducement()
