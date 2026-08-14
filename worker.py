import time
from config import ASSETS, WORKER_POLL_SECONDS, SIGNAL_COOLDOWN_SECONDS
from Signals.signal_engine import generate_omega_signal
from telegram_bot import send_telegram_signal

last_signal_times = {}

def start_worker():
    print("🚀 SEKWAILA OMEGA X Signal Engine Active...")
    
    while True:
        try:
            for symbol in ASSETS.keys():
                signal = generate_omega_signal(symbol)
                
                if signal.get("ok") and signal.get("bias") in ["BUY", "SELL"]:
                    now = time.time()
                    last_time = last_signal_times.get(symbol, 0)

                    # Cooldown check
                    if now - last_time >= SIGNAL_COOLDOWN_SECONDS:
                        send_telegram_signal(
                            symbol=symbol,
                            bias=signal["bias"],
                            entry=signal["entry_price"],
                            sl=signal["stop_loss"],
                            tp1=signal["tp1"],
                            tp2=signal["tp2"],
                            reason=signal["reason"]
                        )
                        last_signal_times[symbol] = now

            time.sleep(WORKER_POLL_SECONDS)
        except Exception as e:
            print(f"[Worker Exception] {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
