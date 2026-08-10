import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime

# ==========================================
# 1. STREAMLIT PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Sekwaila Omega X - Pro Trading Suite",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark TradingView Custom CSS Injection
st.markdown("""
<style>
    .main { background-color: #131722; color: #d1d4dc; }
    .stApp { background-color: #131722; }
    div[data-testid="stSidebar"] { background-color: #1e222d; border-right: 1px solid #2a2e39; }
    .stButton>button {
        background-color: #2962ff; color: white; border-radius: 4px; border: none; font-weight: 600;
    }
    .stButton>button:hover { background-color: #1e53e5; color: white; }
    .metric-card {
        background-color: #1e222d; padding: 15px; border-radius: 6px; border: 1px solid #2a2e39; margin-bottom: 10px;
    }
    .strong-buy { color: #089981; font-weight: bold; border-left: 4px solid #089981; padding-left: 8px; }
    .weak-buy { color: #26a69a; font-weight: bold; border-left: 4px solid #26a69a; padding-left: 8px; }
    .strong-sell { color: #f23645; font-weight: bold; border-left: 4px solid #f23645; padding-left: 8px; }
    .weak-sell { color: #ef5350; font-weight: bold; border-left: 4px solid #ef5350; padding-left: 8px; }
    .neutral { color: #787b86; font-weight: bold; border-left: 4px solid #787b86; padding-left: 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. TELEGRAM ALERT DISPATCHER
# ==========================================
def send_telegram_message(bot_token, chat_id, message):
    """Sends structured HTML alerts via Telegram Bot API."""
    if not bot_token or not chat_id:
        return False, "Missing Token or Chat ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200, res.json().get("description", "Success")
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. KATLEGO AI SIGNAL & ANALYSIS ENGINE
# ==========================================
class KatlegoAIEngine:
    @staticmethod
    def calculate_indicators(df):
        """Computes technicals: EMAs, RSI, and Market Structure (BOS/CHOCH)."""
        df = df.copy()
        # Moving Averages
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Structural Highs & Lows
        df['Pivot_High'] = df['high'][(df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))]
        df['Pivot_Low'] = df['low'][(df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))]
        
        return df

    @staticmethod
    def evaluate_signal(df):
        """Generates Strong/Weak signals based on Smart Money Concepts & Momentum."""
        if len(df) < 50:
            return "NEUTRAL", "INSUFFICIENT DATA", 0

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        reasons = []

        # Trend & Momentum Alignment
        if latest['close'] > latest['EMA_20'] > latest['EMA_50']:
            score += 2
            reasons.append("Bullish EMA Alignment (20 > 50)")
        elif latest['close'] < latest['EMA_20'] < latest['EMA_50']:
            score -= 2
            reasons.append("Bearish EMA Alignment (20 < 50)")

        # RSI Momentum
        if 50 < latest['RSI'] < 70:
            score += 1
            reasons.append("Bullish RSI Momentum")
        elif 30 < latest['RSI'] < 50:
            score -= 1
            reasons.append("Bearish RSI Momentum")

        # Break of Structure / Market Structure Shift
        if latest['close'] > prev['high']:
            score += 2
            reasons.append("Bullish Break of Structure (BOS)")
        elif latest['close'] < prev['low']:
            score -= 2
            reasons.append("Bearish Break of Structure (BOS)")

        # Classification Logic
        if score >= 4:
            return "STRONG BUY", reasons, score
        elif score in [2, 3]:
            return "WEAK BUY", reasons, score
        elif score <= -4:
            return "STRONG SELL", reasons, score
        elif score in [-2, -3]:
            return "WEAK SELL", reasons, score
        else:
            return "NEUTRAL", reasons, score

# ==========================================
# 4. DUMMY DATA GENERATOR (Replace with Live Feed)
# ==========================================
@st.cache_data(ttl=60)
def fetch_market_data(symbol, timeframe, bars=100):
    """Generates synthetic OHLCV data mimicking live feed."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=bars, freq='1H' if timeframe=='1H' else '15min')
    price = 65000.0 if "BTC" in symbol else (2000.0 if "XAU" in symbol else 39000.0)
    
    returns = np.random.normal(0, 0.002, bars)
    prices = price * np.exp(np.cumsum(returns))
    
    highs = prices * (1 + np.abs(np.random.normal(0, 0.001, bars)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.001, bars)))
    opens = prices * (1 + np.random.normal(0, 0.0005, bars))
    
    df = pd.DataFrame({
        'time': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': np.random.randint(100, 10000, bars)
    })
    return df

# ==========================================
# 5. SIDEBAR CONFIGURATION
# ==========================================
st.sidebar.title("⚡ Sekwaila Omega X")
st.sidebar.caption("Katlego AI Trading Engine v2.0")

# Asset & Timeframe Selectors
st.sidebar.subheader("🎯 Market Selection")
symbol = st.sidebar.selectbox("Trading Pair", ["BTCUSD", "XAUUSD", "US30"], index=0)

st.sidebar.write("⏱️ **Timeframe**")
tf_cols = st.sidebar.columns(4)
tf_selected = "1H"
if tf_cols[0].button("M15"): tf_selected = "15m"
if tf_cols[1].button("1H"): tf_selected = "1H"
if tf_cols[2].button("4H"): tf_selected = "4H"
if tf_cols[3].button("D1"): tf_selected = "1D"

st.sidebar.info(f"Active Timeframe: **{tf_selected}**")

# Telegram Bot Integration
st.sidebar.markdown("---")
st.sidebar.subheader("📡 Telegram Notification Layer")
tg_enabled = st.sidebar.checkbox("Enable Telegram Alerts", value=False)
bot_token = st.sidebar.text_input("Bot Token", type="password", help="HTTP API token from @BotFather")
chat_id = st.sidebar.text_input("Chat ID", help="Your Telegram user or channel ID")

# ==========================================
# 6. MAIN DASHBOARD CONTENT
# ==========================================
st.title(f"📊 {symbol} — {tf_selected} Trading Dashboard")

# Fetch & Process Data
raw_data = fetch_market_data(symbol, tf_selected)
df_tech = KatlegoAIEngine.calculate_indicators(raw_data)
signal_type, reasons, score = KatlegoAIEngine.evaluate_signal(df_tech)

# Metric Row Top Bar
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
latest_price = df_tech['close'].iloc[-1]
prev_price = df_tech['close'].iloc[-2]
price_chg = ((latest_price - prev_price) / prev_price) * 100

m_col1.metric("Live Price", f"${latest_price:,.2f}", f"{price_chg:+.2f}%")
m_col2.metric("RSI (14)", f"{df_tech['RSI'].iloc[-1]:.1f}")
m_col3.metric("EMA 20", f"${df_tech['EMA_20'].iloc[-1]:,.2f}")
m_col4.metric("EMA 50", f"${df_tech['EMA_50'].iloc[-1]:,.2f}")

st.markdown("---")

# Main Section: Layout Grid (Chart + Katlego AI Signals)
chart_col, signal_col = st.columns([3, 1])

with chart_col:
    st.subheader("📈 TradingView Style Interactive Chart")
    
    # Custom Interactive Native Chart Overlay
    st.line_chart(df_tech.set_index('time')[['close', 'EMA_20', 'EMA_50']])
    
    # Native Candle Table Display
    with st.expander("🔍 View Raw OHLCV Price Data"):
        st.dataframe(df_tech.tail(15)[['time', 'open', 'high', 'low', 'close', 'volume']].style.format({
            'open': '{:.2f}', 'high': '{:.2f}', 'low': '{:.2f}', 'close': '{:.2f}'
        }), use_container_width=True)

with signal_col:
    st.subheader("🤖 Katlego AI Analysis")
    
    # Styled Signal Output Card
    css_class = "neutral"
    if "STRONG BUY" in signal_type: css_class = "strong-buy"
    elif "WEAK BUY" in signal_type: css_class = "weak-buy"
    elif "STRONG SELL" in signal_type: css_class = "strong-sell"
    elif "WEAK SELL" in signal_type: css_class = "weak-sell"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 12px; color: #787b86;">SIGNAL CONFIRMATION</div>
        <div class="{css_class}" style="font-size: 20px; margin: 5px 0;">{signal_type}</div>
        <div style="font-size: 12px; color: #d1d4dc;">Confidence Score: <b>{score}/5</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("**Confluence Factors:**")
    for r in reasons:
        st.markdown(f"• {r}")
        
    st.markdown("---")
    
    # Trigger Manual Telegram Alert Button
    if st.button("🚀 Broadcast Alert to Telegram"):
        if tg_enabled:
            alert_msg = (
                f"<b>⚡ OMEGA X / KATLEGO AI ALERT</b>\n\n"
                f"<b>Asset:</b> {symbol}\n"
                f"<b>Timeframe:</b> {tf_selected}\n"
                f"<b>Signal:</b> {signal_type}\n"
                f"<b>Price:</b> ${latest_price:,.2f}\n"
                f"<b>RSI:</b> {df_tech['RSI'].iloc[-1]:.1f}\n\n"
                f"<b>Factors:</b>\n" + "\n".join([f"- {r}" for r in reasons])
            )
            success, err = send_telegram_message(bot_token, chat_id, alert_msg)
            if success:
                st.success("Alert sent successfully!")
            else:
                st.error(f"Telegram Failed: {err}")
        else:
            st.warning("Enable Telegram in sidebar first.")

# ==========================================
# 7. ECONOMIC NEWS FILTER SECTION
# ==========================================
st.markdown("---")
st.subheader("📰 High-Impact Economic News Filter")

news_col1, news_col2 = st.columns([2, 1])

with news_col1:
    # Simulated Forex Factory High Impact Events
    news_events = [
        {"time": "14:30 SAST", "currency": "USD", "event": "CPI MoM (Inflation Data)", "impact": "HIGH", "forecast": "0.3%", "previous": "0.2%"},
        {"time": "16:00 SAST", "currency": "USD", "event": "ISM Manufacturing PMI", "impact": "HIGH", "forecast": "48.5", "previous": "47.8"},
        {"time": "20:00 SAST", "currency": "USD", "event": "FOMC Meeting Minutes", "impact": "CRITICAL", "forecast": "-", "previous": "-"}
    ]
    
    news_df = pd.DataFrame(news_events)
    
    def highlight_impact(val):
        color = '#f23645' if val in ['HIGH', 'CRITICAL'] else '#26a69a'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        news_df.style.map(highlight_impact, subset=['impact']),
        use_container_width=True,
        hide_index=True
    )

with news_col2:
    st.info("""
    <b>🛡️ News Risk Protocol:</b><br/>
    Katlego AI recommends pausing automated executions 15 minutes before and after high-impact USD economic events to avoid spread expansion.
    """, unsafe_allow_html=True)
