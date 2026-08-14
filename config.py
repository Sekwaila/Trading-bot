import os

# --- TELEGRAM BOT CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# --- DATA PROVIDER API KEYS ---
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "YOUR_TWELVE_DATA_API_KEY")
DERIV_API_KEY = os.getenv("DERIV_API_KEY", "YOUR_DERIV_API_KEY")

# --- ASSETS MAPPING ---
ASSETS = {
    "XAUUSD": {"twelve": "XAU/USD", "deriv": "frxXAUUSD", "yahoo": "GC=F"},
    "BTCUSD": {"twelve": "BTC/USD", "deriv": "cryBTCUSD", "yahoo": "BTC-USD"},
    "EURUSD": {"twelve": "EUR/USD", "deriv": "frxEURUSD", "yahoo": "EURUSD=X"},
    "GBPUSD": {"twelve": "GBP/USD", "deriv": "frxGBPUSD", "yahoo": "GBPUSD=X"},
    "US30":   {"twelve": "DJI",     "deriv": "SPCUSD",   "yahoo": "^DJI"},
    "NAS100":  {"twelve": "NDX",     "deriv": "NASUSD",   "yahoo": "^NDX"}
}

# --- ENGINE PARAMETERS ---
DEFAULT_MIN_TF_AGREEMENT = 2
DEFAULT_MIN_SCORE = 65.0
DEFAULT_MIN_RR = 1.5
WORKER_POLL_SECONDS = 10
SIGNAL_COOLDOWN_SECONDS = 300
