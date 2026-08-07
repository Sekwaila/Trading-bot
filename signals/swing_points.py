import numpy as np
import pandas as pd
from typing import Tuple

def find_swing_points(df_closed: pd.DataFrame, window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorized swing high/low detection using rolling windows."""
    n = len(df_closed)
    win = 2 * window + 1
    if n < win:
        return np.array([], dtype=int), np.array([], dtype=int)

    highs = df_closed["High"]
    lows = df_closed["Low"]

    roll_max = highs.rolling(win, center=True).max()
    roll_min = lows.rolling(win, center=True).min()

    is_sh = (highs == roll_max) & roll_max.notna()
    is_sl = (lows == roll_min) & roll_min.notna()

    sh_idx = np.where(is_sh.values)[0]
    sl_idx = np.where(is_sl.values)[0]
    return sh_idx, sl_idx
