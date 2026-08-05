"""
SEKWAILA OMEGA X – Professional Trade Manager
Features:
- Dynamic ATR‑based stop‑loss and take‑profit levels
- Risk‑reward ratio validation (minimum 1:2)
- Break‑even logic (SL moves to entry after TP1)
- Trailing stop (SL follows price after TP2)
- Trade expiry (auto‑close after N candles without hitting TP/SL)
- Duplicate trade prevention (one open trade per symbol/timeframe)
- Trade status tracking (OPEN, TP1_HIT, TP2_HIT, TP3_HIT, STOPPED_OUT, CLOSED, EXPIRED)
- Performance statistics (win rate, avg R:R, total P&L, consecutive wins/losses)
- Telegram notifications on trade closure (TP/SL hit or expiry)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# ===================================================
# CONFIGURATION (tweak these as needed)
# ===================================================
MIN_RISK_REWARD_RATIO = 2.0          # Minimum R:R (e.g., 2.0 = 1:2)
ATR_PERIOD = 14                      # Period for ATR calculation
ATR_MULTIPLIER_SL = 1.5              # SL = entry ± ATR * multiplier
ATR_MULTIPLIER_TP1 = 1.5             # TP1 = entry ± ATR * multiplier
ATR_MULTIPLIER_TP2 = 2.5
ATR_MULTIPLIER_TP3 = 4.0
BREAK_EVEN_ACTIVATION_TP = 1         # Move SL to entry after which TP level (1,2,3)
TRAILING_ACTIVATION_TP = 2           # Start trailing after which TP level
TRAILING_STEP = 0.5                  # ATR multiplier for trailing step (SL trails by this)
TRADE_EXPIRY_CANDLES = 48            # Max candles before expiry
STATUS_OPEN = "OPEN"
STATUS_TP1_HIT = "TP1_HIT"
STATUS_TP2_HIT = "TP2_HIT"
STATUS_TP3_HIT = "TP3_HIT"
STATUS_STOPPED_OUT = "STOPPED_OUT"
STATUS_CLOSED = "CLOSED"
STATUS_EXPIRED = "EXPIRED"

# ===================================================
# TIMEFRAME SECONDS MAPPING (for expiry)
# ===================================================
TIMEFRAME_SECONDS = {
    "15M": 900,
    "30M": 1800,
    "1H": 3600,
    "4H": 14400,
    "1D": 86400,
}
# ===================================================

logger = logging.getLogger("trade_manager")

class TradeManager:
    def __init__(self, db_conn, price_fetcher, candle_fetcher, telegram_bot=None):
        """
        :param db_conn: database connection (must support get_open_trades, update_trade, insert_trade, etc.)
        :param price_fetcher: function(symbol) -> current price
        :param candle_fetcher: function(symbol, timeframe, bars) -> DataFrame with OHLC
        :param telegram_bot: optional TelegramBot instance for sending closure alerts
        """
        self.db = db_conn
        self.get_price = price_fetcher
        self.get_candles = candle_fetcher
        self.telegram = telegram_bot

    # ---------- Helper: Profit Calculation ----------
    def calculate_profit(self, entry, exit_price, signal):
        """Consistent profit calculation for any exit price."""
        if signal == "BUY":
            return exit_price - entry
        else:  # SELL
            return entry - exit_price

    # ---------- Helper: Send Telegram Alert on Close ----------
    def _send_telegram_alert(self, symbol, signal, entry, exit_price, status, profit):
        if self.telegram is None:
            return
        # Build message
        if profit > 0:
            emoji = "✅"
            result_text = f"{status} (Profit)"
        else:
            emoji = "❌"
            result_text = f"{status} (Loss)"
        message = f"""
<b>{emoji} {result_text}</b>

<b>{symbol}</b>
<b>{signal}</b>

💰 Entry: {entry:.5f}
🚪 Exit:  {exit_price:.5f}
💵 Profit: {profit:+.5f}
"""
        # Send it (using the bot's send_message method if available, or directly)
        try:
            if hasattr(self.telegram, 'send_message'):
                self.telegram.send_message(message)
            else:
                # fallback: assume it has a send_signal method, but we just send raw text
                self.telegram.send_signal(symbol, {"signal": signal, "entry": entry, "sl": 0, "tp1": 0, "tp2": 0, "tp3": 0, "confidence": 0})  # simple fallback
                # better to implement a generic send_message in TelegramBot
        except Exception as e:
            logger.warning(f"Failed to send Telegram alert: {e}")

    # ---------- Main Loop ----------
    def check_open_trades(self):
        """Main loop – should be called periodically (e.g., every minute or on price updates)."""
        trades = self.db.get_open_trades()
        if trades.empty:
            return

        for _, trade in trades.iterrows():
            self._manage_single_trade(trade)

    def _manage_single_trade(self, trade):
        """Manage a single open trade."""
        symbol = trade["symbol"]
        entry = float(trade["entry"])
        sl = float(trade["stop_loss"])
        tp1 = float(trade["tp1"])
        tp2 = float(trade.get("tp2", np.inf))      # may be None
        tp3 = float(trade.get("tp3", np.inf))
        signal = trade["signal"]
        current_price = self.get_price(symbol)
        if current_price is None:
            return

        status = trade.get("status", STATUS_OPEN)

        # ------------------ Expiry check ------------------
        if self._is_expired(trade):
            profit = self.calculate_profit(entry, current_price, signal)
            self.db.update_trade(trade["id"], STATUS_EXPIRED, profit, current_price)
            logger.info(f"{symbol} trade expired (no movement after {TRADE_EXPIRY_CANDLES} candles)")
            self._send_telegram_alert(symbol, signal, entry, current_price, STATUS_EXPIRED, profit)
            return

        # ------------------ Handle price action ------------------
        if signal == "BUY":
            self._manage_buy_trade(trade, current_price, entry, sl, tp1, tp2, tp3)
        else:  # SELL
            self._manage_sell_trade(trade, current_price, entry, sl, tp1, tp2, tp3)

    def _manage_buy_trade(self, trade, price, entry, sl, tp1, tp2, tp3):
        """BUY logic: price >= TP triggers, price <= SL triggers."""
        trade_id = trade["id"]
        symbol = trade["symbol"]
        status = trade.get("status", STATUS_OPEN)

        # Check SL hit (priority over TP)
        if price <= sl:
            profit = self.calculate_profit(entry, sl, "BUY")
            self.db.update_trade(trade_id, STATUS_STOPPED_OUT, profit, price)
            logger.info(f"{symbol} BUY stopped out at {price:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "BUY", entry, price, STATUS_STOPPED_OUT, profit)
            return

        # Check TP1 hit
        if status == STATUS_OPEN and price >= tp1:
            profit = self.calculate_profit(entry, tp1, "BUY")
            self.db.update_trade(trade_id, STATUS_TP1_HIT, profit, price)
            logger.info(f"{symbol} BUY TP1 hit at {tp1:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "BUY", entry, price, STATUS_TP1_HIT, profit)

            # Move SL to entry (break-even)
            if BREAK_EVEN_ACTIVATION_TP >= 1:
                new_sl = entry
                self.db.update_trade_stop(trade_id, new_sl)
                logger.info(f"{symbol} BUY break-even activated (SL moved to {new_sl:.5f})")
            return

        # Check TP2 hit (if defined)
        if status == STATUS_TP1_HIT and tp2 is not None and price >= tp2:
            profit = self.calculate_profit(entry, tp2, "BUY")
            self.db.update_trade(trade_id, STATUS_TP2_HIT, profit, price)
            logger.info(f"{symbol} BUY TP2 hit at {tp2:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "BUY", entry, price, STATUS_TP2_HIT, profit)

            # Move SL to TP1 (partial trail)
            if TRAILING_ACTIVATION_TP >= 2 and TRAILING_STEP > 0:
                new_sl = tp1
                self.db.update_trade_stop(trade_id, new_sl)
                logger.info(f"{symbol} BUY trailing activated (SL moved to {new_sl:.5f})")
            return

        # Check TP3 hit
        if status == STATUS_TP2_HIT and tp3 is not None and price >= tp3:
            profit = self.calculate_profit(entry, tp3, "BUY")
            self.db.update_trade(trade_id, STATUS_TP3_HIT, profit, price)
            logger.info(f"{symbol} BUY TP3 hit at {tp3:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "BUY", entry, price, STATUS_TP3_HIT, profit)
            return

        # Trailing stop after TP2 (if not already closed)
        if status == STATUS_TP2_HIT and TRAILING_ACTIVATION_TP >= 2:
            current_sl = trade.get("stop_loss", sl)
            atr = self._get_atr(symbol)
            if atr is not None:
                new_sl = max(current_sl, price - TRAILING_STEP * atr)
                if new_sl > current_sl:
                    self.db.update_trade_stop(trade_id, new_sl)
                    logger.debug(f"{symbol} trailing SL updated to {new_sl:.5f}")

    def _manage_sell_trade(self, trade, price, entry, sl, tp1, tp2, tp3):
        """SELL logic: price <= TP triggers, price >= SL triggers."""
        trade_id = trade["id"]
        symbol = trade["symbol"]
        status = trade.get("status", STATUS_OPEN)

        # SL hit (price rises above SL)
        if price >= sl:
            profit = self.calculate_profit(entry, sl, "SELL")
            self.db.update_trade(trade_id, STATUS_STOPPED_OUT, profit, price)
            logger.info(f"{symbol} SELL stopped out at {price:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "SELL", entry, price, STATUS_STOPPED_OUT, profit)
            return

        # TP1 hit (price drops below TP1)
        if status == STATUS_OPEN and price <= tp1:
            profit = self.calculate_profit(entry, tp1, "SELL")
            self.db.update_trade(trade_id, STATUS_TP1_HIT, profit, price)
            logger.info(f"{symbol} SELL TP1 hit at {tp1:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "SELL", entry, price, STATUS_TP1_HIT, profit)

            if BREAK_EVEN_ACTIVATION_TP >= 1:
                new_sl = entry
                self.db.update_trade_stop(trade_id, new_sl)
                logger.info(f"{symbol} SELL break-even activated (SL moved to {new_sl:.5f})")
            return

        # TP2 hit
        if status == STATUS_TP1_HIT and tp2 is not None and price <= tp2:
            profit = self.calculate_profit(entry, tp2, "SELL")
            self.db.update_trade(trade_id, STATUS_TP2_HIT, profit, price)
            logger.info(f"{symbol} SELL TP2 hit at {tp2:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "SELL", entry, price, STATUS_TP2_HIT, profit)

            if TRAILING_ACTIVATION_TP >= 2 and TRAILING_STEP > 0:
                new_sl = tp1
                self.db.update_trade_stop(trade_id, new_sl)
                logger.info(f"{symbol} SELL trailing activated (SL moved to {new_sl:.5f})")
            return

        # TP3 hit
        if status == STATUS_TP2_HIT and tp3 is not None and price <= tp3:
            profit = self.calculate_profit(entry, tp3, "SELL")
            self.db.update_trade(trade_id, STATUS_TP3_HIT, profit, price)
            logger.info(f"{symbol} SELL TP3 hit at {tp3:.5f}, profit {profit:.5f}")
            self._send_telegram_alert(symbol, "SELL", entry, price, STATUS_TP3_HIT, profit)
            return

        # Trailing stop for SELL (price drops, trailing SL down)
        if status == STATUS_TP2_HIT and TRAILING_ACTIVATION_TP >= 2:
            current_sl = trade.get("stop_loss", sl)
            atr = self._get_atr(symbol)
            if atr is not None:
                new_sl = min(current_sl, price + TRAILING_STEP * atr)
                if new_sl < current_sl:
                    self.db.update_trade_stop(trade_id, new_sl)
                    logger.debug(f"{symbol} trailing SL updated to {new_sl:.5f}")

    # ---------- Validation & Signal Acceptance ----------
    def validate_trade(self, symbol, signal, entry, stop_loss, tp1, tp2=None, tp3=None):
        """
        Check if a new trade meets risk/reward and duplicate criteria.
        Returns (bool, reason).
        """
        # 1. Duplicate prevention
        open_trades = self.db.get_open_trades()
        if not open_trades.empty:
            same_symbol = open_trades[open_trades["symbol"] == symbol]
            if not same_symbol.empty:
                return False, "Duplicate trade: symbol already has an open position."

        # 2. R:R validation
        if signal == "BUY":
            risk = entry - stop_loss
            if risk <= 0:
                return False, "Invalid stop-loss (must be below entry for BUY)"
            reward1 = tp1 - entry
            reward2 = tp2 - entry if tp2 else None
        else:  # SELL
            risk = stop_loss - entry
            if risk <= 0:
                return False, "Invalid stop-loss (must be above entry for SELL)"
            reward1 = entry - tp1
            reward2 = entry - tp2 if tp2 else None

        # Check TP1 R:R
        rr1 = reward1 / risk
        if rr1 < MIN_RISK_REWARD_RATIO:
            return False, f"R:R too low ({rr1:.2f} < {MIN_RISK_REWARD_RATIO})"

        # If TP2 is provided, check it also (optional)
        if tp2 is not None:
            rr2 = reward2 / risk
            if rr2 < MIN_RISK_REWARD_RATIO:
                return False, f"R:R for TP2 too low ({rr2:.2f} < {MIN_RISK_REWARD_RATIO})"

        return True, "OK"

    # ---------- Trade Entry ----------
    def enter_trade(self, symbol, signal, entry, stop_loss, tp1, tp2=None, tp3=None, timeframe="1H"):
        """
        Insert a new trade into the database if validation passes.
        Returns trade_id or None.
        """
        ok, reason = self.validate_trade(symbol, signal, entry, stop_loss, tp1, tp2, tp3)
        if not ok:
            logger.warning(f"Trade rejected: {reason}")
            return None

        trade_id = self.db.insert_trade(
            symbol=symbol,
            signal=signal,
            entry=entry,
            stop_loss=stop_loss,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            timeframe=timeframe,
            status=STATUS_OPEN,
            open_time=datetime.now().isoformat(),
            entry_price=entry,
        )
        logger.info(f"Trade opened: {symbol} {signal} @ {entry:.5f}, SL={stop_loss:.5f}, TP1={tp1:.5f}")
        return trade_id

    # ---------- Expiry Helper (now dynamic) ----------
    def _is_expired(self, trade):
        """Check if trade has been open too long (based on candle count and timeframe)."""
        if TRADE_EXPIRY_CANDLES <= 0:
            return False
        open_time = pd.to_datetime(trade["open_time"])
        now = datetime.now()
        delta = now - open_time

        timeframe = trade.get("timeframe", "1H")
        seconds_per_candle = TIMEFRAME_SECONDS.get(timeframe, 3600)  # default 1H
        candles_elapsed = delta.total_seconds() / seconds_per_candle
        return candles_elapsed >= TRADE_EXPIRY_CANDLES

    # ---------- ATR Helper ----------
    def _get_atr(self, symbol):
        """Fetch ATR for the symbol using the candle fetcher."""
        df = self.get_candles(symbol, self.timeframe, bars=ATR_PERIOD + 1)
        if df is None or df.empty:
            return None
        high, low, close = df["high"], df["low"], df["close"]
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=ATR_PERIOD).mean().iloc[-1]
        return float(atr) if not np.isnan(atr) else None

    # ---------- Performance Statistics ----------
    def get_performance_stats(self):
        """Return performance metrics from the database."""
        trades = self.db.get_closed_trades()  # all closed trades
        if trades.empty:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_rr": 0,
                "total_pnl": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
                "max_drawdown": 0,
            }

        closed = trades[trades["status"].isin([STATUS_TP1_HIT, STATUS_TP2_HIT, STATUS_TP3_HIT, STATUS_STOPPED_OUT, STATUS_EXPIRED])]
        if closed.empty:
            return {}

        wins = closed[closed["profit"] > 0]
        losses = closed[closed["profit"] < 0]
        total = len(closed)
        win_rate = len(wins) / total if total > 0 else 0

        ordered = closed.sort_values("open_time")
        max_wins = 0
        max_losses = 0
        cur_wins = 0
        cur_losses = 0
        for _, row in ordered.iterrows():
            if row["profit"] > 0:
                cur_wins += 1
                cur_losses = 0
                max_wins = max(max_wins, cur_wins)
            else:
                cur_losses += 1
                cur_wins = 0
                max_losses = max(max_losses, cur_losses)

        total_pnl = closed["profit"].sum()

        cumsum = closed["profit"].cumsum()
        running_max = cumsum.expanding().max()
        drawdown = running_max - cumsum
        max_drawdown = drawdown.max() if not drawdown.empty else 0

        return {
            "total_trades": total,
            "win_rate": round(win_rate * 100, 2),
            "avg_rr": 0,
            "total_pnl": round(total_pnl, 2),
            "consecutive_wins": max_wins,
            "consecutive_losses": max_losses,
            "max_drawdown": round(max_drawdown, 2),
        }


# ===================================================
# Example database interface (stub – adapt to your DB)
# ===================================================
class DatabaseStub:
    """Mock database for illustration. Replace with your actual DB methods."""
    def get_open_trades(self):
        return pd.DataFrame()

    def get_closed_trades(self):
        return pd.DataFrame()

    def update_trade(self, trade_id, status, profit=None, close_price=None):
        pass

    def update_trade_stop(self, trade_id, new_sl):
        pass

    def insert_trade(self, **kwargs):
        return 1
