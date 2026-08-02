"""
SEKWAILA OMEGA X
Database
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
            check_same_thread=False
        )
        self.create_tables()

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def signal_exists(self, symbol, signal, entry):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM signals
            WHERE symbol=?
            AND signal=?
            AND entry=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                symbol,
                signal,
                entry,
            )
        )

        return cursor.fetchone() is not None

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

        if self.signal_exists(symbol, signal, entry):
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
            VALUES(?,?,?,?,?,?,?,?,?)
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
            )
        )

        self.conn.commit()

        logger.info(
            "Saved signal: %s %s",
            symbol,
            signal,
        )

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


db = Database()
