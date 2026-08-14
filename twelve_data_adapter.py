"""
SEKWAILA OMEGA X
Twelve Data market-data adapter.

Provides:
- Live prices
- Quotes
- Candle/time-series data
- Streamlit Secrets support
"""

import os
from typing import Optional, Dict, Any

import requests


# ============================================================
# API KEY
# ============================================================

def get_api_key() -> str:
    """
    Get Twelve Data API key.

    Priority:
    1. Streamlit Secrets
    2. Environment variable
    """

    try:
        import streamlit as st

        key = st.secrets.get("TWELVE_DATA_API_KEY", "")

        if key:
            return str(key).strip()

    except Exception:
        pass

    return os.getenv(
        "TWELVE_DATA_API_KEY",
        os.getenv("TWELVEDATA_API_KEY", "")
    ).strip()


# ============================================================
# SYMBOL MAPPING
# ============================================================

SYMBOL_MAP = {
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD",
    "USDCHF": "USD/CHF",
    "NZDUSD": "NZD/USD",

    "BTCUSD": "BTC/USD",
    "ETHUSD": "ETH/USD",

    "SPX": "SPX",
    "SP500": "SPX",

    "US30": "DJI",
    "DOW": "DJI",
}


def format_symbol(symbol: str) -> str:
    """
    Convert internal symbols to Twelve Data symbols.
    """

    if not symbol:
        return ""

    clean = (
        str(symbol)
        .replace("/", "")
        .replace(" ", "")
        .upper()
        .strip()
    )

    return SYMBOL_MAP.get(clean, clean)


# ============================================================
# HTTP HELPER
# ============================================================

def _request(
    endpoint: str,
    params: Dict[str, Any]
) -> Optional[Dict[str, Any]]:

    api_key = get_api_key()

    if not api_key:
        return None

    params = dict(params)
    params["apikey"] = api_key

    try:
        response = requests.get(
            f"https://api.twelvedata.com/{endpoint}",
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        if data.get("status") == "error":
            print(
                "[Twelve Data Error]",
                data.get("message", "Unknown error")
            )
            return None

        return data

    except requests.RequestException as exc:
        print(
            f"[Twelve Data Request Error] {endpoint}: {exc}"
        )

    except ValueError as exc:
        print(
            f"[Twelve Data JSON Error] {endpoint}: {exc}"
        )

    except Exception as exc:
        print(
            f"[Twelve Data Error] {endpoint}: {exc}"
        )

    return None


# ============================================================
# LIVE PRICE
# ============================================================

def get_live_price(
    symbol: str
) -> Optional[float]:
    """
    Return latest available price.
    """

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    data = _request(
        "price",
        {
            "symbol": formatted
        }
    )

    if not data:
        return None

    try:
        price = data.get("price")

        if price is None:
            return None

        return float(price)

    except (TypeError, ValueError):
        return None


# ============================================================
# QUOTE
# ============================================================

def get_quote(
    symbol: str
) -> Optional[Dict[str, Any]]:
    """
    Return Twelve Data quote information.
    """

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    return _request(
        "quote",
        {
            "symbol": formatted
        }
    )


# ============================================================
# TIME SERIES
# ============================================================

def get_time_series(
    symbol: str,
    interval: str = "15min",
    outputsize: int = 100
) -> Optional[Dict[str, Any]]:
    """
    Get OHLC candle data.
    """

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    return _request(
        "time_series",
        {
            "symbol": formatted,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON",
        }
    )


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection(
    symbol: str = "XAUUSD"
) -> Dict[str, Any]:

    api_key = get_api_key()

    if not api_key:
        return {
            "connected": False,
            "message": "TWELVE_DATA_API_KEY is missing."
        }

    price = get_live_price(symbol)

    if price is None:
        return {
            "connected": False,
            "message": f"No price received for {symbol}."
        }

    return {
        "connected": True,
        "symbol": format_symbol(symbol),
        "price": price,
        "message": "Twelve Data connected."
    }


__all__ = [
    "get_api_key",
    "format_symbol",
    "get_live_price",
    "get_quote",
    "get_time_series",
    "test_connection",
]
