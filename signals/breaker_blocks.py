import pandas as pd
from .order_blocks import find_order_block

def detect_breaker_block(df: pd.DataFrame, bias: str):
    ob_type, zone, mit, inv = find_order_block(df, bias)
    if inv:
        b_type = "BULLISH_BREAKER" if bias == "BUY" else "BEARISH_BREAKER"
        return b_type, zone
    return "NONE", None
