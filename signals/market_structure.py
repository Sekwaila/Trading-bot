    # ==========================
    # Smart Money Market Structure
    # ==========================

    def market_structure(self, df, lookback=3):

        df = df.copy()

        df["swing_high"] = False
        df["swing_low"] = False

        for i in range(lookback, len(df) - lookback):

            high = df["high"].iloc[i]
            low = df["low"].iloc[i]

            if high == max(
                df["high"].iloc[i - lookback:i + lookback + 1]
            ):
                df.loc[df.index[i], "swing_high"] = True

            if low == min(
                df["low"].iloc[i - lookback:i + lookback + 1]
            ):
                df.loc[df.index[i], "swing_low"] = True

        swing_highs = df[df["swing_high"]]
        swing_lows = df[df["swing_low"]]

        last_high = None
        last_low = None

        if not swing_highs.empty:
            last_high = float(swing_highs.iloc[-1]["high"])

        if not swing_lows.empty:
            last_low = float(swing_lows.iloc[-1]["low"])

        return {
            "last_high": last_high,
            "last_low": last_low,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
        }
