"""
signal_engine.py
SEKWAILA OMEGA X v6.3
SMC voting engine with trend-based EMA fallback.
"""

import numpy as np
import pandas as pd
import streamlit as st  # for optional UI warnings

# ---------- SMC imports (each individually, with correct class names) ----------
SMC_MODULES = {}

try:
    from .market_structure import MarketStructure
    SMC_MODULES['market_structure'] = MarketStructure
except ImportError:
    pass

try:
    from .fair_value_gap import FairValueGap   # <-- corrected class name
    SMC_MODULES['fvg'] = FairValueGap
except ImportError:
    pass

try:
    from .order_blocks import OrderBlocks
    SMC_MODULES['order_blocks'] = OrderBlocks
except ImportError:
    pass

try:
    from .liquidity import Liquidity
    SMC_MODULES['liquidity'] = Liquidity
except ImportError:
    pass

try:
    from .choch import CHOCH
    SMC_MODULES['choch'] = CHOCH
except ImportError:
    pass

SMC_AVAILABLE = bool(SMC_MODULES)


class SignalEngine:

    def __init__(self):
        self.smc_available = SMC_AVAILABLE
        print(f"✅ SMC modules loaded: {list(SMC_MODULES.keys())}")
        if not SMC_AVAILABLE:
            print("ℹ️  No SMC modules – falling back to EMA+RSI only.")

    def _add_indicators(self, df):
        """Add EMA20, EMA50, RSI, ATR to DataFrame."""
        df = df.copy()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["rsi"] = self._rsi(df["close"], 14)
        df["atr"] = self._atr(df, 14)
        return df

    def _detect_from_module(self, detector, df):
        """
        Unified wrapper to call detect() or analyze() and extract a signal.
        Returns "BUY", "SELL", or None.
        """
        # Try detect() first
        if hasattr(detector, "detect"):
            result = detector.detect(df)
        elif hasattr(detector, "analyze"):
            result = detector.analyze(df)
        else:
            print(f"⚠️  No detect() or analyze() method found in {detector.__class__.__name__}")
            return None

        # If result is a dict, extract signal
        if isinstance(result, dict):
            return result.get("signal")
        # If result is a string, return it if valid
        if isinstance(result, str) and result in ["BUY", "SELL"]:
            return result
        # Otherwise, try to interpret common attributes
        if hasattr(result, "signal"):
            return result.signal
        return None

    def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):
        """
        Generate a BUY/SELL signal using SMC voting or EMA fallback.
        """
        if df is None or df.empty:
            print("❌ No data")
            return None
        if len(df) < 50:
            print(f"⚠️  Only {len(df)} candles – need at least 50")
            return None

        df = df.copy()
        required = ["open", "high", "low", "close"]
        for col in required:
            if col not in df.columns:
                print(f"❌ Missing column: {col}")
                return None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=required, inplace=True)
        if len(df) < 50:
            print(f"⚠️  After dropping NaN, only {len(df)} candles")
            return None

        # Debug: print last few candles
        print(f"\n🔍 Last 3 candles for {symbol}:")
        print(df.tail(3)[["open", "high", "low", "close"]].round(2))

        # ------------------ SMC Voting ------------------
        if self.smc_available:
            votes = []
            for name, cls in SMC_MODULES.items():
                try:
                    detector = cls()
                    signal = self._detect_from_module(detector, df)
                    if signal in ["BUY", "SELL"]:
                        votes.append(signal)
                        print(f"   {name} -> {signal}")
                    else:
                        print(f"   {name} -> no signal")
                except Exception as e:
                    print(f"   {name} threw error: {e}")
                    continue

            print(f"📊 Votes: BUY={votes.count('BUY')}, SELL={votes.count('SELL')}")

            buy_votes = votes.count("BUY")
            sell_votes = votes.count("SELL")

            if buy_votes > sell_votes:
                direction = "BUY"
                confidence = 60 + buy_votes * 5
                print(f"✅ SMC consensus: BUY (confidence {confidence})")
                df = self._add_indicators(df)
                return self._build_signal(df, direction, confidence)

            if sell_votes > buy_votes:
                direction = "SELL"
                confidence = 60 + sell_votes * 5
                print(f"✅ SMC consensus: SELL (confidence {confidence})")
                df = self._add_indicators(df)
                return self._build_signal(df, direction, confidence)

            print("➡️  No SMC consensus – falling back to EMA/RSI")

        # ------------------ Trend-based EMA + RSI ------------------
        print("➡️  Using EMA/RSI fallback")
        return self._ema_rsi_signal_with_levels(df)

    def _ema_rsi_signal_with_levels(self, df):
        """Returns full signal based on trend (not just crossover)."""
        df = self._add_indicators(df)
        last = df.iloc[-1]
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        rsi = float(last["rsi"])

        # ---------- TREND-BASED (not crossover) ----------
        if ema20 > ema50:
            direction = "BUY"
        elif ema20 < ema50:
            direction = "SELL"
        else:
            # If equal, use RSI
            if rsi < 30:
                direction = "BUY"
            elif rsi > 70:
                direction = "SELL"
            else:
                print("➡️  EMA/RSI: no clear direction")
                return None

        # Boost confidence if RSI confirms trend
        confidence = 60
        if direction == "BUY" and rsi > 50:
            confidence += 10
        elif direction == "SELL" and rsi < 50:
            confidence += 10
        # Additional confidence if trend is strong
        if abs(ema20 - ema50) / ema50 > 0.001:
            confidence += 10
        confidence = min(95, round(confidence, 2))

        print(f"✅ EMA/RSI signal: {direction} (conf {confidence})")
        return self._build_signal(df, direction, confidence)

    def _build_signal(self, df, direction, confidence):
        """Construct the signal dictionary. Assumes indicators exist."""
        last = df.iloc[-1]
        price = float(last["close"])
        atr = float(last["atr"])
        rsi = float(last["rsi"])
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])

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


# ---------- Instantiate the engine ----------
engine = SignalEngine()
