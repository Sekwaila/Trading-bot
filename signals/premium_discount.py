import pandas as pd

def calculate_premium_discount(df: pd.DataFrame):
    c = df.iloc[:-1]
    hi = float(c["High"].tail(50).max())
    lo = float(c["Low"].tail(50).min())
    eq = (hi + lo) / 2.0
    close = float(c["Close"].iloc[-1])
    
    zone = "PREMIUM" if close > eq else "DISCOUNT"
    return {"zone": zone, "equilibrium": eq, "range_high": hi, "range_low": lo}
