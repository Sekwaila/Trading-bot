"""
SEKWAILA OMEGA X – Database Manager
Now with intelligent duplicate prevention and direction‑aware cooldown.
"""

import sqlite3
from datetime import datetime, timedelta

import pandas as pd

from config import DATABASE_NAME
from logger import get_logger

logger = get_logger("database")

# =====================================
# Signal Filtering Settings
# =====================================
COOLDOWN_MINUTES = 30              # Time to wait before allowing another same‑direction signal
MIN_CONFIDENCE_IMPROVEMENT = 10    # Minimum absolute percentage point increase
                                    # required to save a same‑direction signal
ENTRY_TOLERANCE = 0.0001           # Tolerance for duplicate entry detection


class Database:

    def __init__(self):

        self.conn = sqlite3.connect(
            DATABASE_NAME,
            check_same_thread=False,
        )

        self.create_tables()

    # -----------------------------------
    # Create Tables
    # -----------------------------------

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,
            signal TEXT,

            confidence REAL,

            entry REAL,

            stop_loss REAL,

            tp1 REAL,
            tp2 REAL,
            tp3 REAL,

            timeframe TEXT,

            status TEXT DEFAULT 'OPEN',

            result TEXT DEFAULT '',

            profit REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    # -----------------------------------
    # Duplicate Filter (for OPEN signals)
    # Now checks entry price with a tolerance
    # -----------------------------------

    def signal_exists(self, symbol, signal, entry):
        """
        Check if an OPEN trade exists for the same symbol and signal,
        with entry price within ENTRY_TOLERANCE.
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM signals
            WHERE symbol=?
            AND signal=?
            AND ABS(entry-?) < ?
            AND status='OPEN'
            LIMIT 1
            """,
            (
                symbol,
                signal,
                entry,
                ENTRY_TOLERANCE,
            ),
        )

        return cursor.fetchone() is not None

    # -----------------------------------
    # Get the last signal (including confidence)
    # -----------------------------------

    def get_last_signal_details(self, symbol, timeframe=None):
        """
        Returns the most recent signal for a symbol (and optional timeframe)
        with signal, confidence, and created_at.
        """
        cursor = self.conn.cursor()

        if timeframe:
            cursor.execute(
                """
                SELECT signal, confidence, created_at
                FROM signals
                WHERE symbol = ? AND timeframe = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (symbol, timeframe),
            )
        else:
            cursor.execute(
                """
                SELECT signal, confidence, created_at
                FROM signals
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (symbol,),
            )

        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "signal": row[0],
            "confidence": row[1],
            "created_at": datetime.fromisoformat(row[2]),
        }

    # -----------------------------------
    # Cooldown check (only used when direction unchanged)
    # -----------------------------------

    def _in_cooldown(self, symbol, timeframe, minutes=COOLDOWN_MINUTES):
        last = self.get_last_signal_details(symbol, timeframe)
        if last is None:
            return False
        now = datetime.now()
        age = now - last["created_at"]
        return age < timedelta(minutes=minutes)

    # -----------------------------------
    # Save Signal (with intelligent duplicate + cooldown checks)
    # -----------------------------------

    def save_signal(
        self,
        symbol,
        signal,
        confidence,
        entry,
        stop_loss,
        tp1,
        tp2,
        tp3,
        timeframe,
    ):

        # 1. Check if an identical OPEN trade exists (same entry tolerance)
        if self.signal_exists(symbol, signal, entry):
            logger.info("Duplicate skipped (open trade with close entry): %s %s", symbol, signal)
            return False

        # 2. Get the last signal (any status) to check direction change
        last = self.get_last_signal_details(symbol, timeframe)

        if last is not None:
            # Direction changed → always allow (bypass cooldown)
            if last["signal"] != signal:
                logger.info("Direction change: %s → %s, saving", last["signal"], signal)
            else:
                # Same direction → apply cooldown and confidence improvement checks
                # 2a. Cooldown
                if self._in_cooldown(symbol, timeframe):
                    logger.info("Cooldown active for %s (%s) – same direction", symbol, timeframe)
                    return False

                # 2b. Confidence improvement
                improvement = confidence - last["confidence"]
                if improvement >= MIN_CONFIDENCE_IMPROVEMENT:
                    logger.info(
                        "Confidence improved by %.1f points (%s → %s), saving",
                        improvement,
                        last["confidence"],
                        confidence
                    )
                else:
                    logger.info(
                        "Skipped: same direction and confidence improvement "
                        "%.1f < %d points",
                        improvement,
                        MIN_CONFIDENCE_IMPROVEMENT
                    )
                    return False
        else:
            # No prior signal – always allow
            logger.info("First signal for %s, saving", symbol)

        # If we passed all checks, save the signal
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO signals(
                symbol,
                signal,
                confidence,
                entry,
                stop_loss,
                tp1,
                tp2,
                tp3,
                timeframe
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?
            )
            """,
            (
                symbol,
                signal,
                confidence,
                entry,
                stop_loss,
                tp1,
                tp2,
                tp3,
                timeframe,
            ),
        )

        self.conn.commit()
        logger.info("Saved signal: %s %s @ %.5f (conf %.0f%%)",
                    symbol, signal, entry, confidence)
        return True

    # -----------------------------------
    # Open Trades
    # -----------------------------------

    def get_open_trades(self):

        return pd.read_sql_query(
            """
            SELECT *
            FROM signals
            WHERE status='OPEN'
            ORDER BY id ASC
            """,
            self.conn,
        )

    # -----------------------------------
    # Close Trade
    # -----------------------------------

    def update_trade(
        self,
        signal_id,
        result,
        profit,
    ):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE signals
            SET
                status='CLOSED',
                result=?,
                profit=?
            WHERE id=?
            """,
            (
                result,
                profit,
                signal_id,
            ),
        )

        self.conn.commit()

        logger.info(
            "Trade %s closed as %s",
            signal_id,
            result,
        )

    # -----------------------------------
    # History
    # -----------------------------------

    def get_signals(self, limit=100):

        return pd.read_sql_query(
            f"""
            SELECT *
            FROM signals
            ORDER BY id DESC
            LIMIT {limit}
            """,
            self.conn,
        )

    # -----------------------------------
    # Statistics
    # -----------------------------------

    def statistics(self):

        df = self.get_signals(10000)

        total = len(df)

        if total == 0:

            return {
                "total": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "profit": 0,
            }

        closed = df[df["status"] == "CLOSED"]

        wins = len(closed[closed["result"] == "WIN"])
        losses = len(closed[closed["result"] == "LOSS"])

        profit = closed["profit"].sum()

        trades = wins + losses

        win_rate = 0

        if trades > 0:

            win_rate = round(
                wins / trades * 100,
                2,
            )

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit": round(
                profit,
                2,
            ),
        }


db = Database()
