"""
SEKWAILA OMEGA X — LIVE PRICE OVERLAY

signals/signal_engine.py deliberately bases `entry` on the LAST CLOSED
candle (see analyze the engine's `_closed()` helper) — this is intentional,
so a signal's levels don't shift mid-candle. The tradeoff: on a 15-minute
timeframe, `entry` can lag the real market by up to ~15 minutes.

This module fetches a genuine live tick separately, so the dashboard can
show both: the live price (comparable to what TradingView/MT5 show you
right now) and the engine's entry price (what the signal was actually
built from). They're expected to differ slightly — that's not a bug, it's
the lag between "closed candle" and "right now."
"""

import time

import yfinance as yf
import streamlit as st

from logger import get_logger

logger = get_logger("LIVE_PRICE")


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_live_price(ticker: str, _bucket: int):
    try:
        fi = yf.Ticker(ticker).fast_info
        price = fi.get("last_price") if isinstance(fi, dict) else getattr(fi, "last_price", None)
        if price and price > 0:
            return float(price)
    except Exception as exc:
        logger.warning("Live price fetch failed for %s: %s", ticker, exc)
    return None


def get_live_price(ticker: str):
    """Real-time-ish quote, cached 15s. Returns None if unavailable — callers
    should fall back to the engine's entry price in that case."""
    bucket = int(time.time() // 15)
    return _fetch_live_price(ticker, bucket)
