"""
SEKWAILA OMEGA X
Market Data
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

# Simple in-memory cache
_cache = {}
CACHE_SECONDS = 60


def _cached(key):
    if key not in _cache:
        return None

    ts, value = _cache[key]

    if time.time() - ts > CACHE_SECONDS:
        return None

    return value


def _store(key, value):
    _cache[key] = (time.time(), value)


def get_price(symbol):

    cache_key = f"price:{symbol}"

    cached = _cached(cache_key)

    if cached is not None:
        return cached

    try:

        response = requests.get(
            f"{BASE_URL}/price",
            params={
                "symbol": symbol,
                "apikey": TWELVEDATA_API_KEY,
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if "price" not in data:
            logger.warning("No price returned for %s: %s", symbol, data)
            return None

        price = float(data["price"])

        _store(cache_key, price)

        return price

    except Exception:
        logger.exception("get_price error for %s", symbol)
        return None


def get_all_prices():

    prices = []

    for symbol in SYMBOLS:

        price = get_price(symbol)

        prices.append(
            {
                "symbol": symbol,
                "price": price if price is not None else 0.0,
                "success": price is not None,
            }
        )

    return prices


def get_candles(symbol, interval="15min", outputsize=200):

    cache_key = f"candles:{symbol}:{interval}"

    cached = _cached(cache_key)

    if cached is not None:
        return cached

    try:

        response = requests.get(
            f"{BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": TWELVEDATA_API_KEY,
            },
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if "values" not in data:
            logger.warning("No candles for %s: %s", symbol, data)
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])

        df = df.rename(
            columns={
                "datetime": "time",
            }
        )

        numeric = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for col in numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values("time").reset_index(drop=True)

        _store(cache_key, df)

        return df

    except Exception:
        logger.exception("Failed to fetch candles for %s", symbol)
        return pd.DataFrame()
