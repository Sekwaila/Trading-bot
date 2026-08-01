import time

from config import SYMBOLS, SCAN_INTERVAL

from data.market_data import get_market_data

from signals.signal_engine import SignalEngine

from database import save_trade


engine = SignalEngine()


def run():

    while True:

        print("Scanning markets...")

        for symbol in SYMBOLS:

            try:

                df = get_market_data(symbol)

                signal = engine.generate_signal(df)

                print(symbol, signal)

                save_trade(symbol, signal)

            except Exception as e:

                print(symbol, e)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    run()
