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

SCAN_INTERVAL = 60

TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DATABASE_NAME = os.getenv("DATABASE_NAME", "omega_x.db")
