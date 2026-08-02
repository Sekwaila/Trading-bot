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

from logger import get_logger
from database import db
from telegram_bot import send_message
from data.market_data import get_candles
from signals.signal_engine import SignalEngine

logger = get_logger("worker")

engine = SignalEngine()


def scan_symbol(symbol: str):
    try:
        df = get_candles(symbol)

        if df.empty:
            logger.warning("%s: No candle data", symbol)
            return

        signal = engine.generate_signal(df)

        if signal is None:
            logger.info("%s: No signal", symbol)
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
📈 {symbol}

Signal: {signal['signal']}
Confidence: {signal['confidence']}%

Entry: {signal['entry']}
SL: {signal['sl']}
TP1: {signal['tp1']}
TP2: {signal['tp2']}
TP3: {signal['tp3']}
"""

        send_message(message)

        logger.info("%s signal saved and sent.", symbol)

    except Exception:
        logger.exception("Scanner failed for %s", symbol)


def run():
    logger.info("Scanner started.")

    while True:

        for symbol in SYMBOLS:
            scan_symbol(symbol)

        logger.info("Sleeping %s seconds...", SCAN_INTERVAL)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    run()
