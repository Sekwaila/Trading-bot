"""
signal_engine.py – SEKWAILA OMEGA X V6.2
Self-contained institutional signal generator.
No external module imports – all logic built in.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# ------------------ CONFIG ------------------
DEFAULT_CONFIG = {
    "account_balance": 10000,
    "min_candles_between_trades": 3,
    "max_spread_atr_ratio": 0.15,
    "min_stop_atr_ratio": 0.5,
    "execution_buffer": 0.01,
    "confidence_threshold": 60,
    "confidence_ceiling": 95,
    "adx_trend_threshold": 25,
    "volume_ma_period": 20,
    "volume_spike_threshold": 1.5,
    "dynamic_risk_min": 0.005,
    "dynamic_risk_max": 0.02,
    "grade_thresholds": {93: "A+", 85: "A", 75: "B", 65: "C", 0: "D"},
    "killzone_times": {"london": (7, 10), "new_york": (13, 16), "asia": (0, 4)},
    "killzone_timezone_offset": 2,
    "symbol_metadata": {}
}

class Config:
    def __init__(self, config_dict: Dict = None):
        self.data = dict(config_dict) if config_dict else dict(DEFAULT_CONFIG)
        for key, value in DEFAULT_CONFIG.items():
            setattr(self, key.upper(), self.data.get(key, value))
    def get(self, key, default=None):
        return self.data.get(key, default)

# ------------------ INDICATORS ------------------
class Indicators:
    @staticmethod
    def ema(df, series, period):
        return df[series].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(df, series, period=14):
        delta = df[series].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
        return rsi
    
    @staticmethod
    def atr(df, period=14):
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean()
    
    @staticmethod
    def macd(df, series, fast=12, slow=26, signal=9):
        ema_fast = df[series].ewm(span=fast, adjust=False).mean()
        ema_slow = df[series].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def adx(df, period=14):
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        up_move = high - high.shift()
        down_move = low.shift() - low
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        return dx.ewm(alpha=1/period, adjust=False).mean()
    
    @staticmethod
    def volume_ma(df, period=20):
        if "volume" not in df.columns:
            return None
        return df["volume"].rolling(period).mean()
    
    @staticmethod
    def candle_patterns(df):
        high, low, open_, close = df["high"], df["low"], df["open"], df["close"]
        patterns = pd.DataFrame(index=df.index)
        patterns["bullish_engulfing"] = (close > open_) & (open_ <= close.shift()) & (close >= open_.shift()) & (close > close.shift())
        patterns["bearish_engulfing"] = (close < open_) & (open_ >= close.shift()) & (close <= open_.shift()) & (close < close.shift())
        body = abs(close - open_)
        upper_wick = high - np.maximum(close, open_)
        lower_wick = np.minimum(close, open_) - low
        patterns["bullish_pin"] = (lower_wick > 2 * body) & (upper_wick < body)
        patterns["bearish_pin"] = (upper_wick > 2 * body) & (lower_wick < body)
        patterns["bullish_marubozu"] = (close > open_) & (upper_wick < 0.1 * (high-low)) & (lower_wick < 0.1 * (high-low))
        patterns["bearish_marubozu"] = (close < open_) & (upper_wick < 0.1 * (high-low)) & (lower_wick < 0.1 * (high-low))
        patterns["inside_bar"] = (high <= high.shift()) & (low >= low.shift())
        patterns["outside_bar"] = (high > high.shift()) & (low < low.shift())
        return patterns

# ------------------ ENGINE ------------------
class SignalEngine:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.indicators = Indicators()
    
    def _prepare_data(self, df):
        df = df.copy()
        df["ema20"] = self.indicators.ema(df, "close", 20)
        df["ema50"] = self.indicators.ema(df, "close", 50)
        df["ema200"] = self.indicators.ema(df, "close", 200)
        df["rsi"] = self.indicators.rsi(df, "close")
        df["atr"] = self.indicators.atr(df)
        macd_line, macd_signal, macd_hist = self.indicators.macd(df, "close")
        df["macd_line"] = macd_line
        df["macd_signal"] = macd_signal
        df["macd_hist"] = macd_hist
        if "volume" in df.columns:
            df["volume_ma"] = self.indicators.volume_ma(df, self.config.VOLUME_MA_PERIOD)
        df["candle_patterns"] = self.indicators.candle_patterns(df)
        return df
    
    def _detect_regime(self, df):
        adx_val = self.indicators.adx(df).iloc[-1]
        if adx_val > self.config.ADX_TREND_THRESHOLD:
            return "trending"
        else:
            atr_pct = self.indicators.atr(df).iloc[-1] / df["close"].iloc[-1] * 100
            return "ranging_high" if atr_pct > 0.15 else "ranging_low"
    
    def _get_symbol_metadata(self, symbol):
        return self.config.get("symbol_metadata", {}).get(symbol, {
            "pip_value": 1.0, "tick_size": 0.0001, "contract_size": 100000,
            "lot_step": 0.01, "min_lot": 0.01
        })
    
    def _calculate_position_size(self, price, sl, symbol, confidence):
        meta = self._get_symbol_metadata(symbol)
        conf_norm = (confidence - 60) / 35
        risk_pct = self.config.DYNAMIC_RISK_MIN + conf_norm * (self.config.DYNAMIC_RISK_MAX - self.config.DYNAMIC_RISK_MIN)
        risk_amount = self.config.ACCOUNT_BALANCE * risk_pct
        pip_value = meta["pip_value"]
        tick_size = meta["tick_size"]
        contract_size = meta["contract_size"]
        lot_step = meta["lot_step"]
        min_lot = meta["min_lot"]
        risk_ticks = abs(price - sl) / tick_size
        denominator = 10.0 if tick_size == 0.0001 else 1.0
        risk_per_lot = (risk_ticks / denominator) * pip_value * contract_size
        if risk_per_lot == 0:
            return 0.0, 0.0
        raw_lot = risk_amount / risk_per_lot
        lot = max(min_lot, (raw_lot // lot_step) * lot_step)
        risk_currency = lot * risk_per_lot
        return round(lot, 2), round(risk_currency, 2)
    
    def _is_in_killzone(self, current_time):
        killzone_times = self.config.get("killzone_times", {})
        offset = self.config.get("killzone_timezone_offset", 0)
        gmt_time = current_time - timedelta(hours=offset)
        hour = gmt_time.hour
        for start, end in killzone_times.values():
            if start <= hour < end:
                return True
        return False
    
    def _score_factors(self, df, direction):
        reasons = []
        price = df["close"].iloc[-1]
        atr = df["atr"].iloc[-1]
        
        # Trend
        ema20, ema50, ema200 = df["ema20"].iloc[-1], df["ema50"].iloc[-1], df["ema200"].iloc[-1]
        if direction == "BUY" and ema20 > ema50 > ema200:
            trend_score = 1.0
        elif direction == "SELL" and ema20 < ema50 < ema200:
            trend_score = 1.0
        else:
            if direction == "BUY" and ema20 > ema50:
                trend_score = 0.6
            elif direction == "SELL" and ema20 < ema50:
                trend_score = 0.6
            else:
                trend_score = 0.3
        adx_val = self.indicators.adx(df).iloc[-1]
        trend_score *= min(1.0, adx_val / 50)
        reasons.append({"factor": "Trend Strength", "score": trend_score})
        
        # Volume Spike
        if "volume" in df.columns and "volume_ma" in df.columns:
            vol = df["volume"].iloc[-1]
            vol_ma = df["volume_ma"].iloc[-1]
            if vol_ma > 0:
                spike = vol / vol_ma
                vol_score = min(1.0, (spike - 1.0) / 1.0)
                vol_score = max(0.0, vol_score)
            else:
                vol_score = 0.0
        else:
            vol_score = 0.3
        reasons.append({"factor": "Volume Spike", "score": vol_score})
        
        # Candle Patterns
        patterns = df["candle_patterns"].iloc[-1]
        pattern_score = 0.0
        if direction == "BUY":
            if patterns["bullish_engulfing"]:
                pattern_score = 1.0
            elif patterns["bullish_pin"]:
                pattern_score = 0.8
            elif patterns["bullish_marubozu"]:
                pattern_score = 0.7
        else:
            if patterns["bearish_engulfing"]:
                pattern_score = 1.0
            elif patterns["bearish_pin"]:
                pattern_score = 0.8
            elif patterns["bearish_marubozu"]:
                pattern_score = 0.7
        reasons.append({"factor": "Candle Pattern", "score": pattern_score})
        
        # Killzone
        killzone_score = 1.0 if self._is_in_killzone(datetime.now()) else 0.0
        reasons.append({"factor": "Killzone", "score": killzone_score})
        
        # RSI alignment
        rsi_val = df["rsi"].iloc[-1]
        if direction == "BUY" and 40 < rsi_val < 70:
            rsi_score = 1.0
        elif direction == "SELL" and 30 < rsi_val < 60:
            rsi_score = 1.0
        else:
            rsi_score = 0.5
        reasons.append({"factor": "RSI", "score": rsi_score})
        
        # MACD alignment
        macd_hist = df["macd_hist"].iloc[-1]
        if direction == "BUY" and macd_hist > 0:
            macd_score = 1.0
        elif direction == "SELL" and macd_hist < 0:
            macd_score = 1.0
        else:
            macd_score = 0.5
        reasons.append({"factor": "MACD", "score": macd_score})
        
        return reasons
    
    def _compute_confidence(self, reasons):
        total_weight = 0
        weighted_sum = 0
        for r in reasons:
            weight = 1.0
            total_weight += weight
            weighted_sum += r["score"] * weight
        raw = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0
        return min(raw, self.config.CONFIDENCE_CEILING)
    
    def _get_grade(self, confidence):
        grade = "D"
        for threshold, g in self.config.GRADE_THRESHOLDS.items():
            if confidence >= threshold:
                grade = g
                break
        return grade
    
    def generate_signal(self, df, symbol="EURUSD", timeframe="1H"):
        # Prepare data
        df = self._prepare_data(df)
        
        # Determine direction
        ema20, ema50, ema200 = df["ema20"].iloc[-1], df["ema50"].iloc[-1], df["ema200"].iloc[-1]
        if ema20 > ema50 > ema200:
            direction = "BUY"
        elif ema20 < ema50 < ema200:
            direction = "SELL"
        else:
            # If flat, use close vs ema20
            if df["close"].iloc[-1] > ema20:
                direction = "BUY"
            else:
                direction = "SELL"
        
        # Basic risk/reward
        price = df["close"].iloc[-1]
        atr = df["atr"].iloc[-1]
        
        # Stop loss
        if direction == "BUY":
            sl = price - atr * 1.5
        else:
            sl = price + atr * 1.5
        
        risk = abs(price - sl)
        if risk < atr * self.config.MIN_STOP_ATR_RATIO:
            return None
        
        # Entry with buffer
        buffer = self.config.EXECUTION_BUFFER
        if direction == "BUY":
            entry = price - risk * buffer
            entry = max(entry, price - risk * 0.5)
        else:
            entry = price + risk * buffer
            entry = min(entry, price + risk * 0.5)
        
        # Take profits
        if direction == "BUY":
            tp1, tp2, tp3 = entry + risk, entry + risk*2, entry + risk*3
        else:
            tp1, tp2, tp3 = entry - risk, entry - risk*2, entry - risk*3
        
        # Score factors
        reasons = self._score_factors(df, direction)
        confidence = self._compute_confidence(reasons)
        if confidence < self.config.CONFIDENCE_THRESHOLD:
            return None
        
        grade = self._get_grade(confidence)
        lot_size, risk_currency = self._calculate_position_size(entry, sl, symbol, confidence)
        if lot_size <= 0:
            return None
        
        # Build signal dict
        signal = {
            "signal": direction,
            "confidence": confidence,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "grade": grade,
            "lot": lot_size,
            "risk": risk_currency,
            "diagnostics": {
                "regime": self._detect_regime(df),
                "atr": round(atr, 5),
                "rsi": round(df["rsi"].iloc[-1], 2),
                "macd_hist": round(df["macd_hist"].iloc[-1], 5),
                "adx": round(self.indicators.adx(df).iloc[-1], 2)
            },
            "reasons": [r["factor"] for r in reasons if r["score"] > 0.5]
        }
        return signal

# Instantiate global engine
engine = SignalEngine()
