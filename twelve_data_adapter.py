"""
Twelve Data Client Adapter - Optimized for Reduced Ticker Pair Set
"""

from typing import Optional
import pandas as pd
import requests


class TwelveDataClient:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def normalize_symbol(self, symbol: str) -> str:
        """Maps target symbols strictly to Twelve Data API expected format."""
        clean = symbol.strip().upper()

        mapping = {
            "XAUUSD": "XAU/USD",
            "XAU/USD": "XAU/USD",
            "GOLD": "XAU/USD",
            "BTCUSD": "BTC/USD",
            "BTC/USD": "BTC/USD",
            "US30": "DJI",
            "DJI": "DJI",
        }

        return mapping.get(clean, clean)

    def get_time_series(
        self, symbol: str, interval: str = "15m", outputsize: int = 50
    ) -> Optional[pd.DataFrame]:
        """Fetches historical time series from Twelve Data REST API."""
        if not self.api_key:
            return None

        target_symbol = self.normalize_symbol(symbol)

        params = {
            "symbol": target_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/time_series", params=params, timeout=10
            )
            data = response.json()

            if data.get("status") == "error" or "values" not in data:
                return None

            df = pd.DataFrame(data["values"])

            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.iloc[::-1].reset_index(drop=True)
            return df

        except Exception:
            return None


TwelveDataAdapter = TwelveDataClient
