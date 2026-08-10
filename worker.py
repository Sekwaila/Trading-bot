"""
SEKWAILA OMEGA X — BACKGROUND WORKER

Polls signals/signal_engine.py on a timer and dispatches a Telegram alert
when a pair crosses the configured thresholds. This is the ONLY background
process in the project — it imports the same engine and the same message
formatter (telegram_bot.format_signal_message) that the dashboard uses, so
a Telegram alert and what you see in Streamlit can never disagree.

Run with:  python worker.py
Or via the Procfile's "worker" process on a host that supports one.
"""

import time

from config import (
    ASSETS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
    WORKER_POLL_SECONDS,
)

from signals.signal_engine import generate_omega_signal
from telegram_bot import send_telegram_message, format_signal_message
from logger import get_logger

logger = get_logger("WORKER")


def run_worker():
    logger.info("Starting SEKWAILA OMEGA X worker...")

    while True:
        for symbol, ticker in ASSETS.items():
            try:
                result = generate_omega_signal(
                    symbol,
                    ticker,
                    min_tf=DEFAULT_MIN_TF_AGREEMENT,
                    min_score=DEFAULT_MIN_SCORE,
                    min_rr=DEFAULT_MIN_RR,
                )

                if not result.get("ok"):
                    logger.warning(f"{symbol}: data unavailable — {result.get('reason', 'Unknown reason')}")
                    continue

                bias = result.get("bias")
                score = float(result.get("score", 0))

                if bias in ("BUY", "SELL") and score >= DEFAULT_MIN_SCORE:
                    message = format_signal_message(symbol, result)

                    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                        sent, detail = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
                        if sent:
                            logger.info(f"Telegram alert dispatched for {symbol}: {bias} {score:.1f}")
                        else:
                            logger.warning(f"Telegram dispatch failed for {symbol}: {detail}")
                    else:
                        logger.warning(f"Telegram credentials missing. Signal generated for {symbol} but no alert sent.")
                else:
                    logger.info(f"{symbol}: {bias} | score={score:.1f} | no alert")

            except Exception as exc:
                logger.exception(f"Error evaluating {symbol}: {exc}")

        logger.info(f"Worker sleeping for {WORKER_POLL_SECONDS} seconds...")
        time.sleep(WORKER_POLL_SECONDS)


if __name__ == "__main__":
    run_worker()
