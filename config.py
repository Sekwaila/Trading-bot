"""
SEKWAILA OMEGA X — SYSTEM CONFIGURATION
"""

import os

ASSETS = {
    "XAUUSD": "XAUUSD=X",
    "NAS100": "NQ=F",
    "US30": "YM=F",
    "BTCUSD": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "SPX500": "^GSPC",
    "DXY": "DX-Y.NYB",
}

TF_CONFIG = {
    "1D": ("180d", "1d"),
    "4H": ("60d", "1h"),
    "1H": ("30d", "1h"),
    "15M": ("7d", "15m"),
}

# Ordered for display purposes (highest timeframe first)
TF_ORDER = ["1D", "4H", "1H", "15M"]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DEFAULT_MIN_TF_AGREEMENT = int(os.getenv("DEFAULT_MIN_TF_AGREEMENT", "3"))
DEFAULT_MIN_SCORE = float(os.getenv("DEFAULT_MIN_SCORE", "65.0"))
DEFAULT_MIN_RR = float(os.getenv("DEFAULT_MIN_RR", "1.5"))

WORKER_POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "300"))

DB_PATH = os.getenv("SEKWAILA_DB_PATH", "sekwaila.db")

CONTRACT_SIZE_BY_SYMBOL = {
    "XAUUSD": float(os.getenv("CONTRACT_XAUUSD", "100")),
    "NAS100": float(os.getenv("CONTRACT_NAS100", "1")),
    "US30": float(os.getenv("CONTRACT_US30", "1")),
    "BTCUSD": float(os.getenv("CONTRACT_BTCUSD", "1")),
    "EURUSD": float(os.getenv("CONTRACT_EURUSD", "100000")),
    "GBPUSD": float(os.getenv("CONTRACT_GBPUSD", "100000")),
    "USDJPY": float(os.getenv("CONTRACT_USDJPY", "100000")),
    "SPX500": float(os.getenv("CONTRACT_SPX500", "1")),
    "DXY": float(os.getenv("CONTRACT_DXY", "1")),
}

MINIMUM_DATA_ROWS = int(os.getenv("MINIMUM_DATA_ROWS", "30"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
SWING_WINDOW = int(os.getenv("SWING_WINDOW", "3"))
FVG_LOOKBACK = int(os.getenv("FVG_LOOKBACK", "30"))
EQUAL_LEVEL_LOOKBACK = int(os.getenv("EQUAL_LEVEL_LOOKBACK", "50"))
EQUAL_LEVEL_TOLERANCE = float(os.getenv("EQUAL_LEVEL_TOLERANCE", "0.0015"))
STRUCTURE_DISPLACEMENT_MIN = float(os.getenv("STRUCTURE_DISPLACEMENT_MIN", "0.001"))
ORDER_BLOCK_DISPLACEMENT_MIN = float(os.getenv("ORDER_BLOCK_DISPLACEMENT_MIN", "0.001"))

# ---------------------------------------------------------------------------
# Signal classification thresholds (dashboard display layer only — does not
# change engine bias logic in signals/signal_engine.py).
# A signal can only be classified BUY-side if the engine bias is already BUY,
# and SELL-side if the engine bias is already SELL. NEUTRAL always stays
# NEUTRAL. See classification.py.
# ---------------------------------------------------------------------------
EXTREME_SCORE_MIN = float(os.getenv("EXTREME_SCORE_MIN", "85"))
STRONG_SCORE_MIN = float(os.getenv("STRONG_SCORE_MIN", "72"))
WEAK_SCORE_MAX = float(os.getenv("WEAK_SCORE_MAX", "55"))
EXTREME_MIN_TF_AGREEMENT = int(os.getenv("EXTREME_MIN_TF_AGREEMENT", "4"))

# Settings persistence file (survives restarts; not committed to source control)
SETTINGS_PATH = os.getenv("SEKWAILA_SETTINGS_PATH", "sekwaila_settings.json")
