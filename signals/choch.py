import pandas as pd
from .market_structure import analyze_market_structure

def detect_choch(df: pd.DataFrame):
    bias, struct, sh, sl = analyze_market_structure(df)
    is_choch = "CHoCH" in struct
    return {"is_choch": is_choch, "bias": bias, "swing_high": sh, "swing_low": sl}
