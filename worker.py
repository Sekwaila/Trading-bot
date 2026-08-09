"""
SEKWAILA OMEGA X — BACKGROUND WORKER ENGINE
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

from engine import generate_omega_signal
from telegram_bot import send_telegram_message
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
                    DEFAULT_MIN_TF_AGREEMENT,
                    DEFAULT_MIN_SCORE,
                    DEFAULT_MIN_RR,
                )

                if not result.get("ok"):
                    logger.warning(
                        f"{symbol}: data unavailable — "
                        f"{result.get('reason', 'Unknown reason')}"
                    )
                    continue

                bias = result.get("bias")
                score = float(result.get("score", 0))

                if (
                    bias in ("BUY", "SELL")
                    and score >= DEFAULT_MIN_SCORE
                ):

                    message = (
                        "👑 SEKWAILA OMEGA X ALERT\n"
                        "\n"
                        f"Asset: {symbol}\n"
                        f"Signal: {bias}\n"
                        f"Score: {score:.1f}/100\n"
                        f"Grade: {result.get('grade', '-')}\n"
                        f"Entry: {result.get('entry', 0):.4f}\n"
                        f"Stop: {result.get('stop', 0):.4f}\n"
                        f"TP1: {result.get('tp1', 0):.4f}\n"
                        f"TP2: {result.get('tp2', 0):.4f}\n"
                        f"TP3: {result.get('tp3', 0):.4f}\n"
                        f"R:R: {result.get('rr', 0):.2f}\n"
                    )

                    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                        send_telegram_message(
                            TELEGRAM_BOT_TOKEN,
                            TELEGRAM_CHAT_ID,
                            message,
                        )

                        logger.info(
                            f"Telegram alert dispatched for {symbol}: "
                            f"{bias} {score:.1f}"
                        )

                    else:
                        logger.warning(
                            "Telegram credentials are missing. "
                            f"Signal generated for {symbol} but no alert sent."
                        )

                else:
                    logger.info(
                        f"{symbol}: {bias} | score={score:.1f} | "
                        "no alert"
                    )

            except Exception as exc:
                logger.exception(
                    f"Error evaluating {symbol}: {exc}"
                )

        logger.info(
            f"Worker sleeping for {WORKER_POLL_SECONDS} seconds..."
        )

        time.sleep(WORKER_POLL_SECONDS)


if __name__ == "__main__":
    run_worker()
