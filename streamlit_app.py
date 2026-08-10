"""
SEKWAILA OMEGA X — STREAMLIT TRADING DASHBOARD
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone

from signals.signal_engine import (
    generate_omega_signal,
    calculate_position_size_for_symbol,
    fetch_usdzar_rate,
)

# -----------------------------------------------------------------------------
# 1. ASSET CONFIGURATION & UI STYLES
# -----------------------------------------------------------------------------
ASSETS = {
    "BTCUSD": "BTC-USD",
    "US30": "^DJI",
    "XAUUSD": "GC=F"
}

st.set_page_config(
    page_title="SEKWAILA OMEGA X — Terminal",
    page_icon="👑",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 50% 10%, #0d1527 0%, #050810 80%);
    color: #f4f7fb;
}
.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: rgba(13, 21, 39, 0.85);
    border: 1px solid #1e293b;
    border-radius: 12px;
    margin-bottom: 20px;
}
.brand-title {
    font-size: 1.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.signal-card {
    background: rgba(15, 23, 42, 0.75);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #1e293b;
    margin-bottom: 12px;
}
.glow-buy { color: #10b981; border: 1px solid #10b981; padding: 4px 10px; border-radius: 12px; font-weight: 800; }
.glow-sell { color: #f43f5e; border: 1px solid #f43f5e; padding: 4px 10px; border-radius: 12px; font-weight: 800; }
.glow-neutral { color: #f59e0b; border: 1px solid #f59e0b; padding: 4px 10px; border-radius: 12px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & HEADER
# -----------------------------------------------------------------------------
if "active_pair" not in st.session_state:
    st.session_state.active_pair = None

now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

st.markdown(f"""
<div class="terminal-header">
    <div>
        <div class="brand-title">👑 SEKWAILA OMEGA X</div>
        <div style="color: #64748b; font-size: 0.75rem;">MARKET INTELLIGENCE ENGINE</div>
    </div>
    <div style="text-align: right; color: #94a3b8; font-size: 0.85rem;">
        <div>Engine Status: <span style="color:#10b981; font-weight:700;">● LIVE</span></div>
        <div>Sync: <strong>{now_utc}</strong></div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. ROUTING & CONTROLLER
# -----------------------------------------------------------------------------
if not st.session_state.active_pair:
    st.subheader("LIVE PAIR SIGNALS")
    cols = st.columns(3)
    
    for idx, (sym, tkr) in enumerate(ASSETS.items()):
        col = cols[idx % 3]
        res = generate_omega_signal(sym, tkr)
        
        with col:
            bias = res.get("bias", "NEUTRAL")
            glow_cls = "glow-buy" if bias == "BUY" else "glow-sell" if bias == "SELL" else "glow-neutral"
            
            st.markdown(f"""
            <div class="signal-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{sym}</h3>
                    <span class="{glow_cls}">{bias}</span>
                </div>
                <p style="margin-top:10px; color:#94a3b8; font-size:0.9rem;">
                    Score: <strong>{res.get('score', 0)}</strong> | R:R: <strong>{res.get('rr', 0)}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Open {sym} Desk", key=f"btn_{sym}", use_container_width=True):
                st.session_state.active_pair = sym
                st.rerun()

else:
    sym = st.session_state.active_pair
    tkr = ASSETS[sym]
    
    if st.button("← Back to Dashboard"):
        st.session_state.active_pair = None
        st.rerun()

    res = generate_omega_signal(sym, tkr)
    st.title(f"{sym} Trading Workspace")

    if not res.get("ok"):
        st.error(f"Failed to load engine data: {res.get('reason')}")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Bias", res.get("bias"))
        m2.metric("Entry", f"{res.get('entry'):,.2f}")
        m3.metric("Stop Loss", f"{res.get('stop'):,.2f}")
        m4.metric("TP1", f"{res.get('tp1'):,.2f}")

        # Position Sizing
        usd_zar = fetch_usdzar_rate()
        pos = calculate_position_size_for_symbol(sym, 10000 / usd_zar, 1.0, res.get("entry", 0), res.get("stop", 0))
        if pos:
            st.info(f"Recommended Lot Size: **{pos.get('lots')}** (Risk: ${pos.get('risk_amount_usd')} USD)")

        # Plotly Candlestick Chart
        df = res.get("data", {}).get("15M")
        if df is not None and not df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
            )])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
