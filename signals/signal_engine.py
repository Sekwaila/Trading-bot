"""
SEKWAILA OMEGA X
Signal Engine v6
"""

import pandas as pd
import numpy as np

from logger import get_logger

logger = get_logger("signal_engine")


class SignalEngine:

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series, period=14):
        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        return 100 - (100 / (1 + rs))

    def atr(self, df, period=14):

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)

        return tr.rolling(period).mean()

    def generate_signal(self, df):

        try:

            if df is None or df.empty or len(df) < 50:
                return None

            df = df.copy()

            df["ema50"] = self.ema(df["close"], 50)
            df["ema200"] = self.ema(df["close"], 200)
            df["rsi"] = self.rsi(df["close"])
            df["atr"] = self.atr(df)

            last = df.iloc[-1]

            price = float(last["close"])

            ema50 = float(last["ema50"])
            ema200 = float(last["ema200"])

            rsi = float(last["rsi"]) if not pd.isna(last["rsi"]) else 50

            atr = float(last["atr"]) if not pd.isna(last["atr"]) else price * 0.002

            signal = "BUY" if ema50 >= ema200 else "SELL"

            confidence = 70

            if signal == "BUY":

                if rsi < 35:
                    confidence += 15

                elif rsi < 50:
                    confidence += 5

                sl = price - atr
                tp1 = price + atr
                tp2 = price + atr * 2
                tp3 = price + atr * 3

            else:

                if rsi > 65:
                    confidence += 15

                elif rsi > 50:
                    confidence += 5

                sl = price + atr
                tp1 = price - atr
                tp2 = price - atr * 2
                tp3 = price - atr * 3

            confidence = min(confidence, 95)

            macd = round(ema50 - ema200, 5)

            return {
                "signal": signal,
                "confidence": confidence,
                "entry": round(price,
