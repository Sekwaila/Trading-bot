"""
SEKWAILA OMEGA X
Market Data Engine
Twelve Data (Free Plan)
"""

import requests
from config import TWELVEDATA_API_KEY

BASE_URL = "https://api.twelvedata.com"

SYMBOL_MAP = {
    "BTCUSD": "BTC/USD",
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "US30": "DJI",
}


def get_live_price(symbol: str):
    """
    Returns:
    {
        "symbol": "BTCUSD",
        "price": 118250.45,
        "change": 0.54,
        "success": True
    }
    """

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

            "price": float(data["price"]),

            "change": None

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
