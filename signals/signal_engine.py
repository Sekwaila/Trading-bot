"""
SEKWAILA OMEGA X V7 – Signal Engine (Smart Money Concepts)
Combines CHoCH, BOS, Order Blocks, FVG, and Liquidity Sweeps into a single consensus signal.
Now with trend context, agreement scoring, and a confidence floor.
"""

import pandas as pd
import numpy as np
from .market_structure import market_structure
from .choch import choch
from .order_blocks import order_blocks
from .fair_value_gap import fair_value_gap
from .liquidity import liquidity

class SignalEngine:
    """
    Synthesises signals from multiple SMC modules.
    Returns a dict: {signal, confidence, entry, sl, tp1, tp2, tp3, grade, diagnostics}
    """

    # Module weights (relative importance)
    MODULE_WEIGHTS = {
        "market_structure": 3,   # trend bias
        "choch": 3,              # reversal confirmation
        "order_blocks": 2,       # supply/demand zones
        "fvg": 1,                # fair value gaps
        "liquidity": 2,          # liquidity sweeps
    }

    # Minimum confidence to emit a signal (0-100)
    MIN_CONFIDENCE = 50

    # Grade thresholds
    GRADE_A = 80
    GRADE_B = 65

    def __init__(self):
        self.modules = {
            "market_structure": market_structure,
            "choch": choch,
            "order_blocks": order_blocks,
            "fvg": fair_value_gap,
            "liquidity": liquidity,
        }

    def generate_signal(self, df, symbol=None):
        """
        Main entry point.
        :param df: DataFrame with OHLC data (must have 'open','high','low','close')
        :param symbol: optional symbol name (for logging)
        :return: dict or None
        """
        if df is None or df.empty or len(df) < 10:
            return None

        # 1. Run all modules
        module_results = {}
        for name, mod in self.modules.items():
            try:
                result = mod.detect(df)
                # result should be 'BUY', 'SELL', or None
                module_results[name] = result
            except Exception as e:
                # if a module fails, log and continue
                print(f"Module {name} failed: {e}")
                module_results[name] = None

        # 2. Compute weighted scores
        buy_score = 0
        sell_score = 0
        active_modules = 0
        for name, direction in module_results.items():
            weight = self.MODULE_WEIGHTS.get(name, 1)
            if direction == "BUY":
                buy_score += weight
                active_modules += 1
            elif direction == "SELL":
                sell_score += weight
                active_modules += 1

        # 3. Determine preliminary direction and confidence
        if buy_score == 0 and sell_score == 0:
            return None  # no consensus

        # If both sides have scores, choose the higher one
        total_score = buy_score + sell_score
        if buy_score > sell_score:
            direction = "BUY"
            confidence = int(round((buy_score / total_score) * 100))
        elif sell_score > buy_score:
            direction = "SELL"
            confidence = int(round((sell_score / total_score) * 100))
        else:
            # tie – try to break by checking market structure trend
            # If market structure favours one side, use that
            ms_dir = module_results.get("market_structure")
            if ms_dir:
                direction = ms_dir
                confidence = 50
            else:
                return None  # can't decide

        # 4. (Optional) Trend filter: Avoid trading against a strong trend
        # If market structure is clearly trending, we can require CHoCH or liquidity to confirm.
        # We'll implement a soft filter: if the direction is opposite to the market structure
        # and no CHoCH is present, reduce confidence or reject.
        ms = module_results.get("market_structure")
        ch = module_results.get("choch")
        if ms and ch:
            # If MS says BUY but engine says SELL and CHoCH is not SELL -> reduce confidence
            if ms == "BUY" and direction == "SELL" and ch != "SELL":
                confidence = max(0, confidence - 20)
            elif ms == "SELL" and direction == "BUY" and ch != "BUY":
                confidence = max(0, confidence - 20)

        # 5. Minimum confidence threshold
        if confidence < self.MIN_CONFIDENCE:
            return None

        # 6. Calculate grade
        if confidence >= self.GRADE_A:
            grade = "A"
        elif confidence >= self.GRADE_B:
            grade = "B"
        else:
            grade = "C"

        # 7. Calculate entry, stop-loss, and take-profit levels
        # This is a simplified version – you can replace with your own logic
        last_price = float(df.iloc[-1]["close"])
        atr = self._calculate_atr(df, period=14)
        if atr is None:
            atr = last_price * 0.01  # fallback 1%

        if direction == "BUY":
            entry = last_price
            stop_loss = entry - atr * 1.5
            tp1 = entry + atr * 1.5
            tp2 = entry + atr * 2.5
            tp3 = entry + atr * 4.0
        else:  # SELL
            entry = last_price
            stop_loss = entry + atr * 1.5
            tp1 = entry - atr * 1.5
            tp2 = entry - atr * 2.5
            tp3 = entry - atr * 4.0

        # 8. Diagnostics (for display)
        rsi = self._calculate_rsi(df, period=14)
        diag = {
            "rsi": rsi,
            "atr": atr,
            "module_votes": module_results,
            "buy_score": buy_score,
            "sell_score": sell_score,
        }

        return {
            "signal": direction,
            "confidence": confidence,
            "entry": entry,
            "sl": stop_loss,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "grade": grade,
            "diagnostics": diag,
        }

    # ------------------ Helper methods ------------------
    def _calculate_atr(self, df, period=14):
        """Average True Range (ATR)"""
        if len(df) < period + 1:
            return None
        high = df["high"]
        low = df["low"]
        close = df["close"]
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        return float(atr)

    def _calculate_rsi(self, df, period=14):
        """Relative Strength Index"""
        if len(df) < period + 1:
            return None
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        return float(rsi)

# Singleton instance
engine = SignalEngine()
