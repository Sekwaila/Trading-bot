"""
SEKWAILA OMEGA X
Twelve Data Market Data Adapter
"""

import os
from typing import Optional, Dict, Any

import requests

try:
    import streamlit as st
except Exception:
    st = None


# ============================================================
# SECRET LOADER
# ============================================================

def get_twelve_data_key() -> str:
    """Load Twelve Data API key from Streamlit Secrets or env."""

    if st is not None:
        try:
            key = st.secrets.get(
                "TWELVE_DATA_API_KEY",
                ""
            )

            if key:
                return str(key).strip()

        except Exception:
            pass

    return os.getenv(
        "TWELVE_DATA_API_KEY",
        os.getenv(
            "TWELVEDATA_API_KEY",
            ""
        )
    ).strip()


TWELVE_DATA_API_KEY = get_twelve_data_key()

BASE_URL = "https://api.twelvedata.com"


# ============================================================
# SYMBOL MAP
# ============================================================

SYMBOL_MAP = {
    "XAUUSD": "XAU/USD",
    "XAGUSD": "XAG/USD",

    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "USDCHF": "USD/CHF",
    "AUDUSD": "AUD/USD",
    "NZDUSD": "NZD/USD",
    "USDCAD": "USD/CAD",

    "BTCUSD": "BTC/USD",
    "ETHUSD": "ETH/USD",
}


def format_symbol(symbol: str) -> str:
    """Convert internal symbol to Twelve Data format."""

    if not symbol:
        return ""

    clean = (
        symbol
        .replace("/", "")
        .replace("-", "")
        .strip()
        .upper()
    )

    return SYMBOL_MAP.get(
        clean,
        clean
    )


# ============================================================
# GENERIC REQUEST
# ============================================================

def _request(
    endpoint: str,
    params: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not TWELVE_DATA_API_KEY:
        return None

    params = dict(params)
    params["apikey"] = TWELVE_DATA_API_KEY

    try:

        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") == "error":
            print(
                "[Twelve Data Error]",
                data.get(
                    "message",
                    "Unknown API error"
                )
            )
            return None

        return data

    except requests.RequestException as exc:

        print(
            f"[Twelve Data Request Error] {exc}"
        )

    except ValueError as exc:

        print(
            f"[Twelve Data JSON Error] {exc}"
        )

    return None


# ============================================================
# LIVE PRICE
# ============================================================

def get_live_price(
    symbol: str
) -> Optional[float]:

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

        if price is not None:
            return float(price)

    except (TypeError, ValueError):
        pass

    return None


# ============================================================
# QUOTE
# ============================================================

def get_quote(
    symbol: str
) -> Optional[Dict[str, Any]]:

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
# CANDLES
# ============================================================

def get_candles(
    symbol: str,
    interval: str = "15min",
    outputsize: int = 100,
) -> list:

    formatted = format_symbol(symbol)

    if not formatted:
        return []

    data = _request(
        "time_series",
        {
            "symbol": formatted,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON",
        }
    )

    if not data:
        return []

    values = data.get(
        "values",
        []
    )

    return values


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection(
    symbol: str = "XAUUSD"
) -> Dict[str, Any]:

    if not TWELVE_DATA_API_KEY:

        return {
            "ok": False,
            "symbol": symbol,
            "price": None,
            "error": (
                "TWELVE_DATA_API_KEY "
                "is missing."
            ),
        }

    price = get_live_price(symbol)

    if price is None:

        return {
            "ok": False,
            "symbol": symbol,
            "price": None,
            "error": (
                "Twelve Data returned "
                "no price."
            ),
        }

    return {
        "ok": True,
        "symbol": symbol,
        "price": price,
        "error": None,
    }


__all__ = [
    "get_live_price",
    "get_quote",
    "get_candles",
    "test_connection",
    "format_symbol",
]
