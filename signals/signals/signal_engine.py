"""
SEKWAILA OMEGA X
Signal Engine
"""

import pandas as pd


class SignalEngine:

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    def generate_signal(self, df):

        if df is None or df.empty or len(df) < 50:
            return None

        ema50 = self.ema(df["close"], 50)
        ema200 = self.ema(df["close"], 200)

        price = float(df["close"].iloc[-1])

        signal = "BUY" if ema50.iloc[-1] > ema200.iloc[-1] else "SELL"

        atr = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]

        if pd.isna(atr):
            atr = price * 0.002

        if signal == "BUY":
            sl = price - atr
            tp1 = price + atr
            tp2 = price + atr * 2
            tp3 = price + atr * 3
        else:
            sl = price + atr
            tp1 = price - atr
            tp2 = price - atr * 2
            tp3 = price - atr * 3

        return {
            "signal": signal,
            "confidence": 70,
            "entry": round(price, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
        }
