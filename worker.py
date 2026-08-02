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
from data.market_data import get_candles
from signals.signal_engine import SignalEngine
from telegram_bot import send_message
from logger import get_logger

logger = get_logger("worker")

engine = SignalEngine()


def run():
    logger.info("Worker started.")

    while True:

        for symbol in SYMBOLS:

            try:
                df = get_candles(symbol)

                if df.empty:
                    logger.warning("%s: no candle data", symbol)
                    continue

                signal = engine.generate_signal(df)

                if signal is None:
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

                message = (
                    f"📈 {symbol}\n"
                    f"Signal: {signal['signal']}\n"
                    f"Entry: {signal['entry']}\n"
                    f"SL: {signal['sl']}\n"
                    f"TP1: {signal['tp1']}\n"
                    f"TP2: {signal['tp2']}\n"
                    f"TP3: {signal['tp3']}\n"
                    f"Confidence: {signal['confidence']}%"
                )

                send_message(message)

                logger.info("%s signal processed.", symbol)

            except Exception as e:
                logger.exception("%s failed: %s", symbol, e)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    run()
