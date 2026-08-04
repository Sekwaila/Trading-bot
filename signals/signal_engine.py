"""
signal_engine.py – SEKWAILA OMEGA X V17.2
Institutional‑grade signal generator for manual trading.
Ready for Streamlit deployment.
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, NamedTuple, Tuple
from enum import Enum
import hashlib
from collections import deque
import os

# Optional scipy for SMT divergence – if not installed, SMT will be skipped
try:
    from scipy import stats
except ImportError:
    stats = None

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
DEFAULT_CONFIG = {
    "risk_per_trade": 0.01,
    "account_balance": 10000,
    "min_candles_between_trades": 3,
    "max_spread_atr_ratio": 0.15,
    "min_stop_atr_ratio": 0.5,
    "execution_buffer": 0.01,
    "confidence_threshold": 75,
    "confidence_ceiling": 95,
    "state_timeout_candles": 20,
    "adx_trend_threshold": 25,
    "volume_ma_period": 20,
    "volume_spike_threshold": 1.5,

    # Candle patterns
    "engulfing_weight": 0.15,
    "pinbar_weight": 0.10,
    "marubozu_weight": 0.10,

    # Risk
    "dynamic_risk_enabled": True,
    "dynamic_risk_min": 0.005,
    "dynamic_risk_max": 0.02,
    "grade_thresholds": {93: "A+", 85: "A", 75: "B", 65: "C", 0: "D"},

    # Institutional
    "vwap_period": 14,
    "ote_min": 0.618,
    "ote_max": 0.786,
    "killzone_times": {"london": (7, 10), "new_york": (13, 16), "asia": (0, 4)},
    "killzone_timezone_offset": 2,   # SAST = UTC+2

    # Symbol metadata
    "symbol_metadata": {},

    # Enabled modules (add/remove as needed)
    "enabled_modules": [
        "market_structure", "choch", "order_blocks", "fvg", "liquidity",
        "displacement", "sessions", "mtf", "mitigation",
        "smt_divergence", "vwap", "killzones", "ote", "orderflow"
    ]
}

class Config:
    def __init__(self, config_dict: Dict = None):
        self.data = dict(config_dict) if config_dict else dict(DEFAULT_CONFIG)
        for key, value in DEFAULT_CONFIG.items():
            setattr(self, key.upper(), self.data.get(key, value))
        self._dict = self.data

    def get(self, key, default=None):
        return self.data.get(key, default)


# ---------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------
class SignalReason(NamedTuple):
    factor: str
    score: float
    details: Dict = {}

class State(NamedTuple):
    name: str
    timestamp: datetime
    candle_index: int
    data: Dict = {}

class TradeSignal(NamedTuple):
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    take_profits: List[float]
    confidence: float
    grade: str
    lot_size: float
    risk_amount: float
    reasons: List[SignalReason]
    diagnostics: Dict[str, Any]


# ---------------------------------------------------------------------
# MODULE REGISTRY
# ---------------------------------------------------------------------
class ModuleRegistry:
    def __init__(self):
        self.modules = {}
        self.enabled = set()

    def register(self, name, analyze_fn, dependencies=None):
        self.modules[name] = {"fn": analyze_fn, "deps": dependencies or []}

    def enable(self, name):
        self.enabled.add(name)

    def disable(self, name):
        self.enabled.discard(name)

    def is_enabled(self, name):
        return name in self.enabled

    def run(self, name, df, ctx=None):
        if not self.is_enabled(name):
            return None
        ctx = ctx or {}
        module = self.modules.get(name)
        if module is None:
            raise ValueError(f"Module '{name}' not registered.")
        for dep in module["deps"]:
            if dep not in ctx:
                ctx[dep] = self.run(dep, df, ctx)
        try:
            result = module["fn"](df, ctx) if module["deps"] else module["fn"](df)
            return result
        except Exception as e:
            logging.getLogger("OMEGA_X").error(f"Module {name} error: {e}")
            return None


# ---------------------------------------------------------------------
# SETUP MANAGER (with optional persistence)
# ---------------------------------------------------------------------
class SetupManager:
    def __init__(self, persist_path=None):
        self.memory = {}
        self.persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            with open(persist_path, 'r') as f:
                self.memory = json.load(f)

    def _key(self, symbol, timeframe):
        return f"{symbol}_{timeframe}"

    def get(self, symbol, timeframe):
        return self.memory.get(self._key(symbol, timeframe))

    def save(self, symbol, timeframe, data):
        key = self._key(symbol, timeframe)
        self.memory[key] = data
        if self.persist_path:
            with open(self.persist_path, 'w') as f:
                json.dump(self.memory, f, default=str)

    def clear(self, symbol, timeframe):
        self.memory.pop(self._key(symbol, timeframe), None)

    def clear_all(self):
        self.memory.clear()


# ---------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------
class SignalLogger:
    def __init__(self, maxlen=1000):
        self.logger = logging.getLogger("OMEGA_X")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.recent = deque(maxlen=maxlen)

    def log(self, level, message, data=None):
        msg = f"{message}"
        if data:
            msg += f" | {data}"
        level = level.upper()
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {level} | {msg}"
        self.recent.append(log_entry)
        getattr(self.logger, level.lower())(msg)

    def get_recent(self, n=100):
        return list(self.recent)[-n:]


# ---------------------------------------------------------------------
# INDICATOR CACHE & INDICATORS
# ---------------------------------------------------------------------
class IndicatorCache:
    def __init__(self):
        self.cache = {}

    def _key(self, indicator, df_hash):
        return f"{indicator}_{df_hash}"

    def get(self, indicator, df_hash):
        return self.cache.get(self._key(indicator, df_hash))

    def set(self, indicator, df_hash, value):
        self.cache[self._key(indicator, df_hash)] = value

    def clear(self):
        self.cache.clear()


class Indicators:
    def __init__(self, cache: IndicatorCache = None):
        self.cache = cache or IndicatorCache()

    def _df_hash(self, df: pd.DataFrame) -> str:
        return str(pd.util.hash_pandas_object(df).sum())

    def ema(self, df, series, period):
        key = f"ema_{series}_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        result = df[series].ewm(span=period, adjust=False).mean()
        self.cache.set(key, h, result)
        return result

    def rsi(self, df, series, period=14):
        key = f"rsi_{series}_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        delta = df[series].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
        self.cache.set(key, h, rsi)
        return rsi

    def atr(self, df, period=14):
        key = f"atr_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        result = tr.ewm(alpha=1/period, adjust=False).mean()
        self.cache.set(key, h, result)
        return result

    def macd(self, df, series, fast=12, slow=26, signal=9):
        key = f"macd_{series}_{fast}_{slow}_{signal}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        ema_fast = self.ema(df, series, fast)
        ema_slow = self.ema(df, series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        result = (macd_line, signal_line, histogram)
        self.cache.set(key, h, result)
        return result

    def adx(self, df, period=14):
        key = f"adx_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        high = df["high"]
        low = df["low"]
        close = df["close"]
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        up_move = high - high.shift()
        down_move = low.shift() - low
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        self.cache.set(key, h, adx)
        return adx

    def volume_ma(self, df, period=20):
        if "volume" not in df.columns:
            return None
        key = f"volume_ma_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        result = df["volume"].rolling(period).mean()
        self.cache.set(key, h, result)
        return result

    def vwap(self, df, period=14):
        if "volume" not in df.columns:
            return None
        key = f"vwap_{period}"
        h = self._df_hash(df)
        cached = self.cache.get(key, h)
        if cached is not None:
            return cached
        tp = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (tp * df["volume"]).rolling(period).sum() / df["volume"].rolling(period).sum()
        self.cache.set(key, h, vwap)
        return vwap

    def candle_patterns(self, df):
        high = df["high"]
        low = df["low"]
        open_ = df["open"]
        close = df["close"]
        patterns = pd.DataFrame(index=df.index)
        # Engulfing
        patterns["bullish_engulfing"] = (close > open_) & (open_ <= close.shift()) & (close >= open_.shift()) & (close > close.shift())
        patterns["bearish_engulfing"] = (close < open_) & (open_ >= close.shift()) & (close <= open_.shift()) & (close < close.shift())
        # Pin bar
        body = abs(close - open_)
        upper_wick = high - np.maximum(close, open_)
        lower_wick = np.minimum(close, open_) - low
        patterns["bullish_pin"] = (lower_wick > 2 * body) & (upper_wick < body)
        patterns["bearish_pin"] = (upper_wick > 2 * body) & (lower_wick < body)
        # Marubozu
        patterns["bullish_marubozu"] = (close > open_) & (upper_wick < 0.1 * (high-low)) & (lower_wick < 0.1 * (high-low))
        patterns["bearish_marubozu"] = (close < open_) & (upper_wick < 0.1 * (high-low)) & (lower_wick < 0.1 * (high-low))
        # Inside/Outside
        patterns["inside_bar"] = (high <= high.shift()) & (low >= low.shift())
        patterns["outside_bar"] = (high > high.shift()) & (low < low.shift())
        return patterns


# ---------------------------------------------------------------------
# ENGINE STATE
# ---------------------------------------------------------------------
class EngineState(Enum):
    WAIT_TREND = "WAIT_TREND"
    WAIT_LIQUIDITY = "WAIT_LIQUIDITY"
    WAIT_DISPLACEMENT = "WAIT_DISPLACEMENT"
    WAIT_CHOCH = "WAIT_CHOCH"
    WAIT_FVG = "WAIT_FVG"
    WAIT_ORDERBLOCK = "WAIT_ORDERBLOCK"
    WAIT_MITIGATION = "WAIT_MITIGATION"
    READY_ENTRY = "READY_ENTRY"
    EXPIRED = "EXPIRED"


# ---------------------------------------------------------------------
# MAIN SIGNAL ENGINE
# ---------------------------------------------------------------------
class SignalEngine:
    def __init__(self, config: Config = None, persist_path: str = None):
        self.config = config or Config()
        self.logger = SignalLogger()
        self.setups = SetupManager(persist_path)
        self.cache = IndicatorCache()
        self.indicators = Indicators(self.cache)
        self.registry = ModuleRegistry()
        self._register_modules()

    def _register_modules(self):
        """Register all modules with fallback to DummyModule if imports fail."""
        class DummyModule:
            @staticmethod
            def analyze(*args, **kwargs):
                return {}

        try:
            from signals.market_structure import market_structure
            from signals.choch import choch
            from signals.order_blocks import order_blocks
            from signals.fair_value_gap import fair_value_gap
            from signals.liquidity import liquidity
            from signals.displacement import displacement
            from signals.sessions import sessions
            from signals.multi_timeframe import multi_timeframe
            from signals.mitigation_blocks import mitigation_blocks
            from signals.smt_divergence import smt_divergence
            from signals.vwap import vwap_analysis
            from signals.killzones import killzones
            from signals.ote import ote_retracement
            from signals.orderflow import orderflow_analysis
        except ImportError as e:
            self.logger.log("WARNING", f"Some modules not found: {e}. Using stubs.")
            market_structure = DummyModule
            choch = DummyModule
            order_blocks = DummyModule
            fair_value_gap = DummyModule
            liquidity = DummyModule
            displacement = DummyModule
            sessions = DummyModule
            multi_timeframe = DummyModule
            mitigation_blocks = DummyModule
            smt_divergence = DummyModule
            vwap_analysis = DummyModule
            killzones = DummyModule
            ote_retracement = DummyModule
            orderflow_analysis = DummyModule

        # Register all modules (with dependencies where needed)
        self.registry.register("market_structure", lambda df: market_structure.analyze(df))
        self.registry.register("choch", lambda df, ctx: choch.analyze(ctx.get("market_structure")), dependencies=["market_structure"])
        self.registry.register("order_blocks", lambda df: order_blocks.analyze(df))
        self.registry.register("fvg", lambda df: fair_value_gap.analyze(df))
        self.registry.register("liquidity", lambda df: liquidity.analyze(df))
        self.registry.register("displacement", lambda df: displacement.analyze(df))
        self.registry.register("sessions", lambda df: sessions.analyze(df))
        self.registry.register("mtf", lambda df: multi_timeframe.analyze(df))
        self.registry.register("mitigation", lambda df: mitigation_blocks.analyze(df))
        self.registry.register("smt_divergence", lambda df: smt_divergence.analyze(df))
        self.registry.register("vwap", lambda df: vwap_analysis.analyze(df))
        self.registry.register("killzones", lambda df, ctx: killzones.analyze(df, ctx), dependencies=[])  # passes ctx
        self.registry.register("ote", lambda df: ote_retracement.analyze(df))
        self.registry.register("orderflow", lambda df: orderflow_analysis.analyze(df))

        # Enable modules from config
        for mod in self.config.get("enabled_modules", []):
            self.registry.enable(mod)

    # ---------- Helper Methods ----------
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
            df["vwap"] = self.indicators.vwap(df, self.config.VWAP_PERIOD)
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

    def _calculate_position_size(self, price, sl, symbol, confidence, **kwargs):
        meta = self._get_symbol_metadata(symbol)
        if self.config.DYNAMIC_RISK_ENABLED:
            conf_norm = (confidence - 60) / 35
            risk_pct = self.config.DYNAMIC_RISK_MIN + conf_norm * (self.config.DYNAMIC_RISK_MAX - self.config.DYNAMIC_RISK_MIN)
        else:
            risk_pct = self.config.RISK_PER_TRADE
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

    # ---------- Confidence Scoring ----------
    def _score_factors(self, df, ctx, direction):
        reasons = []
        price = df["close"].iloc[-1]
        atr = df["atr"].iloc[-1]

        # --- Trend ---
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
        reasons.append(SignalReason("Trend Strength", trend_score))

        # --- Liquidity ---
        liquidity_data = ctx.get("liquidity", {})
        if direction == "BUY":
            has_liquidity = liquidity_data.get("buy_liquidity", False)
            level = liquidity_data.get("liquidity_high")
        else:
            has_liquidity = liquidity_data.get("sell_liquidity", False)
            level = liquidity_data.get("liquidity_low")
        if has_liquidity:
            if level is not None:
                dist = abs(price - level) / atr
                liq_score = 1.0 - min(dist, 1.0)
            else:
                liq_score = 0.7
        else:
            liq_score = 0.0
        reasons.append(SignalReason("Liquidity Sweep", liq_score))

        # --- Displacement ---
        displacement_data = ctx.get("displacement", {})
        if direction == "BUY" and displacement_data.get("bullish_displacement", False):
            disp_score = 1.0
        elif direction == "SELL" and displacement_data.get("bearish_displacement", False):
            disp_score = 1.0
        else:
            disp_score = 0.0
        reasons.append(SignalReason("Displacement", disp_score))

        # --- CHOCH ---
        choch_data = ctx.get("choch", {})
        if direction == "BUY" and choch_data.get("bullish_choch", False):
            choch_score = 1.0
        elif direction == "SELL" and choch_data.get("bearish_choch", False):
            choch_score = 1.0
        else:
            choch_score = 0.0
        reasons.append(SignalReason("CHOCH", choch_score))

        # --- FVG ---
        fvg_data = ctx.get("fvg", {})
        if direction == "BUY" and fvg_data.get("bullish_fvg", False):
            fvg_score = 1.0
        elif direction == "SELL" and fvg_data.get("bearish_fvg", False):
            fvg_score = 1.0
        else:
            fvg_score = 0.0
        reasons.append(SignalReason("FVG", fvg_score))

        # --- Order Block ---
        ob_data = ctx.get("order_blocks", {})
        if direction == "BUY" and ob_data.get("bullish_ob", False):
            ob_score = 1.0
        elif direction == "SELL" and ob_data.get("bearish_ob", False):
            ob_score = 1.0
        else:
            ob_score = 0.0
        reasons.append(SignalReason("Order Block", ob_score))

        # --- Mitigation ---
        mitigation_data = ctx.get("mitigation", {})
        if direction == "BUY" and mitigation_data.get("bullish_mitigation", False):
            mit_score = 1.0
        elif direction == "SELL" and mitigation_data.get("bearish_mitigation", False):
            mit_score = 1.0
        else:
            mit_score = 0.0
        reasons.append(SignalReason("Mitigation", mit_score))

        # --- HTF ---
        mtf = ctx.get("mtf", {})
        if direction == "BUY" and mtf.get("bullish_alignment", False):
            htf_score = 1.0
        elif direction == "SELL" and mtf.get("bearish_alignment", False):
            htf_score = 1.0
        else:
            htf_score = 0.3
        reasons.append(SignalReason("HTF Alignment", htf_score))

        # --- Sessions / Killzones ---
        session_data = ctx.get("sessions", {})
        killzone_data = ctx.get("killzones", {})
        active = session_data.get("active_session")
        if active in ["london", "new_york"]:
            sess_score = 1.0
        elif active == "asia":
            sess_score = 0.6
        else:
            sess_score = 0.3
        if killzone_data.get("in_killzone", False):
            sess_score = min(1.0, sess_score + 0.2)
        reasons.append(SignalReason("Session Quality", sess_score))

        # --- Volume Spike ---
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
        reasons.append(SignalReason("Volume Spike", vol_score))

        # --- Candle Patterns ---
        patterns = df["candle_patterns"].iloc[-1]
        pattern_score = 0.0
        if direction == "BUY":
            if patterns["bullish_engulfing"]:
                pattern_score = 1.0
            elif patterns["bullish_pin"]:
                pattern_score = 0.8
            elif patterns["bullish_marubozu"]:
                pattern_score = 0.7
            elif patterns["inside_bar"] and patterns["outside_bar"]:
                pattern_score = 0.5
        else:
            if patterns["bearish_engulfing"]:
                pattern_score = 1.0
            elif patterns["bearish_pin"]:
                pattern_score = 0.8
            elif patterns["bearish_marubozu"]:
                pattern_score = 0.7
        reasons.append(SignalReason("Candle Pattern", pattern_score))

        # --- VWAP ---
        if "vwap" in df.columns:
            vwap = df["vwap"].iloc[-1]
            if direction == "BUY" and price < vwap:
                vwap_score = 1.0 - min((vwap - price) / atr, 1.0)
            elif direction == "SELL" and price > vwap:
                vwap_score = 1.0 - min((price - vwap) / atr, 1.0)
            else:
                vwap_score = 0.3
            reasons.append(SignalReason("VWAP", vwap_score))

        # --- OTE ---
        ote_data = ctx.get("ote", {})
        if ote_data.get("in_ote", False):
            ote_score = 1.0
        else:
            ote_score = 0.0
        reasons.append(SignalReason("OTE", ote_score))

        # --- SMT Divergence ---
        smt_data = ctx.get("smt_divergence", {})
        if direction == "BUY" and smt_data.get("bullish_divergence", False):
            smt_score = 1.0
        elif direction == "SELL" and smt_data.get("bearish_divergence", False):
            smt_score = 1.0
        else:
            smt_score = 0.0
        reasons.append(SignalReason("SMT Divergence", smt_score))

        return reasons

    def _compute_confidence(self, reasons):
        total_weight = 0
        weighted_sum = 0
        for r in reasons:
            weight = 1.0
            total_weight += weight
            weighted_sum += r.score * weight
        raw = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0
        return min(raw, self.config.CONFIDENCE_CEILING)

    def _get_grade(self, confidence):
        grade = "D"
        for threshold, g in self.config.GRADE_THRESHOLDS.items():
            if confidence >= threshold:
                grade = g
                break
        return grade

    # ---------- Entry Logic ----------
    def _build_signal(self, df, ctx, symbol, timeframe, direction, current_time):
        price = df["close"].iloc[-1]
        atr = df["atr"].iloc[-1]
        structure = ctx.get("market_structure", {})
        swing_high = structure.get("swing_high")
        swing_low = structure.get("swing_low")

        # Spread check
        if "spread" in df.columns:
            spread = df["spread"].iloc[-1]
            if spread > atr * self.config.MAX_SPREAD_ATR_RATIO:
                self.logger.log("WARNING", f"Spread too high: {spread}")
                return None

        # Stop Loss
        if direction == "BUY":
            sl = swing_low * 0.999 if swing_low is not None else price - atr
            if sl >= price:
                sl = price - atr
        else:
            sl = swing_high * 1.001 if swing_high is not None else price + atr
            if sl <= price:
                sl = price + atr

        risk = abs(price - sl)
        if risk < atr * self.config.MIN_STOP_ATR_RATIO:
            return None

        # Entry with buffer – limit order offset
        buffer_factor = self.config.EXECUTION_BUFFER
        if direction == "BUY":
            entry = price - risk * buffer_factor
            entry = max(entry, price - risk * 0.5)
        else:
            entry = price + risk * buffer_factor
            entry = min(entry, price + risk * 0.5)

        # Take Profits
        if direction == "BUY":
            tp1, tp2, tp3 = entry + risk, entry + risk*2, entry + risk*3
        else:
            tp1, tp2, tp3 = entry - risk, entry - risk*2, entry - risk*3

        # Score factors
        reasons = self._score_factors(df, ctx, direction)
        confidence = self._compute_confidence(reasons)
        if confidence < self.config.CONFIDENCE_THRESHOLD:
            self.logger.log("INFO", f"Confidence {confidence:.1f} below threshold")
            return None

        grade = self._get_grade(confidence)
        lot_size, risk_currency = self._calculate_position_size(entry, sl, symbol, confidence)
        if lot_size <= 0:
            return None

        signal = TradeSignal(
            symbol=symbol,
            direction=direction,
            entry=round(entry, 5),
            stop_loss=round(sl, 5),
            take_profits=[round(tp1,5), round(tp2,5), round(tp3,5)],
            confidence=confidence,
            grade=grade,
            lot_size=lot_size,
            risk_amount=risk_currency,
            reasons=reasons,
            diagnostics={
                "regime": self._detect_regime(df),
                "atr": round(atr, 5),
                "risk": round(risk, 5),
                "spread": round(spread, 5) if "spread" in df.columns else None,
                "session": ctx.get("sessions", {}).get("active_session"),
                "killzone": ctx.get("killzones", {}).get("in_killzone", False),
                "vwap": round(df["vwap"].iloc[-1], 5) if "vwap" in df.columns else None,
                "ote": ctx.get("ote", {}).get("in_ote", False),
                "smt_divergence": ctx.get("smt_divergence", {}),
                "candle_pattern": df["candle_patterns"].iloc[-1].to_dict() if "candle_patterns" in df else {},
            }
        )

        self.logger.log("INFO", f"Signal {direction} | Conf {confidence:.1f} | Grade {grade}")
        return signal

    # ---------- Main Entry Point ----------
    def generate_signal(self, df, symbol="EURUSD", timeframe="1H", last_trade_time=None, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        elif isinstance(current_time, pd.Timestamp):
            current_time = current_time.to_pydatetime()

        # Check cooldown
        if last_trade_time:
            candle_duration = (df.index[-1] - df.index[-2])
            if current_time - last_trade_time < candle_duration * self.config.MIN_CANDLES_BETWEEN_TRADES:
                return None

        # Prepare data
        df = self._prepare_data(df)

        # Run modules
        ctx = {}
        for mod in self.config.get("enabled_modules", []):
            try:
                # For killzones, we need to pass ctx (which contains config)
                if mod == "killzones":
                    result = self.registry.run(mod, df, {'config': self.config, **ctx})
                else:
                    result = self.registry.run(mod, df, ctx)
                if result is not None:
                    ctx[mod] = result
            except Exception as e:
                self.logger.log("ERROR", f"Module {mod} error: {e}")

        # Determine direction
        direction = None
        ema20, ema50, ema200 = df["ema20"].iloc[-1], df["ema50"].iloc[-1], df["ema200"].iloc[-1]
        if ema20 > ema50 > ema200:
            direction = "BUY"
        elif ema20 < ema50 < ema200:
            direction = "SELL"
        else:
            mtf = ctx.get("mtf", {})
            if mtf.get("bullish_alignment", False):
                direction = "BUY"
            elif mtf.get("bearish_alignment", False):
                direction = "SELL"
        if direction is None:
            self.logger.log("INFO", "No clear trend")
            return None

        # Build signal
        signal = self._build_signal(df, ctx, symbol, timeframe, direction, current_time)
        if signal is None:
            return None

        # Return as dict (for easy integration with Streamlit)
        return {
            "signal": signal.direction,
            "confidence": signal.confidence,
            "entry": signal.entry,
            "sl": signal.stop_loss,
            "tp1": signal.take_profits[0],
            "tp2": signal.take_profits[1],
            "tp3": signal.take_profits[2],
            "grade": signal.grade,
            "lot": signal.lot_size,
            "diagnostics": signal.diagnostics,
            "reasons": [r.factor for r in signal.reasons if r.score > 0.5]
        }


# ---------------------------------------------------------------------
# GLOBAL ENGINE INSTANCE (ready for import)
# ---------------------------------------------------------------------
engine = SignalEngine()

# ---------------------------------------------------------------------
# OPTIONAL: Streamlit helper – demonstrates how to use the engine
# ---------------------------------------------------------------------
def demo_with_sample_data():
    """
    Creates a small sample DataFrame and runs the engine.
    Useful for testing in Streamlit.
    """
    # Generate 100 bars of synthetic data
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
    price = 1.1000 + np.cumsum(np.random.randn(100) * 0.001)
    high = price + np.abs(np.random.randn(100) * 0.0005)
    low = price - np.abs(np.random.randn(100) * 0.0005)
    open_ = price - np.random.randn(100) * 0.0002
    close = price + np.random.randn(100) * 0.0002
    volume = np.random.randint(100, 1000, 100)

    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'spread': 0.0001 + np.random.rand(100) * 0.0002
    }, index=dates)

    signal = engine.generate_signal(df)
    if signal:
        print("Signal generated:")
        for key, val in signal.items():
            print(f"  {key}: {val}")
    else:
        print("No signal.")

if __name__ == "__main__":
    demo_with_sample_data()
