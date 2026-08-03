"""
SEKWAILA OMEGA X
Background Scanner
"""

import time

from config import SYMBOLS, TIMEFRAME, SCAN_INTERVAL
from database import db
from data.market_data import get_candles
from signals.signal_engine import SignalEngine
from trade_manager import trade_manager
from telegram_bot import telegram

engine = SignalEngine()


def scan_market():

    print("=" * 50)
    print("SEKWAILA OMEGA X Scanner Started")
    print("=" * 50)

    while True:

        try:

            # Check open trades
            trade_manager.check_open_trades()

            # Scan market
            for symbol in SYMBOLS:

                df = get_candles(symbol)

                if df.empty:
                    print(f"{symbol}: No data")
                    continue

                signal = engine.generate_signal(df)

                if signal is None:
                    print(f"{symbol}: No signal")
                    continue

                saved = db.save_signal(
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

                if saved:
                    print(f"NEW SIGNAL -> {symbol} {signal['signal']}")
                    telegram.send_signal(symbol, signal)
                else:
                    print(f"Duplicate skipped -> {symbol}")

        except Exception as e:

            print("Scanner Error:", e)

        print(f"Sleeping for {SCAN_INTERVAL} seconds...\n")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    scan_market()
