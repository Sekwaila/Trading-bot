"""
SEKWAILA OMEGA X — TELEGRAM BROADCASTER
"""
import requests
from logger import get_logger

logger = get_logger("TELEGRAM")

def send_telegram_message(token: str, chat_id: str, message: str) -> tuple[bool, str]:
    if not token or not chat_id:
        return False, "Bot token and Chat ID are required."
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=12)
        if resp.ok:
            return True, "Signal dispatched to Telegram."
        return False, f"Telegram Error {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        logger.error(f"Telegram dispatch failed: {exc}")
        return False, f"Connection failure: {exc}"
