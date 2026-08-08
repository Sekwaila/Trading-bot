"""
SEKWAILA OMEGA X — BACKGROUND WORKER ENGINE
"""
import time
from config import ASSETS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE
from signals.signal_engine import generate_omega_signal
from telegram_bot import send_telegram_message
from logger import get_logger

logger = get_logger("WORKER")

def run_worker():
    logger.info("Starting worker loop...")
    while True:
        for symbol, ticker in ASSETS.items():
            try:
                res = generate_omega_signal(symbol, ticker, DEFAULT_MIN_TF_AGREEMENT)
                if res["ok"] and res["bias"] in ("BUY", "SELL") and res["score"] >= DEFAULT_MIN_SCORE:
                    msg = (
                        f"👑 SEKWAILA OMEGA X ALERT\n"
                        f"Asset: {symbol}\n"
                        f"Signal: {res['bias']}\n"
                        f"Score: {res['score']}/100\n"
                        f"Entry: {res['entry']:.4f}\n"
                        f"Stop: {res['stop']:.4f}\n"
                        f"TP2: {res['tp2']:.4f}"
                    )
                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
                    logger.info(f"Dispatched alert for {symbol}")
            except Exception as e:
                logger.error(f"Error evaluating {symbol}: {e}")
        time.sleep(300)

if __name__ == "__main__":
    run_worker()
