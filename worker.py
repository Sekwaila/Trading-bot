"""
SEKWAILA OMEGA X
24/7 Background Worker
"""

import time

from config import (
    SYMBOLS,
    TIMEFRAME,
    SCAN_INTERVAL,
)

from database import db
from data.market_data import get_candles
from signals.signal_engine import SignalEngine
from telegram_bot import telegram

engine = SignalEngine()


def scan_symbol(symbol):

    df = get_candles(symbol)

    if df.empty:
        return

    signal = engine.generate_signal(df)

    if signal is None:
        return

    if db.signal_exists(
        symbol,
        signal["signal"],
        signal["entry"],
    ):
        return

    db.save_signal(
        symbol=symbol,
        signal=signal["signal"],
        confidence=signal["confidence"],
        entry=signal["entry"],
        stop_loss=signal["sl"],
        tp1=signal["tp1"],
        tp2=signal["tp2"],
        tp3=signal["tp3"],
        timeframe=TIMEFRAME,
    )

    message = f"""
📈 SEKWAILA OMEGA X

{symbol}

Signal: {signal['signal']}

Entry: {signal['entry']}

SL: {signal['sl']}

TP1: {signal['tp1']}
TP2: {signal['tp2']}
TP3: {signal['tp3']}

Confidence: {signal['confidence']}%

RSI: {signal['rsi']}
MACD: {signal['macd']}
ATR: {signal['atr']}
"""

    telegram.send(message)

    print(f"{symbol} {signal['signal']} sent")


def run():

    print("===================================")
    print(" SEKWAILA OMEGA X WORKER STARTED ")
    print("===================================")

    while True:

        for symbol in SYMBOLS:

            try:
                scan_symbol(symbol)

            except Exception as e:
                print(f"{symbol}: {e}")

        print(f"Sleeping {SCAN_INTERVAL} seconds...\n")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    run()
