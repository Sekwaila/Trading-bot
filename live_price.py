"""
SEKWAILA OMEGA X — LIVE PRICE OVERLAY

Step 1:
- Prices are requested by OMEGA symbol, not by raw Yahoo ticker.
- No calibration/offset is applied.
- Yahoo Finance is still the current provider.
- MT5/broker integration can replace the provider without changing the UI.
"""

import time

import yfinance as yf
import streamlit as st

from config import ASSETS
from logger import get_logger

logger = get_logger("LIVE_PRICE")


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_live_price(ticker: str, _bucket: int):
    try:
        fi = yf.Ticker(ticker).fast_info
        value = fi.get("last_price") if isinstance(fi, dict) else getattr(fi, "last_price", None)
        if value is not None and float(value) > 0:
            return float(value)
    except Exception as exc:
        logger.warning("Live price fetch failed for %s: %s", ticker, exc)
    return None


def get_live_price(symbol: str):
    """
    Return the current Yahoo quote for an OMEGA symbol.

    The symbol is deliberately the OMEGA symbol (e.g. XAUUSD), while the
    provider ticker is resolved internally from config.ASSETS.

    No manual offset is applied here.
    """
    ticker = ASSETS.get(symbol)
    if not ticker:
        logger.warning("Unknown OMEGA symbol: %s", symbol)
        return None

    bucket = int(time.time() // 15)
    return _fetch_live_price(ticker, bucket)
