"""
SEKWAILA OMEGA X
Database
"""

import sqlite3

from config import DATABASE_NAME


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

        timeframe

    ):

        cursor = self.conn.cursor()

        cursor.execute("""

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

            timeframe

        )

        )

        self.conn.commit()

    def get_signals(self):

        cursor = self.conn.cursor()

        cursor.execute("""

        SELECT *

        FROM signals

        ORDER BY id DESC

        LIMIT 100

        """)

        return cursor.fetchall()


db = Database()
