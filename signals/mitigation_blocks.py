"""
SEKWAILA OMEGA X
Institutional Mitigation Block Engine
Version 3.0
"""


class MitigationBlocks:

    def analyze(self, df, order_blocks):

        if df is None:
            return None

        if order_blocks is None:
            return None

        close = df["close"].iloc[-2]

        bullish = False
        bearish = False

        zone = None

        confidence = 0

        # -----------------------
        # Bullish Mitigation
        # -----------------------

        bull = order_blocks.get("bullish")

        if bull:

            if bull["low"] <= close <= bull["high"]:

                bullish = True

                zone = bull

                confidence = 90

        # -----------------------
        # Bearish Mitigation
        # -----------------------

        bear = order_blocks.get("bearish")

        if bear:

            if bear["low"] <= close <= bear["high"]:

                bearish = True

                zone = bear

                confidence = 90

        direction = "NONE"

        if bullish:
            direction = "BULLISH"

        elif bearish:
            direction = "BEARISH"

        return {

            "direction": direction,

            "bullish": bullish,

            "bearish": bearish,

            "zone": zone,

            "confidence": confidence

        }


mitigation_blocks = MitigationBlocks()
