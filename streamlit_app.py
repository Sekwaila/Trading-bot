"""
SEKWAILA OMEGA X — STREAMLIT DASHBOARD
Full replacement for streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import (
    ASSETS,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
)

# Support either project structure:
#   engine.py
# OR
#   signals/signal_engine.py
try:
    from engine import (
        generate_omega_signal,
        grade,
        fetch_usdzar_rate,
        compute_live_correlation_matrix,
        calculate_position_size,
    )
except ImportError:
    from signals.signal_engine import (
        generate_omega_signal,
        grade,
        fetch_usdzar_rate,
        compute_live_correlation_matrix,
        calculate_position_size,
    )

import database


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');

    .stApp {
        background-color: #0c0a07;
        color: #e5d5b7;
        font-family: 'Inter', sans-serif;
    }

    .title-cinzel {
        font-family: 'Cinzel', serif;
        color: #dfb15b;
        letter-spacing: 2px;
    }

    .css-card {
        background-color: #14100b;
        border: 1px solid #3b2d18;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }

    .signal-box-buy {
        background: linear-gradient(180deg, #0d1a0e 0%, #060d07 100%);
        border: 1px solid #00e676;
        border-radius: 10px;
        padding: 20px;
    }

    .signal-box-sell {
        background: linear-gradient(180deg, #1f0b0b 0%, #0a0404 100%);
        border: 1px solid #ff5252;
        border-radius: 10px;
        padding: 20px;
    }

    .signal-box-blocked {
        background: linear-gradient(180deg, #211c12 0%, #0c0a07 100%);
        border: 1px solid #ffb74d;
        border-radius: 10px;
        padding: 20px;
    }

    .text-gold {
        color: #dfb15b !important;
    }

    .text-green {
        color: #00e676 !important;
        font-weight: bold;
    }

    .text-red {
        color: #ff5252 !important;
        font-weight: bold;
    }

    .text-orange {
        color: #ffb74d !important;
        font-weight: bold;
    }

    div[data-testid="stMetric"] {
        background-color: #14100b;
        border: 1px solid #3b2d18;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

database.init_db()


# ============================================================
# CACHED SIGNAL
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def cached_signal(symbol, ticker, min_tf, min_score, min_rr):
    return generate_omega_signal(
        symbol,
        ticker,
        min_tf,
        min_score,
        min_rr,
    )


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def render_data_down(res):
    st.markdown(
        f"""
        <div class="signal-box-blocked">
            <h3 class="title-cinzel" style="color:#ff5252;">
                ⚠ DATA UNAVAILABLE — {res.get("symbol", "")}
            </h3>
            <p style="font-size:12px; color:#ccc;">
                {res.get("reason", "Unknown error")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_bias_label(bull_score, bear_score):
    difference = bull_score - bear_score

    if difference >= 25:
        return "STRONG BULL"

    if difference <= -25:
        return "STRONG BEAR"

    if bull_score > bear_score:
        return "LEAN BULL"

    if bear_score > bull_score:
        return "LEAN BEAR"

    return "NEUTRAL"


def get_bias_color(label):
    if "BULL" in label:
        return "#00e676"

    if "BEAR" in label:
        return "#ff5252"

    return "#dfb15b"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "<h2 class='title-cinzel'>👑 SEKWAILA</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<small style='color:#888;'>OMEGA X — LIVE ENGINE</small>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    page = st.radio(
        "MODULE",
        [
            "Dashboard",
            "Market Scanner",
            "Heatmap",
            "AI Narrator",
            "Multi-Timeframe",
            "Correlation Matrix",
            "Trade Journal",
            "Performance",
            "Settings",
        ],
        index=0,
    )

    st.markdown("---")

    account_zar = st.number_input(
        "Account (ZAR)",
        min_value=100.0,
        value=1000.0,
        step=100.0,
    )

    risk_pct = st.slider(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
    )

    st.markdown("---")

    st.caption(
        f"Engine thresholds: "
        f"{DEFAULT_MIN_TF_AGREEMENT}/4 TF agreement, "
        f"{DEFAULT_MIN_SCORE} min score, "
        f"{DEFAULT_MIN_RR} min R:R"
    )

    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()

    st.caption(
        "⚠️ Informational only. Not financial advice. "
        "Score is a rules-based heuristic, not a backtested win rate."
    )


# ============================================================
# USD/ZAR
# ============================================================

try:
    usdzar_rate = fetch_usdzar_rate()
except Exception:
    usdzar_rate = None


account_balance_usd = (
    account_zar / usdzar_rate
    if usdzar_rate
    else None
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <h1 class='title-cinzel'
        style='text-align:center; margin:0;'>
        SEKWAILA OMEGA X
    </h1>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <p style='text-align:center;
              color:#dfb15b;
              font-size:11px;
              letter-spacing:2px;'>
        LIVE ENGINE — DASHBOARD AND TELEGRAM ALERTS SHARE THE SAME CODE
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    asset_choice = st.selectbox(
        "Active Asset Focus",
        list(ASSETS.keys()),
        index=0,
    )

    res = cached_signal(
        asset_choice,
        ASSETS[asset_choice],
        DEFAULT_MIN_TF_AGREEMENT,
        DEFAULT_MIN_SCORE,
        DEFAULT_MIN_RR,
    )

    if not res.get("ok"):
        render_data_down(res)
        st.stop()

    # --------------------------------------------------------
    # MAIN COLUMNS
    # --------------------------------------------------------

    col_left, col_center, col_right = st.columns(
        [1.1, 2.4, 1.2]
    )

    # ========================================================
    # LEFT COLUMN
    # ========================================================

    with col_left:

        bull_pct = safe_float(res.get("bull_score"))
        bear_pct = safe_float(res.get("bear_score"))

        market_bias_label = get_bias_label(
            bull_pct,
            bear_pct,
        )

        market_bias_color = get_bias_color(
            market_bias_label
        )

        # ----------------------------------------------------
        # BULL / BEAR
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    ⚔️ BULL / BEAR SCORE
                </small>

                <div style="margin-top:6px;">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        font-size:11px;
                    ">
                        <span>BULL SCORE</span>
                        <b class="text-green">
                            {bull_pct:.1f}%
                        </b>
                    </div>

                    <div style="
                        background:#2a2214;
                        border-radius:4px;
                        height:8px;
                        margin-bottom:6px;
                    ">
                        <div style="
                            background:#00e676;
                            width:{min(max(bull_pct, 0), 100)}%;
                            height:8px;
                            border-radius:4px;
                        "></div>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        font-size:11px;
                    ">
                        <span>BEAR SCORE</span>
                        <b class="text-red">
                            {bear_pct:.1f}%
                        </b>
                    </div>

                    <div style="
                        background:#2a2214;
                        border-radius:4px;
                        height:8px;
                    ">
                        <div style="
                            background:#ff5252;
                            width:{min(max(bear_pct, 0), 100)}%;
                            height:8px;
                            border-radius:4px;
                        "></div>
                    </div>

                </div>

                <div style="
                    margin-top:10px;
                    text-align:center;
                    padding:6px;
                    border-radius:6px;
                    background:#0c0a07;
                    border:1px solid {market_bias_color};
                ">

                    <small style="color:#888;">
                        MARKET BIAS
                    </small>

                    <br/>

                    <b style="
                        color:{market_bias_color};
                        font-size:13px;
                    ">
                        {market_bias_label}
                    </b>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        vwap_status = res.get("vwap_status", "UNKNOWN")
        rsi = safe_float(res.get("rsi"))
        macd_trend = res.get("macd_trend", "UNKNOWN")
        ema_cross = res.get("ema_cross", "UNKNOWN")
        atr = safe_float(res.get("atr"))
        vol_status = res.get("vol_status", "UNKNOWN")
        trend_strong = bool(res.get("trend_strong", False))

        vwap_color = (
            "#00e676"
            if vwap_status == "ABOVE"
            else "#ff5252"
        )

        macd_color = (
            "#00e676"
            if macd_trend == "BULLISH"
            else "#ff5252"
        )

        ema_color = (
            "#00e676"
            if ema_cross == "BULLISH"
            else "#ff5252"
        )

        trend_color = (
            "#00e676"
            if trend_strong
            else "#ffb74d"
        )

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    📊 INDICATOR PANEL
                </small>

                <div style="
                    font-size:11px;
                    margin-top:6px;
                    line-height:1.9;
                ">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            Price/VWAP
                        </span>
                        <b style="color:{vwap_color};">
                            {vwap_status}
                        </b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            RSI (14)
                        </span>
                        <b>{rsi:.1f}</b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            MACD Trend
                        </span>
                        <b style="color:{macd_color};">
                            {macd_trend}
                        </b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            ADX Power
                        </span>
                        <b>
                            {res.get("regime", {}).get("adx", "-")}
                        </b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            EMA Cross
                        </span>
                        <b style="color:{ema_color};">
                            {ema_cross}
                        </b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            ATR 14
                        </span>
                        <b>{atr:.2f}</b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            Vol Status
                        </span>
                        <b>{vol_status}</b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            Trend Strength
                        </span>
                        <b style="color:{trend_color};">
                            {"STRONG" if trend_strong else "WEAK"}
                        </b>
                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">
                        <span style="color:#aaa;">
                            Status
                        </span>
                        <b class="text-gold">
                            {
                                res.get("bias")
                                if res.get("bias") != "NEUTRAL"
                                else "WAIT"
                            }
                        </b>
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # REGIME
        # ----------------------------------------------------

        regime = res.get("regime", {})

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    📈 REGIME
                </small>

                <h4 style="
                    color:#00e676;
                    margin:4px 0;
                ">
                    {regime.get("regime", "-")}
                </h4>

                <div style="
                    font-size:11px;
                    color:#aaa;
                ">
                    ADX:
                    <b>{regime.get("adx", "-")}</b>
                    |
                    Vol Ratio:
                    <b>{regime.get("vol_ratio", "-")}</b>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # SESSION
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    🕐 SESSION
                </small>

                <div style="
                    font-size:12px;
                    margin-top:4px;
                ">
                    {res.get("session", "-")}
                </div>

                <div style="
                    font-size:10px;
                    color:#aaa;
                ">
                    Quality:
                    {res.get("session_quality", "-")}%
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # PREMIUM / DISCOUNT
        # ----------------------------------------------------

        pd_info = res.get("pd_info", {})

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    💎 PREMIUM/DISCOUNT
                </small>

                <div style="
                    font-size:12px;
                    margin-top:4px;
                ">
                    {res.get("pd_zone", "-")}
                </div>

                <div style="
                    font-size:10px;
                    color:#aaa;
                ">
                    Equilibrium:
                    {safe_float(
                        pd_info.get("equilibrium")
                    ): .4f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # POSITION SIZE
        # ----------------------------------------------------

        if res.get("bias") in ("BUY", "SELL"):

            try:
                pos_size = calculate_position_size(
                    account_balance_usd,
                    risk_pct,
                    res.get("entry"),
                    res.get("stop"),
                )
            except Exception:
                pos_size = None

        else:
            pos_size = None

        if usdzar_rate is None:

            st.markdown(
                """
                <div class="css-card">
                    <small class="text-gold">
                        💰 POSITION SIZE
                    </small>

                    <div style="
                        font-size:10px;
                        color:#ff5252;
                    ">
                        USDZAR feed unavailable.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif pos_size is None:

            st.markdown(
                """
                <div class="css-card">
                    <small class="text-gold">
                        💰 POSITION SIZE
                    </small>

                    <div style="
                        font-size:10px;
                        color:#aaa;
                    ">
                        No active signal.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            risk_amount = (
                account_zar * risk_pct / 100
            )

            st.markdown(
                f"""
                <div class="css-card">

                    <small class="text-gold">
                        💰 POSITION SIZE
                    </small>

                    <div style="
                        font-size:11px;
                        margin-top:6px;
                    ">

                        <div>
                            Risk:
                            <b class="text-gold">
                                R{risk_amount:,.2f}
                            </b>
                        </div>

                        <div>
                            SL Distance:
                            <b>
                                {safe_float(
                                    pos_size.get("stop_distance")
                                ):.2f}
                            </b>
                        </div>

                        <div>
                            Size:
                            <b class="text-green">
                                {pos_size.get("lots", "-")} lots
                            </b>
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # ========================================================
    # CENTER COLUMN
    # ========================================================

    with col_center:

        bias = res.get("bias", "NEUTRAL")

        if bias == "BUY":

            box_class = "signal-box-buy"
            bias_display = "CONFIRMED BUY ↑"
            bias_color = "text-green"

        elif bias == "SELL":

            box_class = "signal-box-sell"
            bias_display = "CONFIRMED SELL ↓"
            bias_color = "text-red"

        else:

            box_class = "signal-box-blocked"
            bias_display = "NEUTRAL / NO SETUP"
            bias_color = "text-gold"

        reason = res.get("reason", "")

        reason_html = (
            f"""
            <p style="
                font-size:10px;
                color:#ffb74d;
                margin-top:4px;
            ">
                {reason}
            </p>
            """
            if reason
            else ""
        )

        score = safe_float(res.get("score"))

        st.markdown(
            f"""
            <div class="{box_class}">

                <div style="
                    display:flex;
                    justify-content:space-between;
                ">

                    <div>

                        <h2 style="
                            margin:0;
                            color:#fff;
                        "
                        class="title-cinzel">
                            {res.get("symbol", asset_choice)}
                        </h2>

                        <small style="color:#aaa;">
                            SCORE-BASED SIGNAL
                            (RULES-BASED, NOT BACKTESTED)
                        </small>

                    </div>

                    <div style="text-align:right;">

                        <small style="color:#aaa;">
                            SCORE
                        </small>

                        <h2 style="margin:0;"
                            class="text-gold">
                            {score:.1f}/100
                            ({grade(score)})
                        </h2>

                    </div>

                </div>

                <hr style="
                    border-color:#3b2d18;
                    margin:10px 0;
                "/>

                <h1 class="{bias_color}"
                    style="
                        margin:2px 0;
                        font-family:'Cinzel',serif;
                    ">
                    {bias_display}
                </h1>

                {reason_html}

                <br/>

                <div style="
                    display:flex;
                    justify-content:space-around;
                    text-align:center;
                ">

                    <div>
                        <small style="color:#888;">
                            ENTRY
                        </small>
                        <br/>
                        <b>
                            {safe_float(res.get("entry")):.4f}
                        </b>
                    </div>

                    <div>
                        <small style="color:#888;">
                            TP1
                        </small>
                        <br/>
                        <b class="text-green">
                            {safe_float(res.get("tp1")):.4f}
                        </b>
                    </div>

                    <div>
                        <small style="color:#888;">
                            TP2
                        </small>
                        <br/>
                        <b class="text-green">
                            {safe_float(res.get("tp2")):.4f}
                        </b>
                    </div>

                    <div>
                        <small style="color:#888;">
                            TP3
                        </small>
                        <br/>
                        <b class="text-green">
                            {safe_float(res.get("tp3")):.4f}
                        </b>
                    </div>

                    <div>
                        <small style="color:#888;">
                            STOP
                        </small>
                        <br/>
                        <b class="text-red">
                            {safe_float(res.get("stop")):.4f}
                        </b>
                    </div>

                </div>

                <div style="
                    text-align:center;
                    margin-top:8px;
                    font-size:11px;
                    color:#aaa;
                ">
                    R:R (to TP2):
                    {safe_float(res.get("rr")):.2f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # CHART
        # ----------------------------------------------------

        data = res.get("data", {})
        df_chart = data.get("15M")

        if df_chart is not None and not df_chart.empty:

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df_chart.index,
                        open=df_chart["Open"],
                        high=df_chart["High"],
                        low=df_chart["Low"],
                        close=df_chart["Close"],
                        increasing_line_color="#00e676",
                        decreasing_line_color="#ff5252",
                    )
                ]
            )

            # ------------------------------------------------
            # ORDER BLOCK
            # ------------------------------------------------

            ob_zone = res.get("ob_zone")

            if ob_zone:

                ob_min, ob_max = ob_zone

                ob_type = res.get(
                    "ob_type",
                    "ORDER BLOCK",
                )

                ob_invalidated = res.get(
                    "ob_invalidated",
                    False,
                )

                ob_mitigated = res.get(
                    "ob_mitigated",
                    False,
                )

                ob_state = (
                    "INVALIDATED"
                    if ob_invalidated
                    else (
                        "MITIGATED"
                        if ob_mitigated
                        else "UNMITIGATED"
                    )
                )

                ob_color = (
                    "rgba(0,230,118,0.15)"
                    if "BULLISH" in ob_type
                    else "rgba(255,82,82,0.15)"
                )

                fig.add_hrect(
                    y0=ob_min,
                    y1=ob_max,
                    fillcolor=ob_color,
                    line_width=1,
                    annotation_text=(
                        f"{ob_type} ({ob_state})"
                    ),
                    annotation_position="bottom left",
                )

            # ------------------------------------------------
            # FVG
            # ------------------------------------------------

            fvg = res.get("fvg")

            if fvg is not None:

                fz = fvg.get("zone")

                if fz:

                    fig.add_hrect(
                        y0=fz[0],
                        y1=fz[1],
                        fillcolor=(
                            "rgba(223,177,91,0.18)"
                        ),
                        line_width=1,
                        line_dash="dot",
                        annotation_text=(
                            f"{fvg.get('type', 'FVG')} "
                            "(unfilled)"
                        ),
                        annotation_position="top left",
                    )

            # ------------------------------------------------
            # PREMIUM / DISCOUNT
            # ------------------------------------------------

            pd_info = res.get("pd_info", {})

            equilibrium = pd_info.get("equilibrium")
            swing_high = pd_info.get("swing_high")
            swing_low = pd_info.get("swing_low")

            if (
                equilibrium is not None
                and swing_high is not None
                and swing_low is not None
            ):

                fig.add_hrect(
                    y0=equilibrium,
                    y1=swing_high,
                    fillcolor=(
                        "rgba(255,82,82,0.08)"
                    ),
                    line_width=0,
                )

                fig.add_hrect(
                    y0=swing_low,
                    y1=equilibrium,
                    fillcolor=(
                        "rgba(66,133,244,0.08)"
                    ),
                    line_width=0,
                )

                fig.add_hline(
                    y=equilibrium,
                    line_width=1,
                    line_dash="dash",
                    line_color=(
                        "rgba(223,177,91,0.6)"
                    ),
                    annotation_text="Equilibrium",
                )

            # ------------------------------------------------
            # EQUAL HIGHS
            # ------------------------------------------------

            for eqh in res.get("eq_highs", [])[-3:]:

                fig.add_hline(
                    y=eqh,
                    line_width=1,
                    line_dash="dot",
                    line_color=(
                        "rgba(255,82,82,0.55)"
                    ),
                    annotation_text="EQH",
                    annotation_position="top right",
                )

            # ------------------------------------------------
            # EQUAL LOWS
            # ------------------------------------------------

            for eql in res.get("eq_lows", [])[-3:]:

                fig.add_hline(
                    y=eql,
                    line_width=1,
                    line_dash="dot",
                    line_color=(
                        "rgba(0,230,118,0.55)"
                    ),
                    annotation_text="EQL",
                    annotation_position="bottom right",
                )

            # ------------------------------------------------
            # STRUCTURE
            # ------------------------------------------------

            structure = res.get(
                "structure",
                "STRUCTURE",
            )

            structure_label = structure.replace(
                "_WEAK",
                " (weak)",
            )

            entry = safe_float(
                res.get("entry")
            )

            if entry:

                fig.add_annotation(
                    x=df_chart.index[-1],
                    y=entry,
                    text=structure_label,
                    showarrow=True,
                    arrowhead=2,
                    font=dict(
                        color="#dfb15b",
                        size=11,
                    ),
                    bgcolor=(
                        "rgba(12,10,7,0.85)"
                    ),
                    bordercolor="#3b2d18",
                )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#14100b",
                plot_bgcolor="#14100b",
                height=420,
                margin=dict(
                    l=10,
                    r=10,
                    t=10,
                    b=10,
                ),
                xaxis_rangeslider_visible=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        else:

            st.warning(
                "15M chart data unavailable."
            )

    # ========================================================
    # RIGHT COLUMN
    # ========================================================

    with col_right:

        ob_invalidated = res.get(
            "ob_invalidated",
            False,
        )

        ob_mitigated = res.get(
            "ob_mitigated",
            False,
        )

        ob_state = (
            "INVALIDATED"
            if ob_invalidated
            else (
                "MITIGATED"
                if ob_mitigated
                else "UNMITIGATED"
            )
        )

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    💡 REASONING
                </small>

                <p style="
                    font-size:11px;
                    color:#ccc;
                    margin-top:6px;
                    line-height:1.4;
                ">

                    Structure:
                    {res.get("structure", "-")}.
                    {res.get("sweep_detail", "")}

                    Order block is
                    {ob_state}
                    {res.get("ob_type", "")}.

                    Trend strength:
                    {
                        res.get("trend_detail", "not confirmed")
                        if res.get("trend_strong")
                        else "not confirmed"
                    }.

                    Zone:
                    {res.get("pd_zone", "-")}.

                    Session:
                    {res.get("session", "-")}
                    ({res.get("session_quality", "-")}% quality).

                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        trend_class = (
            "text-green"
            if res.get("trend_strong")
            else "text-orange"
        )

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    📶 TREND STRENGTH
                </small>

                <br/>

                <span class="{trend_class}"
                      style="font-size:11px;">

                    {
                        "CONFIRMED"
                        if res.get("trend_strong")
                        else "NOT CONFIRMED"
                    }

                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )

        integrity_rows = ""

        for tf, value in res.get(
            "data_integrity",
            {},
        ).items():

            integrity_color = (
                "#00e676"
                if value == "LIVE"
                else "#ff5252"
            )

            integrity_rows += (
                f"""
                <div>
                    {tf}:
                    <b style="color:{integrity_color};">
                        {value}
                    </b>
                </div>
                """
            )

        st.markdown(
            f"""
            <div class="css-card">

                <small class="text-gold">
                    📡 DATA INTEGRITY
                </small>

                <div style="
                    font-size:10px;
                    margin-top:6px;
                ">
                    {integrity_rows}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MARKET SCANNER
# ============================================================

elif page == "Market Scanner":

    st.subheader("📊 Live Market Scanner")

    st.caption(
        "Every row calls generate_omega_signal() — "
        "the same engine used by the worker."
    )

    rows = []

    progress = st.progress(
        0,
        text="Scanning...",
    )

    total_assets = len(ASSETS)

    for i, (label, ticker) in enumerate(
        ASSETS.items()
    ):

        try:

            r = cached_signal(
                label,
                ticker,
                DEFAULT_MIN_TF_AGREEMENT,
                DEFAULT_MIN_SCORE,
                DEFAULT_MIN_RR,
            )

            if r.get("ok"):

                rows.append(
                    {
                        "Asset": label,
                        "Signal": r.get("bias"),
                        "Score": r.get("score"),
                        "Grade": grade(
                            safe_float(
                                r.get("score")
                            )
                        ),
                        "R:R": round(
                            safe_float(
                                r.get("rr")
                            ),
                            2,
                        ),
                        "Session": r.get(
                            "session",
                            "-",
                        ),
                        "Zone": r.get(
                            "pd_zone",
                            "-",
                        ),
                        "1D": r.get(
                            "tf_biases",
                            {},
                        ).get("1D", "-"),
                        "4H": r.get(
                            "tf_biases",
                            {},
                        ).get("4H", "-"),
                        "1H": r.get(
                            "tf_biases",
                            {},
                        ).get("1H", "-"),
                        "15M": r.get(
                            "tf_biases",
                            {},
                        ).get("15M", "-"),
                    }
                )

            else:

                rows.append(
                    {
                        "Asset": label,
                        "Signal": "DATA DOWN",
                        "Score": 0,
                        "Grade": "-",
                        "R:R": None,
                        "Session": "-",
                        "Zone": "-",
                        "1D": "-",
                        "4H": "-",
                        "1H": "-",
                        "15M": "-",
                    }
                )

        except Exception as e:

            rows.append(
                {
                    "Asset": label,
                    "Signal": "ERROR",
                    "Score": 0,
                    "Grade": "-",
                    "R:R": None,
                    "Session": "-",
                    "Zone": "-",
                    "1D": "-",
                    "4H": "-",
                    "1H": "-",
                    "15M": "-",
                }
            )

        progress.progress(
            (i + 1) / total_assets,
            text=f"Scanned {label}",
        )

    progress.empty()

    table = pd.DataFrame(rows)

    if not table.empty:

        table = table.sort_values(
            "Score",
            ascending=False,
        )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# HEATMAP
# ============================================================

elif page == "Heatmap":

    st.subheader("🔥 Market Strength Heatmap")

    for label, ticker in ASSETS.items():

        try:

            r = cached_signal(
                label,
                ticker,
                DEFAULT_MIN_TF_AGREEMENT,
                DEFAULT_MIN_SCORE,
                DEFAULT_MIN_RR,
            )

        except Exception:

            r = {
                "ok": False
            }

        if not r.get("ok"):

            st.progress(
                0,
                text=f"{label} — DATA DOWN",
            )

            continue

        score = safe_float(
            r.get("score")
        )

        direction = (
            "Bullish"
            if r.get("bias") == "BUY"
            else (
                "Bearish"
                if r.get("bias") == "SELL"
                else "Neutral"
            )
        )

        regime = r.get(
            "regime",
            {},
        ).get(
            "regime",
            "-",
        )

        st.progress(
            min(max(score / 100, 0), 1),
            text=(
                f"{label} — "
                f"{score:.1f}/100 "
                f"{direction} "
                f"({regime})"
            ),
        )


# ============================================================
# AI NARRATOR
# ============================================================

elif page == "AI Narrator":

    st.subheader("🤖 Katlego AI Narrator")

    asset_choice = st.selectbox(
        "Asset",
        list(ASSETS.keys()),
        key="narrator_asset",
    )

    r = cached_signal(
        asset_choice,
        ASSETS[asset_choice],
        DEFAULT_MIN_TF_AGREEMENT,
        DEFAULT_MIN_SCORE,
        DEFAULT_MIN_RR,
    )

    if not r.get("ok"):

        render_data_down(r)

    else:

        st.markdown(
            f"### {r.get('symbol', asset_choice)} "
            f"— {r.get('bias', 'NEUTRAL')}"
        )

        ob_state_label = (
            "INVALIDATED"
            if r.get("ob_invalidated")
            else (
                "MITIGATED"
                if r.get("ob_mitigated")
                else "UNMITIGATED"
            )
        )

        regime = r.get(
            "regime",
            {},
        )

        narrative = (
            f"{r.get('symbol', asset_choice)} "
            f"shows {r.get('structure', '-')} "
            f"on the 15M timeframe, in a "
            f"{regime.get('regime', '-')} regime "
            f"(ADX {regime.get('adx', '-')}). "
            f"{r.get('sweep_detail', '')}. "
            f"Price sits in the "
            f"{r.get('pd_zone', '-')} zone relative "
            f"to the recent range equilibrium. "
            f"The order block is "
            f"{ob_state_label} "
            f"{r.get('ob_type', '')}. "
            f"Trend strength is "
            f"{'confirmed' if r.get('trend_strong') else 'not confirmed'}. "
            f"Current session: "
            f"{r.get('session', '-')} "
            f"({r.get('session_quality', '-')}% quality). "
            f"Composite score: "
            f"{safe_float(r.get('score')):.1f}/100 "
            f"(Grade "
            f"{grade(safe_float(r.get('score')))})."
        )

        st.write(narrative)

        st.info(
            "Generated directly from the computed values above."
        )


# ============================================================
# MULTI-TIMEFRAME
# ============================================================

elif page == "Multi-Timeframe":

    st.subheader("📈 Multi-Timeframe Alignment")

    asset_choice = st.selectbox(
        "Asset",
        list(ASSETS.keys()),
        key="mtf_asset",
    )

    r = cached_signal(
        asset_choice,
        ASSETS[asset_choice],
        DEFAULT_MIN_TF_AGREEMENT,
        DEFAULT_MIN_SCORE,
        DEFAULT_MIN_RR,
    )

    if not r.get("ok"):

        render_data_down(r)

    else:

        tf_biases = r.get(
            "tf_biases",
            {},
        )

        tf_structures = r.get(
            "tf_structures",
            {},
        )

        cols = st.columns(4)

        for col, tf in zip(
            cols,
            ["1D", "4H", "1H", "15M"],
        ):

            with col:

                st.metric(
                    tf,
                    tf_biases.get(
                        tf,
                        "-",
                    ),
                )

                st.caption(
                    tf_structures.get(
                        tf,
                        "-",
                    )
                )


# ============================================================
# CORRELATION MATRIX
# ============================================================

elif page == "Correlation Matrix":

    st.subheader(
        "🔗 Live Rolling Correlation Matrix"
    )

    try:

        matrix = (
            compute_live_correlation_matrix()
        )

    except Exception as e:

        matrix = None
        st.error(
            f"Correlation calculation failed: {e}"
        )

    if matrix is None:

        st.warning(
            "Correlation data unavailable."
        )

    else:

        st.dataframe(
            matrix,
            width="stretch",
        )


# ============================================================
# TRADE JOURNAL
# ============================================================

elif page == "Trade Journal":

    st.subheader("📒 Trade Journal")

    with st.form(
        "journal_form",
        clear_on_submit=True,
    ):

        j_asset = st.selectbox(
            "Asset",
            list(ASSETS.keys()),
        )

        j_signal = st.selectbox(
            "Signal Taken",
            ["BUY", "SELL"],
        )

        j_entry = st.number_input(
            "Entry Price",
            value=0.0,
            format="%.4f",
        )

        j_stop = st.number_input(
            "Stop Price",
            value=0.0,
            format="%.4f",
        )

        j_tp1 = st.number_input(
            "TP1 Price",
            value=0.0,
            format="%.4f",
        )

        j_notes = st.text_area(
            "Setup / execution notes"
        )

        j_outcome = st.selectbox(
            "Outcome",
            [
                "OPEN",
                "WIN",
                "LOSS",
                "BREAKEVEN",
            ],
        )

        j_submit = st.form_submit_button(
            "Save Entry"
        )

    if j_submit:

        if not j_notes.strip():

            st.warning(
                "Please enter setup / execution notes."
            )

        else:

            try:

                database.log_trade(
                    j_asset,
                    j_signal,
                    j_entry,
                    j_stop,
                    j_tp1,
                    j_outcome,
                    j_notes,
                )

                st.success(
                    "Trade journal entry saved."
                )

            except Exception as e:

                st.error(
                    f"Could not save trade: {e}"
                )

    try:

        trades = database.get_trades()

    except Exception:

        trades = []

    if trades:

        st.dataframe(
            pd.DataFrame(trades),
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No journal entries yet."
        )


# ============================================================
# PERFORMANCE
# ============================================================

elif page == "Performance":

    st.subheader("📉 Performance")

    try:

        perf = database.get_performance()

    except Exception as e:

        st.error(
            f"Could not load performance: {e}"
        )

        perf = {
            "has_data": False
        }

    if not perf.get("has_data"):

        st.info(
            "No resolved trades logged yet. "
            "Log outcomes in Trade Journal "
            "to see real stats here."
        )

    else:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Trades Logged",
            perf.get(
                "total_logged",
                0,
            ),
        )

        c2.metric(
            "Resolved",
            perf.get(
                "resolved",
                0,
            ),
        )

        c3.metric(
            "Win Rate",
            f"{perf.get('win_rate', 0)}%",
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":

    st.subheader("⚙️ Engine Settings")

    st.write(
        f"Timeframes required to agree: "
        f"**{DEFAULT_MIN_TF_AGREEMENT}/4**"
    )

    st.write(
        f"Minimum score to fire a signal: "
        f"**{DEFAULT_MIN_SCORE}/100**"
    )

    st.write(
        f"Minimum R:R (to TP2): "
        f"**{DEFAULT_MIN_RR}**"
    )

    st.caption(
        "These values come from config.py."
    )

    st.markdown("---")

    st.markdown(
        "**Known limitations:**"
    )

    st.markdown(
        """
        - Score is a rules-based heuristic.
        - It is not a backtested win rate.
        - No live economic news calendar is currently wired in.
        - The dashboard does not place trades.
        - Real order execution requires a broker execution bridge / EA.
        """
    )
