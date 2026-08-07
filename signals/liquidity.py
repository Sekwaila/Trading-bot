"""
SEKWAILA OMEGA X
Institutional Liquidity Engine
Version 1.0
"""

class Liquidity:

    def __init__(self, sweep_window=10):
        self.sweep_window = sweep_window

    def analyze(self, df):

        if df is None or len(df) < 50:
            return None

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        current_high = highs[-2]
        current_low = lows[-2]
        current_close = closes[-2]

        previous_highs = highs[-self.sweep_window-2:-2]
        previous_lows = lows[-self.sweep_window-2:-2]

        buy_side_sweep = False
        sell_side_sweep = False

        swept_level = None
        sweep_strength = 0.0

        # -----------------------------
        # Buy-side Liquidity Sweep
        # -----------------------------
        highest = max(previous_highs)

        if current_high > highest and current_close < highest:

            buy_side_sweep = True
            swept_level = float(highest)

            sweep_strength = (
                current_high - highest
            ) / highest * 100

        # -----------------------------
        # Sell-side Liquidity Sweep
        # -----------------------------
        lowest = min(previous_lows)

        if current_low < lowest and current_close > lowest:

            sell_side_sweep = True
            swept_level = float(lowest)

            sweep_strength = (
                lowest - current_low
            ) / lowest * 100

        liquidity = "NONE"

        if buy_side_sweep:
            liquidity = "BUY_SIDE"

        elif sell_side_sweep:
            liquidity = "SELL_SIDE"

        confidence = min(
            100,
            60 + sweep_strength * 800
        )

        return {

            "liquidity": liquidity,

            "buy_side_sweep": buy_side_sweep,

            "sell_side_sweep": sell_side_sweep,

            "level": swept_level,

            "strength": round(sweep_strength, 4),

            "confidence": round(confidence)

        }


liquidity = Liquidity()
