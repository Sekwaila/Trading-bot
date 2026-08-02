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

# Refresh every 5 minutes to reduce API requests
SCAN_INTERVAL = 300

# API Keys
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Database
DATABASE_NAME = "omega_x.db"

# Strategy Settings
EMA_FAST = 50
EMA_SLOW = 200
RSI_PERIOD = 14
ATR_PERIOD = 14
MIN_CONFIDENCE = 65
