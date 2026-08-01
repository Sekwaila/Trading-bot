import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)


def send_signal(symbol, signal):

    msg = f"""
📈 {symbol}

Signal: {signal['signal']}

Confidence: {signal['confidence']}%

Entry: {signal['entry']}

SL: {signal['sl']}

TP1: {signal['tp1']}

TP2: {signal['tp2']}

TP3: {signal['tp3']}
"""

    send_telegram(msg)
