"""
SEKWAILA OMEGA X — PERSISTENCE

Uses stdlib sqlite3 rather than the SQLAlchemy already in requirements.txt.
Reason: this needs to work correctly on the first deploy with zero
debugging room (you're on a phone, not a dev machine) — stdlib sqlite3
against a local file has no connection-string/driver surface to get wrong.
Two real jobs:
  1. alert_state — lets worker.py only send a Telegram message when a
     signal's bias actually CHANGES for a symbol, instead of re-pinging
     every 5 minutes for an unchanged BUY.
  2. trades — your real, user-entered trade journal. Performance stats are
     computed only from what's actually logged here — never fabricated.
"""
import sqlite3
import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_state (
            symbol TEXT PRIMARY KEY,
            last_bias TEXT,
            last_score REAL,
            last_sent_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            signal TEXT,
            entry REAL,
            stop REAL,
            tp1 REAL,
            outcome TEXT,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            bias TEXT,
            score REAL,
            entry REAL,
            stop REAL,
            tp1 REAL,
            tp2 REAL,
            rr REAL
        )
    """)
    conn.commit()
    conn.close()


def should_alert(symbol: str, bias: str, score: float) -> bool:
    """True only if this symbol's bias has changed since the last alert (or no alert has been sent yet)."""
    conn = get_connection()
    row = conn.execute("SELECT last_bias FROM alert_state WHERE symbol = ?", (symbol,)).fetchone()
    conn.close()
    if row is None:
        return True
    return row["last_bias"] != bias


def record_alert(symbol: str, bias: str, score: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO alert_state (symbol, last_bias, last_score, last_sent_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET last_bias=excluded.last_bias, last_score=excluded.last_score, last_sent_at=excluded.last_sent_at",
        (symbol, bias, score, datetime.datetime.now(datetime.timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def log_signal(symbol: str, result: dict):
    """Audit trail of every signal generated — separate from alert_state (which only tracks dedup)."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO signal_log (created_at, symbol, bias, score, entry, stop, tp1, tp2, rr) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.datetime.now(datetime.timezone.utc).isoformat(), symbol,
            result.get("bias"), result.get("score"), result.get("entry"),
            result.get("stop"), result.get("tp1"), result.get("tp2"), result.get("rr"),
        ),
    )
    conn.commit()
    conn.close()


def log_trade(symbol: str, signal: str, entry: float, stop: float, tp1: float, outcome: str, notes: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO trades (created_at, symbol, signal, entry, stop, tp1, outcome, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.datetime.now(datetime.timezone.utc).isoformat(), symbol, signal, entry, stop, tp1, outcome, notes),
    )
    conn.commit()
    conn.close()


def get_trades():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_performance():
    trades = get_trades()
    resolved = [t for t in trades if t["outcome"] in ("WIN", "LOSS")]
    if not resolved:
        return {"has_data": False}
    wins = sum(1 for t in resolved if t["outcome"] == "WIN")
    return {
        "has_data": True,
        "total_logged": len(trades),
        "resolved": len(resolved),
        "wins": wins,
        "losses": len(resolved) - wins,
        "win_rate": round(100 * wins / len(resolved), 1),
    }
