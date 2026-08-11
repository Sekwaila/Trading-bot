# config.py

# Core assets (Twelve Data free plan supports these with intraday)
ASSETS = [
    "XAUUSD",
    "BTCUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "SPX500",
    "DXY",
    # "NAS100",   # Requires paid plan for intraday
    # "US30",     # Requires paid plan for intraday
]

# Timeframe configuration (used by engine)
TF_CONFIG = {
    "1D": {"label": "1D", "interval": "1day"},
    "4H": {"label": "4H", "interval": "4h"},
    "1H": {"label": "1H", "interval": "1h"},
    "15M": {"label": "15M", "interval": "15min"},
}

# Minimum number of timeframes in agreement to trigger a signal
DEFAULT_MIN_TF_AGREEMENT = 2

# Minimum score out of 100 for a signal to be valid
DEFAULT_MIN_SCORE = 60

# Minimum risk-reward ratio (R:R) required
DEFAULT_MIN_RR = 1.5

# Contract size for position sizing (used by helper functions)
CONTRACT_SIZE_BY_SYMBOL = {
    "XAUUSD": 100,
    "BTCUSD": 1,
    "EURUSD": 100000,
    "GBPUSD": 100000,
    "USDJPY": 100000,
    "SPX500": 50,
    "DXY": 1000,
    "NAS100": 100,
    "US30": 100,
}

# Minimum rows required per timeframe to consider data valid
MINIMUM_DATA_ROWS = 30

# Technical parameters
ATR_PERIOD = 14
SWING_WINDOW = 5
FVG_LOOKBACK = 50
EQUAL_LEVEL_LOOKBACK = 30
EQUAL_LEVEL_TOLERANCE = 0.003  # 0.3%
STRUCTURE_DISPLACEMENT_MIN = 0.005  # 0.5%
ORDER_BLOCK_DISPLACEMENT_MIN = 0.01  # 1%

# Logging
LOGGING_LEVEL = "INFO"
