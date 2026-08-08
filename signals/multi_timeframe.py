import yfinance as yf
import pandas as pd
from config import TF_CONFIG
from .market_structure import analyze_market_structure

def fetch_mtf_data(ticker: str):
    data, integrity = {}, {}
    for tf, (period, interval) in TF_CONFIG.items():
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
            if df is None or df.empty: raise ValueError("Empty dataframe")
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df[["Open", "High", "Low", "Close"]].dropna()
            if tf == "4H":
                df = df.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
            data[tf] = df
            integrity[tf] = f"OK ({len(df)} bars)"
        except Exception as e:
            data[tf] = None
            integrity[tf] = f"ERROR: {e}"
    return data, integrity
