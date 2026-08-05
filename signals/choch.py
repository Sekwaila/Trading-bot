"""
SEKWAILA OMEGA X V7
Change of Character (CHoCH)
"""

from .market_structure import MarketStructure

class ChangeOfCharacter:

    def analyze(self, structure):
        """
        Analyze market structure for CHoCH.
        Returns bullish_choch (for downtrend reversal) and bearish_choch (for uptrend reversal).
        """
        if structure is None:
            return None

        price = structure.get("price")
        last_high = structure.get("last_high")
        last_low = structure.get("last_low")
        prev_high = structure.get("prev_high")
        prev_low = structure.get("prev_low")
        bullish_bos = structure.get("bullish_bos", False)
        bearish_bos = structure.get("bearish_bos", False)

        # Determine the prevailing trend using the last two swing points
        trend = None
        if last_high is not None and prev_high is not None and last_low is not None and prev_low is not None:
            if last_high > prev_high and last_low > prev_low:
                trend = "UP"
            elif last_high < prev_high and last_low < prev_low:
                trend = "DOWN"
        # If trend cannot be determined, return no signal

        bullish_choch = False
        bearish_choch = False

        if trend == "UP":
            # In an uptrend, a break below the last higher low signals a bearish CHoCH
            if bearish_bos:  # price < last_low
                bearish_choch = True
        elif trend == "DOWN":
            # In a downtrend, a break above the last lower high signals a bullish CHoCH
            if bullish_bos:  # price > last_high
                bullish_choch = True

        return {
            "bullish_choch": bullish_choch,
            "bearish_choch": bearish_choch,
            "trend": trend,
        }

    def detect(self, df):
        """Compatible with SignalEngine."""
        structure = MarketStructure().analyze(df)
        if structure is None:
            return None
        result = self.analyze(structure)
        if result is None:
            return None
        if result["bullish_choch"]:
            return "BUY"
        if result["bearish_choch"]:
            return "SELL"
        return None

choch = ChangeOfCharacter()
