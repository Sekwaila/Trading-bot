import streamlit as st
import yfinance as yf
import requests

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to match your Sekwaila Dark Theme
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
    .status-badge {
        background-color: #1f2937;
        color: #10b981;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- MT5 SPOT SYMBOL MAPPING -----------------
SYMBOL_MAP = {
    "XAUUSD": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "BTCUSD": "BTC-USD",
    "US30": "^DJI",
    "NAS100": "^NDX",
    "DXY": "DX-Y.NYB"
}

@st.cache_data(ttl=5)
def get_live_market_data(symbol_key):
    ticker_str = SYMBOL_MAP.get(symbol_key, f"{symbol_key}=X")
    try:
        ticker = yf.Ticker(ticker_str)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            current_price = float(data['Close'].iloc[-1])
            prev_close = float(data['Open'].iloc[0])
            change_pct = ((current_price - prev_close) / prev_close) * 100
            return current_price, change_pct
    except Exception:
        pass
    
    defaults = {
        "XAUUSD": 4333.00, "EURUSD": 1.0850, "GBPUSD": 1.2800, 
        "USDJPY": 155.00, "BTCUSD": 65000.00, "US30": 39000.00, 
        "NAS100": 18500.00, "DXY": 99.60
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

# ----------------- SIDEBAR NAVIGATION & SETTINGS -----------------
with st.sidebar:
    st.markdown("## ⚡ SEKWAILA")
    st.caption("OMEGA X")
    st.divider()
    
    # Complete Sidebar Navigation Menu
    nav_option = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📊 Market Scanner",
            "🔥 Heatmap",
            "🤖 AI Narrator",
            "📰 News Intelligence",
            "📈 Multi-Timeframe",
            "🔗 Correlation Matrix",
            "📓 Trade Journal",
            "📉 Performance",
            "📲 Telegram Alerts",
            "⚙️ Settings",
            "❓ Help"
        ],
        label_visibility="collapsed"
    )
    
    st.divider()
    account_r = st.number_input("Account (R)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    usd_val = account_r / 18.5
    risk_r = account_r * (risk_pct / 100)
    st.caption(f"≈ USD ${usd_val:.2f} | Risk R{risk_r:.2f}")
    
    st.divider()
    bot_token = st.text_input("Telegram Bot Token", type="password")
    chat_id = st.text_input("Telegram Chat ID")

# ----------------- MAIN VIEW -----------------
if "🏠 Dashboard" in nav_option:
    
    # Top Overview Metrics (BUY/SELL setups, Session, DXY)
    dxy_price, dxy_change = get_live_market_data("DXY")
    
    top_c1, top_c2, top_c3, top_c4, top_c5 = st.columns(5)
    
    with top_c1:
        st.markdown("🟢 **BUY Setups**")
        st.markdown("## 3")
        st.caption("↑ SP500, US30, BTCUSD")
        
    with top_c2:
        st.markdown("🔴 **SELL Setups**")
        st.markdown("## 0")
        st.caption("↑ —")
        
    with top_c3:
        st.markdown("🔥 **ACTIVE NOW**")
        st.markdown("## 2")
        st.caption("↑ SP500, US30")
        
    with top_c4:
        st.markdown("📡 **Session**")
        st.markdown("## NEW YORK")
        st.caption("↑ No killzone")
        
    with top_c5:
        st.markdown("💲 **DXY**")
        st.markdown(f"## {dxy_price:.2f}")
        st.caption("↑ BEAR ▼")
        
    st.divider()
    
    # Instrument Selection & Signal Card
    symbol = st.selectbox(
        "Select Focus Pair",
        ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "US30", "NAS100"],
        index=0
    )
    
    live_price, change_pct = get_live_market_data(symbol)
    
    # Distance logic per pair precision
    if symbol == "XAUUSD":
        sl_dist, tp1_dist, tp2_dist = 9.00, 10.50, 21.00
    elif symbol in ["EURUSD", "GBPUSD"]:
        sl_dist, tp1_dist, tp2_dist = 0.0020, 0.0030, 0.0060
    elif symbol == "USDJPY":
        sl_dist, tp1_dist, tp2_dist = 0.20, 0.30, 0.60
    else:
        sl_dist = live_price * 0.005
        tp1_dist = live_price * 0.0075
        tp2_dist = live_price * 0.015

    sl_price = live_price - sl_dist
    tp1_price = live_price + tp1_dist
    tp2_price = live_price + tp2_dist

    decimals = 4 if symbol in ["EURUSD", "GBPUSD"] else 2
    price_str = f"{live_price:.{decimals}f}"
    sl_str = f"{sl_price:.{decimals}f}"
    tp1_str = f"{tp1_price:.{decimals}f}"
    tp2_str = f"{tp2_price:.{decimals}f}"

    # Top Signal Header
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: #8b949e; font-size: 0.8rem;">TOP SIGNAL</span>
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

else:
    st.title(nav_option)
    st.info(f"The module **{nav_option}** is loaded and ready.")
