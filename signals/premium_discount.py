import pandas as pd
from typing import Dict

def compute_premium_discount_zones(df_closed: pd.DataFrame) -> Dict[str, float]:
    high = df_closed["High"].tail(50).max()
    low = df_closed["Low"].tail(50).min()
    equilibrium = (high + low) / 2.0
    return {
        "high": float(high),
        "low": float(low),
        "equilibrium": float(equilibrium)
    }
