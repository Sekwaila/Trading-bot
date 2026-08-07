import datetime
import math
import pandas as pd
from typing import Dict, Tuple, List

from config import config
from data.market_data import compute_true_range
from signals.choch import compute_market_regime
from signals.market_structure import analyze_market_structure
from signals.swing_points import find_swing_points
from signals.order_blocks import detect_validated_order_block
from signals.fair_value_gap import detect_fair_value_gaps
from signals.equal_highs_lows import detect_equal_liquidity_levels
from signals.liquidity import evaluate_liquidity_sweeps
from signals.sessions import check_session_validity
from signals.multi_timeframe import evaluate_mtf_bias

def evaluate_trend_strength(df_15m_closed: pd.DataFrame, tf_biases: dict, regime_info: dict, struct_bias: str) -> Tuple[bool, str]:
    close = df_15m_closed["Close"]
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
    elif ema_bear and adx_ok and bear_cnt >= 3 and struct_bias == "SELL":
        return True, "EMA stack + ADX + 3/4 TF aligned bearish"
    return False, "Trend strength criteria not met"

def evaluate_execution_barriers(df_15m: pd.DataFrame, regime_info: dict) -> Tuple[bool, List[str]]:
    barriers = []
    passed = True

    if regime_info["regime"] == "CHOP_LOW_VOLATILITY":
        passed = False
        barriers.append("REJECTED: Market in Low-Volatility Squeeze/Chop")

    df_c = df_15m.iloc[:-1]
    if "Volume" in df_c.columns and len(df_c) >= 20:
        recent_vol = df_c["Volume"].iloc[-1]
        avg_vol = df_c["Volume"].tail(20).mean()
        if avg_vol > 0 and recent_vol < avg_vol * 0.25:
            passed = False
            barriers.append("REJECTED: Relative Liquidity Low (volume vs 20-bar avg)")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_t = now_utc.time()
    for start_t, end_t in config.NEWS_BLACKOUT_WINDOWS_UTC:
        if start_t <= now_t <= end_t:
            passed = False
            barriers.append("REJECTED: High-Impact Macro Event Guard (STATIC PLACEHOLDER)")
            break

    session_ok, session_msg = check_session_validity()
    if not session_ok:
        passed = False
        barriers.append(session_msg)

    return passed, barriers

def calculate_confluence_score(
    tf_biases: dict,
    structure_type: str,
    ob_type: str,
    is_mitigated: bool,
    is_invalidated: bool,
    regime: str,
    sweep_detected: bool,
    fvg_present: bool,
    trend_strong: bool = False,
) -> float:
    z = -1.2
    bull_cnt = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_cnt = sum(1 for v in tf_biases.values() if v == "SELL")
    z += max(bull_cnt, bear_cnt) * 0.45

    is_weak = structure_type.endswith("_WEAK")
    base_structure_type = structure_type[:-5] if is_weak else structure_type

    if "CHoCH" in base_structure_type:
        z += 0.25 if is_weak else 0.65
    elif "BOS" in base_structure_type:
        z += 0.15 if is_weak else 0.40

    if ob_type in ["BULLISH_OB", "BEARISH_OB"]:
        if is_invalidated:
            z -= 0.60
        elif is_mitigated:
            z -= 0.30
        else:
            z += 0.55

    if sweep_detected:
        z += 0.70
    if fvg_present:
        z += 0.25
    if trend_strong:
        z += 0.35

    if regime == "TRENDING_EXPANSION":
        z += 0.50
    elif regime == "CHOP_LOW_VOLATILITY":
        z -= 0.80

    return round((1.0 / (1.0 + math.exp(-z))) * 100, 1)

def compute_dynamic_targets(overall_bias: str, entry_price: float, atr_val: float,
                             eq_highs: list, eq_lows: list, last_sh, last_sl):
    atr_tp1 = entry_price + atr_val * 1.5 if overall_bias == "BUY" else entry_price - atr_val * 1.5
    atr_tp2 = entry_price + atr_val * 3.0 if overall_bias == "BUY" else entry_price - atr_val * 3.0
    atr_tp3 = entry_price + atr_val * 5.0 if overall_bias == "BUY" else entry_price - atr_val * 5.0

    if overall_bias == "BUY":
        pool_levels = [lvl for lvl in eq_highs if lvl > entry_price]
        if last_sh is not None and last_sh > entry_price:
            pool_levels.append(last_sh)
        candidates = sorted(pool_levels)
    elif overall_bias == "SELL":
        pool_levels = [lvl for lvl in eq_lows if lvl < entry_price]
        if last_sl is not None and last_sl < entry_price:
            pool_levels.append(last_sl)
        candidates = sorted(pool_levels, reverse=True)
    else:
        candidates = []

    tp1, tp1_source = atr_tp1, "ATR"
    tp2, tp2_source = atr_tp2, "ATR"

    if len(candidates) >= 1 and abs(candidates[0] - entry_price) >= atr_val * 0.5:
        tp1, tp1_source = candidates[0], "Liquidity Pool"
    if len(candidates) >= 2 and abs(candidates[1] - entry_price) >= atr_val * 1.0:
        tp2, tp2_source = candidates[1], "Liquidity Pool"

    return tp1, tp2, atr_tp3, tp1_source, tp2_source

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
    trend_strong, trend_detail = evaluate_trend_strength(df_15m.iloc[:-1], tf_biases, regime_info, struct_bias)

    sweep_detected, sweep_detail = evaluate_liquidity_sweeps(df_15m.iloc[:-1], eq_highs, eq_lows)

    confluence_score = calculate_confluence_score(
        tf_biases, struct_type, ob_type, is_mitigated, is_invalidated,
        regime_info["regime"], sweep_detected, fvg is not None, trend_strong
    )

    bull_score = sum(1 for v in tf_biases.values() if v == "BUY")
    bear_score = sum(1 for v in tf_biases.values() if v == "SELL")

    if bull_score >= 3 and confluence_score >= config.CONFLUENCE_THRESHOLD:
        overall_bias = "BUY"
    elif bear_score >= 3 and confluence_score >= config.CONFLUENCE_THRESHOLD:
        overall_bias = "SELL"
    else:
        overall_bias = "NEUTRAL"

    passed_filters, filter_rejections = evaluate_execution_barriers(df_15m, regime_info)

    df_c = df_15m.iloc[:-1]
    tr = compute_true_range(df_c)
    atr_val = float(tr.rolling(14).mean().iloc[-1])
    entry_price = float(df_15m["Close"].iloc[-1])

    atr_floor = atr_val * 1.0
    small_buffer = atr_val * 0.15

    if overall_bias == "BUY":
        structural_ref = ob_zone[0] if ob_type == "BULLISH_OB" and not is_invalidated else last_sl
        structural_ref = structural_ref if structural_ref is not None else entry_price - atr_val * 1.5
        stop_loss = min(structural_ref - small_buffer, entry_price - atr_floor)
        be_trigger = entry_price + (atr_val * 1.2)
    elif overall_bias == "SELL":
        structural_ref = ob_zone[1] if ob_type == "BEARISH_OB" and not is_invalidated else last_sh
        structural_ref = structural_ref if structural_ref is not None else entry_price + atr_val * 1.5
        stop_loss = max(structural_ref + small_buffer, entry_price + atr_floor)
        be_trigger = entry_price - (atr_val * 1.2)
    else:
        stop_loss = entry_price - (atr_val * 1.5)
        be_trigger = entry_price + (atr_val * 1.2)

    tp1, tp2, tp3, tp1_source, tp2_source = compute_dynamic_targets(
        overall_bias, entry_price, atr_val, eq_highs, eq_lows, last_sh, last_sl
    )

    fvg_text = "none unfilled nearby" if fvg is None else f"{fvg['type']} at {fvg['zone'][0]:.2f}-{fvg['zone'][1]:.2f} (unfilled)"
    ob_state = "INVALIDATED" if is_invalidated else ("MITIGATED" if is_mitigated else "UNMITIGATED")

    ai_narrative = (
        f"1D & 4H Macro structure remains aligned towards {overall_bias}. "
        f"Current market regime is classified as {regime_info['regime']} (ADX: {regime_info['adx']}). "
        f"A {struct_type} formed on the 15M timeframe. Trend strength: {trend_detail if trend_strong else 'not confirmed'}. "
        f"{sweep_detail} was identified prior to entering the {ob_state} {ob_type} zone ({ob_zone[0]:.2f} - {ob_zone[1]:.2f}). "
        f"Nearest Fair Value Gap: {fvg_text}. TP1 sourced from {tp1_source}, TP2 sourced from {tp2_source}. "
        f"The heuristic confluence score is {confluence_score}%."
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
        "tp3": tp3,
        "be_trigger": be_trigger,
        "atr": atr_val,
        "regime": regime_info,
        "tf_biases": tf_biases,
        "struct_type": struct_type,
        "ob_type": ob_type,
        "ob_zone": ob_zone,
        "is_mitigated": is_mitigated,
        "is_invalidated": is_invalidated,
        "fvg": fvg,
        "eq_highs": eq_highs,
        "eq_lows": eq_lows,
        "trend_strong": trend_strong,
        "trend_detail": trend_detail,
        "tp1_source": tp1_source,
        "tp2_source": tp2_source,
        "sweep_detail": sweep_detail,
        "passed_filters": passed_filters,
        "filter_rejections": filter_rejections,
        "ai_narrative": ai_narrative,
        "df_15m": df_15m,
        "data_integrity": data_integrity,
    }
