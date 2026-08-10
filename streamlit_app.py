import streamlit as st
import requests

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- EXACT SEKWAILA DARK STYLING -----------------
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    
    /* Card Container */
    .sekwaila-card {
        background-color: #121721;
        border: 1px solid #1e2638;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* Glow Badges */
    .buy-badge {
        background-color: #064e3b;
        color: #34d399;
        font-weight: bold;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #10b981;
        display: inline-block;
    }
    
    .buy-now-btn {
        background-color: #059669;
        color: #ffffff;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 1.1rem;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
    }
    
    .med-quality {
        background-color: #312e81;
        color: #f59e0b;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #f59e0b;
        font-size: 0.8rem;
    }
    
    /* Progress / Metric Bars */
    .bar-bg {
        background-color: #1f293d;
        border-radius: 10px;
        height: 10px;
        width: 100%;
        margin-top: 4px;
        margin-bottom: 12px;
    }
    
    .bar-fill-green {
        background-color: #10b981;
        height: 100%;
        border-radius: 10px;
    }
    
    .bar-fill-orange {
        background-color: #f97316;
        height: 100%;
        border-radius: 10px;
    }

    /* Grid Table Styles */
    .grid-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #1a2233;
        font-size: 0.95rem;
    }
    .val-green { color: #10b981; font-weight: bold; }
    .val-red { color: #ef4444; font-weight: bold; }
    .val-gold { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ----------------- TWELVE DATA API INTEGRATION -----------------
TWELVE_DATA_SYMBOLS = {
    "SP500": "SPX",
    "US30": "DJI",
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "BTCUSD": "BTC/USD",
    "DXY": "DXY"
}

@st.cache_data(ttl=5)
def get_twelve_data(symbol_key, api_key):
    td_symbol = TWELVE_DATA_SYMBOLS.get(symbol_key, "XAU/USD")
    
    if not api_key:
        # Replit fallback reference values
        defaults = {
            "SP500": (7755.61, 0.081),
            "US30": (54029.50, -0.002),
            "XAUUSD": (4386.40, -0.120),
            "EURUSD": (1.15527, -0.050),
            "BTCUSD": (64963.04, -0.048),
            "DXY": (99.73, 0.150)
        }
        return defaults.get(symbol_key, (100.0, 0.0))

    url = f"https://api.twelvedata.com/quote?symbol={td_symbol}&apikey={api_key}"
    try:
        res = requests.get(url, timeout=5).json()
        if "close" in res:
            price = float(res["close"])
            change = float(res.get("percent_change", 0.0))
            return price, change
    except Exception:
        pass
        
    defaults = {
        "SP500": (7755.61, 0.081), "US30": (54029.50, -0.002),
        "XAUUSD": (4386.40, -0.120), "EURUSD": (1.15527, -0.050),
        "BTCUSD": (64963.04, -0.048), "DXY": (99.73, 0.150)
    }
    return defaults.get(symbol_key, (100.0, 0.0))

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("## ⚡ SEKWAILA")
    st.caption("OMEGA X")
    st.divider()
    
    twelve_key = st.text_input("Twelve Data API Key", type="password", help="Enter key to fetch real live broker prices")
    
    st.divider()
    nav_option = st.radio(
        "Navigation",
        [
            "🏠 Dashboard", "📊 Market Scanner", "🔥 Heatmap", 
            "🤖 AI Narrator", "📰 News Intelligence", "📈 Multi-Timeframe", 
            "🔗 Correlation Matrix", "📓 Trade Journal", "📉 Performance", 
            "📲 Telegram Alerts", "⚙️ Settings", "❓ Help"
        ],
        label_visibility="collapsed"
    )
    
    st.divider()
    account_r = st.number_input("Account (R)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

# ----------------- MAIN DASHBOARD VIEW -----------------
if "🏠 Dashboard" in nav_option:

    # 1. TOP METRICS PANEL
    dxy_p, _ = get_twelve_data("DXY", twelve_key)
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown("🟢 **BUY Setups**\n# 2\n`↑ SP500, US30`")
    with c2:
        st.markdown("🔴 **SELL Setups**\n# 2\n`↑ XAUUSD, EURUSD`")
    with c3:
        st.markdown("🔥 **ACTIVE NOW**\n# 2\n`↑ SP500, US30`")
    with c4:
        st.markdown("📡 **Session**\n# OFF HOURS\n`↑ No killzone`")
    with c5:
        st.markdown(f"💲 **DXY**\n# {dxy_p:.2f}\n`↑ BULL ▲`")

    st.divider()

    # 2. TOP SIGNAL CARD (MATCHING REPLIT SP500 CARD)
    sp_price, sp_change = get_twelve_data("SP500", twelve_key)
    
    st.markdown(f"""
    <div class="sekwaila-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="color: #6b7280; font-size: 0.8rem; letter-spacing: 1px;">TOP SIGNAL</span>
                <h1 style="margin: 0; font-size: 2.5rem; font-weight: 900;">SP500</h1>
                <h2 style="margin: 0; color: #10b981;">{sp_price:.2f} <span style="font-size: 1rem; color: #10b981;">+{sp_change:.3f}%</span></h2>
            </div>
            <div style="text-align: right;">
                <span style="color: #6b7280; font-size: 0.8rem;">CONFIDENCE</span>
                <h1 style="margin: 0; color: #10b981; font-size: 2.5rem;">77%</h1>
                <span class="med-quality">MED QUALITY</span>
            </div>
        </div>
        <br>
        <div style="display: flex; gap: 10px; align-items: center;">
            <span class="buy-badge">BUY</span>
        </div>
        <div class="buy-now-btn">🔥 BUY NOW</div>
        <br>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #9ca3af;">
            <div><b>TRADE SETUP</b><br>
                ENTRY: <span class="val-green">{sp_price:.2f}</span><br>
                TP1: <span class="val-green">{sp_price + 14.38:.2f}</span><br>
                TP2: <span class="val-green">{sp_price + 28.76:.2f}</span><br>
                SL: <span class="val-red">{sp_price - 14.38:.2f}</span><br>
                R:R: <span class="val-gold">1:1.00</span>
            </div>
            <div><b>ANALYSIS</b><br>
                📐 RANGE | DISTRIBUTION<br>
                📊 ADX 15.7 | RSI 58.6<br>
                🕰️ Daily: BULL | 4H: BULL<br>
                ⚠️ MTF Conflict
            </div>
        </div>
        <br>
        <div style="font-size: 0.8rem; color: #9ca3af;">Signal Confidence <span style="float: right; color: #10b981;">77%</span></div>
        <div class="bar-bg"><div class="bar-fill-green" style="width: 77%;"></div></div>
    </div>
    """, unsafe_allow_html=True)

    # 3. MARKET STRENGTH LIST
    st.markdown("### 📊 MARKET STRENGTH")
    
    us30_p, _ = get_twelve_data("US30", twelve_key)
    xau_p, _ = get_twelve_data("XAUUSD", twelve_key)
    eur_p, _ = get_twelve_data("EURUSD", twelve_key)
    btc_p, _ = get_twelve_data("BTCUSD", twelve_key)

    pairs_data = [
        ("SP500", f"{sp_price:.2f}", "BUY", "77%", 77, "green"),
        ("US30", f"{us30_p:.2f}", "BUY", "75%", 75, "green"),
        ("XAUUSD", f"{xau_p:.2f}", "WEAK SELL", "36%", 36, "orange"),
        ("EURUSD", f"{eur_p:.5f}", "WEAK SELL", "42%", 42, "orange"),
        ("BTCUSD", f"{btc_p:.2f}", "NEUTRAL", "45%", 45, "gray"),
        ("DXY", f"{dxy_p:.2f}", "BULL", "69%", 69, "green"),
    ]

    for sym, pr, act, conf_str, pct, color in pairs_data:
        c_a, c_b = st.columns([3, 1])
        with c_a:
            st.markdown(f"**{sym}**")
        with c_b:
            st.markdown(f"`{pr}` **{act}** `{conf_str}`")
        
        fill_class = "bar-fill-green" if color == "green" else "bar-fill-orange"
        st.markdown(f'<div class="bar-bg"><div class="{fill_class}" style="width: {pct}%;"></div></div>', unsafe_allow_html=True)

    # 4. DETAILED OSCILLATOR & INDICATOR BREAKDOWN (US30 / BTC DETAIL VIEW)
    st.divider()
    st.markdown("### 🎯 INSTRUMENT TECHNICAL GAUGES")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown(f"""
        <div class="sekwaila-card">
            <h3>🔥 US30 — BUY</h3>
            <h2>{us30_p:.2f} <span style="font-size: 0.9rem; color: #ef4444;">-0.002%</span></h2>
            <div class="bar-bg"><div class="bar-fill-green" style="width: 75%;"></div></div>
            <small>Confidence 75% · Grade A</small>
            <br><br>
            <div class="grid-row"><span>Trend</span><span class="val-green">86</span></div>
            <div class="grid-row"><span>Momentum</span><span class="val-green">62</span></div>
            <div class="grid-row"><span>Position</span><span class="val-green">73</span></div>
            <br>
            <div class="grid-row"><span>RSI</span><span><b>53.9</b></span><span>WR%</span><span><b>-26.2</b></span></div>
            <div class="grid-row"><span>ADX</span><span class="val-green">19.9</span><span>CCI</span><span class="val-red">108.4</span></div>
            <div class="grid-row"><span>MFI</span><span><b>45.1</b></span><span>ST</span><span class="val-green">▲ B</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_right:
        st.markdown(f"""
        <div class="sekwaila-card">
            <h3>⚡ BTCUSD — NEUTRAL</h3>
            <h2>{btc_p:.2f} <span style="font-size: 0.9rem; color: #ef4444;">-0.048%</span></h2>
            <div class="bar-bg"><div class="bar-fill-orange" style="width: 45%;"></div></div>
            <small>Confidence 45% · Grade C</small>
            <br><br>
            <div class="grid-row"><span>Trend</span><span class="val-gold">50</span></div>
            <div class="grid-row"><span>Momentum</span><span class="val-red">35</span></div>
            <div class="grid-row"><span>Position</span><span class="val-gold">53</span></div>
            <br>
            <div class="grid-row"><span>RSI</span><span class="val-green">43.6</span><span>WR%</span><span><b>-77.0</b></span></div>
            <div class="grid-row"><span>ADX</span><span class="val-red">14.6</span><span>CCI</span><span><b>-62.8</b></span></div>
            <div class="grid-row"><span>MFI</span><span class="val-red">44.5</span><span>ST</span><span class="val-red">▼ S</span></div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.title(nav_option)
    st.info(f"The module **{nav_option}** is active.")
