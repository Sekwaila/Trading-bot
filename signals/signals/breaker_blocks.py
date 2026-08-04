"""
SEKWAILA OMEGA X
Breaker Blocks
"""


class BreakerBlocks:

    def analyze(self, df):

        if df is None or len(df) < 30:
            return None

        bullish_breaker = False
        bearish_breaker = False

        bullish_level = None
        bearish_level = None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        # Scan from newest closed candles backwards
        for i in range(len(df) - 4, 6, -1):

            # ==========================
            # Bullish Breaker
            # ==========================

            swing_low = (
                lows[i] < lows[i - 1]
                and lows[i] < lows[i - 2]
                and lows[i] < lows[i + 1]
            )

            liquidity_sweep = lows[i] < min(lows[i - 5:i])

            recovery = (
                closes[i + 1] > highs[i]
                and closes[i + 2] > highs[i]
            )

            if swing_low and liquidity_sweep and recovery:

                bullish_breaker = True
                bullish_level = float(highs[i])
                break

            # ==========================
            # Bearish Breaker
            # ==========================

            swing_high = (
                highs[i] > highs[i - 1]
                and highs[i] > highs[i - 2]
                and highs[i] > highs[i + 1]
            )

            liquidity_sweep = highs[i] > max(highs[i - 5:i])

            rejection = (
                closes[i + 1] < lows[i]
                and closes[i + 2] < lows[i]
            )

            if swing_high and liquidity_sweep and rejection:

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
