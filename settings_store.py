"""
SEKWAILA OMEGA X — SETTINGS PERSISTENCE

Small JSON-file-backed settings store so dashboard configuration (risk,
thresholds, Telegram, AI, display prefs) survives a restart without needing a
database. Secrets (bot token, AI API key) are stored in the same file — this
is a local single-user deployment convenience, not a secrets vault. For a
shared/public deployment, prefer environment variables / st.secrets instead.
"""

import json
import os

from config import (
    SETTINGS_PATH, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ASSETS,
)

DEFAULTS = {
    "general": {
        "refresh_seconds": 120,
        "account_currency": "ZAR",
        "account_balance": 10000.0,
    },
    "signals": {
        "min_tf_agreement": DEFAULT_MIN_TF_AGREEMENT,
        "min_score": DEFAULT_MIN_SCORE,
        "min_rr": DEFAULT_MIN_RR,
    },
    "risk": {
        "risk_pct": 1.0,
    },
    "ai": {
        "enabled": False,
        "provider": "Anthropic",
        "api_key": "",
        "model": "",
        "confidence_threshold": 70.0,
        "contributes_to_score": False,
    },
    "telegram": {
        "enabled": False,
        "bot_token": TELEGRAM_BOT_TOKEN,
        "chat_id": TELEGRAM_CHAT_ID,
        "min_signal_level": "STRONG BUY",
        "cooldown_minutes": 30,
    },
    "data": {
        "selected_assets": list(ASSETS.keys()),
        "price_offsets": {},  # e.g. {"XAUUSD": -3.20} — added to displayed entry/stop/TP1-3
    },
    "display": {
        "theme": "Terminal Dark",
        "compact_mode": False,
    },
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                saved = json.load(f)
            merged = {k: {**v, **saved.get(k, {})} for k, v in DEFAULTS.items()}
            return merged
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULTS))


def save_settings(settings: dict) -> bool:
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False
