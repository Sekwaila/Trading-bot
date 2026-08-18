"""
SEKWAILA OMEGA X — DATABASE UTILITIES (database.py)
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "trading_journal.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            asset TEXT,
            signal TEXT,
            entry REAL,
            stop REAL,
            tp1 REAL,
            outcome TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_trade(asset, signal, entry, stop, tp1, outcome, notes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (asset, signal, entry, stop, tp1, outcome, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (asset, signal, entry, stop, tp1, outcome, notes))
    conn.commit()
    conn.close()

def get_trades():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, asset, signal, entry, stop, tp1, outcome, notes FROM trades ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "Timestamp": row[0],
            "Asset": row[1],
            "Signal": row[2],
            "Entry": row[3],
            "Stop": row[4],
            "TP1": row[5],
            "Outcome": row[6],
            "Notes": row[7]
        }
        for row in rows
    ]

def get_performance():
    trades = get_trades()
    if not trades:
        return {"has_data": False, "total_logged": 0, "resolved": 0, "win_rate": 0.0}
    
    total = len(trades)
    resolved_trades = [t for t in trades if t["Outcome"] in ("WIN", "LOSS")]
    wins = len([t for t in trades if t["Outcome"] == "WIN"])
    resolved_count = len(resolved_trades)
    
    win_rate = round((wins / resolved_count) * 100, 1) if resolved_count > 0 else 0.0
    return {
        "has_data": True,
        "total_logged": total,
        "resolved": resolved_count,
        "win_rate": win_rate
    }
