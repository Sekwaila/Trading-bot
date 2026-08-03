"""
SEKWAILA OMEGA X
Telegram Alerts
"""

import requests

from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)


class TelegramBot:

    def __init__(self):

        self.base_url = (
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
        )

    def send_signal(self, symbol, signal):

        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return False

        message = f"""
📈 SEKWAILA OMEGA X

💹 Symbol: {symbol}

📊 Signal: {signal['signal']}

🎯 Confidence: {signal['confidence']}%

💰 Entry: {signal['entry']}

🛑 Stop Loss: {signal['sl']}

🎯 TP1: {signal['tp1']}
🎯 TP2: {signal['tp2']}
🎯 TP3: {signal['tp3']}

📈 RSI: {signal['rsi']}
📉 MACD: {signal['macd']}
📏 ATR: {signal['atr']}
"""

        try:

            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                },
                timeout=15,
            )

            if response.status_code == 200:
                print(f"Telegram sent: {symbol}")
                return True

            print(response.text)
            return False

        except Exception as e:

            print("Telegram Error:", e)
            return False


telegram = TelegramBot()
