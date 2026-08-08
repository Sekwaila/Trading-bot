import pandas as pd
from .swing_points import find_swings

def detect_inducement(df: pd.DataFrame, bias: str) -> bool:
    c = df.iloc[:-1]
    sh, sl = find_swings(c)
    if len(sh) < 1 or len(sl) < 1: return False
    
    last_close = float(c["Close"].iloc[-1])
    if bias == "BUY":
        return last_close < float(c["High"].iloc[sh[-1]])
    elif bias == "SELL":
        return last_close > float(c["Low"].iloc[sl[-1]])
    return False
