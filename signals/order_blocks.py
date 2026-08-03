"""
SEKWAILA OMEGA X V7
Smart Money Order Blocks
"""


class OrderBlocks:

    def analyze(self, df):

        if df is None or len(df) < 10:
            return None

        bullish = False
        bearish = False

        bullish_block = None
        bearish_block = None

        # Bullish Order Block
        # Last bearish candle before a bullish impulse

        for i in range(len(df) - 2, 2, -1):

            current = df.iloc[i]
            previous = df.iloc[i - 1]

            if (
                previous["close"] < previous["open"]
                and current["close"] > previous["high"]
            ):

                bullish = True

                bullish_block = {
                    "high": float(previous["high"]),
                    "low": float(previous["low"]),
                }

                break

        # Bearish Order Block
        # Last bullish candle before a bearish impulse

        for i in range(len(df) - 2, 2, -1):

            current = df.iloc[i]
            previous = df.iloc[i - 1]

            if (
                previous["close"] > previous["open"]
                and current["close"] < previous["low"]
            ):

                bearish = True

                bearish_block = {
                    "high": float(previous["high"]),
                    "low": float(previous["low"]),
                }

                break

        return {
            "bullish_ob": bullish,
            "bearish_ob": bearish,
            "bullish_zone": bullish_block,
            "bearish_zone": bearish_block,
        }


order_blocks = OrderBlocks()
