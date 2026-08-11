"""
SEKWAILA OMEGA X — SIGNAL ENGINE
Step 1: Twelve Data is the active market-data provider.

Provider rules:
- TWELVE_DATA_API_KEY is read from the environment / Streamlit Secrets.
- No calibration.py dependency.
- Missing provider data is unavailable, never converted into a valid/neutral signal.
- The existing indicator/structure logic remains downstream of the provider.
"""

import datetime
import math
import os
import time
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests

try:
    from zoneinfo import ZoneInfo
    _TZ_OK = True
except Exception:
    _TZ_OK = False

from config import (
    ASSETS, TF_CONFIG, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR, CONTRACT_SIZE_BY_SYMBOL, MINIMUM_DATA_ROWS,
    ATR_PERIOD, SWING_WINDOW, FVG_LOOKBACK, EQUAL_LEVEL_LOOKBACK,
    EQUAL_LEVEL_TOLERANCE, STRUCTURE_DISPLACEMENT_MIN,
    ORDER_BLOCK_DISPLACEMENT_MIN,
)
from logger import get_logger

logger = get_logger("ENGINE")

TWELVE_DATA_BASE_URL = "https://api.twelvedata.com/time_series"
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
_TD_TIMEOUT = 20
_TD_RETRIES = 2
_TD_RETRY_SECONDS = 3

# Twelve Data uses these intervals directly.
TD_INTERVALS = {
    "1D": "1day",
    "4H": "4h",
    "1H": "1h",
    "15M": "15min",
}

# Provider symbols. These are deliberately separate from the dashboard symbol.
TD_SYMBOLS = {
    "XAUUSD": "XAU/USD",
    "NAS100": "NDX",
    "US30": "DJI",
    "BTCUSD": "BTC/USD",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "SPX500": "SPX",
    "DXY": "DXY",
}

# Requested history. Kept moderate for free-plan usage.
TD_OUTPUTSIZE = {
    "1D": 180,
    "4H": 60 * 6,
    "1H": 30 * 24,
    "15M": 7 * 24 * 4,
}


def _safe_float(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else float(default)
    except Exception:
        return float(default)


def _clean_ohlcv(df: Any) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    df = df.copy()
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in df.columns for c in required):
        return pd.DataFrame()

    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)

    try:
        df.index = pd.to_datetime(df.index, utc=True)
    except Exception:
        pass

    return df[~df.index.duplicated(keep="last")].sort_index()


def _twelve_data_symbol(symbol: str) -> str:
    return TD_SYMBOLS.get(symbol, symbol)


def _twelve_data_request(symbol: str, interval: str, outputsize: int) -> pd.DataFrame:
    api_key = os.getenv("TWELVE_DATA_API_KEY", TWELVE_DATA_API_KEY).strip()

    if not api_key:
        logger.error("TWELVE_DATA_API_KEY is missing.")
        return pd.DataFrame()

    params = {
        "symbol": _twelve_data_symbol(symbol),
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
        "format": "JSON",
        "order": "ASC",
    }

    last_error = None

    for attempt in range(_TD_RETRIES + 1):
        try:
            response = requests.get(
                TWELVE_DATA_BASE_URL,
                params=params,
                timeout=_TD_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, dict):
                last_error = "Invalid Twelve Data response."
                break

            if payload.get("status") == "error" or payload.get("code"):
                message = payload.get("message", "Twelve Data returned an error.")
                last_error = str(message)
                logger.warning(
                    "Twelve Data error for %s/%s: %s",
                    symbol, interval, last_error
                )

                # Do not retry authentication/symbol/plan errors.
                low = last_error.lower()
                if any(x in low for x in (
                    "api key", "apikey", "invalid", "permission",
                    "not available", "symbol", "plan", "credits",
                    "trial", "subscription"
                )):
                    break

                if attempt < _TD_RETRIES:
                    time.sleep(_TD_RETRY_SECONDS * (attempt + 1))
                    continue
                break

            values = payload.get("values")
            if not values:
                last_error = "Twelve Data returned no values."
                break

            rows = []
            for item in values:
                try:
                    rows.append({
                        "Datetime": item.get("datetime"),
                        "Open": item.get("open"),
                        "High": item.get("high"),
                        "Low": item.get("low"),
                        "Close": item.get("close"),
                        "Volume": item.get("volume", 0),
                    })
                except Exception:
                    continue

            if not rows:
                last_error = "Twelve Data returned no usable OHLC rows."
                break

            df = pd.DataFrame(rows).set_index("Datetime")
            return _clean_ohlcv(df)

        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Twelve Data request failure for %s/%s: %s",
                symbol, interval, exc
            )
            if attempt < _TD_RETRIES:
                time.sleep(_TD_RETRY_SECONDS * (attempt + 1))

    logger.warning(
        "Twelve Data unavailable for %s/%s: %s",
        symbol, interval, last_error or "unknown error"
    )
    return pd.DataFrame()


def _validate_timeframe(tf_label: str, df: pd.DataFrame) -> Tuple[bool, str]:
    if df is None or df.empty:
        return False, "UNAVAILABLE (Twelve Data returned no data)"
    if len(df) < MINIMUM_DATA_ROWS:
        return False, f"UNAVAILABLE (Insufficient data returned ({len(df)} rows))"
    return True, "LIVE"


def fetch_mtf_data(symbol_or_ticker):
    """
    Fetch all configured timeframes from Twelve Data.

    The first argument is intentionally accepted as either the dashboard
    symbol or a legacy ticker so existing callers remain compatible.
    """
    symbol = symbol_or_ticker
    if symbol not in TD_SYMBOLS:
        reverse = {v: k for k, v in TD_SYMBOLS.items()}
        symbol = reverse.get(symbol_or_ticker, symbol_or_ticker)

    tf_data, integrity = {}, {}

    for tf_label in ("1D", "4H", "1H", "15M"):
        interval = TD_INTERVALS[tf_label]
        outputsize = TD_OUTPUTSIZE[tf_label]

        try:
            df = _twelve_data_request(symbol, interval, outputsize)
            ok, status = _validate_timeframe(tf_label, df)

            if not ok:
                tf_data[tf_label] = None
                integrity[tf_label] = status
                logger.warning("%s %s data failure: %s", symbol, tf_label, status)
            else:
                tf_data[tf_label] = df
                integrity[tf_label] = "LIVE"
        except Exception as exc:
            tf_data[tf_label] = None
            integrity[tf_label] = f"UNAVAILABLE ({exc})"
            logger.warning("%s %s data failure: %s", symbol, tf_label, exc)

    return tf_data, integrity


def get_live_price(symbol):
    """Return the latest Twelve Data quote for a dashboard symbol."""
    api_key = os.getenv("TWELVE_DATA_API_KEY", TWELVE_DATA_API_KEY).strip()
    if not api_key:
        return None

    try:
        response = requests.get(
            "https://api.twelvedata.com/quote",
            params={
                "symbol": _twelve_data_symbol(symbol),
                "apikey": api_key,
                "format": "JSON",
            },
            timeout=_TD_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") == "error" or payload.get("code"):
            logger.warning(
                "Twelve Data quote error for %s: %s",
                symbol, payload.get("message", "unknown error")
            )
            return None

        value = _safe_float(payload.get("close"))
        return value if value > 0 else None
    except Exception as exc:
        logger.warning("Twelve Data live price failed for %s: %s", symbol, exc)
        return None


def fetch_usdzar_rate():
    try:
        d = _twelve_data_request("USD/ZAR", "1day", 5)
        if d.empty:
            return None
        value = _safe_float(d["Close"].iloc[-1])
        return value if value > 0 else None
    except Exception as exc:
        logger.warning("USDZAR fetch failed: %s", exc)
        return None


def compute_live_correlation_matrix():
    closes = {}
    for name in ASSETS:
        try:
            d = _twelve_data_request(name, "1h", 240)
            if not d.empty:
                closes[name] = d["Close"]
        except Exception as exc:
            logger.warning("Correlation fetch failed for %s: %s", name, exc)
    frame = pd.DataFrame(closes)
    return frame.corr().round(2) if frame.shape[1] >= 2 else None


def _closed(df):
    if df is None or len(df) < 2:
        return pd.DataFrame()
    return df.iloc[:-1].copy()


def compute_rsi(df_closed, period=14):
    if df_closed is None or len(df_closed) < period + 2:
        return 50.0
    delta = df_closed["Close"].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    al = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = ag / al.replace(0, np.nan)
    value = (100 - 100/(1+rs)).iloc[-1]
    return 50.0 if pd.isna(value) else float(np.clip(value, 0, 100))


def compute_macd_trend(df_closed):
    if df_closed is None or len(df_closed) < 35:
        return "NEUTRAL", 0.0, 0.0
    close = df_closed["Close"]
    line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    sig = line.ewm(span=9, adjust=False).mean()
    lv, sv = _safe_float(line.iloc[-1]), _safe_float(sig.iloc[-1])
    return ("BULLISH" if lv > sv else "BEARISH" if lv < sv else "NEUTRAL"), lv, sv


def compute_vwap_status(df_closed):
    if df_closed is None or df_closed.empty:
        return "UNKNOWN", 0.0
    typical = (df_closed["High"] + df_closed["Low"] + df_closed["Close"]) / 3
    volume = df_closed["Volume"].fillna(0)
    cv = volume.cumsum()
    vwap = (_safe_float(df_closed["Close"].iloc[-1]) if cv.iloc[-1] <= 0 else
            _safe_float((typical * volume).cumsum().div(cv.replace(0, np.nan)).iloc[-1]))
    close = _safe_float(df_closed["Close"].iloc[-1])
    return ("ABOVE" if close > vwap else "BELOW" if close < vwap else "AT"), vwap


def vol_status_label(vol_ratio):
    return "HIGH" if vol_ratio >= 1.40 else "LOW" if vol_ratio <= 0.85 else "NORMAL"


def compute_ema_cross(df_closed):
    if df_closed is None or len(df_closed) < 50:
        return "NEUTRAL"
    close = df_closed["Close"]
    e20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    e50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    return "BULLISH" if e20 > e50 else "BEARISH" if e20 < e50 else "NEUTRAL"


def compute_true_range(df_closed):
    if df_closed is None or df_closed.empty:
        return pd.Series(dtype=float)
    h, l, c = df_closed["High"], df_closed["Low"], df_closed["Close"]
    return pd.concat([(h-l), (h-c.shift(1)).abs(), (l-c.shift(1)).abs()], axis=1).max(axis=1)


def compute_atr(df_closed, period=ATR_PERIOD):
    if df_closed is None or len(df_closed) < period + 2:
        return 0.0
    atr = compute_true_range(df_closed).ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    return _safe_float(atr.iloc[-1])


def compute_adx(df, length=14):
    d = _closed(df)
    if d is None or len(d) < length * 2 + 5:
        return 20.0
    h, l = d["High"], d["Low"]
    up, down = h.diff(), -l.diff()
    plus = pd.Series(np.where((up > down) & (up > 0), up, 0), index=d.index)
    minus = pd.Series(np.where((down > up) & (down > 0), down, 0), index=d.index)
    tr = compute_true_range(d)
    atr = tr.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    ps = plus.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    ms = minus.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    pdi, mdi = 100*ps/(atr+1e-9), 100*ms/(atr+1e-9)
    dx = ((pdi-mdi).abs()/(pdi+mdi).replace(0, np.nan))*100
    return _safe_float(dx.ewm(alpha=1/length, adjust=False, min_periods=length).mean().iloc[-1], 20.0)


def compute_market_regime(df):
    d = _closed(df)
    if d.empty:
        return {"regime":"UNKNOWN","adx":0.0,"vol_ratio":1.0,"slope":0.0}
    adx = compute_adx(df)
    tr = compute_true_range(d)
    fast, slow = tr.rolling(7).mean().iloc[-1], tr.rolling(28).mean().iloc[-1]
    vol = _safe_float(fast/slow, 1.0) if pd.notna(slow) and slow > 0 else 1.0
    y = d["Close"].tail(20).values
    slope = np.polyfit(np.arange(len(y)), y, 1)[0] if len(y) >= 2 else 0.0
    regime = ("TRENDING_EXPANSION" if adx >= 25 and vol >= 1.10
              else "ACCUMULATION_DISTRIBUTION" if adx < 20 and vol < .85
              else "HIGH_VOLATILITY_RANGE" if vol >= 1.40
              else "CHOP_LOW_VOLATILITY")
    return {"regime":regime,"adx":round(adx,2),"vol_ratio":round(vol,2),"slope":round(_safe_float(slope),4)}


def find_swing_points(df_closed, window=SWING_WINDOW):
    if df_closed is None or len(df_closed) < 2*window+1:
        return np.array([], dtype=int), np.array([], dtype=int)
    h, l = df_closed["High"], df_closed["Low"]
    mx = h.rolling(2*window+1, center=True).max()
    mn = l.rolling(2*window+1, center=True).min()
    return np.where(((h == mx) & mx.notna()).values)[0], np.where(((l == mn) & mn.notna()).values)[0]


def measure_displacement(df, index):
    if df is None or index < 0 or index+3 >= len(df):
        return 0.0
    hi, lo = _safe_float(df["High"].iloc[index]), _safe_float(df["Low"].iloc[index])
    if hi <= 0 or lo <= 0:
        return 0.0
    future = df.iloc[index+1:index+4]
    return max(0.0, float((future["High"].max()-hi)/hi), float((lo-future["Low"].min())/lo))


def analyze_market_structure(df):
    d = _closed(df)
    if d.empty:
        return "NEUTRAL","NONE",None,None
    sh, sl = find_swing_points(d)
    if len(sh) < 2 or len(sl) < 2:
        return "NEUTRAL","NONE",None,None
    last_sh, prev_sh = _safe_float(d["High"].iloc[sh[-1]]), _safe_float(d["High"].iloc[sh[-2]])
    last_sl, prev_sl = _safe_float(d["Low"].iloc[sl[-1]]), _safe_float(d["Low"].iloc[sl[-2]])
    close = _safe_float(d["Close"].iloc[-1])
    prior_bull, prior_bear = last_sh > prev_sh and last_sl > prev_sl, last_sh < prev_sh and last_sl < prev_sl
    if close > last_sh:
        disp = (close-last_sh)/max(last_sh,1e-9)
        base = "BULLISH_CHoCH" if prior_bear else "BULLISH_BOS"
        return "BUY", base if disp >= STRUCTURE_DISPLACEMENT_MIN else base+"_WEAK", last_sh,last_sl
    if close < last_sl:
        disp = (last_sl-close)/max(last_sl,1e-9)
        base = "BEARISH_CHoCH" if prior_bull else "BEARISH_BOS"
        return "SELL", base if disp >= STRUCTURE_DISPLACEMENT_MIN else base+"_WEAK", last_sh,last_sl
    return "NEUTRAL","NONE",last_sh,last_sl


def find_order_block(df,bias):
    d = _closed(df)
    neutral_zone = ((float(d["Low"].tail(10).min()),float(d["High"].tail(10).max())) if not d.empty else (0.0,0.0))
    if d.empty or bias not in ("BUY","SELL"):
        return "NEUTRAL_DEMAND",neutral_zone,False,False
    n=len(d)
    for i in range(max(10,n-100),n-4)[::-1]:
        op,cl,hi,lo = [_safe_float(d[c].iloc[i]) for c in ("Open","Close","High","Low")]
        disp=measure_displacement(d,i)
        if bias=="BUY" and cl<op and disp>=ORDER_BLOCK_DISPLACEMENT_MIN:
            after=d.iloc[i+4:]
            return "BULLISH_OB",(lo,hi),not after.empty and bool(after["Low"].min()<=hi),not after.empty and bool(after["Close"].min()<lo)
        if bias=="SELL" and cl>op and disp>=ORDER_BLOCK_DISPLACEMENT_MIN:
            after=d.iloc[i+4:]
            return "BEARISH_OB",(lo,hi),not after.empty and bool(after["High"].max()>=lo),not after.empty and bool(after["Close"].max()>hi)
    return "NEUTRAL_DEMAND",neutral_zone,False,False


def detect_breaker_block(df,bias):
    ob,zone,_,invalidated=find_order_block(df,bias)
    if invalidated and bias=="BUY": return "BULLISH_BREAKER",zone
    if invalidated and bias=="SELL": return "BEARISH_BREAKER",zone
    return "NONE",None


def detect_fvg(df,lookback=FVG_LOOKBACK):
    d=_closed(df)
    if len(d)<5: return None
    start=max(2,len(d)-lookback); gaps=[]
    for i in range(start,len(d)-1):
        ph,pl=_safe_float(d["High"].iloc[i-1]),_safe_float(d["Low"].iloc[i-1])
        nh,nl=_safe_float(d["High"].iloc[i+1]),_safe_float(d["Low"].iloc[i+1])
        if nl>ph: typ,zone="BULLISH_FVG",(ph,nl)
        elif nh<pl: typ,zone="BEARISH_FVG",(nh,pl)
        else: continue
        future=d.iloc[i+2:]
        filled=False if future.empty else bool(((future["Low"]<=zone[1])&(future["High"]>=zone[0])).any())
        gaps.append({"index":i,"type":typ,"zone":zone,"filled":filled})
    unfilled=[g for g in gaps if not g["filled"]]
    return unfilled[-1] if unfilled else None


def find_equal_levels(df,lookback=EQUAL_LEVEL_LOOKBACK,tolerance=EQUAL_LEVEL_TOLERANCE):
    if df is None or df.empty: return [],[]
    r=df.tail(lookback)
    def cluster(values):
        vals=np.sort(np.asarray(values,dtype=float)); vals=vals[np.isfinite(vals)]; groups=[]
        if len(vals)==0: return groups
        cur=[vals[0]]
        for v in vals[1:]:
            if abs(v-cur[-1])/max(abs(cur[-1]),1e-9)<=tolerance: cur.append(v)
            else:
                if len(cur)>=2: groups.append(float(np.mean(cur)))
                cur=[v]
        if len(cur)>=2: groups.append(float(np.mean(cur)))
        return groups
    return cluster(r["High"].values),cluster(r["Low"].values)


def analyze_liquidity_sweep(df):
    d=_closed(df)
    if len(d)<20: return False,"NO_SWEEP"
    rl=_safe_float(d["Low"].iloc[-15:-2].min()); rh=_safe_float(d["High"].iloc[-15:-2].max())
    lo,hi,cl=[_safe_float(d[c].iloc[-1]) for c in ("Low","High","Close")]
    if lo<rl and cl>rl: return True,f"SELL-SIDE SWEEP BELOW {rl:.2f}"
    if hi>rh and cl<rh: return True,f"BUY-SIDE SWEEP ABOVE {rh:.2f}"
    eqh,eql=find_equal_levels(d); tol=cl*EQUAL_LEVEL_TOLERANCE
    for x in eqh:
        if hi>x+tol*.2 and cl<x: return True,f"EQUAL-HIGHS LIQUIDITY POOL SWEPT AT {x:.2f}"
    for x in eql:
        if lo<x-tol*.2 and cl>x: return True,f"EQUAL-LOWS LIQUIDITY POOL SWEPT AT {x:.2f}"
    return False,"NO_SWEEP"


def calculate_premium_discount(df,lookback=50):
    d=_closed(df)
    if d.empty: return {"zone":"UNKNOWN","equilibrium":0.0,"swing_high":0.0,"swing_low":0.0}
    d=d.tail(lookback); hi=_safe_float(d["High"].max()); lo=_safe_float(d["Low"].min()); eq=(hi+lo)/2; cl=_safe_float(d["Close"].iloc[-1])
    return {"zone":"PREMIUM" if cl>eq else "DISCOUNT" if cl<eq else "EQUILIBRIUM","equilibrium":eq,"swing_high":hi,"swing_low":lo}


def get_session_info():
    now=datetime.datetime.now(datetime.timezone.utc)
    if not _TZ_OK: return "UNKNOWN",50.0
    try:
        lh=now.astimezone(ZoneInfo("Europe/London")).hour; nh=now.astimezone(ZoneInfo("America/New_York")).hour
        th=now.astimezone(ZoneInfo("Asia/Tokyo")).hour; sh=now.astimezone(ZoneInfo("Australia/Sydney")).hour
        if 8<=lh<=16 and 8<=nh<=17: return "LONDON / NEW YORK OVERLAP",95.0
        if 8<=lh<=16: return "LONDON SESSION",80.0
        if 8<=nh<=17: return "NEW YORK SESSION",80.0
        if 9<=th<=18: return "TOKYO SESSION",55.0
        if 8<=sh<=17: return "SYDNEY SESSION",45.0
        return "OFF-SESSION / LOW LIQUIDITY",20.0
    except Exception:
        return "UNKNOWN",50.0


def evaluate_trend_strength(d,tf_biases,regime_info,struct_bias):
    if d is None or d.empty: return False,"No closed data"
    c=d["Close"]; e20=c.ewm(span=20,adjust=False).mean().iloc[-1]; e50=c.ewm(span=50,adjust=False).mean().iloc[-1]
    e200=c.ewm(span=200,adjust=False).mean().iloc[-1] if len(c)>=200 else None; last=_safe_float(c.iloc[-1])
    bull=last>e20>e50 and (e200 is None or e50>e200); bear=last<e20<e50 and (e200 is None or e50<e200)
    adx_ok=regime_info.get("adx",0)>=20; bc=sum(v=="BUY" for v in tf_biases.values()); sc=sum(v=="SELL" for v in tf_biases.values())
    available=max(len(tf_biases),1); required=max(2,min(3,available))
    if bull and adx_ok and bc>=required and struct_bias=="BUY": return True,f"EMA stack + ADX + {required}/{available} TF aligned bullish"
    if bear and adx_ok and sc>=required and struct_bias=="SELL": return True,f"EMA stack + ADX + {required}/{available} TF aligned bearish"
    return False,"Trend strength criteria not met"


def calculate_position_size(account_balance_usd,risk_pct,entry_price,stop_loss_price,contract_size=100.0):
    bal,risk,entry,stop,contract=[_safe_float(x) for x in (account_balance_usd,risk_pct,entry_price,stop_loss_price,contract_size)]
    if min(bal,risk,entry,stop,contract)<=0: return None
    dist=abs(entry-stop)
    if dist<=0: return None
    risk_amount=bal*risk/100
    return {"risk_amount_usd":round(risk_amount,2),"stop_distance":round(dist,4),"lots":round(risk_amount/(dist*contract),4)}


def calculate_position_size_for_symbol(symbol,account_balance_usd,risk_pct,entry_price,stop_loss_price):
    contract=CONTRACT_SIZE_BY_SYMBOL.get(symbol,1.0)
    result=calculate_position_size(account_balance_usd,risk_pct,entry_price,stop_loss_price,contract)
    if result is not None: result["contract_size"]=contract
    return result


def score_signal(tf_biases,struct_type,ob_type,mitigated,invalidated,sweep,fvg_present,rr,pd_zone,bias,trend_strong):
    bull=sum(v=="BUY" for v in tf_biases.values()); bear=sum(v=="SELL" for v in tf_biases.values())
    score=max(bull,bear)/max(len(tf_biases),1)*25; weak=struct_type.endswith("_WEAK"); base=struct_type[:-5] if weak else struct_type
    struct=12 if "CHoCH" in base and weak else 20 if "CHoCH" in base else 8 if "BOS" in base and weak else 15 if "BOS" in base else 0
    ob=-10 if invalidated and ob_type in ("BULLISH_OB","BEARISH_OB") else 7 if mitigated and ob_type in ("BULLISH_OB","BEARISH_OB") else 15 if ob_type in ("BULLISH_OB","BEARISH_OB") else 0
    rr_score=min(12,max(0,(rr-1)*6))
    pd_score=10 if (bias=="BUY" and pd_zone=="DISCOUNT") or (bias=="SELL" and pd_zone=="PREMIUM") else -5 if (bias=="BUY" and pd_zone=="PREMIUM") or (bias=="SELL" and pd_zone=="DISCOUNT") else 0
    total=score+struct+ob+(10 if sweep else 0)+(8 if fvg_present else 0)+rr_score+pd_score+(10 if trend_strong else 0)
    return round(float(np.clip(total,0,100)),1)


def score_bull_bear(tf_biases,struct_type,ob_type,mitigated,invalidated,sweep,sweep_msg,fvg,pd_zone,trend_strong,macd_trend,rsi_val):
    bull=bear=0.0; bc=sum(v=="BUY" for v in tf_biases.values()); sc=sum(v=="SELL" for v in tf_biases.values()); n=max(len(tf_biases),1)
    bull+=bc/n*25; bear+=sc/n*25; weak=struct_type.endswith("_WEAK"); base=struct_type[:-5] if weak else struct_type
    pts=10 if "CHoCH" in base and weak else 20 if "CHoCH" in base else 6 if "BOS" in base and weak else 15 if "BOS" in base else 0
    if "BULLISH" in base: bull+=pts
    elif "BEARISH" in base: bear+=pts
    if ob_type=="BULLISH_OB" and not invalidated: bull+=7 if mitigated else 15
    elif ob_type=="BEARISH_OB" and not invalidated: bear+=7 if mitigated else 15
    if sweep:
        if "SELL-SIDE" in sweep_msg or "EQUAL-LOWS" in sweep_msg: bull+=12
        elif "BUY-SIDE" in sweep_msg or "EQUAL-HIGHS" in sweep_msg: bear+=12
    if fvg:
        if fvg["type"]=="BULLISH_FVG": bull+=8
        elif fvg["type"]=="BEARISH_FVG": bear+=8
    if pd_zone=="DISCOUNT": bull+=8
    elif pd_zone=="PREMIUM": bear+=8
    if macd_trend=="BULLISH": bull+=7
    elif macd_trend=="BEARISH": bear+=7
    if rsi_val>=55: bull+=5
    elif rsi_val<=45: bear+=5
    if trend_strong:
        if bull>bear: bull+=10
        elif bear>bull: bear+=10
    return round(min(100,bull),1),round(min(100,bear),1)


def grade(score):
    return "A+" if score>=85 else "A" if score>=75 else "B" if score>=65 else "C" if score>=50 else "D"


def generate_omega_signal(symbol,ticker=None,min_tf=DEFAULT_MIN_TF_AGREEMENT,min_score=DEFAULT_MIN_SCORE,min_rr=DEFAULT_MIN_RR):
    """
    Main entry point. ticker is retained for compatibility with streamlit_app.py,
    but the dashboard symbol is authoritative for Twelve Data.
    """
    data,integrity=fetch_mtf_data(symbol)
    available={tf:df for tf,df in data.items() if df is not None and not df.empty}
    unavailable=[tf for tf,df in data.items() if df is None or df.empty]

    # Signal integrity: ALL configured timeframes must be available.
    if unavailable:
        return {
            "ok":False,
            "symbol":symbol,
            "ticker":ticker or TD_SYMBOLS.get(symbol, symbol),
            "reason":"Required timeframe data unavailable: " + ", ".join(unavailable) + " — signal blocked.",
            "data":data,
            "data_integrity":integrity,
            "available_timeframes":list(available),
            "unavailable_timeframes":unavailable,
            "tf_biases":{},
            "tf_structures":{},
        }

    biases={}; structures={}
    for tf in ("1D","4H","1H","15M"):
        b,s,_,_=analyze_market_structure(data[tf])
        biases[tf]=b; structures[tf]=s

    primary=data["15M"]
    struct_bias,struct_type,sw_high,sw_low=analyze_market_structure(primary)
    ob_type,ob_zone,ob_mitigated,ob_invalidated=find_order_block(primary,struct_bias)
    fvg=detect_fvg(primary); sweep,sweep_detail=analyze_liquidity_sweep(primary)
    pd_info=calculate_premium_discount(primary); regime=compute_market_regime(primary); closed=_closed(primary)
    trend_strong,trend_detail=evaluate_trend_strength(closed,biases,regime,struct_bias)
    eq_highs,eq_lows=find_equal_levels(closed); rsi=compute_rsi(closed)
    macd_trend,macd_line,macd_signal=compute_macd_trend(closed); vwap_status,vwap_value=compute_vwap_status(closed)
    vol_status=vol_status_label(regime["vol_ratio"]); ema_cross=compute_ema_cross(closed)

    if closed.empty:
        return {"ok":False,"symbol":symbol,"ticker":ticker or TD_SYMBOLS.get(symbol,symbol),
                "reason":"No closed 15M candle available.","data":data,"data_integrity":integrity}

    bull_score,bear_score=score_bull_bear(
        biases,struct_type,ob_type,ob_mitigated,ob_invalidated,
        sweep,sweep_detail,fvg,pd_info["zone"],trend_strong,macd_trend,rsi
    )

    entry=_safe_float(closed["Close"].iloc[-1]); atr=compute_atr(closed)
    if atr<=0:
        return {"ok":False,"symbol":symbol,"ticker":ticker or TD_SYMBOLS.get(symbol,symbol),
                "reason":"ATR could not be calculated.","data":data,"data_integrity":integrity}

    buffer=atr*.15
    if struct_bias=="BUY":
        ref=ob_zone[0] if ob_type=="BULLISH_OB" and not ob_invalidated else sw_low
        if ref is None: ref=entry-atr*1.5
        stop=min(ref-buffer,entry-atr); tp1=entry+1.5*atr; tp2=entry+3*atr; tp3=entry+5*atr
    elif struct_bias=="SELL":
        ref=ob_zone[1] if ob_type=="BEARISH_OB" and not ob_invalidated else sw_high
        if ref is None: ref=entry+atr*1.5
        stop=max(ref+buffer,entry+atr); tp1=entry-1.5*atr; tp2=entry-3*atr; tp3=entry-5*atr
    else:
        stop=tp1=tp2=tp3=entry

    rr=abs(tp2-entry)/abs(entry-stop) if struct_bias in ("BUY","SELL") and abs(entry-stop)>0 else 0.0
    score=score_signal(
        biases,struct_type,ob_type,ob_mitigated,ob_invalidated,
        sweep,fvg is not None,rr,pd_info["zone"],struct_bias,trend_strong
    )

    bc=sum(v=="BUY" for v in biases.values())
    sc=sum(v=="SELL" for v in biases.values())
    effective_min_tf= min(max(int(min_tf),1),4)
    reason=None

    if bc>=effective_min_tf and score>=min_score and struct_bias=="BUY":
        bias="BUY"
    elif sc>=effective_min_tf and score>=min_score and struct_bias=="SELL":
        bias="SELL"
    else:
        bias="NEUTRAL"
        reason=f"Timeframe agreement or score below threshold ({max(bc,sc)}/4 usable TF, {score}/{min_score} score)"

    if bias!="NEUTRAL" and rr<min_rr:
        bias="NEUTRAL"; reason=f"R:R {rr:.2f} below minimum {min_rr:.2f} — signal downgraded to NEUTRAL"
    if bias!="NEUTRAL" and ob_invalidated:
        bias="NEUTRAL"; reason="Directional order block is invalidated."

    session,session_quality=get_session_info()

    return {
        "ok":True,"symbol":symbol,"ticker":ticker or TD_SYMBOLS.get(symbol,symbol),
        "data":data,"data_integrity":integrity,
        "available_timeframes":list(available),"unavailable_timeframes":unavailable,
        "bias":bias,"score":score,"grade":grade(score),"entry":entry,"stop":stop,
        "tp1":tp1,"tp2":tp2,"tp3":tp3,"rr":round(rr,3),"atr":round(atr,4),
        "tf_biases":biases,"tf_structures":structures,"structure":struct_type,
        "ob_type":ob_type,"ob_zone":ob_zone,"ob_mitigated":ob_mitigated,
        "ob_invalidated":ob_invalidated,"fvg":fvg,"sweep":sweep,"sweep_detail":sweep_detail,
        "pd_zone":pd_info["zone"],"pd_info":pd_info,"session":session,"session_quality":session_quality,
        "regime":regime,"trend_strong":trend_strong,"trend_detail":trend_detail,
        "eq_highs":eq_highs,"eq_lows":eq_lows,"rsi":round(rsi,2),"macd_trend":macd_trend,
        "macd_line":macd_line,"macd_signal":macd_signal,"vwap_status":vwap_status,
        "vwap_val":vwap_value,"vol_status":vol_status,"ema_cross":ema_cross,
        "bull_score":bull_score,"bear_score":bear_score,"bull_tf_count":bc,
        "bear_tf_count":sc,"reason":reason,
    }


def get_live_price_for_symbol(symbol):
    return get_live_price(symbol)
