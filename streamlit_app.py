"""
SEKWAILA OMEGA X — STREAMLIT LIVE ENGINE
Dashboard wrapper for signals.signal_engine.generate_omega_signal().
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

from config import ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR
from signals.signal_engine import (
    generate_omega_signal,
    calculate_position_size_for_symbol,
    fetch_usdzar_rate,
    compute_live_correlation_matrix,
)

st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#070b12,#0b111b 55%,#070a10);
    color:#f4f7fb;
}
[data-testid="stSidebar"] { background:#080d15; }
.omega-title {font-size:2.35rem;font-weight:800;letter-spacing:.03em;}
.omega-subtitle {color:#9aa8bb;}
.card {
    background:rgba(17,25,38,.88);
    border:1px solid #243247;
    border-radius:14px;
    padding:15px;
    min-height:95px;
}
.label {
    color:#93a4ba;
    font-size:.76rem;
    text-transform:uppercase;
    letter-spacing:.08em;
}
.value {font-size:1.4rem;font-weight:750;margin-top:5px;}
.buy {color:#34d399;}
.sell {color:#fb7185;}
.neutral {color:#fbbf24;}
.signal {
    background:rgba(10,16,26,.92);
    border:1px solid #29384e;
    border-radius:16px;
    padding:20px;
}
</style>
""", unsafe_allow_html=True)


def num(value, default=0.0):
    try:
        value = float(value)
        if pd.notna(value):
            return value
    except Exception:
        pass
    return default


def price(value, decimals=4):
    value = num(value)
    return "—" if value == 0 else f"{value:,.{decimals}f}"


def cls(value):
    value = str(value).upper()
    return "buy" if value == "BUY" else "sell" if value == "SELL" else "neutral"


def metric_card(label, value, css=""):
    st.markdown(
        f'<div class="card"><div class="label">{label}</div>'
        f'<div class="value {css}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def chart_for(res):
    df = res.get("data", {}).get("15M")
    if df is None or df.empty:
        return None

    df = df.tail(180)
    fig = go.Figure(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="15M",
    ))

    if res.get("bias") in ("BUY", "SELL"):
        for name, val in [
            ("Entry", res.get("entry")),
            ("Stop", res.get("stop")),
            ("TP1", res.get("tp1")),
            ("TP2", res.get("tp2")),
            ("TP3", res.get("tp3")),
        ]:
            val = num(val)
            if val > 0:
                fig.add_hline(
                    y=val,
                    line_dash="dash",
                    annotation_text=f"{name} {price(val)}",
                )

    vwap = num(res.get("vwap_val"))
    if vwap > 0:
        fig.add_hline(
            y=vwap,
            line_dash="dot",
            annotation_text=f"VWAP {price(vwap)}",
        )

    fig.update_layout(
        template="plotly_dark",
        height=540,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
    )
    return fig


# ---------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------

symbols = list(ASSETS.keys())
if not symbols:
    st.error("ASSETS is empty. Check config.py.")
    st.stop()

default_symbol = st.session_state.get("selected_symbol", symbols[0])
if default_symbol not in symbols:
    default_symbol = symbols[0]

st.sidebar.markdown("## 👑 SEKWAILA OMEGA X")
st.sidebar.caption("LIVE ENGINE")

selected_symbol = st.sidebar.selectbox(
    "Active Asset Focus",
    symbols,
    index=symbols.index(default_symbol),
)
st.session_state.selected_symbol = selected_symbol

account_currency = st.sidebar.selectbox("Account Currency", ["ZAR", "USD"])
account_balance = st.sidebar.number_input(
    f"Account Balance ({account_currency})",
    min_value=0.0,
    value=10000.0,
    step=500.0,
)

risk_pct = st.sidebar.slider(
    "Risk per Trade (%)",
    min_value=0.10,
    max_value=5.00,
    value=1.00,
    step=0.10,
)

st.sidebar.markdown("### Engine thresholds")

min_tf = st.sidebar.slider(
    "Minimum TF Agreement",
    min_value=1,
    max_value=4,
    value=int(DEFAULT_MIN_TF_AGREEMENT),
)

min_score = st.sidebar.slider(
    "Minimum Score",
    min_value=0.0,
    max_value=100.0,
    value=float(DEFAULT_MIN_SCORE),
)

min_rr = st.sidebar.number_input(
    "Minimum R:R",
    min_value=0.1,
    max_value=10.0,
    value=float(DEFAULT_MIN_RR),
    step=0.1,
)

refresh_seconds = st.sidebar.selectbox(
    "Auto Refresh",
    [30, 60, 120, 300],
    index=2,
)

if st.sidebar.button("🔄 Refresh Now", width="stretch"):
    st.rerun()

st_autorefresh(
    interval=refresh_seconds * 1000,
    key="omega_refresh",
)

# ---------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------

st.markdown(
    '<div class="omega-title">👑 SEKWAILA OMEGA X</div>'
    '<div class="omega-subtitle">'
    'LIVE ENGINE — DASHBOARD AND TELEGRAM ALERTS SHARE THE SAME CODE'
    '</div>',
    unsafe_allow_html=True,
)

st.caption(
    f"Engine thresholds: {min_tf}/4 TF agreement, "
    f"{min_score:.1f} min score, {min_rr:.1f} min R:R"
)

st.warning(
    "⚠️ Informational only. Not financial advice. "
    "Score is a rules-based heuristic."
)

# ---------------------------------------------------------------------
# ENGINE
# ---------------------------------------------------------------------

ticker = ASSETS[selected_symbol]

with st.spinner(f"Evaluating {selected_symbol} ({ticker})..."):
    try:
        result = generate_omega_signal(
            selected_symbol,
            ticker,
            min_tf=min_tf,
            min_score=min_score,
            min_rr=min_rr,
        )
    except TypeError:
        result = generate_omega_signal(
            selected_symbol,
            ticker,
            min_tf,
            min_score,
            min_rr,
        )
    except Exception as exc:
        result = {
            "ok": False,
            "symbol": selected_symbol,
            "ticker": ticker,
            "reason": str(exc),
        }

if not result.get("ok"):
    st.error(
        f"Engine could not evaluate {selected_symbol}: "
        f"{result.get('reason', 'Unknown error')}"
    )
    if result.get("data_integrity"):
        st.subheader("Data Integrity")
        st.json(result["data_integrity"])
    st.stop()

bias = result.get("bias", "NEUTRAL")
bull_score = num(result.get("bull_score"))
bear_score = num(result.get("bear_score"))
tf_count = len(result.get("tf_biases", {})) or 4
agreement = max(
    int(result.get("bull_tf_count", 0)),
    int(result.get("bear_tf_count", 0)),
)

# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------

st.markdown("## ⚔️ BULL / BEAR SCORE")

c1, c2, c3, c4 = st.columns(4)

with c1:
    metric_card("Bull Score", f"{bull_score:.1f}%", "buy")
with c2:
    metric_card("Bear Score", f"{bear_score:.1f}%", "sell")
with c3:
    market_bias = (
        "LEAN BULL" if bull_score > bear_score
        else "LEAN BEAR" if bear_score > bull_score
        else "NEUTRAL"
    )
    metric_card(
        "Market Bias",
        market_bias,
        cls("BUY" if bull_score > bear_score else "SELL"),
    )
with c4:
    icon = "🟢" if bias == "BUY" else "🔴" if bias == "SELL" else "🟡"
    metric_card("Signal", f"{icon} {bias}", cls(bias))

# ---------------------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------------------

st.markdown("## 📊 INDICATOR PANEL")

i1, i2, i3, i4 = st.columns(4)

with i1:
    metric_card("Price / VWAP", result.get("vwap_status", "UNKNOWN"))
    metric_card("RSI (14)", f"{num(result.get('rsi')):.1f}")

with i2:
    metric_card("MACD Trend", result.get("macd_trend", "NEUTRAL"))
    metric_card("EMA Cross", result.get("ema_cross", "NEUTRAL"))

with i3:
    adx = result.get("regime", {}).get("adx", 0)
    metric_card("ADX Power", f"{num(adx):.2f}")
    metric_card("ATR 14", price(result.get("atr")))

with i4:
    metric_card("Vol Status", result.get("vol_status", "UNKNOWN"))
    metric_card(
        "Trend Strength",
        "STRONG" if result.get("trend_strong") else "WEAK",
    )

# ---------------------------------------------------------------------
# CONTEXT
# ---------------------------------------------------------------------

st.markdown("## 📈 MARKET CONTEXT")

r1, r2, r3 = st.columns(3)

with r1:
    regime = result.get("regime", {})
    st.markdown("### 📈 REGIME")
    st.metric("Regime", regime.get("regime", "UNKNOWN"))
    st.write(
        f"ADX: **{num(regime.get('adx')):.2f}** | "
        f"Vol Ratio: **{num(regime.get('vol_ratio'), 1):.2f}**"
    )
    st.caption(result.get("trend_detail", ""))

with r2:
    st.markdown("### 🕐 SESSION")
    st.metric("Session", result.get("session", "UNKNOWN"))
    st.write(
        f"Quality: **{num(result.get('session_quality'), 50):.1f}%**"
    )

with r3:
    st.markdown("### 💎 PREMIUM / DISCOUNT")
    pd_info = result.get("pd_info", {})
    st.metric("Zone", result.get("pd_zone", "UNKNOWN"))
    st.write(f"Equilibrium: **{price(pd_info.get('equilibrium'))}**")
    st.write(f"Low: {price(pd_info.get('swing_low'))}")
    st.write(f"High: {price(pd_info.get('swing_high'))}")

# ---------------------------------------------------------------------
# POSITION SIZING
# ---------------------------------------------------------------------

st.markdown("## 💰 POSITION SIZE")

if bias in ("BUY", "SELL"):
    sizing_usd = account_balance

    if account_currency == "ZAR":
        usd_zar = fetch_usdzar_rate()
        if usd_zar and usd_zar > 0:
            sizing_usd = account_balance / usd_zar
            st.caption(
                f"Live USD/ZAR: {usd_zar:.4f} | "
                f"Sizing balance: ${sizing_usd:,.2f}"
            )
        else:
            sizing_usd = 0
            st.warning("USD/ZAR unavailable; position size withheld.")

    position = calculate_position_size_for_symbol(
        selected_symbol,
        sizing_usd,
        risk_pct,
        result.get("entry", 0),
        result.get("stop", 0),
    )

    if position:
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Risk Amount", f"${position['risk_amount_usd']:,.2f}")
        with p2:
            st.metric("Stop Distance", price(position["stop_distance"]))
        with p3:
            st.metric("Lots", f"{position['lots']:.4f}")
        with p4:
            st.metric("Contract Size", f"{position['contract_size']:g}")
    else:
        st.info("Position size unavailable.")
else:
    st.info("No active signal.")

# ---------------------------------------------------------------------
# SIGNAL
# ---------------------------------------------------------------------

st.markdown(f"## {selected_symbol}")
st.markdown("### SCORE-BASED SIGNAL")

if bias == "BUY":
    st.success("🟢 BUY SETUP")
elif bias == "SELL":
    st.error("🔴 SELL SETUP")
else:
    st.warning("🟡 NEUTRAL / NO SETUP")

st.metric("Score", f"{num(result.get('score')):.1f}/100")

st.caption(
    f"Timeframe agreement: {agreement}/{tf_count} | "
    f"Minimum: {min_tf}/{tf_count} | "
    f"Score threshold: {min_score:.1f}"
)

if bias == "NEUTRAL":
    st.info(result.get("reason") or "No actionable setup.")

q1, q2, q3 = st.columns(3)
with q1:
    st.metric("ENTRY", price(result.get("entry")))
    st.metric("TP1", price(result.get("tp1")))
with q2:
    st.metric("STOP", price(result.get("stop")))
    st.metric("TP2", price(result.get("tp2")))
with q3:
    rr = num(result.get("rr"))
    st.metric("R:R to TP2", f"{rr:.2f}" if rr else "—")
    st.metric("TP3", price(result.get("tp3")))

# ---------------------------------------------------------------------
# CHART
# ---------------------------------------------------------------------

st.markdown("## 📉 PRIMARY 15M CHART")

fig = chart_for(result)
if fig:
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displaylogo": False, "responsive": True},
    )
else:
    st.info("15M chart data unavailable.")

# ---------------------------------------------------------------------
# MULTI-TIMEFRAME
# ---------------------------------------------------------------------

st.markdown("## 🧭 MULTI-TIMEFRAME AGREEMENT")

rows = []
tf_biases = result.get("tf_biases", {})
tf_structures = result.get("tf_structures", {})

for tf in tf_biases:
    rows.append({
        "Timeframe": tf,
        "Bias": tf_biases.get(tf, "NEUTRAL"),
        "Structure": tf_structures.get(tf, "NONE"),
    })

if rows:
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
    )

st.write(
    f"**Bullish:** {result.get('bull_tf_count', 0)}/{tf_count} | "
    f"**Bearish:** {result.get('bear_tf_count', 0)}/{tf_count} | "
    f"**Required:** {min_tf}/{tf_count}"
)

# ---------------------------------------------------------------------
# SMC
# ---------------------------------------------------------------------

st.markdown("## 🧠 SMART MONEY CONCEPTS")

s1, s2 = st.columns(2)

with s1:
    st.markdown("### Market Structure")
    st.write(f"**{result.get('structure', 'NONE')}**")

    st.markdown("### Order Block")
    st.write(f"**{result.get('ob_type', 'NONE')}**")

    zone = result.get("ob_zone")
    if zone:
        st.write(f"Zone: **{price(zone[0])} — {price(zone[1])}**")

    st.write(
        f"Mitigated: **{'YES' if result.get('ob_mitigated') else 'NO'}**"
    )
    st.write(
        f"Invalidated: **{'YES' if result.get('ob_invalidated') else 'NO'}**"
    )

with s2:
    st.markdown("### Liquidity Sweep")
    st.write("**YES**" if result.get("sweep") else "**NO**")
    st.caption(result.get("sweep_detail", "NO_SWEEP"))

    st.markdown("### Fair Value Gap")
    fvg = result.get("fvg")
    if fvg:
        st.write(f"**{fvg.get('type', 'UNKNOWN')}**")
        zone = fvg.get("zone")
        if zone:
            st.write(f"Zone: **{price(zone[0])} — {price(zone[1])}**")
        st.write(
            f"Filled: **{'YES' if fvg.get('filled') else 'NO'}**"
        )
    else:
        st.write("**NONE / NO UNFILLED FVG**")

# ---------------------------------------------------------------------
# CORRELATION
# ---------------------------------------------------------------------

with st.expander("📊 Live Asset Correlation"):
    if st.button("Calculate Correlation Matrix", width="stretch"):
        with st.spinner("Fetching correlation data..."):
            try:
                corr = compute_live_correlation_matrix()
            except Exception as exc:
                corr = None
                st.error(f"Correlation calculation failed: {exc}")

        if corr is not None and not corr.empty:
            st.dataframe(corr, width="stretch")
        else:
            st.info("Not enough live data to calculate correlation.")

# ---------------------------------------------------------------------
# DATA INTEGRITY
# ---------------------------------------------------------------------

with st.expander("🛡️ Data Integrity"):
    integrity = result.get("data_integrity", {})
    if integrity:
        st.dataframe(
            pd.DataFrame([
                {"Timeframe": tf, "Status": status}
                for tf, status in integrity.items()
            ]),
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "The engine removes the currently forming candle before "
        "indicator and structure calculations."
    )

# ---------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------

now = datetime.now(timezone.utc)
st.markdown("---")
st.caption(
    f"SEKWAILA OMEGA X • {selected_symbol} • {ticker} • "
    f"{now.strftime('%Y-%m-%d %H:%M:%S UTC')} • "
    f"Auto-refresh {refresh_seconds}s"
)
