"""
SEKWAILA OMEGA X – Telegram Alerts
Features:
- Config variable match (TELEGRAM_BOT_TOKEN)
- HTML formatting with clear icons and structure
- Safe value handling using .get()
- Retry logic (3 attempts)
- Timestamp, Grade, Risk:Reward, and BUY/SELL icons
- Graceful fallback if config missing
"""

import requests
from datetime import datetime
from time import sleep

from config import (
    TELEGRAM_BOT_TOKEN,   # FIXED: correct config key
    TELEGRAM_CHAT_ID,
)


class TelegramBot:

    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.max_retries = 3

    def send_signal(self, symbol, signal):
        """
        Send a signal alert to Telegram.
        signal: dict with keys: signal, entry, sl, tp1, tp2, tp3,
                confidence, grade, diagnostics (rsi, macd, atr)
        """
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("Telegram: missing TOKEN or CHAT_ID – alert disabled")
            return False

        # ---------- Prepare values safely ----------
        sig = signal.get("signal", "N/A")
        entry = signal.get("entry", 0)
        sl = signal.get("sl", 0)
        tp1 = signal.get("tp1", 0)
        tp2 = signal.get("tp2", 0)
        tp3 = signal.get("tp3", 0)
        confidence = signal.get("confidence", 0)
        grade = signal.get("grade", "N/A")

        # Diagnostics
        diag = signal.get("diagnostics", {})
        rsi = diag.get("rsi", "N/A")
        macd = diag.get("macd", "N/A")
        atr = diag.get("atr", "N/A")

        # Risk:Reward calculation (based on TP1)
        if sig == "BUY":
            risk = entry - sl if sl else 1
            reward = tp1 - entry if tp1 else 1
        elif sig == "SELL":
            risk = sl - entry if sl else 1
            reward = entry - tp1 if tp1 else 1
        else:
            risk = reward = 1
        rr = reward / risk if risk != 0 else 0

        # Icon for signal
        icon = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "⚪"

        # Timestamp
        ts = datetime.now().strftime("%d %b %Y %H:%M")

        # ---------- Build message (HTML) ----------
        message = f"""
<b>📈 SEKWAILA OMEGA X</b>  <i>{ts}</i>

<b>{icon} {sig}  {symbol}</b>

💰 Entry:   <code>{entry:.5f}</code>
🛑 SL:     <code>{sl:.5f}</code>
🎯 TP1:    <code>{tp1:.5f}</code>
🎯 TP2:    <code>{tp2:.5f}</code>
🎯 TP3:    <code>{tp3:.5f}</code>

⭐ Grade: <b>{grade}</b>   |   Confidence: <b>{confidence}%</b>

📊 Risk : Reward  <b>1 : {rr:.2f}</b>

📈 RSI:   {rsi}
📉 MACD:  {macd}
📏 ATR:   {atr}
"""

        # ---------- Send with retries ----------
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    print(f"Telegram sent: {symbol} ({sig})")
                    return True
                else:
                    print(f"Telegram attempt {attempt+1} failed: {resp.text}")
            except Exception as e:
                print(f"Telegram attempt {attempt+1} error: {e}")
            sleep(2)  # wait before retry

        print(f"Telegram: failed after {self.max_retries} attempts")
        return False


# Singleton instance
telegram = TelegramBot()
