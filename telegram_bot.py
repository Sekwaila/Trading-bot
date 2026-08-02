"""
SEKWAILA OMEGA X
Telegram Bot
"""

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from logger import get_logger

logger = get_logger("telegram")


def send_message(message: str):

    if not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token not configured.")
        return False

    if not TELEGRAM_CHAT_ID:
        logger.warning("Telegram chat ID not configured.")
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

        result = response.json()

        if result.get("ok"):
            logger.info("Telegram message sent.")
            return True

        logger.error(result)
        return False

    except Exception as e:
        logger.exception(e)
        return False
