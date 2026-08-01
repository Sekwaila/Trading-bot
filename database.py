"""
SEKWAILA OMEGA X
Database Engine
SQLite
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_FOLDER = Path("database")
DB_FOLDER.mkdir(exist_ok=True)

DB_PATH = DB_FOLDER / "omega_x.db"


class Database:

    def __init__(self):

        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self.create_tables()

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS signals(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            signal TEXT,

            confidence INTEGER,

            entry REAL,

            stop_loss REAL,

            tp1 REAL,

            tp2 REAL,

            tp3 REAL,

            timeframe TEXT,

            reason TEXT,

            created_at TEXT

        )

        """)

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS trades(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            direction TEXT,

            entry REAL,

            exit REAL,

            profit REAL,

            status TEXT,

            opened_at TEXT,

            closed_at TEXT

        )

        """)

        self.conn.commit()

    # ===========================================
    # SIGNALS
    # ===========================================

    def add_signal(

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

        reason

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

            timeframe,

            reason,

            created_at

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?)

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

            reason,

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

        )

        self.conn.commit()

    def get_signals(self, limit=50):

        cursor = self.conn.cursor()

        cursor.execute("""

        SELECT *

        FROM signals

        ORDER BY id DESC

        LIMIT ?

        """,

        (limit,)

        )

        return cursor.fetchall()

    # ===========================================
    # TRADES
    # ===========================================

    def add_trade(

        self,

        symbol,

        direction,

        entry,

        exit_price,

        profit,

        status

    ):

        cursor = self.conn.cursor()

        cursor.execute("""

        INSERT INTO trades(

            symbol,

            direction,

            entry,

            exit,

            profit,

            status,

            opened_at,

            closed_at

        )

        VALUES(?,?,?,?,?,?,?,?)

        """,

        (

            symbol,

            direction,

            entry,

            exit_price,

            profit,

            status,

            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

        )

        self.conn.commit()

    def get_trades(self):

        cursor = self.conn.cursor()

        cursor.execute("""

        SELECT *

        FROM trades

        ORDER BY id DESC

        """)

        return cursor.fetchall()

    # ===========================================
    # STATS
    # ===========================================

    def total_trades(self):

        cursor = self.conn.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM trades"

        )

        return cursor.fetchone()[0]

    def total_profit(self):

        cursor = self.conn.cursor()

        cursor.execute(

            "SELECT SUM(profit) FROM trades"

        )

        result = cursor.fetchone()[0]

        if result is None:

            return 0

        return round(result, 2)

    def win_rate(self):

        cursor = self.conn.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM trades"

        )

        total = cursor.fetchone()[0]

        if total == 0:

            return 0

        cursor.execute(

            "SELECT COUNT(*) FROM trades WHERE profit > 0"

        )

        wins = cursor.fetchone()[0]

        return round((wins / total) * 100, 2)

    def close(self):

        self.conn.close()


db = Database()
