import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Signal Hunter AI PRO", layout="wide", page_icon="🔥")

st.markdown("""
<style>
.green { color: #00ff88; font-weight: bold; }
.red { color: #ff4d4d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("SIGNAL HUNTER AI PRO - ADVANCED EDITION")
st.caption(f"SMC | BOS | CHoCH | Volume | AI | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

ACCOUNT_BALANCE = 1000

with st.sidebar:
    st.header("CONTROL PANEL")
    risk_percent = st.slider("Risk % Per Trade", 0.5, 5.0, 1.5, 0.1)
    selected_pairs = st.multiselect("Select Markets", ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"], default=["XAUUSD", "EURUSD"])
    st.metric("Account Balance", f"R{ACCOUNT_BALANCE:,.2f}")
    st.success("AI ACTIVE")

@st.cache_data(ttl=60)
def get_data(symbol, lookback=300):
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=lookback, freq="1h")
    
    config = {
        "XAUUSD": {"base": 4570, "vol": 14},
        "EURUSD": {"base": 1.1640, "vol": 0.008},
        "GBPUSD": {"base": 1.2530, "vol": 0.010},
        "USDJPY": {"base": 158.5, "vol": 0.22},
        "BTCUSD": {"base": 77000, "vol": 1200}
    }
    cfg = config.get(symbol, {"base": 100, "vol": 1})
    
    prices = [cfg["base"]]
    for i in range(1, lookback):
        drift = np.sin(i / 35) * cfg["vol"] * 0.2
        noise = np.random.normal(0, cfg["vol"] * 0.4)
        prices.append(prices[-1] + drift + noise)
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(np.random.randn() * cfg["vol"] * 0.2) for p in prices],
        'low': [p - abs(np.random.randn() * cfg["vol"] * 0.2) for p in prices],
        'close': [p + np.random.randn() * cfg["vol"] * 0.1 for p in prices],
        'volume': np.random.randint(10000, 30000, lookback)
    })

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    avg_loss = avg_loss.replace(0, np.nan)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def detect_structure(df):
    recent_high = df["high"].rolling(10).max()
    recent_low = df["low"].rolling(10).min()
    current_close = df["close"].iloc[-1]
    
    if current_close > recent_high.iloc[-2]:
        return "BULLISH BOS", 88
    elif current_close < recent_low.iloc[-2]:
        return "BEARISH BOS", 88
    return "RANGING", 45

def volume_signal(df):
    avg_vol = df["volume"].tail(20).mean()
    ratio = df["volume"].iloc[-1] / avg_vol
    if ratio > 1.5:
        return "HIGH VOLUME", 90
    elif ratio > 1:
        return "NORMAL VOLUME", 60
    return "LOW VOLUME", 35

tab1, tab2, tab3 = st.tabs(["MARKET ANALYSIS", "SOCCER", "PORTFOLIO"])

with tab1:
    for symbol in selected_pairs:
        st.divider()
        st.subheader(symbol)
        
        df = get_data(symbol)
        current_price = df["close"].iloc[-1]
        prev_price = df["close"].iloc[-2]
        change = ((current_price - prev_price) / prev_price) * 100
        
        rsi = calculate_rsi(df["close"]).iloc[-1]
        atr = calculate_atr(df).iloc[-1]
        structure, struct_score = detect_structure(df)
        volume, vol_score = volume_signal(df)
        
        confidence = int(struct_score * 0.5 + vol_score * 0.3)
        if 45 < rsi < 70:
            confidence += 20
        confidence = min(confidence, 99)
        
        if "BULLISH" in structure:
            signal = "BUY"
            stop = current_price - atr * 1.2
            tp1 = current_price + atr * 1.5
            tp2 = current_price + atr * 3
        elif "BEARISH" in structure:
            signal = "SELL"
            stop = current_price + atr * 1.2
            tp1 = current_price - atr * 1.5
            tp2 = current_price - atr * 3
        else:
            signal = "WAIT"
            stop = current_price
            tp1 = current_price
            tp2 = current_price
        
        lot = max(0.01, round(ACCOUNT_BALANCE * (risk_percent/100) / (atr * 10), 2))
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Price", f"${current_price:.2f}", delta=f"{change:.2f}%")
        with col2:
            st.metric("RSI", f"{rsi:.1f}")
        with col3:
            st.metric("ATR", f"{atr:.2f}")
        with col4:
            st.metric("Volume", volume[:3])
        with col5:
            st.metric("AI Conf", f"{confidence}%")
        
        if signal == "BUY":
            st.success(f"SIGNAL: {signal} - {structure}")
        elif signal == "SELL":
            st.error(f"SIGNAL: {signal} - {structure}")
        else:
            st.info(f"SIGNAL: {signal}")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Stop Loss", f"${stop:.2f}")
        with col_b:
            st.metric("TP 1", f"${tp1:.2f}")
        with col_c:
            st.metric("TP 2", f"${tp2:.2f}")
        with col_d:
            st.metric("Lot Size", f"{lot:.2f}")
        
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'].tail(100),
            open=df['open'].tail(100),
            high=df['high'].tail(100),
            low=df['low'].tail(100),
            close=df['close'].tail(100)
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark")
        fig.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("SOCCER PREDICTIONS")
    
    soccer = [
        {"match": "Man City vs Arsenal", "pred": "HOME", "conf": 85, "odds": 1.35},
        {"match": "Liverpool vs Wolves", "pred": "HOME", "conf": 82, "odds": 1.40},
        {"match": "Real Madrid vs Getafe", "pred": "HOME", "conf": 88, "odds": 1.32},
        {"match": "Bayern vs Koln", "pred": "HOME", "conf": 84, "odds": 1.38},
        {"match": "Arsenal vs Tottenham", "pred": "OVER 1.5", "conf": 92, "odds": 1.22},
        {"match": "Chelsea vs Man United", "pred": "OVER 1.5", "conf": 88, "odds": 1.25},
    ]
    
    for s in soccer:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(s["match"])
        with col2:
            st.write(f"Pred: {s['pred']}")
        with col3:
            st.write(f"{s['conf']}%")
        with col4:
            stake = round(ACCOUNT_BALANCE * 0.02 * (s['conf']/100), 2)
            st.write(f"R{stake}")
        st.divider()

with tab3:
    st.header("PORTFOLIO")
    
    portfolio = []
    for symbol in selected_pairs:
        df = get_data(symbol)
        structure, _ = detect_structure(df)
        price = df["close"].iloc[-1]
        portfolio.append({"Asset": symbol, "Signal": "BUY" if "BULLISH" in structure else "SELL" if "BEARISH" in structure else "WAIT", "Price": f"${price:.2f}"})
    
    st.dataframe(pd.DataFrame(portfolio), use_container_width=True)

st.divider()
st.success("SIGNAL HUNTER AI PRO - RUNNING")
