"""
SEKWAILA OMEGA X — PERSISTENCE

Uses stdlib sqlite3 rather than SQLAlchemy for lightweight, zero-dependency storage.
Guarantees compatibility across environments (mobile/server/local) with no driver setup.

Two main responsibilities:
  1. alert_state — Prevents repetitive Telegram notifications by checking if bias has changed.
  2. trades — Local trade journal for recording actual performance metrics.
  3. signal_log — Full audit trail of every scanned market opportunity.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

from config import DB_PATH


def _ensure_db_dir_exists():
    """Ensures parent directory for DB_PATH exists to prevent SQLite connection failures."""
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Creates a new SQLite database connection with row factory configured."""
    _ensure_db_dir_exists()
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes schema tables if they do not already exist."""
    _ensure_db_dir_exists()
    with get_connection() as conn:
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


def should_alert(symbol: str, bias: str, score: float) -> bool:
    """Returns True if symbol bias has changed or if no alert has been sent yet."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT last_bias FROM alert_state WHERE symbol = ?", 
                (symbol,)
            ).fetchone()
            
            if row is None:
                return True
            return row["last_bias"] != bias
    except Exception as exc:
        print(f"[Persistence Error] Error checking alert state for {symbol}: {exc}")
        return True


def record_alert(symbol: str, bias: str, score: float):
    """Updates or inserts the latest alert state for a symbol."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO alert_state (symbol, last_bias, last_score, last_sent_at) 
                VALUES (?, ?, ?, ?) 
                ON CONFLICT(symbol) DO UPDATE SET 
                    last_bias=excluded.last_bias, 
                    last_score=excluded.last_score, 
                    last_sent_at=excluded.last_sent_at
                """,
                (symbol, bias, float(score) if score else 0.0, now_iso),
            )
            conn.commit()
    except Exception as exc:
        print(f"[Persistence Error] Failed recording alert for {symbol}: {exc}")


def log_signal(symbol: str, result: Dict[str, Any]):
    """Records an audit entry for every generated signal."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Standardize dictionary keys between engine versions
    bias = result.get("bias", "NEUTRAL")
    score = result.get("score", 0.0)
    entry = result.get("entry_price") or result.get("entry", 0.0)
    stop = result.get("stop_loss") or result.get("stop", 0.0)
    tp1 = result.get("tp1", 0.0)
    tp2 = result.get("tp2", 0.0)
    rr = result.get("rr", 0.0)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO signal_log (created_at, symbol, bias, score, entry, stop, tp1, tp2, rr) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now_iso, symbol, bias, score, entry, stop, tp1, tp2, rr),
            )
            conn.commit()
    except Exception as exc:
        print(f"[Persistence Error] Failed logging signal for {symbol}: {exc}")


def log_trade(
    symbol: str, 
    signal: str, 
    entry: float, 
    stop: float, 
    tp1: float, 
    outcome: str, 
    notes: str = ""
):
    """Logs a trade execution into the local trading journal."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO trades (created_at, symbol, signal, entry, stop, tp1, outcome, notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now_iso, symbol, signal, entry, stop, tp1, outcome, notes),
            )
            conn.commit()
    except Exception as exc:
        print(f"[Persistence Error] Failed logging trade for {symbol}: {exc}")


def get_trades() -> List[Dict[str, Any]]:
    """Retrieves all logged trades sorted by newest first."""
    try:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[Persistence Error] Failed fetching trades: {exc}")
        return []


def get_performance() -> Dict[str, Any]:
    """Calculates performance statistics from resolved trade entries."""
    trades = get_trades()
    resolved = [t for t in trades if t.get("outcome") in ("WIN", "LOSS")]
    
    if not resolved:
        return {"has_data": False}
        
    wins = sum(1 for t in resolved if t.get("outcome") == "WIN")
    losses = len(resolved) - wins
    win_rate = round((100.0 * wins / len(resolved)), 1)
    
    return {
        "has_data": True,
        "total_logged": len(trades),
        "resolved": len(resolved),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
    }
