def generate_signal(self, df, symbol="EUR/USD", timeframe="1H"):

    if df is None or len(df) < 50:
        return None

    df = df.copy()

    # Fix Yahoo Finance duplicate/MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.loc[:, ~df.columns.duplicated()]

    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['rsi'] = self._rsi(df['close'], 14)
    df['atr'] = self._atr(df, 14)

    df = df.dropna()

    if len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]


    # Convert Pandas objects to real floats
    ema20_last = float(np.asarray(last["ema20"]).flatten()[0])
    ema50_last = float(np.asarray(last["ema50"]).flatten()[0])

    ema20_prev = float(np.asarray(prev["ema20"]).flatten()[0])
    ema50_prev = float(np.asarray(prev["ema50"]).flatten()[0])

    rsi = float(np.asarray(last["rsi"]).flatten()[0])
    price = float(np.asarray(last["close"]).flatten()[0])
    atr = float(np.asarray(last["atr"]).flatten()[0])


    if ema20_last > ema50_last and ema20_prev <= ema50_prev:
        direction = "BUY"

    elif ema20_last < ema50_last and ema20_prev >= ema50_prev:
        direction = "SELL"

    else:

        if rsi < 30:
            direction = "BUY"

        elif rsi > 70:
            direction = "SELL"

        else:
            return None


    if direction == "BUY":

        sl = price - atr * 1.5
        tp1 = price + atr * 1.5
        tp2 = price + atr * 2.5
        tp3 = price + atr * 4

    else:

        sl = price + atr * 1.5
        tp1 = price - atr * 1.5
        tp2 = price - atr * 2.5
        tp3 = price - atr * 4


    entry = price - atr * 0.01 if direction == "BUY" else price + atr * 0.01


    confidence = 60 + (abs(rsi - 50) / 50) * 20

    if abs(ema20_last - ema50_last) / ema50_last > 0.001:
        confidence += 10

    confidence = min(95, confidence)


    grade = (
        "A" if confidence >= 85 else
        "B" if confidence >= 70 else
        "C" if confidence >= 60 else
        "D"
    )


    return {

        "signal": direction,

        "confidence": round(confidence,2),

        "entry": round(entry,5),

        "sl": round(sl,5),

        "tp1": round(tp1,5),

        "tp2": round(tp2,5),

        "tp3": round(tp3,5),

        "grade": grade,

        "lot": 0.01,

        "risk": round(0.01 * abs(entry-sl)*10000,2),

        "diagnostics": {

            "rsi": round(rsi,2),

            "atr": round(atr,5),

            "ema20": round(ema20_last,5),

            "ema50": round(ema50_last,5)

        },

        "reasons": [

            f"EMA crossover {direction}",

            f"RSI {rsi:.1f}"

        ]

    }
