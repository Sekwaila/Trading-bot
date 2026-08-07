import pandas as pd
from typing import Tuple, List

def evaluate_liquidity_sweeps(df_closed: pd.DataFrame, eq_highs: List[float], eq_lows: List[float]) -> Tuple[bool, str]:
    recent_low = df_closed["Low"].iloc[-15:-2].min()
    recent_high = df_closed["High"].iloc[-15:-2].max()
    curr_low = df_closed["Low"].iloc[-1]
    curr_high = df_closed["High"].iloc[-1]
    curr_close = df_closed["Close"].iloc[-1]

    sweep_detected = False
    sweep_detail = "NO_SWEEP"

    if curr_low < recent_low and curr_close > recent_low:
        return True, f"SELL-SIDE SWEEP BELOW {recent_low:.2f}"
    elif curr_high > recent_high and curr_close < recent_high:
        return True, f"BUY-SIDE SWEEP ABOVE {recent_high:.2f}"

    pool_tolerance = curr_close * 0.0006
    for eqh in eq_highs:
        if curr_high > eqh + pool_tolerance * 0.2 and curr_close < eqh:
            return True, f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {eqh:.2f}"

    for eql in eq_lows:
        if curr_low < eql - pool_tolerance * 0.2 and curr_close > eql:
            return True, f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {eql:.2f}"

    return sweep_detected, sweep_detail
