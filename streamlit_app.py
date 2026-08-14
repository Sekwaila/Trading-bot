"""
SEKWAILA OMEGA X

Main Streamlit application.

Stage:
- Live market data
- Pair selector
- Signal engine
- Deriv public tick test
- Risk calculator
- Telegram-ready architecture

LIVE ORDER EXECUTION IS DISABLED.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from data.market_data import (
    get_live_price,
    get_quote,
)

from deriv_adapter import (
    get_deriv_price,
)

from signals.signal_engine import (
    generate_omega_signal,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #0A0D14;
    color: #E2E8F0;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background-color: #0F131C;
}

.card-box {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}

.signal-header {
    font-size: 28px;
    font-weight: 800;
    color: #FFFFFF;
}

.signal-price {
    font-size: 24px;
    font-weight: 700;
    color: #10B981;
}

.text-muted {
    color: #94A3B8;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 600;
}

.text-green {
    color: #10B981;
}

.text-red {
    color: #EF4444;
}

.badge-buy {
    background: rgba(16,185,129,.10);
    border: 2px solid #10B981;
    color: #10B981;
    padding: 10px 20px;
    border-radius: 12px;
    font-weight: 800;
    text-align: center;
}

.badge-sell {
    background: rgba(239,68,68,.10);
    border: 2px solid #EF4444;
    color: #EF4444;
    padding: 10px 20px;
    border-radius: 12px;
    font-weight: 800;
    text-align: center;
}

.target-card {
    background: #161D2A;
    border: 1px solid #232D42;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
}

.target-val {
    font-size: 18px;
    font-weight: 700;
}

.connection {
    background: #111622;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SYMBOLS
# ============================================================

SYMBOLS = {
    "XAUUSD": "Gold Spot",
    "EURUSD": "Euro / US Dollar",
    "GBPUSD": "British Pound / US Dollar",
    "USDJPY": "US Dollar / Japanese Yen",
    "AUDUSD": "Australian Dollar / US Dollar",
    "USDCAD": "US Dollar / Canadian Dollar",
    "USDCHF": "US Dollar / Swiss Franc",
    "NZDUSD": "New Zealand Dollar / US Dollar",
    "BTCUSD": "Bitcoin / US Dollar",
    "ETHUSD": "Ethereum / US Dollar",
    "SP500": "S&P 500",
    "US30": "Dow Jones 30",
}


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center; padding:10px;">
            <div style="
                font-size:28px;
                font-weight:900;
                letter-spacing:5px;
                color:#F5C542;
            ">
                ⚡ SEKWAILA
            </div>

            <div style="
                font-size:12px;
                letter-spacing:5px;
                color:#64748B;
                margin-top:5px;
            ">
                OMEGA X
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📊 Market Scanner",
            "🔥 Heatmap",
            "🧠 AI Narrator",
            "📰 News Intelligence",
            "📈 Multi-Timeframe",
            "🔗 Correlation Matrix",
            "📒 Trade Journal",
            "📉 Performance",
            "📲 Telegram Alerts",
            "⚙️ Settings",
            "❓ Help",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### Market")

    selected_symbol = st.selectbox(
        "Trading pair",
        list(SYMBOLS.keys()),
        index=0,
    )

    st.caption(
        SYMBOLS[selected_symbol]
    )

    st.markdown("---")

    account_balance = st.number_input(
        "Account ($)",
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
        f"Risk amount: **${risk_amount:.2f}**"
    )

    st.markdown("---")

    st.warning(
        "LIVE ORDER EXECUTION IS DISABLED"
    )

    st.caption(
        "Market data and signal testing only."
    )


# ============================================================
# TIME
# ============================================================

utc_now = datetime.now(
    timezone.utc
).strftime("%H:%M:%S")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
<div style="
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding-bottom:10px;
">

    <div>
        <h1 style="
            margin:0;
            font-size:28px;
        ">
            👑 SEKWAILA OMEGA X
        </h1>

        <p style="
            margin:0;
            color:#94A3B8;
            font-size:12px;
        ">
            ANCIENT WISDOM. MODERN PROFIT.
        </p>
    </div>

    <div style="
        background:#111622;
        border:1px solid #10B981;
        padding:6px 16px;
        border-radius:20px;
        color:#10B981;
        font-weight:600;
        font-size:12px;
    ">
        ● LIVE &nbsp;&nbsp; UTC {utc_now}
    </div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# CURRENT PRICES
# ============================================================

twelve_price = get_live_price(
    selected_symbol
)

deriv_price = get_deriv_price(
    selected_symbol
)


# ============================================================
# SIGNAL
# ============================================================

signal = generate_omega_signal(
    selected_symbol
)


# ============================================================
# TOP METRICS
# ============================================================

buy_symbols = []
sell_symbols = []

for symbol in SYMBOLS:

    try:
        result = generate_omega_signal(
            symbol,
            min_score=65,
        )

        if result.get("ok"):

            if result.get("bias") == "BUY":
                buy_symbols.append(symbol)

            elif result.get("bias") == "SELL":
                sell_symbols.append(symbol)

    except Exception:
        continue


m1, m2, m3, m4, m5 = st.columns(5)


with m1:

    st.markdown(
        f"""
        <div class="card-box"
             style="padding:12px;text-align:center;">

            <div class="text-muted">
                🟢 BUY SETUPS
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#10B981;
            ">
                {len(buy_symbols)}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                {", ".join(buy_symbols[:4]) or "None"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m2:

    st.markdown(
        f"""
        <div class="card-box"
             style="padding:12px;text-align:center;">

            <div class="text-muted">
                🔴 SELL SETUPS
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#EF4444;
            ">
                {len(sell_symbols)}
            </div>

            <div style="
                font-size:10px;
                color:#EF4444;
            ">
                {", ".join(sell_symbols[:4]) or "None"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m3:

    active = len(
        buy_symbols
    ) + len(
        sell_symbols
    )

    st.markdown(
        f"""
        <div class="card-box"
             style="padding:12px;text-align:center;">

            <div class="text-muted">
                🔥 ACTIVE NOW
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#10B981;
            ">
                {active}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                Live scanner
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m4:

    utc_hour = datetime.now(
        timezone.utc
    ).hour

    if 7 <= utc_hour < 16:
        session = "LONDON"
    elif 12 <= utc_hour < 21:
        session = "NEW YORK"
    else:
        session = "ASIA"

    st.markdown(
        f"""
        <div class="card-box"
             style="padding:12px;text-align:center;">

            <div class="text-muted">
                📡 SESSION
            </div>

            <div style="
                font-size:18px;
                font-weight:800;
                color:#F59E0B;
            ">
                {session}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                ● Active
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m5:

    dxy = get_live_price(
        "DXY"
    )

    dxy_text = (
        f"{dxy:.2f}"
        if dxy is not None
        else "N/A"
    )

    st.markdown(
        f"""
        <div class="card-box"
             style="padding:12px;text-align:center;">

            <div class="text-muted">
                💵 DXY
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#10B981;
            ">
                {dxy_text}
            </div>

            <div style="
                font-size:10px;
                color:#94A3B8;
            ">
                Live data
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


col_a, col_b, col_c = st.columns(3)


with col_a:

    if twelve_price is not None:

        st.success(
            f"Twelve Data CONNECTED\n\n"
            f"{selected_symbol}: "
            f"{twelve_price:.5f}"
        )

    else:

        st.error(
            "Twelve Data ERROR\n\n"
            "No price received."
        )


with col_b:

    if deriv_price is not None:

        st.success(
            f"Deriv CONNECTED\n\n"
            f"{selected_symbol}: "
            f"{deriv_price:.5f}"
        )

    else:

        st.error(
            "Deriv ERROR\n\n"
            "No Deriv tick received."
        )


with col_c:

    eur_price = get_live_price(
        "EURUSD"
    )

    if eur_price is not None:

        st.success(
            f"EUR/USD LIVE\n\n"
            f"{eur_price:.5f}"
        )

    else:

        st.error(
            "EUR/USD unavailable"
        )


# ============================================================
# MAIN SIGNAL
# ============================================================

left, right = st.columns(
    [1.35, 1]
)


with left:

    st.markdown(
        """
        <div class="card-box">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="text-muted">
            SIGNAL &nbsp; <b>{selected_symbol}</b>
        </div>

        <div class="signal-header">
            {SYMBOLS[selected_symbol]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if twelve_price is not None:

        st.markdown(
            f"""
            <div style="margin-top:8px;">
                <span class="signal-price">
                    {twelve_price:.5f}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if signal.get("ok"):

        bias = signal["bias"]
        score = signal["score"]
        grade = signal["grade"]

        if bias == "BUY":
            badge = (
                '<div class="badge-buy">'
                '🚀 STRONG BUY'
                '</div>'
            )

        elif bias == "SELL":
            badge = (
                '<div class="badge-sell">'
                '🔻 STRONG SELL'
                '</div>'
            )

        else:
            badge = (
                '<div style="
                    background:#161D2A;
                    border:1px solid #334155;
                    color:#CBD5E1;
                    padding:10px 20px;
                    border-radius:12px;
                    text-align:center;
                    font-weight:800;
                ">
                    WAIT / NEUTRAL
                </div>'
            )

        st.markdown(
            f"""
            <div style="
                display:flex;
                gap:15px;
                margin-top:20px;
                align-items:center;
            ">

                <div style="flex:1;">
                    {badge}
                </div>

                <div class="target-card">
                    <span class="text-muted">
                        GRADE
                    </span><br>

                    <b style="
                        color:#10B981;
                        font-size:18px;
                    ">
                        {grade}
                    </b>
                </div>

                <div class="target-card">
                    <span class="text-muted">
                        SCORE
                    </span><br>

                    <b style="
                        color:#FFFFFF;
                        font-size:18px;
                    ">
                        {score:.0f}
                    </b>
                </div>

                <div class="target-card">
                    <span class="text-muted">
                        R : R
                    </span><br>

                    <b style="
                        color:#FFFFFF;
                        font-size:18px;
                    ">
                        1 : {signal["rr"]:.2f}
                    </b>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<hr style='border-color:#1E293B;'>",
            unsafe_allow_html=True,
        )

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            st.metric(
                "TP1",
                f"{signal['tp1']:.5f}",
            )

        with p2:

            st.metric(
                "TP2",
                f"{signal['tp2']:.5f}",
            )

        with p3:

            st.metric(
                "TP3",
                f"{signal['tp3']:.5f}",
            )

        with p4:

            st.metric(
                "STOP LOSS",
                f"{signal['stop_loss']:.5f}",
            )

        st.markdown(
            f"""
            <div style="
                margin-top:15px;
                color:#94A3B8;
                font-size:12px;
            ">
                <b>Analysis:</b>
                {signal["reason"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.warning(
            signal.get(
                "reason",
                "Signal unavailable.",
            )
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# RIGHT PANEL
# ============================================================

with right:

    st.markdown(
        """
        <div class="card-box">
            <div class="text-muted">
                MARKET DATA
            </div>
        """,
        unsafe_allow_html=True,
    )

    quote = None

    try:
        quote = get_quote(
            selected_symbol
        )
    except Exception:
        quote = None

    if quote:

        fields = [
            ("Open", quote.get("open")),
            ("High", quote.get("high")),
            ("Low", quote.get("low")),
            ("Close", quote.get("close")),
        ]

        for label, value in fields:

            st.write(
                f"**{label}:** "
                f"{value if value is not None else 'N/A'}"
            )

    else:

        st.info(
            "Detailed quote unavailable."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# EXECUTION STATUS
# ============================================================

st.markdown(
    "### 🛡️ EXECUTION STATUS"
)

st.info(
    "Live execution is DISABLED. "
    "The application currently reads market data and "
    "generates signals only. No real order can be placed "
    "by this version."
)
