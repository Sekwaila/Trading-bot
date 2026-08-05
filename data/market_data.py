"""
SEKWAILA OMEGA X
Market Data (Twelve Data)
Improved with:
- Automatic retries (3 attempts)
- Quota detection (429 and message)
- HTTP status checking (raise_for_status)
- Price validation (>0)
- Candle data validation (columns, dropna)
- Persistent session (reuses connections)
"""

import time
import requests
import pandas as pd

from config import (
    SYMBOLS,
    TWELVEDATA_API_KEY,
)
from logger import get_logger

logger = get_logger("market_data")

BASE_URL = "https://api.twelvedata.com"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
CACHE_SECONDS = 60

# Persistent session
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SEKWAILA-OMEGA-X/1.0"})

_cache = {}


def _cached(key):
    """Return cached value if still fresh."""
    if key not in _cache:
        return None
    ts, value = _cache[key]
    if time.time() - ts > CACHE_SECONDS:
        return None
    return value


def _store(key, value):
    _cache[key] = (time.time(), value)


def _get_with_retry(url, params, timeout=20):
    """
    Perform GET request with automatic retries.
    Raises exception after max retries.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            response.raise_for_status()  # raises HTTPError for 4xx/5xx
            return response
        except requests.exceptions.HTTPError as e:
            # Check if it's a quota error (429 or message)
            if response.status_code == 429:
                logger.warning("Twelve Data quota exceeded (HTTP 429)")
            elif "quota" in response.text.lower():
                logger.warning("API quota exceeded (message)")
            if attempt == MAX_RETRIES - 1:
                raise
            logger.warning(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            logger.warning(f"Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Max retries exceeded")


def get_price(symbol):
    """
    Fetch current price for a single symbol.
    Returns float or None.
    """
    key = f"price:{symbol}"
    cached = _cached(key)
    if cached is not None:
        return cached

    try:
        response = _get_with_retry(
            f"{BASE_URL}/price",
            params={"symbol": symbol, "apikey": TWELVEDATA_API_KEY},
            timeout=15
        )
        data = response.json()
        if "price" not in data:
            logger.error(f"Price missing in response for {symbol}")
            return None

        price = float(data["price"])
        if price <= 0:
            logger.warning(f"Invalid price for {symbol}: {price}")
            return None

        _store(key, price)
        return price

    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {e}")
        return None


def get_all_prices():
    """Fetch prices for all configured symbols."""
    prices = []
    for symbol in SYMBOLS:
        price = get_price(symbol)
        prices.append({
            "symbol": symbol,
            "price": price if price else 0,
            "success": price is not None,
        })
    return prices


def get_candles(symbol, interval="15min", outputsize=300):
    """
    Fetch OHLCV candles for a symbol.
    Returns DataFrame with columns: time, open, high, low, close, volume.
    Returns empty DataFrame on failure.
    """
    key = f"{symbol}:{interval}"
    cached = _cached(key)
    if cached is not None:
        return cached

    try:
        response = _get_with_retry(
            f"{BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": TWELVEDATA_API_KEY,
            },
            timeout=20
        )
        data = response.json()

        if "values" not in data:
            logger.warning(f"No 'values' in response for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])
        if df.empty:
            return pd.DataFrame()

        # Rename and convert types
        df = df.rename(columns={"datetime": "time"})
        required = ["open", "high", "low", "close"]
        # Ensure required columns exist
        missing = [col for col in required if col not in df.columns]
        if missing:
            logger.error(f"Missing columns {missing} for {symbol}")
            return pd.DataFrame()

        for col in required + ["volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows with NaN in required columns
        df = df.dropna(subset=required)
        if df.empty:
            logger.warning(f"All rows dropped for {symbol} (invalid OHLC)")
            return pd.DataFrame()

        # Ensure volume exists, default to 0
        if "volume" not in df.columns:
            df["volume"] = 0
        else:
            df["volume"] = df["volume"].fillna(0)

        df = df.sort_values("time").reset_index(drop=True)

        _store(key, df)
        return df

    except Exception as e:
        logger.error(f"Failed to fetch candles for {symbol}: {e}")
        return pd.DataFrame()
