"""
SEKWAILA OMEGA X
Signal Engine V10
"""

import numpy as np
import pandas as pd

from signals.market_structure import market_structure
from signals.choch import choch
from signals.order_blocks import order_blocks
from signals.fair_value_gap import fair_value_gap
from signals.liquidity import liquidity
from signals.equal_highs_lows import equal_highs_lows
from signals.premium_discount import premium_discount
from signals.breaker_blocks import breaker_blocks
from signals.mitigation_blocks import mitigation_blocks
from signals.inducement import inducement
from signals.displacement import displacement
from signals.sessions import sessions
from signals.multi_timeframe import multi_timeframe


class SignalEngine:

    # =====================================
    # EMA
    # =====================================

    def ema(self, series, period):
        return series.ewm(span=period, adjust=False).mean()

    # =====================================
    # MACD
    # =====================================

    def macd(self, series, fast=12, slow=26, signal=9):

        ema_fast = self.ema(series, fast)
        ema_slow = self.ema(series, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

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
    # Helper to debug module failures
    # Now raises an exception to show the exact failing module
    # =====================================

    def _check_module(self, name, result):
        if result is None:
            raise ValueError(f"{name} returned None")
        return result

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

        macd_line, signal_line, histogram = self.macd(df["close"])

        df["macd_line"] = macd_line
        df["macd_signal"] = signal_line
        df["macd_hist"] = histogram

        # =====================================
        # All analysis modules with debug checks
        # =====================================

        structure = self._check_module("market_structure", market_structure.analyze(df))
        if structure is None:
            return None

        choch_data = self._check_module("choch", choch.analyze(structure))
        if choch_data is None:
            return None

        ob = self._check_module("order_blocks", order_blocks.analyze(df))
        if ob is None:
            return None

        fvg = self._check_module("fair_value_gap", fair_value_gap.analyze(df))
        if fvg is None:
            return None

        liquidity_data = self._check_module("liquidity", liquidity.analyze(df))
        if liquidity_data is None:
            return None

        eqhl = self._check_module("equal_highs_lows", equal_highs_lows.analyze(df))
        if eqhl is None:
            return None

        premium_data = self._check_module("premium_discount", premium_discount.analyze(df))
        if premium_data is None:
            return None

        breaker_data = self._check_module("breaker_blocks", breaker_blocks.analyze(df))
        if breaker_data is None:
            return None

        mitigation_data = self._check_module("mitigation_blocks", mitigation_blocks.analyze(df))
        if mitigation_data is None:
            return None

        inducement_data = self._check_module("inducement", inducement.analyze(df))
        if inducement_data is None:
            return None

        displacement_data = self._check_module("displacement", displacement.analyze(df))
        if displacement_data is None:
            return None

        session_data = self._check_module("sessions", sessions.analyze(df))
        if session_data is None:
            return None

        mtf_data = self._check_module("multi_timeframe", multi_timeframe.analyze(df))
        if mtf_data is None:
            return None

        # =====================================
        # Scoring
        # =====================================

        last = df.iloc[-2]

        price = float(last["close"])
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        ema200 = float(last["ema200"])

        rsi = 50 if pd.isna(last["rsi"]) else float(last["rsi"])

        macd_val = 0.0 if pd.isna(last["macd_line"]) else float(last["macd_line"])
        macd_signal_val = 0.0 if pd.isna(last["macd_signal"]) else float(last["macd_signal"])
        macd_hist = 0.0 if pd.isna(last["macd_hist"]) else float(last["macd_hist"])

        atr_raw = last["atr"]
        min_atr = price * 0.0005

        if pd.isna(atr_raw) or float(atr_raw) < min_atr:
            atr = price * 0.002
        else:
            atr = float(atr_raw)

        buy_score = 0
        sell_score = 0

        if ema20 > ema50:
            buy_score += 20
        else:
            sell_score += 20

        if ema50 > ema200:
            buy_score += 25
        else:
            sell_score += 25

        if price > ema20:
            buy_score += 15
        else:
            sell_score += 15

        if rsi > 60:
            buy_score += 20
        elif rsi < 40:
            sell_score += 20
        else:
            buy_score += 10
            sell_score += 10

        if macd_val > macd_signal_val:
            buy_score += 10
        else:
            sell_score += 10

        if structure.get("bullish_bos"):
            buy_score += 25
        if structure.get("bearish_bos"):
            sell_score += 25

        if choch_data.get("bullish_choch"):
            buy_score += 10
        if choch_data.get("bearish_choch"):
            sell_score += 10

        if ob.get("bullish_ob"):
            buy_score += 15
        if ob.get("bearish_ob"):
            sell_score += 15

        if fvg.get("bullish_fvg"):
            buy_score += 15
        if fvg.get("bearish_fvg"):
            sell_score += 15

        if liquidity_data.get("buy_liquidity"):
            buy_score += 20
        if liquidity_data.get("sell_liquidity"):
            sell_score += 20

        if eqhl.get("equal_low"):
            buy_score += 10
        if eqhl.get("equal_high"):
            sell_score += 10

        if premium_data.get("discount"):
            buy_score += 15
        if premium_data.get("premium"):
            sell_score += 15

        if breaker_data.get("bullish_breaker"):
            buy_score += 20
        if breaker_data.get("bearish_breaker"):
            sell_score += 20

        # =====================================
        # Mitigation Blocks (V10)
        # =====================================

        if mitigation_data.get("bullish_mitigation"):
            buy_score += 15
        if mitigation_data.get("bearish_mitigation"):
            sell_score += 15

        # =====================================
        # Inducement (V10)
        # =====================================

        if inducement_data.get("bullish_inducement"):
            buy_score += 10
        if inducement_data.get("bearish_inducement"):
            sell_score += 10

        # =====================================
        # Displacement (V10)
        # =====================================

        if displacement_data.get("bullish_displacement"):
            buy_score += 20
        if displacement_data.get("bearish_displacement"):
            sell_score += 20

        # =====================================
        # Sessions (V10)
        # =====================================

        if session_data.get("london") or session_data.get("new_york"):
            buy_score += 5
            sell_score += 5

        # =====================================
        # Multi-Timeframe Alignment (V10)
        # =====================================

        if mtf_data.get("bullish_alignment"):
            buy_score += 25
        if mtf_data.get("bearish_alignment"):
            sell_score += 25

        if buy_score == sell_score:
            return None

        if buy_score > sell_score:

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
            "trend_strength": round(ema50 - ema200, 5),
            "macd": round(macd_val, 5),
            "macd_signal": round(macd_signal_val, 5),
            "macd_hist": round(macd_hist, 5),
            "atr": round(atr, 5),
            "buy_score": buy_score,
            "sell_score": sell_score,
            "market_structure": structure,
            "choch": choch_data,
            "order_blocks": ob,
            "fair_value_gap": fvg,
            "liquidity": liquidity_data,
            "equal_highs_lows": eqhl,
            "premium_discount": premium_data,
            "breaker_blocks": breaker_data,
            "mitigation_blocks": mitigation_data,
            "inducement": inducement_data,
            "displacement": displacement_data,
            "sessions": session_data,
            "multi_timeframe": mtf_data,
        }


engine = SignalEngine()
