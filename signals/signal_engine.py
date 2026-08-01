import pandas as pd
import numpy as np


class SignalEngine:

    def __init__(self, confidence=90):
        self.confidence = confidence

    def ema(self, df, period):
        return df["close"].ewm(span=period).mean()

    def rsi(self, df, period=14):
        delta = df["close"].diff()

        gain = delta.where(delta > 0, 0).rolling(period).mean()

        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

        rs = gain / loss

        return 100 - (100 / (1 + rs))

    def atr(self, df, period=14):

        high_low = df.high - df.low

        high_close = abs(df.high - df.close.shift())

        low_close = abs(df.low - df.close.shift())

        tr = pd.concat(
            [high_low, high_close, low_close],
            axis=1
        ).max(axis=1)

        return tr.rolling(period).mean()

    def trend(self, df):

        ema50 = self.ema(df, 50)

        ema200 = self.ema(df, 200)

        if ema50.iloc[-1] > ema200.iloc[-1]:
            return "BUY"

        return "SELL"

    def strength(self, df):

        rsi = self.rsi(df).iloc[-1]

        if rsi > 70:
            return "AGGRESSIVE BUY", 98

        if rsi > 60:
            return "STRONG BUY", 95

        if rsi < 30:
            return "AGGRESSIVE SELL", 98

        if rsi < 40:
            return "STRONG SELL", 95

        return "WAIT", 50

    def generate_signal(self, df):

        trend = self.trend(df)

        signal, confidence = self.strength(df)

        price = float(df.close.iloc[-1])

        atr = float(self.atr(df).iloc[-1])

        if np.isnan(atr):
            atr = price * 0.005

        if "BUY" in signal:

            sl = price - atr

            tp1 = price + atr

            tp2 = price + atr * 2

            tp3 = price + atr * 3

        elif "SELL" in signal:

            sl = price + atr

            tp1 = price - atr

            tp2 = price - atr * 2

            tp3 = price - atr * 3

        else:

            sl = price

            tp1 = price

            tp2 = price

            tp3 = price

        return {

            "signal": signal,

            "trend": trend,

            "confidence": confidence,

            "entry": round(price, 5),

            "sl": round(sl, 5),

            "tp1": round(tp1, 5),

            "tp2": round(tp2, 5),

            "tp3": round(tp3, 5)

        }
