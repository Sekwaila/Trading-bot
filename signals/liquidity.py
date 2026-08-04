"""
SEKWAILA OMEGA X V7
Liquidity Sweeps
"""


class Liquidity:

    def analyze(self, df, lookback=20):

        if df is None or len(df) < lookback + 5:
            return None

        recent = df.tail(lookback)

        previous_high = float(recent["high"][:-1].max())
        previous_low = float(recent["low"][:-1].min())

        last = recent.iloc[-1]

        high = float(last["high"])
        low = float(last["low"])
        close = float(last["close"])

        bullish_sweep = False
        bearish_sweep = False

        liquidity_high = previous_high
        liquidity_low = previous_low

        # ==================================
        # Bearish Liquidity Sweep
        # Price takes previous highs
        # then closes back below them
        # ==================================

        if high > previous_high and close < previous_high:

            bearish_sweep = True

        # ==================================
        # Bullish Liquidity Sweep
        # Price takes previous lows
        # then closes back above them
        # ==================================

        if low < previous_low and close > previous_low:

            bullish_sweep = True

        return {

            "bullish_sweep": bullish_sweep,

            "bearish_sweep": bearish_sweep,

            "liquidity_high": liquidity_high,

            "liquidity_low": liquidity_low,

            "current_price": close,
        }


liquidity = Liquidity()
