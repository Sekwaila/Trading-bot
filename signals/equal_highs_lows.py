import numpy as np
import pandas as pd

def find_equal_levels(df: pd.DataFrame, lookback: int = 60, tolerance: float = 0.0006):
    r = df.tail(lookback)
    def cluster(values):
        vals = np.sort(np.asarray(values, dtype=float))
        groups = []
        if len(vals) == 0: return groups
        cur = [vals[0]]
        for v in vals[1:]:
            if abs(v - cur[-1]) / max(abs(cur[-1]), 1e-9) <= tolerance:
                cur.append(v)
            else:
                if len(cur) >= 2: groups.append(float(np.mean(cur)))
                cur = [v]
        if len(cur) >= 2: groups.append(float(np.mean(cur)))
        return groups

    return cluster(r["High"].values), cluster(r["Low"].values)
