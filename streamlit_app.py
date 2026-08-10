import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & MODERN DARK TERMINAL STYLING
# ==========================================
st.set_page_config(
    page_title="Sekwaila Omega X Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark Terminal Theme Background */
    .stApp {
        background-color: #131722;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }

    /* Top HUD / Technical Metric Bar */
    .hud-card {
        background: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    
    .hud-title {
        font-size: 11px;
        color: #787b86;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .hud-value {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 2px;
    }

    /* Signal Badge Highlights */
    .badge-buy {
        background-color: #26a69a;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .badge-sell {
        background-color: #ef5350;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }

    /* Custom Streamlit Input Overrides */
    div[data-baseweb="select"] > div {
        background-color: #1e222d !important;
        border-color: #2a2e39 !important;
        color: #ffffff !important;
    }
    
    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.title("⚙️ Market Settings")
    symbol = st.selectbox("Symbol", ["BTCUSD", "XAUUSD", "US30", "SP500", "EURUSD"], index=0)
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1D"], index=2)
    
    st.markdown("---")
    st.markdown("### Risk Management")
    account_balance = st.number_input("Account Balance (ZAR)", value=500.0, step=50.0)
    risk_percent = st.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
    
    send_alert = st.checkbox("📩 Send alert on click", value=True)
    
    st.markdown("---")
    if st.button("🚀 Analyze Market", use_container_width=True):
        st.success(f"Market structure calculated for {symbol} ({timeframe})")

# ==========================================
# 3. DUMMY DATA GENERATOR (OHLCV + SMC LEVELS)
# ==========================================
@st.cache_data(ttl=60)
def generate_chart_data(symbol_name):
    np.random.seed(42)
    periods = 60
    dates = [datetime.now() - timedelta(minutes=15 * i) for i in range(periods)][::-1]
    
    base_price = 64900.0 if "BTC" in symbol_name else (2350.0 if "XAU" in symbol_name else 40000.0)
    returns = np.random.normal(0.0002, 0.0015, periods)
    price_path = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({'Datetime': dates})
    df['Open'] = price_path + np.random.uniform(-10, 10, periods)
    df['High'] = df['Open'] + np.abs(np.random.uniform(5, 25, periods))
    df['Low'] = df['Open'] - np.abs(np.random.uniform(5, 25, periods))
    df['Close'] = price_path
    
    # Ensure High is max and Low is min
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
    return df

df = generate_chart_data(symbol)

# Current market levels
current_price = round(df['Close'].iloc[-1], 2)
entry_price = round(current_price - 12.0, 2)
sl_price = round(entry_price - 50.0, 2)
tp1 = round(entry_price + 50.0, 2)
tp2 = round(entry_price + 100.0, 2)
tp3 = round(entry_price + 150.0, 2)
tp4 = round(entry_price + 200.0, 2)
tp5 = round(entry_price + 250.0, 2)

# ==========================================
# 4. TOP METRICS & HUD PANEL
# ==========================================
st.markdown(f"### **{symbol}** · `{timeframe}` · **SEKWAILA OMEGA X**")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-title">Current Price</div>
        <div class="hud-value" style="color: #26a69a;">{current_price}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="hud-card">
        <div class="hud-title">Market Bias</div>
        <div class="hud-value"><span class="badge-buy">STRONG BULL</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="hud-card">
        <div class="hud-title">RSI (14) / ADX</div>
        <div class="hud-value" style="font-size:16px;">53.1 / 19.8</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="hud-card">
        <div class="hud-title">Trend / Volatility</div>
        <div class="hud-value" style="font-size:16px; color:#f0b90b;">WEAK / LOW</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="hud-card">
        <div class="hud-title">Sniper Mode</div>
        <div class="hud-value" style="font-size:15px; color:#29b6f6;">KHANSAAB V.02</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. TRADINGVIEW PLOTLY CANDLESTICK CHART
# ==========================================
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df['Datetime'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name="Price",
    increasing_line_color='#26a69a', 
    decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a',
    decreasing_fillcolor='#ef5350'
))

# Premium Zone Shading (Upper Region)
premium_high = df['High'].max()
premium_low = (df['High'].max() + df['Low'].min()) / 2
fig.add_hrect(
    y0=premium_low, y1=premium_high,
    fillcolor="rgba(239, 83, 80, 0.12)", line_width=0,
    annotation_text="Premium Zone", annotation_position="top left",
    annotation_font_color="#ef5350"
)

# Equilibrium Line
eq_level = (df['High'].max() + df['Low'].min()) / 2
fig.add_hline(
    y=eq_level, line_dash="dash", line_color="#787b86", line_width=1,
    annotation_text="Equilibrium", annotation_position="bottom left"
)

# Entry Line
fig.add_hline(
    y=entry_price, line_color="#29b6f6", line_width=2,
    annotation_text=f"ENTRY: {entry_price}", annotation_position="right",
    annotation_font_color="#29b6f6"
)

# Stop Loss Line
fig.add_hline(
    y=sl_price, line_color="#ef5350", line_width=2,
    annotation_text=f"SL: {sl_price}", annotation_position="right",
    annotation_font_color="#ef5350"
)

# Take Profit Targets
tps = [(tp1, "TP1"), (tp2, "TP2"), (tp3, "TP3"), (tp4, "TP4"), (tp5, "TP5")]
for price, label in tps:
    fig.add_hline(
        y=price, line_color="#26a69a", line_dash="dot", line_width=1.5,
        annotation_text=f"{label}: {price}", annotation_position="right",
        annotation_font_color="#26a69a"
    )

# Buy/Sell Signal Annotations on Chart
fig.add_annotation(
    x=df['Datetime'].iloc[-8], y=df['Low'].iloc[-8],
    text="BUY", showarrow=True, arrowhead=2, arrowcolor="#26a69a",
    ax=0, ay=25, bgcolor="#26a69a", font=dict(color="white", size=11, family="Arial")
)

fig.add_annotation(
    x=df['Datetime'].iloc[-22], y=df['High'].iloc[-22],
    text="SELL", showarrow=True, arrowhead=2, arrowcolor="#ef5350",
    ax=0, ay=-25, bgcolor="#ef5350", font=dict(color="white", size=11, family="Arial")
)

# Chart Layout Adjustments (TradingView Dark Theme Style)
fig.update_layout(
    height=550,
    margin=dict(l=10, r=60, t=10, b=10),
    paper_bgcolor='#131722',
    plot_bgcolor='#131722',
    xaxis=dict(
        gridcolor='#1e222d',
        showgrid=True,
        rangeslider=dict(visible=False),
        type='date'
    ),
    yaxis=dict(
        gridcolor='#1e222d',
        showgrid=True,
        side='right',
        tickformat='.2f'
    ),
    showlegend=False,
    font=dict(color='#d1d4dc')
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================================
# 6. ACTION CONTROLS & SNIPER OVERRIDES
# ==========================================
c_act1, c_act2, c_act3 = st.columns([1, 1, 2])
with c_act1:
    if st.button("🟢 BUY EXECUTION", use_container_width=True):
        st.success(f"Buy Signal Triggered @ {entry_price} | SL: {sl_price}")
with c_act2:
    if st.button("🔴 SELL EXECUTION", use_container_width=True):
        st.error(f"Sell Signal Triggered @ {entry_price} | SL: {sl_price}")
with c_act3:
    st.info("💡 **Katlego AI Status:** Monitoring Break of Structure (BOS) & Change of Character (CHoCH) on 15m timeframe.")
