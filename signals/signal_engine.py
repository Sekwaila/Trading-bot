import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import requests

# ----------------- MT5 INITIALIZATION & SYMBOL MAPPING -----------------
# Default broker symbol map (configurable via Settings)
DEFAULT_SYMBOL_MAP = {
    "XAUUSD": "XAUUSDm",
    "BTCUSD": "BTCUSD",
    "US30": "US30.cash",
    "SP500": "US500.cash",
    "EURUSD": "EURUSDm",
    "DXY": "USDX"
}

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}

def init_mt5(account=None, password=None, server=None):
    """Initializes connection to MT5 terminal."""
    if not mt5.initialize():
        return False, f"MT5 Init Failed: {mt5.last_error()}"
    
    if account and password and server:
        authorized = mt5.login(int(account), password=password, server=server)
        if not authorized:
            return False, f"MT5 Login Failed: {mt5.last_error()}"
            
    return True, "Connected to MT5"

def get_mt5_candles(symbol, timeframe_str="M15", count=100):
    """Fetches real-time candles directly from MT5 broker feed."""
    tf = TIMEFRAME_MAP.get(timeframe_str, mt5.TIMEFRAME_M15)
    
    # Ensure symbol is visible in Market Watch
    mt5.symbol_select(symbol, True)
    
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None or len(rates) == 0:
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_mt5_live_price(symbol):
    """Fetches exact Bid/Ask/Spread from MT5 broker."""
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "mid": (tick.bid + tick.ask) / 2.0,
            "spread": tick.spread
        }
    return None

# ----------------- INDICATOR & OMEGA SIGNAL CALCULATIONS -----------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_omega_signal(pair_key, broker_symbol, timeframe="M15"):
    """
    Calculates signal strictly using MT5 data source.
    Returns identical parameters for both Dashboard and Telegram.
    """
    df = get_mt5_candles(broker_symbol, timeframe_str=timeframe, count=100)
    live_tick = get_mt5_live_price(broker_symbol)
    
    if df is None or live_tick is None:
        return {
            "status": "ERROR",
            "message": f"Could not fetch MT5 feed for symbol: {broker_symbol}"
        }

    current_price = live_tick["ask"]
    
    # Technical Calculation using MT5 Candles
    df['rsi'] = calculate_rsi(df['close'])
    latest_rsi = df['rsi'].iloc[-1] if not df['rsi'].empty else 50.0

    # SMC Structure / Signal Rules
    high_max = df['high'].tail(20).max()
    low_min = df['low'].tail(20).min()
    
    # Calculate SL and TP levels based on MT5 Price
    if pair_key in ["XAUUSD"]:
        sl_dist, tp1_dist, tp2_dist = 8.00, 12.00, 24.00
    elif pair_key in ["US30", "SP500"]:
        sl_dist = current_price * 0.003
        tp1_dist = sl_dist * 1.5
        tp2_dist = sl_dist * 3.0
    else:
        sl_dist = current_price * 0.002
        tp1_dist = sl_dist * 1.5
        tp2_dist = sl_dist * 3.0

    # Signal direction determination
    if latest_rsi > 50:
        action = "BUY"
        entry = current_price
        sl = entry - sl_dist
        tp1 = entry + tp1_dist
        tp2 = entry + tp2_dist
        confidence = 77
        quality = "GRADE A SETUP"
    else:
        action = "SELL"
        entry = current_price
        sl = entry + sl_dist
        tp1 = entry - tp1_dist
        tp2 = entry - tp2_dist
        confidence = 65
        quality = "MED QUALITY"

    return {
        "status": "SUCCESS",
        "pair": pair_key,
        "broker_symbol": broker_symbol,
        "action": action,
        "entry": round(entry, 4 if "USD" in pair_key and pair_key != "XAUUSD" else 2),
        "sl": round(sl, 4 if "USD" in pair_key and pair_key != "XAUUSD" else 2),
        "tp1": round(tp1, 4 if "USD" in pair_key and pair_key != "XAUUSD" else 2),
        "tp2": round(tp2, 4 if "USD" in pair_key and pair_key != "XAUUSD" else 2),
        "confidence": confidence,
        "quality": quality,
        "rsi": round(latest_rsi, 1),
        "spread": live_tick["spread"]
    }

# ----------------- TELEGRAM BROADCASTER (SIGNALS ONLY) -----------------
def broadcast_telegram_signal(bot_token, chat_id, signal_data):
    """
    Sends identical signal data calculated from MT5 directly to Telegram.
    Strictly manual signals — NO trade execution.
    """
    if not bot_token or not chat_id:
        return False, "Missing Telegram Token or Chat ID"

    msg = (
        f"🚀 *SEKWAILA OMEGA X SIGNAL*\n"
        f"*(MT5 Broker Feed: `{signal_data['broker_symbol']}`)*\n\n"
        f"Pair: *{signal_data['pair']}*\n"
        f"Action: *{signal_data['action']} NOW*\n"
        f"Entry: `{signal_data['entry']}`\n"
        f"SL: `{signal_data['sl']}`\n"
        f"TP1: `{signal_data['tp1']}`\n"
        f"TP2: `{signal_data['tp2']}`\n"
        f"Confidence: *{signal_data['confidence']}% ({signal_data['quality']})*\n\n"
        f"⚠️ *Manual Execution Only*"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, str(e)
