"""
Twelve Data Client Adapter - Enhanced Error Handling & Ticker Normalization
"""

from typing import Optional
import pandas as pd
import requests


class TwelveDataClient:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def normalize_symbol(self, symbol: str) -> str:
        """Translates common user input tickers into Twelve Data API format."""
        clean = symbol.strip().upper()

        mapping = {
            "XAU/USD": "XAU/USD",
            "XAUUSD": "XAU/USD",
            "GOLD": "XAU/USD",
            "BTC/USD": "BTC/USD",
            "BTCUSD": "BTC/USD",
            "EUR/USD": "EUR/USD",
            "EURUSD": "EUR/USD",
            "GBP/USD": "GBP/USD",
            "GBPUSD": "GBP/USD",
            "USD/JPY": "USD/JPY",
            "USDJPY": "USD/JPY",
            "SP500": "SPX",
            "US30": "DJI",
            "DXY": "DXY",
        }

        return mapping.get(clean, clean)

    def get_time_series(
        self, symbol: str, interval: str = "15m", outputsize: int = 50
    ) -> Optional[pd.DataFrame]:
        """Fetches historical time series from Twelve Data REST API."""
        if not self.api_key:
            print("[TwelveData] Missing API key.")
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

            # Check for Twelve Data error payloads (e.g. rate limits or bad keys)
            if data.get("status") == "error" or "values" not in data:
                error_msg = data.get("message", "Unknown API error")
                print(
                    f"[TwelveData API Error] Ticker: {target_symbol} | Detail: {error_msg}"
                )
                return None

            df = pd.DataFrame(data["values"])

            # Format numeric columns
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Reverse dataframe so chronological order starts at index 0
            df = df.iloc[::-1].reset_index(drop=True)
            return df

        except Exception as e:
            print(f"[TwelveData Exception] {target_symbol}: {str(e)}")
            return None


# Class Alias
TwelveDataAdapter = TwelveDataClient
