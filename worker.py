"""
SEKWAILA OMEGA X – Background Scanner
Runs continuously, scans all symbols, manages trades, sends Telegram alerts.
Features:
- Per‑symbol error isolation (one failure doesn't stop others)
- Retry on market data download (3 attempts)
- Scan time logging
- Signal counter + error counter
- Graceful shutdown on KeyboardInterrupt
- Clean, readable console summary
- Passes symbol to signal engine
"""

import time
import sys
from datetime import datetime

from config import SYMBOLS, TIMEFRAME, SCAN_INTERVAL
from database import db
from data.market_data import get_candles
from signals.signal_engine import SignalEngine
from trade_manager import trade_manager
from telegram_bot import telegram

engine = SignalEngine()


def scan_market():
    """Main scanning loop."""
    print("=" * 50)
    print("SEKWAILA OMEGA X Scanner Started")
    print("=" * 50)

    try:
        while True:
            start_time = time.time()
            errors = 0
            signals_found = 0
            results = []   # for summary

            # ----- 1. Check open trades -----
            try:
                trade_manager.check_open_trades()
            except Exception as e:
                print(f"Trade manager error: {e}")
                errors += 1

            # ----- 2. Scan each symbol (isolated) -----
            for symbol in SYMBOLS:
                try:
                    # ---- Retry market data (max 3 attempts) ----
                    df = None
                    for attempt in range(3):
                        df = get_candles(symbol)
                        if df is not None and not df.empty:
                            break
                        print(f"{symbol}: No data (attempt {attempt+1}/3), retrying...")
                        time.sleep(2)

                    if df is None or df.empty:
                        print(f"{symbol}: ❌ No data after retries")
                        results.append(f"{symbol} ❌ No Data")
                        continue

                    # ---- Generate signal (pass symbol) ----
                    signal = engine.generate_signal(df, symbol=symbol)   # <-- symbol passed

                    if signal is None:
                        print(f"{symbol}: No signal")
                        results.append(f"{symbol} ✔ No Signal")
                        continue

                    # ---- Save signal ----
                    saved = db.save_signal(
                        symbol=symbol,
                        signal=signal["signal"],
                        confidence=signal["confidence"],
                        entry=signal["entry"],
                        stop_loss=signal["sl"],
                        tp1=signal["tp1"],
                        tp2=signal["tp2"],
                        tp3=signal["tp3"],
                        timeframe=TIMEFRAME,
                    )

                    if saved:
                        signals_found += 1
                        print(f"✅ NEW SIGNAL -> {symbol} {signal['signal']}")
                        # Send Telegram alert
                        try:
                            telegram.send_signal(symbol, signal)
                        except Exception as e:
                            print(f"Telegram error: {e}")
                            errors += 1
                        results.append(f"{symbol} ✔ {signal['signal']}")
                    else:
                        print(f"{symbol}: Duplicate (skipped)")
                        results.append(f"{symbol} ✔ Duplicate")

                except Exception as e:
                    errors += 1
                    print(f"Symbol {symbol} error: {e}")
                    results.append(f"{symbol} ❌ Error")
                    continue

            # ----- 3. Summary -----
            elapsed = time.time() - start_time
            print("\n" + "=" * 50)
            print(f"SEKWAILA OMEGA X  {datetime.now().strftime('%H:%M')}")
            print("=" * 50)
            for line in results:
                print(line)
            print("-" * 50)
            print(f"Signals : {signals_found}")
            print(f"Errors  : {errors}")
            print(f"Time    : {elapsed:.2f} sec")
            print(f"Next scan: {SCAN_INTERVAL} sec")
            print("=" * 50 + "\n")

            # ----- 4. Sleep until next scan -----
            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    scan_market()
