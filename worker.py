"""
SEKWAILA OMEGA X
Background Scanner
"""

import time

from config import SYMBOLS, TIMEFRAME
from database import db
from data.market_data import get_candles
from signals.signal_engine import SignalEngine

engine = SignalEngine()


def scan_market():
    print("Scanner started...")

    while True:

        try:

            for symbol in SYMBOLS:

                df = get_candles(symbol)

                if df.empty:
                    print(f"{symbol}: no data")
                    continue

                signal = engine.generate_signal(df)

                if signal is None:
                    print(f"{symbol}: no signal")
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
                    timeframe=TIMEFRAME,
                )

                print(
                    f"{symbol}: {signal['signal']} @ {signal['entry']} ({signal['confidence']}%)"
                )

        except Exception as e:
            print("Scanner error:", e)

        # Scan every 5 minutes
        time.sleep(300)


if __name__ == "__main__":
    scan_market()
