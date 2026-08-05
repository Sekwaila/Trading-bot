"""
SEKWAILA OMEGA X – Configuration
Centralised settings for the entire project.
All constants are defined here and imported where needed.
"""

import os

# ===================================================
# Application Metadata
# ===================================================
APP_NAME = "SEKWAILA OMEGA X"
VERSION = "7.0"                     # Upgraded version reflecting all improvements

# ===================================================
# Symbols & Timeframes
# ===================================================
SYMBOLS = [
    "BTC/USD",
    "XAU/USD",
    "EUR/USD",
]

# Unified timeframe across dashboard, scanner, and trade manager
TIMEFRAME = "1H"                    # Options: 15M, 30M, 1H, 4H, 1D

# Scanner sleep time (seconds)
SCAN_INTERVAL = 300                 # 5 minutes

# ===================================================
# Twelve Data API
# ===================================================
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")

# ===================================================
# Telegram Alerts
# ===================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")   # Matches telegram_bot.py
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ===================================================
# Database
# ===================================================
DATABASE_NAME = "signals.db"        # Consistent with dashboard and scanner

# ===================================================
# Yahoo Finance Fallback
# ===================================================
YFINANCE_ENABLED = True

# Ticker mapping: symbol -> list of Yahoo tickers (tried in order)
YFINANCE_MAP = {
    "XAU/USD": ["GC=F"],            # Gold Futures (XAUUSD=X is dead)
    "BTC/USD": ["BTC-USD"],
    "EUR/USD": ["EURUSD=X"],
}

# Maximum allowed deviation from cached price (percent) before rejecting Yahoo data
MAX_FALLBACK_DEVIATION_PCT = 1.0    # 1% sanity guard

# ===================================================
# Caching
# ===================================================
CACHE_SECONDS = 60                  # Market data cache TTL (seconds)

# ===================================================
# Signal Engine Settings
# ===================================================
MIN_CONFIDENCE = 50                 # Minimum confidence to emit a signal (0–100)
RSI_OVERBOUGHT = 70                 # RSI threshold for reducing BUY confidence
RSI_EXTREME = 75                    # RSI threshold for rejecting BUY signals

# Module weights (influence on final score)
MODULE_WEIGHTS = {
    "market_structure": 3,
    "choch": 3,
    "order_blocks": 2,
    "fvg": 1,
    "liquidity": 2,
}

# Grade thresholds
GRADE_A = 80
GRADE_B = 65

# ===================================================
# Trade Manager Settings
# ===================================================
# Risk / Reward
MIN_RISK_REWARD_RATIO = 2.0         # Minimum R:R (e.g., 2.0 = 1:2)

# ATR parameters
ATR_PERIOD = 14
ATR_MULTIPLIER_SL = 1.5
ATR_MULTIPLIER_TP1 = 1.5
ATR_MULTIPLIER_TP2 = 2.5
ATR_MULTIPLIER_TP3 = 4.0

# Break-even & trailing
BREAK_EVEN_ACTIVATION_TP = 1        # Move SL to entry after which TP level (1,2,3)
TRAILING_ACTIVATION_TP = 2          # Start trailing after which TP level
TRAILING_STEP = 0.5                 # ATR multiplier for trailing step

# Trade expiry
TRADE_EXPIRY_CANDLES = 48           # Max candles before expiry (timeframe‑aware)

# Cooldown (same‑direction signals)
COOLDOWN_MINUTES = 30               # Minutes to wait before allowing another signal in same direction
MIN_CONFIDENCE_IMPROVEMENT = 10     # Minimum percentage point increase to override cooldown

# ===================================================
# Status Constants (used by trade manager)
# ===================================================
STATUS_OPEN = "OPEN"
STATUS_TP1_HIT = "TP1_HIT"
STATUS_TP2_HIT = "TP2_HIT"
STATUS_TP3_HIT = "TP3_HIT"
STATUS_STOPPED_OUT = "STOPPED_OUT"
STATUS_CLOSED = "CLOSED"
STATUS_EXPIRED = "EXPIRED"

# ===================================================
# Timeframe Seconds (for expiry calculation)
# ===================================================
TIMEFRAME_SECONDS = {
    "15M": 900,
    "30M": 1800,
    "1H": 3600,
    "4H": 14400,
    "1D": 86400,
}
