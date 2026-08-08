import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
import random

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM DARK THEME CSS (matches screenshots)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global dark background */
    .stApp {
        background-color: #0b0d12;
        color: #e1e3e8;
        font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* Card style */
    .card {
        background-color: #12161f;
        border: 1px solid #1f2633;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .card-gold-border {
        border: 1px solid #d9a441 !important;
    }
    .text-gold { color: #d9a441 !important; font-weight: 600; }
    .text-green { color: #22c55e !important; font-weight: 600; }
    .text-red { color: #ef4444 !important; font-weight: 600; }
    .text-muted { color: #8a94a6 !important; font-size: 13px; }
    .metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px 12px;
        background-color: #161b26;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 13px;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .setup-row {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        font-size: 14px;
        border-bottom: 1px solid #1a202c;
    }
    .bar-container {
        background-color: #1a202c;
        border-radius: 6px;
        height: 8px;
        width: 100%;
        overflow: hidden;
        margin-top: 4px;
    }
    .bar-fill-green { background-color: #22c55e; height: 100%; }
    .bar-fill-gold { background-color: #d9a441; height: 100%; }
    .bar-fill-red { background-color: #ef4444; height: 100%; }
    /* Hide default header */
    header { visibility: hidden; }
    /* Sidebar styling */
    .css-1d391kg { background-color: #0f131c !important; }
    .css-1d391kg .stRadio label { color: #e1e3e8 !important; }
    .css-1d391kg .stRadio div[role="radiogroup"] label {
        background: #1a202c;
        border-radius: 6px;
        padding: 6px 12px;
        margin-bottom: 4px;
    }
    .css-1d391kg .stRadio div[role="radiogroup"] label:hover {
        background: #2a2f3f;
    }
    .css-1d391kg .stRadio div[role="radiogroup"] label[data-checked="true"] {
        background: #2a2010;
        border-left: 3px solid #d9a441;
    }
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & RISK CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#d9a441; margin:0;'>⚡ SEKWAILA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8a94a6; font-size:11px; margin-top:-4px;'>OMEGA X</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Navigation
    nav_options = [
        "Dashboard", "Market Scanner", "Heatmap", "AI Narrator",
        "News Intelligence", "Multi-Timeframe", "Correlation Matrix",
        "Trade Journal", "Performance", "Telegram Alerts", "Settings", "Help"
    ]
    page = st.radio("Navigation", nav_options, label_visibility="collapsed")

    st.markdown("---")
    st.subheader("Account (R)")
    account_r = st.number_input("Balance", value=500.00, step=50.0, label_visibility="collapsed")
    risk_pct = st.slider("Risk %", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    usd_val = account_r / 18.5  # example exchange rate
    risk_r = account_r * (risk_pct / 100.0)
    st.caption(f"≈ USD ${usd_val:.2f} | Risk R{risk_r:.2f}")

    st.markdown("---")
    auto_scan = st.toggle("Live Auto-Scan", value=True)
    scan_interval = st.slider("Interval (sec)", 10, 120, 60)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.caption("Educational only — not financial advice")

# -----------------------------------------------------------------------------
# HELPER: PLOTLY GAUGE (semi-circle)
# -----------------------------------------------------------------------------
def create_gauge(score, color_hex):
    fig = go.Figure(go.Indicator(
        mode="number+gauge",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': color_hex}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_hex, 'thickness': 0.25},
            'bgcolor': "#161b26",
            'bordercolor': "rgba(0,0,0,0)",
            'steps': [{'range': [0, 100], 'color': '#161b26'}]
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# -----------------------------------------------------------------------------
# PAGE: DASHBOARD
# -----------------------------------------------------------------------------
if page == "Dashboard":
    # Asset selector
    asset = st.selectbox("Active Asset Focus", ["BTCUSD", "XAUUSD", "US30", "EURUSD", "NAS100"], index=0)
    
    # Mock data per asset
    mock = {
        "BTCUSD": {"score": 81, "dir": "STRONG BUY", "conf": 81, "price": 54076.57, "tp1": 54160.64, "tp2": 54244.70, "sl": 53992.50, "color": "#22c55e"},
        "XAUUSD": {"score": 92, "dir": "EXTREME BUY", "conf": 92, "price": 2358.45, "tp1": 2364.80, "tp2": 2373.60, "sl": 2346.20, "color": "#d9a441"},
        "US30":   {"score": 72, "dir": "BUY", "conf": 72, "price": 43120.50, "tp1": 43240.00, "tp2": 43360.00, "sl": 43000.00, "color": "#22c55e"},
        "EURUSD": {"score": 38, "dir": "WEAK SELL", "conf": 38, "price": 1.0895, "tp1": 1.0870, "tp2": 1.0845, "sl": 1.0920, "color": "#ef4444"},
        "NAS100": {"score": 87, "dir": "STRONG BUY", "conf": 87, "price": 19780.00, "tp1": 19880.00, "tp2": 19980.00, "sl": 19680.00, "color": "#d9a441"},
    }
    data = mock[asset]

    # Gauge
    st.plotly_chart(create_gauge(data["score"], data["color"]), use_container_width=True)

    # Indicator grid (matching screenshots)
    st.markdown(f"""
    <div class='card'>
        <div style='display:flex; justify-content:space-between;'>
            <span class='text-gold'>DIRECTION</span>
            <span style='color:{data["color"]}; font-weight:bold;'>{data["dir"]}</span>
        </div>
        <div style='display:flex; justify-content:space-between; margin-top:4px;'>
            <span class='text-muted'>CONFIDENCE</span>
            <span style='color:{data["color"]};'>{data["conf"]}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Indicators (RSI, ADX, etc.)
    st.markdown("""
    <div class='card'>
        <div class='metric-grid'>
            <div class='metric-row'><span>RSI</span><span class='text-green'>58.8</span></div>
            <div class='metric-row'><span>ADX</span><span class='text-green'>21.2</span></div>
            <div class='metric-row'><span>ATR</span><span>18.65</span></div>
            <div class='metric-row'><span>WR%</span><span class='text-red'>-10.1</span></div>
            <div class='metric-row'><span>MFI</span><span>46.9</span></div>
            <div class='metric-row'><span>ST</span><span class='text-green'>▲ B</span></div>
            <div class='metric-row'><span>Ichimoku</span><span class='text-muted'>☁ N</span></div>
            <div class='metric-row'><span>Squeeze</span><span class='text-muted'>OFF</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Trade Setup
    st.markdown(f"""
    <div class='card card-gold-border'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span class='text-gold'>TRADE SETUP</span>
            <span style='background:#2a2010; color:#d9a441; padding:2px 8px; border-radius:4px; font-size:12px;'>ANALYSIS</span>
        </div>
        <div class='setup-row'><span>ENTRY</span><b>{data['price']:,.2f}</b></div>
        <div class='setup-row'><span>TP1</span><b class='text-green'>{data['tp1']:,.2f}</b></div>
        <div class='setup-row'><span>TP2</span><b class='text-green'>{data['tp2']:,.2f}</b></div>
        <div class='setup-row'><span>SL</span><b class='text-red'>{data['sl']:,.2f}</b></div>
        <div class='setup-row' style='border-bottom:none;'><span>R:R</span><b class='text-gold'>1:1.00</b></div>
        <div style='margin-top:8px; font-size:13px; color:#8a94a6;'>
            <span>Daily: BULL | 4H: BULL | MTF Conflict</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Market Strength (bars)
    st.markdown("""
    <div class='card'>
        <div class='text-gold' style='margin-bottom:8px;'>📊 MARKET STRENGTH</div>
        <div><span>US30</span> <span class='text-green'>STRONG BUY 81%</span></div>
        <div class='bar-container'><div class='bar-fill-green' style='width:81%;'></div></div>
        <div style='margin-top:8px;'><span>SP500</span> <span class='text-green'>BUY 72%</span></div>
        <div class='bar-container'><div class='bar-fill-green' style='width:72%;'></div></div>
        <div style='margin-top:8px;'><span>XAUUSD</span> <span class='text-gold'>EXTREME BUY 92%</span></div>
        <div class='bar-container'><div class='bar-fill-gold' style='width:92%;'></div></div>
        <div style='margin-top:8px;'><span>BTCUSD</span> <span class='text-green'>BUY 68%</span></div>
        <div class='bar-container'><div class='bar-fill-green' style='width:68%;'></div></div>
    </div>
    """, unsafe_allow_html=True)

    # Small Account Tips (as seen in screenshot)
    with st.expander("💡 Small Account Tips (R500)", expanded=False):
        st.markdown("""
        - Trade micro lots (0.01) only
        - Max 1 trade at a time on R500
        - Focus on SCALP setups — smaller stops
        - Only trade STRONG BUY/SELL NOW signals
        - XAUUSD and EURUSD best for small accounts
        - Never risk more than 1% per trade = R5
        """)

# -----------------------------------------------------------------------------
# PAGE: MARKET SCANNER
# -----------------------------------------------------------------------------
elif page == "Market Scanner":
    st.markdown("<h2 class='text-gold'>📡 Market Scanner</h2>", unsafe_allow_html=True)
    st.caption("Real-time signal overview across all assets")

    # Sample data
    scanner_data = pd.DataFrame({
        "Symbol": ["XAUUSD", "NAS100", "US30", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY", "SPX500"],
        "Signal": ["EXTREME BUY", "STRONG BUY", "BUY", "BUY", "WEAK SELL", "WEAK SELL", "WEAK SELL", "BUY"],
        "Confidence": [92, 87, 72, 68, 45, 38, 42, 65],
        "Price": [2358.45, 19780.00, 43120.50, 54076.57, 1.0895, 1.2780, 149.20, 5340.00],
    })
    # Color code
    def color_signal(val):
        if "BUY" in val or "EXTREME" in val:
            return "color: #22c55e;"
        elif "SELL" in val:
            return "color: #ef4444;"
        return "color: #d9a441;"
    styled = scanner_data.style.applymap(color_signal, subset=['Signal'])
    st.dataframe(styled, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: HEATMAP
# -----------------------------------------------------------------------------
elif page == "Heatmap":
    st.markdown("<h2 class='text-gold'>🔥 Heatmap</h2>", unsafe_allow_html=True)
    st.caption("Performance heatmap across assets (24h change)")

    # Generate mock heatmap data
    assets = ["XAUUSD", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY", "NAS100", "SPX500", "US30"]
    changes = np.random.uniform(-3, 3, len(assets)).round(2)
    df_heat = pd.DataFrame({"Asset": assets, "Change %": changes})
    fig = px.treemap(df_heat, path=['Asset'], values=np.abs(changes), color='Change %',
                     color_continuous_scale=['red', 'grey', 'green'],
                     color_continuous_midpoint=0,
                     title="24h % Change")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e1e3e8')
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: AI NARRATOR
# -----------------------------------------------------------------------------
elif page == "AI Narrator":
    st.markdown("<h2 class='text-gold'>🤖 AI Narrator (Katlego)</h2>", unsafe_allow_html=True)
    with st.chat_message("assistant"):
        st.write("""
        **XAUUSD** is showing strong bullish momentum after sweeping liquidity below 2,346. 
        Structure is bullish on all key timeframes. DXY is weak, which supports the upside continuation. 
        Institutional buying detected in the London/NY overlap. 
        Bullish Structure (BOS on 15m & 1H). 
        Recommendation: **EXTREME BUY** with 92% confidence.
        """)
    user_input = st.chat_input("Ask SEKWAILA AI... e.g. 'Should I buy gold now?'")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            st.write("I'm Katlego, your AI trading assistant. Based on current market structure and momentum, I recommend watching for a retest of the FVG before entering. Always manage your risk.")

# -----------------------------------------------------------------------------
# PAGE: NEWS INTELLIGENCE
# -----------------------------------------------------------------------------
elif page == "News Intelligence":
    st.markdown("<h2 class='text-gold'>📰 News Intelligence</h2>", unsafe_allow_html=True)
    st.caption("Latest market-moving news and sentiment")

    news = [
        {"time": "18:00", "event": "USD Retail Sales", "impact": "MEDIUM", "sentiment": "BULLISH"},
        {"time": "20:30", "event": "USD FOMC Member Speaks", "impact": "MEDIUM", "sentiment": "NEUTRAL"},
        {"time": "22:00", "event": "USD Crude Oil Inventories", "impact": "MEDIUM", "sentiment": "BEARISH"},
    ]
    for item in news:
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            st.write(item["time"])
        with col2:
            st.write(item["event"])
        with col3:
            if item["sentiment"] == "BULLISH":
                st.markdown(f"<span class='text-green'>{item['sentiment']}</span>", unsafe_allow_html=True)
            elif item["sentiment"] == "BEARISH":
                st.markdown(f"<span class='text-red'>{item['sentiment']}</span>", unsafe_allow_html=True)
            else:
                st.write(item["sentiment"])

# -----------------------------------------------------------------------------
# PAGE: MULTI-TIMEFRAME
# -----------------------------------------------------------------------------
elif page == "Multi-Timeframe":
    st.markdown("<h2 class='text-gold'>⏳ Multi-Timeframe Analysis</h2>", unsafe_allow_html=True)
    tf_data = {
        "Daily": "BULL",
        "4H": "BULL",
        "1H": "BULL",
        "15min": "BEAR",
        "5min": "NEUTRAL"
    }
    for tf, trend in tf_data.items():
        col1, col2 = st.columns([1,2])
        with col1:
            st.write(tf)
        with col2:
            if "BULL" in trend:
                st.markdown(f"<span class='text-green'>▲ {trend}</span>", unsafe_allow_html=True)
            elif "BEAR" in trend:
                st.markdown(f"<span class='text-red'>▼ {trend}</span>", unsafe_allow_html=True)
            else:
                st.write(trend)

# -----------------------------------------------------------------------------
# PAGE: CORRELATION MATRIX
# -----------------------------------------------------------------------------
elif page == "Correlation Matrix":
    st.markdown("<h2 class='text-gold'>📊 Correlation Matrix</h2>", unsafe_allow_html=True)
    # Mock correlation matrix
    symbols = ["XAUUSD", "DXY", "BTCUSD", "NAS100", "US30", "EURUSD"]
    corr = np.array([
        [1.00, -0.78, 0.42, -0.65, -0.55, 0.30],
        [-0.78, 1.00, -0.45, 0.85, 0.75, -0.20],
        [0.42, -0.45, 1.00, -0.32, -0.28, 0.10],
        [-0.65, 0.85, -0.32, 1.00, 0.90, -0.15],
        [-0.55, 0.75, -0.28, 0.90, 1.00, -0.10],
        [0.30, -0.20, 0.10, -0.15, -0.10, 1.00]
    ])
    df_corr = pd.DataFrame(corr, index=symbols, columns=symbols)
    fig = px.imshow(df_corr, text_auto=True, color_continuous_scale='RdBu_r', 
                    title="Correlation Matrix", aspect="auto")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e1e3e8')
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: TRADE JOURNAL
# -----------------------------------------------------------------------------
elif page == "Trade Journal":
    st.markdown("<h2 class='text-gold'>📖 Trade Journal</h2>", unsafe_allow_html=True)
    # Mock trade data
    trades = pd.DataFrame({
        "Date": pd.date_range(start='2026-08-01', periods=5, freq='D'),
        "Symbol": ["XAUUSD", "BTCUSD", "EURUSD", "NAS100", "US30"],
        "Direction": ["BUY", "SELL", "BUY", "BUY", "SELL"],
        "Entry": [2358.45, 54076.57, 1.0895, 19780.00, 43120.50],
        "Exit": [2364.80, 53992.50, 1.0870, 19880.00, 43050.00],
        "PnL": [6.35, -84.07, -0.0025, 100.00, -70.50],
        "R": [1.2, -1.0, -0.5, 2.0, -1.5],
    })
    st.dataframe(trades, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: PERFORMANCE
# -----------------------------------------------------------------------------
elif page == "Performance":
    st.markdown("<h2 class='text-gold'>📈 Performance</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Win Rate", "72%", "+2%")
    with col2:
        st.metric("Total PnL (R)", "R185.50", "+R45.20")
    with col3:
        st.metric("Trades Today", "3", "+1")

    # Equity curve
    dates = pd.date_range(start='2026-07-01', periods=30, freq='D')
    equity = np.random.normal(500, 10, 30).cumsum() + 500
    df_eq = pd.DataFrame({"Date": dates, "Equity": equity})
    fig = px.line(df_eq, x='Date', y='Equity', title="Equity Curve")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e1e3e8')
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: TELEGRAM ALERTS
# -----------------------------------------------------------------------------
elif page == "Telegram Alerts":
    st.markdown("<h2 class='text-gold'>📱 Telegram Alerts</h2>", unsafe_allow_html=True)
    st.caption("Configure your alert preferences")
    st.checkbox("Enable Telegram Alerts", value=True)
    st.text_input("Bot Token", placeholder="123456:ABC-DEF...")
    st.text_input("Chat ID", placeholder="-123456789")
    st.multiselect("Alert on signals for:", ["XAUUSD", "BTCUSD", "EURUSD", "NAS100"], default=["XAUUSD", "BTCUSD"])
    st.button("Save Alert Settings")

# -----------------------------------------------------------------------------
# PAGE: SETTINGS
# -----------------------------------------------------------------------------
elif page == "Settings":
    st.markdown("<h2 class='text-gold'>⚙️ Settings</h2>", unsafe_allow_html=True)
    st.markdown("### Scanner Settings")
    st.selectbox("Timeframe", ["15min", "1H", "4H", "Daily"], index=0)
    st.number_input("Symbols Monitored", min_value=1, max_value=20, value=3)
    st.markdown("### Risk Settings")
    st.number_input("Default Risk %", value=1.0, step=0.1)
    st.checkbox("Auto-save trade journal", value=True)
    if st.button("Apply Settings"):
        st.success("Settings updated successfully!")

# -----------------------------------------------------------------------------
# PAGE: HELP
# -----------------------------------------------------------------------------
elif page == "Help":
    st.markdown("<h2 class='text-gold'>❓ Help & Guide</h2>", unsafe_allow_html=True)
    st.markdown("""
    **How to use SEKWAILA OMEGA X**

    1. **Dashboard** – View real-time signals and trade setups.
    2. **Market Scanner** – Scan all assets for high-conviction signals.
    3. **Heatmap** – Visualize asset performance.
    4. **AI Narrator** – Get market commentary from Katlego.
    5. **News Intelligence** – Stay updated with economic events.
    6. **Multi-Timeframe** – Check trend alignment across timeframes.
    7. **Correlation Matrix** – Understand asset relationships.
    8. **Trade Journal** – Keep a record of your trades.
    9. **Performance** – Monitor your equity and win rate.
    10. **Telegram Alerts** – Receive signals on your phone.
    11. **Settings** – Customize scanner and risk parameters.
    12. **Help** – You are here!

    > Always trade with proper risk management. Past performance does not guarantee future results.
    """)

# -----------------------------------------------------------------------------
# FOOTER (optional)
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ and Streamlit • SEKWAILA OMEGA X • Educational only — not financial advice")
