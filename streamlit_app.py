"""
SEKWAILA OMEGA X - Professional Trading Analysis Dashboard
Architected for high-performance Streamlit Community Cloud deployment.
"""

from datetime import datetime
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pytz
import streamlit as st

from signals.signal_engine import analyze_market, get_market_overview
from twelve_data_adapter import TwelveDataClient

# ---------------------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------
# Timezone Definition
# ---------------------------------------------------------------------

SAST_TZ = pytz.timezone("Africa/Johannesburg")

def get_sast_time():
    return datetime.now(SAST_TZ).strftime("%H:%M:%S")

# ---------------------------------------------------------------------
# Dark Terminal CSS Styling
# ---------------------------------------------------------------------

st.markdown(
    """
<style>
/* Main Container Styling */
.stApp {
    background-color: #0A0E17;
    color: #D1D5DB;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Hide Streamlit Top Menu and Footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 98%;
}

/* Card Styling */
.terminal-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 8px;
    margin-bottom: 12px;
}

.title-text {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #FFFFFF;
}

.subtitle-text {
    font-size: 11px;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Signal Badges */
.badge-extreme-buy { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; padding: 4px 12px; border-radius: 4px; font-weight: 800; text-align: center; }
.badge-strong-buy  { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid #34D399; padding: 4px 12px; border-radius: 4px; font-weight: 700; text-align: center; }
.badge-buy         { background: rgba(52, 211, 153, 0.1); color: #6EE7B7; border: 1px solid #6EE7B7; padding: 4px 12px; border-radius: 4px; font-weight: 600; text-align: center; }
.badge-weak-buy    { background: rgba(110, 231, 183, 0.05); color: #A7F3D0; border: 1px solid #A7F3D0; padding: 4px 12px; border-radius: 4px; font-weight: 500; text-align: center; }
.badge-neutral     { background: rgba(156, 163, 175, 0.1); color: #9CA3AF; border: 1px solid #9CA3AF; padding: 4px 12px; border-radius: 4px; font-weight: 600; text-align: center; }
.badge-weak-sell   { background: rgba(252, 165, 165, 0.05); color: #FCA5A5; border: 1px solid #FCA5A5; padding: 4px 12px; border-radius: 4px; font-weight: 500; text-align: center; }
.badge-sell        { background: rgba(248, 113, 113, 0.1); color: #F87171; border: 1px solid #F87171; padding: 4px 12px; border-radius: 4px; font-weight: 600; text-align: center; }
.badge-strong-sell { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid #EF4444; padding: 4px 12px; border-radius: 4px; font-weight: 700; text-align: center; }
.badge-extreme-sell{ background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #DC2626; padding: 4px 12px; border-radius: 4px; font-weight: 800; text-align: center; }

/* Metrics Displays */
.metric-box {
    background: #171E2E;
    border: 1px solid #232D42;
    border-radius: 6px;
    padding: 10px;
    text-align: center;
}
.metric-label { font-size: 10px; color: #9CA3AF; text-transform: uppercase; margin-bottom: 4px; }
.metric-value { font-size: 16px; font-weight: 700; color: #F3F4F6; }

</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# API Key and Client Setup
# ---------------------------------------------------------------------

def get_secret(name: str) -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.getenv(name, "").strip()

twelve_key = get_secret("TWELVE_DATA_API_KEY")
td_client = TwelveDataClient(api_key=twelve_key)

# ---------------------------------------------------------------------
# Top Header Bar
# ---------------------------------------------------------------------

header_col1, header_col2, header_col3 = st.columns([2, 2, 1])

with header_col1:
    st.markdown(
        """
        <div>
            <span class="title-text">⚡ SEKWAILA OMEGA X</span><br>
            <span class="subtitle-text">ANCIENT WISDOM. MODERN PROFIT.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_col2:
    status_td = "🟢 CONNECTED" if twelve_key else "🔴 NO API KEY"
    st.markdown(
        f"""
        <div style="font-size:12px; color:#9CA3AF; padding-top:4px;">
            Market Data: <strong style="color:#F3F4F6">{status_td}</strong> | 
            Deriv: <strong style="color:#9CA3AF">OPTIONAL / UNCONFIGURED</strong> | 
            Execution: <strong style="color:#EF4444">DISABLED</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_col3:
    st.markdown(
        f"""
        <div style="background:#111827; border:1px solid #1F2937; border-radius:6px; padding:6px 12px; text-align:right;">
            <span style="font-size:10px; color:#6B7280;">LOCAL TIME (SAST)</span><br>
            <span style="font-size:14px; font-weight:700; color:#10B981;">{get_sast_time()}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------
# Navigation / Interactive Toolbar
# ---------------------------------------------------------------------

supported_markets = [
    "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", 
    "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "BTCUSD"
]

supported_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

tb_col1, tb_col2, tb_col3 = st.columns([2, 2, 3])

with tb_col1:
    selected_symbol = st.selectbox("Select Asset", supported_markets, index=0)

with tb_col2:
    selected_tf = st.selectbox("Select Timeframe", supported_timeframes, index=2)

with tb_col3:
    active_tab = st.radio("View Mode", ["OVERVIEW & SIGNALS", "CANDLESTICK CHART", "MARKET MATRIX"], horizontal=True)

st.markdown("---")

# ---------------------------------------------------------------------
# Tab 1: Overview & Signal Analysis
# ---------------------------------------------------------------------

if active_tab == "OVERVIEW & SIGNALS":
    result = analyze_market(selected_symbol, selected_tf, td_client)

    if not result["ok"]:
        st.error(f"Data Fetch Warning: {result['reason']}")
    else:
        # Main Metrics Row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)

        with m_col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Asset Price</div>
                <div class="metric-value">{result['entry_price']:.5f if result['entry_price'] < 10 else result['entry_price']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col2:
            badge_class = f"badge-{result['signal'].lower().replace(' ', '-')}"
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Signal Bias</div>
                <div class="{badge_class}">{result['signal']}</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Signal Score</div>
                <div class="metric-value">{result['score']} / 100</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Risk : Reward</div>
                <div class="metric-value">{result['rr']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Signal Panel & Risk Parameters
        left_panel, right_panel = st.columns([1.5, 1])

        with left_panel:
            st.markdown("<div class='terminal-card'>", unsafe_allow_html=True)
            st.markdown("### 🎯 Order Parameters & Risk Targets")

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.write(f"**Entry Price:** `{result['entry_price']}`")
                st.write(f"**Stop Loss (SL):** `{result['stop_loss']}`")
                st.write(f"**Reasoning:** {result['reason']}")

            with p_col2:
                st.write(f"**Take Profit 1 (TP1):** `{result['tp1']}`")
                st.write(f"**Take Profit 2 (TP2):** `{result['tp2']}`")
                st.write(f"**Take Profit 3 (TP3):** `{result['tp3']}`")

            st.markdown("</div>", unsafe_allow_html=True)

        with right_panel:
            st.markdown("<div class='terminal-card'>", unsafe_allow_html=True)
            st.markdown("### 🌐 Multi-Timeframe Alignment")

            tf_data = result.get("timeframes", {})
            for tf_name, tf_val in tf_data.items():
                st.write(f"**{tf_name.upper()}:** {tf_val}")

            st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Tab 2: Candlestick Chart
# ---------------------------------------------------------------------

elif active_tab == "CANDLESTICK CHART":
    st.markdown(f"### 📈 Technical Chart: {selected_symbol} ({selected_tf.upper()})")

    candles, err = td_client.get_candles(selected_symbol, selected_tf, outputsize=100)

    if err or not candles:
        st.warning(f"Chart data unavailable: {err}")
    else:
        df = pd.DataFrame(candles)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, 
            vertical_spacing=0.03, subplot_titles=(f'{selected_symbol} Price', 'Volume'), 
            row_width=[0.2, 0.8]
        )

        fig.add_trace(
            go.Candlestick(
                x=df["datetime"], open=df["open"], high=df["high"],
                low=df["low"], close=df["close"], name="OHLC"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(x=df["datetime"], y=df["volume"], name="Volume", marker_color="#3B82F6"),
            row=2, col=1
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=600,
            paper_bgcolor="#0A0E17",
            plot_bgcolor="#111827",
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------
# Tab 3: Market Matrix
# ---------------------------------------------------------------------

elif active_tab == "MARKET MATRIX":
    st.markdown("### 📊 Market Overview Matrix")
    
    with st.spinner("Fetching live market matrix..."):
        overview_df = get_market_overview(supported_markets, td_client)

    if not overview_df.empty:
        st.dataframe(overview_df, width="stretch", hide_index=True)
    else:
        st.info("Market matrix temporarily unavailable.")

# ---------------------------------------------------------------------
# Dashboard Footer
# ---------------------------------------------------------------------

st.markdown("---")
st.caption(
    "SEKWAILA OMEGA X • Informational Market Intelligence Terminal • "
    "Automated Trade Execution Disabled"
)
