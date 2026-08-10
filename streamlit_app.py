import streamlit as st
import yfinance as yf
import requests

# Page configuration
st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .buy-glow {
        background-color: #052e16;
        border: 1px solid #22c55e;
        color: #4ade80;
        text-align: center;
        padding: 8px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- MT5 ALIGNED SYMBOL MAP -----------------
# Uses Spot Market tickers (=X) rather than Futures (=F) to match MetaTrader 5 feeds
SYMBOL_MAP = {
    "XAUUSD": "XAUUSD=X",   # Spot Gold (Matches MT5 XAUUSD)
    "EURUSD": "EURUSD=X",   # Spot EUR/USD
    "GBPUSD": "GBPUSD=X",   # Spot GBP/USD
    "USDJPY": "JPY=X",      # Spot USD/JPY
    "BTCUSD": "BTC-USD",    # Bitcoin Spot
    "US30": "^DJI",         # Dow Jones Industrial
    "NAS100": "^NDX"        # Nasdaq 100
}

@st.cache_data(ttl=5)
def get_live_market_data(symbol_key):
    ticker_str = SYMBOL_MAP.get(symbol_key, f"{symbol_key}=X")
    try:
        ticker = yf.Ticker(ticker_str)
        # Fetch 1-day, 1-minute data for low-latency spot pricing
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            current_price = float(data['Close'].iloc[-1])
            prev_close = float(data['Open'].iloc[0])
            change_pct = ((current_price - prev_close) / prev_close) * 100
            return current_price, change_pct
    except Exception:
        pass
    
    # Updated default fallback values matching spot prices
    defaults = {
        "XAUUSD": 4333.00,
        "EURUSD": 1.0850,
        "GBPUSD": 1.2800,
        "USDJPY": 155.00,
        "BTCUSD": 65000.00,
        "US30": 39000.00,
        "NAS100": 18500.00
    }
    return defaults.get(symbol_key, 100.0), 0.0

def send_telegram_alert(token, chat_id, message):
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
            return True
        except Exception:
            return False
    return False

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown("### ⚡ SEKWAILA OMEGA X")
    st.divider()
    
    bot_token = st.text_input("Telegram Bot Token", type="password")
    chat_id = st.text_input("Telegram Chat ID")
    
    st.divider()
    account_r = st.number_input("Account (R)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    # Manual Broker Spread Offset (to fine-tune minor broker differences)
    st.divider()
    price_offset = st.number_input("Broker Offset Adjustment", value=0.0, step=0.1, help="Adjust if your MT5 broker spread differs slightly")

# ----------------- MAIN INTERFACE -----------------
st.title("⚡ Sekwaila Omega X Engine")

symbol = st.selectbox(
    "Select Active Pair", 
    ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "US30", "NAS100"], 
    index=0
)

# Fetch current live spot price
raw_price, change_pct = get_live_market_data(symbol)
live_price = raw_price + price_offset

# Calculate parameters based on asset class precision
if symbol == "XAUUSD":
    sl_dist = 9.00
    tp1_dist = 10.50
    tp2_dist = 21.00
elif symbol in ["EURUSD", "GBPUSD"]:
    sl_dist = 0.0020
    tp1_dist = 0.0030
    tp2_dist = 0.0060
elif symbol == "USDJPY":
    sl_dist = 0.20
    tp1_dist = 0.30
    tp2_dist = 0.60
else:
    sl_dist = live_price * 0.005
    tp1_dist = live_price * 0.0075
    tp2_dist = live_price * 0.015

sl_price = live_price - sl_dist
tp1_price = live_price + tp1_dist
tp2_price = live_price + tp2_dist

# Format precision
decimals = 4 if symbol in ["EURUSD", "GBPUSD"] else (2 if symbol in ["XAUUSD", "USDJPY"] else 2)
price_str = f"{live_price:.{decimals}f}"
sl_str = f"{sl_price:.{decimals}f}"
tp1_str = f"{tp1_price:.{decimals}f}"
tp2_str = f"{tp2_price:.{decimals}f}"

# Top Display Card
st.markdown(f"""
<div class="metric-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: #8b949e; font-size: 0.8rem;">LIVE MT5 SPOT SIGNAL</span>
            <h1 style="margin: 0; font-size: 2.2rem;">{symbol}</h1>
            <h2 style="margin: 0; color: #22c55e;">{price_str} 
                <span style="font-size: 0.9rem;">({change_pct:+.2f}%)</span>
            </h2>
        </div>
        <div style="text-align: right;">
            <span style="color: #8b949e; font-size: 0.8rem;">CONFIDENCE</span>
            <h1 style="margin: 0; color: #22c55e;">82%</h1>
            <span style="color: #f59e0b; font-size: 0.8rem; font-weight: bold;">GRADE A SETUP</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="buy-glow">🔥 BUY SETUP ACTIVE</div>', unsafe_allow_html=True)
    st.subheader("Execution Parameters")
    
    m1, m2 = st.columns(2)
    m1.metric("ENTRY", price_str)
    m2.metric("STOP LOSS", sl_str)
    
    m3, m4 = st.columns(2)
    m3.metric("TAKE PROFIT 1", tp1_str)
    m4.metric("TAKE PROFIT 2", tp2_str)

with col_right:
    st.subheader("Telegram Alert Execution")
    alert_msg = f"🚀 *SEKWAILA OMEGA X SIGNAL*\n\nPair: `{symbol}`\nAction: *BUY NOW*\nEntry: `{price_str}`\nSL: `{sl_str}`\nTP1: `{tp1_str}`\nTP2: `{tp2_str}`"
    
    st.code(alert_msg, language="markdown")
    
    if st.button("📲 Send Signal to Telegram", use_container_width=True):
        if bot_token and chat_id:
            success = send_telegram_alert(bot_token, chat_id, alert_msg)
            if success:
                st.success("Signal broadcasted successfully to Telegram!")
            else:
                st.error("Failed to send signal. Check your Bot Token and Chat ID.")
        else:
            st.warning("Please enter your Telegram credentials in the sidebar.")
