"""
SEKWAILA OMEGA X
Displacement
"""

import numpy as np


class Displacement:

    def analyze(self, df):

        if df is None or len(df) < 30:
            return None

        bullish_displacement = False
        bearish_displacement = False

        bullish_level = None
        bearish_level = None

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values

        # Average candle body
        bodies = np.abs(closes - opens)
        avg_body = np.mean(bodies[-20:])

        # Scan from newest candle backwards
        for i in range(len(df) - 2, 20, -1):

            body = abs(closes[i] - opens[i])

            # ==========================
            # Bullish Displacement
            # ==========================

            if (
                closes[i] > opens[i]
                and body > avg_body * 2
                and closes[i] > highs[i - 1]
            ):

                bullish_displacement = True
                bullish_level = float(closes[i])
                break

            # ==========================
            # Bearish Displacement
            # ==========================

            if (
                closes[i] < opens[i]
                and body > avg_body * 2
                and closes[i] < lows[i - 1]
            ):

                bearish_displacement = True
                bearish_level = float(closes[i])
                break

        return {

            "bullish_displacement": bullish_displacement,
            "bearish_displacement": bearish_displacement,

            "bullish_level": bullish_level,
            "bearish_level": bearish_level,

        }


displacement = Displacement()
