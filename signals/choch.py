"""
SEKWAILA OMEGA X
Institutional Change of Character (CHoCH)
Version 2.0
"""

class CHoCH:

    def analyze(self, df, structure):

        if df is None:
            return None

        if structure is None:
            return None

        trend = structure["trend"]
        bias = structure["bias"]
        structure_type = structure["structure"]

        bullish_choch = False
        bearish_choch = False

        confidence = 0

        if trend == "BEARISH":

            if structure_type == "BULLISH_CHOCH":

                bullish_choch = True
                confidence = 90

        elif trend == "BULLISH":

            if structure_type == "BEARISH_CHOCH":

                bearish_choch = True
                confidence = 90

        choch = "NONE"

        if bullish_choch:
            choch = "BULLISH"

        elif bearish_choch:
            choch = "BEARISH"

        return {

            "choch": choch,

            "bullish_choch": bullish_choch,

            "bearish_choch": bearish_choch,

            "bias": bias,

            "confidence": confidence

        }


choch = CHoCH()
