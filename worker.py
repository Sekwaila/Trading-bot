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

engine = SignalEngine()


def scan_market():

    print("Scanner started...")

    while True:

        try:

            # ---------------------------------
            # Check existing OPEN trades
            # ---------------------------------

            trade_manager.check_open_trades()

            # ---------------------------------
            # Scan for new signals
            # ---------------------------------

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
                    f"{symbol}: {signal['signal']} "
                    f"@ {signal['entry']} "
                    f"({signal['confidence']}%)"
                )

        except Exception as e:

            print("Scanner error:", e)

        # Wait until next scan
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":

    scan_market()
