import requests
from typing import Dict, List


class MarketData:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"


    def get_price(self, symbol: str):

        url = f"{self.base_url}/price"

        params = {
            "symbol": symbol,
            "apikey": self.api_key
        }

        r = requests.get(url, params=params, timeout=15)

        data = r.json()

        if "price" not in data:
            raise Exception(data)

        return float(data["price"])


    def get_candles(
        self,
        symbol: str,
        interval: str = "15min",
        outputsize: int = 500
    ):

        url = f"{self.base_url}/time_series"

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key
        }

        r = requests.get(url, params=params, timeout=20)

        data = r.json()

        if "values" not in data:
            raise Exception(data)

        candles = []

        for candle in reversed(data["values"]):

            candles.append({

                "datetime": candle["datetime"],

                "open": float(candle["open"]),

                "high": float(candle["high"]),

                "low": float(candle["low"]),

                "close": float(candle["close"]),

                "volume": float(candle.get("volume", 0))

            })

        return candles
