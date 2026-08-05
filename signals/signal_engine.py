"""
signal_engine.py
SEKWAILA OMEGA X v6.1
Fixed:
- Pandas Series ambiguity error
- Yahoo Finance MultiIndex issue
- Safe float conversion
"""

import numpy as np
import pandas as pd


class SignalEngine:

    def __init__(self):
        pass


    def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):

        if df is None or df.empty:
            return None

        if len(df) < 50:
            return None


        df = df.copy()


        # Force numeric columns
        required = ["open", "high", "low", "close"]

        for col in required:
            if col not in df.columns:
                return None

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )


        df.dropna(
            subset=required,
            inplace=True
        )


        if len(df) < 50:
            return None


        # Indicators

        df["ema20"] = (
            df["close"]
            .ewm(span=20, adjust=False)
            .mean()
        )

        df["ema50"] = (
            df["close"]
            .ewm(span=50, adjust=False)
            .mean()
        )

        df["rsi"] = self._rsi(
            df["close"],
            14
        )

        df["atr"] = self._atr(
            df,
            14
        )


        last = df.iloc[-1]
        prev = df.iloc[-2]


        # Convert everything to float
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])

        prev_ema20 = float(prev["ema20"])
        prev_ema50 = float(prev["ema50"])

        rsi = float(last["rsi"])
        price = float(last["close"])
        atr = float(last["atr"])


        if np.isnan(atr) or atr == 0:
            return None


        # Signal logic

        if ema20 > ema50 and prev_ema20 <= prev_ema50:

            direction = "BUY"

        elif ema20 < ema50 and prev_ema20 >= prev_ema50:

            direction = "SELL"

        else:

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
            tp3 = price + atr * 4


        else:

            sl = price + atr * 1.5
            tp1 = price - atr * 1.5
            tp2 = price - atr * 2.5
            tp3 = price - atr * 4



        entry = (
            price - atr * 0.01
            if direction == "BUY"
            else price + atr * 0.01
        )


        # Confidence

        confidence = 60 + (
            abs(rsi - 50) / 50
        ) * 20


        if abs(ema20 - ema50) / ema50 > 0.001:
            confidence += 10


        confidence = min(
            95,
            round(confidence,2)
        )


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

            "entry": round(entry,5),

            "sl": round(sl,5),

            "tp1": round(tp1,5),

            "tp2": round(tp2,5),

            "tp3": round(tp3,5),

            "grade": grade,

            "lot":0.01,

            "risk":round(abs(entry-sl)*10000,2),


            "diagnostics":{

                "rsi":round(rsi,2),

                "atr":round(atr,5),

                "ema20":round(ema20,5),

                "ema50":round(ema50,5)

            },


            "reasons":[

                f"EMA trend {direction}",

                f"RSI {rsi:.1f}"

            ]

        }



    @staticmethod
    def _rsi(series, period=14):

        delta = series.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)


        avg_gain = (
            gain
            .ewm(
                alpha=1/period,
                adjust=False
            )
            .mean()
        )


        avg_loss = (
            loss
            .ewm(
                alpha=1/period,
                adjust=False
            )
            .mean()
        )


        rs = avg_gain / avg_loss.replace(0,np.nan)

        rsi = 100 - (
            100/(1+rs)
        )


        return rsi.fillna(50)



    @staticmethod
    def _atr(df, period=14):

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


        return (
            tr
            .ewm(
                alpha=1/period,
                adjust=False
            )
            .mean()
        )



engine = SignalEngine()
