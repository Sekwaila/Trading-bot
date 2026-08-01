"""
SEKWAILA OMEGA X
Market Data Engine
Twelve Data
"""

import requests
import pandas as pd

from config import TWELVEDATA_API_KEY

BASE_URL = "https://api.twelvedata.com"

SYMBOL_MAP = {
    "BTCUSD": "BTC/USD",
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "US30": "DJI",
}


def get_live_price(symbol):

    if symbol not in SYMBOL_MAP:
        return {
            "success": False,
            "error": "Unknown symbol"
        }

    url = f"{BASE_URL}/price"

    params = {
        "symbol": SYMBOL_MAP[symbol],
        "apikey": TWELVEDATA_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if "price" not in data:
            return {
                "success": False,
                "error": data
            }

        return {
            "success": True,
            "symbol": symbol,
            "price": float(data["price"])
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def get_all_prices():

    prices = []

    for symbol in SYMBOL_MAP:
        prices.append(
            get_live_price(symbol)
        )

    return prices


def get_market_data(symbol, interval="15min", outputsize=200):

    if symbol not in SYMBOL_MAP:
        return pd.DataFrame()

    url = f"{BASE_URL}/time_series"

    params = {
        "symbol": SYMBOL_MAP[symbol],
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVEDATA_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if "values" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["values"])

        df = df.rename(columns={
            "datetime": "time"
        })

        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        df = df.iloc[::-1].reset_index(drop=True)

        return df

    except Exception:

        return pd.DataFrame()
