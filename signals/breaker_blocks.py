"""
SEKWAILA OMEGA X
Breaker Blocks
"""


class BreakerBlocks:

    def analyze(self, df):

        if df is None or len(df) < 20:
            return None

        bullish_breaker = False
        bearish_breaker = False

        bullish_level = None
        bearish_level = None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        # Scan from newest candle backwards
        for i in range(len(df) - 3, 10, -1):

            # -------------------------
            # Bullish Breaker
            # -------------------------

            previous_low = min(lows[i-5:i])

            if (
                lows[i] < previous_low
                and closes[i+1] > highs[i]
            ):

                bullish_breaker = True
                bullish_level = float(highs[i])
                break

            # -------------------------
            # Bearish Breaker
            # -------------------------

            previous_high = max(highs[i-5:i])

            if (
                highs[i] > previous_high
                and closes[i+1] < lows[i]
            ):

                bearish_breaker = True
                bearish_level = float(lows[i])
                break

        return {

            "bullish_breaker": bullish_breaker,
            "bearish_breaker": bearish_breaker,

            "bullish_level": bullish_level,
            "bearish_level": bearish_level,

        }


breaker_blocks = BreakerBlocks()
