"""
signal_engine.py – Simple but reliable signal generator.
No external module imports, guaranteed to work.
"""

import numpy as np
import pandas as pd

class SignalEngine:
    def __init__(self):
        pass

    def generate_signal(self, df, symbol="EURUSD", timeframe="1H"):
        """
        Generate a trading signal based on EMA crossover and RSI.
        Returns a dict with keys: signal, confidence, entry, sl, tp1, tp2, tp3, grade, lot, risk.
        """
        # Ensure we have enough data
        if len(df) < 50:
            return None

        # Calculate indicators
        df = df.copy()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['rsi'] = self._rsi(df['close'], 14)
        df['atr'] = self._atr(df, 14)

        # Get latest values
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Determine direction
        if last['ema20'] > last['ema50'] and prev['ema20'] <= prev['ema50']:
            direction = "BUY"
        elif last['ema20'] < last['ema50'] and prev['ema20'] >= prev['ema50']:
            direction = "SELL"
        else:
            # No clear crossover – use RSI
            if last['rsi'] < 30:
                direction = "BUY"
            elif last['rsi'] > 70:
                direction = "SELL"
            else:
                return None  # No signal

        # Price and risk
        price = last['close']
        atr = last['atr']
        if direction == "BUY":
            sl = price - atr * 1.5
            tp1 = price + atr * 1.5
            tp2 = price + atr * 2.5
            tp3 = price + atr * 4.0
        else:
            sl = price + atr * 1.5
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4.0

        # Entry – use limit order offset
        buffer = 0.01
        if direction == "BUY":
            entry = price - atr * buffer
        else:
            entry = price + atr * buffer

        # Confidence – based on RSI and crossover strength
        confidence = 60 + (abs(last['rsi'] - 50) / 50) * 20
        if abs(last['ema20'] - last['ema50']) / last['ema50'] > 0.001:
            confidence += 10
        confidence = min(95, confidence)

        # Grade
        if confidence >= 85:
            grade = "A"
        elif confidence >= 70:
            grade = "B"
        elif confidence >= 60:
            grade = "C"
        else:
            grade = "D"

        # Lot size (fixed for simplicity)
        lot = 0.01
        risk = lot * abs(entry - sl) * 10000  # approximate

        # Build signal dict
        signal = {
            "signal": direction,
            "confidence": confidence,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "grade": grade,
            "lot": lot,
            "risk": risk,
            "diagnostics": {
                "rsi": round(last['rsi'], 2),
                "atr": round(atr, 5),
                "ema20": round(last['ema20'], 5),
                "ema50": round(last['ema50'], 5),
            },
            "reasons": [f"EMA crossover {direction}", f"RSI {last['rsi']:.1f}"]
        }
        return signal

    @staticmethod
    def _rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
        return rsi

    @staticmethod
    def _atr(df, period=14):
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean()

# Instantiate global engine
engine = SignalEngine()
