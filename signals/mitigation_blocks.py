"""
SEKWAILA OMEGA X
Mitigation Blocks
"""


class MitigationBlocks:

    def analyze(self, df):

        if df is None or len(df) < 30:
            return None

        bullish_mitigation = False
        bearish_mitigation = False

        bullish_level = None
        bearish_level = None

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values

        # Scan from newest candle backwards
        for i in range(len(df) - 5, 10, -1):

            previous_high = max(highs[i - 5:i])
            previous_low = min(lows[i - 5:i])

            # ==========================
            # Bullish Mitigation Block
            # ==========================

            if (
                closes[i] > previous_high
                and lows[i + 1] <= highs[i]
                and closes[i + 1] > opens[i + 1]
            ):

                bullish_mitigation = True
                bullish_level = float(highs[i])
                break

            # ==========================
            # Bearish Mitigation Block
            # ==========================

            if (
                closes[i] < previous_low
                and highs[i + 1] >= lows[i]
                and closes[i + 1] < opens[i + 1]
            ):

                bearish_mitigation = True
                bearish_level = float(lows[i])
                break

        return {

            "bullish_mitigation": bullish_mitigation,
            "bearish_mitigation": bearish_mitigation,

            "bullish_level": bullish_level,
            "bearish_level": bearish_level,

        }


mitigation_blocks = MitigationBlocks()
