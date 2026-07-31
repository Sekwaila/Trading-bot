import sqlite3
from pathlib import Path

DB_FILE = Path("omega_x.db")


class Database:

    def __init__(self):

        self.conn = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

        self.create_tables()


    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS signals(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            timeframe TEXT,

            signal TEXT,

            confidence INTEGER,

            entry REAL,

            stop REAL,

            tp1 REAL,

            tp2 REAL,

            tp3 REAL,

            status TEXT,

            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """)

        self.conn.commit()


    def insert_signal(

        self,

        symbol,

        timeframe,

        signal,

        confidence,

        entry,

        stop,

        tp1,

        tp2,

        tp3,

        status

    ):

        cursor = self.conn.cursor()

        cursor.execute("""

        INSERT INTO signals(

        symbol,

        timeframe,

        signal,

        confidence,

        entry,

        stop,

        tp1,

        tp2,

        tp3,

        status

        )

        VALUES(?,?,?,?,?,?,?,?,?,?)

        """,

        (

            symbol,

            timeframe,

            signal,

            confidence,

            entry,

            stop,

            tp1,

            tp2,

            tp3,

            status

        )

        )

        self.conn.commit()


    def recent(self):

        cursor = self.conn.cursor()

        cursor.execute("""

        SELECT *

        FROM signals

        ORDER BY id DESC

        LIMIT 20

        """)

        return cursor.fetchall()
