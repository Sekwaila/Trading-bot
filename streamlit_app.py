import sys
import os
import math
import datetime
import logging
from typing import Dict, Tuple, Optional, List

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import streamlit as st

# Configure page setup at entry
st.set_page_config(
    page_title="SEKWAILA OMEGA X Pro Engine",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Setup Logger
logger = logging.getLogger("SEKWAILA_OMEGA_X")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ==========================================
# 1. CONFIGURATION & ENGINE SETTINGS
# ==========================================
class EngineConfig:
    SYMBOL: str = "GC=F"  # Gold Futures Proxy
    DISPLAY_SYMBOL: str = "XAUUSD"
    CONFLUENCE_THRESHOLD: float = 60.0
    RISK_PERCENT_DEFAULT: float = 1.0
    ACCOUNT_BALANCE_ZAR_DEFAULT: float = 10000.0
    CONTRACT_SIZE_OZ: float = 100.0  # 1 standard lot = 100oz

    TIMEFRAMES: dict = {
        "1D": ("180d", "1d"),
        "4H": ("60d", "1h"),
        "1H": ("30d", "1h"),
        "15M": ("7d", "15m"),
    }

    NEWS_BLACKOUT_WINDOWS_UTC: List[Tuple[datetime.time, datetime.time]] = [
        (datetime.time(12, 20), datetime.time(12, 40)),
        (datetime.time(18, 0), datetime.time(18, 15)),
    ]

config = EngineConfig()


# ==========================================
# 2. DATA LAYER
# ==========================================
def compute_true_range(df_closed: pd.DataFrame) -> pd.Series:
    high, low, close = df_closed["High"], df_closed["Low"], df_closed["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def fetch_institutional_data(symbol: str = config.SYMBOL) -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, str]]:
    tf_data = {}
    data_integrity = {}

    for tf_label, (period, interval) in config.TIMEFRAMES.items():
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty or len(df) < 30:
                raise ValueError(f"Insufficient candles ({len(df)})")

            if tf_label == "4H":
                df = df.resample("4h").agg({
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum"
                }).dropna()

            tf_data[tf_label] = df
            data_integrity[tf_label] = "LIVE"
        except Exception as e:
            logger.warning(f"Failed fetching timeframe {tf_label}: {e}")
            tf_data[tf_label] = None
            data_integrity[tf_label] = f"UNAVAILABLE ({e})"

    return tf_data, data_integrity

def fetch_usdzar_rate() -> Optional[float]:
    try:
        df = yf.download("ZAR=X", period="5d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching USDZAR rate: {e}")
        return None

def compute_live_correlation_matrix() -> Optional[pd.DataFrame]:
    symbols = {
        "XAUUSD": "GC=F",
        "DXY": "DX-Y.NYB",
        "BTCUSD": "BTC-USD",
        "US30": "^DJI",
    }
    df_closes = pd.DataFrame()
    for name, ticker in symbols.items():
        try:
            d = yf.download(ticker, period="10d", interval="1h", progress=False)
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
            df_closes[name] = d["Close"]
        except Exception:
            pass

    if df_closes.shape[1] < 2:
        return None
    return df_closes.corr().round(2)


# ==========================================
# 3. SMC QUANTITATIVE ENGINE
# ==========================================
def find_swing_points(df_closed: pd.DataFrame, window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    n = len(df_closed)
    win = 2 * window + 1
    if n < win:
        return np.array([], dtype=int), np.array([], dtype=int)

    highs, lows = df_closed["High"], df_closed["Low"]
    roll_max = highs.rolling(win, center=True).max()
    roll_min = lows.rolling(win, center=True).min()

    is_sh = (highs == roll_max) & roll_max.notna()
    is_sl = (lows == roll_min) & roll_min.notna()

    return np.where(is_sh.values)[0], np.where(is_sl.values)[0]

def analyze_market_structure(df: pd.DataFrame) -> Tuple[str, str, Optional[float], Optional[float]]:
    df_c = df.iloc[:-1].copy()
    sh_idx, sl_idx = find_swing_points(df_c)

    if len(sh_idx) < 2 or len(sl_idx) < 2:
        return "NEUTRAL", "NONE", None, None

    last_sh, prev_sh = float(df_c["High"].iloc[sh_idx[-1]]), float(df_c["High"].iloc[sh_idx[-2]])
    last_sl, prev_sl = float(df_c["Low"].iloc[sl_idx[-1]]), float(df_c["Low"].iloc[sl_idx[-2]])
    close_val = df_c["Close"].iloc[-1]

    prior_bullish = last_sh > prev_sh and last_sl > prev_sl
    prior_bearish = last_sh < prev_sh and last_sl < prev_sl

    structure_type, bias, DISPLACEMENT_MIN = "NONE", "NEUTRAL", 0.0008

    if close_val > last_sh:
        displacement = (close_val - last_sh) / last_sh
        base = "BULLISH_CHoCH" if prior_bearish else "BULLISH_BOS"
        structure_type = base if displacement >= DISPLACEMENT_MIN else base + "_WEAK"
        bias = "BUY"
    elif close_val < last_sl:
        displacement = (last_sl - close_val) / last_sl
        base = "BEARISH_CHoCH" if prior_bullish else "BEARISH_BOS"
        structure_type = base if displacement >= DISPLACEMENT_MIN else base + "_WEAK"
        bias = "SELL"

    return bias, structure_type, last_sh, last_sl

def check_displacement(df_closed: pd.DataFrame, index: int, direction: str, threshold: float = 0.0025) -> bool:
    if index + 3 >= len(df_closed):
        return False
    c_high, c_low = df_closed["High"].iloc[index], df_closed["Low"].iloc[index]
    if direction == "BULLISH":
        subsequent_high = df_closed["High"].iloc[index + 1 : index + 4].max()
        return ((subsequent_high - c_high) / c_high) >= threshold
    elif direction == "BEARISH":
        subsequent_low = df_closed["Low"].iloc[index + 1 : index + 4].min()
        return ((c_low - subsequent_low) / c_low) >= threshold
    return False

def detect_validated_order_block(df: pd.DataFrame, struct_bias: str) -> Tuple[str, Tuple[float, float], bool, bool]:
    df_c = df.iloc[:-1].copy()
    n = len(df_c)

    ob_zone = None
    ob_type = "NEUTRAL_DEMAND"
    is_mitigated, is_invalidated = False, False

    for i in range(n - 4, 10, -1):
        c_open, c_close = df_c["Open"].iloc[i], df_c["Close"].iloc[i]
        c_high, c_low = df_c["High"].iloc[i], df_c["Low"].iloc[i]

        if struct_bias == "BUY" and c_close < c_open:
            if check_displacement(df_c, i, "BULLISH", threshold=0.0025):
                ob_zone = (c_low, c_high)
                ob_type = "BULLISH_OB"
                after = df_c.iloc[i + 4 :]
                if len(after) > 0:
                    if after["Low"].min() <= c_high: is_mitigated = True
                    if after["Close"].min() < c_low: is_invalidated = True
                break

        elif struct_bias == "SELL" and c_close > c_open:
            if check_displacement(df_c, i, "BEARISH", threshold=0.0025):
                ob_zone = (c_low, c_high)
                ob_type = "BEARISH_OB"
                after = df_c.iloc[i + 4 :]
                if len(after) > 0:
                    if after["High"].max() >= c_low: is_mitigated = True
                    if after["Close"].max() > c_high: is_invalidated = True
                break

    if not ob_zone:
        low_val = float(df_c["Low"].iloc[-10:].min())
        ob_zone = (low_val, low_val * 1.001)

    return ob_type, ob_zone, is_mitigated, is_invalidated

def detect_fair_value_gaps(df: pd.DataFrame, lookback: int = 40) -> Optional[Dict]:
    df_c = df.iloc[:-1].copy()
    n = len(df_c)
    start = max(2, n - lookback)
    gaps = []

    for i in range(start, n - 1):
        c_prev_high, c_prev_low = df_c["High"].iloc[i - 1], df_c["Low"].iloc[i - 1]
        c_next_high, c_next_low = df_c["High"].iloc[i + 1], df_c["Low"].iloc[i + 1]

        if c_next_low > c_prev_high:
            zone, gap_type = (c_prev_high, c_next_low), "BULLISH_FVG"
        elif c_next_high < c_prev_low:
            zone, gap_type = (c_next_high, c_prev_low), "BEARISH_FVG"
        else:
            continue

        future = df_c.iloc[i + 2 :]
        filled = bool(((future["Low"] <= zone[1]) & (future["High"] >= zone[0])).any()) if len(future) > 0 else False
        gaps.append({"type": gap_type, "zone": zone, "filled": filled})

    unfilled = [g for g in gaps if not g["filled"]]
    return unfilled[-1] if unfilled else None

def detect_equal_liquidity_levels(df_closed: pd.DataFrame, lookback: int = 50, tolerance_pct: float = 0.0006) -> Tuple[List[float], List[float]]:
    recent = df_closed.tail(lookback)
    def cluster(values: np.ndarray) -> List[float]:
        vals = np.sort(values)
        if len(vals) == 0: return []
        clusters, current = [], [vals[0]]
        for v in vals[1:]:
            if abs(v - current[-1]) / current[-1] <= tolerance_pct:
                current.append(v)
            else:
                if len(current) >= 2: clusters.append(float(np.mean(current)))
                current = [v]
        if len(current) >= 2: clusters.append(float(np.mean(current)))
        return clusters

    return cluster(recent["High"].values), cluster(recent["Low"].values)

def evaluate_liquidity_sweeps(df_closed: pd.DataFrame, eq_highs: List[float], eq_lows: List[float]) -> Tuple[bool, str]:
    recent_low, recent_high = df_closed["Low"].iloc[-15:-2].min(), df_closed["High"].iloc[-15:-2].max()
    curr_low, curr_high, curr_close = df_closed["Low"].iloc[-1], df_closed["High"].iloc[-1], df_closed["Close"].iloc[-1]

    if curr_low < recent_low and curr_close > recent_low:
        return True, f"SELL-SIDE SWEEP BELOW {recent_low:.2f}"
    elif curr_high > recent_high and curr_close < recent_high:
        return True, f"BUY-SIDE SWEEP ABOVE {recent_high:.2f}"

    pool_tolerance = curr_close * 0.0006
    for eqh in eq_highs:
        if curr_high > eqh + pool_tolerance * 0.2 and curr_close < eqh:
            return True, f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {eqh:.2f}"
    for eql in eq_lows:
        if curr_low < eql - pool_tolerance * 0.2 and curr_close > eql:
            return True, f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {eql:.2f}"

    return False, "NO_SWEEP"

def compute_market_regime(df: pd.DataFrame) -> dict:
    df_c = df.iloc[:-1].copy()
    high, low = df_c["High"], df_c["Low"]
    up_move, down_move = high.diff(), -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = compute_true_range(df_c)
    eps = 1e-9

    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df_c.index).ewm(alpha=1/14, adjust=False, min_periods=14).mean() / (atr + eps))
    minus_di = 100 * (pd.Series(minus_dm, index=df_c.index).ewm(alpha=1/14, adjust=False, min_periods=14).mean() / (atr + eps))

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = (plus_di - minus_di).abs() / di_sum * 100
    adx_val = float(np.nan_to_num(dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean().iloc[-1], nan=20.0))

    atr_fast = tr.rolling(7).mean().iloc[-1]
    atr_slow = tr.rolling(28).mean().iloc[-1]
    vol_ratio = atr_fast / atr_slow if atr_slow > 0 else 1.0

    y = df_c["Close"].tail(20).values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    angle = math.degrees(math.atan(slope))

    if adx_val > 25 and vol_ratio > 1.1: regime = "TRENDING_EXPANSION"
    elif adx_val < 20 and vol_ratio < 0.85: regime = "ACCUMULATION_DISTRIBUTION"
    elif vol_ratio > 1.4: regime = "HIGH_VOLATILITY_RANGE"
    else: regime = "CHOP_LOW_VOLATILITY"

    return {"regime": regime, "adx": round(adx_val, 2), "vol_ratio": round(vol_ratio, 2), "angle": round(angle, 2)}

def evaluate_mtf_bias(tf_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    biases = {}
    for tf, df in tf_data.items():
        if df is not None:
            bias, _, _, _ = analyze_market_structure(df)
            biases[tf] = bias
        else:
            biases[tf] = "NEUTRAL"
    return biases

def calculate_confluence_score(tf_biases: dict, structure_type: str, ob_type: str, is_mitigated: bool, is_invalidated: bool, regime: str, sweep_detected: bool, fvg_present: bool) -> float:
    z = -1.2
    bull_cnt = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_cnt = sum(1 for v in tf_biases.values() if v == "SELL")
    z += max(bull_cnt, bear_cnt) * 0.45

    if "CHoCH" in structure_type: z += 0.65
    elif "BOS" in structure_type: z += 0.40

    if ob_type in ["BULLISH_OB", "BEARISH_OB"]:
        if is_invalidated: z -= 0.60
        elif is_mitigated: z -= 0.30
        else: z += 0.55

    if sweep_detected: z += 0.70
    if fvg_present: z += 0.25
    if regime == "TRENDING_EXPANSION": z += 0.50
    elif regime == "CHOP_LOW_VOLATILITY": z -= 0.80

    return round((1.0 / (1.0 + math.exp(-z))) * 100, 1)

def run_quantitative_smc_engine(tf_data: dict, data_integrity: dict) -> dict:
    missing = [tf for tf, df in tf_data.items() if df is None]
    if missing:
        return {"data_ok": False, "missing_timeframes": missing, "data_integrity": data_integrity}

    df_15m = tf_data["15M"]
    regime_info = compute_market_regime(df_15m)
    tf_biases = evaluate_mtf_bias(tf_data)

    struct_bias, struct_type, last_sh, last_sl = analyze_market_structure(df_15m)
    ob_type, ob_zone, is_mitigated, is_invalidated = detect_validated_order_block(df_15m, struct_bias)
    fvg = detect_fair_value_gaps(df_15m)
    eq_highs, eq_lows = detect_equal_liquidity_levels(df_15m.iloc[:-1])
    sweep_detected, sweep_detail = evaluate_liquidity_sweeps(df_15m.iloc[:-1], eq_highs, eq_lows)

    confluence_score = calculate_confluence_score(
        tf_biases, struct_type, ob_type, is_mitigated, is_invalidated,
        regime_info["regime"], sweep_detected, fvg is not None
    )

    bull_score = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_score = sum(1 for v in tf_biases.values() if v == "SELL")

    if bull_score >= 3 and confluence_score >= config.CONFLUENCE_THRESHOLD: overall_bias = "BUY"
    elif bear_score >= 3 and confluence_score >= config.CONFLUENCE_THRESHOLD: overall_bias = "SELL"
    else: overall_bias = "NEUTRAL"

    # Execution Barriers
    passed_filters, filter_rejections = True, []
    if regime_info["regime"] == "CHOP_LOW_VOLATILITY":
        passed_filters = False
        filter_rejections.append("REJECTED: Market in Low-Volatility Chop")

    df_c = df_15m.iloc[:-1]
    tr = compute_true_range(df_c)
    atr_val = float(tr.rolling(14).mean().iloc[-1])
    entry_price = float(df_15m["Close"].iloc[-1])

    if overall_bias == "BUY":
        stop_loss = min(ob_zone[0] - (atr_val * 0.15), entry_price - atr_val)
        tp1, tp2 = entry_price + (atr_val * 1.5), entry_price + (atr_val * 3.0)
    elif overall_bias == "SELL":
        stop_loss = max(ob_zone[1] + (atr_val * 0.15), entry_price + atr_val)
        tp1, tp2 = entry_price - (atr_val * 1.5), entry_price - (atr_val * 3.0)
    else:
        stop_loss, tp1, tp2 = entry_price - atr_val, entry_price + atr_val, entry_price + (atr_val * 2.0)

    fvg_text = "none unfilled" if fvg is None else f"{fvg['type']} at {fvg['zone'][0]:.2f}-{fvg['zone'][1]:.2f}"
    ob_state = "INVALIDATED" if is_invalidated else ("MITIGATED" if is_mitigated else "UNMITIGATED")

    ai_narrative = (
        f"Macro direction is {overall_bias}. Market Regime: {regime_info['regime']} (ADX: {regime_info['adx']}). "
        f"Structure: {struct_type} on 15M. Liquidity state: {sweep_detail}. "
        f"Testing {ob_state} {ob_type} ({ob_zone[0]:.2f}-{ob_zone[1]:.2f}). Nearest Gap: {fvg_text}."
    )

    return {
        "data_ok": True,
        "symbol": config.DISPLAY_SYMBOL,
        "bias": overall_bias,
        "probability": confluence_score,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "tp1": tp1,
        "tp2": tp2,
        "regime": regime_info,
        "passed_filters": passed_filters,
        "filter_rejections": filter_rejections,
        "ai_narrative": ai_narrative,
        "df_15m": df_15m,
    }

def calculate_position_size(account_balance_usd: Optional[float], risk_pct: float, entry_price: float, stop_loss_price: float) -> Optional[Dict]:
    if not account_balance_usd or account_balance_usd <= 0: return None
    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance <= 0: return None

    risk_amount_usd = account_balance_usd * (risk_pct / 100.0)
    lots = risk_amount_usd / (stop_distance * config.CONTRACT_SIZE_OZ)

    return {"risk_usd": round(risk_amount_usd, 2), "lots": round(lots, 3)}


# ==========================================
# 4. STREAMLIT UI DASHBOARD
# ==========================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');
    .stApp { background-color: #0c0a07; color: #e5d5b7; font-family: 'Inter', sans-serif; }
    .title-cinzel { font-family: 'Cinzel', serif; color: #dfb15b; letter-spacing: 2px; }
    .css-card { background-color: #14100b; border: 1px solid #3b2d18; border-radius: 8px; padding: 14px; margin-bottom: 12px; }
    .signal-box-buy { background: linear-gradient(180deg, #0d1a0e 0%, #060d07 100%); border: 1px solid #00e676; border-radius: 10px; padding: 20px; }
    .signal-box-sell { background: linear-gradient(180deg, #1f0b0b 0%, #0a0404 100%); border: 1px solid #ff5252; border-radius: 10px; padding: 20px; }
    .signal-box-blocked { background: linear-gradient(180deg, #211c12 0%, #0c0a07 100%); border: 1px solid #ffb74d; border-radius: 10px; padding: 20px; }
    .text-gold { color: #dfb15b !important; }
    .text-green { color: #00e676 !important; font-weight: bold; }
    .text-red { color: #ff5252 !important; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

tf_data, data_integrity = fetch_institutional_data(config.SYMBOL)
results = run_quantitative_smc_engine(tf_data, data_integrity)
corr_matrix = compute_live_correlation_matrix()

with st.sidebar:
    st.markdown("### 💰 Position Sizing")
    account_balance_zar = st.number_input("Account Balance (ZAR)", min_value=0.0, value=config.ACCOUNT_BALANCE_ZAR_DEFAULT, step=500.0)
    risk_pct_input = st.number_input("Risk per Trade (%)", min_value=0.1, max_value=10.0, value=config.RISK_PERCENT_DEFAULT, step=0.1)

usdzar_rate = fetch_usdzar_rate()
account_balance_usd = (account_balance_zar / usdzar_rate) if usdzar_rate else None

head_c1, head_c2, head_c3 = st.columns([1.2, 2.5, 1.2])
with head_c1:
    st.markdown("<h3 class='title-cinzel' style='margin:0;'>👑 SEKWAILA OMEGA X</h3>", unsafe_allow_html=True)
with head_c2:
    st.markdown("<h2 style='text-align: center; margin:0;' class='title-cinzel'>SEKWAILA OMEGA X — QUANT ENGINE</h2>", unsafe_allow_html=True)
with head_c3:
    now_sast = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).strftime("%H:%M:%S")
    st.markdown(f"<div style='text-align: right;'><b class='text-gold'>{now_sast} SAST</b></div>", unsafe_allow_html=True)

st.markdown("---")

if not results["data_ok"]:
    st.error(f"Data Feed Error: {results['missing_timeframes']}")
    st.stop()

col_left, col_center, col_right = st.columns([1.1, 2.4, 1.2])

with col_left:
    st.markdown(f'<div class="css-card"><small class="text-gold">📈 MARKET REGIME</small><h4 style="color: #00e676; margin: 4px 0;">{results["regime"]["regime"]}</h4><div style="font-size:11px; color:#aaa;">ADX: <b>{results["regime"]["adx"]}</b> | Vol Ratio: <b>{results["regime"]["vol_ratio"]}</b></div></div>', unsafe_allow_html=True)
    
    filter_status = "APPROVED" if results["passed_filters"] else "BLOCKED"
    filter_color = "text-green" if results["passed_filters"] else "text-red"
    st.markdown(f'<div class="css-card"><small class="text-gold">🛡️ SAFETY BARRIER</small><br/><span class="{filter_color}">{filter_status}</span></div>', unsafe_allow_html=True)
    
    pos_size = calculate_position_size(account_balance_usd, risk_pct_input, results["entry"], results["stop_loss"]) if results["bias"] in ("BUY", "SELL") else None
    if pos_size:
        st.markdown(f'<div class="css-card"><small class="text-gold">💰 POSITION SIZE</small><div style="font-size:11px; margin-top:6px;">Size: <b class="text-green">{pos_size["lots"]} lots</b><br/>Risk: <b>${pos_size["risk_usd"]}</b></div></div>', unsafe_allow_html=True)

with col_center:
    box_class = "signal-box-buy" if results["bias"] == "BUY" and results["passed_filters"] else ("signal-box-sell" if results["bias"] == "SELL" and results["passed_filters"] else "signal-box-blocked")
    st.markdown(f'<div class="{box_class}"><div style="display: flex; justify-content: space-between;"><h2 style="margin:0;" class="title-cinzel">{config.DISPLAY_SYMBOL}</h2><h2 style="margin:0;" class="text-gold">{results["probability"]}%</h2></div><h1 class="text-gold" style="margin: 2px 0;">{results["bias"]}</h1><div style="display: flex; justify-content: space-around; text-align: center;"><div><small>ENTRY</small><br/><b>{results["entry"]:.2f}</b></div><div><small>TP1</small><br/><b class="text-green">{results["tp1"]:.2f}</b></div><div><small>STOP</small><br/><b class="text-red">{results["stop_loss"]:.2f}</b></div></div></div>', unsafe_allow_html=True)

    df_chart = results["df_15m"]
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart["Open"], high=df_chart["High"], low=df_chart["Low"], close=df_chart["Close"], increasing_line_color="#00e676", decreasing_line_color="#ff5252")])
    fig.update_layout(template="plotly_dark", paper_bgcolor="#14100b", plot_bgcolor="#14100b", height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown(f'<div class="css-card"><small class="text-gold">💡 KATLEGO AI REASONING</small><p style="font-size: 11px; color: #ccc; margin-top: 6px;">{results["ai_narrative"]}</p></div>', unsafe_allow_html=True)
    if corr_matrix is not None:
        st.dataframe(corr_matrix.style.background_gradient(cmap="coolwarm", axis=None), use_container_width=True)
