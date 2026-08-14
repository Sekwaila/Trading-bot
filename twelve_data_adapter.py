"""
Twelve Data Client Adapter
Provides standard methods for fetching OHLC time series data using REST requests.
"""

from typing import Optional
import pandas as pd
import requests


class TwelveDataClient:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def get_time_series(
        self, symbol: str, interval: str = "15m", outputsize: int = 50
    ) -> Optional[pd.DataFrame]:
        """Fetches historical time series from Twelve Data REST API."""
        if not self.api_key:
            return None

        # Clean symbol formatting for Twelve Data API (e.g. BTCUSD -> BTC/USD)
        formatted_symbol = symbol
        if (
            "USD" in symbol
            and "/" not in symbol
            and symbol not in ["SP500", "US30", "DXY"]
        ):
            formatted_symbol = symbol.replace("USD", "/USD")

        params = {
            "symbol": formatted_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/time_series", params=params, timeout=10
            )
            data = response.json()

            if "values" in data:
                df = pd.DataFrame(data["values"])
                # Parse OHLC to numeric float values
                for col in ["open", "high", "low", "close"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                # Reverse so index 0 is oldest and index -1 is latest
                df = df.iloc[::-1].reset_index(drop=True)
                return df
            else:
                return None
        except Exception:
            return None


# Class Aliases to prevent import attribute mismatch
TwelveDataAdapter = TwelveDataClient
