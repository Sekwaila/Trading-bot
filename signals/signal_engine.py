"""
SEKWAILA OMEGA X
Professional Signal Engine v6
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
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    ):

        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    # ==========================================
    # EMA
    # ==========================================

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    # ==========================================
    # RSI
    # ==========================================

    def rsi(self, close):

        delta = close.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1/self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.rsi_period, adjust=False).mean()

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
                high-low,
                (high-close.shift()).abs(),
                (low-close.shift()).abs()
            ],
            axis=1
        ).max(axis=1)

        return tr.rolling(self.atr_period).mean()

    # ==========================================
    # MACD
    # ==========================================

    def macd(self, close):

        ema12 = self.ema(close, self.macd_fast)
        ema26 = self.ema(close, self.macd_slow)

        macd = ema12 - ema26
        signal = macd.ewm(span=self.macd_signal, adjust=False).mean()

        return macd, signal

    # ==========================================
    # SIGNAL
    # ==========================================

    def generate_signal(self, df):

        if df.empty:
            return None

        if len(df) < 200:
            return None

        df = df.copy()

        df["ema50"] = self.ema(df["close"], 50)
        df["ema200"] = self.ema(df["close"], 200)

        df["rsi"] = self.rsi(df["close"])

        df["atr"] = self.atr(df)

        df["macd"], df["macd_signal"] = self.macd(df["close"])

        last = df.iloc[-1]

        if last.isna().any():
            return None

        price = float(last["close"])
        atr = float(last["atr"])

        confidence = 0

        buy = False
        sell = False

        # EMA

        if last["ema50"] > last["ema200"]:
            buy = True
            confidence += 30
        else:
            sell = True
            confidence += 30

        # RSI

        if 50 < last["rsi"] < 70:
            confidence += 20

        elif 30 < last["rsi"] < 50:
            confidence += 20

        # MACD

        if buy and last["macd"] > last["macd_signal"]:
            confidence += 30

        if sell and last["macd"] < last["macd_signal"]:
            confidence += 30

        # Momentum

        if buy and price > last["ema50"]:
            confidence += 20

       
