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
        Returns a dict with keys:
        signal, confidence, entry, sl, tp1, tp2, tp3, grade, lot, risk
        """

        # Ensure enough candles
        if df is None or len(df) < 50:
            return None

        df = df.copy()

        # Remove duplicate columns (prevents Pandas Series errors)
        df = df.loc[:, ~df.columns.duplicated()]

        # Ensure required columns exist
        required = ["close", "high", "low"]
        for col in required:
            if col not in df.columns:
                return None

        # Indicators
        df["ema20"] = df["close"].ewm(
            span=20,
            adjust=False
        ).mean()

        df["ema50"] = df["close"].ewm(
            span=50,
            adjust=False
        ).mean()

        df["rsi"] = self._rsi(df["close"], 14)
        df["atr"] = self._atr(df, 14)

        # Remove incomplete rows
        df = df.dropna()

        if len(df) < 2:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Convert values to normal floats
        ema20_last = float(last["ema20"])
        ema50_last = float(last["ema50"])

        ema20_prev = float(prev["ema20"])
        ema50_prev = float(prev["ema50"])

        rsi = float(last["rsi"])
        price = float(last["close"])
        atr = float(last["atr"])

        if atr <= 0:
            return None

        # Signal detection
        if ema20_last > ema50_last and ema20_prev <= ema50_prev:
            direction = "BUY"

        elif ema20_last < ema50_last and ema20_prev >= ema50_prev:
            direction = "SELL"

        else:
            # RSI fallback
            if rsi < 30:
                direction = "BUY"

            elif rsi > 70:
                direction = "SELL"

            else:
                return None

        # Risk levels
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


        # Entry buffer
        buffer = 0.01

        if direction == "BUY":
            entry = price - atr * buffer
        else:
            entry = price + atr * buffer


        # Confidence
        confidence = 60 + (abs(rsi - 50) / 50) * 20

        if abs(ema20_last - ema50_last) / ema50_last > 0.001:
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


        # Fixed lot size
        lot = 0.01

        risk = lot * abs(entry - sl) * 10000


        return {

            "signal": direction,

            "confidence": round(confidence, 2),

            "entry": round(entry, 5),

            "sl": round(sl, 5),

            "tp1": round(tp1, 5),

            "tp2": round(tp2, 5),

            "tp3": round(tp3, 5),

            "grade": grade,

            "lot": lot,

            "risk": round(risk, 2),

            "diagnostics": {

                "rsi": round(rsi, 2),

                "atr": round(atr, 5),

                "ema20": round(ema20_last, 5),

                "ema50": round(ema50_last, 5),

            },

            "reasons": [

                f"EMA crossover {direction}",

                f"RSI {rsi:.1f}"

            ]

        }


    @staticmethod
    def _rsi(series, period=14):

        delta = series.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)


        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()


        rs = avg_gain / avg_loss.replace(0, np.nan)

        rsi = 100 - (100 / (1 + rs))


        rsi = rsi.where(avg_loss != 0, 100.0)

        rsi = rsi.where(
            ~((avg_loss == 0) & (avg_gain == 0)),
            50.0
        )

        return rsi



    @staticmethod
    def _atr(df, period=14):

        high = df["high"]

        low = df["low"]

        close = df["close"]


        tr = pd.concat(

            [

                high - low,

                (high - close.shift()).abs(),

                (low - close.shift()).abs()

            ],

            axis=1

        ).max(axis=1)


        return tr.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()



# Global engine instance
engine = SignalEngine()
