import pandas as pd
import yfinance as yf
from typing import Dict, Tuple, Optional
from config import config
from logger import logger

def compute_true_range(df_closed: pd.DataFrame) -> pd.Series:
    """Single source of truth for 3-term True Range computation."""
    high, low, close = df_closed["High"], df_closed["Low"], df_closed["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def fetch_institutional_data(symbol: str = config.SYMBOL) -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, str]]:
    tf_data = {}
    data_integrity = {}

    for tf_label, (period, interval) in config.TIMEFRAMES.items():
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty or len(df) < 30:
                raise ValueError(f"Insufficient candles fetched ({len(df)})")

            if tf_label == "4H":
                df = df.resample("4h").agg({
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum"
                }).dropna()

            tf_data[tf_label] = df
            data_integrity[tf_label] = "LIVE"
        except Exception as e:
            logger.warning(f"Failed fetching timeframe {tf_label}: {e}")
            tf_data[tf_label] = None
            data_integrity[tf_label] = f"UNAVAILABLE ({e})"

    return tf_data, data_integrity

def fetch_usdzar_rate() -> Optional[float]:
    try:
        df = yf.download("ZAR=X", period="5d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching USDZAR rate: {e}")
        return None

def compute_live_correlation_matrix() -> Optional[pd.DataFrame]:
    symbols = {
        "XAUUSD": "GC=F",
        "DXY": "DX-Y.NYB",
        "BTCUSD": "BTC-USD",
        "US30": "^DJI",
    }
    df_closes = pd.DataFrame()
    for name, ticker in symbols.items():
        try:
            d = yf.download(ticker, period="10d", interval="1h", progress=False)
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
            df_closes[name] = d["Close"]
        except Exception:
            pass

    if df_closes.shape[1] < 2:
        return None
    return df_closes.corr().round(2)
