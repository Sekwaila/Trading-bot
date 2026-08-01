"""
SEKWAILA OMEGA X
Background Scanner
"""

import time

from config import (
    SYMBOLS,
    TIMEFRAME,
    SCAN_INTERVAL,
)

from database import db
from telegram_bot import send_signal
from data.market_data import get_candles
from signals.signal_engine import SignalEngine


engine = SignalEngine()


def run():

    print("SEKWAILA OMEGA X Scanner Started")

    while True:

        for symbol in SYMBOLS:

            try:

                df = get_candles(symbol)

                if df.empty:
                    print(f"{symbol}: No candle data")
                    continue

                signal = engine.generate_signal(df)

                if signal is None:
                    print(f"{symbol}: Not enough data")
                    continue

                db.save_signal(

                    symbol=symbol,

                    signal=signal["signal"],

                    confidence=signal["confidence"],

                    entry=signal["entry"],

                    stop_loss=signal["sl"],

                    tp1=signal["tp1"],

                    tp2=signal["tp2"],

                    tp3=signal["tp3"],

                    timeframe=TIMEFRAME

                )

                send_signal(symbol, signal)

                print(f"{symbol}: {signal['signal']}")

            except Exception as e:

                print(f"{symbol}: {e}")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    run()
