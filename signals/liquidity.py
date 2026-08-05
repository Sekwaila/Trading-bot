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

        # Bearish Liquidity Sweep: price takes previous high, closes below it
        if high > previous_high and close < previous_high:
            bearish_sweep = True

        # Bullish Liquidity Sweep: price takes previous low, closes above it
        if low < previous_low and close > previous_low:
            bullish_sweep = True

        return {
            "bullish_sweep": bullish_sweep,
            "bearish_sweep": bearish_sweep,
            "liquidity_high": liquidity_high,
            "liquidity_low": liquidity_low,
            "current_price": close,
        }

    def detect(self, df):
        result = self.analyze(df)
        if result is None:
            return None
        if result["bullish_sweep"]:
            return "BUY"
        if result["bearish_sweep"]:
            return "SELL"
        return None

liquidity = Liquidity()
