import pandas as pd
from market_data import get_candles

# Imports from your SMC sub-modules
from Signals.order_blocks import detect_order_blocks
from Signals.fair_value_gap import detect_fvg
from Signals.choch import detect_choch
from Signals.liquidity import detect_liquidity_sweep

def generate_omega_signal(symbol: str, ticker_info: dict = None, min_tf: int = 2, min_score: float = 65.0, min_rr: float = 1.5) -> dict:
    """
    Runs Smart Money Concepts (SMC) checks across timeframes and returns signal JSON.
    """
    df = get_candles(symbol, interval="5min", limit=100)
    if df.empty:
        return {"ok": False, "symbol": symbol, "reason": "No market data retrieved."}

    latest_price = df['close'].iloc[-1]
    
    # Analyze SMC Patterns
    choch = detect_choch(df)
    ob = detect_order_blocks(df)
    fvg = detect_fvg(df)
    sweep = detect_liquidity_sweep(df)

    score = 0.0
    bias = "NEUTRAL"
    reason = []

    if choch == "BULLISH": score += 30; reason.append("Bullish CHoCH")
    if sweep == "LIQUIDITY_TAKEN_LOW": score += 30; reason.append("Liquidity Sweep Low")
    if fvg.get("bullish_fvg"): score += 25; reason.append("Bullish FVG Mitigated")

    if choch == "BEARISH": score -= 30; reason.append("Bearish CHoCH")
    if sweep == "LIQUIDITY_TAKEN_HIGH": score -= 30; reason.append("Liquidity Sweep High")
    if fvg.get("bearish_fvg"): score -= 25; reason.append("Bearish FVG Mitigated")

    # Evaluate Buy / Sell Conditions
    if score >= min_score:
        bias = "BUY"
        sl = ob.get("bullish_ob_low", latest_price * 0.995)
        risk = latest_price - sl
        tp1 = latest_price + (risk * 1.5)
        tp2 = latest_price + (risk * min_rr)
    elif score <= -min_score:
        bias = "SELL"
        sl = ob.get("bearish_ob_high", latest_price * 1.005)
        risk = sl - latest_price
        tp1 = latest_price - (risk * 1.5)
        tp2 = latest_price - (risk * min_rr)
    else:
        sl, tp1, tp2 = 0.0, 0.0, 0.0

    return {
        "ok": True,
        "symbol": symbol,
        "bias": bias,
        "score": abs(score),
        "entry_price": latest_price,
        "stop_loss": sl,
        "tp1": tp1,
        "tp2": tp2,
        "reason": " + ".join(reason) if reason else "Market Consolidation",
        "data_integrity": {"candles_loaded": len(df)}
    }
