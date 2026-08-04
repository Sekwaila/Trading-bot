"""
SEKWAILA OMEGA X
Signal Engine V7
"""

import numpy as np
import pandas as pd

from signals.market_structure import market_structure
from signals.choch import choch
from signals.order_blocks import order_blocks
from signals.fair_value_gap import fair_value_gap


class SignalEngine:

    # =====================================
    # EMA
    # =====================================

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    # =====================================
    # RSI
    # =====================================

    def rsi(self, series, period=14):

        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)

        return rsi

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

        return tr.ewm(alpha=1 / period, adjust=False).mean()

    # =====================================
    # Generate Signal
    # =====================================

    def generate_signal(self, df):

        if df is None or df.empty or len(df) < 201:
            return None

        df = df.copy()

        df["ema20"] = self.ema(df["close"], 20)
        df["ema50"] = self.ema(df["close"], 50)
        df["ema200"] = self.ema(df["close"], 200)
        df["rsi"] = self.rsi(df["close"])
        df["atr"] = self.atr(df)

        structure = market_structure.analyze(df)

        if structure is None:
            return None

        choch_data = choch.analyze(structure)

        if choch_data is None:
            return None

        ob = order_blocks.analyze(df)

        if ob is None:
            return None

        fvg = fair_value_gap.analyze(df)

        if fvg is None:
            return None

        # Use last CLOSED candle

        last = df.iloc[-2]

        price = float(last["close"])

        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        ema200 = float(last["ema200"])

        rsi = 50 if pd.isna(last["rsi"]) else float(last["rsi"])

        # --- FIX: floor ATR, don't just guard against NaN ---
        # A near-zero ATR (quiet session, flat/illiquid print) previously
        # slipped past the pd.isna() check and collapsed SL/TP1/TP2/TP3
        # onto the entry price (zero-width stop, unusable targets).
        atr_raw = last["atr"]
        min_atr = price * 0.0005

        if pd.isna(atr_raw) or float(atr_raw) < min_atr:
            atr = price * 0.002
        else:
            atr = float(atr_raw)

        buy_score = 0
        sell_score = 0

        # =====================================
        # EMA Trend
        # =====================================

        if ema20 > ema50:
            buy_score += 20
        else:
            sell_score += 20

        if ema50 > ema200:
            buy_score += 25
        else:
            sell_score += 25

        # =====================================
        # Momentum
        # =====================================

        if price > ema20:
            buy_score += 15
        else:
            sell_score += 15

        # =====================================
        # RSI
        # =====================================

        if rsi > 60:
            buy_score += 20
        elif rsi < 40:
            sell_score += 20
        else:
            buy_score += 10
            sell_score += 10

        # =====================================
        # Break Of Structure (BOS)
        # =====================================

        if structure.get("bullish_bos"):
            buy_score += 25

        if structure.get("bearish_bos"):
            sell_score += 25

        # =====================================
        # Change Of Character (CHoCH)
        # =====================================

        if choch_data.get("bullish_choch"):
            buy_score += 10

        if choch_data.get("bearish_choch"):
            sell_score += 10

        # =====================================
        # Order Blocks
        # =====================================

        if ob.get("bullish_ob"):
            buy_score += 15

        if ob.get("bearish_ob"):
            sell_score += 15

        # =====================================
        # Fair Value Gap
        # =====================================

        if fvg.get("bullish_fvg"):
            buy_score += 15

        if fvg.get("bearish_fvg"):
            sell_score += 15

        # =====================================
        # No Edge
        # =====================================

        if buy_score == sell_score:
            return None

        # =====================================
        # Final Decision
        # =====================================

        if buy_score > sell_score:

            signal = "BUY"
            confidence = min(buy_score, 95)

            sl = price - atr
            tp1 = price + atr
            tp2 = price + (atr * 2)
            tp3 = price + (atr * 3)

        else:

            signal = "SELL"
            confidence = min(sell_score, 95)

            sl = price + atr
            tp1 = price - atr
            tp2 = price - (atr * 2)
            tp3 = price - (atr * 3)

        # Ignore weak setups

        if confidence < 60:
            return None

        # =====================================
        # Return Signal
        # =====================================

        return {
            "signal": signal,
            "confidence": confidence,
            "entry": round(price, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "rsi": round(rsi, 2),
            # EMA Trend Strength
            "trend_strength": round(ema50 - ema200, 5),
            "macd": round(ema50 - ema200, 5),
            "atr": round(atr, 5),
            "buy_score": buy_score,
            "sell_score": sell_score,
            "market_structure": structure,
            "choch": choch_data,
            "order_blocks": ob,
            "fair_value_gap": fvg,
        }


engine = SignalEngine()
