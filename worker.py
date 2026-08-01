"""
SEKWAILA OMEGA X
Background Scanner
"""

import time

from config import SYMBOLS, SCAN_INTERVAL

from data.market_data import get_market_data
from signals.signal_engine import SignalEngine
from database import db


engine = SignalEngine()


def run():

    print("SEKWAILA OMEGA X Scanner Started")

    while True:

        print("Scanning markets...")

        for symbol in SYMBOLS:

            try:

                df = get_market_data(symbol)

                if df.empty:
                    print(f"{symbol}: No market data")
                    continue

                signal = engine.generate_signal(df)

                print(symbol, signal)

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

                    print(f"{symbol}: Signal saved")

            except Exception as e:

                print(symbol, e)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    run()
