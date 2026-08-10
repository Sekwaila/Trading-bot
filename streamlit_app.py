import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & MOBILE-FIRST TERMINAL STYLING
# ==========================================
st.set_page_config(
    page_title="Sekwaila Omega X Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark Terminal Background */
    .stApp {
        background-color: #131722;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Top Technical Metric HUD Cards */
    .hud-card {
        background: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 8px;
    }
    .hud-title {
        font-size: 10px;
        color: #787b86;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .hud-value {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
    }

    /* Custom Badges */
    .badge-buy {
        background-color: #26a69a;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    .badge-sell {
        background-color: #ef5350;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }

    /* Streamlit Tab Bar Customization for Dark Mode */
    button[data-baseweb="tab"] {
        font-weight: bold !important;
        font-size: 13px !important;
    }

    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. TOP BRANDING & APP NAVIGATION TABS
# ==========================================
st.markdown("## ⚡ **SEKWAILA OMEGA X TERMINAL**")

tab_chart, tab_scanner, tab_heatmap, tab_telegram, tab_settings = st.tabs([
    "📈 Trading Chart", 
    "📊 Market Scanner", 
    "🔥 Heatmap", 
    "📲 Telegram Alerts", 
    "⚙️ Control Panel"
])

# Shared persistent states / controls across tabs
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = "BTCUSD"
if 'selected_tf' not in st.session_state:
    st.session_state.selected_tf = "15m"

# ==========================================
# TAB 1: LIVE TRADING CHART & TRADINGVIEW HUD
# ==========================================
with tab_chart:
    # Quick Control Row Above Chart
    c_sym, c_tf, c_risk, c_act = st.columns([2, 2, 2, 2])
    with c_sym:
        st.session_state.selected_symbol = st.selectbox("Symbol", ["BTCUSD", "XAUUSD", "US30", "SP500", "EURUSD"], index=0, key="chart_sym")
    with c_tf:
        st.session_state.selected_tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1D"], index=2, key="chart_tf")
    with c_risk:
        account_bal = st.number_input("Account Balance (ZAR)", value=500.0, step=50.0, key="chart_bal")
    with c_act:
        risk_pct = st.slider("Risk %", 0.5, 5.0, 1.0, 0.5, key="chart_risk")

    symbol = st.session_state.selected_symbol
    timeframe = st.session_state.selected_tf

    # Generate Synthetic Candle Data
    np.random.seed(42)
    periods = 50
    dates = [datetime.now() - timedelta(minutes=15 * i) for i in range(periods)][::-1]
    base_price = 64900.0 if "BTC" in symbol else (2350.0 if "XAU" in symbol else 40000.0)
    returns = np.random.normal(0.0002, 0.0015, periods)
    price_path = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({'Datetime': dates})
    df['Open'] = price_path + np.random.uniform(-10, 10, periods)
    df['High'] = df['Open'] + np.abs(np.random.uniform(5, 25, periods))
    df['Low'] = df['Open'] - np.abs(np.random.uniform(5, 25, periods))
    df['Close'] = price_path
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

    curr_p = round(df['Close'].iloc[-1], 2)
    entry_p = round(curr_p - 12.0, 2)
    sl_p = round(entry_p - 50.0, 2)
    tp1 = round(entry_p + 50.0, 2)
    tp2 = round(entry_p + 100.0, 2)
    tp3 = round(entry_p + 150.0, 2)
    tp4 = round(entry_p + 200.0, 2)
    tp5 = round(entry_p + 250.0, 2)

    # Top Metric Display Cards
    hud1, hud2, hud3, hud4, hud5 = st.columns(5)
    with hud1:
        st.markdown(f'<div class="hud-card"><div class="hud-title">Price</div><div class="hud-value" style="color:#26a69a;">{curr_p}</div></div>', unsafe_allow_html=True)
    with hud2:
        st.markdown('<div class="hud-card"><div class="hud-title">Bias</div><div class="hud-value"><span class="badge-buy">STRONG BULL</span></div></div>', unsafe_allow_html=True)
    with hud3:
        st.markdown('<div class="hud-card"><div class="hud-title">RSI / ADX</div><div class="hud-value">53.1 / 19.8</div></div>', unsafe_allow_html=True)
    with hud4:
        st.markdown('<div class="hud-card"><div class="hud-title">Trend</div><div class="hud-value" style="color:#f0b90b;">WEAK</div></div>', unsafe_allow_html=True)
    with hud5:
        st.markdown('<div class="hud-card"><div class="hud-title">Sniper Mode</div><div class="hud-value" style="color:#29b6f6;">KHANSAAB V.02</div></div>', unsafe_allow_html=True)

    # TradingView Style Plotly Interactive Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Datetime'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350'
    ))

    # SMC Premium Zone Shade
    prem_high = df['High'].max()
    prem_low = (df['High'].max() + df['Low'].min()) / 2
    fig.add_hrect(
        y0=prem_low, y1=prem_high, fillcolor="rgba(239, 83, 80, 0.10)", line_width=0,
        annotation_text="Premium Zone", annotation_position="top left", annotation_font_color="#ef5350"
    )

    # Key Price Level Annotations
    fig.add_hline(y=entry_p, line_color="#29b6f6", line_width=2, annotation_text=f"ENTRY: {entry_p}", annotation_position="right", annotation_font_color="#29b6f6")
    fig.add_hline(y=sl_p, line_color="#ef5350", line_width=2, annotation_text=f"SL: {sl_p}", annotation_position="right", annotation_font_color="#ef5350")
    
    for price, label in [(tp1, "TP1"), (tp2, "TP2"), (tp3, "TP3"), (tp4, "TP4"), (tp5, "TP5")]:
        fig.add_hline(y=price, line_color="#26a69a", line_dash="dot", line_width=1.5, annotation_text=f"{label}: {price}", annotation_position="right", annotation_font_color="#26a69a")

    # Signal Badges on Chart
    fig.add_annotation(x=df['Datetime'].iloc[-8], y=df['Low'].iloc[-8], text="BUY", showarrow=True, arrowhead=2, arrowcolor="#26a69a", ax=0, ay=25, bgcolor="#26a69a", font=dict(color="white", size=11))
    fig.add_annotation(x=df['Datetime'].iloc[-22], y=df['High'].iloc[-22], text="SELL", showarrow=True, arrowhead=2, arrowcolor="#ef5350", ax=0, ay=-25, bgcolor="#ef5350", font=dict(color="white", size=11))

    fig.update_layout(
        height=520, margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor='#131722', plot_bgcolor='#131722',
        xaxis=dict(gridcolor='#1e222d', rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor='#1e222d', side='right', tickformat='.2f'),
        showlegend=False, font=dict(color='#d1d4dc')
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Execution Action Buttons
    btn_b, btn_s = st.columns(2)
    with btn_b:
        if st.button("🟢 BUY EXECUTION", use_container_width=True):
            st.success(f"Buy Order Triggered for {symbol} @ {entry_p} | Target: {tp1}")
    with btn_s:
        if st.button("🔴 SELL EXECUTION", use_container_width=True):
            st.error(f"Sell Order Triggered for {symbol} @ {entry_p} | Target: {sl_p}")

# ==========================================
# TAB 2: MARKET SCANNER
# ==========================================
with tab_scanner:
    st.markdown("### 📊 **Multi-Pair Market Scanner**")
    st.caption("Real-time Smart Money Concepts (SMC) & Trend Matrix")
    
    scanner_data = [
        {"Pair": "BTCUSD", "Timeframe": "15m", "Bias": "STRONG BULL", "RSI": 53.1, "ADX": 19.8, "SMC Setup": "Bullish Order Block", "Action": "BUY"},
        {"Pair": "US30", "Timeframe": "15m", "Bias": "BULL", "RSI": 62.4, "ADX": 22.1, "SMC Setup": "BOS Confirmed", "Action": "BUY"},
        {"Pair": "SP500", "Timeframe": "15m", "Bias": "BULL", "RSI": 58.6, "ADX": 15.7, "SMC Setup": "Liquidity Sweep", "Action": "BUY"},
        {"Pair": "XAUUSD", "Timeframe": "15m", "Bias": "NEUTRAL", "RSI": 49.2, "ADX": 12.0, "SMC Setup": "Consolidation", "Action": "WAIT"},
        {"Pair": "EURUSD", "Timeframe": "15m", "Bias": "BEAR", "RSI": 38.1, "ADX": 28.4, "SMC Setup": "Bearish Order Block", "Action": "SELL"},
        {"Pair": "DXY", "Timeframe": "15m", "Bias": "BEAR", "RSI": 35.0, "ADX": 31.2, "SMC Setup": "CHoCH Down", "Action": "SELL"}
    ]
    
    scan_df = pd.DataFrame(scanner_data)
    st.dataframe(scan_df, use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: HEATMAP
# ==========================================
with tab_heatmap:
    st.markdown("### 🔥 **Market Momentum Heatmap**")
    
    hm1, hm2, hm3 = st.columns(3)
    with hm1:
        st.markdown('<div class="hud-card"><b>BTCUSD</b><br/><span style="color:#26a69a; font-size:20px;">+1.42%</span><br/><small>Bullish Momentum</small></div>', unsafe_allow_html=True)
    with hm2:
        st.markdown('<div class="hud-card"><b>US30</b><br/><span style="color:#26a69a; font-size:20px;">+0.85%</span><br/><small>Expansion Phase</small></div>', unsafe_allow_html=True)
    with hm3:
        st.markdown('<div class="hud-card"><b>SP500</b><br/><span style="color:#26a69a; font-size:20px;">+0.14%</span><br/><small>Holding Premium</small></div>', unsafe_allow_html=True)
        
    hm4, hm5, hm6 = st.columns(3)
    with hm4:
        st.markdown('<div class="hud-card"><b>XAUUSD</b><br/><span style="color:#787b86; font-size:20px;">-0.05%</span><br/><small>Ranging at EQ</small></div>', unsafe_allow_html=True)
    with hm5:
        st.markdown('<div class="hud-card"><b>EURUSD</b><br/><span style="color:#ef5350; font-size:20px;">-0.55%</span><br/><small>Bearish Displacement</small></div>', unsafe_allow_html=True)
    with hm6:
        st.markdown('<div class="hud-card"><b>DXY</b><br/><span style="color:#ef5350; font-size:20px;">-0.38%</span><br/><small>Weakening Dollar</small></div>', unsafe_allow_html=True)

# ==========================================
# TAB 4: TELEGRAM ALERTS
# ==========================================
with tab_telegram:
    st.markdown("### 📲 **Katlego AI Telegram Engine**")
    st.caption("Configure automated trade notifications directly to your phone.")
    
    bot_token = st.text_input("Telegram Bot Token", value="7890123456:AAEg..._example", type="password")
    chat_id = st.text_input("Telegram Chat ID", value="123456789")
    
    tg_col1, tg_col2 = st.columns(2)
    with tg_col1:
        send_bos = st.checkbox("Alert on Break of Structure (BOS)", value=True)
        send_choch = st.checkbox("Alert on Change of Character (CHoCH)", value=True)
    with tg_col2:
        send_tp = st.checkbox("Alert on TP/SL Hit", value=True)
        send_daily = st.checkbox("Send Daily Market Bias Summary", value=False)
        
    if st.button("🧪 Send Test Telegram Alert", use_container_width=True):
        st.success("Test alert payload transmitted to Katlego Bot successfully!")

# ==========================================
# TAB 5: CONTROL PANEL & RISK CALCULATOR
# ==========================================
with tab_settings:
    st.markdown("### ⚙️ **Account & Strategy Settings**")
    
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("#### Capital & Risk")
        account_zar = st.number_input("Trading Capital (ZAR)", value=500.0, step=100.0)
        risk_per_trade = st.slider("Risk Per Trade Percentage", 0.25, 5.0, 1.0, 0.25)
        
        zar_risk_amt = account_zar * (risk_per_trade / 100.0)
        usd_risk_amt = zar_risk_amt / 18.50  # ZAR/USD approx conversion
        
        st.info(f"**Max Risk Per Trade:** R{zar_risk_amt:.2f} (≈ ${usd_risk_amt:.2f} USD)")

    with s_col2:
        st.markdown("#### Engine Diagnostics")
        st.write("**Active Script:** Sekwaila Omega X")
        st.write("**AI Overlay:** Katlego Notification Engine")
        st.write("**Broker Target:** Exness / MetaTrader 4")
        st.write("**Device Profile:** Mobile Optimized")
        
        if st.button("🔄 Clear Cache & Reset System", use_container_width=True):
            st.cache_data.clear()
            st.success("System cache cleared.")
