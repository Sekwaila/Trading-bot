import pandas as pd
from .equal_highs_lows import find_equal_levels

def analyze_liquidity_sweep(df: pd.DataFrame):
    c = df.iloc[:-1]
    if len(c) < 18: return False, "NO_SWEEP"
    eqh, eql = find_equal_levels(c)
    
    rlow = float(c["Low"].iloc[-15:-2].min())
    rhigh = float(c["High"].iloc[-15:-2].max())
    lo = float(c["Low"].iloc[-1])
    hi = float(c["High"].iloc[-1])
    close = float(c["Close"].iloc[-1])
    
    if lo < rlow and close > rlow: return True, f"SELL-SIDE SWEEP BELOW {rlow:.4f}"
    if hi > rhigh and close < rhigh: return True, f"BUY-SIDE SWEEP ABOVE {rhigh:.4f}"
    
    tol = close * 0.0006
    for x in eqh:
        if hi > x + tol * 0.2 and close < x: return True, f"EQUAL-HIGHS SWEPT AT {x:.4f}"
    for x in eql:
        if lo < x - tol * 0.2 and close > x: return True, f"EQUAL-LOWS SWEPT AT {x:.4f}"
        
    return False, "NO_SWEEP"
