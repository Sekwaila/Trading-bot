"""
SEKWAILA OMEGA X
Institutional Order Block Engine
Version 2.0
"""


class OrderBlocks:

    def __init__(self, displacement_threshold=0.003):
        self.displacement_threshold = displacement_threshold

    def analyze(self, df, structure):

        if df is None:
            return None

        if structure is None:
            return None

        if len(df) < 60:
            return None

        bias = structure["bias"]

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values

        bullish_ob = None
        bearish_ob = None

        bullish_valid = False
        bearish_valid = False

        # ---------------------------------------------------
        # Search from newest closed candle backwards
        # ---------------------------------------------------

        for i in range(len(df) - 5, 10, -1):

            # ===========================
            # Bullish Order Block
            # ===========================

            if bias == "BUY":

                if closes[i] < opens[i]:

                    impulse = (
                        highs[i + 3] - highs[i]
                    ) / highs[i]

                    if impulse > self.displacement_threshold:

                        bullish_ob = {

                            "low": float(lows[i]),
                            "high": float(highs[i]),
                            "index": i

                        }

                        bullish_valid = True
                        break

            # ===========================
            # Bearish Order Block
            # ===========================

            if bias == "SELL":

                if closes[i] > opens[i]:

                    impulse = (
                        lows[i] - lows[i + 3]
                    ) / lows[i]

                    if impulse > self.displacement_threshold:

                        bearish_ob = {

                            "low": float(lows[i]),
                            "high": float(highs[i]),
                            "index": i

                        }

                        bearish_valid = True
                        break

        active = None

        if bullish_valid:
            active = "BULLISH"

        elif bearish_valid:
            active = "BEARISH"

        confidence = 50

        if active:
            confidence = 90

        return {

            "active": active,

            "bullish": bullish_ob,

            "bearish": bearish_ob,

            "bullish_valid": bullish_valid,

            "bearish_valid": bearish_valid,

            "confidence": confidence

        }


order_blocks = OrderBlocks()
