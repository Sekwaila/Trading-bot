import numpy as np
import pandas as pd
from typing import Tuple, List

def detect_equal_liquidity_levels(df_closed: pd.DataFrame, lookback: int = 50, tolerance_pct: float = 0.0006) -> Tuple[List[float], List[float]]:
    recent = df_closed.tail(lookback)

    def cluster(values: np.ndarray) -> List[float]:
        vals = np.sort(values)
        if len(vals) == 0:
            return []
        clusters = []
        current = [vals[0]]
        for v in vals[1:]:
            if abs(v - current[-1]) / current[-1] <= tolerance_pct:
                current.append(v)
            else:
                if len(current) >= 2:
                    clusters.append(float(np.mean(current)))
                current = [v]
        if len(current) >= 2:
            clusters.append(float(np.mean(current)))
        return clusters

    eq_highs = cluster(recent["High"].values)
    eq_lows = cluster(recent["Low"].values)
    return eq_highs, eq_lows
