"""
SEKWAILA OMEGA X — JSON PERSISTENCE DATABASE
"""
import json
import os
from typing import List, Dict, Any
from logger import get_logger

logger = get_logger("DATABASE")
DB_FILE = os.path.join("data", "journal.json")

def _init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)

def load_journal() -> List[Dict[str, Any]]:
    _init_db()
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load journal: {e}")
        return []

def save_journal_entry(entry: Dict[str, Any]) -> bool:
    journal = load_journal()
    journal.insert(0, entry)
    try:
        with open(DB_FILE, "w") as f:
            json.dump(journal, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save entry: {e}")
        return False
