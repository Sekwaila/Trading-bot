"""
SEKWAILA OMEGA X
Unified market-data layer.

Twelve Data is used for:
- Forex
- Gold
- Crypto
- supported indices/stocks

This module intentionally has no dependency on the SMC signal modules.
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests


TWELVE_DATA_URL = "https://api.twelvedata.com"


SYMBOL_MAP = {
    "XAUUSD": "XAU/USD",
    "XAU/USD": "XAU/USD",

    "EURUSD": "EUR/USD",
    "EUR/USD": "EUR/USD",

    "GBPUSD": "GBP/USD",
    "GBP/USD": "GBP/USD",

    "USDJPY": "USD/JPY",
    "USD/JPY": "USD/JPY",

    "AUDUSD": "AUD/USD",
    "AUD/USD": "AUD/USD",

    "USDCAD": "USD/CAD",
    "USD/CAD": "USD/CAD",

    "USDCHF": "USD/CHF",
    "USD/CHF": "USD/CHF",

    "NZDUSD": "NZD/USD",
    "NZD/USD": "NZD/USD",

    "BTCUSD": "BTC/USD",
    "BTC/USD": "BTC/USD",

    "ETHUSD": "ETH/USD",
    "ETH/USD": "ETH/USD",

    "SP500": "SPX",
    "SPX": "SPX",

    "US30": "DJI",
    "DJI": "DJI",

    "NAS100": "IXIC",
    "IXIC": "IXIC",
}


def _get_secret(name: str, default: str = "") -> str:
    """
    Reads a Streamlit secret first, then environment variable.
    """

    try:
        import streamlit as st

        value = st.secrets.get(name)

        if value:
            return str(value).strip()

    except Exception:
        pass

    return os.getenv(name, default).strip()


def get_api_key() -> str:
    return (
        _get_secret("TWELVE_DATA_API_KEY")
        or _get_secret("TWELVEDATA_API_KEY")
    )


def format_symbol(symbol: str) -> str:
    """
    Convert application symbols into Twelve Data symbols.
    """

    if not symbol:
        return ""

    raw = str(symbol).strip().upper()

    if raw in SYMBOL_MAP:
        return SYMBOL_MAP[raw]

    compact = raw.replace("/", "").replace(" ", "")

    if compact in SYMBOL_MAP:
        return SYMBOL_MAP[compact]

    # Generic six-character forex pair.
    if len(compact) == 6 and compact.isalpha():
        return f"{compact[:3]}/{compact[3:]}"

    return raw


def _request(endpoint: str, params: dict) -> Optional[dict]:
    api_key = get_api_key()

    if not api_key:
        return None

    request_params = dict(params)
    request_params["apikey"] = api_key

    try:
        response = requests.get(
            f"{TWELVE_DATA_URL}/{endpoint}",
            params=request_params,
            timeout=15,
        )

        data = response.json()

        if response.status_code != 200:
            print(
                f"[Twelve Data] HTTP {response.status_code}: "
                f"{data.get('message', 'Unknown error')}"
            )
            return None

        if data.get("status") == "error":
            print(
                f"[Twelve Data] "
                f"{data.get('code', '')}: "
                f"{data.get('message', 'Unknown error')}"
            )
            return None

        return data

    except requests.RequestException as exc:
        print(f"[Twelve Data request error] {exc}")
        return None

    except ValueError as exc:
        print(f"[Twelve Data JSON error] {exc}")
        return None


def get_live_price(symbol: str) -> Optional[float]:
    """
    Return latest available price.
    """

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
        return float(data["price"])
    except (KeyError, TypeError, ValueError):
        return None


def get_quote(symbol: str) -> Optional[dict]:
    """
    Return Twelve Data quote response.
    """

    formatted = format_symbol(symbol)

    if not formatted:
        return None

    return _request(
        "quote",
        {
            "symbol": formatted,
        },
    )


def get_candles(
    symbol: str,
    interval: str = "5min",
    limit: int = 100,
) -> pd.DataFrame:
    """
    Retrieve OHLC candles from Twelve Data.

    Returned columns:
        datetime
        open
        high
        low
        close
        volume
    """

    formatted = format_symbol(symbol)

    if not formatted:
        return pd.DataFrame()

    try:
        limit = max(10, min(int(limit), 5000))
    except Exception:
        limit = 100

    data = _request(
        "time_series",
        {
            "symbol": formatted,
            "interval": interval,
            "outputsize": limit,
            "order": "asc",
        },
    )

    if not data:
        return pd.DataFrame()

    values = data.get("values", [])

    if not values:
        return pd.DataFrame()

    rows = []

    for candle in values:
        try:
            rows.append(
                {
                    "datetime": candle.get("datetime"),
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": (
                        float(candle["volume"])
                        if candle.get("volume") not in (None, "")
                        else 0.0
                    ),
                }
            )
        except (TypeError, ValueError, KeyError):
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "open",
            "high",
            "low",
            "close",
        ]
    )

    df = df.sort_values("datetime")
    df = df.reset_index(drop=True)

    return df


__all__ = [
    "get_api_key",
    "format_symbol",
    "get_live_price",
    "get_quote",
    "get_candles",
]
