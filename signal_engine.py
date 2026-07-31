from dataclasses import dataclass

@dataclass
class Signal:
    symbol: str
    signal: str
    confidence: int
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    reason: str


def calculate_signal(direction, entry, sl, confidence, reason, symbol):
    risk = abs(entry - sl)

    if direction == "BUY":
        tp1 = entry + risk
        tp2 = entry + risk * 2
        tp3 = entry + risk * 3

    else:
        tp1 = entry - risk
        tp2 = entry - risk * 2
        tp3 = entry - risk * 3

    if confidence >= 95:
        signal = f"🔥 AGGRESSIVE {direction}"
    elif confidence >= 90:
        signal = f"🟢 STRONG {direction}"
    elif confidence >= 75:
        signal = direction
    else:
        signal = "WAIT"

    return Signal(
        symbol=symbol,
        signal=signal,
        confidence=confidence,
        entry=entry,
        stop_loss=sl,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        reason=reason
    )
