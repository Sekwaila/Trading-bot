"""
SEKWAILA OMEGA X
Multi Timeframe
"""


class MultiTimeframe:

    def analyze(self, current_df, h1_df=None, h4_df=None):

        if current_df is None or len(current_df) < 200:
            return None

        def trend(df):

            if df is None or len(df) < 200:
                return "UNKNOWN"

            ema50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-2]
            ema200 = df["close"].ewm(span=200, adjust=False).mean().iloc[-2]

            if ema50 > ema200:
                return "BULLISH"

            if ema50 < ema200:
                return "BEARISH"

            return "RANGING"

        current = trend(current_df)
        h1 = trend(h1_df)
        h4 = trend(h4_df)

        bullish_alignment = (
            current == "BULLISH"
            and h1 == "BULLISH"
            and h4 == "BULLISH"
        )

        bearish_alignment = (
            current == "BEARISH"
            and h1 == "BEARISH"
            and h4 == "BEARISH"
        )

        return {

            "current_trend": current,
            "h1_trend": h1,
            "h4_trend": h4,

            "bullish_alignment": bullish_alignment,
            "bearish_alignment": bearish_alignment,

        }


multi_timeframe = MultiTimeframe()
