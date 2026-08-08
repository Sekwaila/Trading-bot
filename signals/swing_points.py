import numpy as np
import pandas as pd

def find_swings(df: pd.DataFrame, window: int = 5):
    width = 2 * window + 1
    if len(df) < width:
        return np.array([], dtype=int), np.array([], dtype=int)
    hi, lo = df["High"], df["Low"]
    rh = hi.rolling(width, center=True).max()
    rl = lo.rolling(width, center=True).min()
    sh = np.where(((hi == rh) & rh.notna()).values)[0]
    sl = np.where(((lo == rl) & rl.notna()).values)[0]
    return sh, sl
