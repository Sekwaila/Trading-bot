"""
SEKWAILA OMEGA X — TELEGRAM BROADCASTER

Used by both streamlit_app.py (Settings > Telegram > Test button) and
worker.py (automatic alerts). Neither computes its own signal — both call
signals.signal_engine.generate_omega_signal() and pass the result here.
"""

import requests

from logger import get_logger
from classification import classify_signal

logger = get_logger("TELEGRAM")


def send_telegram_message(token: str, chat_id: str, message: str) -> tuple[bool, str]:
    if not token or not chat_id:
        return False, "Bot token and Chat ID are required."
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=12)
        if resp.ok:
            return True, "Signal dispatched to Telegram."
        return False, f"Telegram Error {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        logger.error(f"Telegram dispatch failed: {exc}")
        return False, f"Connection failure: {exc}"


def format_signal_message(symbol: str, result: dict) -> str:
    """Build the alert text from an engine result. Same formatting used by
    the dashboard's test button and the background worker, so what you see
    on-screen always matches what gets sent."""
    if not result or not result.get("ok"):
        reason = (result or {}).get("reason", "unknown error")
        return f"⚠️ {symbol}: DATA UNAVAILABLE — {reason}"

    level = classify_signal(result)
    lines = [
        "👑 SEKWAILA OMEGA X ALERT",
        "",
        f"Asset: {symbol}",
        f"Signal: {level}",
        f"Score: {result.get('score', 0):.1f}/100",
        f"Grade: {result.get('grade', '-')}",
    ]
    if result.get("bias") in ("BUY", "SELL"):
        lines += [
            f"Entry: {result.get('entry', 0):.4f}",
            f"Stop: {result.get('stop', 0):.4f}",
            f"TP1: {result.get('tp1', 0):.4f}",
            f"TP2: {result.get('tp2', 0):.4f}",
            f"TP3: {result.get('tp3', 0):.4f}",
            f"R:R: {result.get('rr', 0):.2f}",
        ]
    return "\n".join(lines)
