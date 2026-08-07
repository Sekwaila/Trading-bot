"""
SEKWAILA OMEGA X
Institutional Inducement Engine
Version 3.0
"""


class Inducement:

    def analyze(self, df):

        if df is None or len(df) < 20:
            return None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        inducement = False
        direction = "NONE"
        level = None
        confidence = 0

        # Scan from newest closed candles backwards
        for i in range(len(df) - 4, 8, -1):

            # Bullish inducement
            if (
                lows[i] < lows[i - 1]
                and lows[i] > lows[i - 2]
                and closes[i + 1] > highs[i]
            ):

                inducement = True
                direction = "BULLISH"
                level = float(lows[i])
                confidence = 88
                break

            # Bearish inducement
            if (
                highs[i] > highs[i - 1]
                and highs[i] < highs[i - 2]
                and closes[i + 1] < lows[i]
            ):

                inducement = True
                direction = "BEARISH"
                level = float(highs[i])
                confidence = 88
                break

        return {

            "inducement": inducement,

            "direction": direction,

            "level": level,

            "confidence": confidence

        }


inducement = Inducement()
