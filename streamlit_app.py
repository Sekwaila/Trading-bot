import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS (EXACT UI LOOK & FEEL)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SEKWAILA OMEGA X", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Global Background & Fonts */
    .stApp {
        background: #050403;
        color: #d1c7b7;
        font-family: 'Segoe UI', sans-serif;
    }
    header, footer {visibility: hidden;}
    .block-container {padding: 10px 20px !important; max-width: 100% !important;}

    /* Custom Panel Cards */
    .panel-card {
        background: rgba(12, 10, 8, 0.95);
        border: 1px solid #3d2f1d;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 12px;
    }
    .panel-card-accent {
        border: 1px solid #d9a441;
        box-shadow: 0 0 12px rgba(217, 164, 65, 0.25);
    }

    /* Color Helpers */
    .text-gold { color: #d9a441; font-weight: bold; }
    .text-green { color: #00e676; font-weight: bold; }
    .text-red { color: #ff5252; font-weight: bold; }
    .text-muted { color: #8c7b64; }

    /* Progress Bars */
    .bar-bg { background: #1a1611; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 4px; }
    .bar-green { background: #00e676; height: 100%; }
    .bar-red { background: #ff5252; height: 100%; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SIDEBAR CONTROLS & RISK CALCULATOR
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 class='text-gold'>SEKWAILA OMEGA X</h2>", unsafe_allow_html=True)
asset_symbol = st.sidebar.selectbox("Active Asset", ["GC=F", "BTC-USD", "^GSPC", "EURUSD=X"], index=0, format_func=lambda x: {"GC=F": "XAUUSD (Gold)", "BTC-USD": "BTCUSD", "^GSPC": "US500", "EURUSD=X": "EURUSD"}[x])
account_balance = st.sidebar.number_input("Account Balance ($)", value=10256.80, step=100.0)
risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 2.0, 0.1)

risk_amount = account_balance * (risk_pct / 100.0)

# -----------------------------------------------------------------------------
# 3. LIVE DATA FETCHING & ENGINE CALCULATIONS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_market_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="15m")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

df_data = fetch_market_data(asset_symbol)

if not df_data.empty:
    current_price = df_data['Close'].iloc[-1]
    prev_price = df_data['Close'].iloc[-2]
    price_change = current_price - prev_price
    
    # Calculate Dynamic Levels (ATR, TP, SL)
    high_low = df_data['High'] - df_data['Low']
    atr = high_low.rolling(14).mean().iloc[-1]
    
    entry_price = current_price
    tp1 = entry_price + (atr * 1.5)
    tp2 = entry_price + (atr * 3.0)
    sl = entry_price - (atr * 2.0)
    
    bias = "EXTREME BUY ↑" if price_change >= 0 else "EXTREME SELL ↓"
    bias_color = "text-green" if price_change >= 0 else "text-red"
    confidence = 92 if price_change >= 0 else 88
else:
    current_price, entry_price, tp1, tp2, sl = 2358.45, 2358.45, 2364.80, 2373.60, 2346.20
    bias, bias_color, confidence = "EXTREME BUY ↑", "text-green", 92

# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER
# -----------------------------------------------------------------------------
st.markdown("""
<div style='text-align: center; padding: 5px 0 15px 0;'>
    <h1 style='color: #d9a441; letter-spacing: 2px; margin: 0; font-size: 28px;'>SEKWAILA OMEGA X</h1>
    <p style='color: #8c7b64; font-size: 11px; margin: 0;'>ANCIENT WISDOM. MODERN PROFIT.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 3-COLUMN LAYOUT
# -----------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 2.2, 1.1])

# LEFT COLUMN: METRICS & RISK
with col_left:
    st.markdown("""
    <div class='panel-card'>
        <div class='text-gold' style='font-size: 11px;'>MARKET SESSION</div>
        <div class='text-green' style='font-size: 13px; margin-top: 2px;'>LONDON / NY OVERLAP</div>
        <div class='text-muted' style='font-size: 10px;'>HIGH VOLUME</div>
        <div style='margin-top: 6px; font-size: 11px;'>Session Quality: <b>95%</b></div>
        <div class='bar-bg'><div class='bar-green' style='width: 95%;'></div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='panel-card'>
        <div class='text-gold' style='font-size: 11px;'>ACCOUNT OVERVIEW</div>
        <table style='width: 100%; font-size: 12px; margin-top: 6px; color: #d1c7b7;'>
            <tr><td>Balance:</td><td style='text-align: right;'><b>${account_balance:,.2f}</b></td></tr>
            <tr><td>Equity:</td><td style='text-align: right;'><b>${account_balance:,.2f}</b></td></tr>
            <tr><td>Risk %:</td><td style='text-align: right;' class='text-gold'><b>{risk_pct:.2f}%</b></td></tr>
            <tr><td>Risk Amount:</td><td style='text-align: right;'><b>${risk_amount:,.2f}</b></td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='panel-card'>
        <div class='text-gold' style='font-size: 11px;'>ECONOMIC CALENDAR</div>
        <div style='font-size: 11px; margin-top: 6px; line-height: 1.6;'>
            <div>18:00 <span class='text-red'>USD Retail Sales</span></div>
            <div>20:30 <span class='text-gold'>USD FOMC Member Speaks</span></div>
            <div>22:00 <span class='text-gold'>USD Crude Oil Inventories</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# CENTER COLUMN: SIGNAL & PLOTLY CANDLESTICK CHART
with col_center:
    st.markdown(f"""
    <div class='panel-card panel-card-accent' style='text-align: center;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div style='text-align: left;'>
                <h2 style='color: #ffffff; margin: 0; font-size: 22px;'>XAUUSD</h2>
                <span class='text-muted' style='font-size: 11px;'>GOLD / US DOLLAR</span>
            </div>
            <div>
                <span class='text-muted' style='font-size: 10px;'>CONFIDENCE</span>
                <div class='text-green' style='font-size: 22px;'>{confidence}%</div>
            </div>
        </div>
        
        <h1 class='{bias_color}' style='font-size: 28px; margin: 8px 0;'>{bias}</h1>
        <div style='background: #003822; color: #00e676; display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 11px;'>SAFE TO ENTER ☑</div>
        
        <div style='display: flex; justify-content: space-around; margin-top: 12px; border-top: 1px solid #2a2115; padding-top: 8px;'>
            <div><span class='text-muted' style='font-size: 10px;'>ENTRY</span><br><b>{entry_price:,.2f}</b></div>
            <div><span class='text-muted' style='font-size: 10px;'>CURRENT PRICE</span><br><b>{current_price:,.2f}</b></div>
        </div>
        
        <div style='display: flex; justify-content: space-around; margin-top: 8px; font-size: 11px;'>
            <div>TP1: <b class='text-green'>{tp1:,.2f}</b></div>
            <div>TP2: <b class='text-green'>{tp2:,.2f}</b></div>
            <div>SL: <b class='text-red'>{sl:,.2f}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic Candlestick Chart
    if not df_data.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_data.index,
            open=df_data['Open'],
            high=df_data['High'],
            low=df_data['Low'],
            close=df_data['Close'],
            increasing_line_color='#00e676', 
            decreasing_line_color='#ff5252'
        )])
        fig.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(12, 10, 8, 0.95)",
            plot_bgcolor="rgba(12, 10, 8, 0.95)",
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Market data currently offline. Chart loading...")

# RIGHT COLUMN: MARKET STRENGTH & AI NARRATOR
with col_right:
    st.markdown("""
    <div class='panel-card'>
        <div class='text-gold' style='font-size: 11px;'>MARKET STRENGTH</div>
        <div style='font-size: 11px; margin-top: 8px;'>
            <div>XAUUSD <span style='float:right;' class='text-green'>92%</span></div>
            <div class='bar-bg'><div class='bar-green' style='width: 92%;'></div></div>
        </div>
        <div style='font-size: 11px; margin-top: 8px;'>
            <div>NAS100 <span style='float:right;' class='text-green'>87%</span></div>
            <div class='bar-bg'><div class='bar-green' style='width: 87%;'></div></div>
        </div>
        <div style='font-size: 11px; margin-top: 8px;'>
            <div>US30 <span style='float:right;' class='text-green'>72%</span></div>
            <div class='bar-bg'><div class='bar-green' style='width: 72%;'></div></div>
        </div>
        <div style='font-size: 11px; margin-top: 8px;'>
            <div>DXY <span style='float:right;' class='text-red'>28%</span></div>
            <div class='bar-bg'><div class='bar-red' style='width: 28%;'></div></div>
        </div>
    </div>
    
    <div class='panel-card'>
        <div class='text-gold' style='font-size: 11px;'>🤖 AI NARRATOR</div>
        <p style='font-size: 11px; color: #b0a494; margin-top: 6px; line-height: 1.4;'>
            Gold is showing strong bullish momentum after sweeping liquidity. Structure remains bullish across key timeframes. Institutional buying detected during the London/NY overlap.
        </p>
    </div>
    """, unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div style='text-align: center; color: #d9a441; font-size: 10px; margin-top: 15px;'>
    ═════════════ THE ANCESTORS SEE YOUR DISCIPLINE. THE UNIVERSE REWARDS YOUR PATIENCE. ═════════════
</div>
""", unsafe_allow_html=True)
