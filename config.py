import os

# Settings file path (local JSON store used by Streamlit UI)
SETTINGS_PATH = os.getenv("SEKWAILA_SETTINGS_PATH", "sekwaila_settings.json")
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "30"))

# Database path
DB_PATH = os.getenv("SEKWAILA_DB_PATH", "sekwaila.db")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Worker
WORKER_POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "300"))

# Engine defaults
DEFAULT_MIN_TF_AGREEMENT = int(os.getenv("DEFAULT_MIN_TF_AGREEMENT", "2"))
DEFAULT_MIN_SCORE = float(os.getenv("DEFAULT_MIN_SCORE", "65.0"))
DEFAULT_MIN_RR = float(os.getenv("DEFAULT_MIN_RR", "1.5"))

# Classification thresholds
EXTREME_SCORE_MIN = float(os.getenv("EXTREME_SCORE_MIN", "90"))
STRONG_SCORE_MIN = float(os.getenv("STRONG_SCORE_MIN", "75"))
WEAK_SCORE_MAX = float(os.getenv("WEAK_SCORE_MAX", "40"))
EXTREME_MIN_TF_AGREEMENT = int(os.getenv("EXTREME_MIN_TF_AGREEMENT", "3"))

# Asset mapping (internal symbol -> price source ticker). Update to match your feed.
# These tickers are used for yfinance fallback and for constructing chart URLs.
ASSETS = {
    "XAUUSD": "GC=F",    # Gold futures on Yahoo
    "EURUSD": "EURUSD=X",
    "BTCUSD": "BTC-USD",
    "USDZAR": "USDZAR=X",
}

# Timeframe configuration
# TF_CONFIG maps a timeframe label to (yfinance_period, yfinance_interval)
TF_CONFIG = {
    "15m": ("7d", "15m"),
    "1h": ("30d", "60m"),
    "4h": ("90d", "240m"),
    "1d": ("730d", "1d"),
}

# Deriv/WebSocket mapping: labels -> granularity in seconds
DERIV_GRANULARITY = {
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

# Number of candles to request per timeframe (Deriv)
DERIV_CANDLE_COUNT = {"15m": 300, "1h": 300, "4h": 300, "1d": 365}

# Map internal symbol to Deriv symbol code if you use Deriv live feed
DERIV_SYMBOL_MAP = {
    # Example: "XAUUSD": "frxXAUUSD",
}

# Deriv API credentials (optional)
DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "")

# Data & indicator tuning
MINIMUM_DATA_ROWS = int(os.getenv("MINIMUM_DATA_ROWS", "30"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
SWING_WINDOW = int(os.getenv("SWING_WINDOW", "5"))
FVG_LOOKBACK = int(os.getenv("FVG_LOOKBACK", "20"))
EQUAL_LEVEL_LOOKBACK = int(os.getenv("EQUAL_LEVEL_LOOKBACK", "50"))
EQUAL_LEVEL_TOLERANCE = float(os.getenv("EQUAL_LEVEL_TOLERANCE", "0.001"))
STRUCTURE_DISPLACEMENT_MIN = float(os.getenv("STRUCTURE_DISPLACEMENT_MIN", "0.0025"))
ORDER_BLOCK_DISPLACEMENT_MIN = float(os.getenv("ORDER_BLOCK_DISPLACEMENT_MIN", "0.0025"))

# Contract sizing defaults (used for position sizing); override per symbol if needed
CONTRACT_SIZE_BY_SYMBOL = {
    # "XAUUSD": 100,
}
