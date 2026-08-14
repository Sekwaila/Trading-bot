"""
SEKWAILA OMEGA X — CONFIGURATION ENGINE

Defines application defaults, database paths, supported asset mappings, 
and system fallback values.
"""

import os
from typing import Dict

# -------------------------------------------------------------------
# PATHS & PERSISTENCE
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "omega.db")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# -------------------------------------------------------------------
# ENGINE CONFLUENCE DEFAULTS
# -------------------------------------------------------------------
DEFAULT_MIN_TF_AGREEMENT: int = 2
DEFAULT_MIN_SCORE: float = 70.0
DEFAULT_MIN_RR: float = 1.5
WORKER_POLL_SECONDS: int = 300

# -------------------------------------------------------------------
# ASSET DICTIONARY
# -------------------------------------------------------------------
ASSETS: Dict[str, str] = {
    "XAUUSD": "Gold Spot",
    "EURUSD": "Euro / US Dollar",
    "GBPUSD": "British Pound / US Dollar",
    "USDJPY": "US Dollar / Japanese Yen",
    "BTCUSD": "Bitcoin / US Dollar",
    "NAS100": "Nasdaq 100",
    "US30": "Dow Jones Industrial",
    "VOL100": "Volatility 100 Index",
    "VOL75": "Volatility 75 Index",
}
