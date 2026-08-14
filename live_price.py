"""
SEKWAILA OMEGA X — Twelve Data Live Price Adapter

Fetches real-time price quotes for Forex, Gold (XAUUSD), Crypto, and Stock Indices.
Uses the official Twelve Data Python SDK if installed, with a requests REST fallback.
"""

import os
import requests
from typing import Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", os.getenv("TWELVEDATA_API_KEY", "")).strip()


def _format_symbol_for_twelvedata(symbol: str) -> str:
    """Formats market symbol conventions for Twelve Data API standards.
    E.g., XAUUSD -> XAU/USD, EURUSD -> EUR/USD, BTCUSD -> BTC/USD
    """
    clean_sym = symbol.replace("/", "").strip().upper()
    
    # Forex and Metal pairs
    if len(clean_sym) == 6 and not clean_sym.startswith("US"):
        return f"{clean_sym[:3]}/{clean_sym[3:]}"
    
    # Crypto pairs like BTCUSD, ETHUSD
    if clean_sym.endswith("USD") and len(clean_sym) > 5 and not clean_sym.startswith("US"):
        base = clean_sym[:-3]
        return f"{base}/USD"
        
    return clean_sym


def get_live_price(symbol: str) -> Optional[float]:
    """Fetch the current real-time market price for a given asset symbol.

    Args:
        symbol (str): Asset ticker (e.g., 'XAUUSD', 'EURUSD', 'BTCUSD', 'AAPL')

    Returns:
        Optional[float]: Latest price float if successful, else None.
    """
    if not symbol:
        return None

    formatted_symbol = _format_symbol_for_twelvedata(symbol)

    # Method 1: Try official Twelve Data SDK if installed
    try:
        from twelvedata import TDClient
        if TWELVE_DATA_API_KEY:
            td = TDClient(apikey=TWELVE_DATA_API_KEY)
            res = td.price(symbol=formatted_symbol).as_json()
            if isinstance(res, dict) and "price" in res:
                return float(res["price"])
    except Exception:
        pass  # Fallback to direct HTTP REST request

    # Method 2: Direct REST Request (Lightweight & Reliable)
    try:
        url = "https://api.twelvedata.com/price"
        params = {"symbol": formatted_symbol}
        
        if TWELVE_DATA_API_KEY:
            params["apikey"] = TWELVE_DATA_API_KEY
        else:
            # Fallback demo key (Limited access to AAPL, EUR/USD, etc.)
            params["apikey"] = "demo"

        response = requests.get(url, params=params, timeout=8)
        data = response.json()

        if response.status_code == 200 and "price" in data:
            return float(data["price"])
        
        # Secondary fallback using /quote endpoint if /price fails
        quote_url = "https://api.twelvedata.com/quote"
        quote_res = requests.get(quote_url, params=params, timeout=8).json()
        if "close" in quote_res:
            return float(quote_res["close"])

    except Exception as exc:
        print(f"[TwelveData Adapter Error] Failed fetching price for {symbol}: {exc}")

    return None


__all__ = ["get_live_price"]
