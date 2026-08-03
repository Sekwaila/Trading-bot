"""
SEKWAILA OMEGA X
Signal Engine
"""

import pandas as pd


class SignalEngine:

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series, period=14):
        delta = series.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss.replace(0, 0.000001)

        return 100 - (100 / (1 + rs))

    def atr(self, df, period=14):
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

        return tr.rolling(period).mean()

    def generate_signal(self, df):

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

        rsi = 50.0 if pd.isna(last["rsi"]) else float(last["rsi"])
        atr = price * 0.002 if pd.isna(last["atr"]) else float(last["atr"])

        # Support & Resistance
        recent_high = df["high"].tail(20).max()
        recent_low = df["low"].tail(20).min()

        # Trend + RSI + Support/Resistance Filter
        if (
            ema50 > ema200
            and rsi > 55
            and price < recent_high - atr
        ):
            signal = "BUY"

        elif (
            ema50 < ema200
            and rsi < 45
            and price > recent_low + atr
        ):
            signal = "SELL"

        else:
            return None

        # Dynamic Confidence
        confidence = 60

        confidence += 15

        if signal == "BUY":
            if rsi >= 70:
                confidence += 5
            elif rsi >= 60:
                confidence += 10
            elif rsi >= 55:
                confidence += 15
        else:
            if rsi <= 30:
                confidence += 5
            elif rsi <= 40:
                confidence += 10
            elif rsi <= 45:
                confidence += 15

        gap = abs(ema50 - ema200)

        if gap > atr:
            confidence += 10

        confidence = min(confidence, 95)

        # Targets
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
            "confidence": confidence,
            "entry": round(price, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "rsi": round(rsi, 2),
            "macd": round(ema50 - ema200, 5),
            "atr": round(atr, 5),
        }
