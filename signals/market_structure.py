import pandas as pd
from typing import Tuple, Optional
from signals.swing_points import find_swing_points

def analyze_market_structure(df: pd.DataFrame) -> Tuple[str, str, Optional[float], Optional[float]]:
    """Evaluates market structure bias and determines BOS / CHoCH displacement strength."""
    df_c = df.iloc[:-1].copy()
    sh_idx, sl_idx = find_swing_points(df_c)

    if len(sh_idx) < 2 or len(sl_idx) < 2:
        return "NEUTRAL", "NONE", None, None

    last_sh = float(df_c["High"].iloc[sh_idx[-1]])
    prev_sh = float(df_c["High"].iloc[sh_idx[-2]])
    last_sl = float(df_c["Low"].iloc[sl_idx[-1]])
    prev_sl = float(df_c["Low"].iloc[sl_idx[-2]])
    close_val = df_c["Close"].iloc[-1]

    prior_trend_bullish = last_sh > prev_sh and last_sl > prev_sl
    prior_trend_bearish = last_sh < prev_sh and last_sl < prev_sl

    structure_type = "NONE"
    bias = "NEUTRAL"
    DISPLACEMENT_MIN = 0.0008

    if close_val > last_sh:
        displacement = (close_val - last_sh) / last_sh
        base_type = "BULLISH_CHoCH" if prior_trend_bearish else "BULLISH_BOS"
        structure_type = base_type if displacement >= DISPLACEMENT_MIN else base_type + "_WEAK"
        bias = "BUY"
    elif close_val < last_sl:
        displacement = (last_sl - close_val) / last_sl
        base_type = "BEARISH_CHoCH" if prior_trend_bullish else "BEARISH_BOS"
        structure_type = base_type if displacement >= DISPLACEMENT_MIN else base_type + "_WEAK"
        bias = "SELL"

    return bias, structure_type, last_sh, last_sl
