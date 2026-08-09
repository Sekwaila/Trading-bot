"""
SEKWAILA OMEGA X
Advanced Signal-Only Trading Dashboard

IMPORTANT:
- Dashboard uses engine.py for signal generation.
- Telegram worker continues using worker.py.
- This file does NOT place trades.
- Settings stored in Streamlit session state.
"""

import datetime
import html
import math
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from config import (
    ASSETS,
    DEFAULT_MIN_TF_AGREEMENT,
    DEFAULT_MIN_SCORE,
    DEFAULT_MIN_RR,
)

from engine import (
    generate_omega_signal,
    grade,
    fetch_usdzar_rate,
    compute_live_correlation_matrix,
    calculate_position_size,
)

import database


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# SESSION STATE
# =============================================================================

DEFAULT_SETTINGS = {
    "min_tf": DEFAULT_MIN_TF_AGREEMENT,
    "min_score": DEFAULT_MIN_SCORE,
    "min_rr": DEFAULT_MIN_RR,
    "risk_pct": 1.0,
    "account_zar": 1000.0,

    "show_chart": True,
    "show_indicators": True,
    "show_reasoning": True,
    "show_market_strength": True,
    "show_mtf": True,
    "show_order_blocks": True,
    "show_fvg": True,
    "show_liquidity": True,
    "show_premium_discount": True,

    "katlego_enabled": True,
    "katlego_detail": "Advanced",
    "katlego_style": "Professional",
    "katlego_auto_analysis": True,

    "telegram_enabled": False,

    "background": "OMEGA DARK",
    "gold_intensity": "Normal",
    "compact_mode": False,
}

for key, value in DEFAULT_SETTINGS.items():
    if key not in st.session_state:
        st.session_state[key] = value


database.init_db()


# =============================================================================
# THEME / CSS
# =============================================================================

THEMES = {
    "OMEGA DARK": {
        "bg": "#080909",
        "panel": "#10130f",
        "panel2": "#151912",
        "border": "#3b321e",
        "gold": "#d9ad57",
        "green": "#00e676",
        "red": "#ff5252",
        "orange": "#ffb74d",
        "blue": "#4da3ff",
        "text": "#e8e1d2",
        "muted": "#8d918a",
    },
    "ROYAL GOLD": {
        "bg": "#080603",
        "panel": "#151006",
        "panel2": "#1b1409",
        "border": "#60491f",
        "gold": "#f0c96a",
        "green": "#00e676",
        "red": "#ff5252",
        "orange": "#ffb74d",
        "blue": "#5faeff",
        "text": "#f1e5cb",
        "muted": "#a59a83",
    },
    "TRADINGVIEW BLACK": {
        "bg": "#0b0e11",
        "panel": "#131722",
        "panel2": "#171b26",
        "border": "#2a2e39",
        "gold": "#d9ad57",
        "green": "#26a69a",
        "red": "#ef5350",
        "orange": "#ffb74d",
        "blue": "#42a5f5",
        "text": "#d1d4dc",
        "muted": "#787b86",
    },
    "MIDNIGHT BLUE": {
        "bg": "#070b14",
        "panel": "#0e1524",
        "panel2": "#121c2e",
        "border": "#243552",
        "gold": "#d9ad57",
        "green": "#00e676",
        "red": "#ff5252",
        "orange": "#ffb74d",
        "blue": "#42a5f5",
        "text": "#e1e8f0",
        "muted": "#8290a3",
    },
}

T = THEMES[st.session_state.background]

compact_padding = "8px" if st.session_state.compact_mode else "14px"


st.markdown(
    f"""
<style>

html, body, [class*="css"] {{
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

.stApp {{
    background:
        radial-gradient(circle at 15% 5%, rgba(217,173,87,.06), transparent 30%),
        radial-gradient(circle at 90% 90%, rgba(0,230,118,.025), transparent 25%),
        {T["bg"]};
    color: {T["text"]};
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}}

header {{
    visibility: hidden;
}}

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {T["panel"]}, {T["bg"]});
    border-right: 1px solid {T["border"]};
}}

[data-testid="stSidebar"] * {{
    color: {T["text"]};
}}

.omega-title {{
    color: {T["gold"]};
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 2px;
    text-align: center;
}}

.omega-subtitle {{
    color: {T["muted"]};
    font-size: 10px;
    letter-spacing: 2px;
    text-align: center;
}}

.card {{
    background: linear-gradient(145deg, {T["panel2"]}, {T["panel"]});
    border: 1px solid {T["border"]};
    border-radius: 12px;
    padding: {compact_padding};
    margin-bottom: 12px;
    box-shadow: 0 8px 25px rgba(0,0,0,.18);
}}

.card:hover {{
    border-color: {T["gold"]};
}}

.card-title {{
    color: {T["gold"]};
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    margin-bottom: 9px;
}}

.muted {{
    color: {T["muted"]};
}}

.gold {{
    color: {T["gold"]};
}}

.green {{
    color: {T["green"]};
    font-weight: 800;
}}

.red {{
    color: {T["red"]};
    font-weight: 800;
}}

.orange {{
    color: {T["orange"]};
    font-weight: 800;
}}

.blue {{
    color: {T["blue"]};
    font-weight: 800;
}}

.big-score {{
    font-size: 38px;
    font-weight: 900;
}}

.signal-buy {{
    background: linear-gradient(145deg, rgba(0,230,118,.13), rgba(0,230,118,.025));
    border: 1px solid {T["green"]};
    border-radius: 14px;
    padding: 20px;
}}

.signal-sell {{
    background: linear-gradient(145deg, rgba(255,82,82,.13), rgba(255,82,82,.025));
    border: 1px solid {T["red"]};
    border-radius: 14px;
    padding: 20px;
}}

.signal-neutral {{
    background: linear-gradient(145deg, rgba(217,173,87,.12), rgba(217,173,87,.025));
    border: 1px solid {T["gold"]};
    border-radius: 14px;
    padding: 20px;
}}

.pair-card {{
    background: {T["panel"]};
    border: 1px solid {T["border"]};
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
}}

.pair-card:hover {{
    border-color: {T["gold"]};
}}

.metric-value {{
    font-size: 18px;
    font-weight: 800;
}}

.tag {{
    display:inline-block;
    padding:3px 8px;
    border-radius:20px;
    font-size:10px;
    font-weight:700;
}}

.tag-green {{
    color:#001b0b;
    background:{T["green"]};
}}

.tag-red {{
    color:#250000;
    background:{T["red"]};
}}

.tag-gold {{
    color:#211600;
    background:{T["gold"]};
}}

hr {{
    border-color: {T["border"]};
}}

.stButton > button {{
    border-radius: 8px;
    border: 1px solid {T["border"]};
}}

</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# HELPERS
# =============================================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_text(value, default="N/A"):
    if value is None:
        return default
    return str(value)


def cached_signal(symbol, ticker, min_tf, min_score, min_rr):
    """
    Intentionally NOT permanently cached.

    A trading dashboard should not keep stale signals for long periods.
    """
    return generate_omega_signal(
        symbol,
        ticker,
        min_tf,
        min_score,
        min_rr,
    )


def signal_color(bias):
    if bias == "BUY":
        return T["green"]
    if bias == "SELL":
        return T["red"]
    return T["gold"]


def signal_label(bias):
    if bias == "BUY":
        return "BUY"
    if bias == "SELL":
        return "SELL"
    return "WAIT"


def bias_label(bull, bear):
    difference = bull - bear

    if difference >= 30:
        return "EXTREME BULL"
    if difference >= 20:
        return "STRONG BULL"
    if difference >= 8:
        return "LEAN BULL"

    if difference <= -30:
        return "EXTREME BEAR"
    if difference <= -20:
        return "STRONG BEAR"
    if difference <= -8:
        return "LEAN BEAR"

    return "NEUTRAL"


def score_bar(score, color):
    score = max(0, min(100, safe_float(score)))

    return f"""
    <div style="background:#24261f;border-radius:6px;height:8px;width:100%;overflow:hidden;">
        <div style="background:{color};width:{score}%;height:8px;border-radius:6px;"></div>
    </div>
    """


def render_data_down(res):
    st.markdown(
        f"""
        <div class="signal-neutral">
            <h3 class="gold">⚠ DATA UNAVAILABLE</h3>
            <b>{safe_text(res.get("symbol"))}</b>
            <p class="muted">{safe_text(res.get("reason"), "Unknown data error")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_signal(asset):
    return cached_signal(
        asset,
        ASSETS[asset],
        st.session_state.min_tf,
        st.session_state.min_score,
        st.session_state.min_rr,
    )


def render_signal_card(res, compact=False):
    bias = res.get("bias", "NEUTRAL")
    score = safe_float(res.get("score"))
    rr = safe_float(res.get("rr"))

    if bias == "BUY":
        css = "signal-buy"
        title = "CONFIRMED BUY ↑"
        color_class = "green"
    elif bias == "SELL":
        css = "signal-sell"
        title = "CONFIRMED SELL ↓"
        color_class = "red"
    else:
        css = "signal-neutral"
        title = "NEUTRAL / NO SETUP"
        color_class = "gold"

    reason = safe_text(res.get("reason"), "")

    st.markdown(
        f"""
        <div class="{css}">
            <div style="display:flex;justify-content:space-between;gap:20px;">
                <div>
                    <div style="font-size:24px;font-weight:900;">{safe_text(res.get("symbol"))}</div>
                    <div class="muted" style="font-size:10px;">
                        OMEGA X RULE-BASED SIGNAL ENGINE
                    </div>
                </div>

                <div style="text-align:right;">
                    <div class="muted" style="font-size:10px;">SCORE</div>
                    <div class="gold big-score">{score:.1f}</div>
                </div>
            </div>

            <hr>

            <div class="{color_class}" style="font-size:24px;font-weight:900;">
                {title}
            </div>

            {f'<div class="orange" style="font-size:11px;margin-top:5px;">{html.escape(reason)}</div>' if reason else ''}

            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:18px;text-align:center;">

                <div>
                    <div class="muted" style="font-size:9px;">ENTRY</div>
                    <b>{safe_float(res.get("entry")):.4f}</b>
                </div>

                <div>
                    <div class="muted" style="font-size:9px;">TP1</div>
                    <b class="green">{safe_float(res.get("tp1")):.4f}</b>
                </div>

                <div>
                    <div class="muted" style="font-size:9px;">TP2</div>
                    <b class="green">{safe_float(res.get("tp2")):.4f}</b>
                </div>

                <div>
                    <div class="muted" style="font-size:9px;">TP3</div>
                    <b class="green">{safe_float(res.get("tp3")):.4f}</b>
                </div>

                <div>
                    <div class="muted" style="font-size:9px;">STOP</div>
                    <b class="red">{safe_float(res.get("stop")):.4f}</b>
                </div>

            </div>

            <div style="text-align:center;margin-top:12px;">
                <span class="tag tag-gold">R:R {rr:.2f}</span>
                <span class="tag tag-gold">GRADE {grade(score)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_indicator_panel(res):
    vwap = safe_text(res.get("vwap_status"))
    macd = safe_text(res.get("macd_trend"))
    ema = safe_text(res.get("ema_cross"))
    trend = "STRONG" if res.get("trend_strong") else "WEAK"

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">📊 OMEGA INDICATOR ENGINE</div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px 20px;font-size:12px;">

                <div>Price / VWAP</div>
                <b class="{'green' if vwap == 'ABOVE' else 'red'}">{vwap}</b>

                <div>RSI (14)</div>
                <b>{safe_float(res.get("rsi")):.2f}</b>

                <div>MACD Trend</div>
                <b class="{'green' if macd == 'BULLISH' else 'red'}">{macd}</b>

                <div>ADX Power</div>
                <b>{safe_float(res.get("regime", {}).get("adx")):.2f}</b>

                <div>EMA Cross</div>
                <b class="{'green' if ema == 'BULLISH' else 'red'}">{ema}</b>

                <div>ATR 14</div>
                <b>{safe_float(res.get("atr")):.2f}</b>

                <div>Volatility</div>
                <b>{safe_text(res.get("vol_status"))}</b>

                <div>Trend Strength</div>
                <b class="{'green' if trend == 'STRONG' else 'orange'}">{trend}</b>

                <div>Structure</div>
                <b>{safe_text(res.get("structure"))}</b>

                <div>Status</div>
                <b class="gold">{safe_text(res.get("bias"), "WAIT")}</b>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart(res):
    if not st.session_state.show_chart:
        return

    df = res.get("data", {}).get("15M")

    if df is None or len(df) == 0:
        st.warning("15M chart data unavailable.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            increasing_line_color=T["green"],
            decreasing_line_color=T["red"],
            increasing_fillcolor=T["green"],
            decreasing_fillcolor=T["red"],
            name=res.get("symbol", "PRICE"),
        )
    )

    if st.session_state.show_order_blocks:
        ob_zone = res.get("ob_zone")

        if ob_zone:
            ob_min, ob_max = ob_zone

            ob_type = safe_text(res.get("ob_type"), "ORDER BLOCK")
            state = (
                "INVALIDATED"
                if res.get("ob_invalidated")
                else "MITIGATED"
                if res.get("ob_mitigated")
                else "UNMITIGATED"
            )

            color = (
                "rgba(0,230,118,.15)"
                if "BULL" in ob_type
                else "rgba(255,82,82,.15)"
            )

            fig.add_hrect(
                y0=ob_min,
                y1=ob_max,
                fillcolor=color,
                line_width=1,
                annotation_text=f"{ob_type} — {state}",
                annotation_position="bottom left",
            )

    if st.session_state.show_fvg:
        fvg = res.get("fvg")

        if fvg:
            zone = fvg.get("zone")

            if zone:
                fig.add_hrect(
                    y0=zone[0],
                    y1=zone[1],
                    fillcolor="rgba(217,173,87,.13)",
                    line_width=1,
                    line_dash="dot",
                    annotation_text=f"{safe_text(fvg.get('type'))} FVG",
                    annotation_position="top left",
                )

    if st.session_state.show_premium_discount:
        pd_info = res.get("pd_info", {})

        equilibrium = safe_float(pd_info.get("equilibrium"))
        swing_hi = safe_float(pd_info.get("swing_high"))
        swing_lo = safe_float(pd_info.get("swing_low"))

        if swing_hi > swing_lo:
            fig.add_hrect(
                y0=equilibrium,
                y1=swing_hi,
                fillcolor="rgba(255,82,82,.06)",
                line_width=0,
            )

            fig.add_hrect(
                y0=swing_lo,
                y1=equilibrium,
                fillcolor="rgba(66,133,244,.06)",
                line_width=0,
            )

            fig.add_hline(
                y=equilibrium,
                line_dash="dash",
                line_color=T["gold"],
                annotation_text="EQUILIBRIUM",
            )

    if st.session_state.show_liquidity:
        for value in res.get("eq_highs", [])[-3:]:
            fig.add_hline(
                y=value,
                line_dash="dot",
                line_color=T["red"],
                annotation_text="EQH",
            )

        for value in res.get("eq_lows", [])[-3:]:
            fig.add_hline(
                y=value,
                line_dash="dot",
                line_color=T["green"],
                annotation_text="EQL",
            )

    try:
        fig.add_hline(
            y=res["entry"],
            line_dash="dash",
            line_color=T["gold"],
            annotation_text="ENTRY",
        )

        fig.add_hline(
            y=res["stop"],
            line_dash="dot",
            line_color=T["red"],
            annotation_text="STOP",
        )

        fig.add_hline(
            y=res["tp2"],
            line_dash="dot",
            line_color=T["green"],
            annotation_text="TP2",
        )
    except Exception:
        pass

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=T["panel"],
        plot_bgcolor=T["panel"],
        height=470,
        margin=dict(l=5, r=5, t=10, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        font=dict(color=T["text"]),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
            "responsive": True,
        },
    )


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown(
        """
        <div class="omega-title">👑 SEKWAILA</div>
        <div class="omega-subtitle">OMEGA X INTELLIGENCE ENGINE</div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    pages = [
        "🏠 Dashboard",
        "📡 Market Scanner",
        "🔥 Market Heatmap",
        "🤖 Katlego AI",
        "📊 Multi-Timeframe",
        "🔗 Correlation Matrix",
        "📒 Trade Journal",
        "📈 Performance",
        "📱 Telegram",
        "⚙️ Settings",
        "❓ Help",
    ]

    page = st.radio(
        "OMEGA MODULES",
        pages,
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### 💰 Risk Engine")

    st.session_state.account_zar = st.number_input(
        "Account Balance (ZAR)",
        min_value=100.0,
        value=float(st.session_state.account_zar),
        step=100.0,
    )

    st.session_state.risk_pct = st.slider(
        "Risk Per Signal %",
        0.1,
        5.0,
        float(st.session_state.risk_pct),
        0.1,
    )

    risk_money = (
        st.session_state.account_zar
        * st.session_state.risk_pct
        / 100
    )

    st.caption(
        f"Risk per signal: R{risk_money:,.2f}"
    )

    st.divider()

    if st.button(
        "🔄 REFRESH ENGINE",
        use_container_width=True,
    ):
        st.rerun()

    st.caption(
        "Signal-only system. No broker execution."
    )


# =============================================================================
# HEADER
# =============================================================================

st.markdown(
    """
    <div class="omega-title" style="font-size:30px;">
        👑 SEKWAILA OMEGA X
    </div>
    <div class="omega-subtitle">
        ADVANCED MARKET INTELLIGENCE • SIGNAL ENGINE • KATLEGO AI
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# =============================================================================
# DASHBOARD
# =============================================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="card-title">MARKET SIGNAL BOARD</div>',
        unsafe_allow_html=True,
    )

    assets = list(ASSETS.keys())

    # Main asset
    asset_choice = st.selectbox(
        "Active Asset",
        assets,
        index=0,
    )

    res = get_signal(asset_choice)

    if not res.get("ok"):
        render_data_down(res)
        st.stop()

    # -------------------------------------------------------------------------
    # Top status row
    # -------------------------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Asset",
        asset_choice,
    )

    c2.metric(
        "Score",
        f"{safe_float(res.get('score')):.1f}/100",
    )

    c3.metric(
        "Signal",
        signal_label(res.get("bias")),
    )

    c4.metric(
        "R:R",
        f"{safe_float(res.get('rr')):.2f}",
    )

    # -------------------------------------------------------------------------
    # Signal
    # -------------------------------------------------------------------------

    render_signal_card(res)

    st.markdown("")

    # -------------------------------------------------------------------------
    # Main dashboard columns
    # -------------------------------------------------------------------------

    left, center, right = st.columns(
        [1.15, 2.6, 1.15],
        gap="medium",
    )

    with left:

        bull = safe_float(res.get("bull_score"))
        bear = safe_float(res.get("bear_score"))

        bias = bias_label(bull, bear)

        bias_color = (
            T["green"]
            if "BULL" in bias
            else T["red"]
            if "BEAR" in bias
            else T["gold"]
        )

        st.markdown(
            f"""
            <div class="card">

                <div class="card-title">⚔️ BULL / BEAR SCORE</div>

                <div style="display:flex;justify-content:space-between;">
                    <span>BULL</span>
                    <b class="green">{bull:.1f}%</b>
                </div>

                {score_bar(bull, T["green"])}

                <br>

                <div style="display:flex;justify-content:space-between;">
                    <span>BEAR</span>
                    <b class="red">{bear:.1f}%</b>
                </div>

                {score_bar(bear, T["red"])}

                <div style="
                    margin-top:12px;
                    text-align:center;
                    padding:9px;
                    border:1px solid {bias_color};
                    border-radius:8px;
                ">
                    <small class="muted">MARKET BIAS</small>
                    <br>
                    <b style="color:{bias_color};">{bias}</b>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.show_indicators:
            render_indicator_panel(res)

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">📈 MARKET REGIME</div>
                <b class="green">
                    {safe_text(res.get("regime", {}).get("regime"))}
                </b>
                <br>
                <small class="muted">
                    ADX {safe_float(res.get("regime", {}).get("adx")):.2f}
                    |
                    VOL RATIO {safe_float(res.get("regime", {}).get("vol_ratio")):.2f}
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">🕐 SESSION</div>
                <b>{safe_text(res.get("session"))}</b>
                <br>
                <small class="muted">
                    Quality {safe_float(res.get("session_quality")):.1f}%
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with center:

        render_chart(res)

        if st.session_state.show_mtf:

            st.markdown(
                '<div class="card-title">⏱ MULTI-TIMEFRAME AGREEMENT</div>',
                unsafe_allow_html=True,
            )

            tf_cols = st.columns(4)

            for col, tf in zip(
                tf_cols,
                ["1D", "4H", "1H", "15M"],
            ):

                trend = safe_text(
                    res.get("tf_biases", {}).get(tf),
                    "N/A",
                )

                color = (
                    T["green"]
                    if trend == "BUY"
                    else T["red"]
                    if trend == "SELL"
                    else T["gold"]
                )

                with col:
                    st.markdown(
                        f"""
                        <div class="card" style="text-align:center;">
                            <small class="muted">{tf}</small>
                            <br>
                            <b style="color:{color};font-size:18px;">
                                {trend}
                            </b>
                            <br>
                            <small class="muted">
                                {safe_text(res.get("tf_structures", {}).get(tf))}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with right:

        if st.session_state.show_reasoning:

            structure = safe_text(res.get("structure"))

            sweep = safe_text(
                res.get("sweep_detail"),
                "No sweep information",
            )

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">🧠 OMEGA REASONING</div>

                    <small class="muted">STRUCTURE</small>
                    <br>
                    <b>{structure}</b>

                    <br><br>

                    <small class="muted">LIQUIDITY</small>
                    <br>
                    <span>{sweep}</span>

                    <br><br>

                    <small class="muted">ZONE</small>
                    <br>
                    <b>{safe_text(res.get("pd_zone"))}</b>

                    <br><br>

                    <small class="muted">ORDER BLOCK</small>
                    <br>
                    <b>{safe_text(res.get("ob_type"))}</b>

                </div>
                """,
                unsafe_allow_html=True,
            )

        pd_info = res.get("pd_info", {})

        st.markdown(
            f"""
            <div class="card">

                <div class="card-title">💎 PREMIUM / DISCOUNT</div>

                <b>{safe_text(res.get("pd_zone"))}</b>

                <br>

                <small class="muted">
                    Equilibrium:
                    {safe_float(pd_info.get("equilibrium")):.4f}
                </small>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # Position sizing
        rate = fetch_usdzar_rate()

        usd_balance = (
            st.session_state.account_zar / rate
            if rate
            else None
        )

        if usd_balance and res.get("bias") in ["BUY", "SELL"]:

            try:

                position = calculate_position_size(
                    usd_balance,
                    st.session_state.risk_pct,
                    res["entry"],
                    res["stop"],
                )

                if position:

                    st.markdown(
                        f"""
                        <div class="card">

                            <div class="card-title">💰 POSITION SIZE</div>

                            <div>
                                Risk:
                                <b class="gold">
                                R{risk_money:,.2f}
                                </b>
                            </div>

                            <div>
                                Stop Distance:
                                <b>
                                {safe_float(position.get("stop_distance")):.2f}
                                </b>
                            </div>

                            <div>
                                Lots:
                                <b class="green">
                                {safe_text(position.get("lots"))}
                                </b>
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            except Exception:
                pass


# =============================================================================
# MARKET SCANNER
# =============================================================================

elif page == "📡 Market Scanner":

    st.subheader("📡 OMEGA X LIVE MARKET SCANNER")

    st.caption(
        "All signals are generated through the same engine used by the alert worker."
    )

    rows = []

    progress = st.progress(
        0,
        text="Initializing OMEGA scanner...",
    )

    total = len(ASSETS)

    for i, asset in enumerate(ASSETS):

        try:

            r = get_signal(asset)

            if r.get("ok"):

                rows.append(
                    {
                        "PAIR": asset,
                        "SIGNAL": r.get("bias", "WAIT"),
                        "SCORE": round(
                            safe_float(r.get("score")),
                            1,
                        ),
                        "GRADE": grade(
                            safe_float(r.get("score"))
                        ),
                        "R:R": round(
                            safe_float(r.get("rr")),
                            2,
                        ),
                        "SESSION": r.get("session"),
                        "ZONE": r.get("pd_zone"),
                        "1D": r.get("tf_biases", {}).get("1D"),
                        "4H": r.get("tf_biases", {}).get("4H"),
                        "1H": r.get("tf_biases", {}).get("1H"),
                        "15M": r.get("tf_biases", {}).get("15M"),
                    }
                )

            else:

                rows.append(
                    {
                        "PAIR": asset,
                        "SIGNAL": "DATA DOWN",
                        "SCORE": 0,
                        "GRADE": "-",
                        "R:R": 0,
                        "SESSION": "-",
                        "ZONE": "-",
                        "1D": "-",
                        "4H": "-",
                        "1H": "-",
                        "15M": "-",
                    }
                )

        except Exception as exc:

            rows.append(
                {
                    "PAIR": asset,
                    "SIGNAL": "ERROR",
                    "SCORE": 0,
                    "GRADE": "-",
                    "R:R": 0,
                    "SESSION": "-",
                    "ZONE": "-",
                    "1D": "-",
                    "4H": "-",
                    "1H": "-",
                    "15M": "-",
                }
            )

        progress.progress(
            (i + 1) / total,
            text=f"Scanning {asset}...",
        )

    progress.empty()

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values(
            ["SCORE", "R:R"],
            ascending=False,
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# =============================================================================
# HEATMAP
# =============================================================================

elif page == "🔥 Market Heatmap":

    st.subheader("🔥 OMEGA X MARKET STRENGTH")

    results = []

    for asset in ASSETS:

        try:

            r = get_signal(asset)

            if r.get("ok"):

                results.append(
                    {
                        "Asset": asset,
                        "Score": safe_float(r.get("score")),
                        "Signal": r.get("bias"),
                    }
                )

        except Exception:
            pass

    if results:

        df = pd.DataFrame(results)

        fig = go.Figure(
            go.Bar(
                x=df["Asset"],
                y=df["Score"],
                text=[
                    f"{s:.0f}"
                    for s in df["Score"]
                ],
                textposition="auto",
                marker_color=[
                    T["green"]
                    if s["Signal"] == "BUY"
                    else T["red"]
                    if s["Signal"] == "SELL"
                    else T["gold"]
                    for _, s in df.iterrows()
                ],
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=T["bg"],
            plot_bgcolor=T["panel"],
            yaxis=dict(
                range=[0, 100],
                title="OMEGA SCORE",
            ),
            height=430,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# =============================================================================
# KATLEGO AI
# =============================================================================

elif page == "🤖 Katlego AI":

    st.subheader("🤖 KATLEGO AI — OMEGA MARKET INTELLIGENCE")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.session_state.katlego_enabled = st.toggle(
            "Enable Katlego",
            st.session_state.katlego_enabled,
        )

    with c2:
        st.session_state.katlego_detail = st.selectbox(
            "Analysis Depth",
            [
                "Basic",
                "Advanced",
                "Institutional",
                "OMEGA MAX",
            ],
            index=[
                "Basic",
                "Advanced",
                "Institutional",
                "OMEGA MAX",
            ].index(st.session_state.katlego_detail),
        )

    with c3:
        st.session_state.katlego_style = st.selectbox(
            "Narration Style",
            [
                "Professional",
                "Short Signal",
                "Trader",
                "Institutional",
            ],
            index=[
                "Professional",
                "Short Signal",
                "Trader",
                "Institutional",
            ].index(st.session_state.katlego_style),
        )

    st.divider()

    asset = st.selectbox(
        "Ask Katlego about",
        list(ASSETS.keys()),
    )

    r = get_signal(asset)

    if not r.get("ok"):

        render_data_down(r)

    elif not st.session_state.katlego_enabled:

        st.warning("Katlego AI is disabled in Settings.")

    else:

        score = safe_float(r.get("score"))
        bias = r.get("bias", "NEUTRAL")

        structure = safe_text(r.get("structure"))
        regime = safe_text(
            r.get("regime", {}).get("regime")
        )

        session = safe_text(r.get("session"))

        zone = safe_text(r.get("pd_zone"))

        ob = safe_text(r.get("ob_type"))

        trend = (
            "confirmed"
            if r.get("trend_strong")
            else "not confirmed"
        )

        if bias == "BUY":
            action = "bullish confirmation is present"
        elif bias == "SELL":
            action = "bearish confirmation is present"
        else:
            action = "there is currently no sufficiently strong confirmed setup"

        narrative = f"""
### 👑 Katlego AI — {asset}

**Market assessment:** {action}.

**OMEGA Score:** `{score:.1f}/100`  
**Current bias:** `{bias}`  
**Market structure:** `{structure}`  
**Regime:** `{regime}`  
**Session:** `{session}`  
**Premium/Discount:** `{zone}`  
**Order Block:** `{ob}`  
**Trend strength:** `{trend}`

Katlego's current interpretation is that the engine should respect the
multi-timeframe structure, volatility regime, liquidity information and
minimum-score requirements before treating a setup as actionable.

**Risk control:** Never increase position size simply because the score is
high. The score is a rules-based signal metric, not a guaranteed probability
of profit.
"""

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    👑 KATLEGO AI — {st.session_state.katlego_detail.upper()}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(narrative)

        question = st.chat_input(
            "Ask Katlego about this market..."
        )

        if question:

            st.chat_message(
                "user"
            ).write(question)

            st.chat_message(
                "assistant"
            ).write(
                f"Katlego: Based on the current OMEGA X engine values for "
                f"{asset}, the current engine bias is **{bias}** with a "
                f"score of **{score:.1f}/100**. The key structure is "
                f"**{structure}** and the market is in a **{regime}** regime. "
                f"Use the displayed Entry, Stop and TP levels rather than "
                f"chasing price."
            )


# =============================================================================
# MULTI TIMEFRAME
# =============================================================================

elif page == "📊 Multi-Timeframe":

    st.subheader("📊 MULTI-TIMEFRAME OMEGA ALIGNMENT")

    asset = st.selectbox(
        "Asset",
        list(ASSETS.keys()),
        key="mtf_asset",
    )

    r = get_signal(asset)

    if not r.get("ok"):

        render_data_down(r)

    else:

        cols = st.columns(4)

        for col, tf in zip(
            cols,
            ["1D", "4H", "1H", "15M"],
        ):

            trend = r.get(
                "tf_biases",
                {},
            ).get(tf, "N/A")

            structure = r.get(
                "tf_structures",
                {},
            ).get(tf, "N/A")

            color = (
                T["green"]
                if trend == "BUY"
                else T["red"]
                if trend == "SELL"
                else T["gold"]
            )

            with col:

                st.markdown(
                    f"""
                    <div class="card" style="text-align:center;">

                        <div class="card-title">{tf}</div>

                        <div style="
                            color:{color};
                            font-size:24px;
                            font-weight:900;
                        ">
                            {trend}
                        </div>

                        <small class="muted">
                            {structure}
                        </small>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =============================================================================
# CORRELATION
# =============================================================================

elif page == "🔗 Correlation Matrix":

    st.subheader("🔗 LIVE ROLLING CORRELATION MATRIX")

    try:

        matrix = compute_live_correlation_matrix()

        if matrix is None:

            st.warning(
                "Correlation data unavailable."
            )

        else:

            fig = go.Figure(
                go.Heatmap(
                    z=matrix.values,
                    x=matrix.columns,
                    y=matrix.index,
                    zmin=-1,
                    zmax=1,
                    text=np.round(
                        matrix.values,
                        2,
                    ),
                    texttemplate="%{text}",
                    colorscale="RdBu",
                    reversescale=True,
                )
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor=T["bg"],
                plot_bgcolor=T["panel"],
                height=600,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    except Exception as exc:

        st.error(
            f"Correlation engine error: {exc}"
        )


# =============================================================================
# TRADE JOURNAL
# =============================================================================

elif page == "📒 Trade Journal":

    st.subheader("📒 OMEGA X TRADE JOURNAL")

    with st.form(
        "omega_journal",
        clear_on_submit=True,
    ):

        c1, c2 = st.columns(2)

        with c1:

            asset = st.selectbox(
                "Asset",
                list(ASSETS.keys()),
            )

            direction = st.selectbox(
                "Signal",
                ["BUY", "SELL"],
            )

            entry = st.number_input(
                "Entry",
                value=0.0,
            )

        with c2:

            stop = st.number_input(
                "Stop",
                value=0.0,
            )

            tp1 = st.number_input(
                "TP1",
                value=0.0,
            )

            outcome = st.selectbox(
                "Outcome",
                [
                    "OPEN",
                    "WIN",
                    "LOSS",
                    "BREAKEVEN",
                ],
            )

        notes = st.text_area(
            "Execution Notes"
        )

        submit = st.form_submit_button(
            "💾 SAVE TRADE"
        )

    if submit:

        try:

            database.log_trade(
                asset,
                direction,
                entry,
                stop,
                tp1,
                outcome,
                notes,
            )

            st.success(
                "Trade journal entry saved."
            )

        except Exception as exc:

            st.error(
                f"Could not save trade: {exc}"
            )

    try:

        trades = database.get_trades()

        if trades:

            st.dataframe(
                pd.DataFrame(trades),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No trades recorded yet."
            )

    except Exception as exc:

        st.error(
            f"Journal error: {exc}"
        )


# =============================================================================
# PERFORMANCE
# =============================================================================

elif page == "📈 Performance":

    st.subheader("📈 OMEGA X PERFORMANCE")

    try:

        perf = database.get_performance()

        if not perf.get("has_data"):

            st.info(
                "No resolved trades yet."
            )

        else:

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Trades",
                perf.get("total_logged", 0),
            )

            c2.metric(
                "Resolved",
                perf.get("resolved", 0),
            )

            c3.metric(
                "Win Rate",
                f"{perf.get('win_rate', 0)}%",
            )

            c4.metric(
                "Status",
                "TRACKING",
            )

    except Exception as exc:

        st.error(
            f"Performance error: {exc}"
        )


# =============================================================================
# TELEGRAM
# =============================================================================

elif page == "📱 Telegram":

    st.subheader("📱 OMEGA X TELEGRAM ALERTS")

    st.info(
        "Telegram sending remains controlled by worker.py. "
        "This page stores/display alert preferences only."
    )

    enabled = st.toggle(
        "Enable Telegram Alerts",
        st.session_state.telegram_enabled,
    )

    st.session_state.telegram_enabled = enabled

    st.divider()

    st.markdown("### Alert Rules")

    alert_assets = st.multiselect(
        "Assets",
        list(ASSETS.keys()),
        default=list(ASSETS.keys()),
    )

    alert_types = st.multiselect(
        "Alert Types",
        [
            "CONFIRMED BUY",
            "CONFIRMED SELL",
            "HIGH SCORE",
            "MTF ALIGNMENT",
            "LIQUIDITY SWEEP",
            "ORDER BLOCK",
            "FVG",
        ],
        default=[
            "CONFIRMED BUY",
            "CONFIRMED SELL",
        ],
    )

    st.markdown("### Telegram configuration")

    st.text_input(
        "Bot Token",
        type="password",
        placeholder="Stored through your deployment environment",
    )

    st.text_input(
        "Chat ID",
        placeholder="-100xxxxxxxxxx",
    )

    st.markdown(
        """
        **Recommended:** keep the actual Telegram bot token in your
        Railway environment variables rather than hard-coding it in this file.
        """,
    )


# =============================================================================
# SETTINGS
# =============================================================================

elif page == "⚙️ Settings":

    st.subheader("⚙️ SEKWAILA OMEGA X CONTROL CENTER")

    tabs = st.tabs(
        [
            "🎯 Signal Engine",
            "📊 Indicators",
            "🤖 Katlego AI",
            "🎨 Appearance",
            "📱 Telegram",
            "🛡 Risk",
            "🖥 Dashboard",
        ]
    )

    # -------------------------------------------------------------------------
    # SIGNAL ENGINE
    # -------------------------------------------------------------------------

    with tabs[0]:

        st.markdown("### 🎯 Signal Engine")

        st.session_state.min_tf = st.slider(
            "Minimum timeframe agreement",
            1,
            4,
            int(st.session_state.min_tf),
        )

        st.session_state.min_score = st.slider(
            "Minimum signal score",
            0,
            100,
            int(st.session_state.min_score),
        )

        st.session_state.min_rr = st.number_input(
            "Minimum R:R",
            min_value=0.1,
            max_value=10.0,
            value=float(st.session_state.min_rr),
            step=0.1,
        )

        st.markdown(
            f"""
            <div class="card">

                <div class="card-title">
                    CURRENT ENGINE RULES
                </div>

                <div>
                    TF Agreement:
                    <b>{st.session_state.min_tf}/4</b>
                </div>

                <div>
                    Minimum Score:
                    <b>{st.session_state.min_score}/100</b>
                </div>

                <div>
                    Minimum R:R:
                    <b>{st.session_state.min_rr:.2f}</b>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning(
            "These session settings affect this dashboard. "
            "Your worker.py still reads its own config.py/env thresholds."
        )

    # -------------------------------------------------------------------------
    # INDICATORS
    # -------------------------------------------------------------------------

    with tabs[1]:

        st.markdown("### 📊 Indicator Library")

        indicators = {
            "RSI 14": True,
            "MACD": True,
            "EMA Cross": True,
            "VWAP": True,
            "ADX": True,
            "ATR": True,
            "Volume": True,
            "Money Flow": True,
            "Ichimoku": True,
            "Bollinger Bands": True,
            "Stochastic": True,
            "Liquidity Sweeps": True,
            "Market Structure": True,
            "BOS": True,
            "CHoCH": True,
            "Fair Value Gap": True,
            "Order Blocks": True,
            "Premium / Discount": True,
        }

        cols = st.columns(3)

        for i, (name, default) in enumerate(
            indicators.items()
        ):

            with cols[i % 3]:

                st.checkbox(
                    name,
                    value=default,
                    key=f"indicator_{i}",
                )

        st.caption(
            "These controls define the dashboard presentation layer. "
            "The actual calculations remain in engine.py."
        )

    # -------------------------------------------------------------------------
    # KATLEGO
    # -------------------------------------------------------------------------

    with tabs[2]:

        st.markdown("### 🤖 Katlego AI")

        st.session_state.katlego_enabled = st.toggle(
            "Enable Katlego AI",
            st.session_state.katlego_enabled,
        )

        st.session_state.katlego_auto_analysis = st.toggle(
            "Automatic market narration",
            st.session_state.katlego_auto_analysis,
        )

        st.session_state.katlego_detail = st.select_slider(
            "Intelligence depth",
            options=[
                "Basic",
                "Advanced",
                "Institutional",
                "OMEGA MAX",
            ],
            value=st.session_state.katlego_detail,
        )

        st.session_state.katlego_style = st.selectbox(
            "Response style",
            [
                "Professional",
                "Short Signal",
                "Trader",
                "Institutional",
            ],
        )

        st.checkbox(
            "Explain why signal was blocked",
            value=True,
        )

        st.checkbox(
            "Explain liquidity structure",
            value=True,
        )

        st.checkbox(
            "Explain MTF conflict",
            value=True,
        )

        st.checkbox(
            "Explain risk/reward",
            value=True,
        )

    # -------------------------------------------------------------------------
    # APPEARANCE
    # -------------------------------------------------------------------------

    with tabs[3]:

        st.markdown("### 🎨 OMEGA Appearance")

        selected_theme = st.selectbox(
            "Dashboard Theme",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(
                st.session_state.background
            ),
        )

        if selected_theme != st.session_state.background:

            st.session_state.background = selected_theme

            st.rerun()

        st.markdown(
            "### 🖼 Wallpaper / Background"
        )

        wallpaper = st.selectbox(
            "Wallpaper",
            [
                "OMEGA DARK",
                "ROYAL GOLD",
                "TRADINGVIEW BLACK",
                "MIDNIGHT BLUE",
            ],
        )

        if wallpaper != st.session_state.background:

            st.session_state.background = wallpaper

            st.rerun()

        st.session_state.compact_mode = st.toggle(
            "Compact dashboard mode",
            st.session_state.compact_mode,
        )

        st.selectbox(
            "Gold intensity",
            [
                "Soft",
                "Normal",
                "Strong",
                "Royal",
            ],
            index=1,
        )

        st.info(
            "Custom ancestor wallpapers can be added later as local image "
            "assets. This version intentionally does not embed copyrighted "
            "or personal images into the application."
        )

    # -------------------------------------------------------------------------
    # TELEGRAM
    # -------------------------------------------------------------------------

    with tabs[4]:

        st.markdown("### 📱 Telegram Alert Controls")

        st.session_state.telegram_enabled = st.toggle(
            "Telegram alerts enabled",
            st.session_state.telegram_enabled,
        )

        st.checkbox(
            "Only confirmed BUY/SELL",
            value=True,
        )

        st.checkbox(
            "High-score alerts",
            value=True,
        )

        st.checkbox(
            "MTF alignment alerts",
            value=True,
        )

        st.checkbox(
            "Liquidity sweep alerts",
            value=False,
        )

        st.checkbox(
            "Order block alerts",
            value=False,
        )

        st.checkbox(
            "FVG alerts",
            value=False,
        )

    # -------------------------------------------------------------------------
    # RISK
    # -------------------------------------------------------------------------

    with tabs[5]:

        st.markdown("### 🛡 Risk Management")

        st.session_state.account_zar = st.number_input(
            "Account balance",
            min_value=100.0,
            value=float(
                st.session_state.account_zar
            ),
            step=100.0,
        )

        st.session_state.risk_pct = st.slider(
            "Risk per signal",
            0.1,
            5.0,
            float(st.session_state.risk_pct),
            0.1,
        )

        st.checkbox(
            "Show position size",
            value=True,
        )

        st.checkbox(
            "Show stop distance",
            value=True,
        )

        st.checkbox(
            "Warn when R:R is below threshold",
            value=True,
        )

    # -------------------------------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------------------------------

    with tabs[6]:

        st.markdown("### 🖥 Dashboard Modules")

        st.session_state.show_chart = st.toggle(
            "Price chart",
            st.session_state.show_chart,
        )

        st.session_state.show_indicators = st.toggle(
            "Indicator panel",
            st.session_state.show_indicators,
        )

        st.session_state.show_reasoning = st.toggle(
            "Katlego reasoning",
            st.session_state.show_reasoning,
        )

        st.session_state.show_market_strength = st.toggle(
            "Market strength",
            st.session_state.show_market_strength,
        )

        st.session_state.show_mtf = st.toggle(
            "Multi-timeframe",
            st.session_state.show_mtf,
        )

        st.session_state.show_order_blocks = st.toggle(
            "Order blocks",
            st.session_state.show_order_blocks,
        )

        st.session_state.show_fvg = st.toggle(
            "Fair Value Gaps",
            st.session_state.show_fvg,
        )

        st.session_state.show_liquidity = st.toggle(
            "Liquidity pools",
            st.session_state.show_liquidity,
        )

        st.session_state.show_premium_discount = st.toggle(
            "Premium / Discount",
            st.session_state.show_premium_discount,
        )


# =============================================================================
# HELP
# =============================================================================

elif page == "❓ Help":

    st.subheader("❓ SEKWAILA OMEGA X GUIDE")

    st.markdown(
        """
### 👑 Dashboard
Clean overview of the selected trading pair, signal, score,
entry, TP levels, stop and market structure.

### 📡 Market Scanner
Scans every asset defined in `config.py`.

### 🔥 Market Heatmap
Ranks markets by their current OMEGA score.

### 🤖 Katlego AI
Explains the current engine output using market structure,
regime, liquidity, premium/discount and timeframe information.

### 📊 Multi-Timeframe
Shows 1D, 4H, 1H and 15M alignment.

### 🔗 Correlation
Displays live rolling correlations where data is available.

### 📒 Trade Journal
Records executed/observed trades.

### 📈 Performance
Calculates statistics from journaled outcomes.

### 📱 Telegram
Displays and controls alert preferences.

### ⚙️ Settings
Controls dashboard presentation, signal thresholds,
indicator display, Katlego configuration, risk controls,
Telegram preferences and appearance.

---

### IMPORTANT

SEKWAILA OMEGA X is a **signal-only** system.

It does not place broker orders.

The displayed score is a rules-based heuristic and should not
be interpreted as a guaranteed probability of winning.

Always verify market data and manage risk independently.
"""
    )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.markdown(
    f"""
    <div style="text-align:center;color:{T["muted"]};font-size:10px;">
        👑 SEKWAILA OMEGA X
        • LIVE MARKET INTELLIGENCE
        • SIGNAL ONLY
        • KATLEGO AI
        • {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    """,
    unsafe_allow_html=True,
)
