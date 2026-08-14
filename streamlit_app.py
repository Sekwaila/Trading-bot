"""
SEKWAILA OMEGA X — Pro Mobile Terminal
Designed specifically for high-frequency dark mode UI matching Replit / Rocket layout.
"""

from typing import Any, Dict, List
import pandas as pd
import streamlit as st
from signals.signal_engine import analyze_market, get_market_overview
from twelve_data_adapter import TwelveDataClient

# --------------------------------------------------------------------
# 1. Page Config
# --------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------
# 2. Custom CSS Injection (Matching Screenshots Exactly)
# --------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Dark Terminal Theme Background */
    .stApp {
        background-color: #0d0f14 !important;
        color: #e0e6ed !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { visibility: hidden; }

    /* Main Container Cards */
    .dark-card {
        background: #131722;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
    }

    /* Direction Badges */
    .btn-strong-sell {
        background: rgba(255, 23, 68, 0.12);
        color: #ff1744;
        border: 1px solid #ff1744;
        border-radius: 20px;
        padding: 6px 16px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        text-align: center;
    }
    .btn-strong-buy {
        background: rgba(0, 230, 118, 0.12);
        color: #00e676;
        border: 1px solid #00e676;
        border-radius: 20px;
        padding: 6px 16px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        text-align: center;
    }

    /* Action Trigger Buttons */
    .btn-action-sell {
        background: linear-gradient(180deg, #d50000 0%, #8e0000 100%);
        color: #ffffff;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0 0 12px rgba(255, 23, 68, 0.4);
    }
    .btn-action-buy {
        background: linear-gradient(180deg, #00c853 0%, #00701a 100%);
        color: #ffffff;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.4);
    }

    /* Custom Progress Bars */
    .progress-bg {
        background-color: #1e222d;
        border-radius: 6px;
        height: 8px;
        width: 100%;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    .progress-fill-green {
        background-color: #00e676;
        height: 100%;
        border-radius: 6px;
        box-shadow: 0 0 8px #00e676;
    }
    .progress-fill-red {
        background-color: #ff1744;
        height: 100%;
        border-radius: 6px;
        box-shadow: 0 0 8px #ff1744;
    }

    /* Typography */
    .sub-label {
        color: #787b86;
        font-size: 0.72rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .text-green { color: #00e676 !important; }
    .text-red { color: #ff1744 !important; }
    .text-yellow { color: #ffc107 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------
# 3. Helper Functions for Signal Classification & Sorting
# --------------------------------------------------------------------
WATCHLIST = ["SP500", "US30", "BTCUSD", "XAUUSD", "EURUSD", "DXY"]


def classify_signal(confidence: int, is_bullish: bool) -> Dict[str, Any]:
    """Categorizes market signals based on confidence percentage."""
    if is_bullish:
        if confidence >= 80:
            return {
                "label": "STRONG BUY",
                "color": "#00e676",
                "rank": 7,
                "is_buy": True,
            }
        elif confidence >= 65:
            return {"label": "BUY", "color": "#00e676", "rank": 6, "is_buy": True}
        else:
            return {
                "label": "WEAK BUY",
                "color": "#81c784",
                "rank": 5,
                "is_buy": True,
            }
    else:
        if confidence <= 20:
            return {
                "label": "STRONG SELL",
                "color": "#ff1744",
                "rank": 1,
                "is_buy": False,
            }
        elif confidence <= 35:
            return {
                "label": "SELL",
                "color": "#ff1744",
                "rank": 2,
                "is_buy": False,
            }
        elif confidence < 50:
            return {
                "label": "WEAK SELL",
                "color": "#e57373",
                "rank": 3,
                "is_buy": False,
            }
        else:
            return {
                "label": "NEUTRAL",
                "color": "#787b86",
                "rank": 4,
                "is_buy": True,
            }


# Mock/Adapter scanner data generator (Order from EXTREME BUY to EXTREME SELL)
def fetch_sorted_market_signals() -> List[Dict[str, Any]]:
    raw_data = [
        {
            "symbol": "SP500",
            "price": "7771.55",
            "confidence": 86,
            "is_bullish": True,
        },
        {"symbol": "US30", "price": "53883.29", "confidence": 78, "is_bullish": True},
        {
            "symbol": "XAUUSD",
            "price": "4450.60",
            "confidence": 59,
            "is_bullish": True,
        },
        {
            "symbol": "EURUSD",
            "price": "1.15393",
            "confidence": 51,
            "is_bullish": True,
        },
        {
            "symbol": "BTCUSD",
            "price": "63552.43",
            "confidence": 33,
            "is_bullish": False,
        },
        {"symbol": "DXY", "price": "99.84", "confidence": 18, "is_bullish": False},
    ]

    for item in raw_data:
        sig = classify_signal(item["confidence"], item["is_bullish"])
        item.update(sig)

    # Sort strictly from Rank 7 (Strong Buy) down to Rank 1 (Strong Sell)
    return sorted(raw_data, key=lambda x: x["rank"], reverse=True)


# --------------------------------------------------------------------
# 4. Sidebar Controls
# --------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **SEKWAILA**")
    st.caption("OMEGA X ENGINE")
    st.markdown("---")

    api_key = st.secrets.get("TWELVE_DATA_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Twelve Data API Key", type="password")

    symbol = st.selectbox("Active Ticker", WATCHLIST, index=2)
    account_bal = st.number_input("Account (R)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", 0.5, 5.0, 1.0, 0.25)
    run_btn = st.button("🚀 REFRESH SIGNALS", type="primary", use_container_width=True)

client = TwelveDataClient(api_key=api_key)

# --------------------------------------------------------------------
# 5. Top Overview Stats (Buy/Sell Counter & Session)
# --------------------------------------------------------------------
market_signals = fetch_sorted_market_signals()

buy_count = sum(1 for x in market_signals if x["is_buy"] and x["rank"] >= 5)
sell_count = sum(1 for x in market_signals if not x["is_buy"] and x["rank"] <= 3)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class="dark-card">
            <span class="sub-label">🟢 BUY Setups</span>
            <h2 style="margin:2px 0;">{buy_count}</h2>
            <span style="background:rgba(0,230,118,0.15); color:#00e676; padding:2px 8px; border-radius:12px; font-size:0.75rem;">↑ SP500, US30</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="dark-card">
            <span class="sub-label">🔴 SELL Setups</span>
            <h2 style="margin:2px 0;">{sell_count}</h2>
            <span style="background:rgba(255,23,68,0.15); color:#ff1744; padding:2px 8px; border-radius:12px; font-size:0.75rem;">↑ BTCUSD, DXY</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="dark-card">
            <span class="sub-label">🔥 ACTIVE NOW</span>
            <h2 style="margin:2px 0;">2</h2>
            <span style="background:rgba(0,230,118,0.15); color:#00e676; padding:2px 8px; border-radius:12px; font-size:0.75rem;">↑ SP500, US30</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="dark-card">
            <span class="sub-label">📡 Session</span>
            <h2 style="margin:2px 0; font-size:1.2rem;">OFF HOURS</h2>
            <span style="background:rgba(255,255,255,0.08); color:#787b86; padding:2px 8px; border-radius:12px; font-size:0.75rem;">↑ No killzone</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# --------------------------------------------------------------------
# 6. Main Top Signal Focus Card (Matches Screenshot #2)
# --------------------------------------------------------------------
top_signal = market_signals[-1] if symbol == "BTCUSD" else market_signals[0]

st.markdown(
    f"""
    <div class="dark-card" style="border:1px solid rgba(255,23,68,0.3);">
        <span class="sub-label">TOP SIGNAL</span>
        <h1 style="margin:0; font-size:2.4rem;">{top_signal['symbol']}</h1>
        <h2 class="text-red" style="margin:0;">{top_signal['price']} <span style="font-size:0.9rem; color:#787b86;">-0.016%</span></h2>
        
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:15px;">
            <div>
                <span class="sub-label">DIRECTION</span><br>
                <div class="btn-strong-sell">{top_signal['label']}</div>
            </div>
            <div>
                <span class="sub-label">CONFIDENCE</span>
                <h2 class="text-red" style="margin:0;">{top_signal['confidence']}%</h2>
            </div>
        </div>

        <div style="display:flex; gap:10px; margin-top:12px;">
            <div class="btn-action-sell" style="flex:1;">🔥 SELL NOW</div>
            <div style="background:rgba(0,230,118,0.1); border:1px solid #00e676; color:#00e676; border-radius:8px; padding:10px; font-weight:bold; font-size:0.8rem; text-align:center;">HIGH QUALITY</div>
        </div>

        <div style="margin-top:20px; display:flex; justify-content:space-between; font-size:0.85rem;">
            <div>
                <span class="sub-label">TRADE SETUP</span><br>
                <b>ENTRY:</b> {top_signal['price']}<br>
                <span class="text-green"><b>TP1:</b> 63420.61</span><br>
                <span class="text-green"><b>TP2:</b> 63289.88</span><br>
                <span class="text-red"><b>SL:</b> 63682.07</span><br>
                <span class="text-yellow"><b>R:R:</b> 1:1.00</span>
            </div>
            <div>
                <span class="sub-label">ANALYSIS</span><br>
                📐 RANGE | MARKDOWN<br>
                📊 ADX 20.1 | RSI 43.0<br>
                🕰️ Daily: BEAR | 4H: BEAR<br>
                ⚠️ MTF Conflict
            </div>
        </div>

        <div class="progress-bg" style="margin-top:15px;">
            <div class="progress-fill-red" style="width:{top_signal['confidence']}%;"></div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------
# 7. Market Strength Section (Ordered Strong Buy -> Strong Sell)
# --------------------------------------------------------------------
st.markdown("### 📊 **MARKET STRENGTH**")

for item in market_signals:
    fill_class = "progress-fill-green" if item["is_buy"] else "progress-fill-red"
    text_class = "text-green" if item["is_buy"] else "text-red"

    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; font-size:1rem;">{item['symbol']}</span>
                <div>
                    <span style="color:#787b86; margin-right:10px;">{item['price']}</span>
                    <span class="{text_class}" style="font-weight:bold;">{item['label']}</span>
                    <span class="{text_class}" style="font-weight:bold; margin-left:8px;">{item['confidence']}%</span>
                </div>
            </div>
            <div class="progress-bg">
                <div class="{fill_class}" style="width:{item['confidence']}%;"></div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
