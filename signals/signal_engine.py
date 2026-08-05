"""
signal_engine.py
SEKWAILA OMEGA X v6.2
SMC voting engine with fallback to EMA+RSI.
"""

import numpy as np
import pandas as pd

# Import your actual SMC modules (adjust class names as needed)
try:
    from .market_structure import MarketStructure
    from .fair_value_gap import FairValueGap    # or FVG if that's the class name
    from .order_blocks import OrderBlocks        # or OrderBlock
    from .liquidity import Liquidity
    from .choch import CHOCH
    SMC_AVAILABLE = True
except ImportError as e:
    SMC_AVAILABLE = False
    # Define dummy placeholders to avoid errors
    class Dummy:
        @staticmethod
        def detect(*args, **kwargs): return None
    MarketStructure = FairValueGap = OrderBlocks = Liquidity = CHOCH = Dummy


class SignalEngine:

    def __init__(self):
        self.smc_available = SMC_AVAILABLE

    def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):
        """
        Generate a BUY/SELL signal.
        Uses SMC modules if available, otherwise EMA/RSI.
        """
        if df is None or df.empty:
            return None
        if len(df) < 50:
            return None

        df = df.copy()
        required = ["open", "high", "low", "close"]
        for col in required:
            if col not in df.columns:
                return None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=required, inplace=True)
        if len(df) < 50:
            return None

        # ------------------ SMC Voting ------------------
        if self.smc_available:
            # Instantiate detectors (adjust method names as per your actual implementation)
            ms = MarketStructure()
            fvg = FairValueGap()
            ob = OrderBlocks()
            liq = Liquidity()
            choch = CHOCH()

            # Each detector should return a direction or None.
            # Adjust the method name if yours is different (e.g., `get_signal()`).
            try:
                ms_signal = ms.detect(df)
                fvg_signal = fvg.detect(df)
                ob_signal = ob.detect(df)
                liq_signal = liq.detect(df)
                choch_signal = choch.detect(df)
            except AttributeError:
                # If your modules use different method names, adapt here.
                st.warning("SMC modules detected but method 'detect' not found. Falling back to EMA/RSI.")
                return self._ema_rsi_signal_with_levels(df)

            votes = [ms_signal, fvg_signal, ob_signal, liq_signal, choch_signal]
            buy_votes = sum(1 for v in votes if v == "BUY")
            sell_votes = sum(1 for v in votes if v == "SELL")

            if buy_votes > sell_votes:
                direction = "BUY"
                confidence = 60 + buy_votes * 6  # max 60+30=90
            elif sell_votes > buy_votes:
                direction = "SELL"
                confidence = 60 + sell_votes * 6
            else:
                # No clear consensus, fallback to EMA/RSI
                return self._ema_rsi_signal_with_levels(df)

            # Build signal with computed confidence
            return self._build_signal(df, direction, confidence)

        # ------------------ Fallback to EMA/RSI ------------------
        return self._ema_rsi_signal_with_levels(df)

    def _ema_rsi_signal(self, df):
        """Return BUY/SELL/None based on EMA crossover and RSI."""
        df = df.copy()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["rsi"] = self._rsi(df["close"], 14)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        prev_ema20 = float(prev["ema20"])
        prev_ema50 = float(prev["ema50"])
        rsi = float(last["rsi"])

        if ema20 > ema50 and prev_ema20 <= prev_ema50:
            return "BUY"
        elif ema20 < ema50 and prev_ema20 >= prev_ema50:
            return "SELL"
        elif rsi < 30:
            return "BUY"
        elif rsi > 70:
            return "SELL"
        else:
            return None

    def _ema_rsi_signal_with_levels(self, df):
        """Original EMA/RSI logic with full signal object."""
        direction = self._ema_rsi_signal(df)
        if direction is None:
            return None

        # Recalculate indicators for levels
        df = df.copy()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["rsi"] = self._rsi(df["close"], 14)
        df["atr"] = self._atr(df, 14)

        last = df.iloc[-1]
        price = float(last["close"])
        atr = float(last["atr"])
        rsi = float(last["rsi"])
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])

        if np.isnan(atr) or atr == 0:
            return None

        confidence = 60 + (abs(rsi - 50) / 50) * 20
        if abs(ema20 - ema50) / ema50 > 0.001:
            confidence += 10
        confidence = min(95, round(confidence, 2))

        return self._build_signal(df, direction, confidence)

    def _build_signal(self, df, direction, confidence):
        """Construct the signal dictionary."""
        last = df.iloc[-1]
        price = float(last["close"])
        atr = float(last.get("atr", 0))
        rsi = float(last.get("rsi", 50))
        ema20 = float(last.get("ema20", price))
        ema50 = float(last.get("ema50", price))

        if direction == "BUY":
            sl = price - atr * 1.5
            tp1 = price + atr * 1.5
            tp2 = price + atr * 2.5
            tp3 = price + atr * 4.0
            entry = price - atr * 0.01
        else:
            sl = price + atr * 1.5
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4.0
            entry = price + atr * 0.01

        if confidence >= 85:
            grade = "A"
        elif confidence >= 70:
            grade = "B"
        elif confidence >= 60:
            grade = "C"
        else:
            grade = "D"

        return {
            "signal": direction,
            "confidence": confidence,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "grade": grade,
            "lot": 0.01,
            "risk": round(abs(entry - sl) * 10000, 2),
            "diagnostics": {
                "rsi": round(rsi, 2),
                "atr": round(atr, 5),
                "ema20": round(ema20, 5),
                "ema50": round(ema50, 5)
            },
            "reasons": [
                f"Direction: {direction}",
                f"RSI: {rsi:.1f}"
            ]
        }

    @staticmethod
    def _rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def _atr(df, period=14):
        high = df["high"]
        low = df["low"]
        close = df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean()


# Instantiate the engine
engine = SignalEngine()
