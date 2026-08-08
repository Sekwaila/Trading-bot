import pandas as pd
from .swing_points import find_swings

def safe_float(val, default=0.0):
    try:
        if isinstance(val, (pd.Series)):
            return float(val.iloc[-1]) if not val.empty else default
        return float(val)
    except Exception:
        return default

def analyze_market_structure(df: pd.DataFrame):
    c = df.iloc[:-1].copy()
    sh, sl = find_swings(c)
    if len(sh) < 2 or len(sl) < 2:
        return "NEUTRAL", "NONE", None, None
    
    last_sh = safe_float(c["High"].iloc[sh[-1]])
    prev_sh = safe_float(c["High"].iloc[sh[-2]])
    last_sl = safe_float(c["Low"].iloc[sl[-1]])
    prev_sl = safe_float(c["Low"].iloc[sl[-2]])
    close = safe_float(c["Close"].iloc[-1])
    
    prior_bull = last_sh > prev_sh and last_sl > prev_sl
    prior_bear = last_sh < prev_sh and last_sl < prev_sl
    
    if close > last_sh:
        base = "BULLISH_CHoCH" if prior_bear else "BULLISH_BOS"
        return "BUY", base, last_sh, last_sl
    if close < last_sl:
        base = "BEARISH_CHoCH" if prior_bull else "BEARISH_BOS"
        return "SELL", base, last_sh, last_sl
        
    return "NEUTRAL", "NONE", last_sh, last_sl
