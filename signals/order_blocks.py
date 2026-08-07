import pandas as pd
from typing import Tuple, Optional
from signals.displacement import check_displacement

def detect_validated_order_block(df: pd.DataFrame, struct_bias: str) -> Tuple[str, Tuple[float, float], bool, bool]:
    df_c = df.iloc[:-1].copy()
    n = len(df_c)

    ob_zone = None
    ob_type = "NEUTRAL_DEMAND"
    is_mitigated = False
    is_invalidated = False

    want_bullish = struct_bias == "BUY"
    want_bearish = struct_bias == "SELL"

    for i in range(n - 4, 10, -1):
        c_open, c_close = df_c["Open"].iloc[i], df_c["Close"].iloc[i]
        c_high, c_low = df_c["High"].iloc[i], df_c["Low"].iloc[i]

        if want_bullish and c_close < c_open:
            if check_displacement(df_c, i, "BULLISH", threshold=0.0025):
                ob_zone = (c_low, c_high)
                ob_type = "BULLISH_OB"
                after = df_c.iloc[i + 4 :]
                if len(after) > 0:
                    if after["Low"].min() <= c_high:
                        is_mitigated = True
                    if after["Close"].min() < c_low:
                        is_invalidated = True
                break

        elif want_bearish and c_close > c_open:
            if check_displacement(df_c, i, "BEARISH", threshold=0.0025):
                ob_zone = (c_low, c_high)
                ob_type = "BEARISH_OB"
                after = df_c.iloc[i + 4 :]
                if len(after) > 0:
                    if after["High"].max() >= c_low:
                        is_mitigated = True
                    if after["Close"].max() > c_high:
                        is_invalidated = True
                break

    if not ob_zone:
        low_val = float(df_c["Low"].iloc[-10:].min())
        ob_zone = (low_val, low_val * 1.001)

    return ob_type, ob_zone, is_mitigated, is_invalidated
