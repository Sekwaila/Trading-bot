import pandas as pd

def detect_fvg(df: pd.DataFrame, lookback: int = 50):
    c = df.iloc[:-1].copy()
    n = len(c)
    start = max(2, n - lookback)
    gaps = []
    for i in range(start, n - 1):
        ph, pl = float(c["High"].iloc[i-1]), float(c["Low"].iloc[i-1])
        nh, nl = float(c["High"].iloc[i+1]), float(c["Low"].iloc[i+1])
        
        if nl > ph:
            zone = (ph, nl)
            typ = "BULLISH_FVG"
        elif nh < pl:
            zone = (nh, pl)
            typ = "BEARISH_FVG"
        else:
            continue
            
        future = c.iloc[i+2:]
        filled = False if future.empty else bool(((future["Low"] <= zone[1]) & (future["High"] >= zone[0])).any())
        if not filled:
            gaps.append({"type": typ, "zone": zone, "index": i})
            
    return gaps[-1] if gaps else None
