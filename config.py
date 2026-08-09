"""
SEKWAILA OMEGA X — SYSTEM CONFIGURATION
"""

import os


# ------------------------------------------------------------------------------
# ASSETS
# ------------------------------------------------------------------------------

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


# ------------------------------------------------------------------------------
# TIMEFRAMES
# ------------------------------------------------------------------------------

TF_CONFIG = {
    "1D": ("180d", "1d"),
    "4H": ("60d", "1h"),
    "1H": ("30d", "1h"),
    "15M": ("7d", "15m"),
}


# ------------------------------------------------------------------------------
# SIGNAL ENGINE THRESHOLDS
# ------------------------------------------------------------------------------

DEFAULT_MIN_TF_AGREEMENT = int(
    os.getenv("MIN_TF_AGREEMENT", "3")
)

DEFAULT_MIN_SCORE = float(
    os.getenv("MIN_SCORE", "65.0")
)

DEFAULT_MIN_RR = float(
    os.getenv("MIN_RR", "1.5")
)


# ------------------------------------------------------------------------------
# WORKER
# ------------------------------------------------------------------------------

WORKER_POLL_SECONDS = int(
    os.getenv("WORKER_POLL_SECONDS", "300")
)


# ------------------------------------------------------------------------------
# TELEGRAM
# ------------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    ""
)


# ------------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------------

DB_PATH = os.getenv(
    "SEKWAILA_DB_PATH",
    "sekwaila.db"
)


# ------------------------------------------------------------------------------
# POSITION-SIZING CONTRACT VALUES
#
# These are reference contract multipliers for informational sizing.
# Actual broker contract specifications can differ.
# ------------------------------------------------------------------------------

CONTRACT_SIZE_BY_SYMBOL = {
    "XAUUSD": 100.0,
    "NAS100": 20.0,
    "US30": 5.0,
    "BTCUSD": 1.0,
    "EURUSD": 100000.0,
    "GBPUSD": 100000.0,
    "USDJPY": 100000.0,
    "SPX500": 50.0,
    "DXY": 1000.0,
}


# ------------------------------------------------------------------------------
# ENGINE SAFETY
# ------------------------------------------------------------------------------

MINIMUM_DATA_ROWS = 80

ATR_PERIOD = 14

SWING_WINDOW = 5

FVG_LOOKBACK = 40

EQUAL_LEVEL_LOOKBACK = 60

EQUAL_LEVEL_TOLERANCE = 0.0006

STRUCTURE_DISPLACEMENT_MIN = 0.0008

ORDER_BLOCK_DISPLACEMENT_MIN = 0.0025
