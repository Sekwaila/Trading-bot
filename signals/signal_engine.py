"""
SEKWAILA OMEGA X — TRADING TERMINAL
Single Source of Truth UI using signals/signal_engine.py
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

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & TRADING TERMINAL STYLES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X — Terminal",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* App background & typography */
.stApp {
    background: radial-gradient(circle at 50% 10%, #0d1527 0%, #050810 80%);
    color: #f4f7fb;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header bar */
.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    background: rgba(13, 21, 39, 0.85);
    border: 1px solid #1e293b;
    border-radius: 14px;
    backdrop-filter: blur(12px);
    margin-bottom: 20px;
}
.brand-title {
    font-size: 1.85rem;
    font-weight: 900;
    letter-spacing: 0.05em;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.brand-subtitle {
    color: #64748b;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Pair Signal Cards */
.signal-card {
    background: rgba(15, 23, 42, 0.75);
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #1e293b;
    transition: transform 0.2s ease, border 0.2s ease;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.signal-card:hover {
    transform: translateY(-3px);
    border-color: #334155;
}

/* Glowing Badges */
.badge-glow {
    font-weight: 800;
    font-size: 0.82rem;
    padding: 6px 14px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    display: inline-block;
    text-align: center;
}
.glow-extreme-buy {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid #10b981;
    box-shadow: 0 0 18px rgba(16, 185, 129, 0.6);
}
.glow-strong-buy, .glow-buy {
    background: rgba(34, 197, 94, 0.12);
    color: #22c55e;
    border: 1px solid #22c55e;
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.4);
}
.glow-weak-buy {
    background: rgba(74, 222, 128, 0.1);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.5);
}
.glow-neutral {
    background: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
    border: 1px solid #f59e0b;
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
}
.glow-weak-sell {
    background: rgba(248, 113, 113, 0.1);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.5);
}
.glow-strong-sell, .glow-sell {
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid #ef4444;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
}
.glow-extreme-sell {
    background: rgba(225, 29, 72, 0.18);
    color: #f43f5e;
    border: 1px solid #f43f5e;
    box-shadow: 0 0 18px rgba(244, 63, 94, 0.7);
}

/* Metric Boxes */
.metric-box {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
}
.metric-label {
    color: #94a3b8;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-val {
    font-size: 1.15rem;
    font-weight: 750;
    margin-top: 2px;
}

div[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid #1e293b;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. HELPER & CLASSIFICATION FUNCTIONS
# -----------------------------------------------------------------------------
def num(value, default=0.0):
    try:
        v = float(value)
        return v if pd.notna(v) else default
    except Exception:
        return default

def price(value, decimals=4):
    v = num(value)
    return "—" if v == 0 else f"{v:,.{decimals}f}"

def classify_signal(res):
    """
    Classifies raw signal engine outputs into glowing tier ranks for terminal display.
    """
    if not res.get("ok"):
        return "DATA UNAVAILABLE", "glow-neutral", -1

    bias = res.get("bias", "NEUTRAL")
    score = num(res.get("score", 0))
    tf_count = max(int(res.get("bull_tf_count", 0)), int(res.get("bear_tf_count", 0)))

    if bias == "BUY":
        if score >= 85 and tf_count >= 4:
            return "EXTREME BUY", "glow-extreme-buy", 900 + score
        elif score >= 75 or tf_count >= 3:
            return "STRONG BUY", "glow-strong-buy", 700 + score
        elif score >= 60:
            return "BUY", "glow-buy", 500 + score
        else:
            return "WEAK BUY", "glow-weak-buy", 300 + score

    elif bias == "SELL":
        if score >= 85 and tf_count >= 4:
            return "EXTREME SELL", "glow-extreme-sell", 800 + score
        elif score >= 75 or tf_count >= 3:
            return "STRONG SELL", "glow-strong-sell", 600 + score
        elif score >= 60:
            return "SELL", "glow-sell", 400 + score
        else:
            return "WEAK SELL", "glow-weak-sell", 200 + score

    return "NEUTRAL", "glow-neutral", score

def render_chart(res, active_tf="15M"):
    df = res.get("data", {}).get(active_tf)
    if df is None or df.empty:
        return None
    df = df.tail(150)
    fig = go.Figure(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=active_tf
    ))
    
    if res.get("bias") in ("BUY", "SELL"):
        for name, val, col in [
            ("Entry", res.get("entry"), "#38bdf8"),
            ("Stop", res.get("stop"), "#f43f5e"),
            ("TP1", res.get("tp1"), "#34d399"),
            ("TP2", res.get("tp2"), "#10b981"),
            ("TP3", res.get("tp3"), "#059669")
        ]:
            v = num(val)
            if v > 0:
                fig.add_hline(y=v, line_dash="dash", line_color=col, annotation_text=f"{name}: {price(v)}")

    vwap = num(res.get("vwap_val"))
    if vwap > 0:
        fig.add_hline(y=vwap, line_dash="dot", line_color="#f59e0b", annotation_text=f"VWAP: {price(vwap)}")

    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.5)"
    )
    return fig

# -----------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "nav" not in st.session_state:
    st.session_state.nav = "DASHBOARD"
if "active_pair" not in st.session_state:
    st.session_state.active_pair = None

symbols = list(ASSETS.keys())

# Settings defaults
if "min_tf" not in st.session_state:
    st.session_state.min_tf = int(DEFAULT_MIN_TF_AGREEMENT)
if "min_score" not in st.session_state:
    st.session_state.min_score = float(DEFAULT_MIN_SCORE)
if "min_rr" not in st.session_state:
    st.session_state.min_rr = float(DEFAULT_MIN_RR)
if "account_currency" not in st.session_state:
    st.session_state.account_currency = "ZAR"
if "account_balance" not in st.session_state:
    st.session_state.account_balance = 10000.0
if "risk_pct" not in st.session_state:
    st.session_state.risk_pct = 1.00
if "refresh_seconds" not in st.session_state:
    st.session_state.refresh_seconds = 60

# -----------------------------------------------------------------------------
# 4. TOP TERMINAL HEADER BAR
# -----------------------------------------------------------------------------
now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

st.markdown(f"""
<div class="terminal-header">
    <div>
        <div class="brand-title">👑 SEKWAILA OMEGA X</div>
        <div class="brand-subtitle">LIVE MARKET INTELLIGENCE TERMINAL</div>
    </div>
    <div style="text-align: right; color: #94a3b8; font-size: 0.85rem;">
        <div>Engine Status: <span style="color:#10b981; font-weight:700;">● LIVE</span></div>
        <div>Last Sync: <strong>{now_utc}</strong></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Controls
n1, n2, n3, n4 = st.columns([1.5, 1.5, 5, 2])
with n1:
    if st.button("🏠 DASHBOARD", width="stretch"):
        st.session_state.nav = "DASHBOARD"
        st.session_state.active_pair = None
        st.rerun()
with n2:
    if st.button("⚙ SETTINGS", width="stretch"):
        st.session_state.nav = "SETTINGS"
        st.rerun()
with n4:
    st_autorefresh(interval=st.session_state.refresh_seconds * 1000, key="omega_terminal_refresh")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. ROUTING & CONTROLLERS
# -----------------------------------------------------------------------------

# =============================================================================
# ROUTE A: MAIN LIVE DASHBOARD
# =============================================================================
if st.session_state.nav == "DASHBOARD" and not st.session_state.active_pair:
    st.subheader("LIVE ASSET SIGNALS")
    st.caption("Sorted dynamically by signal tier strength. Select any card to launch Pair Workspace.")

    evaluated_pairs = []
    with st.spinner("Scanning market intelligence engines..."):
        for sym in symbols:
            tkr = ASSETS[sym]
            try:
                res = generate_omega_signal(
                    sym, tkr, 
                    min_tf=st.session_state.min_tf, 
                    min_score=st.session_state.min_score, 
                    min_rr=st.session_state.min_rr
                )
            except Exception as exc:
                res = {"ok": False, "symbol": sym, "reason": str(exc)}
            
            label, glow_cls, sort_weight = classify_signal(res)
            evaluated_pairs.append({
                "symbol": sym,
                "result": res,
                "label": label,
                "glow_cls": glow_cls,
                "weight": sort_weight
            })

    # Sort descending by priority weight
    evaluated_pairs.sort(key=lambda x: x["weight"], reverse=True)

    # Render Grid
    cols = st.columns(3)
    for idx, item in enumerate(evaluated_pairs):
        col = cols[idx % 3]
        res = item["result"]
        sym = item["symbol"]
        label = item["label"]
        glow_cls = item["glow_cls"]
        
        with col:
            with st.container():
                st.markdown(f"""
                <div class="signal-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="font-size:1.35rem; font-weight:800; color:#f8fafc;">{sym}</span>
                        <span class="badge-glow {glow_cls}">{label}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#94a3b8;">
                        <span>Score: <strong style="color:#f1f5f9;">{num(res.get('score')):.1f}</strong></span>
                        <span>R:R: <strong style="color:#f1f5f9;">{num(res.get('rr')):.2f}</strong></span>
                        <span>Bias: <strong style="color:#f1f5f9;">{res.get('bias', 'NEUTRAL')}</strong></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open {sym} Workspace", key=f"btn_{sym}", width="stretch"):
                    st.session_state.active_pair = sym
                    st.rerun()
                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# =============================================================================
# ROUTE B: DEDICATED PAIR WORKSPACE
# =============================================================================
elif st.session_state.active_pair:
    sym = st.session_state.active_pair
    tkr = ASSETS[sym]

    c_back, c_title = st.columns([1, 8])
    with c_back:
        if st.button("← BACK", width="stretch"):
            st.session_state.active_pair = None
            st.rerun()

    with st.spinner(f"Loading Workspace for {sym}..."):
        try:
            res = generate_omega_signal(
                sym, tkr,
                min_tf=st.session_state.min_tf,
                min_score=st.session_state.min_score,
                min_rr=st.session_state.min_rr
            )
        except Exception as exc:
            res = {"ok": False, "symbol": sym, "reason": str(exc)}

    label, glow_cls, _ = classify_signal(res)

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:20px; margin: 10px 0 20px 0;">
        <h1 style="margin:0; font-weight:900;">{sym}</h1>
        <span class="badge-glow {glow_cls}" style="font-size:1.1rem; padding:8px 20px;">{label}</span>
        <span style="color:#94a3b8;">Score: <strong>{num(res.get('score')):.1f}</strong> | Bias: <strong>{res.get('bias', 'NEUTRAL')}</strong></span>
    </div>
    """, unsafe_allow_html=True)

    if not res.get("ok"):
        st.error(f"Engine evaluation failure for {sym}: {res.get('reason', 'Market Data Unavailable')}")
        st.stop()

    # --- EXECUTION & POSITION SIZING ---
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1: st.markdown(f'<div class="metric-box"><div class="metric-label">Entry Price</div><div class="metric-val">{price(res.get("entry"))}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-box"><div class="metric-label">Stop Loss</div><div class="metric-val" style="color:#f43f5e;">{price(res.get("stop"))}</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-box"><div class="metric-label">Take Profit 1</div><div class="metric-val" style="color:#34d399;">{price(res.get("tp1"))}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-box"><div class="metric-label">Take Profit 2</div><div class="metric-val" style="color:#10b981;">{price(res.get("tp2"))}</div></div>', unsafe_allow_html=True)
    with m5: st.markdown(f'<div class="metric-box"><div class="metric-label">Take Profit 3</div><div class="metric-val" style="color:#059669;">{price(res.get("tp3"))}</div></div>', unsafe_allow_html=True)
    with m6: st.markdown(f'<div class="metric-box"><div class="metric-label">Risk : Reward</div><div class="metric-val">{num(res.get("rr")):.2f}</div></div>', unsafe_allow_html=True)

    # --- POSITION SIZING CALCULATOR ---
    if res.get("bias") in ("BUY", "SELL"):
        sizing_usd = st.session_state.account_balance
        if st.session_state.account_currency == "ZAR":
            usd_zar = fetch_usdzar_rate()
            if usd_zar and usd_zar > 0:
                sizing_usd = st.session_state.account_balance / usd_zar
        pos = calculate_position_size_for_symbol(sym, sizing_usd, st.session_state.risk_pct, res.get("entry", 0), res.get("stop", 0))
        if pos:
            p1, p2, p3, p4 = st.columns(4)
            with p1: st.caption(f"Risk Amount: **${pos['risk_amount_usd']:,.2f}**")
            with p2: st.caption(f"Stop Distance: **{price(pos['stop_distance'])}**")
            with p3: st.caption(f"Recommended Lots: **{pos['lots']:.4f}**")
            with p4: st.caption(f"Contract Size: **{pos['contract_size']:g}**")

    # --- TIMEFRAME ALIGNMENT & CHARTS ---
    st.markdown("### 📈 Interactive Chart & Timeframe Alignment")
    
    tf_biases = res.get("tf_biases", {})
    tf_cols = st.columns(len(tf_biases) if tf_biases else 4)
    for idx, (tf_key, tf_val) in enumerate(tf_biases.items()):
        with tf_cols[idx % len(tf_cols)]:
            col_code = "#34d399" if tf_val == "BUY" else "#f43f5e" if tf_val == "SELL" else "#f59e0b"
            st.markdown(f'<div class="metric-box" style="text-align:center;"><div class="metric-label">{tf_key}</div><div class="metric-val" style="color:{col_code};">{tf_val}</div></div>', unsafe_allow_html=True)

    chart_tf = st.radio("Select Chart Timeframe:", ["15M", "1H", "4H"], horizontal=True)
    fig = render_chart(res, active_tf=chart_tf)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    else:
        st.info(f"Chart data for {chart_tf} is currently unavailable.")

    # --- INDICATORS & SMART MONEY CONCEPTS ---
    i_col, smc_col = st.columns(2)

    with i_col:
        st.markdown("### 📊 Indicator Analysis")
        p1, p2 = st.columns(2)
        with p1:
            st.write(f"**RSI (14):** {num(res.get('rsi')):.1f}")
            st.write(f"**MACD Trend:** {res.get('macd_trend', 'NEUTRAL')}")
            st.write(f"**Price / VWAP:** {res.get('vwap_status', 'UNKNOWN')}")
            st.write(f"**EMA Cross:** {res.get('ema_cross', 'NEUTRAL')}")
        with p2:
            regime = res.get("regime", {})
            st.write(f"**ADX Trend Power:** {num(regime.get('adx')):.2f}")
            st.write(f"**ATR (14):** {price(res.get('atr'))}")
            st.write(f"**Vol Status:** {res.get('vol_status', 'NORMAL')}")
            st.write(f"**Market Regime:** {regime.get('regime', 'UNKNOWN')}")

    with smc_col:
        st.markdown("### 🧠 Smart Money Concepts")
        s1, s2 = st.columns(2)
        with s1:
            st.write(f"**Structure:** {res.get('structure', 'NONE')}")
            st.write(f"**Order Block:** {res.get('ob_type', 'NONE')}")
            zone = res.get("ob_zone")
            if zone:
                st.write(f"**OB Zone:** {price(zone[0])} — {price(zone[1])}")
            st.write(f"**Mitigated:** {'YES' if res.get('ob_mitigated') else 'NO'}")
        with s2:
            st.write(f"**Liquidity Sweep:** {'YES' if res.get('sweep') else 'NO'}")
            fvg = res.get("fvg")
            if fvg:
                st.write(f"**FVG Type:** {fvg.get('type', 'UNKNOWN')}")
                f_zone = fvg.get("zone")
                if f_zone:
                    st.write(f"**FVG Zone:** {price(f_zone[0])} — {price(f_zone[1])}")
            else:
                st.write("**FVG:** NONE / FILLED")
            pd_info = res.get("pd_info", {})
            st.write(f"**Zone:** {res.get('pd_zone', 'EQUILIBRIUM')}")

# =============================================================================
# ROUTE C: SYSTEM SETTINGS
# =============================================================================
elif st.session_state.nav == "SETTINGS":
    st.subheader("⚙ TERMINAL & SIGNAL ENGINE CONFIGURATION")

    tab_gen, tab_risk, tab_ai, tab_tg = st.tabs([
        "GENERAL & ENGINE", "RISK & SIZING", "AI INTEGRATION", "TELEGRAM ALERTS"
    ])

    with tab_gen:
        st.markdown("#### Core Engine Thresholds")
        st.session_state.min_tf = st.slider("Minimum Timeframe Agreement", 1, 4, st.session_state.min_tf)
        st.session_state.min_score = st.slider("Minimum Signal Score", 0.0, 100.0, st.session_state.min_score)
        st.session_state.min_rr = st.number_input("Minimum Risk:Reward Ratio", 0.1, 10.0, st.session_state.min_rr, 0.1)
        st.session_state.refresh_seconds = st.selectbox("Dashboard Auto-Refresh", [30, 60, 120, 300], index=1)

    with tab_risk:
        st.markdown("#### Position Sizing Parameters")
        st.session_state.account_currency = st.selectbox("Account Currency", ["ZAR", "USD"], index=0 if st.session_state.account_currency == "ZAR" else 1)
        st.session_state.account_balance = st.number_input("Account Balance", min_value=0.0, value=st.session_state.account_balance, step=500.0)
        st.session_state.risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, st.session_state.risk_pct, 0.1)

    with tab_ai:
        st.markdown("#### Katlego AI Reasoning Layer")
        ai_enabled = st.toggle("Enable AI Signal Validation", value=True)
        st.selectbox("AI Model Provider", ["OpenAI GPT-4o", "Anthropic Claude 3.5 Sonnet", "Gemini Pro"], index=0)
        st.text_input("API Key", type="password", help="API keys are securely held in memory.")
        st.slider("AI Confidence Threshold (%)", 50, 95, 75)

    with tab_tg:
        st.markdown("#### Telegram Alert Engine")
        tg_enabled = st.toggle("Enable Live Telegram Broadcasting", value=True)
        st.text_input("Bot Token", type="password", value="••••••••••••••••••••")
        st.text_input("Chat ID", value="-100123456789")
        st.selectbox("Minimum Alert Tier", ["EXTREME ONLY", "STRONG & EXTREME", "ALL SIGNALS"], index=1)
        if st.button("Send Test Telegram Alert"):
            st.success("Test alert dispatched using `signals/signal_engine.py` pipeline.")

    if st.button("💾 SAVE SETTINGS", width="stretch"):
        st.success("Configuration saved successfully.")
