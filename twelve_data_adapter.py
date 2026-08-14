"""
Twelve Data Adapter for SEKWAILA OMEGA X
Handles REST requests for stock, forex, crypto, and index market data.
"""

from typing import Any, Dict, List, Optional, Tuple
import requests


class TwelveDataAdapter:
    """Primary REST client for fetching live prices and historical candle data."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def get_price(self, symbol: str) -> Tuple[Optional[float], Optional[str]]:
        """Fetch the latest price for a single ticker symbol."""
        if not self.api_key:
            return None, "API Key missing"

        try:
            url = f"{self.base_url}/price?symbol={symbol}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()

            if "price" in data:
                return float(data["price"]), None
            return None, data.get("message", "Price unavailable")
        except Exception as e:
            return None, str(e)

    def get_candles(
        self, symbol: str, interval: str = "15min", outputsize: int = 50
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Fetch time-series candle data (OHLCV)."""
        if not self.api_key:
            return None, "API Key missing"

        # Standardize interval strings for Twelve Data format (e.g. '15m' -> '15min')
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1day",
        }
        formatted_interval = interval_map.get(interval, interval)

        try:
            url = (
                f"{self.base_url}/time_series?"
                f"symbol={symbol}&interval={formatted_interval}&"
                f"outputsize={outputsize}&apikey={self.api_key}"
            )
            response = requests.get(url, timeout=10)
            data = response.json()

            if "values" in data:
                return data["values"], None
            return None, data.get("message", "Candle data unavailable")
        except Exception as e:
            return None, str(e)


# Alias to resolve potential naming mismatches across codebase imports
TwelveDataClient = TwelveDataAdapter
