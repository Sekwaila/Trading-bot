import requests
import pandas as pd
import yfinance as yf
from config import TWELVE_DATA_API_KEY, ASSETS

def get_candles(symbol: str, interval: str = "5min", limit: int = 100) -> pd.DataFrame:
    """
    Fetches clean OHLCV candles from Twelve Data.
    Falls back seamlessly to Yahoo Finance if API limits or errors occur.
    """
    asset_info = ASSETS.get(symbol, {})
    twelve_symbol = asset_info.get("twelve", symbol)

    # 1. Primary: Twelve Data API
    if TWELVE_DATA_API_KEY and TWELVE_DATA_API_KEY != "YOUR_TWELVE_DATA_API_KEY":
        url = f"https://api.twelvedata.com/time_series?symbol={twelve_symbol}&interval={interval}&outputsize={limit}&apikey={TWELVE_DATA_API_KEY}"
        try:
            res = requests.get(url, timeout=8)
            data = res.json()
            if "values" in data:
                df = pd.DataFrame(data["values"])
                df['datetime'] = pd.to_datetime(df['datetime'])
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = df[col].astype(float)
                return df.sort_values('datetime').reset_index(drop=True)
        except Exception as e:
            print(f"[MarketData] Twelve Data fetch error for {symbol}: {e}")

    # 2. Fallback: Yahoo Finance
    yahoo_symbol = asset_info.get("yahoo", symbol)
    try:
        yf_interval = "5m" if interval == "5min" else "15m"
        df_yf = yf.download(tickers=yahoo_symbol, period="5d", interval=yf_interval, progress=False)
        if not df_yf.empty:
            df_yf = df_yf.reset_index()
            df_yf.rename(columns={
                "Datetime": "datetime", "Date": "datetime",
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume"
            }, inplace=True)
            return df_yf[['datetime', 'open', 'high', 'low', 'close']].tail(limit)
    except Exception as e:
        print(f"[MarketData] Yahoo Finance fallback error for {symbol}: {e}")

    return pd.DataFrame()
