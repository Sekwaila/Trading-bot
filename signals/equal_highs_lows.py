"""
SEKWAILA OMEGA X V7
Equal Highs / Equal Lows (EQH / EQL)
"""


class EqualHighsLows:

    def analyze(self, df):

        if df is None or len(df) < 10:
            return None

        equal_high = False
        equal_low = False

        high_price = None
        low_price = None

        tolerance = 0.0002

        # Scan recent candles

        for i in range(len(df) - 10, len(df) - 1):

            high1 = float(df.iloc[i]["high"])
            high2 = float(df.iloc[i + 1]["high"])

            low1 = float(df.iloc[i]["low"])
            low2 = float(df.iloc[i + 1]["low"])

            # ==========================
            # Equal Highs
            # ==========================

            if abs(high1 - high2) <= tolerance:

                equal_high = True
                high_price = max(high1, high2)

            # ==========================
            # Equal Lows
            # ==========================

            if abs(low1 - low2) <= tolerance:

                equal_low = True
                low_price = min(low1, low2)

        return {

            "equal_high": equal_high,
            "equal_low": equal_low,

            "equal_high_price": high_price,
            "equal_low_price": low_price,

        }


equal_highs_lows = EqualHighsLows()
