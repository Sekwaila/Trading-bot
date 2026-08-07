import pandas as pd
import numpy as np
import math
from data.market_data import compute_true_range

def compute_adx(df: pd.DataFrame, length: int = 14) -> float:
    df_c = df.iloc[:-1].copy()
    high, low = df_c["High"], df_c["Low"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = compute_true_range(df_c)
    eps = 1e-9

    atr = tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus_dm_s = pd.Series(plus_dm, index=df_c.index).ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    minus_dm_s = pd.Series(minus_dm, index=df_c.index).ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    plus_di = 100 * (plus_dm_s / (atr + eps))
    minus_di = 100 * (minus_dm_s / (atr + eps))

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = (plus_di - minus_di).abs() / di_sum * 100
    adx = dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean().iloc[-1]
    return float(np.nan_to_num(adx, nan=20.0))

def compute_market_regime(df: pd.DataFrame) -> dict:
    df_closed = df.iloc[:-1]
    adx_val = compute_adx(df)

    tr = compute_true_range(df_closed)
    atr_fast = tr.rolling(7).mean().iloc[-1]
    atr_slow = tr.rolling(28).mean().iloc[-1]
    vol_ratio = atr_fast / atr_slow if atr_slow > 0 else 1.0

    y = df_closed["Close"].tail(20).values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    angle = math.degrees(math.atan(slope))

    if adx_val > 25 and vol_ratio > 1.1:
        regime = "TRENDING_EXPANSION"
    elif adx_val < 20 and vol_ratio < 0.85:
        regime = "ACCUMULATION_DISTRIBUTION"
    elif vol_ratio > 1.4:
        regime = "HIGH_VOLATILITY_RANGE"
    else:
        regime = "CHOP_LOW_VOLATILITY"

    return {
        "regime": regime,
        "adx": round(adx_val, 2),
        "vol_ratio": round(vol_ratio, 2),
        "slope": round(slope, 4),
        "angle": round(angle, 2),
    }
