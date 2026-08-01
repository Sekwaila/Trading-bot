"""
SEKWAILA OMEGA X
Market Data
"""

import requests
import pandas as pd

from config import (
    TWELVEDATA_API_KEY,
    TIMEFRAME,
)

BASE_URL = "https://api.twelvedata.com"

SYMBOLS = {
    "BTC/USD": "BTC/USD",
    "XAU/USD": "XAU/USD",
    "EUR/USD": "EUR/USD",
}


def get_price(symbol):

    url = f"{BASE_URL}/price"

    params = {
        "symbol": symbol,
        "apikey": TWELVEDATA_API_KEY
    }

    response = requests.get(url, params=params, timeout=10)

    return response.json()


def get_candles(symbol, outputsize=200):

    url = f"{BASE_URL}/time_series"

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": outputsize,
        "apikey": TWELVEDATA_API_KEY
    }

    response = requests.get(url, params=params, timeout=15)

    data = response.json()

    if "values" not in data:
        return pd.DataFrame()

    df = pd.DataFrame(data["values"])

    df = df.rename(columns={"datetime": "time"})

    numeric = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])

    df = df.iloc[::-1].reset_index(drop=True)

    return df


def get_all_prices():

    prices = []

    for symbol in SYMBOLS:

        try:

            data = get_price(symbol)

            prices.append({

                "symbol": symbol,

                "price": float(data["price"]),

                "success": True

            })

        except Exception:

            prices.append({

                "symbol": symbol,

                "price": None,

                "success": False

            })

    return prices
