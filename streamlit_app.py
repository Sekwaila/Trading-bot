"""
SEKWAILA OMEGA X
================
Stable Streamlit dashboard.

This version intentionally keeps the application self-contained:
- Twelve Data live market data
- Multiple forex / metals / crypto / index instruments
- Pair selector toolbar
- Live price
- Candlestick chart
- Basic technical signal engine
- TP / SL calculation
- Risk calculator
- Multi-timeframe analysis
- Safe Deriv status
- No automatic trade execution

Required Streamlit secrets:
    TWELVE_DATA_API_KEY = "your_key"

Optional:
    DERIV_API_TOKEN = "your_token"
    DERIV_APP_ID = "1089"
"""

import os
import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANTS
# ============================================================

APP_NAME = "SEKWAILA OMEGA X"

ASSETS = {
    "XAUUSD": {
        "name": "Gold",
        "td_symbol": "XAU/USD",
        "category": "METALS",
        "decimals": 2,
    },
    "EURUSD": {
        "name": "Euro / US Dollar",
        "td_symbol": "EUR/USD",
        "category": "FOREX",
        "decimals": 5,
    },
    "GBPUSD": {
        "name": "British Pound / US Dollar",
        "td_symbol": "GBP/USD",
        "category": "FOREX",
        "decimals": 5,
    },
    "USDJPY": {
        "name": "US Dollar / Japanese Yen",
        "td_symbol": "USD/JPY",
        "category": "FOREX",
        "decimals": 3,
    },
    "AUDUSD": {
        "name": "Australian Dollar / US Dollar",
        "td_symbol": "AUD/USD",
        "category": "FOREX",
        "decimals": 5,
    },
    "USDCAD": {
        "name": "US Dollar / Canadian Dollar",
        "td_symbol": "USD/CAD",
        "category": "FOREX",
        "decimals": 5,
    },
    "USDCHF": {
        "name": "US Dollar / Swiss Franc",
        "td_symbol": "USD/CHF",
        "category": "FOREX",
        "decimals": 5,
    },
    "NZDUSD": {
        "name": "New Zealand Dollar / US Dollar",
        "td_symbol": "NZD/USD",
        "category": "FOREX",
        "decimals": 5,
    },
    "BTCUSD": {
        "name": "Bitcoin / US Dollar",
        "td_symbol": "BTC/USD",
        "category": "CRYPTO",
        "decimals": 2,
    },
    "ETHUSD": {
        "name": "Ethereum / US Dollar",
        "td_symbol": "ETH/USD",
        "category": "CRYPTO",
        "decimals": 2,
    },
}

INTERVALS = {
    "15M": "15min",
    "1H": "1h",
    "4H": "4h",
    "1D": "1day",
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 50% -20%,
            #162033 0%,
            #0A0D14 42%,
            #06080D 100%
        );
    color: #E2E8F0;
}

.block-container {
    max-width: 1550px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #0B1019;
    border-right: 1px solid #1E293B;
}

.omega-title {
    color: #FFFFFF;
    font-size: 30px;
    font-weight: 900;
    letter-spacing: 1px;
}

.omega-subtitle {
    color: #94A3B8;
    font-size: 11px;
    letter-spacing: 1.5px;
}

.card {
    background: rgba(17, 22, 34, 0.95);
    border: 1px solid #1E293B;
    border-radius: 15px;
    padding: 18px;
    margin-bottom: 14px;
}

.metric-card {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    min-height: 105px;
}

.label {
    color: #94A3B8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.big-value {
    color: #FFFFFF;
    font-size: 25px;
    font-weight: 850;
    margin-top: 5px;
}

.green {
    color: #10B981 !important;
}

.red {
    color: #EF4444 !important;
}

.gold {
    color: #F59E0B !important;
}

.muted {
    color: #94A3B8;
}

.signal-header {
    color: #FFFFFF;
    font-size: 27px;
    font-weight: 850;
}

.price {
    color: #10B981;
    font-size: 25px;
    font-weight: 850;
}

.buy-badge {
    background: rgba(16,185,129,.10);
    border: 2px solid #10B981;
    border-radius: 12px;
    padding: 11px;
    text-align: center;
    color: #10B981;
    font-size: 18px;
    font-weight: 850;
}

.sell-badge {
    background: rgba(239,68,68,.10);
    border: 2px solid #EF4444;
    border-radius: 12px;
    padding: 11px;
    text-align: center;
    color: #EF4444;
    font-size: 18px;
    font-weight: 850;
}

.wait-badge {
    background: rgba(245,158,11,.10);
    border: 2px solid #F59E0B;
    border-radius: 12px;
    padding: 11px;
    text-align: center;
    color: #F59E0B;
    font-size: 18px;
    font-weight: 850;
}

.score {
    width: 82px;
    height: 82px;
    border-radius: 50%;
    border: 4px solid #10B981;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #111622;
}

.score-number {
    color: #FFFFFF;
    font-size: 23px;
    font-weight: 900;
}

.score-text {
    color: #94A3B8;
    font-size: 8px;
    font-weight: 700;
}

.target {
    background: #161D2A;
    border: 1px solid #263247;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
}

.target-label {
    color: #94A3B8;
    font-size: 10px;
    font-weight: 700;
}

.target-value {
    font-size: 18px;
    font-weight: 800;
    margin-top: 3px;
}

.connection {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 11px;
    margin-bottom: 8px;
}

.connection-ok {
    color: #10B981;
    font-weight: 750;
}

.connection-error {
    color: #EF4444;
    font-weight: 750;
}

.tf-card {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 13px;
    text-align: center;
}

.tf-name {
    color: #F59E0B;
    font-size: 13px;
    font-weight: 850;
}

.toolbar {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 15px;
}

.small {
    font-size: 11px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SECRETS
# ============================================================

def get_secret(name: str, default: str = "") -> str:
    """
    Safely read a Streamlit secret, then environment variable.
    """

    try:
        value = st.secrets.get(name)

        if value is not None:
            return str(value).strip()

    except Exception:
        pass

    return os.getenv(name, default).strip()


TWELVE_DATA_API_KEY = get_secret("TWELVE_DATA_API_KEY")

DERIV_API_TOKEN = get_secret("DERIV_API_TOKEN")

DERIV_APP_ID = get_secret(
    "DERIV_APP_ID",
    "1089",
)


# ============================================================
# TWELVE DATA
# ============================================================

def twelve_data_request(
    endpoint: str,
    params: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Generic Twelve Data request.
    """

    if not TWELVE_DATA_API_KEY:
        return None

    request_params = dict(params)
    request_params["apikey"] = TWELVE_DATA_API_KEY

    try:

        response = requests.get(
            f"https://api.twelvedata.com/{endpoint}",
            params=request_params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        if data.get("status") == "error":
            return None

        return data

    except Exception:
        return None


@st.cache_data(ttl=10, show_spinner=False)
def get_live_price(symbol: str) -> Optional[float]:

    data = twelve_data_request(
        "price",
        {
            "symbol": symbol,
        },
    )

    if not data:
        return None

    try:
        return float(data["price"])
    except Exception:
        return None


@st.cache_data(ttl=20, show_spinner=False)
def get_quote(symbol: str) -> Optional[Dict[str, Any]]:

    return twelve_data_request(
        "quote",
        {
            "symbol": symbol,
        },
    )


@st.cache_data(ttl=30, show_spinner=False)
def get_candles(
    symbol: str,
    interval: str,
    outputsize: int = 120,
) -> pd.DataFrame:

    data = twelve_data_request(
        "time_series",
        {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON",
        },
    )

    if not data:
        return pd.DataFrame()

    values = data.get("values", [])

    if not values:
        return pd.DataFrame()

    try:

        df = pd.DataFrame(values)

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce",
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        df = df.dropna(
            subset=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
            ]
        )

        df = df.sort_values("datetime")

        df = df.set_index("datetime")

        return df

    except Exception:

        return pd.DataFrame()


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def calculate_ema(
    series: pd.Series,
    period: int,
) -> pd.Series:

    return series.ewm(
        span=period,
        adjust=False,
    ).mean()


def calculate_rsi(
    series: pd.Series,
    period: int = 14,
) -> pd.Series:

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        math.nan,
    )

    return 100 - (
        100 / (1 + rs)
    )


def analyze_dataframe(
    df: pd.DataFrame,
) -> Dict[str, Any]:

    result = {
        "bias": "WAIT",
        "score": 50.0,
        "ema_bias": "NEUTRAL",
        "rsi_bias": "NEUTRAL",
        "momentum": "NEUTRAL",
        "trend": "NEUTRAL",
    }

    if df.empty or len(df) < 30:
        return result

    close = df["close"]

    ema20 = calculate_ema(
        close,
        20,
    )

    ema50 = calculate_ema(
        close,
        50,
    )

    rsi = calculate_rsi(
        close,
        14,
    )

    current = float(close.iloc[-1])

    e20 = float(ema20.iloc[-1])

    e50 = float(ema50.iloc[-1])

    current_rsi = float(rsi.iloc[-1])

    score = 50.0

    if e20 > e50:

        score += 20

        result["ema_bias"] = "BULLISH"

        result["trend"] = "BULLISH"

    elif e20 < e50:

        score -= 20

        result["ema_bias"] = "BEARISH"

        result["trend"] = "BEARISH"

    if current_rsi >= 55:

        score += 15

        result["rsi_bias"] = "BULLISH"

    elif current_rsi <= 45:

        score -= 15

        result["rsi_bias"] = "BEARISH"

    if len(close) >= 6:

        previous = float(
            close.iloc[-6]
        )

        if current > previous:

            score += 10

            result["momentum"] = "BULLISH"

        elif current < previous:

            score -= 10

            result["momentum"] = "BEARISH"

    score = max(
        0,
        min(100, score),
    )

    if score >= 70:

        bias = "BUY"

    elif score <= 30:

        bias = "SELL"

    else:

        bias = "WAIT"

    result.update(
        {
            "bias": bias,
            "score": score,
            "rsi": current_rsi,
            "ema20": e20,
            "ema50": e50,
            "price": current,
        }
    )

    return result


# ============================================================
# MULTI-TIMEFRAME ANALYSIS
# ============================================================

@st.cache_data(ttl=30, show_spinner=False)
def get_multi_timeframe(
    symbol: str,
) -> Dict[str, Dict[str, Any]]:

    results = {}

    for tf_name, interval in INTERVALS.items():

        df = get_candles(
            symbol,
            interval,
            100,
        )

        results[tf_name] = analyze_dataframe(
            df
        )

    return results


def combined_signal(
    mtf: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:

    valid = [
        x
        for x in mtf.values()
        if x.get("price")
    ]

    if not valid:

        return {
            "bias": "WAIT",
            "score": 50,
        }

    buy_count = sum(
        1
        for x in valid
        if x["bias"] == "BUY"
    )

    sell_count = sum(
        1
        for x in valid
        if x["bias"] == "SELL"
    )

    average_score = sum(
        x["score"]
        for x in valid
    ) / len(valid)

    if buy_count >= 3:

        bias = "BUY"

    elif sell_count >= 3:

        bias = "SELL"

    else:

        bias = "WAIT"

    return {
        "bias": bias,
        "score": round(
            average_score,
            1,
        ),
        "buy_count": buy_count,
        "sell_count": sell_count,
    }


# ============================================================
# TP / SL
# ============================================================

def calculate_levels(
    price: float,
    bias: str,
) -> Dict[str, float]:

    if not price or price <= 0:

        return {
            "sl": 0,
            "tp1": 0,
            "tp2": 0,
            "tp3": 0,
        }

    # Conservative percentage-based initial levels.
    # These are dashboard calculations, not broker orders.

    if bias == "BUY":

        risk = price * 0.004

        sl = price - risk

        tp1 = price + risk * 1.5

        tp2 = price + risk * 2.2

        tp3 = price + risk * 2.8

    elif bias == "SELL":

        risk = price * 0.004

        sl = price + risk

        tp1 = price - risk * 1.5

        tp2 = price - risk * 2.2

        tp3 = price - risk * 2.8

    else:

        sl = 0
        tp1 = 0
        tp2 = 0
        tp3 = 0

    return {
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
    }


# ============================================================
# DERIV CONNECTION CHECK
# ============================================================

def check_deriv() -> Dict[str, Any]:
    """
    Safe Deriv connectivity check.

    It does not execute trades.
    """

    if not DERIV_API_TOKEN:

        return {
            "ok": False,
            "message": "Deriv token not configured.",
        }

    try:

        import asyncio
        import json
        import websockets

        async def check():

            url = (
                "wss://ws.derivws.com/"
                f"websockets/v3?app_id={DERIV_APP_ID}"
            )

            async with websockets.connect(
                url,
                open_timeout=8,
                close_timeout=5,
            ) as ws:

                await ws.send(
                    json.dumps(
                        {
                            "authorize":
                            DERIV_API_TOKEN
                        }
                    )
                )

                response = await ws.recv()

                return json.loads(response)

        data = asyncio.run(check())

        if data.get("error"):

            return {
                "ok": False,
                "message":
                    data["error"].get(
                        "message",
                        "Deriv error",
                    ),
            }

        if data.get("authorize"):

            return {
                "ok": True,
                "message":
                    "Deriv authorized.",
            }

        return {
            "ok": False,
            "message": "No authorization response.",
        }

    except Exception as exc:

        return {
            "ok": False,
            "message": str(exc),
        }


# ============================================================
# HELPERS
# ============================================================

def fmt_price(
    value: Optional[float],
    decimals: int = 2,
) -> str:

    if value is None:

        return "—"

    try:

        return f"{float(value):,.{decimals}f}"

    except Exception:

        return "—"


def signal_class(
    bias: str,
) -> str:

    if bias == "BUY":

        return "buy-badge"

    if bias == "SELL":

        return "sell-badge"

    return "wait-badge"


def bias_color(
    bias: str,
) -> str:

    if bias == "BUY":

        return "green"

    if bias == "SELL":

        return "red"

    return "gold"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="omega-title">
            👑 SEKWAILA
        </div>

        <div class="omega-subtitle">
            OMEGA X — ANCIENT WISDOM. MODERN PROFIT.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    selected_symbol = st.selectbox(
        "ACTIVE MARKET",
        list(ASSETS.keys()),
        index=0,
    )

    asset = ASSETS[selected_symbol]

    st.caption(
        f"{asset['category']} · "
        f"{asset['name']}"
    )

    st.divider()

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

    risk_amount = (
        account_balance
        * risk_pct
        / 100
    )

    st.caption(
        f"Risk Amount: **${risk_amount:.2f}**"
    )

    st.divider()

    refresh_seconds = st.selectbox(
        "AUTO REFRESH",
        [15, 30, 60, 120],
        index=1,
    )

    if st.button(
        "🔄 REFRESH NOW",
        use_container_width=True,
    ):

        st.cache_data.clear()

        st.rerun()

    st.divider()

    st.markdown(
        "**LIVE TRADING**"
    )

    st.warning(
        "Live execution is disabled. "
        "This dashboard only generates "
        "market analysis."
    )


# ============================================================
# AUTO REFRESH
# ============================================================

if (
    st_autorefresh is not None
):

    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="omega_refresh",
    )


# ============================================================
# HEADER
# ============================================================

utc_now = datetime.now(
    timezone.utc
).strftime("%H:%M:%S")

st.markdown(
    f"""
    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:15px;
    ">

        <div>
            <div class="omega-title">
                👑 SEKWAILA OMEGA X
            </div>

            <div class="omega-subtitle">
                ANCIENT WISDOM. MODERN PROFIT.
            </div>
        </div>

        <div style="
            background:#111622;
            border:1px solid #10B981;
            padding:8px 16px;
            border-radius:20px;
            color:#10B981;
            font-weight:700;
            font-size:12px;
        ">
            ● LIVE &nbsp;&nbsp; UTC {utc_now}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MARKET TOOLBAR
# ============================================================

st.markdown(
    '<div class="toolbar">',
    unsafe_allow_html=True,
)

toolbar_cols = st.columns(
    [
        1.2,
        1,
        1,
        1,
        1,
        1,
    ]
)

with toolbar_cols[0]:

    st.markdown(
        '<div class="label">MARKET</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="
            font-size:19px;
            font-weight:850;
            margin-top:5px;
        ">
            {selected_symbol}
        </div>
        """,
        unsafe_allow_html=True,
    )

with toolbar_cols[1]:

    st.markdown(
        '<div class="label">CATEGORY</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="big-value"
             style="font-size:16px">
            {asset["category"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

with toolbar_cols[2]:

    st.markdown(
        '<div class="label">TIMEFRAME</div>',
        unsafe_allow_html=True,
    )

    selected_tf = st.selectbox(
        "TF",
        list(INTERVALS.keys()),
        index=0,
        label_visibility="collapsed",
    )

with toolbar_cols[3]:

    st.markdown(
        '<div class="label">SOURCE</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="big-value"
             style="font-size:15px;color:#10B981">
            TWELVE DATA
        </div>
        """,
        unsafe_allow_html=True,
    )

with toolbar_cols[4]:

    st.markdown(
        '<div class="label">STATUS</div>',
        unsafe_allow_html=True,
    )

    if TWELVE_DATA_API_KEY:

        st.markdown(
            """
            <div class="big-value"
                 style="font-size:15px;color:#10B981">
                ● CONNECTED
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="big-value"
                 style="font-size:15px;color:#EF4444">
                ● NO KEY
            </div>
            """,
            unsafe_allow_html=True,
        )

with toolbar_cols[5]:

    st.markdown(
        '<div class="label">UTC</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="big-value"
             style="font-size:15px">
            {utc_now}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# NO API KEY
# ============================================================

if not TWELVE_DATA_API_KEY:

    st.error(
        "TWELVE_DATA_API_KEY is not available."
    )

    st.info(
        "Open Streamlit Cloud → Settings → Secrets "
        "and make sure you have:"
    )

    st.code(
        'TWELVE_DATA_API_KEY = "YOUR_KEY"',
        language="toml",
    )

    st.stop()


# ============================================================
# LIVE PRICE
# ============================================================

current_price = get_live_price(
    asset["td_symbol"]
)

quote = get_quote(
    asset["td_symbol"]
)

decimals = asset["decimals"]


# ============================================================
# TOP METRICS
# ============================================================

mtf = get_multi_timeframe(
    asset["td_symbol"]
)

overall = combined_signal(
    mtf
)

buy_count = sum(
    1
    for x in mtf.values()
    if x["bias"] == "BUY"
)

sell_count = sum(
    1
    for x in mtf.values()
    if x["bias"] == "SELL"
)

active_count = max(
    buy_count,
    sell_count,
)

m1, m2, m3, m4, m5 = st.columns(5)

with m1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">🟢 BUY SETUPS</div>
            <div class="big-value green">
                {buy_count}
            </div>
            <div class="small green">
                Multi-timeframe
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">🔴 SELL SETUPS</div>
            <div class="big-value red">
                {sell_count}
            </div>
            <div class="small red">
                Multi-timeframe
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">🔥 ACTIVE NOW</div>
            <div class="big-value green">
                {active_count}
            </div>
            <div class="small green">
                Confirmed TFs
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:

    hour = datetime.now(
        timezone.utc
    ).hour

    if 7 <= hour < 16:
        session = "LONDON"
    elif 13 <= hour < 21:
        session = "NEW YORK"
    elif hour >= 21 or hour < 7:
        session = "ASIA"
    else:
        session = "TRANSITION"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">📡 SESSION</div>
            <div class="big-value gold"
                 style="font-size:18px">
                {session}
            </div>
            <div class="small green">
                ● Monitoring
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m5:

    dxy_price = get_live_price(
        "DXY"
    )

    # Twelve Data may not provide DXY under this
    # exact symbol on every plan.
    dxy_display = (
        fmt_price(dxy_price, 2)
        if dxy_price
        else "N/A"
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">💵 DXY</div>
            <div class="big-value">
                {dxy_display}
            </div>
            <div class="small muted">
                Reference
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CONNECTIONS
# ============================================================

st.markdown(
    "### 🔌 LIVE CONNECTIONS"
)

conn1, conn2, conn3 = st.columns(3)

with conn1:

    if current_price is not None:

        st.markdown(
            f"""
            <div class="connection">
                <div class="connection-ok">
                    Twelve Data CONNECTED
                </div>
                <div class="small muted">
                    {asset["td_symbol"]}:
                    <b>
                    {fmt_price(current_price, decimals)}
                    </b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="connection">
                <div class="connection-error">
                    Twelve Data ERROR
                </div>
                <div class="small muted">
                    No price received.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with conn2:

    deriv_status = check_deriv()

    if deriv_status["ok"]:

        st.markdown(
            """
            <div class="connection">
                <div class="connection-ok">
                    Deriv CONNECTED
                </div>
                <div class="small muted">
                    Account authorization available.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            f"""
            <div class="connection">
                <div class="connection-error">
                    Deriv NOT CONNECTED
                </div>
                <div class="small muted">
                    {deriv_status["message"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with conn3:

    eur_price = get_live_price(
        "EUR/USD"
    )

    if eur_price:

        st.markdown(
            f"""
            <div class="connection">
                <div class="connection-ok">
                    EUR/USD LIVE
                </div>
                <div class="small muted">
                    {fmt_price(eur_price, 5)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="connection">
                <div class="connection-error">
                    EUR/USD ERROR
                </div>
                <div class="small muted">
                    No price received.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN SIGNAL
# ============================================================

st.markdown("### SIGNAL")

signal_cols = st.columns(
    [1.55, 1]
)

levels = calculate_levels(
    current_price or 0,
    overall["bias"],
)

with signal_cols[0]:

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    head1, head2 = st.columns(
        [4, 1]
    )

    with head1:

        st.markdown(
            f"""
            <div class="label">
                SIGNAL &nbsp; <b>{selected_symbol}</b>
            </div>

            <div class="signal-header">
                {asset["name"].upper()}
            </div>

            <div style="margin-top:8px">

                <span class="price">
                    {fmt_price(
                        current_price,
                        decimals
                    )}
                </span>

                <span class="muted"
                      style="
                      margin-left:10px;
                      font-size:13px;
                      ">
                    CURRENT:
                    <b class="green">
                        {fmt_price(
                            current_price,
                            decimals
                        )}
                    </b>
                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with head2:

        score = overall["score"]

        st.markdown(
            f"""
            <div class="score">

                <div class="score-number">
                    {score:.0f}
                </div>

                <div class="score-text">
                    SCORE
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='height:18px'></div>",
        unsafe_allow_html=True,
    )

    badge = signal_class(
        overall["bias"]
    )

    badge_text = {
        "BUY": "🚀 STRONG BUY",
        "SELL": "🔻 STRONG SELL",
        "WAIT": "⏳ WAIT",
    }.get(
        overall["bias"],
        "⏳ WAIT",
    )

    st.markdown(
        f"""
        <div style="
            display:flex;
            gap:12px;
            align-items:center;
        ">

            <div class="{badge}"
                 style="flex:1">
                {badge_text}
            </div>

            <div class="target"
                 style="min-width:85px">

                <div class="target-label">
                    GRADE
                </div>

                <div class="target-value
                    {bias_color(overall["bias"])}">
                    {
                        "A"
                        if score >= 80
                        else "B"
                        if score >= 65
                        else "C"
                    }
                </div>

            </div>

            <div class="target"
                 style="min-width:95px">

                <div class="target-label">
                    R : R
                </div>

                <div class="target-value">
                    1 : 2.8
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<hr style='border-color:#1E293B;margin:20px 0'>",
        unsafe_allow_html=True,
    )

    t1, t2, t3, sl = st.columns(4)

    target_items = [
        (
            t1,
            "TP1",
            levels["tp1"],
            "green",
        ),
        (
            t2,
            "TP2",
            levels["tp2"],
            "green",
        ),
        (
            t3,
            "TP3",
            levels["tp3"],
            "green",
        ),
        (
            sl,
            "STOP LOSS",
            levels["sl"],
            "red",
        ),
    ]

    for col, label, value, color in target_items:

        with col:

            st.markdown(
                f"""
                <div class="target">

                    <div class="target-label">
                        {label}
                    </div>

                    <div class="
                        target-value
                        {color}
                    ">
                        {
                            fmt_price(
                                value,
                                decimals
                            )
                            if value
                            else "—"
                        }
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# MULTI-TIMEFRAME
# ============================================================

with signal_cols[1]:

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="label">MULTI-TIMEFRAME ANALYSIS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='height:8px'></div>",
        unsafe_allow_html=True,
    )

    for tf in [
        "1D",
        "4H",
        "1H",
        "15M",
    ]:

        data = mtf.get(
            tf,
            {},
        )

        bias = data.get(
            "bias",
            "WAIT",
        )

        score = data.get(
            "score",
            50,
        )

        color = bias_color(
            bias
        )

        structure = (
            "BOS ↑"
            if bias == "BUY"
            else
            "BOS ↓"
            if bias == "SELL"
            else
            "CONSOLIDATION"
        )

        st.markdown(
            f"""
            <div class="tf-card"
                 style="margin-bottom:7px">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">

                    <span class="tf-name">
                        {tf}
                    </span>

                    <span class="{color}"
                          style="
                          font-weight:800;
                          font-size:12px;
                          ">
                        {bias}
                    </span>

                </div>

                <div class="small muted"
                     style="margin-top:5px">
                    {structure}
                    &nbsp; · &nbsp;
                    Score {score:.0f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# CHART
# ============================================================

st.markdown(
    "### 📈 PRICE ACTION"
)

chart_df = get_candles(
    asset["td_symbol"],
    INTERVALS[selected_tf],
    150,
)

if (
    go is not None
    and not chart_df.empty
):

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=chart_df.index,
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name=selected_symbol,
        )
    )

    if levels["sl"]:

        fig.add_hline(
            y=levels["sl"],
            line_dash="dash",
            annotation_text="STOP",
        )

    if levels["tp1"]:

        fig.add_hline(
            y=levels["tp1"],
            line_dash="dot",
            annotation_text="TP1",
        )

    if levels["tp2"]:

        fig.add_hline(
            y=levels["tp2"],
            line_dash="dot",
            annotation_text="TP2",
        )

    if levels["tp3"]:

        fig.add_hline(
            y=levels["tp3"],
            line_dash="dot",
            annotation_text="TP3",
        )

    fig.update_layout(
        template="plotly_dark",
        height=520,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10,
        ),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.warning(
        "No candle data available for "
        f"{selected_symbol} / {selected_tf}."
    )


# ============================================================
# MARKET DETAILS
# ============================================================

left, right = st.columns(2)

with left:

    st.markdown(
        "### 🧠 TECHNICAL CONFLUENCE"
    )

    analysis = mtf.get(
        selected_tf,
        {},
    )

    rows = [
        {
            "Indicator": "EMA 20 / EMA 50",
            "Bias": analysis.get(
                "ema_bias",
                "N/A",
            ),
        },
        {
            "Indicator": "RSI",
            "Bias": analysis.get(
                "rsi_bias",
                "N/A",
            ),
        },
        {
            "Indicator": "Momentum",
            "Bias": analysis.get(
                "momentum",
                "N/A",
            ),
        },
        {
            "Indicator": "Trend",
            "Bias": analysis.get(
                "trend",
                "N/A",
            ),
        },
    ]

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


with right:

    st.markdown(
        "### 💰 RISK REFERENCE"
    )

    if current_price and levels["sl"]:

        distance = abs(
            current_price
            - levels["sl"]
        )

        if distance > 0:

            risk_per_unit = distance

            estimated_units = (
                risk_amount
                / risk_per_unit
            )

        else:

            estimated_units = 0

        st.markdown(
            f"""
            <div class="card">

                <div class="label">
                    ACCOUNT
                </div>

                <div class="big-value">
                    ${account_balance:,.2f}
                </div>

                <div class="label"
                     style="margin-top:12px">
                    RISK
                </div>

                <div class="big-value red">
                    ${risk_amount:,.2f}
                </div>

                <div class="label"
                     style="margin-top:12px">
                    STOP DISTANCE
                </div>

                <div class="big-value">
                    {fmt_price(
                        distance,
                        decimals
                    )}
                </div>

                <div class="label"
                     style="margin-top:12px">
                    REFERENCE UNITS
                </div>

                <div class="big-value green">
                    {estimated_units:,.4f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Reference calculation only. "
            "Actual broker contract sizing, "
            "margin and tick value can differ."
        )

    else:

        st.info(
            "Risk calculation will appear "
            "when a valid market price and "
            "signal levels are available."
        )


# ============================================================
# RAW QUOTE
# ============================================================

with st.expander(
    "📡 Twelve Data Quote Details"
):

    if quote:

        useful_quote = {
            key: quote.get(key)
            for key in [
                "symbol",
                "name",
                "exchange",
                "currency",
                "open",
                "high",
                "low",
                "close",
                "previous_close",
                "change",
                "percent_change",
                "volume",
            ]
            if quote.get(key) is not None
        }

        if useful_quote:

            st.json(
                useful_quote
            )

        else:

            st.json(
                quote
            )

    else:

        st.info(
            "No quote details returned."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    f"""
    <div style="
        display:flex;
        justify-content:space-between;
        color:#64748B;
        font-size:10px;
    ">

        <span>
            SEKWAILA OMEGA X
        </span>

        <span>
            {selected_symbol}
            ·
            {asset["td_symbol"]}
        </span>

        <span>
            LIVE DATA
        </span>

        <span>
            {utc_now} UTC
        </span>

    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Market analysis only. "
    "No automatic trading or broker order placement is enabled."
)
