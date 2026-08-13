"""
SEKWAILA OMEGA X — TELEGRAM ALERT WORKER

Runs continuously, independent of the Streamlit dashboard, and pushes a
Telegram alert whenever a NEW BUY/SELL signal appears on any tracked asset.
This worker now uses the local sqlite persistence to deduplicate alerts and
logs every generated signal for audit.
"""

import time
import traceback

from config import (
    ASSETS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WORKER_POLL_SECONDS,
    DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
)
from signals.signal_engine import generate_omega_signal
from logger import get_logger

# Use central modules for persistence and Telegram handling
from database import init_db, should_alert, record_alert, log_signal
from telegram_bot import send_telegram_message, format_signal_message

logger = get_logger("WORKER")


def scan_once():
    for symbol, ticker in ASSETS.items():
        try:
            result = generate_omega_signal(
                symbol, ticker,
                min_tf=DEFAULT_MIN_TF_AGREEMENT,
                min_score=DEFAULT_MIN_SCORE,
                min_rr=DEFAULT_MIN_RR,
            )
        except Exception:
            logger.error("Signal generation failed for %s:\n%s", symbol, traceback.format_exc())
            continue

        # Always log the raw signal for auditing
        try:
            log_signal(symbol, result)
        except Exception as e:
            logger.warning("Failed to log signal for %s: %s", symbol, e)

        if not result.get("ok"):
            logger.info("%s not evaluable: %s", symbol, result.get("reason"))
            continue

        bias = result.get("bias", "NEUTRAL")
        score = float(result.get("score") or 0.0)

        try:
            if bias in ("BUY", "SELL"):
                if should_alert(symbol, bias, score):
                    message = format_signal_message(symbol, result)
                    if send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)[0]:
                        logger.info("Alert sent: %s %s (score=%s)", symbol, bias, score)
                        try:
                            record_alert(symbol, bias, score)
                        except Exception as e:
                            logger.warning("Failed to record alert state for %s: %s", symbol, e)
                    else:
                        logger.warning("Telegram send returned failure for %s", symbol)
            else:
                # If the symbol is now neutral, clear last alert state so future signals can re-fire
                if not should_alert(symbol, bias, score):
                    # Record neutral as last bias (or remove row). We'll record neutral to indicate cleared state
                    try:
                        record_alert(symbol, "NEUTRAL", score)
                    except Exception as e:
                        logger.debug("Failed to record neutral alert state for %s: %s", symbol, e)
        except Exception:
            logger.error("Error handling alert logic for %s:\n%s", symbol, traceback.format_exc())


def main():
    logger.info("SEKWAILA OMEGA X worker starting — polling every %ss", WORKER_POLL_SECONDS)
    # Ensure DB schema exists
    try:
        init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)

    # Announce startup to Telegram (best-effort)
    try:
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, "🟡 SEKWAILA OMEGA X worker started and monitoring markets.")
    except Exception:
        logger.debug("Startup Telegram announcement failed (continuing)")

    while True:
        try:
            scan_once()
        except Exception:
            logger.error("Worker loop error:\n%s", traceback.format_exc())
        time.sleep(WORKER_POLL_SECONDS)


if __name__ == "__main__":
    main()
