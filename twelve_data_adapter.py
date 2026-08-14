"""
SEKWAILA OMEGA X
Twelve Data market-data adapter.

Provides:
- latest price
- quote
- historical OHLC candles
- symbol normalization
- Streamlit Secrets / environment variable support
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

import requests


TWELVE_DATA_URL = "https://api.twelvedata.com"


# Twelve Data symbol mappings.
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

    # Common index aliases.
    "SP500": "SPX",
    "US30": "DJI",
    "NAS100": "NDX",
}


def get_api_key() -> str:
    """Read Twelve Data key from Streamlit Secrets or environment."""

    # Streamlit Cloud / Replit / local Streamlit.
    try:
        import streamlit as st

        for key_name in (
            "TWELVE_DATA_API_KEY",
            "TWELVEDATA_API_KEY",
        ):
            try:
                value = st.secrets.get(key_name, "")
            except Exception:
                value = ""

            if value:
                return str(value).strip()

    except Exception:
        pass

    # Local environment fallback.
    return (
        os.getenv("TWELVE_DATA_API_KEY")
        or os.getenv("TWELVEDATA_API_KEY")
        or ""
    ).strip()


def format_symbol(symbol: str) -> str:
    """Convert application symbol into Twelve Data format."""

    if not symbol:
        return ""

    clean = (
        str(symbol)
        .replace("/", "")
        .replace(" ", "")
        .replace("-", "")
        .upper()
        .strip()
    )

    return SYMBOL_MAP.get(clean, clean)


def _request(
    endpoint: str,
    params: Dict[str, Any],
    timeout: int = 12,
) -> Optional[Dict[str, Any]]:
    """Safe Twelve Data request."""

    api_key = get_api_key()

    if not api_key:
        return None

    request_params = dict(params)
    request_params["apikey"] = api_key

    try:
        response = requests.get(
            f"{TWELVE_DATA_URL}/{endpoint}",
            params=request_params,
            timeout=timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        if data.get("status") == "error":
            print(
                "[Twelve Data]",
                data.get("code", ""),
                data.get("message", "Unknown API error"),
            )
            return None

        return data

    except requests.RequestException as exc:
        print(f"[Twelve Data HTTP Error] {exc}")
        return None

    except ValueError as exc:
        print(f"[Twelve Data JSON Error] {exc}")
        return None

    except Exception as exc:
        print(f"[Twelve Data Error] {exc}")
        return None


def get_live_price(symbol: str) -> Optional[float]:
    """Return latest Twelve Data price."""

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    data = _request(
        "price",
        {
            "symbol": formatted,
        },
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


def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Return Twelve Data quote object."""

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    return _request(
        "quote",
        {
            "symbol": formatted,
        },
    )


def get_time_series(
    symbol: str,
    interval: str = "5min",
    outputsize: int = 100,
) -> Optional[Dict[str, Any]]:
    """Return raw Twelve Data time-series response."""

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    return _request(
        "time_series",
        {
            "symbol": formatted,
            "interval": interval,
            "outputsize": max(1, min(int(outputsize), 5000)),
        },
        timeout=20,
    )


def get_candles(
    symbol: str,
    interval: str = "5min",
    outputsize: int = 100,
) -> list[dict]:
    """Return normalized OHLC candles."""

    data = get_time_series(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
    )

    if not data:
        return []

    values = data.get("values", [])

    if not isinstance(values, list):
        return []

    candles = []

    for row in reversed(values):
        try:
            candles.append(
                {
                    "datetime": row.get("datetime"),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0) or 0),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    return candles


def is_connected(symbol: str = "XAUUSD") -> bool:
    """Simple connection test."""

    return get_live_price(symbol) is not None


__all__ = [
    "get_api_key",
    "format_symbol",
    "get_live_price",
    "get_quote",
    "get_time_series",
    "get_candles",
    "is_connected",
]
