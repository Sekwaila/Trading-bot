import yfinance as yf
import pandas as pd


MARKETS = {
    "BTCUSD": "BTC-USD",
    "XAUUSD": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "US30": "^DJI",
}


def get_price(symbol):

    try:
        df = yf.Ticker(MARKETS[symbol]).history(
            period="1d",
            interval="1m"
        )

        if df.empty:
            return None

        return float(df["Close"].iloc[-1])

    except Exception:
        return None


def get_h1(symbol):

    df = yf.Ticker(MARKETS[symbol]).history(
        period="30d",
        interval="60m"
    )

    if df.empty:
        return df

    df = df.rename(columns=str.lower)

    return df[
        ["open", "high", "low", "close", "volume"]
    ]
