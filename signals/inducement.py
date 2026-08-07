import pandas as pd
from signals.swing_points import find_swing_points

def check_inducement_sweep(df_closed: pd.DataFrame, struct_bias: str) -> bool:
    sh_idx, sl_idx = find_swing_points(df_closed)
    if len(sh_idx) == 0 or len(sl_idx) == 0:
        return False
    
    last_close = df_closed["Close"].iloc[-1]
    if struct_bias == "BUY" and len(sl_idx) > 0:
        minor_low = df_closed["Low"].iloc[sl_idx[-1]]
        return bool(df_closed["Low"].iloc[-1] < minor_low and last_close > minor_low)
    elif struct_bias == "SELL" and len(sh_idx) > 0:
        minor_high = df_closed["High"].iloc[sh_idx[-1]]
        return bool(df_closed["High"].iloc[-1] > minor_high and last_close < minor_high)
    
    return False
