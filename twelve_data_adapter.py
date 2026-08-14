"""
SEKWAILA OMEGA X
Twelve Data market-data adapter.
"""

import os
from typing import Optional

import requests


def get_api_key() -> str:

    try:
        import streamlit as st

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
}


def format_symbol(symbol: str) -> str:

    clean = (
        symbol
        .replace("/", "")
        .replace(" ", "")
        .upper()
        .strip()
    )

    return SYMBOL_MAP.get(clean, clean)


def get_live_price(
    symbol: str
) -> Optional[float]:

    api_key = get_api_key()

    if not api_key:
        return None

    formatted = format_symbol(symbol)

    try:

        response = requests.get(
            "https://api.twelvedata.com/price",
            params={
                "symbol": formatted,
                "apikey": api_key,
            },
            timeout=10,
        )

        data = response.json()

        if data.get("status") == "error":
            print(
                "[Twelve Data]",
                data.get("message")
            )
            return None

        price = data.get("price")

        if price is None:
            return None

        return float(price)

    except Exception as exc:

        print(
            f"[Twelve Data error] {symbol}: {exc}"
        )

        return None


def get_quote(
    symbol: str
):

    api_key = get_api_key()

    if not api_key:
        return None

    formatted = format_symbol(symbol)

    try:

        response = requests.get(
            "https://api.twelvedata.com/quote",
            params={
                "symbol": formatted,
                "apikey": api_key,
            },
            timeout=10,
        )

        data = response.json()

        if data.get("status") == "error":
            return None

        return data

    except Exception as exc:

        print(
            f"[Twelve Data quote error] {symbol}: {exc}"
        )

        return None


__all__ = [
    "get_live_price",
    "get_quote",
    "format_symbol",
]
