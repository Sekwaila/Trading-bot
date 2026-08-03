"""
SEKWAILA OMEGA X
Signal Engine V7
"""

import numpy as np
import pandas as pd

from signals.market_structure import market_structure
from signals.choch import choch
from signals.order_blocks import order_blocks


class SignalEngine:

    # =====================================
    # EMA
    # =====================================

    def ema(self, series, period):
        return series.ewm(
            span=period,
            adjust=False,
        ).mean()

    # =====================================
    # RSI
    # =====================================

    def rsi(self, series, period=14):

        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        rs = avg_gain / avg_loss.replace(
            0,
            np.nan,
        )

        return 100 - (
            100 / (1 + rs)
        )

    # =====================================
    # ATR
    # =====================================

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

    # =====================================
    # Generate Signal
    # =====================================

    def generate_signal(self, df):

        if (
            df is None
            or df.empty
            or len(df) < 200
        ):
            return None

        df = df.copy()

        df["ema20"] = self.ema(
            df["close"],
            20,
        )

        df["ema50"] = self.ema(
            df["close"],
            50,
        )

        df["ema200"] = self.ema(
            df["close"],
            200,
        )

        df["rsi"] = self.rsi(
            df["close"]
        )

        df["atr"] = self.atr(df)

        structure = market_structure.analyze(df)

        if structure is None:
            return None

        choch_data = choch.analyze(
            structure
        )

        if choch_data is None:
            return None

        ob = order_blocks.analyze(df)

        if ob is None:
            return None

        last = df.iloc[-1]

        price = float(
            last["close"]
        )

        ema20 = float(
            last["ema20"]
        )

        ema50 = float(
            last["ema50"]
        )

        ema200 = float(
            last["ema200"]
        )

        rsi = (
            50
            if pd.isna(last["rsi"])
            else float(last["rsi"])
        )

        atr = (
            price * 0.002
            if pd.isna(last["atr"])
            else float(last["atr"])
        )

        buy_score = 0
        sell_score = 0

        # Trend

        if ema20 > ema50:
            buy_score += 20
        else:
            sell_score += 20

        if ema50 > ema200:
            buy_score += 25
        else:
            sell_score += 25

        # Momentum

        if price > ema20:
            buy_score += 15
        else:
            sell_score += 15

        # RSI

        if rsi > 60:
            buy_score += 20

        elif rsi < 40:
            sell_score += 20

        else:
            buy_score += 10
            sell_score += 10
            
        # =====================================
        
        # Break Of Structure
        # =====================================

        if structure["bullish_bos"]:
            buy_score += 25

        if structure["bearish_bos"]:
            sell_score += 25

        # =====================================
        # Change Of Character
        # =====================================

        if choch_data["bullish_choch"]:
            buy_score += 10

        if choch_data["bearish_choch"]:
            sell_score += 10

        # =====================================
        # Order Blocks
        # =====================================

        if ob["bullish_ob"]:
            buy_score += 15

        if ob["bearish_ob"]:
            sell_score += 15

        # =====================================
        # Final Decision
        # =====================================

        if buy_score >= sell_score:

            signal = "BUY"
            confidence = min(buy_score, 95)

            sl = price - atr
            tp1 = price + atr
            tp2 = price + atr * 2
            tp3 = price + atr * 3

        else:

            signal = "SELL"
            confidence = min(sell_score, 95)

            sl = price + atr
            tp1 = price - atr
            tp2 = price - atr * 2
            tp3 = price - atr * 3

        if confidence < 60:
            return None

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
            "buy_score": buy_score,
            "sell_score": sell_score,
            "market_structure": structure,
            "choch": choch_data,
            "order_blocks": ob,
        }
