"""
SEKWAILA OMEGA X — SYSTEM CONFIGURATION
"""

import os


# ==============================================================================
# ASSETS
# ==============================================================================

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


# ==============================================================================
# TIMEFRAMES
# ==============================================================================

TF_CONFIG = {
    "1D": ("180d", "1d"),
    "4H": ("60d", "1h"),
    "1H": ("30d", "1h"),
    "15M": ("7d", "15m"),
}


# ==============================================================================
# TELEGRAM
# ==============================================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "",
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "",
)


# ==============================================================================
# SIGNAL THRESHOLDS
# ==============================================================================

DEFAULT_MIN_TF_AGREEMENT = int(
    os.getenv(
        "DEFAULT_MIN_TF_AGREEMENT",
        "3",
    )
)

DEFAULT_MIN_SCORE = float(
    os.getenv(
        "DEFAULT_MIN_SCORE",
        "65.0",
    )
)

DEFAULT_MIN_RR = float(
    os.getenv(
        "DEFAULT_MIN_RR",
        "1.5",
    )
)


# ==============================================================================
# ENGINE SETTINGS
# ==============================================================================

# Minimum candles required after downloading/processing data.
MINIMUM_DATA_ROWS = int(
    os.getenv(
        "MINIMUM_DATA_ROWS",
        "30",
    )
)

# ATR period.
ATR_PERIOD = int(
    os.getenv(
        "ATR_PERIOD",
        "14",
    )
)

# Swing-point detection.
SWING_WINDOW = int(
    os.getenv(
        "SWING_WINDOW",
        "3",
    )
)

# FVG search depth.
FVG_LOOKBACK = int(
    os.getenv(
        "FVG_LOOKBACK",
        "50",
    )
)

# Equal highs/lows.
EQUAL_LEVEL_LOOKBACK = int(
    os.getenv(
        "EQUAL_LEVEL_LOOKBACK",
        "50",
    )
)

EQUAL_LEVEL_TOLERANCE = float(
    os.getenv(
        "EQUAL_LEVEL_TOLERANCE",
        "0.0015",
    )
)

# Minimum structural displacement.
STRUCTURE_DISPLACEMENT_MIN = float(
    os.getenv(
        "STRUCTURE_DISPLACEMENT_MIN",
        "0.001",
    )
)

# Minimum displacement required to qualify an order block.
ORDER_BLOCK_DISPLACEMENT_MIN = float(
    os.getenv(
        "ORDER_BLOCK_DISPLACEMENT_MIN",
        "0.0015",
    )
)


# ==============================================================================
# CONTRACT / POINT VALUES
# ==============================================================================

# Approximate USD value of one full price point per contract/unit.
#
# IMPORTANT:
# These values are appropriate for the Yahoo Finance instruments currently
# used by the engine, not necessarily the exact contract specification of
# every broker's CFD.
#
# For live broker execution, these should eventually come from the broker.

CONTRACT_SIZE_BY_SYMBOL = {
    "XAUUSD": 100.0,       # GC futures: $100 per $1.00 move
    "NAS100": 20.0,       # NQ futures: $20 per index point
    "US30": 5.0,          # YM futures: $5 per index point
    "BTCUSD": 1.0,        # $1 per $1 BTC move
    "EURUSD": 100000.0,   # standard FX lot
    "GBPUSD": 100000.0,
    "USDJPY": 100000.0,
    "SPX500": 50.0,
    "DXY": 1000.0,
}


# ==============================================================================
# WORKER
# ==============================================================================

WORKER_POLL_SECONDS = int(
    os.getenv(
        "WORKER_POLL_SECONDS",
        "300",
    )
)


# ==============================================================================
# DATABASE
# ==============================================================================

DB_PATH = os.getenv(
    "SEKWAILA_DB_PATH",
    "sekwaila.db",
)
