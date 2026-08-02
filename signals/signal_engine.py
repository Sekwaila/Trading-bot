"""
SEKWAILA OMEGA X
Professional Signal Engine v5
"""

import numpy as np
import pandas as pd


class SignalEngine:

    def __init__(
        self,
        ema_fast=50,
        ema_slow=200,
        rsi_period=14,
        atr_period=14,
    ):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.atr_period = atr_period

    # ==========================================
    # EMA
    # ==========================================

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    # ==========================================
    # RSI (Wilder)
    # ==========================================

    def rsi(self, close):

        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / self.rsi_period,
            adjust=False,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / self.rsi_period,
            adjust=False,
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        return 100 - (100 / (1 + rs))

    # ==========================================
    # ATR
    # ==========================================

    def atr(self, df):

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = pd.concat(
            [
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return tr.rolling(self.atr_period).mean()

    # ==========================================
    # SIGNAL GENERATION
    # ==========================================

    def generate_signal(self, df):

        if df is None or df.empty:
            return None

        if len(df) < self.ema_slow:
            return None

        df = df.copy()

        df["ema_fast"] = self.ema(df["close"], self.ema_fast)
        df["ema_slow"] = self.ema(df["close"], self.ema_slow)
        df["rsi"] = self.rsi(df["close"])
        df["atr"] = self.atr(df)

        last = df.iloc[-1]

        if (
            pd.isna(last["ema_fast"])
            or pd.isna(last["ema_slow"])
            or pd.isna(last["rsi"])
            or pd.isna(last["atr"])
        ):
            return None

        price = float(last["close"])
        atr = float(last["atr"])
        rsi = float(last["rsi"])

        if last["ema_fast"] > last["ema_slow"]:

            signal = "BUY"

            confidence = 70

            if rsi > 55:
                confidence += 10

            if price > last["ema_fast"]:
                confidence += 10

            if rsi > 65:
                confidence += 10

            sl = price - atr
            tp1 = price + atr
            tp2 = price + atr * 2
            tp3 = price + atr * 3

        else:

            signal = "SELL"

            confidence = 70

            if rsi < 45:
                confidence += 10

            if price < last["ema_fast"]:
                confidence += 10

            if rsi < 35:
                confidence += 10

            sl = price + atr
            tp1 = price - atr
            tp2 = price - atr * 2
            tp3 = price - atr * 3

        confidence = min(confidence, 100)

        return {
            "signal": signal,
            "confidence": confidence,
            "entry": round(price, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "rsi": round(rsi, 2),
            "atr": round(atr, 5),
            "ema_fast": round(float(last["ema_fast"]), 5),
            "ema_slow": round(float(last["ema_slow"]), 5),
        }
