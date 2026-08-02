"""
SEKWAILA OMEGA X
Telegram Bot
"""

import requests

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from logger import get_logger

logger = get_logger("telegram")


class TelegramBot:

    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID

    def send(self, message):

        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=15,
            )

            response.raise_for_status()

            logger.info("Telegram message sent.")

            return True

        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False


telegram = TelegramBot()
