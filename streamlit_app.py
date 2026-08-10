import streamlit as st
import requests

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Sekwaila Omega X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- STYLING -----------------
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    .sekwaila-card {
        background-color: #121721;
        border: 1px solid #1e2638;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .buy-badge {
        background-color: #064e3b; color: #34d399;
        font-weight: bold; padding: 6px 14px;
        border-radius: 20px; border: 1px solid #10b981;
        display: inline-block;
    }
    .buy-now-btn {
        background-color: #059669; color: #ffffff;
        font-weight: bold; text-align: center;
        padding: 10px; border-radius: 8px;
        margin-top: 10px; font-size: 1.1rem;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
    }
    .med-quality {
        background-color: #312e81; color: #f59e0b;
        font-weight: bold; padding: 4px 10px;
        border-radius: 6px; border: 1px solid #f59e0b;
        font-size: 0.8rem;
    }
    .bar-bg {
        background-color: #1f293d; border-radius: 10px;
        height: 10px; width: 100%; margin-top: 4px; margin-bottom: 12px;
    }
    .bar-fill-green { background-color: #10b981; height: 100%; border-radius: 10px; }
    .bar-fill-orange { background-color: #f97316; height: 100%; border-radius: 10px; }
    .grid-row {
        display: flex; justify-content: space-between;
        padding: 6px 0; border-bottom: 1px solid #1a2233; font-size: 0.95rem;
    }
    .val-green { color: #10b981; font-weight: bold; }
    .val-red { color: #ef4444; font-weight: bold; }
    .val-gold { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ----------------- TWELVE DATA SYMBOL MAPPING -----------------
# SPY is used for SP500 on free endpoints if SPX is restricted
TWELVE_DATA_SYMBOLS = {
    "SP500": "SPY",
    "US30": "DJI",
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "BTCUSD": "BTC/USD",
    "DXY": "USD/EUR"  # Fallback proxy if DXY index requires paid plan
}

def get_twelve_data(symbol_key, api_key):
    td_symbol = TWELVE_DATA_SYMBOLS.get(symbol_key, "XAU/USD")
    
    if not api_key:
        return None, 0.0, "No API Key Provided"

    # Query Quote Endpoint
    url = f"https://api.twelvedata.com/quote?symbol={td_symbol}&apikey={api_key}"
    try:
        res = requests.get(url, timeout=5).json()
        
        if "close" in res and res["close"] is not None:
            price = float(res["close"])
            change = float(res.get("percent_change", 0.0))
            return price, change, "OK"
        elif "status" in res and res["status"] == "error":
            return None, 0.0, res.get("message", "API Error")
    except Exception as e:
        return None, 0.0, str(e)
        
    return None, 0.0, "Unknown Error"

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("## ⚡ SEKWAILA")
    st.caption("OMEGA X")
    st.divider()
    
    twelve_key = st.text_input("Twelve Data API Key", type="password", help="Enter key to fetch real broker prices")
    
    if twelve_key:
        st.success("API Key Active")
    else:
        st.warning("Enter API key for live market prices")
        
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

# ----------------- MAIN DASHBOARD VIEW -----------------
if "🏠 Dashboard" in nav_option:

    dxy_p, _, dxy_status = get_twelve_data("DXY", twelve_key)
    dxy_display = f"{dxy_p:.2f}" if dxy_p else "N/A"

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
        st.markdown(f"💲 **DXY Proxy**\n# {dxy_display}\n`↑ BULL ▲`")

    st.divider()

    # TOP SIGNAL CARD
    sp_price, sp_change, sp_status = get_twelve_data("SP500", twelve_key)
    
    if sp_price is None:
        st.error(f"SP500 Live Fetch Error: {sp_status}")
        sp_price = 0.00
        sp_change = 0.00

    st.markdown(f"""
    <div class="sekwaila-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="color: #6b7280; font-size: 0.8rem; letter-spacing: 1px;">TOP SIGNAL</span>
                <h1 style="margin: 0; font-size: 2.5rem; font-weight: 900;">SP500 (SPY)</h1>
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
                TP1: <span class="val-green">{sp_price * 1.002:.2f}</span><br>
                TP2: <span class="val-green">{sp_price * 1.004:.2f}</span><br>
                SL: <span class="val-red">{sp_price * 0.998:.2f}</span><br>
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

    # LIVE MARKET TABLE
    st.markdown("### 📊 LIVE MARKET PRICES")
    
    symbols = ["SP500", "US30", "XAUUSD", "EURUSD", "BTCUSD"]
    for sym in symbols:
        price, change, status = get_twelve_data(sym, twelve_key)
        
        c_a, c_b, c_c = st.columns([2, 2, 2])
        with c_a:
            st.markdown(f"**{sym}**")
        with c_b:
            if price:
                st.markdown(f"`{price:.4f}` ({change:+.2f}%)")
            else:
                st.markdown(f"❌ `{status}`")
        with c_c:
            st.markdown(f"Ticker used: `{TWELVE_DATA_SYMBOLS.get(sym)}`")
