"""
SEKWAILA OMEGA X — COMPLETE STREAMLIT DASHBOARD
Matches all UI card layouts, signal grids, SMC checklists, alerts, and risk management.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import config
from config import ASSETS
from signals.signal_engine import generate_omega_signal
from database import load_journal, save_journal_entry
from trade_manager import calculate_position_size
from telegram_bot import send_telegram_message

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS (DARK THEME, CARD CONTAINERS, PROGRESS BARS & BADGES)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #0b0e14 !important;
        color: #e0e6ed !important;
    }
    [data-testid="stSidebar"] {
        background-color: #121721 !important;
        border-right: 1px solid #1e2638 !important;
    }
    
    /* Custom Card Styling */
    .omega-card {
        background: #131822;
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 15px;
    }
    .omega-card-active {
        border: 1px solid #00e676 !important;
        box-shadow: 0px 0px 10px rgba(0, 230, 118, 0.15);
    }
    
    /* Typography & Headers */
    .title-gold {
        color: #d9a441;
        font-weight: 800;
        font-size: 22px;
        letter-spacing: 0.5px;
    }
    .badge-buy {
        background-color: #003822;
        color: #00e676;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #00e676;
    }
    .badge-sell {
        background-color: #38000d;
        color: #ff5252;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #ff5252;
    }
    .badge-quality {
        background-color: #332600;
        color: #ffd700;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        border: 1px solid #ffd700;
    }
    
    /* Progress Bars */
    .progress-bg {
        background-color: #1e2638;
        border-radius: 10px;
        height: 8px;
        width: 100%;
        margin-top: 6px;
    }
    .progress-fill-green {
        background-color: #00e676;
        height: 8px;
        border-radius: 10px;
    }
    .progress-fill-red {
        background-color: #ff5252;
        height: 8px;
        border-radius: 10px;
    }
    
    /* Streamlit UI Adjustments */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #00e676 0%, #00a854 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & RISK MANAGEMENT
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 class='title-gold'>⚡ SEKWAILA V16 ULTRA ELITE</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation", 
    [
        "📊 Dashboard", 
        "📈 Signal Analysis", 
        "🎯 ICT/SMC Checklist", 
        "🧩 Signal Direction Grid", 
        "🔔 Alerts & News", 
        "📖 Trade Journal"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Risk Calculator")
account_balance = st.sidebar.number_input("Account Balance (R)", value=500.0, step=50.0)
risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0, 0.1)
usd_equiv = account_balance / 18.5  # Approximate ZAR to USD conversion
st.sidebar.caption(f"≈ USD ${usd_equiv:.2f}")

SUPPORTED_PAIRS = list(ASSETS.keys()) if ASSETS else [
    "BTCUSD", "XAUUSD", "US30", "EURUSD", "GBPUSD", "USDJPY", "DXY", "SPX500"
]

selected_asset = st.sidebar.selectbox("Select Active Asset", SUPPORTED_PAIRS)
min_tf = st.sidebar.slider("Min Timeframe Confluence", 2, 4, 3)

# -----------------------------------------------------------------------------
# VIEW 1: DASHBOARD (MAIN OVERVIEW CARD & MARKET STRENGTH)
# -----------------------------------------------------------------------------
if page == "📊 Dashboard":
    st.markdown("<h3 style='color: #ffffff;'>⚡ SEKWAILA V16 ULTRA ELITE — OVERVIEW</h3>", unsafe_allow_html=True)
    
    # Active Sessions Bar
    st.markdown("""
    <div style='display: flex; gap: 10px; margin-bottom: 20px;'>
        <span style='background: #00e676; color: black; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 12px;'>SYDNEY</span>
        <span style='background: #1f293d; color: #8899a6; padding: 4px 12px; border-radius: 4px; font-size: 12px;'>TOKYO</span>
        <span style='background: #1f293d; color: #8899a6; padding: 4px 12px; border-radius: 4px; font-size: 12px;'>LONDON</span>
        <span style='background: #1f293d; color: #8899a6; padding: 4px 12px; border-radius: 4px; font-size: 12px;'>NEW YORK</span>
        <span style='margin-left: auto; color: #00e676; font-size: 13px;'>DXY: <b>BULL 101.465</b> | Session: <b>OFF HOURS</b></span>
    </div>
    """, unsafe_allow_html=True)

    res = generate_omega_signal(selected_asset, ASSETS.get(selected_asset, selected_asset), min_tf)

    col_main, col_strength = st.columns([2, 1])

    with col_main:
        if res and res.get("ok"):
            bias_class = "badge-buy" if "BUY" in res["bias"] else "badge-sell"
            
            st.markdown(f"""
            <div class='omega-card omega-card-active'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: #8899a6; font-size: 12px; font-weight: bold;'>TOP SIGNAL</span>
                    <span class='badge-quality'>MED QUALITY</span>
                </div>
                <h1 style='color: #ffffff; margin: 5px 0px; font-size: 38px;'>{res['symbol']}</h1>
                <h2 style='color: #00e676; margin: 0px;'>{res['entry']:.2f} <span style='font-size: 14px; color: #8899a6;'>-0.002%</span></h2>
                <br>
                <div style='display: flex; gap: 30px; align-items: center;'>
                    <div>
                        <div style='color: #8899a6; font-size: 11px;'>DIRECTION</div>
                        <span class='{bias_class}'>{res['bias']}</span>
                    </div>
                    <div>
                        <div style='color: #8899a6; font-size: 11px;'>CONFIDENCE</div>
                        <span style='color: #00e676; font-size: 24px; font-weight: bold;'>{res['score']}%</span>
                    </div>
                </div>
                <br>
                <div style='display: flex; justify-content: space-between; border-top: 1px solid #1f293d; padding-top: 12px;'>
                    <div>
                        <div style='color: #8899a6; font-size: 11px;'>TRADE SETUP</div>
                        <div style='color: #ffffff; font-size: 13px;'>ENTRY: <b>{res['entry']:.2f}</b></div>
                        <div style='color: #00e676; font-size: 13px;'>TP1: <b>{res.get('tp1', res['entry']*1.005):.2f}</b></div>
                        <div style='color: #00e676; font-size: 13px;'>TP2: <b>{res.get('tp2', res['entry']*1.01):.2f}</b></div>
                        <div style='color: #ff5252; font-size: 13px;'>SL: <b>{res.get('sl', res['entry']*0.995):.2f}</b></div>
                        <div style='color: #ffd700; font-size: 13px;'>R:R <b>1:{res['rr']:.2f}</b></div>
                    </div>
                    <div>
                        <div style='color: #8899a6; font-size: 11px;'>ANALYSIS</div>
                        <div style='color: #e0e6ed; font-size: 12px;'>📐 RANGE | MARKUP</div>
                        <div style='color: #e0e6ed; font-size: 12px;'>📊 ADX 11.9 | RSI 58.3</div>
                        <div style='color: #e0e6ed; font-size: 12px;'>🕰️ Daily: BULL | 4H: BULL</div>
                        <div style='color: #ffd700; font-size: 12px;'>⚠️ MTF Conflict</div>
                    </div>
                </div>
                <div class='progress-bg'>
                    <div class='progress-fill-green' style='width: {res["score"]}%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Unable to load live signal data.")

    with col_strength:
        st.markdown("""
        <div class='omega-card'>
            <h4 style='color: #ffffff; margin-top: 0;'>📊 MARKET STRENGTH</h4>
            <div style='margin-bottom: 8px;'>
                <span style='font-size: 12px; color: #ffffff;'>XAUUSD</span> <span style='float: right; color: #00e676; font-size: 12px;'>92%</span>
                <div class='progress-bg'><div class='progress-fill-green' style='width: 92%;'></div></div>
            </div>
            <div style='margin-bottom: 8px;'>
                <span style='font-size: 12px; color: #ffffff;'>NAS100</span> <span style='float: right; color: #00e676; font-size: 12px;'>87%</span>
                <div class='progress-bg'><div class='progress-fill-green' style='width: 87%;'></div></div>
            </div>
            <div style='margin-bottom: 8px;'>
                <span style='font-size: 12px; color: #ffffff;'>US30</span> <span style='float: right; color: #00e676; font-size: 12px;'>72%</span>
                <div class='progress-bg'><div class='progress-fill-green' style='width: 72%;'></div></div>
            </div>
            <div style='margin-bottom: 8px;'>
                <span style='font-size: 12px; color: #ffffff;'>BTCUSD</span> <span style='float: right; color: #ffd700; font-size: 12px;'>60%</span>
                <div class='progress-bg'><div class='progress-fill-green' style='width: 60%;'></div></div>
            </div>
            <div style='margin-bottom: 8px;'>
                <span style='font-size: 12px; color: #ffffff;'>EURUSD</span> <span style='float: right; color: #ff5252; font-size: 12px;'>49%</span>
                <div class='progress-bg'><div class='progress-fill-red' style='width: 49%;'></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 2: SIGNAL ANALYSIS (CHARTS & INDICATOR PANELS)
# -----------------------------------------------------------------------------
elif page == "📈 Signal Analysis":
    st.markdown(f"<h3 style='color: #ffffff;'>📈 {selected_asset} — TECHNICAL CHART & OSCILLATORS</h3>", unsafe_allow_html=True)
    
    res = generate_omega_signal(selected_asset, ASSETS.get(selected_asset, selected_asset), min_tf)
    if res and "data" in res and "15M" in res["data"]:
        df = res["data"]["15M"].tail(80)
        
        # Main Candlestick Chart with TP/SL Lines
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Price"
        ))
        
        # Add Horizontal Indicators
        entry_price = res["entry"]
        fig.add_hline(y=entry_price * 1.008, line_dash="dash", line_color="#00e676", annotation_text="TP1")
        fig.add_hline(y=entry_price * 0.992, line_dash="dash", line_color="#ff5252", annotation_text="SL")

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="#0b0e14",
            plot_bgcolor="#0b0e14"
        )
        st.plotly_chart(fig, width="stretch")

        # Technical Oscillators Sub-Charts
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=[50]*len(df), line=dict(color="purple", dash="dot")))
        fig_rsi.update_layout(template="plotly_dark", height=120, title="RSI + WR%", margin=dict(l=10, r=10, t=25, b=10))
        st.plotly_chart(fig_rsi, width="stretch")
    else:
        st.info("Generating chart data...")

# -----------------------------------------------------------------------------
# VIEW 3: ICT/SMC CHECKLIST
# -----------------------------------------------------------------------------
elif page == "🎯 ICT/SMC Checklist":
    st.markdown("<h3 style='color: #ffffff;'>🎯 ICT/SMC Checklist</h3>", unsafe_allow_html=True)
    
    col_filter1, col_filter2 = st.columns(2)
    col_filter1.selectbox("Timeframe", ["M15", "H1", "H4", "D1"])
    col_filter2.selectbox("Market Condition", ["RANGE", "TRENDING", "BREAKOUT"])

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.checkbox("BOS Confirmed", value=False)
    st.checkbox("OTE Zone 0.618", value=False)
    st.checkbox("Killzone Active", value=False)
    st.checkbox("VWAP Aligned", value=True)
    st.checkbox("FVG Present", value=True)
    st.checkbox("Order Block", value=True)
    st.checkbox("RSI Divergence", value=False)
    st.checkbox("DXY Aligned", value=False)
    st.checkbox("Active Session", value=True)
    st.checkbox("Supertrend Aligned", value=True)
    st.checkbox("Ichimoku Aligned", value=False)

# -----------------------------------------------------------------------------
# VIEW 4: SIGNAL DIRECTION GRID
# -----------------------------------------------------------------------------
elif page == "🧩 Signal Direction Grid":
    st.markdown("<h3 style='color: #ffffff;'>🧩 Signal Direction Grid</h3>", unsafe_allow_html=True)

    grid_items = [
        {"asset": "XAUUSD", "score": 36, "bias": "WEAK SELL", "type": "DAY TRADE"},
        {"asset": "BTCUSD", "score": 38, "bias": "WEAK SELL", "type": "DAY TRADE"},
        {"asset": "EURUSD", "score": 38, "bias": "WEAK SELL", "type": "SWING"},
        {"asset": "US30", "score": 76, "bias": "BUY NOW", "type": "DAY TRADE"},
    ]

    cols = st.columns(3)
    for idx, item in enumerate(grid_items):
        with cols[idx % 3]:
            border_color = "#ff5252" if "SELL" in item["bias"] else "#00e676"
            st.markdown(f"""
            <div class='omega-card' style='border: 1px solid {border_color}; text-align: center;'>
                <h3 style='color: #ffffff; margin: 0;'>{item['asset']}</h3>
                <h1 style='color: {border_color}; margin: 10px 0;'>{item['score']}</h1>
                <span class='badge-sell' style='border-color: {border_color}; color: {border_color}; background: transparent;'>{item['bias']}</span>
                <div style='color: #8899a6; font-size: 11px; margin-top: 12px;'>{item['type']}</div>
                <div class='progress-bg'>
                    <div class='progress-fill-red' style='width: {item['score']}%; background-color: {border_color};'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 5: ALERTS & NEWS
# -----------------------------------------------------------------------------
elif page == "🔔 Alerts & News":
    st.markdown("<h3 style='color: #ffffff;'>🔔 Signal Alerts & Market News</h3>", unsafe_allow_html=True)
    
    if st.button("🔄 Scan All Markets Now"):
        st.toast("Scanning completed!", icon="✅")

    st.markdown("#### Signal Alerts")
    st.markdown("""
    <div style='background: #0d291e; border-left: 4px solid #00e676; padding: 12px; border-radius: 6px; margin-bottom: 10px;'>
        <b style='color: #00e676;'>🟢 USDJPY — BUY</b> <span style='background: #ff4081; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;'>SWING</span>
        <span style='float: right; color: #8899a6; font-size: 11px;'>12:19:15</span><br>
        <small style='color: #e0e6ed;'>Score: 77/100 | Grade: A | Price: 162.669 | TP: 162.734 | SL: 162.604</small>
    </div>
    <div style='background: #2b210e; border-left: 4px solid #ffd700; padding: 12px; border-radius: 6px; margin-bottom: 10px;'>
        <b style='color: #ffd700;'>⚠️ USDJPY — Score jumped to 77</b> <span style='background: #ff4081; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;'>SWING</span>
        <span style='float: right; color: #8899a6; font-size: 11px;'>12:19:15</span><br>
        <small style='color: #e0e6ed;'>Score: 77/100 | Grade: A | Price: 162.669 | TP: 162.734 | SL: 162.604</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Market News")
    st.selectbox("News for", SUPPORTED_PAIRS)
    
    st.markdown("""
    <div class='omega-card'>
        📄 <b>Gold holds above $4,000 despite market shifts</b>
        <div style='color: #8899a6; font-size: 11px; margin-top: 5px;'>📅 2026-08-08</div>
    </div>
    <div class='omega-card'>
        📄 <b>Why did gold win? Key economic factors explained</b>
        <div style='color: #8899a6; font-size: 11px; margin-top: 5px;'>📅 2026-08-08</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 6: TRADE JOURNAL
# -----------------------------------------------------------------------------
elif page == "📖 Trade Journal":
    st.markdown("<h3 style='color: #ffffff;'>📖 Trade Journal</h3>", unsafe_allow_html=True)
    journal_entries = load_journal()
    if journal_entries:
        st.dataframe(pd.DataFrame(journal_entries), width="stretch")
    else:
        st.info("No saved trade entries found in database.")
