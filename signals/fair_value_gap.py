import pandas as pd
from typing import Optional, Dict

def detect_fair_value_gaps(df: pd.DataFrame, lookback: int = 40) -> Optional[Dict]:
    df_c = df.iloc[:-1].copy()
    n = len(df_c)
    start = max(2, n - lookback)

    gaps = []
    for i in range(start, n - 1):
        c_prev_high = df_c["High"].iloc[i - 1]
        c_prev_low = df_c["Low"].iloc[i - 1]
        c_next_high = df_c["High"].iloc[i + 1]
        c_next_low = df_c["Low"].iloc[i + 1]

        if c_next_low > c_prev_high:
            zone = (c_prev_high, c_next_low)
            gap_type = "BULLISH_FVG"
        elif c_next_high < c_prev_low:
            zone = (c_next_high, c_prev_low)
            gap_type = "BEARISH_FVG"
        else:
            continue

        future = df_c.iloc[i + 2 :]
        filled = False
        if len(future) > 0:
            filled = bool(((future["Low"] <= zone[1]) & (future["High"] >= zone[0])).any())

        gaps.append({"index": i, "type": gap_type, "zone": zone, "filled": filled})

    unfilled = [g for g in gaps if not g["filled"]]
    return unfilled[-1] if unfilled else None
