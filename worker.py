"""
SEKWAILA OMEGA X — TELEGRAM ALERT WORKER (enhanced)

- Uses send_engine_signal for richer messaging (chart links, MarkdownV2, retries)
- Reads telegram cooldown from settings_store on each scan so changes in the UI take effect
  without restarting the worker.
- Graceful shutdown handling (SIGTERM) so the process can be stopped cleanly in containers.
"""

import time
import traceback
import signal
import threading

from config import (
    ASSETS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WORKER_POLL_SECONDS,
    DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR, ALERT_COOLDOWN_MINUTES,
)
from signals.signal_engine import generate_omega_signal
from logger import get_logger

# Use central modules for persistence and Telegram handling
from database import init_db, should_alert, record_alert, log_signal
from telegram_bot import send_engine_signal
from settings_store import load_settings

logger = get_logger("WORKER")

# Shutdown flag for graceful termination
_shutdown = threading.Event()


def _handle_sigterm(signum, frame):
    logger.info("Received shutdown signal, stopping worker...")
    _shutdown.set()


signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


def scan_once():
    settings = load_settings()
    cooldown = int(settings.get("telegram", {}).get("cooldown_minutes", ALERT_COOLDOWN_MINUTES))

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
                if should_alert(symbol, bias, score, cooldown):
                    ok, info = send_engine_signal(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, symbol, result)
                    if ok:
                        logger.info("Alert sent: %s %s (score=%s)", symbol, bias, score)
                        try:
                            record_alert(symbol, bias, score)
                        except Exception as e:
                            logger.warning("Failed to record alert state for %s: %s", symbol, e)
                    else:
                        logger.warning("Telegram send returned failure for %s: %s", symbol, info)
            else:
                # If the symbol is now neutral, record neutral state so future signals can re-fire
                if not should_alert(symbol, bias, score, cooldown):
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
        send_engine_signal(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, "WORKER", {"ok": True, "bias": "NEUTRAL", "score": 0, "grade": "system"})
    except Exception:
        logger.debug("Startup Telegram announcement failed (continuing)")

    while not _shutdown.is_set():
        try:
            scan_once()
        except Exception:
            logger.error("Worker loop error:\n%s", traceback.format_exc())
        # Wait with early exit if shutdown requested
        for _ in range(WORKER_POLL_SECONDS):
            if _shutdown.is_set():
                break
            time.sleep(1)

    logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    main()
