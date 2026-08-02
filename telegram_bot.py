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
    """
    Send a Telegram message.
    Returns True on success, False otherwise.
    """

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("ok"):
            logger.info("Telegram alert sent.")
            return True

        logger.error("Telegram API error: %s", data)
        return False

    except Exception as e:
        logger.exception("Telegram send failed: %s", e)
        return False
