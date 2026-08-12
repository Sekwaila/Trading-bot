"""
SEKWAILA OMEGA X — TELEGRAM ALERT WORKER

Runs continuously, independent of the Streamlit dashboard, and pushes a
Telegram alert whenever a NEW BUY/SELL signal appears on any tracked asset.

Deploy this as a SEPARATE Railway service from the same repo (different
start command) so it keeps scanning and alerting even when nobody has the
dashboard open on their phone.
"""

import time
import traceback
import requests

from config import (
    ASSETS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WORKER_POLL_SECONDS,
    DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
)
from signals.signal_engine import generate_omega_signal
from logger import get_logger

logger = get_logger("WORKER")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Tracks the last alerted bias per symbol so we only alert when a signal is
# NEW, not on every poll cycle. Resets to empty if the worker restarts —
# that's fine, worst case is one repeat alert after a redeploy.
_last_alerted_bias = {}


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — cannot send alert.")
        return False
    try:
        resp = requests.post(
            TELEGRAM_API_URL,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("Telegram send failed (%s): %s", resp.status_code, resp.text)
            return False
        return True
    except Exception as exc:
        logger.error("Telegram send exception: %s", exc)
        return False


def format_alert(result):
    symbol = result["symbol"]
    bias = result["bias"]
    icon = "🟢 BUY" if bias == "BUY" else "🔴 SELL"
    lines = [
        f"*{icon} — {symbol}*",
        f"Score: {result['score']}/100",
        f"Entry: {result['entry']:.4f}",
        f"Stop: {result['stop']:.4f}",
        f"TP1: {result['tp1']:.4f}",
        f"TP2: {result['tp2']:.4f}",
        f"TP3: {result['tp3']:.4f}",
        f"R:R: {result['rr']:.2f}",
        f"Structure: {result['structure']}",
        f"Session: {result['session']}",
    ]
    return "\n".join(lines)


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

        if not result.get("ok"):
            logger.info("%s not evaluable: %s", symbol, result.get("reason"))
            continue

        bias = result.get("bias", "NEUTRAL")
        previous = _last_alerted_bias.get(symbol)

        if bias in ("BUY", "SELL") and bias != previous:
            message = format_alert(result)
            if send_telegram_message(message):
                logger.info("Alert sent: %s %s (score=%s)", symbol, bias, result.get("score"))
                _last_alerted_bias[symbol] = bias
        elif bias == "NEUTRAL" and previous is not None:
            # Signal faded back to neutral — clear state so a future
            # BUY/SELL on this symbol triggers a fresh alert.
            _last_alerted_bias[symbol] = None


def main():
    logger.info("SEKWAILA OMEGA X worker starting — polling every %ss", WORKER_POLL_SECONDS)
    send_telegram_message("🟡 SEKWAILA OMEGA X worker started and monitoring markets.")
    while True:
        try:
            scan_once()
        except Exception:
            logger.error("Worker loop error:\n%s", traceback.format_exc())
        time.sleep(WORKER_POLL_SECONDS)


if __name__ == "__main__":
    main()
