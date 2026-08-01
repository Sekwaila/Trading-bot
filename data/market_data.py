"""
SEKWAILA OMEGA X
Market Data
"""

import requests
import pandas as pd
from typing import List, Dict, Any

from logger import get_logger
from config import (
    TWELVEDATA_API_KEY,
    TIMEFRAME,
)

logger = get_logger("market_data")

BASE_URL = "https://api.twelvedata.com"

# Mapping of friendly symbol -> symbol sent to Twelve Data (kept the same here)
SYMBOLS = {
    "BTC/USD": "BTC/USD",
    "XAU/USD": "XAU/USD",
    "EUR/USD": "EUR/USD",
}


def get_price(symbol: str) -> Dict[str, Any]:
    """
    Fetch current price for a symbol from Twelve Data.
    Returns the raw JSON response. Caller must validate.
    """
    if not TWELVEDATA_API_KEY:
        logger.warning("TWELVEDATA_API_KEY is empty; get_price will request but likely fail.")
    url = f"{BASE_URL}/price"
    params = {
        "symbol": symbol,
        "apikey": TWELVEDATA_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            logger.warning("Unexpected response format for price: %s", data)
            return {}
        return data
    except Exception as e:
        logger.exception("get_price error for %s: %s", symbol, e)
        return {}


def get_candles(symbol: str, outputsize: int = 200) -> pd.DataFrame:
    """
    Fetch time series candles. Returns a pandas DataFrame with numeric columns or an empty DataFrame on failure.
    """
    if not TWELVEDATA_API_KEY:
        logger.warning("TWELVEDATA_API_KEY is empty; get_candles will request but likely fail.")

    url = f"{BASE_URL}/time_series"
    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": outputsize,
        "apikey": TWELVEDATA_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.exception("Failed to fetch candles for %s: %s", symbol, e)
        return pd.DataFrame()

    # Twelve Data returns an error message as {"code": ..., "message": ...} or missing 'values'
    if not isinstance(data, dict) or "values" not in data or not isinstance(data["values"], list):
        logger.warning("Invalid or empty candle data for %s: %s", symbol, data)
        return pd.DataFrame()

    try:
        df = pd.DataFrame(data["values"])
        # Convert time column to datetime if present; Twelve Data uses 'datetime'
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "time"})
            try:
                df["time"] = pd.to_datetime(df["time"])
            except Exception:
                pass
        # Convert numeric columns
        numeric = ["open", "high", "low", "close", "volume"]
        for col in numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # Data comes reversed (most recent first) -> reverse to chronological order
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    except Exception as e:
        logger.exception("Error processing candle data for %s: %s", symbol, e)
        return pd.DataFrame()


def get_all_prices() -> List[Dict[str, Any]]:
    """
    Returns a list of dicts: [{ 'symbol': str, 'price': float|None, 'success': bool }, ...]
    Always returns a list (maybe empty), never raises.
    """
    prices = []
    for symbol in SYMBOLS.keys():
        try:
            data = get_price(symbol)
            price = None
            success = False
            if isinstance(data, dict) and "price" in data:
                try:
                    price = float(data["price"])
                    success = True
                except Exception:
                    logger.warning("Price conversion failed for %s: %s", symbol, data.get("price"))
            else:
                logger.info("No price returned for %s: %s", symbol, data)
            prices.append({"symbol": symbol, "price": price, "success": success})
        except Exception:
            logger.exception("Unexpected exception retrieving price for %s", symbol)
            prices.append({"symbol": symbol, "price": None, "success": False})
    return prices
