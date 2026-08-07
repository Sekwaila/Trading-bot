import pandas as pd

def check_displacement(df_closed: pd.DataFrame, index: int, direction: str, threshold: float = 0.0025) -> bool:
    """Verifies multi-candle impulse displacement following a structural event."""
    if index + 3 >= len(df_closed):
        return False

    c_high = df_closed["High"].iloc[index]
    c_low = df_closed["Low"].iloc[index]

    if direction == "BULLISH":
        subsequent_high = df_closed["High"].iloc[index + 1 : index + 4].max()
        return ((subsequent_high - c_high) / c_high) >= threshold
    elif direction == "BEARISH":
        subsequent_low = df_closed["Low"].iloc[index + 1 : index + 4].min()
        return ((c_low - subsequent_low) / c_low) >= threshold
    return False
