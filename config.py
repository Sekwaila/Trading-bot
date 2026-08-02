"""
SEKWAILA OMEGA X
Configuration
"""

import os

APP_NAME = "SEKWAILA OMEGA X"
VERSION = "5.0"

SYMBOLS = [
    "BTC/USD",
    "XAU/USD",
    "EUR/USD",
]

TIMEFRAME = "15min"

# Scan every 5 minutes
SCAN_INTERVAL = 300

# Twelve Data
TWELVEDATA_API_KEY = os.getenv(
    "TWELVEDATA_API_KEY",
    ""
)

# Telegram
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    ""
)

# Database
DATABASE_NAME = "omega_x.db"
