import pandas as pd
from typing import Optional, Tuple

def detect_breaker_block(df_closed: pd.DataFrame, struct_type: str) -> Optional[Tuple[float, float]]:
    """Identifies a failed Order Block that acted as a structural breaker."""
    if "CHoCH" not in struct_type:
        return None
    
    last_candle = df_closed.iloc[-2]
    return float(last_candle["Low"]), float(last_candle["High"])
