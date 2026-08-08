import pandas as pd
from .displacement import measure_displacement

def find_order_block(df: pd.DataFrame, bias: str):
    c = df.iloc[:-1].copy()
    n = len(c)
    if n < 15:
        base = float(c["Low"].min())
        return "NEUTRAL_ZONE", (base, base * 1.001), False, False
        
    for i in range(n - 5, 10, -1):
        op, cl = float(c["Open"].iloc[i]), float(c["Close"].iloc[i])
        hi, lo = float(c["High"].iloc[i]), float(c["Low"].iloc[i])
        disp = measure_displacement(c, i)
        
        if bias == "BUY" and cl < op and disp > 0.0025:
            after = c.iloc[i+4:]
            mit = False if after.empty else bool((after["Low"] <= hi).any())
            inv = False if after.empty else bool((after["Close"] < lo).any())
            return "BULLISH_OB", (lo, hi), mit, inv
            
        if bias == "SELL" and cl > op and disp > 0.0025:
            after = c.iloc[i+4:]
            mit = False if after.empty else bool((after["High"] >= lo).any())
            inv = False if after.empty else bool((after["Close"] > hi).any())
            return "BEARISH_OB", (lo, hi), mit, inv
            
    base = float(c["Low"].tail(10).min())
    return "NEUTRAL_ZONE", (base, base * 1.001), False, False
