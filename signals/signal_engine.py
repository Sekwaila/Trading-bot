"""
SEKWAILA OMEGA X — MASTER SIGNAL ENGINE
"""
import pandas as pd
import numpy as np
from .multi_timeframe import fetch_mtf_data
from .market_structure import analyze_market_structure
from .order_blocks import find_order_block
from .fair_value_gap import detect_fvg
from .liquidity import analyze_liquidity_sweep
from .sessions import get_session_info
from .premium_discount import calculate_premium_discount

def score_signal(tf_biases, struct_type, ob_type, inv, sweep, fvg, rr):
    bull = sum(v == "BUY" for v in tf_biases.values())
    bear = sum(v == "SELL" for v in tf_biases.values())
    tf_score = (max(bull, bear) / 4.0) * 30.0
    
    struct_score = 20 if "BOS" in struct_type else 15 if "CHoCH" in struct_type else 5
    ob_score = 15 if ob_type in ("BULLISH_OB", "BEARISH_OB") and not inv else 0
    sweep_score = 15 if sweep else 0
    fvg_score = 10 if fvg else 0
    rr_score = min(10, max(0, (rr - 1.0) * 5.0))
    
    return float(min(100.0, round(tf_score + struct_score + ob_score + sweep_score + fvg_score + rr_score, 1)))

def generate_omega_signal(symbol: str, ticker: str, min_tf: int = 3):
    data, integrity = fetch_mtf_data(ticker)
    if any(v is None for v in data.values()):
        return {"ok": False, "symbol": symbol, "reason": "Data fetch failed"}
        
    biases, structs = {}, {}
    for tf, df in data.items():
        b, s, _, _ = analyze_market_structure(df)
        biases[tf], structs[tf] = b, s
        
    struct_bias, struct_type, sh, sl = analyze_market_structure(data["15M"])
    ob_type, ob_zone, mit, inv = find_order_block(data["15M"], struct_bias)
    fvg = detect_fvg(data["15M"])
    sweep, sweep_msg = analyze_liquidity_sweep(data["15M"])
    pd_info = calculate_premium_discount(data["15M"])
    
    entry = float(data["15M"]["Close"].iloc[-1])
    atrv = float((data["15M"]["High"] - data["15M"]["Low"]).tail(14).mean())
    
    stop = entry - 1.5 * atrv if struct_bias == "BUY" else entry + 1.5 * atrv
    tp1 = entry + 1.5 * atrv if struct_bias == "BUY" else entry - 1.5 * atrv
    tp2 = entry + 3.0 * atrv if struct_bias == "BUY" else entry - 3.0 * atrv
    tp3 = entry + 5.0 * atrv if struct_bias == "BUY" else entry - 5.0 * atrv
    
    rr = abs(tp2 - entry) / max(abs(entry - stop), 1e-9)
    score = score_signal(biases, struct_type, ob_type, inv, sweep, fvg, rr)
    
    bull_cnt = sum(v == "BUY" for v in biases.values())
    bear_cnt = sum(v == "SELL" for v in biases.values())
    
    bias = "BUY" if bull_cnt >= min_tf and score >= 65 else "SELL" if bear_cnt >= min_tf and score >= 65 else "NEUTRAL"
    
    return {
        "ok": True, "symbol": symbol, "ticker": ticker, "data": data,
        "bias": bias, "score": score, "entry": entry, "stop": stop,
        "tp1": tp1, "tp2": tp2, "tp3": tp3, "rr": rr,
        "tf_biases": biases, "tf_structures": structs, "structure": struct_type,
        "ob_type": ob_type, "ob_zone": ob_zone, "fvg": fvg, "sweep": sweep,
        "sweep_detail": sweep_msg, "pd_zone": pd_info["zone"],
        "session": get_session_info()[0]
    }
