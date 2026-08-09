"""
SEKWAILA OMEGA X — CORE ENGINE

Single source of truth for every SMC calculation. streamlit_app.py and
worker.py both import generate_omega_signal() from here — the dashboard
and your phone alerts can never disagree, because they call the same code.

This replaces the old signals/ folder. Function names below intentionally
match what your old signal_engine.py / breaker_blocks.py / choch.py already
expected (find_order_block, analyze_market_structure, get_session_info,
etc.) so nothing that referenced those names has to change its calling
convention — only the logic underneath is new.

FIXES vs the previous signal_engine.py:
- ATR was computed as a 1-term range (High-Low only). Real True Range needs
  three terms (High-Low, |High-PrevClose|, |Low-PrevClose|) — the version
  here was missing both PrevClose terms, which understated every stop and
  take-profit distance in the whole engine.
- Stop-loss was a flat 1.5x ATR multiple. This version anchors the stop
  beyond the order block / swing point that would actually invalidate the
  setup, using ATR only as a minimum-distance floor.
- config.DEFAULT_MIN_RR was declared but never enforced anywhere — a setup
  could score well and still ship with a sub-1.5 R:R. Now enforced: a
  signal below the minimum R:R is forced to NEUTRAL with a stated reason.
- find_order_block returned a `mit` (mitigated) flag that scoring silently
  ignored (only `inv`/invalidated was checked). Mitigated-but-valid blocks
  now score lower than clean unmitigated ones, instead of scoring the same.
- equal_highs_lows.py and displacement.py existed as separate modules but
  were never imported into signal_engine.py. Their logic is now wired into
  the liquidity sweep and structure-confirmation checks below.
"""
import datetime
import math
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from zoneinfo import ZoneInfo
    _TZ_OK = True
except Exception:
    _TZ_OK = False

from config import ASSETS, TF_CONFIG, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR
from logger import get_logger

logger = get_logger("ENGINE")


# ------------------------------------------------------------------------------
# ADDITIONAL INDICATORS (RSI, MACD, VWAP) — for the Khansaab-style panel
# ------------------------------------------------------------------------------
def compute_rsi(df_closed: pd.DataFrame, period: int = 14) -> float:
    delta = df_closed["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def compute_macd_trend(df_closed: pd.DataFrame):
    close = df_closed["Close"]
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    trend = "BULLISH" if macd_line.iloc[-1] > signal_line.iloc[-1] else "BEARISH"
    return trend, float(macd_line.iloc[-1]), float(signal_line.iloc[-1])


def compute_vwap_status(df_closed: pd.DataFrame):
    """Session VWAP over the visible window (not a true exchange-anchored VWAP — labeled as such, not overclaimed)."""
    typical = (df_closed["High"] + df_closed["Low"] + df_closed["Close"]) / 3.0
    vwap = (typical * df_closed["Volume"]).cumsum() / df_closed["Volume"].cumsum().replace(0, np.nan)
    vwap_val = float(vwap.iloc[-1]) if pd.notna(vwap.iloc[-1]) else float(df_closed["Close"].iloc[-1])
    close = float(df_closed["Close"].iloc[-1])
    status = "ABOVE" if close > vwap_val else "BELOW"
    return status, vwap_val


def vol_status_label(vol_ratio: float) -> str:
    if vol_ratio >= 1.4:
        return "HIGH"
    if vol_ratio <= 0.85:
        return "LOW"
    return "NORMAL"


def compute_ema_cross(df_closed: pd.DataFrame) -> str:
    close = df_closed["Close"]
    ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    return "BULLISH" if ema20 > ema50 else "BEARISH"


# ------------------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------------------
def fetch_mtf_data(ticker: str):
    """Fetches all configured timeframes for one ticker. Never fabricates data on failure."""
    tf_data = {}
    data_integrity = {}
    for tf_label, (period, interval) in TF_CONFIG.items():
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 30:
                raise ValueError(f"Insufficient data returned ({len(df)} rows).")
            if tf_label == "4H":
                df = df.resample("4h").agg({
                    "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
                }).dropna()
            tf_data[tf_label] = df
            data_integrity[tf_label] = "LIVE"
        except Exception as e:
            tf_data[tf_label] = None
            data_integrity[tf_label] = f"UNAVAILABLE ({e})"
    return tf_data, data_integrity


def fetch_usdzar_rate():
    try:
        d = yf.download("ZAR=X", period="5d", interval="1d", progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        if d.empty:
            return None
        return float(d["Close"].iloc[-1])
    except Exception:
        return None


def compute_live_correlation_matrix():
    df_closes = pd.DataFrame()
    for name, ticker in ASSETS.items():
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


# ------------------------------------------------------------------------------
# TRUE RANGE / ADX / REGIME
# ------------------------------------------------------------------------------
def compute_true_range(df_closed: pd.DataFrame) -> pd.Series:
    """The ONLY place True Range is computed. Everything else calls this."""
    high, low, close = df_closed["High"], df_closed["Low"], df_closed["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def compute_adx(df: pd.DataFrame, length: int = 14) -> float:
    df_c = df.iloc[:-1].copy()
    high, low, close = df_c["High"], df_c["Low"], df_c["Close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = compute_true_range(df_c)
    eps = 1e-9
    atr = tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus_dm_s = pd.Series(plus_dm, index=df_c.index).ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    minus_dm_s = pd.Series(minus_dm, index=df_c.index).ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus_di = 100 * (plus_dm_s / (atr + eps))
    minus_di = 100 * (minus_dm_s / (atr + eps))
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = (plus_di - minus_di).abs() / di_sum * 100
    adx = dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean().iloc[-1]
    return float(np.nan_to_num(adx, nan=20.0))


def compute_market_regime(df: pd.DataFrame) -> dict:
    df_closed = df.iloc[:-1]
    adx_val = compute_adx(df)
    tr = compute_true_range(df_closed)
    atr_fast = tr.rolling(7).mean().iloc[-1]
    atr_slow = tr.rolling(28).mean().iloc[-1]
    vol_ratio = atr_fast / atr_slow if atr_slow > 0 else 1.0
    y = df_closed["Close"].tail(20).values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    if adx_val > 25 and vol_ratio > 1.1:
        regime = "TRENDING_EXPANSION"
    elif adx_val < 20 and vol_ratio < 0.85:
        regime = "ACCUMULATION_DISTRIBUTION"
    elif vol_ratio > 1.4:
        regime = "HIGH_VOLATILITY_RANGE"
    else:
        regime = "CHOP_LOW_VOLATILITY"
    return {"regime": regime, "adx": round(adx_val, 2), "vol_ratio": round(vol_ratio, 2), "slope": round(slope, 4)}


# ------------------------------------------------------------------------------
# STRUCTURE: SWINGS, BOS/CHoCH, DISPLACEMENT
# ------------------------------------------------------------------------------
def find_swing_points(df_closed: pd.DataFrame, window: int = 5):
    n = len(df_closed)
    win = 2 * window + 1
    if n < win:
        return np.array([], dtype=int), np.array([], dtype=int)
    highs = df_closed["High"]
    lows = df_closed["Low"]
    roll_max = highs.rolling(win, center=True).max()
    roll_min = lows.rolling(win, center=True).min()
    is_sh = (highs == roll_max) & roll_max.notna()
    is_sl = (lows == roll_min) & roll_min.notna()
    return np.where(is_sh.values)[0], np.where(is_sl.values)[0]


def measure_displacement(df: pd.DataFrame, index: int) -> float:
    """Max bullish/bearish displacement over the 3 candles following `index`."""
    if index + 3 >= len(df):
        return 0.0
    hi = df["High"].iloc[index]
    lo = df["Low"].iloc[index]
    fut = df.iloc[index + 1:index + 4]
    bull_disp = (fut["High"].max() - hi) / max(hi, 1e-9)
    bear_disp = (lo - fut["Low"].min()) / max(lo, 1e-9)
    return float(max(bull_disp, bear_disp))


def analyze_market_structure(df: pd.DataFrame):
    """
    Returns (bias, structure_type, last_swing_high, last_swing_low).
    CHoCH = break counter to the prior trend (reversal). BOS = break that
    continues it. A break under DISPLACEMENT_MIN gets a `_WEAK` suffix and
    is scored lower rather than treated as a full-strength signal.
    """
    df_c = df.iloc[:-1].copy()
    sh_idx, sl_idx = find_swing_points(df_c)
    if len(sh_idx) < 2 or len(sl_idx) < 2:
        return "NEUTRAL", "NONE", None, None
    last_sh = float(df_c["High"].iloc[sh_idx[-1]])
    prev_sh = float(df_c["High"].iloc[sh_idx[-2]])
    last_sl = float(df_c["Low"].iloc[sl_idx[-1]])
    prev_sl = float(df_c["Low"].iloc[sl_idx[-2]])
    close_val = df_c["Close"].iloc[-1]
    prior_trend_bullish = last_sh > prev_sh and last_sl > prev_sl
    prior_trend_bearish = last_sh < prev_sh and last_sl < prev_sl
    structure_type, bias = "NONE", "NEUTRAL"
    DISPLACEMENT_MIN = 0.0008
    if close_val > last_sh:
        displacement = (close_val - last_sh) / last_sh
        base = "BULLISH_CHoCH" if prior_trend_bearish else "BULLISH_BOS"
        structure_type = base if displacement >= DISPLACEMENT_MIN else base + "_WEAK"
        bias = "BUY"
    elif close_val < last_sl:
        displacement = (last_sl - close_val) / last_sl
        base = "BEARISH_CHoCH" if prior_trend_bullish else "BEARISH_BOS"
        structure_type = base if displacement >= DISPLACEMENT_MIN else base + "_WEAK"
        bias = "SELL"
    return bias, structure_type, last_sh, last_sl


def detect_choch(df: pd.DataFrame) -> dict:
    bias, struct, sh, sl = analyze_market_structure(df)
    return {"is_choch": "CHoCH" in struct, "bias": bias, "swing_high": sh, "swing_low": sl, "structure": struct}


# ------------------------------------------------------------------------------
# ORDER BLOCKS / BREAKERS / FVG
# ------------------------------------------------------------------------------
def find_order_block(df: pd.DataFrame, bias: str):
    """Returns (ob_type, zone, is_mitigated, is_invalidated). Only searches
    for a block matching the given bias — an OB in the wrong direction isn't
    "the OB that created the break," it's noise."""
    df_c = df.iloc[:-1].copy()
    n = len(df_c)
    ob_zone, ob_type = None, None
    is_mitigated, is_invalidated = False, False
    want_bullish, want_bearish = bias == "BUY", bias == "SELL"
    for i in range(n - 4, 10, -1):
        c_open, c_close = df_c["Open"].iloc[i], df_c["Close"].iloc[i]
        c_high, c_low = df_c["High"].iloc[i], df_c["Low"].iloc[i]
        disp = measure_displacement(df_c, i)
        if want_bullish and c_close < c_open and disp > 0.0025:
            ob_zone, ob_type = (c_low, c_high), "BULLISH_OB"
            after = df_c.iloc[i + 4:]
            if len(after) > 0:
                if after["Low"].min() <= c_high:
                    is_mitigated = True
                if after["Close"].min() < c_low:
                    is_invalidated = True
            break
        elif want_bearish and c_close > c_open and disp > 0.0025:
            ob_zone, ob_type = (c_low, c_high), "BEARISH_OB"
            after = df_c.iloc[i + 4:]
            if len(after) > 0:
                if after["High"].max() >= c_low:
                    is_mitigated = True
                if after["Close"].max() > c_high:
                    is_invalidated = True
            break
    if not ob_zone:
        base = df_c["Low"].iloc[-10:].min()
        ob_zone, ob_type = (base, base * 1.001), "NEUTRAL_DEMAND"
    return ob_type, ob_zone, is_mitigated, is_invalidated


def detect_breaker_block(df: pd.DataFrame, bias: str):
    """An invalidated order block flips into a breaker block (support becomes resistance, or vice versa)."""
    ob_type, zone, mit, inv = find_order_block(df, bias)
    if inv:
        b_type = "BULLISH_BREAKER" if bias == "BUY" else "BEARISH_BREAKER"
        return b_type, zone
    return "NONE", None


def detect_fvg(df: pd.DataFrame, lookback: int = 40):
    """3-candle Fair Value Gap. Returns the most recent UNFILLED gap, or None."""
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
        future = df_c.iloc[i + 2:]
        filled = bool(((future["Low"] <= zone[1]) & (future["High"] >= zone[0])).any()) if len(future) > 0 else False
        gaps.append({"index": i, "type": gap_type, "zone": zone, "filled": filled})
    unfilled = [g for g in gaps if not g["filled"]]
    return unfilled[-1] if unfilled else None


# ------------------------------------------------------------------------------
# LIQUIDITY: EQUAL HIGHS/LOWS + SWEEPS
# ------------------------------------------------------------------------------
def find_equal_levels(df: pd.DataFrame, lookback: int = 60, tolerance: float = 0.0006):
    r = df.tail(lookback)

    def cluster(values):
        vals = np.sort(np.asarray(values, dtype=float))
        groups = []
        if len(vals) == 0:
            return groups
        cur = [vals[0]]
        for v in vals[1:]:
            if abs(v - cur[-1]) / max(abs(cur[-1]), 1e-9) <= tolerance:
                cur.append(v)
            else:
                if len(cur) >= 2:
                    groups.append(float(np.mean(cur)))
                cur = [v]
        if len(cur) >= 2:
            groups.append(float(np.mean(cur)))
        return groups

    return cluster(r["High"].values), cluster(r["Low"].values)


def analyze_liquidity_sweep(df: pd.DataFrame):
    """Returns (swept: bool, message: str). Checks both a plain swing sweep
    and an equal-highs/lows engineered liquidity pool sweep — previously
    equal_highs_lows.py was never actually called from anywhere."""
    df_c = df.iloc[:-1].copy()
    recent_low = df_c["Low"].iloc[-15:-2].min()
    recent_high = df_c["High"].iloc[-15:-2].max()
    curr_low, curr_high, curr_close = df_c["Low"].iloc[-1], df_c["High"].iloc[-1], df_c["Close"].iloc[-1]

    if curr_low < recent_low and curr_close > recent_low:
        return True, f"SELL-SIDE SWEEP BELOW {recent_low:.2f}"
    if curr_high > recent_high and curr_close < recent_high:
        return True, f"BUY-SIDE SWEEP ABOVE {recent_high:.2f}"

    eq_highs, eq_lows = find_equal_levels(df_c)
    tol = curr_close * 0.0006
    for eqh in eq_highs:
        if curr_high > eqh + tol * 0.2 and curr_close < eqh:
            return True, f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {eqh:.2f}"
    for eql in eq_lows:
        if curr_low < eql - tol * 0.2 and curr_close > eql:
            return True, f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {eql:.2f}"
    return False, "NO_SWEEP"


# ------------------------------------------------------------------------------
# PREMIUM / DISCOUNT + SESSIONS
# ------------------------------------------------------------------------------
def calculate_premium_discount(df: pd.DataFrame, lookback: int = 50) -> dict:
    """Fibonacci-midpoint premium/discount zone over the recent swing range."""
    df_c = df.iloc[:-1].tail(lookback)
    swing_high, swing_low = df_c["High"].max(), df_c["Low"].min()
    equilibrium = (swing_high + swing_low) / 2.0
    close = df_c["Close"].iloc[-1]
    zone = "PREMIUM" if close > equilibrium else "DISCOUNT"
    return {"zone": zone, "equilibrium": float(equilibrium), "swing_high": float(swing_high), "swing_low": float(swing_low)}


def get_session_info():
    """Returns (session_name, quality_pct). DST-aware via zoneinfo."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if not _TZ_OK:
        return "UNKNOWN (tz database unavailable)", 50.0
    try:
        london_hour = now_utc.astimezone(ZoneInfo("Europe/London")).hour
        ny_hour = now_utc.astimezone(ZoneInfo("America/New_York")).hour
        tokyo_hour = now_utc.astimezone(ZoneInfo("Asia/Tokyo")).hour
        sydney_hour = now_utc.astimezone(ZoneInfo("Australia/Sydney")).hour

        in_london = 8 <= london_hour <= 16
        in_ny = 8 <= ny_hour <= 17
        in_tokyo = 9 <= tokyo_hour <= 18
        in_sydney = 8 <= sydney_hour <= 17

        if in_london and in_ny:
            return "LONDON / NEW YORK OVERLAP", 95.0
        if in_london:
            return "LONDON SESSION", 80.0
        if in_ny:
            return "NEW YORK SESSION", 80.0
        if in_tokyo:
            return "TOKYO SESSION", 55.0
        if in_sydney:
            return "SYDNEY SESSION", 45.0
        return "OFF-SESSION / LOW LIQUIDITY", 20.0
    except Exception:
        return "UNKNOWN (session lookup failed)", 50.0


# ------------------------------------------------------------------------------
# TREND STRENGTH
# ------------------------------------------------------------------------------
def evaluate_trend_strength(df_closed: pd.DataFrame, tf_biases: dict, regime_info: dict, struct_bias: str):
    close = df_closed["Close"]
    ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(close) >= 200 else None
    last_close = close.iloc[-1]
    ema_bull = last_close > ema20 > ema50 and (ema200 is None or ema50 > ema200)
    ema_bear = last_close < ema20 < ema50 and (ema200 is None or ema50 < ema200)
    adx_ok = regime_info["adx"] >= 20
    bull_cnt = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_cnt = sum(1 for v in tf_biases.values() if v == "SELL")
    if ema_bull and adx_ok and bull_cnt >= 3 and struct_bias == "BUY":
        return True, "EMA stack + ADX + 3/4 TF aligned bullish"
    if ema_bear and adx_ok and bear_cnt >= 3 and struct_bias == "SELL":
        return True, "EMA stack + ADX + 3/4 TF aligned bearish"
    return False, "Trend strength criteria not met"


# ------------------------------------------------------------------------------
# POSITION SIZING
# ------------------------------------------------------------------------------
def calculate_position_size(account_balance_usd, risk_pct: float, entry_price: float, stop_loss_price: float, contract_size: float = 100.0):
    if not account_balance_usd or account_balance_usd <= 0:
        return None
    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance <= 0:
        return None
    risk_amount_usd = account_balance_usd * (risk_pct / 100.0)
    lots = risk_amount_usd / (stop_distance * contract_size)
    return {"risk_amount_usd": round(risk_amount_usd, 2), "stop_distance": round(stop_distance, 2), "lots": round(lots, 3)}


# ------------------------------------------------------------------------------
# SCORING
# ------------------------------------------------------------------------------
def score_signal(tf_biases, struct_type, ob_type, mitigated, invalidated, sweep, fvg_present, rr, pd_zone, bias, trend_strong):
    """
    0-100 additive score (kept in the same style as your original
    score_signal, since additive/interpretable is genuinely better than a
    black-box formula for a system you're trusting with real money — but
    every input now actually gets used, unlike before.
    """
    bull = sum(v == "BUY" for v in tf_biases.values())
    bear = sum(v == "SELL" for v in tf_biases.values())
    tf_score = (max(bull, bear) / 4.0) * 25.0

    is_weak = struct_type.endswith("_WEAK")
    base_struct = struct_type[:-5] if is_weak else struct_type
    if "CHoCH" in base_struct:
        struct_score = 12.0 if is_weak else 20.0
    elif "BOS" in base_struct:
        struct_score = 8.0 if is_weak else 15.0
    else:
        struct_score = 0.0

    if ob_type in ("BULLISH_OB", "BEARISH_OB"):
        if invalidated:
            ob_score = -10.0
        elif mitigated:
            ob_score = 7.0
        else:
            ob_score = 15.0
    else:
        ob_score = 0.0

    sweep_score = 10.0 if sweep else 0.0
    fvg_score = 8.0 if fvg_present else 0.0
    rr_score = min(12.0, max(0.0, (rr - 1.0) * 6.0))

    pd_score = 0.0
    if bias == "BUY" and pd_zone == "DISCOUNT":
        pd_score = 10.0
    elif bias == "SELL" and pd_zone == "PREMIUM":
        pd_score = 10.0
    elif bias == "BUY" and pd_zone == "PREMIUM":
        pd_score = -5.0
    elif bias == "SELL" and pd_zone == "DISCOUNT":
        pd_score = -5.0

    trend_score = 10.0 if trend_strong else 0.0

    total = tf_score + struct_score + ob_score + sweep_score + fvg_score + rr_score + pd_score + trend_score
    return float(min(100.0, max(0.0, round(total, 1))))


def score_bull_bear(tf_biases, struct_type, ob_type, mitigated, invalidated, sweep, sweep_msg, fvg, pd_zone, trend_strong, macd_trend, rsi_val):
    """
    Independent BULL and BEAR scores (not mirrors of each other — e.g.
    14%/71% is a valid reading, they don't have to sum to 100). Each side
    accumulates evidence pointing its own direction; a market can show weak
    evidence on BOTH sides at once, which a single 0-100 "confidence" number
    can't represent but two independent scores can.
    """
    bull, bear = 0.0, 0.0
    bull_cnt = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_cnt = sum(1 for v in tf_biases.values() if v == "SELL")
    bull += (bull_cnt / 4.0) * 25.0
    bear += (bear_cnt / 4.0) * 25.0

    is_weak = struct_type.endswith("_WEAK")
    base_struct = struct_type[:-5] if is_weak else struct_type
    struct_pts = (10.0 if is_weak else 20.0) if "CHoCH" in base_struct else ((6.0 if is_weak else 15.0) if "BOS" in base_struct else 0.0)
    if "BULLISH" in base_struct:
        bull += struct_pts
    elif "BEARISH" in base_struct:
        bear += struct_pts

    if ob_type == "BULLISH_OB" and not invalidated:
        bull += 15.0 if not mitigated else 7.0
    elif ob_type == "BEARISH_OB" and not invalidated:
        bear += 15.0 if not mitigated else 7.0

    if sweep:
        if "SELL-SIDE" in sweep_msg or "EQUAL-LOWS" in sweep_msg:
            bull += 12.0  # sell-side liquidity swept -> often precedes a bullish move
        elif "BUY-SIDE" in sweep_msg or "EQUAL-HIGHS" in sweep_msg:
            bear += 12.0

    if fvg is not None:
        if fvg["type"] == "BULLISH_FVG":
            bull += 8.0
        else:
            bear += 8.0

    if pd_zone == "DISCOUNT":
        bull += 8.0
    elif pd_zone == "PREMIUM":
        bear += 8.0

    if macd_trend == "BULLISH":
        bull += 7.0
    else:
        bear += 7.0

    if rsi_val >= 55:
        bull += 5.0
    elif rsi_val <= 45:
        bear += 5.0

    if trend_strong:
        bull += 10.0 if bull > bear else 0.0
        bear += 10.0 if bear > bull else 0.0

    return round(min(100.0, bull), 1), round(min(100.0, bear), 1)


# ------------------------------------------------------------------------------
# MASTER SIGNAL GENERATOR
# ------------------------------------------------------------------------------
def generate_omega_signal(symbol: str, ticker: str, min_tf: int = DEFAULT_MIN_TF_AGREEMENT,
                           min_score: float = DEFAULT_MIN_SCORE, min_rr: float = DEFAULT_MIN_RR):
    data, integrity = fetch_mtf_data(ticker)
    if any(v is None for v in data.values()):
        return {"ok": False, "symbol": symbol, "ticker": ticker, "reason": "Data fetch failed", "data_integrity": integrity}

    biases, structs = {}, {}
    for tf, df in data.items():
        b, s, _, _ = analyze_market_structure(df)
        biases[tf], structs[tf] = b, s

    struct_bias, struct_type, sh, sl = analyze_market_structure(data["15M"])
    ob_type, ob_zone, mitigated, invalidated = find_order_block(data["15M"], struct_bias)
    fvg = detect_fvg(data["15M"])
    sweep, sweep_msg = analyze_liquidity_sweep(data["15M"])
    pd_info = calculate_premium_discount(data["15M"])
    regime_info = compute_market_regime(data["15M"])
    trend_strong, trend_detail = evaluate_trend_strength(data["15M"].iloc[:-1], biases, regime_info, struct_bias)
    eq_highs, eq_lows = find_equal_levels(data["15M"].iloc[:-1])

    rsi_val = compute_rsi(data["15M"].iloc[:-1])
    macd_trend, macd_line, macd_signal = compute_macd_trend(data["15M"].iloc[:-1])
    vwap_status, vwap_val = compute_vwap_status(data["15M"].iloc[:-1])
    vol_status = vol_status_label(regime_info["vol_ratio"])
    ema_cross = compute_ema_cross(data["15M"].iloc[:-1])
    bull_score, bear_score = score_bull_bear(biases, struct_type, ob_type, mitigated, invalidated, sweep, sweep_msg, fvg, pd_info["zone"], trend_strong, macd_trend, rsi_val)

    entry = float(data["15M"]["Close"].iloc[-1])
    tr = compute_true_range(data["15M"].iloc[:-1])
    atrv = float(tr.rolling(14).mean().iloc[-1])

    # Structure-based stop: beyond the OB zone (if valid) or last swing point,
    # ATR only as a minimum-distance floor — not the thing driving the stop.
    atr_floor = atrv * 1.0
    small_buffer = atrv * 0.15
    if struct_bias == "BUY":
        structural_ref = ob_zone[0] if ob_type == "BULLISH_OB" and not invalidated else sl
        structural_ref = structural_ref if structural_ref is not None else entry - atrv * 1.5
        stop = min(structural_ref - small_buffer, entry - atr_floor)
    elif struct_bias == "SELL":
        structural_ref = ob_zone[1] if ob_type == "BEARISH_OB" and not invalidated else sh
        structural_ref = structural_ref if structural_ref is not None else entry + atrv * 1.5
        stop = max(structural_ref + small_buffer, entry + atr_floor)
    else:
        stop = entry - atrv * 1.5

    tp1 = entry + 1.5 * atrv if struct_bias == "BUY" else entry - 1.5 * atrv
    tp2 = entry + 3.0 * atrv if struct_bias == "BUY" else entry - 3.0 * atrv
    tp3 = entry + 5.0 * atrv if struct_bias == "BUY" else entry - 5.0 * atrv

    rr = abs(tp2 - entry) / max(abs(entry - stop), 1e-9)

    score = score_signal(biases, struct_type, ob_type, mitigated, invalidated, sweep, fvg is not None, rr, pd_info["zone"], struct_bias, trend_strong)

    bull_cnt = sum(v == "BUY" for v in biases.values())
    bear_cnt = sum(v == "SELL" for v in biases.values())

    reason = None
    if bull_cnt >= min_tf and score >= min_score and struct_bias == "BUY":
        bias = "BUY"
    elif bear_cnt >= min_tf and score >= min_score and struct_bias == "SELL":
        bias = "SELL"
    else:
        bias = "NEUTRAL"
        reason = f"Timeframe agreement or score below threshold ({max(bull_cnt,bear_cnt)}/{min_tf} TF, {score}/{min_score} score)"

    # Enforce the minimum R:R that was previously declared in config but never checked.
    if bias != "NEUTRAL" and rr < min_rr:
        reason = f"R:R {rr:.2f} below minimum {min_rr} — signal downgraded to NEUTRAL"
        bias = "NEUTRAL"

    return {
        "ok": True, "symbol": symbol, "ticker": ticker, "data": data, "data_integrity": integrity,
        "bias": bias, "score": score, "entry": entry, "stop": stop,
        "tp1": tp1, "tp2": tp2, "tp3": tp3, "rr": rr, "atr": atrv,
        "tf_biases": biases, "tf_structures": structs, "structure": struct_type,
        "ob_type": ob_type, "ob_zone": ob_zone, "ob_mitigated": mitigated, "ob_invalidated": invalidated,
        "fvg": fvg, "sweep": sweep, "sweep_detail": sweep_msg,
        "pd_zone": pd_info["zone"], "pd_info": pd_info,
        "session": get_session_info()[0], "session_quality": get_session_info()[1],
        "regime": regime_info, "trend_strong": trend_strong, "trend_detail": trend_detail,
        "eq_highs": eq_highs, "eq_lows": eq_lows,
        "rsi": rsi_val, "macd_trend": macd_trend, "macd_line": macd_line, "macd_signal": macd_signal,
        "vwap_status": vwap_status, "vwap_val": vwap_val, "vol_status": vol_status, "ema_cross": ema_cross,
        "bull_score": bull_score, "bear_score": bear_score,
        "reason": reason,
    }


def grade(score: float) -> str:
    if score >= 85:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"
