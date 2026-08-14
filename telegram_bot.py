import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def send_telegram_signal(symbol: str, bias: str, entry: float, sl: float, tp1: float, tp2: float, reason: str = "") -> bool:
    """
    Sends rich SMC signal messages to Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("[Telegram] Bot Token not configured.")
        return False

    emoji = "🟢 BUY SIGNAL" if bias.upper() in ["BUY", "BULLISH"] else "🔴 SELL SIGNAL"

    message = (
        f"⚡ *SEKWAILA OMEGA X SIGNAL*\n"
        f"----------------------------\n"
        f"{emoji}\n"
        f"🔥 *Asset:* `{symbol}`\n"
        f"📍 *Entry:* `{entry:.2f}`\n"
        f"🛑 *Stop Loss:* `{sl:.2f}`\n"
        f"🎯 *Take Profit 1:* `{tp1:.2f}`\n"
        f"🎯 *Take Profit 2:* `{tp2:.2f}`\n"
        f"💡 *Setup:* _{reason}_\n"
        f"----------------------------\n"
        f"⚠️ _Signal-only mode. Manage risk manually._"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=8)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"[Telegram] Broadcast error: {e}")
        return False
