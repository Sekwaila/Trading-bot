import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & SIDEBAR DEFAULT STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. SIDEBAR: SETTINGS, THEMES, TELEGRAM & INDICATORS
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ SEKWAILA OMEGA X")
st.sidebar.caption("System Control Panel")

# --- THEME SELECTOR ---
st.sidebar.subheader("🎨 UI Theme")
theme_choice = st.sidebar.selectbox("Color Theme", ["TradingView Dark", "OLED Pure Black", "Gold Accent"], index=0)

bg_color = "#131722" if theme_choice == "TradingView Dark" else ("#000000" if theme_choice == "OLED Pure Black" else "#0b0d12")
card_color = "#1e222d" if theme_choice != "Gold Accent" else "#141722"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: #d1d4dc; }}
    [data-testid="stSidebar"] {{ background-color: {card_color}; }}
    header {{ visibility: hidden; }}
    .block-container {{ padding: 0.5rem !important; }}
    .indicator-box {{
        background-color: {card_color};
        border: 1px solid #2a2e39;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    .ind-row {{
        display: flex;
        justify-content: space-between;
        padding: 3px 0;
        font-size: 13px;
        border-bottom: 1px solid #2a2e39;
    }}
    .text-green {{ color: #089981; font-weight: bold; }}
    .text-red {{ color: #f23645; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# --- TELEGRAM ALERTS SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Telegram Signals")
enable_tg = st.sidebar.toggle("Enable Telegram Alerts", value=False)
tg_bot_token = st.sidebar.text_input("Bot Token", type="password", placeholder="123456:ABC-DEF...")
tg_chat_id = st.sidebar.text_input("Chat ID", placeholder="-10012345678")

def send_telegram_alert(msg):
    if enable_tg and tg_bot_token and tg_chat_id:
        url = f"https://api.telegram.org/bot{tg_bot_token}/sendMessage"
        payload = {"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=3)
        except Exception as e:
            st.sidebar.error(f"Telegram Failed: {e}")

if st.sidebar.button("Test Telegram Connection"):
    send_telegram_alert("⚡ *SEKWAILA OMEGA X*: Connection Test Successful!")
    st.sidebar.success("Test message sent!")

# --- INDICATOR TOGGLES ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Chart Indicators")
show_rsi = st.sidebar.checkbox("Show RSI Table Row", value=True)
show_macd = st.sidebar.checkbox("Show MACD Trend", value=True)
show_targets = st.sidebar.checkbox("Show TP / SL Lines", value=True)

# -----------------------------------------------------------------------------
# 3. NATIVE TECHNICAL INDICATOR CALCULATIONS
# -----------------------------------------------------------------------------
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD CONTROLS
# -----------------------------------------------------------------------------
TICKER_MAP = {
    "XAUUSD": "GC=F",
    "BTCUSD": "BTC-USD",
    "US30": "^DJI",
    "EURUSD": "EURUSD=X"
}

TF_MAP = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "1h", "1D": "1d"}

col_sym, col_tf, col_title = st.columns([2, 3, 2])
with col_sym:
    symbol = st.selectbox("Symbol", list(TICKER_MAP.keys()), index=0, label_visibility="collapsed")
with col_tf:
    timeframe = st.radio("Timeframe", list(TF_MAP.keys()), index=2, horizontal=True, label_visibility="collapsed")
with col_title:
    st.markdown("<p style='text-align:right; color:#d9a441; font-weight:bold;'>⚡ SEKWAILA OMEGA X</p>", unsafe_allow_html=True)

@st.cache_data(ttl=15)
def get_live_data(sym, tf):
    ticker = TICKER_MAP[sym]
    interval = TF_MAP[tf]
    period = "5d" if interval in ["1m", "5m", "15m", "1h"] else "100d"
    
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.dropna(inplace=True)
    
    df['RSI'] = calc_rsi(df['Close'], 14)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['ATR'] = calc_atr(df, 14)
    
    return df

df = get_live_data(symbol, timeframe)

if df.empty or len(df) < 20:
    st.error("Market feed offline or timeframe unavailable.")
    st.stop()

last_bar = df.iloc[-1]
last_price = float(last_bar['Close'])
rsi_val = float(last_bar['RSI'])
atr_val = float(last_bar['ATR']) if not np.isnan(last_bar['ATR']) else (last_price * 0.005)
macd_trend = "BULL" if last_bar['MACD'] > last_bar['Signal'] else "BEAR"

# -----------------------------------------------------------------------------
# 5. CUSTOM METRICS MATRIX
# -----------------------------------------------------------------------------
matrix_html = f"""
<div class='indicator-box'>
    <div class='ind-row'><span>Asset / Timeframe</span><b>{symbol} ({timeframe})</b></div>
    <div class='ind-row'><span>Live Market Price</span><b>{last_price:,.2f}</b></div>
"""

if show_rsi:
    matrix_html += f"<div class='ind-row'><span>RSI (14)</span><b class='{'text-green' if rsi_val > 50 else 'text-red'}'>{rsi_val:.1f}</b></div>"
if show_macd:
    matrix_html += f"<div class='ind-row'><span>MACD Trend</span><b class='{'text-green' if macd_trend == 'BULL' else 'text-red'}'>{macd_trend}</b></div>"

matrix_html += f"<div class='ind-row'><span>ATR (14 Volatility)</span><b>{atr_val:.2f}</b></div></div>"

st.markdown(matrix_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. CHART WITH DIRECT TARGETS
# -----------------------------------------------------------------------------
fig = go.Figure()

plot_df = df.tail(60)

fig.add_trace(go.Candlestick(
    x=plot_df.index,
    open=plot_df['Open'],
    high=plot_df['High'],
    low=plot_df['Low'],
    close=plot_df['Close'],
    increasing_line_color='#089981',
    decreasing_line_color='#f23645',
    name=symbol
))

if show_targets:
    entry = last_price
    tp1 = entry + (1 * atr_val)
    tp2 = entry + (2 * atr_val)
    sl = entry - (1.5 * atr_val)

    targets = [
        (f"TP2: {tp2:,.2f}", tp2, "#089981"),
        (f"TP1: {tp1:,.2f}", tp1, "#089981"),
        (f"ENTRY: {entry:,.2f}", entry, "#2962ff"),
        (f"SL: {sl:,.2f}", sl, "#f23645")
    ]

    for label, val, color in targets:
        fig.add_hline(
            y=val, 
            line_dash="solid", 
            line_color=color, 
            line_width=2,
            annotation_text=f"<b>{label}</b>",
            annotation_position="top right",
            annotation_font_color="white",
            annotation_bgcolor=color
        )

fig.update_layout(
    height=550,
    margin=dict(l=0, r=50, t=10, b=10),
    paper_bgcolor=bg_color,
    plot_bgcolor=bg_color,
    xaxis=dict(gridcolor='#2a2e39', rangeslider=dict(visible=False)),
    yaxis=dict(gridcolor='#2a2e39', side='right')
)

st.plotly_chart(fig, width="stretch")
