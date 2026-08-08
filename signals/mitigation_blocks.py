import pandas as pd
from .order_blocks import find_order_block

def detect_mitigation_block(df: pd.DataFrame, bias: str):
    ob_type, zone, mit, inv = find_order_block(df, bias)
    if mit and not inv:
        return f"{bias}_MITIGATION_BLOCK", zone
    return "NONE", None
