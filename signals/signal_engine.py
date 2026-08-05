"""
signal_engine.py
SEKWAILA OMEGA X v6.5
SMC voting engine with weighted voting, CHoCH adaptation, and logging.
"""

import numpy as np
import pandas as pd
import logging
import streamlit as st

# Configure logging for the engine
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------- SMC imports (correct class names) ----------
SMC_MODULES = {}

try:
    from .market_structure import MarketStructure
    SMC_MODULES['market_structure'] = MarketStructure
except ImportError:
    pass

try:
    from .fair_value_gap import FairValueGap
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
    from .choch import ChangeOfCharacter   # correct class name
    SMC_MODULES['choch'] = ChangeOfCharacter
except ImportError:
    pass

SMC_AVAILABLE = bool(SMC_MODULES)

# ---------- Weighted voting weights (higher = more influential) ----------
WEIGHTS = {
    "market_structure": 3,
    "choch": 3,
    "order_blocks": 2,
    "liquidity": 2,
    "fvg": 1,
}


class SignalEngine:

    def __init__(self):
        self.smc_available = SMC_AVAILABLE
        logger.info(f"SMC modules loaded: {list(SMC_MODULES.keys())}")
        if not SMC_AVAILABLE:
            logger.info("No SMC modules – falling back to EMA+RSI only.")

    def _add_indicators(self, df):
        df = df.copy()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["rsi"] = self._rsi(df["close"], 14)
        df["atr"] = self._atr(df, 14)
        return df

    def _interpret_result(self, result):
        """
        Convert any dict with SMC flags into "BUY", "SELL", or None.
        Also returns confidence if provided.
        """
        if result is None:
            return None, None

        # If it's a string
        if isinstance(result, str):
            return (result if result in ["BUY", "SELL"] else None), None

        # If it's a dict
        if isinstance(result, dict):
            # Check for explicit signal field
            if "signal" in result:
                signal = result["signal"]
                if signal in ["BUY", "SELL"]:
                    confidence = result.get("confidence")
                    return signal, confidence

            # Look for bullish/bearish flags
            bullish_keys = ["bullish", "bullish_bos", "bullish_fvg", "bullish_ob", "bullish_sweep", "bullish_choch"]
            bearish_keys = ["bearish", "bearish_bos", "bearish_fvg", "bearish_ob", "bearish_sweep", "bearish_choch"]

            for key in bullish_keys:
                if result.get(key) is True:
                    return "BUY", None
            for key in bearish_keys:
                if result.get(key) is True:
                    return "SELL", None

        # If it's a custom object with .signal
        if hasattr(result, "signal"):
            signal = result.signal
            if signal in ["BUY", "SELL"]:
                confidence = getattr(result, "confidence", None)
                return signal, confidence

        return None, None

    def _detect_from_module(self, detector, df):
        """
        Call detect() or analyze() and convert result to a vote.
        Special handling for ChangeOfCharacter: it needs market structure.
        """
        # Special case: if detector is ChangeOfCharacter, we must pass structure
        if isinstance(detector, ChangeOfCharacter):
            # Build market structure first
            ms = MarketStructure()
            structure = ms.analyze(df)
            if structure is None:
                return None, None
            # Now call CHOCH's analyze with the structure
            result = detector.analyze(structure)
            return self._interpret_result(result)

        # Default: call detect() or analyze() with df
        if hasattr(detector, "detect"):
            result = detector.detect(df)
        elif hasattr(detector, "analyze"):
            result = detector.analyze(df)
        else:
            logger.warning(f"No detect() or analyze() in {detector.__class__.__name__}")
            return None, None

        return self._interpret_result(result)

    def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):
        if df is None or df.empty:
            logger.warning("No data")
            return None
        if len(df) < 50:
            logger.warning(f"Only {len(df)} candles")
            return None

        df = df.copy()
        required = ["open", "high", "low", "close"]
        for col in required:
            if col not in df.columns:
                logger.error(f"Missing column: {col}")
                return None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=required, inplace=True)
        if len(df) < 50:
            logger.warning(f"After dropping NaN, only {len(df)} candles")
            return None

        # ------------------ SMC Voting (weighted) ------------------
        if self.smc_available:
            buy_score = 0
            sell_score = 0
            total_weight = 0

            for name, cls in SMC_MODULES.items():
                try:
                    detector = cls()
                    signal, confidence = self._detect_from_module(detector, df)
                    weight = WEIGHTS.get(name, 1)
                    total_weight += weight

                    if signal == "BUY":
                        buy_score += weight
                        logger.info(f"   {name} -> BUY (weight {weight})")
                    elif signal == "SELL":
                        sell_score += weight
                        logger.info(f"   {name} -> SELL (weight {weight})")
                    else:
                        logger.info(f"   {name} -> no signal")
                except Exception as e:
                    logger.exception(f"{name} threw error: {e}")
                    continue

            if total_weight > 0:
                logger.info(f"📊 Weighted scores: BUY={buy_score}, SELL={sell_score}")

                if buy_score > sell_score:
                    direction = "BUY"
                    # Confidence based on score difference
                    confidence = min(95, 60 + int((buy_score / total_weight) * 35))
                    logger.info(f"✅ SMC consensus: BUY (conf {confidence})")
                    df = self._add_indicators(df)
                    return self._build_signal(df, direction, confidence)

                if sell_score > buy_score:
                    direction = "SELL"
                    confidence = min(95, 60 + int((sell_score / total_weight) * 35))
                    logger.info(f"✅ SMC consensus: SELL (conf {confidence})")
                    df = self._add_indicators(df)
                    return self._build_signal(df, direction, confidence)

            logger.info("➡️  No SMC consensus – falling back to EMA/RSI")

        # ------------------ Trend-based EMA + RSI ------------------
        return self._ema_rsi_signal_with_levels(df)

    def _ema_rsi_signal_with_levels(self, df):
        df = self._add_indicators(df)
        last = df.iloc[-1]
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        rsi = float(last["rsi"])

        if ema20 > ema50:
            direction = "BUY"
        elif ema20 < ema50:
            direction = "SELL"
        else:
            if rsi < 30:
                direction = "BUY"
            elif rsi > 70:
                direction = "SELL"
            else:
                logger.info("EMA/RSI: no clear direction")
                return None

        confidence = 60
        if direction == "BUY" and rsi > 50:
            confidence += 10
        elif direction == "SELL" and rsi < 50:
            confidence += 10
        if abs(ema20 - ema50) / ema50 > 0.001:
            confidence += 10
        confidence = min(95, round(confidence, 2))

        logger.info(f"✅ EMA/RSI signal: {direction} (conf {confidence})")
        return self._build_signal(df, direction, confidence)

    def _build_signal(self, df, direction, confidence):
        last = df.iloc[-1]
        price = float(last["close"])
        atr = float(last["atr"])

        # --- ATR safety ---
        if np.isnan(atr) or atr <= 0:
            logger.error("ATR is zero or NaN – cannot build signal")
            return None

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


engine = SignalEngine()
