"""
SEKWAILA OMEGA X
Stable Streamlit dashboard.

This file is intentionally self-contained:
- It does not import data.market_data.
- It does not import signals.signal_engine.
- It does not require a Deriv App ID.
- It reads TWELVE_DATA_API_KEY from Streamlit Secrets.
- It provides live Twelve Data prices and a clean pair selector.
- Trading execution is deliberately disabled.
"""

import os
from datetime import datetime, timezone

import requests
import streamlit as st

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

PAIRS = {
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD",
    "USDCHF": "USD/CHF",
    "NZDUSD": "NZD/USD",
    "BTCUSD": "BTC/USD",
}

# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------

st.markdown(
    """
<style>
.stApp {
    background: #0A0D14;
    color: #E2E8F0;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    background: #0F131C;
}
.omega-title {
    font-size: 28px;
    font-weight: 800;
    color: #FFFFFF;
}
.omega-subtitle {
    color: #94A3B8;
    font-size: 12px;
}
.card {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}
.metric-label {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
.metric-value {
    font-size: 25px;
    font-weight: 800;
}
.green {
    color: #10B981;
}
.red {
    color: #EF4444;
}
.yellow {
    color: #F59E0B;
}
.muted {
    color: #94A3B8;
}
.signal-box {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 22px;
}
.buy-badge {
    background: rgba(16,185,129,.10);
    border: 2px solid #10B981;
    color: #10B981;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    font-weight: 800;
}
.sell-badge {
    background: rgba(239,68,68,.10);
    border: 2px solid #EF4444;
    color: #EF4444;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    font-weight: 800;
}
.small {
    font-size: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Secrets / API
# ---------------------------------------------------------------------


def get_secret(name: str, default: str = "") -> str:
    """Read a Streamlit secret first, then environment variable."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


TWELVE_DATA_API_KEY = get_secret("TWELVE_DATA_API_KEY")

# Deriv is optional. No App ID is required for this dashboard.
DERIV_API_TOKEN = get_secret("DERIV_API_TOKEN")

# ---------------------------------------------------------------------
# Twelve Data functions
# ---------------------------------------------------------------------


@st.cache_data(ttl=10, show_spinner=False)
def twelve_price(symbol: str):
    """Return a Twelve Data live price."""
    if not TWELVE_DATA_API_KEY:
        return None, "TWELVE_DATA_API_KEY is missing."

    try:
        response = requests.get(
            "https://api.twelvedata.com/price",
            params={
                "symbol": symbol,
                "apikey": TWELVE_DATA_API_KEY,
            },
            timeout=10,
        )

        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        data = response.json()

        if data.get("status") == "error":
            return None, str(data.get("message", "Twelve Data error"))

        value = data.get("price")

        if value is None:
            return None, "No price returned."

        return float(value), None

    except requests.RequestException as exc:
        return None, f"Network error: {exc}"
    except (ValueError, TypeError) as exc:
        return None, f"Invalid price: {exc}"


@st.cache_data(ttl=30, show_spinner=False)
def twelve_candles(symbol: str, interval: str = "15min", outputsize: int = 100):
    """Return recent candles as a list."""
    if not TWELVE_DATA_API_KEY:
        return [], "TWELVE_DATA_API_KEY is missing."

    try:
        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": TWELVE_DATA_API_KEY,
            },
            timeout=15,
        )

        if response.status_code != 200:
            return [], f"HTTP {response.status_code}"

        data = response.json()

        if data.get("status") == "error":
            return [], str(data.get("message", "Twelve Data error"))

        return data.get("values", []), None

    except requests.RequestException as exc:
        return [], f"Network error: {exc}"
    except Exception as exc:
        return [], str(exc)


def format_price(value):
    if value is None:
        return "—"
    if value >= 100:
        return f"{value:,.2f}"
    if value >= 10:
        return f"{value:,.3f}"
    return f"{value:,.5f}"


# ---------------------------------------------------------------------
# Simple signal calculation
# ---------------------------------------------------------------------


def calculate_signal(candles):
    """
    Conservative informational signal based on recent candle structure.
    This is NOT an automated trading strategy and does not place orders.
    """
    if len(candles) < 20:
        return {
            "bias": "NEUTRAL",
            "score": 0,
            "reason": "Not enough candles.",
        }

    closes = []
    for candle in candles:
        try:
            closes.append(float(candle["close"]))
        except (KeyError, TypeError, ValueError):
            continue

    if len(closes) < 20:
        return {
            "bias": "NEUTRAL",
            "score": 0,
            "reason": "Invalid candle data.",
        }

    # Twelve Data returns newest first.
    recent = closes[:10]
    older = closes[10:20]

    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)

    if recent_avg > older_avg:
        difference = (recent_avg - older_avg) / older_avg
        score = min(95, int(60 + difference * 5000))
        return {
            "bias": "BUY",
            "score": score,
            "reason": "Recent average is above the prior average.",
        }

    if recent_avg < older_avg:
        difference = (older_avg - recent_avg) / older_avg
        score = min(95, int(60 + difference * 5000))
        return {
            "bias": "SELL",
            "score": score,
            "reason": "Recent average is below the prior average.",
        }

    return {
        "bias": "NEUTRAL",
        "score": 50,
        "reason": "Recent price structure is balanced.",
    }


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚡ SEKWAILA")
    st.caption("OMEGA X — ANCIENT WISDOM. MODERN PROFIT.")
    st.markdown("---")

    selected_pair = st.selectbox(
        "Market",
        list(PAIRS.keys()),
        index=0,
    )

    st.markdown("### Markets")

    for pair_name in PAIRS:
        if st.button(
            pair_name,
            key=f"pair_{pair_name}",
            width="stretch",
        ):
            st.session_state["selected_pair"] = pair_name
            st.rerun()

    if "selected_pair" in st.session_state:
        selected_pair = st.session_state["selected_pair"]

    st.markdown("---")

    account_balance = st.number_input(
        "Account Balance ($)",
        min_value=0.0,
        value=500.0,
        step=50.0,
    )

    risk_pct = st.slider(
        "Risk %",
        min_value=0.25,
        max_value=5.0,
        value=1.0,
        step=0.25,
    )

    risk_amount = account_balance * risk_pct / 100

    st.caption(f"Risk Amount: **${risk_amount:.2f}**")

    st.markdown("---")

    st.markdown("### Live Trading")
    st.warning(
        "Execution is disabled. This version only reads market data "
        "and displays analysis."
    )

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

utc_now = datetime.now(timezone.utc).strftime("%H:%M:%S")

header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown(
        """
<div>
    <div class="omega-title">👑 SEKWAILA OMEGA X</div>
    <div class="omega-subtitle">
        ANCIENT WISDOM. MODERN PROFIT.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        f"""
<div style="
    background:#111622;
    border:1px solid #10B981;
    padding:8px 16px;
    border-radius:20px;
    color:#10B981;
    font-weight:700;
    font-size:12px;
    text-align:center;
">
    ● LIVE &nbsp;&nbsp; UTC {utc_now}
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------
# Current market
# ---------------------------------------------------------------------

td_symbol = PAIRS[selected_pair]
current_price, price_error = twelve_price(td_symbol)
candles, candle_error = twelve_candles(td_symbol)

signal = calculate_signal(candles)

# ---------------------------------------------------------------------
# Top metrics
# ---------------------------------------------------------------------

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(
        """
<div class="card">
<div class="metric-label">Selected Market</div>
<div class="metric-value green">""" + selected_pair + """</div>
</div>
""",
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        """
<div class="card">
<div class="metric-label">Live Price</div>
<div class="metric-value">"""
        + format_price(current_price)
        + """</div>
</div>
""",
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        """
<div class="card">
<div class="metric-label">Signal</div>
<div class="metric-value">"""
        + signal["bias"]
        + """</div>
</div>
""",
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        """
<div class="card">
<div class="metric-label">Score</div>
<div class="metric-value yellow">"""
        + str(signal["score"])
        + """</div>
</div>
""",
        unsafe_allow_html=True,
    )

with m5:
    st.markdown(
        """
<div class="card">
<div class="metric-label">Session</div>
<div class="metric-value yellow">LIVE</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------
# Connection status
# ---------------------------------------------------------------------

st.markdown("### 🔌 LIVE CONNECTIONS")

conn1, conn2, conn3 = st.columns(3)

with conn1:
    if current_price is not None:
        st.success(
            f"Twelve Data CONNECTED\n\n{td_symbol}: {format_price(current_price)}"
        )
    else:
        st.error(
            "Twelve Data ERROR\n\n"
            + (price_error or "No price received.")
        )

with conn2:
    if DERIV_API_TOKEN:
        st.info(
            "Deriv token detected.\n\n"
            "Streaming remains disabled in this safe dashboard."
        )
    else:
        st.warning(
            "Deriv NOT CONFIGURED\n\n"
            "No Deriv App ID is required for this dashboard."
        )

with conn3:
    if TWELVE_DATA_API_KEY:
        st.success("Market data API key loaded")
    else:
        st.error("TWELVE_DATA_API_KEY missing")

# ---------------------------------------------------------------------
# Main signal
# ---------------------------------------------------------------------

st.markdown("### 📡 MARKET SIGNAL")

left, right = st.columns([1.4, 1])

with left:
    if signal["bias"] == "BUY":
        badge_class = "buy-badge"
        badge_text = "🚀 BUY BIAS"
    elif signal["bias"] == "SELL":
        badge_class = "sell-badge"
        badge_text = "🔻 SELL BIAS"
    else:
        badge_class = "card"
        badge_text = "⏸ NEUTRAL"

    st.markdown(
        f"""
<div class="signal-box">
    <div class="metric-label">SIGNAL &nbsp; {selected_pair}</div>
    <h1 style="margin:5px 0 0 0;color:#FFFFFF;">
        {td_symbol}
    </h1>
    <div style="margin-top:8px;font-size:24px;font-weight:800;"
         class="green">
        {format_price(current_price)}
    </div>
    <div style="margin-top:20px;" class="{badge_class}">
        {badge_text}
    </div>
    <div style="margin-top:18px;" class="muted">
        Score: <strong>{signal["score"]}</strong>
    </div>
    <div style="margin-top:8px;" class="muted">
        {signal["reason"]}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
<div class="card">
<div class="metric-label">DATA STATUS</div>
<h3 style="color:#FFFFFF;">Twelve Data</h3>
<p class="muted small">
Live quote and recent candles are requested directly from Twelve Data.
</p>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------
# Recent candles
# ---------------------------------------------------------------------

st.markdown("### 📊 RECENT MARKET DATA")

if candles:
    rows = []

    for candle in candles[:15]:
        rows.append(
            {
                "Time": candle.get("datetime", ""),
                "Open": candle.get("open", ""),
                "High": candle.get("high", ""),
                "Low": candle.get("low", ""),
                "Close": candle.get("close", ""),
            }
        )

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )
else:
    st.warning(
        "No candle data received."
        + (f" {candle_error}" if candle_error else "")
    )

# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.markdown("---")

st.caption(
    "SEKWAILA OMEGA X • Market-data dashboard only • "
    "No orders are placed by this version."
)
