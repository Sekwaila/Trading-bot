"""
SEKWAILA OMEGA X — SETTINGS STORE

Handles persistence of dashboard configuration, AI provider settings, 
and user confluence preferences.
"""

import os
import json
from typing import Dict, Any

from config import (
    SETTINGS_FILE,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
    WORKER_POLL_SECONDS
)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "min_tf_agreement": DEFAULT_MIN_TF_AGREEMENT,
    "min_score": DEFAULT_MIN_SCORE,
    "min_rr": DEFAULT_MIN_RR,
    "worker_poll_seconds": WORKER_POLL_SECONDS,
    "ai": {
        "enabled": True,
        "model": "gpt-3.5-turbo"
    },
    "telegram": {
        "enabled": False,
        "chat_id": ""
    }
}


def load_settings() -> Dict[str, Any]:
    """Loads settings from JSON file or creates default configuration if absent."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge defaults to handle missing keys dynamically
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception as exc:
        print(f"[Settings Engine] Failed to read {SETTINGS_FILE}: {exc}")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """Saves settings dictionary to JSON file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as exc:
        print(f"[Settings Engine] Failed to write {SETTINGS_FILE}: {exc}")
        return False
