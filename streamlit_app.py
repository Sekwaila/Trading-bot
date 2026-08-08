import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & DARK THEME CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #131722;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Bottom Navigation Bar styling */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #1e222d;
        border-top: 1px solid #2a2e39;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 9999;
    }
    .nav-item {
        color: #787b86;
        text-align: center;
        font-size: 11px;
        text-decoration: none;
    }
    .nav-item.active {
        color: #2962ff;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. GENERATE SYNTHETIC / MOCK CANDLESTICK DATA WITH SIGNALS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def generate_chart_data(symbol, timeframe_num):
    np.random.seed(42)
    dates = pd.date_range(end=datetime.datetime.now(), periods=60, freq='15min')
    
    base_price = 64900.0 if "BTC" in symbol else (2350.0 if "XAU" in symbol else 42000.0)
    prices = [base_price]
    for _ in range(59):
        prices.append(prices[-1] + np.random.normal(0, 15))
        
    df = pd.DataFrame({'Date': dates, 'Close': prices})
    df['Open'] = df['Close'].shift(1).fillna(df['Close'] - 5)
    df['High'] = df[['Open', 'Close']].max(axis=1) + np.random.uniform(5, 20, size=60)
    df['Low'] = df[['Open', 'Close']].min(axis=1) - np.random.uniform(5, 20, size=60)
    
    # Calculate indicators
    df['RSI'] = 53.1
    df['ADX'] = 19.8
    df['ATR'] = 26.42
    
    return df

# -----------------------------------------------------------------------------
# 3. TOP CONTROLS (SYMBOL & TIMEFRAME SELECTOR)
# -----------------------------------------------------------------------------
col_sym, col_tf, col_engine = st.columns([2, 3, 2])

with col_sym:
    symbol = st.selectbox("Symbol", ["BTCUSD", "XAUUSD", "US30", "EURUSD"], index=0, label_visibility="collapsed")

with col_tf:
    timeframe = st.radio("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1D"], index=2, horizontal=True, label_visibility="collapsed")

with col_engine:
    st.markdown("<p style='text-align:right; color:#2962ff; font-weight:bold; margin-top:5px;'>⚡ SEKWAILA OMEGA X</p>", unsafe_allow_html=True)

df = generate_chart_data(symbol, 15)
last_price = df['Close'].iloc[-1]

# -----------------------------------------------------------------------------
# 4. PLOTLY CANDLESTICK CHART WITH TV OVERLAYS
# -----------------------------------------------------------------------------
fig = go.Figure()

# --- Candlesticks ---
fig.add_trace(go.Candlestick(
    x=df['Date'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    increasing_line_color='#089981',
    decreasing_line_color='#f23645',
    name=symbol
))

# --- Target Levels (TP1 - TP5, ENTRY, SL) ---
entry_price = last_price
tp1 = entry_price + 50.66
tp2 = entry_price + 101.31
tp3 = entry_price + 151.97
tp4 = entry_price + 202.63
tp5 = entry_price + 253.28
sl_price = entry_price - 50.66

levels = [
    ("TP5: " + str(round(tp5, 2)), tp5, "#089981"),
    ("TP4: " + str(round(tp4, 2)), tp4, "#089981"),
    ("TP3: " + str(round(tp3, 2)), tp3, "#089981"),
    ("TP2: " + str(round(tp2, 2)), tp2, "#089981"),
    ("TP1: " + str(round(tp1, 2)), tp1, "#089981"),
    ("ENTRY: " + str(round(entry_price, 2)), entry_price, "#2962ff"),
    ("SL: " + str(round(sl_price, 2)), sl_price, "#f23645")
]

for label, val, color in levels:
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

# --- BUY / SELL Signal Markers ---
fig.add_trace(go.Scatter(
    x=[df['Date'].iloc[-12], df['Date'].iloc[-5]],
    y=[df['Low'].iloc[-12] - 15, df['High'].iloc[-5] + 15],
    mode="text",
    text=["BUY", "SELL"],
    textposition=["bottom center", "top center"],
    textfont=dict(color="white", size=12, family="Arial Black"),
    marker=dict(size=12),
    hoverinfo="none",
    showlegend=False
))

# --- Premium / Discount Background Zones ---
high_max = df['High'].max()
low_min = df['Low'].min()
eq_mid = (high_max + low_min) / 2

# Premium Zone (Red Shade)
fig.add_hrect(y0=eq_mid, y1=high_max, fillcolor="rgba(242, 54, 69, 0.08)", line_width=0)
# Discount Zone (Green Shade)
fig.add_hrect(y0=low_min, y1=eq_mid, fillcolor="rgba(8, 153, 129, 0.08)", line_width=0)

# --- TOP-LEFT INDICATOR OVERLAY TABLE ---
overlay_html = """
<table style='width:210px; background-color:rgba(255, 255, 220, 0.95); border-collapse:collapse; font-size:11px; color:#131722; font-weight:bold;'>
  <tr style='background-color:#f23645; color:white;'>
    <td style='padding:2px 4px;'>BEAR SCORE</td>
    <td style='padding:2px 4px; background-color:#089981; text-align:right;'>STRONG BULL</td>
  </tr>
  <tr><td style='padding:2px 4px;'>Price / VWAP</td><td style='padding:2px 4px; text-align:right; color:#089981;'>ABOVE</td></tr>
  <tr><td style='padding:2px 4px;'>RSI (14)</td><td style='padding:2px 4px; text-align:right;'>53.1</td></tr>
  <tr><td style='padding:2px 4px;'>MACD Trend</td><td style='padding:2px 4px; text-align:right; color:#f23645;'>BEAR</td></tr>
  <tr><td style='padding:2px 4px;'>ADX Power</td><td style='padding:2px 4px; text-align:right;'>19.8</td></tr>
  <tr><td style='padding:2px 4px;'>EMA Cross</td><td style='padding:2px 4px; text-align:right; color:#089981;'>BULL</td></tr>
  <tr><td style='padding:2px 4px;'>ATR 14</td><td style='padding:2px 4px; text-align:right;'>26.42</td></tr>
  <tr><td style='padding:2px 4px;'>Vol Status</td><td style='padding:2px 4px; text-align:right; color:#f57c00;'>LOW</td></tr>
  <tr><td style='padding:2px 4px;'>Trend Str</td><td style='padding:2px 4px; text-align:right; color:#f23645;'>WEAK</td></tr>
  <tr><td style='padding:2px 4px;'>Status</td><td style='padding:2px 4px; text-align:right;'>WAIT</td></tr>
  <tr style='border-top:1px solid #ccc;'><td style='padding:2px 4px;'>Sniper Mode</td><td style='padding:2px 4px; text-align:right; color:#2962ff;'>OMEGA X</td></tr>
</table>
"""

fig.add_annotation(
    dict(
        x=0.01,
        y=0.99,
        xref="paper",
        yref="paper",
        text=overlay_html,
        showarrow=False,
        align="left",
        valign="top"
    )
)

# --- Layout Styling ---
fig.update_layout(
    height=600,
    margin=dict(l=0, r=60, t=10, b=10),
    paper_bgcolor='#131722',
    plot_bgcolor='#131722',
    xaxis=dict(
        gridcolor='#2a2e39',
        showgrid=True,
        rangeslider=dict(visible=False)
    ),
    yaxis=dict(
        gridcolor='#2a2e39',
        showgrid=True,
        side='right'
    )
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. WATCHLIST & QUICK SCANNER EXPANDER
# -----------------------------------------------------------------------------
with st.expander("📋 Watchlist & Live Scanner", expanded=False):
    st.dataframe(
        pd.DataFrame({
            "Asset": ["BTCUSD", "XAUUSD", "US30", "EURUSD"],
            "Price": [64966.00, 2358.40, 39850.10, 1.0850],
            "Signal": ["STRONG BULL", "NEUTRAL", "STRONG BUY", "SELL"],
            "RSI": [53.1, 43.7, 61.9, 38.2]
        }),
        use_container_width=True
    )
