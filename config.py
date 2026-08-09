"""
SEKWAILA OMEGA X — SYSTEM CONFIGURATION
"""

import os


ASSETS = {
    "XAUUSD": "GC=F",
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


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


DEFAULT_MIN_TF_AGREEMENT = int(
    os.getenv("DEFAULT_MIN_TF_AGREEMENT", "3")
)

DEFAULT_MIN_SCORE = float(
    os.getenv("DEFAULT_MIN_SCORE", "65.0")
)

DEFAULT_MIN_RR = float(
    os.getenv("DEFAULT_MIN_RR", "1.5")
)


WORKER_POLL_SECONDS = int(
    os.getenv("WORKER_POLL_SECONDS", "300")
)


DB_PATH = os.getenv(
    "SEKWAILA_DB_PATH",
    "sekwaila.db"
)
