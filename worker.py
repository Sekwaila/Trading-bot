"""
SEKWAILA OMEGA X
Background Scanner
"""

import time

from config import (
    SYMBOLS,
    SCAN_INTERVAL
)

from data.market_data import get_market_data
from signals.signal_engine import SignalEngine
from database import db
from telegram_bot import send_signal


engine = SignalEngine()


def run():

    print("=" * 50)
    print("SEKWAILA OMEGA X SCANNER STARTED")
    print("=" * 50)

    while True:

        print("\nScanning Markets...\n")

        for symbol in SYMBOLS:

            try:

                df = get_market_data(symbol)

                if df.empty:

                    print(f"{symbol} : No market data")

                    continue

                signal = engine.generate_signal(df)

                print(signal)

                if signal["signal"] != "WAIT":

                    db.add_signal(

                        symbol=symbol,

                        signal=signal["signal"],

                        confidence=signal["confidence"],

                        entry=signal["entry"],

                        stop_loss=signal["sl"],

                        tp1=signal["tp1"],

                        tp2=signal["tp2"],

                        tp3=signal["tp3"],

                        timeframe="15m",

                        reason=signal["trend"]

                    )

                    send_signal(symbol, signal)

                    print(f"{symbol} Signal Saved")

                else:

                    print(f"{symbol} WAIT")

            except Exception as e:

                print(f"{symbol} ERROR: {e}")

        print(f"\nSleeping {SCAN_INTERVAL} seconds...\n")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    run()
