"""
SEKWAILA OMEGA X
Database Manager
"""

import sqlite3
import pandas as pd

from config import DATABASE_NAME
from logger import get_logger

logger = get_logger("database")


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
    # Duplicate Filter
    # -----------------------------------

    def signal_exists(self, symbol, signal):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM signals
            WHERE symbol=?
            AND signal=?
            AND status='OPEN'
            LIMIT 1
            """,
            (
                symbol,
                signal,
            ),
        )

        return cursor.fetchone() is not None

    # -----------------------------------
    # Save Signal
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

        if self.signal_exists(symbol, signal):

            logger.info(
                "Duplicate skipped: %s %s",
                symbol,
                signal,
            )

            return

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

        logger.info(
            "Saved signal: %s %s",
            symbol,
            signal,
        )

    # -----------------------------------
    # Get Open Trades
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
