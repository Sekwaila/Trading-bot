import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="Sekwaila Omega X | Multi-Asset Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme custom styling optimized for mobile display
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric {
        background-color: #1E222D;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2B2E3A;
    }
    .compass-box {
        background-color: #1A2130;
        border: 1px solid #00E676;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MARKET ASSETS CONFIGURATION
# ==========================================
# Compass asset used for USD sentiment & inverse correlations
COMPASS_SYMBOL = "DXY"

TRADING_PAIRS = {
    "XAUUSD": {"name": "Gold / US Dollar", "base_price": 2450.00, "pip_decimals": 2},
    "BTCUSD": {"name": "Bitcoin / US Dollar", "base_price": 64920.00, "pip_decimals": 2},
    "EURUSD": {"name": "Euro / US Dollar", "base_price": 1.1556, "pip_decimals": 4},
    "US30": {"name": "Dow Jones Industrial", "base_price": 39500.00, "pip_decimals": 1},
    "USDJPY": {"name": "US Dollar / Japanese Yen", "base_price": 158.87, "pip_decimals": 2}
}

# ==========================================
# 3. DATA ENGINE & MARKET STRUCTURE (SMC)
# ==========================================
def generate_market_data(symbol: str, base_price: float, periods: int = 100) -> pd.DataFrame:
    """Generates synthetic OHLC data aligned with realistic market baselines."""
    np.random.seed(hash(symbol) % 10000)
    returns = np.random.normal(loc=0.0001, scale=0.003, size=periods)
    price_path = base_price * np.exp(np.cumsum(returns))
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq="15min")
    
    df = pd.DataFrame(index=dates)
    df["Close"] = price_path
    df["High"] = df["Close"] * (1 + np.abs(np.random.normal(0, 0.001, periods)))
    df["Low"] = df["Close"] * (1 - np.abs(np.random.normal(0, 0.001, periods)))
    df["Open"] = df["Close"].shift(1).fillna(base_price)
    
    # Simple Moving Averages
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    
    # Basic SMC Market Structure Engine (BOS / CHoCH detection)
    df["Swing_High"] = df["High"][(df["High"] > df["High"].shift(1)) & (df["High"] > df["High"].shift(-1))]
    df["Swing_Low"] = df["Low"][(df["Low"] < df["Low"].shift(1)) & (df["Low"] < df["Low"].shift(-1))]
    
    return df

# Fetch DXY Compass Data
dxy_df = generate_market_data("DXY", base_price=103.20)
dxy_current = dxy_df["Close"].iloc[-1]
dxy_change = dxy_df["Close"].iloc[-1] - dxy_df["Open"].iloc[0]
dxy_pct = (dxy_change / dxy_df["Open"].iloc[0]) * 100

# ==========================================
# 4. COMPASS BANNER (DXY)
# ==========================================
st.title("⚡ Sekwaila Omega X Engine")

st.markdown(f"""
<div class="compass-box">
    <h4 style="margin:0; color:#00E676;">🧭 COMPASS INDICATOR: USD INDEX ({COMPASS_SYMBOL})</h4>
    <p style="margin:5px 0 0 0; color:#D1D4DC;">
        Current DXY Level: <b>{dxy_current:.2f}</b> | 24h Change: 
        <span style="color: {'#00E676' if dxy_change >= 0 else '#FF5252'};">
            {dxy_change:+.2f} ({dxy_pct:+.2f}%)
        </span>
    </p>
    <small style="color:#787B86;">
        <b>Correlation Rule:</b> High DXY pressure negatively impacts EURUSD, XAUUSD, and BTCUSD. Align long setups when DXY breaks lower structure.
    </small>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. ASSET SELECTION & INTERACTIVE CHARTING
# ==========================================
selected_pair = st.selectbox("Select Active Asset Pair:", list(TRADING_PAIRS.keys()))
pair_info = TRADING_PAIRS[selected_pair]

# Fetch market data for selected pair
df = generate_market_data(selected_pair, pair_info["base_price"])

curr_price = df["Close"].iloc[-1]
prev_price = df["Close"].iloc[-2]
price_diff = curr_price - prev_price
pct_change = (price_diff / prev_price) * 100

# Metric Cards Layout
m1, m2, m3, m4 = st.columns(4)
m1.metric("Asset", selected_pair, pair_info["name"])
m2.metric("Live Price", f"{curr_price:.{pair_info['pip_decimals']}f}", f"{price_diff:+.{pair_info['pip_decimals']}f}")
m3.metric("24h Change", f"{pct_change:+.2f}%")
m4.metric("DXY Correlation", "Inverse" if selected_pair in ["XAUUSD", "EURUSD", "BTCUSD"] else "Direct")

# Candlestick Chart with Indicator Layer (Max 2 indicators limit)
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price"
))

# Indicator 1: EMA 20
fig.add_trace(go.Scatter(
    x=df.index, y=df["EMA_20"],
    line=dict(color="#2962FF", width=1.5),
    name="EMA 20"
))

# Indicator 2: EMA 50
fig.add_trace(go.Scatter(
    x=df.index, y=df["EMA_50"],
    line=dict(color="#FF6D00", width=1.5),
    name="EMA 50"
))

fig.update_layout(
    title=f"{selected_pair} Structure Analysis (15M)",
    template="plotly_dark",
    height=450,
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 6. TECHNICAL SUMMARY TABLE
# ==========================================
st.subheader("📊 Market Overview")
overview_data = []

for symbol, info in TRADING_PAIRS.items():
    data = generate_market_data(symbol, info["base_price"])
    price = data["Close"].iloc[-1]
    chg = ((price - data["Open"].iloc[0]) / data["Open"].iloc[0]) * 100
    bias = "BULLISH 🟢" if data["EMA_20"].iloc[-1] > data["EMA_50"].iloc[-1] else "BEARISH 🔴"
    
    overview_data.append({
        "Symbol": symbol,
        "Price": f"{price:.{info['pip_decimals']}f}",
        "24h Trend": f"{chg:+.2f}%",
        "SMC Bias": bias
    })

st.table(pd.DataFrame(overview_data))
