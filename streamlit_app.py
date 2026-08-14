"""
SEKWAILA OMEGA X
ANCIENT WISDOM. MODERN PROFIT.

Main Streamlit application.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# OPTIONAL AUTO REFRESH
# ============================================================

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(
        interval=15000,
        key="omega_refresh",
    )

except Exception:
    pass


# ============================================================
# IMPORTS
# ============================================================

from data.market_data import (
    get_live_price,
    get_candles,
    is_deriv_symbol,
)

from signals.signal_engine import (
    generate_omega_signal,
)

from twelve_data_adapter import (
    get_quote,
)

from deriv_adapter import (
    get_deriv_price,
    resolve_deriv_symbol,
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color:#0A0D14 !important;
    color:#E2E8F0;
}

.block-container {
    padding-top:1.2rem !important;
    padding-bottom:2rem !important;
}

[data-testid="stSidebar"] {
    background:#0F131C !important;
}

[data-testid="stSidebarContent"] {
    padding-top:1rem;
}

.card-box {
    background:#111622;
    border:1px solid #1E293B;
    border-radius:16px;
    padding:20px;
    margin-bottom:16px;
}

.signal-header {
    font-size:28px;
    font-weight:800;
    color:#FFFFFF;
    margin:0;
}

.signal-price {
    font-size:24px;
    font-weight:700;
    color:#10B981;
}

.badge-buy-glow {
    background:rgba(16,185,129,.10);
    border:2px solid #10B981;
    color:#10B981;
    padding:10px 20px;
    border-radius:12px;
    font-weight:800;
    font-size:18px;
    text-align:center;
}

.badge-sell-glow {
    background:rgba(239,68,68,.10);
    border:2px solid #EF4444;
    color:#EF4444;
    padding:10px 20px;
    border-radius:12px;
    font-weight:800;
    font-size:18px;
    text-align:center;
}

.badge-neutral {
    background:rgba(148,163,184,.08);
    border:2px solid #64748B;
    color:#94A3B8;
    padding:10px 20px;
    border-radius:12px;
    font-weight:800;
    font-size:18px;
    text-align:center;
}

.score-circle {
    width:85px;
    height:85px;
    border-radius:50%;
    border:5px solid #10B981;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

.score-value {
    font-size:24px;
    font-weight:800;
    color:#FFFFFF;
}

.score-label {
    font-size:9px;
    color:#94A3B8;
}

.target-card {
    background:#161D2A;
    border:1px solid #232D42;
    border-radius:10px;
    padding:12px;
    text-align:center;
}

.target-val {
    font-size:18px;
    font-weight:700;
}

.text-green {
    color:#10B981;
}

.text-red {
    color:#EF4444;
}

.text-yellow {
    color:#F59E0B;
}

.text-muted {
    color:#94A3B8;
    font-size:11px;
    text-transform:uppercase;
    font-weight:600;
}

.connection-good {
    color:#10B981;
    font-weight:700;
}

.connection-bad {
    color:#EF4444;
    font-weight:700;
}

.connection-neutral {
    color:#F59E0B;
    font-weight:700;
}

.small-card {
    background:#111622;
    border:1px solid #1E293B;
    border-radius:12px;
    padding:12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# MARKET LIST
# ============================================================

MARKETS = {
    "XAUUSD": "Gold — XAU/USD",
    "EURUSD": "Euro — EUR/USD",
    "GBPUSD": "Pound — GBP/USD",
    "USDJPY": "Dollar/Yen — USD/JPY",
    "AUDUSD": "Australian Dollar — AUD/USD",
    "USDCAD": "Dollar/Canadian — USD/CAD",
    "USDCHF": "Dollar/Swiss — USD/CHF",
    "NZDUSD": "New Zealand Dollar — NZD/USD",
    "BTCUSD": "Bitcoin — BTC/USD",

    "SP500": "S&P 500",
    "US30": "Dow Jones 30",
    "NAS100": "Nasdaq 100",

    "VOL100": "Volatility 100",
    "VOL75": "Volatility 75",
    "VOL50": "Volatility 50",
    "BOOM1000": "Boom 1000",
    "CRASH1000": "Crash 1000",
    "BOOM500": "Boom 500",
    "CRASH500": "Crash 500",
}


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:8px 0 18px 0;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
                letter-spacing:5px;
                color:#F5C542;
            ">
                ⚡ SEKWAILA
            </div>

            <div style="
                color:#64748B;
                font-size:13px;
                letter-spacing:5px;
                margin-top:4px;
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

    # --------------------------------------------------------
    # MARKET SELECTOR
    # --------------------------------------------------------

    st.markdown(
        '<div class="text-muted">MARKET / PAIR</div>',
        unsafe_allow_html=True,
    )

    selected_symbol = st.selectbox(
        "Market",
        list(MARKETS.keys()),
        format_func=lambda x: (
            f"{x} — {MARKETS[x]}"
        ),
        index=0,
        key="selected_market",
        label_visibility="collapsed",
    )

    st.session_state[
        "selected_symbol"
    ] = selected_symbol

    # --------------------------------------------------------
    # PROVIDER
    # --------------------------------------------------------

    provider = (
        "DERIV"
        if is_deriv_symbol(selected_symbol)
        else "TWELVE DATA"
    )

    st.markdown(
        f"""
        <div style="
            background:#111622;
            border:1px solid #1E293B;
            border-radius:10px;
            padding:10px;
            margin-top:10px;
        ">

            <div class="text-muted">
                DATA SOURCE
            </div>

            <div style="
                color:#10B981;
                font-size:14px;
                font-weight:800;
                margin-top:4px;
            ">
                ● {provider}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    st.markdown(
        '<div class="text-muted">ACCOUNT</div>',
        unsafe_allow_html=True,
    )

    account_balance = st.number_input(
        "Account Balance",
        min_value=0.0,
        value=500.0,
        step=50.0,
        format="%.2f",
        key="account_balance",
        label_visibility="collapsed",
    )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    st.markdown(
        '<div class="text-muted" style="margin-top:10px;">RISK %</div>',
        unsafe_allow_html=True,
    )

    risk_pct = st.slider(
        "Risk percentage",
        min_value=0.25,
        max_value=5.0,
        value=1.0,
        step=0.25,
        key="risk_percentage",
        label_visibility="collapsed",
    )

    risk_amount = (
        account_balance
        * risk_pct
        / 100
    )

    st.caption(
        f"Risk Amount: **${risk_amount:.2f}**"
    )

    # --------------------------------------------------------
    # LIVE EXECUTION
    # --------------------------------------------------------

    st.markdown("---")

    live_execution = st.toggle(
        "🔴 Live Trading",
        value=False,
        key="live_trading_enabled",
    )

    if live_execution:

        st.warning(
            "Live execution is not enabled by default. "
            "Only enable it after demo testing."
        )

    else:

        st.caption(
            "Live execution disabled."
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

st.markdown("---")


# ============================================================
# LIVE PRICE
# ============================================================

live_price = get_live_price(
    selected_symbol
)


# ============================================================
# CONNECTION STATUS
# ============================================================

st.markdown(
    "### 🔌 LIVE CONNECTIONS"
)

conn1, conn2, conn3 = st.columns(3)


# Twelve Data status.
with conn1:

    if is_deriv_symbol(selected_symbol):

        st.markdown(
            """
            <div class="small-card">
                <div class="text-muted">
                    Twelve Data
                </div>
                <div class="connection-neutral">
                    ● NOT USED
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        td_price = live_price

        if td_price is not None:

            st.markdown(
                f"""
                <div class="small-card">

                    <div class="text-muted">
                        Twelve Data
                    </div>

                    <div class="connection-good">
                        ● CONNECTED
                    </div>

                    <div style="
                        color:#E2E8F0;
                        margin-top:4px;
                    ">
                        {selected_symbol}:
                        <b>
                            {td_price:.5f}
                        </b>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="small-card">

                    <div class="text-muted">
                        Twelve Data
                    </div>

                    <div class="connection-bad">
                        ● ERROR
                    </div>

                    <div style="
                        color:#94A3B8;
                        margin-top:4px;
                    ">
                        No price received.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


# Deriv status.
with conn2:

    if is_deriv_symbol(selected_symbol):

        deriv_price = get_deriv_price(
            selected_symbol
        )

        if deriv_price is not None:

            st.markdown(
                f"""
                <div class="small-card">

                    <div class="text-muted">
                        Deriv
                    </div>

                    <div class="connection-good">
                        ● CONNECTED
                    </div>

                    <div style="
                        color:#E2E8F0;
                        margin-top:4px;
                    ">
                        {selected_symbol}:
                        <b>
                            {deriv_price:.5f}
                        </b>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="small-card">

                    <div class="text-muted">
                        Deriv
                    </div>

                    <div class="connection-bad">
                        ● ERROR
                    </div>

                    <div style="
                        color:#94A3B8;
                        margin-top:4px;
                    ">
                        No Deriv tick received.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.markdown(
            """
            <div class="small-card">

                <div class="text-muted">
                    Deriv
                </div>

                <div class="connection-neutral">
                    ● STANDBY
                </div>

                <div style="
                    color:#94A3B8;
                    margin-top:4px;
                ">
                    Used for synthetic markets.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# Current price.
with conn3:

    if live_price is not None:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="text-muted">
                    SELECTED MARKET
                </div>

                <div style="
                    color:#10B981;
                    font-size:20px;
                    font-weight:800;
                ">
                    {selected_symbol}
                </div>

                <div style="
                    color:#FFFFFF;
                    margin-top:3px;
                ">
                    {live_price:.5f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="small-card">

                <div class="text-muted">
                    SELECTED MARKET
                </div>

                <div class="connection-bad">
                    ● NO PRICE
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown("---")


# ============================================================
# SIGNAL
# ============================================================

signal = generate_omega_signal(
    selected_symbol,
    min_score=65.0,
    min_rr=1.5,
)


# ============================================================
# TOP METRICS
# ============================================================

buy_count = 0
sell_count = 0

if signal.get("bias") == "BUY":
    buy_count = 1

if signal.get("bias") == "SELL":
    sell_count = 1


m1, m2, m3, m4, m5 = st.columns(5)


with m1:

    st.markdown(
        f"""
        <div class="card-box"
             style="
                padding:12px;
                text-align:center;
             ">

            <div class="text-muted">
                🟢 BUY SETUPS
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#10B981;
            ">
                {buy_count}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                {selected_symbol if buy_count else "—"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m2:

    st.markdown(
        f"""
        <div class="card-box"
             style="
                padding:12px;
                text-align:center;
             ">

            <div class="text-muted">
                🔴 SELL SETUPS
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#EF4444;
            ">
                {sell_count}
            </div>

            <div style="
                font-size:10px;
                color:#EF4444;
            ">
                {selected_symbol if sell_count else "—"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m3:

    active = (
        signal.get("bias")
        in {"BUY", "SELL"}
    )

    st.markdown(
        f"""
        <div class="card-box"
             style="
                padding:12px;
                text-align:center;
             ">

            <div class="text-muted">
                🔥 ACTIVE NOW
            </div>

            <div style="
                font-size:26px;
                font-weight:800;
                color:#10B981;
            ">
                {1 if active else 0}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                {selected_symbol if active else "WAITING"}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m4:

    st.markdown(
        """
        <div class="card-box"
             style="
                padding:12px;
                text-align:center;
             ">

            <div class="text-muted">
                📡 SESSION
            </div>

            <div style="
                font-size:18px;
                font-weight:800;
                color:#F59E0B;
                margin-top:4px;
            ">
                GLOBAL
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                ● Market monitor
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with m5:

    st.markdown(
        f"""
        <div class="card-box"
             style="
                padding:12px;
                text-align:center;
             ">

            <div class="text-muted">
                💵 MARKET
            </div>

            <div style="
                font-size:20px;
                font-weight:800;
                color:#10B981;
            ">
                {selected_symbol}
            </div>

            <div style="
                font-size:10px;
                color:#10B981;
            ">
                ● LIVE
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN SIGNAL CARD
# ============================================================

if not signal.get("ok"):

    st.error(
        signal.get(
            "reason",
            "Signal engine could not generate data.",
        )
    )

else:

    bias = signal.get(
        "bias",
        "NEUTRAL",
    )

    entry = float(
        signal.get(
            "entry_price",
            live_price or 0,
        )
        or 0
    )

    sl = float(
        signal.get(
            "stop_loss",
            0,
        )
        or 0
    )

    tp1 = float(
        signal.get("tp1", 0)
        or 0
    )

    tp2 = float(
        signal.get("tp2", 0)
        or 0
    )

    tp3 = float(
        signal.get("tp3", 0)
        or 0
    )

    score = float(
        signal.get("score", 0)
        or 0
    )

    grade = signal.get(
        "grade",
        "N/A",
    )

    rr = float(
        signal.get("rr", 0)
        or 0
    )

    reason = signal.get(
        "reason",
        "No additional information.",
    )

    if bias == "BUY":
        badge = (
            '<div class="badge-buy-glow">'
            '🚀 STRONG BUY'
            '</div>'
        )

    elif bias == "SELL":
        badge = (
            '<div class="badge-sell-glow">'
            '🔻 STRONG SELL'
            '</div>'
        )

    else:
        badge = (
            '<div class="badge-neutral">'
            '⏸ WAIT / NO TRADE'
            '</div>'
        )

    c1, c2 = st.columns(
        [1.3, 1]
    )

    with c1:

        st.markdown(
            f"""
            <div class="card-box">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:flex-start;
                ">

                    <div>

                        <div class="text-muted">
                            SIGNAL &nbsp;
                            <b>{selected_symbol}</b>
                        </div>

                        <div class="signal-header">
                            {MARKETS.get(
                                selected_symbol,
                                selected_symbol
                            )}
                        </div>

                        <div style="
                            margin-top:8px;
                        ">

                            <span class="signal-price">
                                {entry:.5f}
                            </span>

                            <span style="
                                color:#94A3B8;
                                font-size:14px;
                                margin-left:10px;
                            ">
                                CURRENT:
                                <b style="
                                    color:#10B981;
                                ">
                                    {(
                                        live_price
                                        if live_price is not None
                                        else entry
                                    ):.5f}
                                </b>
                            </span>

                        </div>

                    </div>

                    <div class="score-circle">

                        <div class="score-value">
                            {score:.0f}
                        </div>

                        <div class="score-label">
                            SCORE
                        </div>

                    </div>

                </div>

                <div style="
                    display:flex;
                    gap:15px;
                    margin-top:20px;
                    align-items:center;
                ">

                    <div style="flex:1;">
                        {badge}
                    </div>

                    <div style="
                        background:#161D2A;
                        padding:10px 16px;
                        border-radius:10px;
                        border:1px solid #232D42;
                        text-align:center;
                    ">

                        <span class="text-muted">
                            GRADE
                        </span>

                        <br>

                        <b style="
                            color:#10B981;
                            font-size:18px;
                        ">
                            {grade}
                        </b>

                    </div>

                    <div style="
                        background:#161D2A;
                        padding:10px 16px;
                        border-radius:10px;
                        border:1px solid #232D42;
                        text-align:center;
                    ">

                        <span class="text-muted">
                            R : R
                        </span>

                        <br>

                        <b style="
                            color:#FFFFFF;
                            font-size:18px;
                        ">
                            1 : {rr:.2f}
                        </b>

                    </div>

                </div>

                <hr style="
                    border-color:#1E293B;
                    margin:20px 0;
                ">

                <div style="
                    display:grid;
                    grid-template-columns:
                        repeat(4, 1fr);
                    gap:10px;
                ">

                    <div class="target-card">

                        <div class="text-muted">
                            TP1
                        </div>

                        <div class="target-val text-green">
                            {tp1:.5f}
                        </div>

                    </div>

                    <div class="target-card">

                        <div class="text-muted">
                            TP2
                        </div>

                        <div class="target-val text-green">
                            {tp2:.5f}
                        </div>

                    </div>

                    <div class="target-card">

                        <div class="text-muted">
                            TP3
                        </div>

                        <div class="target-val text-green">
                            {tp3:.5f}
                        </div>

                    </div>

                    <div class="target-card"
                         style="
                            border-left:
                            3px solid #EF4444;
                         ">

                        <div class="text-muted">
                            STOP LOSS
                        </div>

                        <div class="target-val text-red">
                            {sl:.5f}
                        </div>

                    </div>

                </div>

                <div style="
                    margin-top:16px;
                    color:#94A3B8;
                    font-size:12px;
                ">
                    <b>Analysis:</b>
                    {reason}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # MULTI-TIMEFRAME CARD
    # ========================================================

    with c2:

        st.markdown(
            """
            <div class="card-box">

                <div class="text-muted"
                     style="margin-bottom:12px;">
                    MULTI-TIMEFRAME ANALYSIS
                </div>

                <table style="
                    width:100%;
                    color:#E2E8F0;
                    font-size:13px;
                    border-collapse:collapse;
                ">

                    <thead>

                        <tr style="
                            border-bottom:
                            1px solid #1E293B;
                            text-align:left;
                            color:#94A3B8;
                        ">

                            <th style="padding:8px;">
                                TF
                            </th>

                            <th style="padding:8px;">
                                BIAS
                            </th>

                            <th style="padding:8px;">
                                STRUCTURE
                            </th>

                            <th style="padding:8px;">
                                STATUS
                            </th>

                        </tr>

                    </thead>

                    <tbody>

                        <tr>
                            <td style="padding:10px;">
                                1D
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                {bias}
                            </td>

                            <td style="padding:10px;">
                                SMC
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                Active
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:10px;">
                                4H
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                {bias}
                            </td>

                            <td style="padding:10px;">
                                Structure
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                Active
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:10px;">
                                1H
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                {bias}
                            </td>

                            <td style="padding:10px;">
                                BOS / CHoCH
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                Monitoring
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:10px;">
                                15M
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                {bias}
                            </td>

                            <td style="padding:10px;">
                                Liquidity
                            </td>

                            <td style="
                                padding:10px;
                                color:#10B981;
                            ">
                                Monitoring
                            </td>
                        </tr>

                    </tbody>

                </table>

            </div>
            """.replace(
                "{bias}",
                str(bias),
            ),
            unsafe_allow_html=True,
        )


# ============================================================
# NAVIGATION PAGES
# ============================================================

if page == "📊 Market Scanner":

    st.markdown("## 📊 Market Scanner")

    scanner_rows = []

    for symbol in list(MARKETS.keys())[:12]:

        try:
            price = get_live_price(symbol)

            scanner_rows.append(
                {
                    "Symbol": symbol,
                    "Market": MARKETS[symbol],
                    "Price": (
                        round(price, 5)
                        if price is not None
                        else "N/A"
                    ),
                }
            )

        except Exception:
            scanner_rows.append(
                {
                    "Symbol": symbol,
                    "Market": MARKETS[symbol],
                    "Price": "ERROR",
                }
            )

    st.dataframe(
        scanner_rows,
        use_container_width=True,
        hide_index=True,
    )


elif page == "📒 Trade Journal":

    st.markdown("## 📒 Trade Journal")

    st.info(
        "Trade journal storage is available through persistence.py."
    )


elif page == "📉 Performance":

    st.markdown("## 📉 Performance")

    try:

        from persistence import get_performance

        performance = get_performance()

        if performance.get("has_data"):

            a, b, c = st.columns(3)

            a.metric(
                "Resolved",
                performance["resolved"],
            )

            b.metric(
                "Wins",
                performance["wins"],
            )

            c.metric(
                "Win Rate",
                f'{performance["win_rate"]}%',
            )

        else:

            st.info(
                "No resolved trades have been recorded yet."
            )

    except Exception as exc:

        st.error(
            f"Performance module error: {exc}"
        )


elif page == "📲 Telegram Alerts":

    st.markdown("## 📲 Telegram Alerts")

    st.info(
        "Telegram alerts can be connected through telegram_bot.py."
    )


elif page == "⚙️ Settings":

    st.markdown("## ⚙️ Settings")

    st.write(
        "Current market:",
        selected_symbol,
    )

    st.write(
        "Provider:",
        provider,
    )

    st.write(
        "Risk:",
        f"{risk_pct:.2f}%",
    )

    st.write(
        "Risk amount:",
        f"${risk_amount:.2f}",
    )


elif page == "❓ Help":

    st.markdown("## ❓ Help")

    st.markdown(
        """
        **SEKWAILA OMEGA X**

        Select a market from the sidebar.

        Normal markets use Twelve Data.

        Synthetic markets use Deriv.

        The signal engine calculates entry,
        stop loss and targets dynamically
        from the selected market's data.

        Live trading remains disabled by default.
        """
    )


elif page == "🧠 AI Narrator":

    st.markdown("## 🧠 AI Narrator")

    st.info(
        "AI narration can be connected to your ai_provider.py module."
    )


elif page == "📰 News Intelligence":

    st.markdown("## 📰 News Intelligence")

    st.info(
        "News intelligence can be connected to news.py."
    )


elif page == "🔥 Heatmap":

    st.markdown("## 🔥 Heatmap")

    st.info(
        "Heatmap module ready for market-strength integration."
    )


elif page == "📈 Multi-Timeframe":

    st.markdown("## 📈 Multi-Timeframe")

    st.info(
        "The dashboard currently displays the selected market's SMC state."
    )


elif page == "🔗 Correlation Matrix":

    st.markdown("## 🔗 Correlation Matrix")

    st.info(
        "Correlation analysis can be connected to the market scanner."
    )
