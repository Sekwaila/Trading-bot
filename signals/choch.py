"""
SEKWAILA OMEGA X V7
Change of Character (CHoCH)
"""

from .market_structure import MarketStructure

class ChangeOfCharacter:

    def analyze(self, structure):
        """
        Analyze a market structure dictionary.
        Returns a dict with bullish_choch and bearish_choch flags.
        """
        if structure is None:
            return None

        bullish = False
        bearish = False

        # Bullish BOS means price has broken above the last swing high
        if structure.get("bullish_bos"):
            bullish = True

        # Bearish BOS means price has broken below the last swing low
        if structure.get("bearish_bos"):
            bearish = True

        return {
            "bullish_choch": bullish,
            "bearish_choch": bearish,
        }

    # ----- NEW detect() method -----
    def detect(self, df):
        """
        Compatible with SignalEngine.
        First builds market structure, then analyzes it for CHOCH.
        """
        # Get market structure from the DataFrame
        structure = MarketStructure().analyze(df)
        if structure is None:
            return None

        # Analyze the structure for CHOCH
        result = self.analyze(structure)
        if result is None:
            return None

        if result["bullish_choch"]:
            return "BUY"
        if result["bearish_choch"]:
            return "SELL"
        return None


choch = ChangeOfCharacter()
