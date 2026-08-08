import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK THEME CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark Theme Setup */
    .stApp {
        background-color: #0b0d12;
        color: #e1e3e8;
        font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
    }
    
    /* Remove Padding for Mobile UI */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* Outer Container Cards */
    .card-box {
        background-color: #12161f;
        border: 1px solid #1f2633;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    .accent-border {
        border: 1px solid #d9a441 !important;
    }

    /* Colors */
    .text-green { color: #22c55e !important; font-weight: 600; }
    .text-red { color: #ef4444 !important; font-weight: 600; }
    .text-gold { color: #d9a441 !important; font-weight: 600; }
    .text-muted { color: #8a94a6 !important; font-size: 13px; }

    /* Indicator Data Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        background-color: #161b26;
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
    }

    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Trade Setup Values */
    .setup-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        font-size: 14px;
        border-bottom: 1px solid #1a202c;
    }

    /* Progress Bar Container */
    .bar-container {
        background-color: #1a202c;
        border-radius: 6px;
        height: 8px;
        width: 100%;
        overflow: hidden;
        margin-top: 6px;
    }
    
    .bar-fill-green {
        background-color: #22c55e;
        height: 100%;
    }

    /* Hide standard header elements */
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SIDEBAR NAVIGATION & RISK SETTINGS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#d9a441; margin-bottom:0;'>⚡ SEKWAILA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8a94a6; font-size:11px; margin-top:0;'>OMEGA X</p>", unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Dashboard", "Market Scanner", "Heatmap", "AI Narrator", "Signal History", "Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.subheader("Risk Management")
    
    account_r = st.number_input("Account (R)", value=500.00, step=50.0)
    risk_pct = st.slider("Risk %", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    
    # Currency Converters
    usd_val = account_r / 18.5
    risk_r = account_r * (risk_pct / 100.0)
    st.caption(f"≈ USD ${usd_val:.2f} | Risk R{risk_r:.2f}")

    st.markdown("---")
    auto_scan = st.toggle("Live Auto-Scan", value=True)
    scan_interval = st.slider("Interval (sec)", 10, 120, 60)
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTION: Plotly Semi-Circle Speedometer Gauge
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
            'steps': [
                {'range': [0, 100], 'color': '#161b26'}
            ]
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
# 4. PAGE: DASHBOARD (MAIN MOBILE SIGNAL VIEW)
# -----------------------------------------------------------------------------
if page == "Dashboard":

    # --- TOP ASSET SELECTOR & SIGNAL BANNER ---
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    selected_asset = st.selectbox("Active Asset Focus", ["BTCUSD", "XAUUSD", "US30", "EURUSD"], index=0)
    
    # Mock data setup based on asset
    if selected_asset == "BTCUSD":
        score, direction, conf_pct, price = 60, "STRONG BUY", 81, 64939.18
        gauge_color = "#22c55e"
        tp1, tp2, sl = 65108.40, 65277.63, 64769.96
    elif selected_asset == "XAUUSD":
        score, direction, conf_pct, price = 34, "NEUTRAL / SELL", 43, 2358.45
        gauge_color = "#ef4444"
        tp1, tp2, sl = 2348.20, 2335.00, 2370.10
    else:
        score, direction, conf_pct, price = 72, "BUY", 72, 4312.20
        gauge_color = "#d9a441"
        tp1, tp2, sl = 4296.99, 4281.77, 4327.41

    # Gauge Render
    st.plotly_chart(create_gauge(score, gauge_color), use_container_width=True)

    # Indicator Matrix Block
    st.markdown("""
    <div class='metric-grid'>
        <div class='metric-row'><span>RSI</span><span class='text-green'>55.0</span></div>
        <div class='metric-row'><span>WR%</span><span class='text-red'>-10.1</span></div>
        <div class='metric-row'><span>ADX</span><span class='text-green'>17.1</span></div>
        <div class='metric-row'><span>CCI</span><span>72.1</span></div>
        <div class='metric-row'><span>MFI</span><span>46.9</span></div>
        <div class='metric-row'><span>ST</span><span class='text-green'>▲ B</span></div>
        <div class='metric-row'><span>Ichimoku</span><span class='text-muted'>☁ N</span></div>
        <div class='metric-row'><span>Squeeze</span><span class='text-muted'>OFF</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- TRADE SETUP CARD ---
    st.markdown(f"""
    <div class='card-box'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
            <span class='text-gold'>TRADE SETUP</span>
            <span style='background:#2a2010; color:#d9a441; padding:2px 8px; border-radius:4px; font-size:12px;'>MED</span>
        </div>
        <div class='setup-row'><span>ENTRY</span><b>{price:,.2f}</b></div>
        <div class='setup-row'><span>TP1</span><b class='text-green'>{tp1:,.2f}</b></div>
        <div class='setup-row'><span>TP2</span><b class='text-green'>{tp2:,.2f}</b></div>
        <div class='setup-row'><span>SL</span><b class='text-red'>{sl:,.2f}</b></div>
        <div class='setup-row' style='border-bottom:none;'><span>R:R</span><b class='text-gold'>1:1.00</b></div>
    </div>
    """, unsafe_allow_html=True)

    # --- MARKET STRENGTH SECTION ---
    st.markdown("""
    <div class='card-box'>
        <div class='text-gold' style='margin-bottom:10px;'>📊 MARKET STRENGTH</div>
        
        <div style='display:flex; justify-content:space-between; font-size:13px; margin-top:8px;'>
            <span><b>US30</b></span><span class='text-green'>STRONG BUY 81%</span>
        </div>
        <div class='bar-container'><div class='bar-fill-green' style='width: 81%;'></div></div>

        <div style='display:flex; justify-content:space-between; font-size:13px; margin-top:12px;'>
            <span><b>SP500</b></span><span class='text-green'>BUY 72%</span>
        </div>
        <div class='bar-container'><div class='bar-fill-green' style='width: 72%;'></div></div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. PAGE: AI NARRATOR (KATLEGO)
# -----------------------------------------------------------------------------
elif page == "AI Narrator":
    st.markdown("<h2 class='text-gold'>🤖 AI Narrator (Katlego)</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card-box'>
        <p style='font-size:15px; line-height:1.6;'>
            <b>GC=F</b> is showing strong buy momentum.<br><br>
            Market structure is aligned on key timeframes with ATR at <b>18.41</b>. 
            Institutional liquidity sweeps detected during the London/NY overlap.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. PAGE: SIGNAL HISTORY & STATISTICS
# -----------------------------------------------------------------------------
elif page == "Signal History":
    st.markdown("<h2>📜 Signal History</h2>", unsafe_allow_html=True)
    
    # Mock Signal Table Data
    data = {
        "timestamp": [
            datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        ],
        "symbol": ["BTC/USD", "EUR/USD", "XAU/USD"],
        "signal": ["BUY", "BUY", "SELL"]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("<h2>📊 Statistics</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Unique Signals", "3")
    with col2:
        st.metric("BUY", "2")
    with col3:
        st.metric("SELL", "1")

# -----------------------------------------------------------------------------
# 7. PAGE: SETTINGS
# -----------------------------------------------------------------------------
elif page == "Settings":
    st.markdown("<h2>⚙️ Settings</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card-box'>
        <div style='background:#183824; border:1px solid #22c55e; padding:12px; border-radius:6px; color:#22c55e; margin-bottom:12px;'>
            🟢 Scanner Online
        </div>
        <p><b>Timeframe:</b> 15min</p>
        <p><b>Monitored Symbols:</b> 3</p>
    </div>
    """, unsafe_allow_html=True)
          
