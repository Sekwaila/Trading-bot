import pandas as pd


def detect_trend(df):

    ema50 = df["close"].ewm(span=50).mean()

    ema200 = df["close"].ewm(span=200).mean()

    if ema50.iloc[-1] > ema200.iloc[-1]:
        return "bullish"

    elif ema50.iloc[-1] < ema200.iloc[-1]:
        return "bearish"

    return "neutral"


def detect_signal(df):

    trend = detect_trend(df)

    last = df.iloc[-1]

    previous = df.iloc[-2]

    confidence = 50

    reasons = []

    if trend == "bullish":

        if last.close > previous.high:
            confidence += 20
            reasons.append("Break of Structure")

        if last.close > last.open:
            confidence += 10
            reasons.append("Bullish Candle")

    elif trend == "bearish":

        if last.close < previous.low:
            confidence += 20
            reasons.append("Break of Structure")

        if last.close < last.open:
            confidence += 10
            reasons.append("Bearish Candle")

    if confidence >= 95:

        signal = f"🔥 AGGRESSIVE {'BUY' if trend=='bullish' else 'SELL'}"

    elif confidence >= 90:

        signal = f"🟢 STRONG {'BUY' if trend=='bullish' else 'SELL'}"

    elif confidence >= 75:

        signal = "BUY" if trend=="bullish" else "SELL"

    else:

        signal = "WAIT"

    return {
        "trend": trend,
        "signal": signal,
        "confidence": confidence,
        "reason": ", ".join(reasons)
    }
