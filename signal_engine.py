"""
SEKWAILA OMEGA X
Signal Engine

Features:
- BOS
- CHoCH
- Swing High / Low
- Liquidity Sweep
- Order Block
- Fair Value Gap
- Premium / Discount
- Strong Buy
- Strong Sell
- Aggressive Buy
- Aggressive Sell
"""

import pandas as pd
import numpy as np


# ==========================================
# SWING DETECTION
# ==========================================

def detect_swings(df, left=2, right=2):

    df = df.copy()

    df["swing_high"] = False
    df["swing_low"] = False

    highs = df["high"].values
    lows = df["low"].values

    for i in range(left, len(df)-right):

        if highs[i] == max(highs[i-left:i+right+1]):
            df.loc[df.index[i], "swing_high"] = True

        if lows[i] == min(lows[i-left:i+right+1]):
            df.loc[df.index[i], "swing_low"] = True

    return df


# ==========================================
# BOS / CHOCH
# ==========================================

def detect_structure(df):

    trend = None

    events = []

    last_high = None
    last_low = None

    for i in range(len(df)):

        row = df.iloc[i]

        if row["swing_high"]:
            last_high = row["high"]

        if row["swing_low"]:
            last_low = row["low"]

        if last_high:

            if row["close"] > last_high:

                if trend == "bullish":
                    events.append(("BOS","bullish"))

                else:
                    events.append(("CHOCH","bullish"))

                trend = "bullish"

                last_high = None

        if last_low:

            if row["close"] < last_low:

                if trend == "bearish":
                    events.append(("BOS","bearish"))

                else:
                    events.append(("CHOCH","bearish"))

                trend = "bearish"

                last_low = None

    return events, trend


# ==========================================
# FAIR VALUE GAP
# ==========================================

def detect_fvg(df):

    fvgs = []

    for i in range(1,len(df)-1):

        if df["low"].iloc[i+1] > df["high"].iloc[i-1]:

            fvgs.append({

                "direction":"bullish",

                "top":df["low"].iloc[i+1],

                "bottom":df["high"].iloc[i-1]

            })

        elif df["high"].iloc[i+1] < df["low"].iloc[i-1]:

            fvgs.append({

                "direction":"bearish",

                "top":df["low"].iloc[i-1],

                "bottom":df["high"].iloc[i+1]

            })

    return fvgs
