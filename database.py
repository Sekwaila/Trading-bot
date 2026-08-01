"""
SEKWAILA OMEGA X
Database
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any

from logger import get_logger
from config import DATABASE_NAME

logger = get_logger("database")


class Database:

    def __init__(self, db_name: str = DATABASE_NAME):
        # Allow access from different threads (worker + streamlit)
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        # Use Row factory for named columns
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
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
            """
        )
        self.conn.commit()

    def save_signal(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        entry: float,
        stop_loss: float,
        tp1: float,
        tp2: float,
        tp3: float,
        timeframe: str,
    ):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO signals(
                    symbol, signal, confidence, entry, stop_loss, tp1, tp2, tp3, timeframe
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    str(signal),
                    float(confidence) if confidence is not None else None,
                    float(entry) if entry is not None else None,
                    float(stop_loss) if stop_loss is not None else None,
                    float(tp1) if tp1 is not None else None,
                    float(tp2) if tp2 is not None else None,
                    float(tp3) if tp3 is not None else None,
                    str(timeframe),
                ),
            )
            self.conn.commit()
            logger.info("Saved signal: %s %s (conf=%s)", symbol, signal, confidence)
        except Exception as e:
            logger.exception("Failed to save signal for %s: %s", symbol, e)

    def get_signals(self, limit: int = 100) -> pd.DataFrame:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM signals
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            # Convert sqlite3.Row to dicts, then to DataFrame
            records = [dict(r) for r in rows]
            df = pd.DataFrame.from_records(records)
            return df
        except Exception as e:
            logger.exception("Failed to fetch signals: %s", e)
            return pd.DataFrame()


# Single global DB instance used by the app
db = Database()
