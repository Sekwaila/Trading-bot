"""
SEKWAILA OMEGA X V7
Change of Character (CHoCH)
"""


class ChangeOfCharacter:

    def analyze(self, structure):

        if structure is None:
            return None

        bullish = False
        bearish = False

        # Bullish BOS means price has broken above
        # the last swing high.

        if structure["bullish_bos"]:
            bullish = True

        # Bearish BOS means price has broken below
        # the last swing low.

        if structure["bearish_bos"]:
            bearish = True

        return {
            "bullish_choch": bullish,
            "bearish_choch": bearish,
        }


choch = ChangeOfCharacter()
