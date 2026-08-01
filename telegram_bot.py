"""
SEKWAILA OMEGA X
Telegram Alerts
"""

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {

        "chat_id": TELEGRAM_CHAT_ID,

        "text": message,

        "parse_mode": "Markdown"

    }

    try:

        response = requests.post(

            url,

            json=payload,

            timeout=10

        )

        return response.status_code == 200

    except Exception as e:

        print(e)

        return False


def send_signal(symbol, signal):

    message = f"""
🚨 *SEKWAILA OMEGA X*

📈 *{symbol}*

Signal: *{signal['signal']}*

Confidence: *{signal['confidence']}%*

Entry: `{signal['entry']}`

Stop Loss: `{signal['sl']}`

TP1: `{signal['tp1']}`

TP2: `{signal['tp2']}`

TP3: `{signal['tp3']}`
"""

    return send_telegram(message)
