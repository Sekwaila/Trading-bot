"""
SEKWAILA OMEGA X
Telegram Alerts
"""

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


def send_signal(symbol, signal):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    message = f"""
🚨 SEKWAILA OMEGA X

{symbol}

Signal: {signal['signal']}

Confidence: {signal['confidence']}%

Entry: {signal['entry']}

Stop Loss: {signal['sl']}

TP1: {signal['tp1']}

TP2: {signal['tp2']}

TP3: {signal['tp3']}
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=10
    )
