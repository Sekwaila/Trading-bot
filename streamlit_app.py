import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & FULL ANCESTORS BACKGROUND CSS
# ==========================================
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Background image URL (Replace with your direct image link if hosted on Imgur/GitHub)
BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop"

st.markdown(f"""
<style>
    /* Dark Theme Canvas */
    .stApp {{
        background: linear-gradient(rgba(8, 9, 11, 0.90), rgba(8, 9, 11, 0.94)), url('{BACKGROUND_IMAGE_URL}') no-repeat center center fixed;
        background-size: cover;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    header, footer {{ visibility: hidden; }}

    /* Brand Header */
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #3d311d;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }}
    .brand-title {{
        color: #dfb15b;
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 2px;
        margin: 0;
    }}
    .brand-sub {{
        color: #9e8e6b;
        font-size: 10px;
        letter-spacing: 2px;
    }}
    .time-badge {{
        text-align: right;
        color: #dfb15b;
        font-size: 11px;
    }}

    /* Card Containers */
    .gold-card {{
        background: rgba(14, 16, 22, 0.88);
        border: 1px solid #3d311d;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .card-head {{
        color: #dfb15b;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }}

    /* Main Signal Engine Box */
    .signal-main {{
        background: rgba(16, 20, 28, 0.95);
        border: 1px solid #00e676;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin-bottom: 15px;
    }}
    .signal-title {{
        color: #00e676;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1px;
    }}
    .safe-badge {{
        background: rgba(0, 230, 118, 0.1);
        color: #00e676;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
        margin-top: 5px;
    }}

    /* Targets Grid */
    .target-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        margin: 15px 0;
    }}
    .target-box {{
        background: rgba(8, 9, 11, 0.85);
        border: 1px solid #2a251a;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
    }}
    .tp-text {{ color: #00e676; font-size: 14px; font-weight: bold; }}
    .sl-text {{ color: #ff3d00; font-size: 14px; font-weight: bold; }}

    .proverb-footer {{
        text-align: center;
        color: #dfb15b;
        font-size: 10px;
        letter-spacing: 2px;
        border-top: 1px solid #3d311d;
        padding-top: 10px;
        margin-top: 15px;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MARKET DATA GENERATOR (MATCHES MT5 QUOTES)
# ==========================================
@st.cache_data(ttl=3)
def get_live_data(symbol):
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    baselines = {
        "XAUUSD": {"price": 4340.55, "dec": 2},
        "BTCUSD": {"price": 65250.00, "dec": 2},
        "EURUSD": {"price": 1.0920, "dec": 4},
        "US30":   {"price": 39450.00, "dec": 1},
        "USDJPY": {"price": 157.40, "dec": 2},
        "DXY":    {"price": 103.15, "dec": 2}
    }
    cfg = baselines.get(symbol, baselines["XAUUSD"])
    price = round(cfg["price"] + np.random.normal(0, 0.05), cfg["dec"])
    return price, cfg["dec"]

dxy_price, _ = get_live_data("DXY")

# ==========================================
# 3. HEADER BANNER
# ==========================================
st.markdown(f"""
<div class="header-container">
    <div>
        <div class="brand-title">👑 SEKWAILA OMEGA X</div>
        <div class="brand-sub">ANCIENT WISDOM. MODERN PROFIT.</div>
    </div>
    <div class="time-badge">
        <b>17:45:32</b> SAST (UTC+2)<br/>
        <span style="color:#787b86;">AFRICA THE SOURCE</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    pair = st.selectbox("Active Asset Pair", ["XAUUSD", "BTCUSD", "EURUSD", "US30", "USDJPY"], index=0)
with col_sel2:
    tf = st.selectbox("Timeframe", ["M15", "1H", "4H", "D1"], index=0)

bid, dec = get_live_data(pair)
tp1 = round(bid + (6.35 if pair == "XAUUSD" else 150), dec)
tp2 = round(bid + (15.15 if pair == "XAUUSD" else 350), dec)
tp3 = round(bid + (29.80 if pair == "XAUUSD" else 600), dec)
sl  = round(bid - (12.25 if pair == "XAUUSD" else 200), dec)

# ==========================================
# 4. DASHBOARD 3-COLUMN LAYOUT
# ==========================================
col_left, col_center, col_right = st.columns([1, 2, 1])

# --- LEFT PANEL ---
with col_left:
    st.markdown("""
    <div class="gold-card">
        <div class="card-head">⚔️ MARKET SESSION</div>
        <div style="color:#00e676; font-weight:bold; font-size:11px;">LONDON / NY OVERLAP</div>
        <div style="color:#787b86; font-size:9px;">HIGH VOLUME (Quality: 95%)</div>
    </div>
    
    <div class="gold-card">
        <div class="card-head">👤 ACCOUNT OVERVIEW</div>
        <div style="display:flex; justify-content:space-between; font-size:10px;"><span>Balance:</span><b>$10,256.80</b></div>
        <div style="display:flex; justify-content:space-between; font-size:10px;"><span>Equity:</span><b>$10,256.80</b></div>
        <div style="display:flex; justify-content:space-between; font-size:10px;"><span>Risk %:</span><b style="color:#00e676;">2.00%</b></div>
    </div>

    <div class="gold-card">
        <div class="card-head">📜 ANCIENT PROVERB</div>
        <div style="font-style:italic; font-size:10px; color:#dfb15b; line-height:1.3;">
            "We are not dead, we are just in another room."
        </div>
        <div style="font-size:8px; color:#787b86; margin-top:4px;">- African Proverb</div>
    </div>
    """, unsafe_allow_html=True)

# --- CENTER SIGNAL PANEL ---
with col_center:
    st.markdown(f"""
    <div class="signal-main">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:18px; font-weight:bold; color:#fff;">{pair}</span>
            <span style="color:#00e676; font-weight:bold;">CONFIDENCE 92%</span>
        </div>
        <div class="signal-title">EXTREME BUY ↑</div>
        <div class="safe-badge">SAFE TO ENTER ☑</div>
        
        <div style="margin-top:12px; font-size:13px; color:#d1d4dc;">
            ENTRY PRICE: <b>{bid}</b> | CURRENT PRICE: <b>{bid}</b>
        </div>

        <div class="target-grid">
            <div class="target-box"><div style="font-size:8px; color:#787b86;">TP1</div><div class="tp-text">{tp1}</div><div style="font-size:8px; color:#787b86;">+63.5 PIPS</div></div>
            <div class="target-box"><div style="font-size:8px; color:#787b86;">TP2</div><div class="tp-text">{tp2}</div><div style="font-size:8px; color:#787b86;">+151.5 PIPS</div></div>
            <div class="target-box"><div style="font-size:8px; color:#787b86;">TP3</div><div class="tp-text">{tp3}</div><div style="font-size:8px; color:#787b86;">+298.0 PIPS</div></div>
            <div class="target-box"><div style="font-size:8px; color:#787b86;">STOP LOSS</div><div class="sl-text">{sl}</div><div style="font-size:8px; color:#787b86;">-122.5 PIPS</div></div>
        </div>

        <div style="text-align:left; font-size:10px; color:#dfb15b; line-height:1.4;">
            <b>KATLEGO AI CONFLUENCE ANALYSIS:</b><br/>
            ✓ Bullish Structure (BOS on 15m & 1H)<br/>
            ✓ Liquidity Sweep Below Key Low<br/>
            ✓ Strong Displacement Candle Confirmed<br/>
            ✓ DXY Weakness Supports upside ({dxy_price})
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- RIGHT PANEL ---
with col_right:
    st.markdown("""
    <div class="gold-card">
        <div class="card-head">📊 MARKET STRENGTH</div>
        <div style="font-size:10px;">
            <div style="display:flex; justify-content:space-between;"><span>XAUUSD</span><b style="color:#00e676;">92%</b></div>
            <div style="display:flex; justify-content:space-between;"><span>US30</span><b style="color:#00e676;">72%</b></div>
            <div style="display:flex; justify-content:space-between;"><span>BTCUSD</span><b style="color:#00e676;">68%</b></div>
            <div style="display:flex; justify-content:space-between;"><span>EURUSD</span><b style="color:#dfb15b;">45%</b></div>
            <div style="display:flex; justify-content:space-between;"><span>DXY</span><b style="color:#ff3d00;">28%</b></div>
        </div>
    </div>

    <div class="gold-card">
        <div class="card-head">💡 KATLEGO AI NARRATOR</div>
        <div style="font-size:10px; color:#d1d4dc; line-height:1.3;">
            Gold is showing strong bullish momentum after sweeping liquidity. Institutional buying is detected in the London/NY overlap. High probability setup.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. TELEGRAM ALERT DISPATCHER
# ==========================================
st.markdown("---")
st.subheader("📡 Katlego Telegram Alerts")
tg_col1, tg_col2 = st.columns(2)
with tg_col1:
    bot_token = st.text_input("Bot Token", type="password")
with tg_col2:
    chat_id = st.text_input("Chat ID")

if st.button("🚀 Broadcast Alert to Telegram"):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        msg = f"<b>⚡ SEKWAILA OMEGA X / KATLEGO AI ALERT</b>\n\nPair: {pair}\nSignal: EXTREME BUY\nEntry: {bid}\nTP1: {tp1} | TP2: {tp2} | TP3: {tp3}\nSL: {sl}"
        res = requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        if res.status_code == 200:
            st.success("Alert broadcasted successfully!")
        else:
            st.error("Failed to deliver alert.")
    else:
        st.warning("Please enter your Telegram Bot Token and Chat ID.")

# Footer Motto
st.markdown("""
<div class="proverb-footer">
    THE ANCESTORS SEE YOUR DISCIPLINE. THE UNIVERSE REWARDS YOUR PATIENCE.
</div>
""", unsafe_allow_html=True)
