"""
SEKWAILA OMEGA X
Market Data
"""

import yfinance as yf
import pandas as pd


def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")

        if data.empty:
            return {
                "success": False,
                "symbol": symbol,
                "price": 0,
            }

        return {
            "success": True,
            "symbol": symbol,
            "price": float(data["Close"].iloc[-1]),
        }

    except Exception:
        return {
            "success": False,
            "symbol": symbol,
            "price": 0,
        }


def get_all_prices():

    symbols = [
        "BTC-USD",
        "GC=F",
        "EURUSD=X",
    ]

    prices = []

    for symbol in symbols:
        prices.append(get_price(symbol))

    return prices


def get_candles(symbol):

    mapping = {
        "BTC/USD": "BTC-USD",
        "XAU/USD": "GC=F",
        "EUR/USD": "EURUSD=X",
    }

    ticker = mapping.get(symbol, symbol)

    try:

        df = yf.download(
            ticker,
            period="30d",
            interval="15m",
            progress=False,
            auto_adjust=True,
        )

        if df.empty:
            return pd.DataFrame()

        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        return df[
            [
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

    except Exception:
        return pd.DataFrame()
