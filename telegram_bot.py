"""
SEKWAILA OMEGA X — TELEGRAM BROADCASTER (enhanced)

Enhancements:
- Uses MarkdownV2 and escapes message content to avoid parse errors.
- Retries transient Telegram errors (429, 5xx) with exponential backoff.
- Optional inline "View chart" button using the ticker from config.ASSETS when available.
- Safe numeric coercion and stable formatting.
"""

import json
import time
import requests
from typing import Optional, Tuple

from logger import get_logger
from classification import classify_signal
from config import ASSETS

logger = get_logger("TELEGRAM")


def _escape_md_v2(text: str) -> str:
    """Escape text for Telegram MarkdownV2 parsing."""
    if text is None:
        return ""
    replacements = [
        ('\\', r'\\\\'),
        ('_', r'\\_'),
        ('*', r'\\*'),
        ('[', r'\\['),
        (']', r'\\]'),
        ('(', r'\\('),
        (')', r'\\)'),
        ('~', r'\\~'),
        ('`', r'\\`'),
        ('>', r'\\>'),
        ('#', r'\\#'),
        ('+', r'\\+'),
        ('-', r'\\-'),
        ('=', r'\\='),
        ('|', r'\\|'),
        ('{', r'\\{'),
        ('}', r'\\}'),
        ('.', r'\\.'),
        ('!', r'\\!'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _safe_num(value, default=0.0):
    try:
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def format_signal_message(symbol: str, result: dict) -> str:
    """Build the alert text from an engine result. Returns a MarkdownV2-escaped string."""
    if not result or not result.get("ok"):
        reason = (result or {}).get("reason", "unknown error")
        return _escape_md_v2(f"⚠️ {symbol}: DATA UNAVAILABLE — {reason}")

    level = classify_signal(result)
    score = _safe_num(result.get("score"), 0.0)
    entry = _safe_num(result.get("entry"), 0.0)
    stop = _safe_num(result.get("stop"), 0.0)
    tp1 = _safe_num(result.get("tp1"), 0.0)
    tp2 = _safe_num(result.get("tp2"), 0.0)
    tp3 = _safe_num(result.get("tp3"), 0.0)
    rr = _safe_num(result.get("rr"), 0.0)

    lines = [
        "👑 *SEKWAILA OMEGA X ALERT*",
        "",
        f"*Asset:* {symbol}",
        f"*Signal:* {level}",
        f"*Score:* {score:.1f}/100",
        f"*Grade:* {result.get('grade', '-')}",
    ]
    if result.get("bias") in ("BUY", "SELL"):
        lines += [
            f"*Entry:* {entry:.4f}",
            f"*Stop:* {stop:.4f}",
            f"*TP1:* {tp1:.4f}",
            f"*TP2:* {tp2:.4f}",
            f"*TP3:* {tp3:.4f}",
            f"*R:R:* {rr:.2f}",
        ]

    text = "\n".join(lines)
    return _escape_md_v2(text)


def _build_reply_markup(chart_url: Optional[str] = None) -> Optional[dict]:
    if not chart_url:
        return None
    return {"inline_keyboard": [[{"text": "View chart", "url": chart_url}]]}


def send_telegram_message(token: str, chat_id: str, message: str, chart_url: Optional[str] = None,
                          max_retries: int = 3, backoff_base: float = 1.0) -> Tuple[bool, str]:
    """Send a message to Telegram with limited retries on transient errors.

    message is expected to already be escaped for MarkdownV2.
    chart_url (optional) is used to add an inline "View chart" button.
    Returns (ok: bool, info: str).
    """
    if not token or not chat_id:
        return False, "Bot token and Chat ID are required."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}
    markup = _build_reply_markup(chart_url)
    if markup is not None:
        payload["reply_markup"] = markup

    attempt = 0
    while attempt < max_retries:
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.ok:
                return True, "Signal dispatched to Telegram."
            status = resp.status_code
            text = resp.text
            # Retry on rate limit or server errors
            if status == 429 or 500 <= status < 600:
                attempt += 1
                wait = backoff_base * (2 ** (attempt - 1))
                logger.warning("Telegram transient error %s: %s — retrying in %.1fs (attempt %d/%d)", status, text[:200], wait, attempt, max_retries)
                time.sleep(wait)
                continue
            # Non-retryable error
            return False, f"Telegram Error {status}: {text[:200]}"
        except requests.RequestException as exc:
            attempt += 1
            wait = backoff_base * (2 ** (attempt - 1))
            logger.warning("Telegram request exception: %s — retrying in %.1fs (attempt %d/%d)", exc, wait, attempt, max_retries)
            time.sleep(wait)
            continue
    return False, f"Failed to send message after {max_retries} attempts"


# Convenience helper: format+send for an engine result. Attempts to include a chart URL derived
# from config.ASSETS mapping if available (uses Yahoo/Investing/TradingView style link guess).
def send_engine_signal(token: str, chat_id: str, symbol: str, result: dict) -> Tuple[bool, str]:
    msg = format_signal_message(symbol, result)
    # Try to construct a chart URL using TradingView pattern; fall back to Yahoo ticker if available
    chart_url = None
    ticker = ASSETS.get(symbol)
    if ticker:
        try:
            # If ticker looks like Yahoo (contains = or - or ^), provide Yahoo finance link
            if any(c in ticker for c in ['=', '-', '^', '.']):
                chart_url = f"https://finance.yahoo.com/quote/{ticker}"
            else:
                chart_url = f"https://www.tradingview.com/symbols/{ticker}/"
        except Exception:
            chart_url = None
    return send_telegram_message(token, chat_id, msg, chart_url=chart_url)
