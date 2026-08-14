"""
SEKWAILA OMEGA X — Pro Terminal Dashboard
Ultra-sleek TradingView/Bloomberg style institutional dashboard.
"""

from typing import Any, Dict
import plotly.graph_objects as go
import streamlit as st
from signals.signal_engine import analyze_market, get_market_overview
from twelve_data_adapter import TwelveDataClient

# --------------------------------------------------------------------
# 1. Page Config
# --------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------
# 2. Custom CSS Injection (TradingView Dark Theme)
# --------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0b0e14 !important;
        color: #d1d4dc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    
    /* Hide Default Headers/Footers */
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { visibility: hidden; }

    /* Custom Glassmorphism Signal Cards */
    .card-box {
        background: rgba(18, 22, 31, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
    }

    /* Signal Badges */
    .badge-buy {
        background: rgba(0, 230, 118, 0.15);
        color: #00E676;
        border: 1px solid #00E676;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-sell {
        background: rgba(255, 23, 68, 0.15);
        color: #FF1744;
        border: 1px solid #FF1744;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Metric Typography */
    .metric-value-green {
        font-size: 1.8rem;
        font-weight: 800;
        color: #00E676;
        margin: 0;
    }
    .metric-value-red {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FF1744;
        margin: 0;
    }
    .metric-value-gold {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFC107;
        margin: 0;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #787b86;
        letter-spacing: 1px;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #131722 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper function to plot a modern TradingView-style gauge
def create_score_gauge(score: int, is_buy: bool):
    color = "#00E676" if is_buy else "#FF1744"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"color": "#FFFFFF", "size": 32}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#363a45",
                },
                "bar": {"color": color, "thickness": 0.25},
                "bgcolor": "#1e222d",
                "borderwidth": 0,
            },
        )
    )
    fig.update_layout(
        height=140,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# --------------------------------------------------------------------
# 3. Sidebar Setup
# --------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **SEKWAILA**")
    st.caption("OMEGA X • PRO TERMINAL")
    st.markdown("---")

    # Mode Selector Navigation
    nav_mode = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔍 Market Scanner", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Trading Parameters**")

    api_key = st.secrets.get("TWELVE_DATA_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Twelve Data API Key", type="password")

    symbol = st.text_input("Asset Ticker", value="XAU/USD")
    timeframe = st.selectbox(
        "Timeframe", ["5m", "15m", "30m", "1h", "4h", "1d"], index=1
    )

    account_balance = st.number_input("Account (ZAR)", value=1000.0, step=100.0)
    risk_pct = st.slider("Risk %", 0.5, 5.0, 1.0, 0.5)

    run_btn = st.button("🚀 RUN ANALYSIS", type="primary", use_container_width=True)

client = TwelveDataClient(api_key=api_key)

# --------------------------------------------------------------------
# 4. Top Status Toolbar
# --------------------------------------------------------------------
tb_col1, tb_col2, tb_col3, tb_col4 = st.columns([2, 1, 1, 1])
with tb_col1:
    st.markdown("## **SEKWAILA OMEGA X**")
with tb_col2:
    st.markdown(
        "<div class='card-box' style='padding:10px; text-align:center;'><span class='metric-label'>STATUS</span><br><b style='color:#00E676;'>● LIVE FEED</b></div>",
        unsafe_allow_html=True,
    )
with tb_col3:
    st.markdown(
        "<div class='card-box' style='padding:10px; text-align:center;'><span class='metric-label'>RISK ENGINE</span><br><b style='color:#FFC107;'>ACTIVE</b></div>",
        unsafe_allow_html=True,
    )
with tb_col4:
    st.markdown(
        f"<div class='card-box' style='padding:10px; text-align:center;'><span class='metric-label'>ACCOUNT RISK</span><br><b style='color:#00E676;'>R {(account_balance * (risk_pct/100)):.2f}</b></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# --------------------------------------------------------------------
# 5. Dashboard View
# --------------------------------------------------------------------
if nav_mode == "📊 Dashboard":
    if run_btn or "last_analysis" not in st.session_state:
        if not api_key:
            st.error("⚠️ Please provide a valid Twelve Data API Key.")
        else:
            with st.spinner(f"Analyzing {symbol} structure..."):
                st.session_state["last_analysis"] = analyze_market(
                    symbol, timeframe, client
                )

    if "last_analysis" in st.session_state:
        res = st.session_state["last_analysis"]

        if res["ok"]:
            is_buy = "BUY" in res["signal"]
            badge_class = "badge-buy" if is_buy else "badge-sell"
            price_color = "metric-value-green" if is_buy else "metric-value-red"

            # Top Signal Card Layout (Matches Replit/Rocket Screenshot)
            main_col1, main_col2 = st.columns([2, 1])

            with main_col1:
                st.markdown(
                    f"""
                    <div class="card-box">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span class="metric-label">TOP SIGNAL</span>
                                <h1 style="margin:0; font-size:2.5rem; letter-spacing:1px;">{res['symbol']}</h1>
                            </div>
                            <div class="{badge_class}">{res['signal']}</div>
                        </div>
                        <div style="margin-top:15px;">
                            <span class="metric-label">LIVE ENTRY PRICE</span>
                            <div class="{price_color}">{res['entry_price']}</div>
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                # Trade Setup Box
                s1, s2, s3, s4 = st.columns(4)
                with s1:
                    st.markdown(
                        f"<div class='card-box'><span class='metric-label'>STOP LOSS</span><div class='metric-value-red'>{res['stop_loss']}</div></div>",
                        unsafe_allow_html=True,
                    )
                with s2:
                    st.markdown(
                        f"<div class='card-box'><span class='metric-label'>TAKE PROFIT 1</span><div class='metric-value-green'>{res['tp1']}</div></div>",
                        unsafe_allow_html=True,
                    )
                with s3:
                    st.markdown(
                        f"<div class='card-box'><span class='metric-label'>TAKE PROFIT 2</span><div class='metric-value-green'>{res['tp2']}</div></div>",
                        unsafe_allow_html=True,
                    )
                with s4:
                    st.markdown(
                        f"<div class='card-box'><span class='metric-label'>R : R RATIO</span><div class='metric-value-gold'>{res['rr']}</div></div>",
                        unsafe_allow_html=True,
                    )

            with main_col2:
                st.markdown(
                    "<div class='card-box' style='text-align:center;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<span class='metric-label'>SIGNAL CONFIDENCE SCORE</span>",
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    create_score_gauge(res["score"], is_buy),
                    use_container_width=True,
                )
                st.markdown(
                    f"<p style='color:#787b86; font-size:0.85rem;'>{res['reason']}</p></div>",
                    unsafe_allow_html=True,
                )

            # Multi-Timeframe Structure Grid
            st.markdown("### 🌐 **Multi-Timeframe Alignment**")
            tf_cols = st.columns(6)
            for idx, (tf_name, tf_bias) in enumerate(res["timeframes"].items()):
                color = "#00E676" if "BUY" in tf_bias else "#FF1744"
                with tf_cols[idx]:
                    st.markdown(
                        f"""
                        <div class="card-box" style="text-align:center;">
                            <span class="metric-label">{tf_name}</span>
                            <div style="color:{color}; font-weight:bold; font-size:1.1rem; margin-top:5px;">{tf_bias}</div>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.error(f"Analysis Error: {res['reason']}")

elif nav_mode == "🔍 Market Scanner":
    st.subheader("🔥 **Active Watchlist Scanner**")
    watchlist = ["EUR/USD", "GBP/USD", "USD/JPY", "BTC/USD", "XAU/USD", "QQQ"]
    if api_key:
        with st.spinner("Fetching live market snapshot..."):
            df = get_market_overview(watchlist, client)
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("Please provide an API key in the sidebar.")

elif nav_mode == "⚙️ Settings":
    st.subheader("⚙️ **System Configuration**")
    st.json(
        {
            "Engine": "SEKWAILA OMEGA X v3.2",
            "Provider": "Twelve Data REST / WebSocket",
            "SMC Modules": ["Order Blocks", "Liquidity Runs", "Multi-Timeframe"],
            "Account Base Currency": "ZAR (R)",
        }
    )
