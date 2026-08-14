"""
Twelve Data Client Adapter - Enhanced Error Handling & Ticker Formatting
"""

from typing import Optional
import pandas as pd
import requests


class TwelveDataClient:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    def format_symbol(self, symbol: str) -> str:
        """Sanitizes ticker symbols for Twelve Data REST API."""
        clean_sym = symbol.strip().upper()

        # Handle Forex / Metals / Crypto formatting
        if clean_sym in ["XAUUSD", "XAU/USD", "GOLD"]:
            return "XAU/USD"
        elif clean_sym in ["BTCUSD", "BTC/USD"]:
            return "BTC/USD"
        elif clean_sym in ["EURUSD", "EUR/USD"]:
            return "EUR/USD"
        elif clean_sym in ["GBPUSD", "GBP/USD"]:
            return "GBP/USD"
        elif clean_sym in ["USDJPY", "USD/JPY"]:
            return "USD/JPY"

        return clean_sym

    def get_time_series(
        self, symbol: str, interval: str = "15m", outputsize: int = 50
    ) -> Optional[pd.DataFrame]:
        """Fetches historical time series from Twelve Data REST API."""
        if not self.api_key:
            print("[ERROR] Missing API Key.")
            return None

        formatted_symbol = self.format_symbol(symbol)

        params = {
            "symbol": formatted_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/time_series", params=params, timeout=12
            )
            data = response.json()

            # Handle Twelve Data API Errors (Rate Limit, Invalid Symbol, etc.)
            if data.get("status") == "error" or "values" not in data:
                err_msg = data.get("message", "Unknown Twelve Data API error.")
                print(
                    f"[TwelveData Error] Symbol: {formatted_symbol} | Msg: {err_msg}"
                )
                return None

            df = pd.DataFrame(data["values"])

            # Convert columns to numeric values
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Reverse dataframe so chronologically older candles come first
            df = df.iloc[::-1].reset_index(drop=True)
            return df

        except Exception as e:
            print(f"[Exception] Failed fetching {formatted_symbol}: {str(e)}")
            return None


# Class Aliases for compatibility
TwelveDataAdapter = TwelveDataClient
