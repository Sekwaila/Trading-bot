import os
import asyncio
from telegram import Bot
from logger import logger

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_telegram_signal_async(signal_data: dict):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram token or chat ID not set. Skipping message.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    msg = (
        f"👑 *SEKWAILA OMEGA X SIGNAL*\n"
        f"Asset: *{signal_data.get('symbol', 'XAUUSD')}*\n"
        f"Action: *{signal_data['bias']}*\n"
        f"Confluence: *{signal_data['probability']}%*\n\n"
        f"Entry: `{signal_data['entry']:.2f}`\n"
        f"SL: `{signal_data['stop_loss']:.2f}`\n"
        f"TP1: `{signal_data['tp1']:.2f}`\n"
        f"TP2: `{signal_data['tp2']:.2f}`\n"
        f"TP3: `{signal_data['tp3']:.2f}`\n\n"
        f"_{signal_data['ai_narrative']}_"
    )
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
        logger.info("Telegram signal broadcast successfully.")
    except Exception as e:
        logger.error(f"Failed sending Telegram alert: {e}")

def send_telegram_signal(signal_data: dict):
    asyncio.run(send_telegram_signal_async(signal_data))
