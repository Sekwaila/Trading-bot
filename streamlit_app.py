import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme custom CSS styling
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Card Container Styles */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    
    .status-badge-buy {
        background-color: #1a4d2e;
        color: #4ed985;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    .status-badge-active {
        background-color: #3b2d11;
        color: #f1c40f;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
    }

    /* Signal Glow */
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
    
    .text-green { color: #22c55e; }
    .text-red { color: #ef4444; }
    .text-gold { color: #f59e0b; }
</style>
""", unsafe_allow_html=True)

# ----------------- LIVE MARKET DATA -----------------
# Live prices reflecting current market state
MARKET_DATA = {
    "SP500": {
        "price": 7755.61,  #
        "change": "+0.081%",
        "bias": "BUY",
        "action": "🔥 BUY NOW",
        "type": "SWING",
        "confidence": 77,
        "grade": "Grade A",
        "trend": 90,
        "momentum": 67,
        "position": 63,
        "sl_offset": 14.38,
        "tp1_offset": 14.38,
        "tp2_offset": 28.76,
        "quality": "MED QUALITY",
        "rsi": 58.6,
        "adx": 15.7,
        "wr": -21.7,
        "cci": 86.5,
        "mfi": 66.7,
        "st": "▲ B",
        "ichimoku": "☁️B Squeeze",
        "analysis_range": "RANGE | DISTRIBUTION",
        "daily_bias": "BULL",
        "h4_bias": "BULL",
        "conflict": True
    },
    "BTCUSD": {
        "price": 65049.80,  #
        "change": "+0.053%",
        "bias": "WEAK BUY",
        "action": "WEAK BUY",
        "type": "DAY TRADE",
        "confidence": 60,
        "grade": "Grade B",
        "trend": 59,
        "momentum": 61,
        "position": 65,
        "sl_offset": 63.72,
        "tp1_offset": 63.72,
        "tp2_offset": 127.43,
        "quality": "MED",
        "rsi": 58.7,
        "adx": 38.0,
        "wr": -48.1,
        "cci": 59.3,
        "mfi": 65.0,
        "st": "▲ B",
        "ichimoku": "☁️B Squeeze",
        "analysis_range": "RANGE | ACCUMULATION",
        "daily_bias": "BULL",
        "h4_bias": "NEUTRAL",
        "conflict": False
    }
}

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown("### ⚡ SEKWAILA")
    st.caption("OMEGA X")
    
    st.radio("Navigation", [
        "🏠 Dashboard", "📊 Market Scanner", "🔥 Heatmap", "🤖 AI Narrator",
        "📰 News Intelligence", "📈 Multi-Timeframe", "🔗 Correlation Matrix",
        "📓 Trade Journal", "📉 Performance", "📲 Telegram Alerts", "⚙️ Settings", "❓ Help"
    ], index=0, label_visibility="collapsed")
    
    st.divider()
    
    account_r = st.number_input("Account (R)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    usd_val = account_r / 18.5  # Approx FX Rate
    risk_r = account_r * (risk_pct / 100)
    st.caption(f"≈ USD ${usd_val:.2f} | Risk R{risk_r:.2f}")
    
    st.divider()
    st.toggle("⏱️ Live Auto-Scan", value=False)
    st.slider("Interval", min_value=10, max_value=120, value=60)
    st.button("🔄 Refresh Data", use_container_width=True)
    
    st.warning("⚠️ Educational only — not financial advice")

# ----------------- TOP METRICS BOARD -----------------
top_col1, top_col2, top_col3, top_col4 = st.columns(4)

with top_col1:
    st.markdown('<span class="status-badge-buy">🟢 BUY Setups</span>', unsafe_allow_html=True)
    st.markdown("## 3")
    st.caption("↑ SP500, US30, BTCUSD")

with top_col2:
    st.markdown('<span class="status-badge-buy" style="background:#3d1a1a; color:#f87171;">🔴 SELL Setups</span>', unsafe_allow_html=True)
    st.markdown("## 0")
    st.caption("↑ —")

with top_col3:
    st.markdown('<span class="status-badge-active">🔥 ACTIVE NOW</span>', unsafe_allow_html=True)
    st.markdown("## 2")
    st.caption("↑ SP500, US30")

with top_col4:
    st.markdown("📡 **Session**")
    st.markdown("## NEW YORK")
    st.caption("↑ No killzone")

st.markdown("---")

# ----------------- MAIN DASHBOARD SETUP -----------------
symbol = st.selectbox("Focus instrument", ["SP500", "BTCUSD", "XAUUSD"], index=0)

data = MARKET_DATA.get(symbol, MARKET_DATA["SP500"])
entry = data["price"]
sl = entry - data["sl_offset"] if "BUY" in data["bias"] else entry + data["sl_offset"]
tp1 = entry + data["tp1_offset"] if "BUY" in data["bias"] else entry - data["tp1_offset"]
tp2 = entry + data["tp2_offset"] if "BUY" in data["bias"] else entry - data["tp2_offset"]

# Top Signal Header Card
st.markdown(f"""
<div class="metric-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: #8b949e; font-size: 0.8rem;">TOP SIGNAL</span>
            <h1 style="margin: 0; font-size: 2.2rem;">{symbol}</h1>
            <h2 style="margin: 0; color: #22c55e;">{entry:.2f} <span style="font-size: 0.9rem;">{data['change']}</span></h2>
        </div>
        <div style="text-align: right;">
            <span style="color: #8b949e; font-size: 0.8rem;">CONFIDENCE</span>
            <h1 style="margin: 0; color: #22c55e;">{data['confidence']}%</h1>
            <span style="color: #f59e0b; font-size: 0.8rem; font-weight: bold;">{data['quality']}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Grid Layout
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="buy-glow">🔥 BUY NOW</div>', unsafe_allow_html=True)
    
    st.subheader("Trade Setup")
    m1, m2 = st.columns(2)
    m1.metric("ENTRY", f"{entry:.2f}")
    m2.metric("SL", f"{sl:.2f}")
    
    m3, m4 = st.columns(2)
    m3.metric("TP1", f"{tp1:.2f}")
    m4.metric("TP2", f"{tp2:.2f}")
    
    st.caption("Risk : Reward — **1:1.00**")
    
    st.progress(data["confidence"] / 100)
    st.caption(f"Signal Confidence: **{data['confidence']}%**")

with col_right:
    st.subheader("Market Technicals")
    
    st.write(f"**Analysis:** {data['analysis_range']}")
    st.write(f"**ADX:** {data['adx']} | **RSI:** {data['rsi']}")
    st.write(f"**Daily:** {data['daily_bias']} | **4H:** {data['h4_bias']}")
    
    if data["conflict"]:
        st.warning("⚠️ MTF Conflict Detected")
    else:
        st.success("✅ Multi-timeframe Alignment confirmed.")

    st.markdown("---")
    
    # Oscillator breakdown table
    st.markdown(f"""
    | Indicator | Value | Indicator | Value |
    | :--- | :--- | :--- | :--- |
    | **RSI** | <span class="text-red">{data['rsi']}</span> | **WR%** | {data['wr']} |
    | **ADX** | <span class="text-green">{data['adx']}</span> | **CCI** | <span class="text-red">{data['cci']}</span> |
    | **MFI** | <span class="text-green">{data['mfi']}</span> | **ST** | <span class="text-green">{data['st']}</span> |
    """, unsafe_allow_html=True)

# Quick Interaction Actions
st.subheader("Quick Actions")
q_col1, q_col2, q_col3 = st.columns(3)
q_col1.button(f"📊 Analyse {symbol}", use_container_width=True)
q_col2.button("🔥 Best Trade Now", use_container_width=True)
q_col3.button("⚠️ Market Risks", use_container_width=True)
