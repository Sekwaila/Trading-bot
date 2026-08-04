"""
SEKWAILA OMEGA X
Market Data (Twelve Data)
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

    key = f"price:{symbol}"

    cached = _cached(key)

    if cached is not None:
        return cached

    try:

        r = requests.get(
            f"{BASE_URL}/price",
            params={
                "symbol": symbol,
                "apikey": TWELVEDATA_API_KEY,
            },
            timeout=15,
        )

        data = r.json()

        if "price" not in data:
            return None

        price = float(data["price"])

        _store(key, price)

        return price

    except Exception as e:
        logger.error(e)
        return None


def get_all_prices():

    prices = []

    for symbol in SYMBOLS:

        price = get_price(symbol)

        prices.append(
            {
                "symbol": symbol,
                "price": price if price else 0,
                "success": price is not None,
            }
        )

    return prices


def get_candles(
    symbol,
    interval="15min",
    outputsize=300,
):

    key = f"{symbol}:{interval}"

    cached = _cached(key)

    if cached is not None:
        return cached

    try:

        r = requests.get(
            f"{BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": TWELVEDATA_API_KEY,
            },
            timeout=20,
        )

        data = r.json()

        if "values" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])

        df = df.rename(
            columns={
                "datetime": "time",
            }
        )

        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:

            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce",
                )

        df = df.sort_values("time").reset_index(drop=True)

        _store(key, df)

        return df

    except Exception as e:

        logger.error(e)

        return pd.DataFrame()
