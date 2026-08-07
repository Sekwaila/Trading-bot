"""
SEKWAILA OMEGA X
Institutional Breaker Block Engine
Version 3.0
"""


class BreakerBlocks:

    def analyze(self, df, order_blocks, liquidity):

        if df is None:
            return None

        if order_blocks is None:
            return None

        if liquidity is None:
            return None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        bullish_breaker = False
        bearish_breaker = False

        breaker_zone = None
        confidence = 0

        # -------------------------
        # Bullish Breaker
        # -------------------------

        if (
            order_blocks["active"] == "BEARISH"
            and liquidity["sell_side_sweep"]
        ):

            ob = order_blocks["bearish"]

            if ob:

                if closes[-2] > ob["high"]:

                    bullish_breaker = True

                    breaker_zone = {

                        "low": ob["low"],
                        "high": ob["high"]

                    }

                    confidence = 92

        # -------------------------
        # Bearish Breaker
        # -------------------------

        if (
            order_blocks["active"] == "BULLISH"
            and liquidity["buy_side_sweep"]
        ):

            ob = order_blocks["bullish"]

            if ob:

                if closes[-2] < ob["low"]:

                    bearish_breaker = True

                    breaker_zone = {

                        "low": ob["low"],
                        "high": ob["high"]

                    }

                    confidence = 92

        direction = "NONE"

        if bullish_breaker:
            direction = "BULLISH"

        elif bearish_breaker:
            direction = "BEARISH"

        return {

            "direction": direction,

            "bullish": bullish_breaker,

            "bearish": bearish_breaker,

            "zone": breaker_zone,

            "confidence": confidence

        }


breaker_blocks = BreakerBlocks()
