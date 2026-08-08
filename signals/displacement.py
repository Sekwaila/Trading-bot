import pandas as pd

def measure_displacement(df: pd.DataFrame, index: int) -> float:
    if index + 3 >= len(df):
        return 0.0
    hi = df["High"].iloc[index]
    lo = df["Low"].iloc[index]
    fut = df.iloc[index+1:index+4]
    
    bull_disp = (fut["High"].max() - hi) / max(hi, 1e-9)
    bear_disp = (lo - fut["Low"].min()) / max(lo, 1e-9)
    return float(max(bull_disp, bear_disp))
