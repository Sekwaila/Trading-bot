"""
SEKWAILA OMEGA X
Telegram Alerts
"""

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

from logger import get_logger

logger = get_logger("telegram")


def send_message(message: str) -> bool:
    """Send Telegram alert safely."""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            logger.error("Telegram API error: %s", data)
            return False

        logger.info("Telegram message sent.")
        return True

    except Exception:
        logger.exception("Failed to send Telegram message.")
        return False
