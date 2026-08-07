import time
from data.market_data import fetch_institutional_data
from signals.signal_engine import run_quantitative_smc_engine
from database import init_db, save_signal
from telegram_bot import send_telegram_signal
from logger import logger

def execution_loop():
    init_db()
    logger.info("Worker loop started.")
    last_signal_time = None

    while True:
        try:
            tf_data, data_integrity = fetch_institutional_data()
            results = run_quantitative_smc_engine(tf_data, data_integrity)

            if results["data_ok"] and results["passed_filters"] and results["bias"] in ("BUY", "SELL"):
                curr_candle_time = results["df_15m"].index[-1]
                if last_signal_time != curr_candle_time:
                    logger.info(f"New Signal Detected: {results['bias']} @ {results['entry']}")
                    save_signal(results)
                    send_telegram_signal(results)
                    last_signal_time = curr_candle_time

        except Exception as e:
            logger.error(f"Execution loop error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    execution_loop()
