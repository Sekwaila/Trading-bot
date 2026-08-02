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

# ===========================
# API KEYS
# ===========================

TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ===========================
# DATABASE
# ===========================

DATABASE_NAME = "omega_x.db"

# ===========================
# SIGNAL SETTINGS
# ===========================

EMA_FAST = 50
EMA_SLOW = 200
RSI_PERIOD = 14
ATR_PERIOD = 14

MIN_CONFIDENCE = 65

# ===========================
# RISK SETTINGS
# ===========================

RISK_REWARD_1 = 1.0
RISK_REWARD_2 = 2.0
RISK_REWARD_3 = 3.0
