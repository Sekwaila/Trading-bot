# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import os
import datetime

# Import the signal engine and telegram alert (optional)
from signals.signal_engine import generate_omega_signal, get_live_price_for_symbol
from config import ASSETS

# Optional: Telegram alerts (uncomment when ready)
# from telegram_alerter import send_telegram_alert

# Page configuration
st.set_page_config(page_title="SEKWAILA OMEGA X", layout="wide")

# Auto-refresh every 60 seconds (optional)
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 SEKWAILA OMEGA X — SMC Signal Engine")
st.caption("Live prices powered by Twelve Data")

# ------------------------------------------------------------
# Sidebar: Select asset and configure risk
# ------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_symbol = st.selectbox("📊 Select Instrument", ASSETS, index=0)

    st.divider()
    st.subheader("Risk Management")
    account_balance = st.number_input("Account Balance (USD)", min_value=100.0, value=10000.0, step=100.0)
    risk_per_trade = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

    st.divider()
    st.subheader("Signal Filters")
    min_tf_agreement = st.slider("Min TF Agreement (out of 4)", min_value=1, max_value=4, value=2)
    min_score = st.slider("Min Signal Score", min_value=30, max_value=90, value=60, step=5)
    min_rr = st.slider("Min R:R Ratio", min_value=1.0, max_value=5.0, value=1.5, step=0.5)

# ------------------------------------------------------------
# Main content: Generate signal only for the selected asset
# ------------------------------------------------------------
if selected_symbol:
    with st.spinner(f"Fetching data for {selected_symbol}..."):
        # Generate the signal (only one asset – 4 API calls)
        signal = generate_omega_signal(
            symbol=selected_symbol,
            min_tf=min_tf_agreement,
            min_score=min_score,
            min_rr=min_rr,
        )

    # Display signal status
    if not signal.get("ok", False):
        st.error(f"❌ Data unavailable for {selected_symbol}: {signal.get('reason', 'Unknown error')}")
        st.stop()

    # ------------------------------------------------------------
    # Signal Summary (Top)
    # ------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    bias = signal.get("bias", "NEUTRAL")
    score = signal.get("score", 0)
    grade = signal.get("grade", "D")
    rr = signal.get("rr", 0)

    col1.metric("Bias", bias)
    col2.metric("Score", f"{score} / 100")
    col3.metric("Grade", grade)
    col4.metric("R:R", f"{rr:.2f}")

    if bias in ("BUY", "SELL"):
        st.success(f"🔥 **{bias} SIGNAL DETECTED** — {signal.get('structure', 'N/A')}")
        if signal.get("reason"):
            st.info(f"ℹ️ {signal['reason']}")
    else:
        st.warning(f"⏳ No strong signal. Reason: {signal.get('reason', 'Neutral')}")

    # ------------------------------------------------------------
    # Trade Setup
    # ------------------------------------------------------------
    st.subheader("📈 Trade Setup")
    cols = st.columns(6)
    cols[0].metric("Entry", f"{signal['entry']:.2f}")
    cols[1].metric("Stop Loss", f"{signal['stop']:.2f}")
    cols[2].metric("TP1", f"{signal['tp1']:.2f}")
    cols[3].metric("TP2", f"{signal['tp2']:.2f}")
    cols[4].metric("TP3", f"{signal['tp3']:.2f}")
    cols[5].metric("ATR", f"{signal['atr']:.4f}")

    # Position size
    if bias in ("BUY", "SELL"):
        from signals.signal_engine import calculate_position_size_for_symbol
        pos = calculate_position_size_for_symbol(
            symbol=selected_symbol,
            account_balance_usd=account_balance,
            risk_pct=risk_per_trade,
            entry_price=signal['entry'],
            stop_loss_price=signal['stop']
        )
        if pos:
            st.metric("Recommended Lots", pos['lots'])

    # ------------------------------------------------------------
    # Market Structure & SMC Details
    # ------------------------------------------------------------
    st.subheader("🧠 Smart Money Concepts")
    c1, c2 = st.columns(2)

    with c1:
        st.write("**Structure**")
        st.write(f"- Type: `{signal.get('structure', 'N/A')}`")
        st.write(f"- Order Block: `{signal.get('ob_type', 'N/A')}`")
        st.write(f"- Mitigated: {signal.get('ob_mitigated', False)}")
        st.write(f"- Invalidated: {signal.get('ob_invalidated', False)}")
        st.write(f"- FVG: {signal.get('fvg', 'None')}")
        st.write(f"- Liquidity Sweep: {signal.get('sweep', False)}")
        if signal.get('sweep_detail'):
            st.write(f"  - {signal['sweep_detail']}")

    with c2:
        st.write("**Market Context**")
        st.write(f"- Session: {signal.get('session', 'Unknown')}")
        st.write(f"- Session Quality: {signal.get('session_quality', 50)}%")
        regime = signal.get('regime', {})
        st.write(f"- Regime: {regime.get('regime', 'N/A')}")
        st.write(f"- ADX: {regime.get('adx', 0)}")
        st.write(f"- Vol Ratio: {regime.get('vol_ratio', 1.0)}")
        st.write(f"- Trend Strong: {signal.get('trend_strong', False)}")
        st.write(f"- EMA Cross: {signal.get('ema_cross', 'NEUTRAL')}")
        st.write(f"- MACD Trend: {signal.get('macd_trend', 'NEUTRAL')}")
        st.write(f"- VWAP: {signal.get('vwap_status', 'UNKNOWN')}")

    # Premium/Discount
    pd_info = signal.get('pd_info', {})
    st.write(f"**Premium/Discount Zone:** {pd_info.get('zone', 'UNKNOWN')} (Equilibrium: {pd_info.get('equilibrium', 0):.2f})")

    # ------------------------------------------------------------
    # Timeframe Agreement (Biases across all TFs)
    # ------------------------------------------------------------
    st.subheader("⏰ Timeframe Alignment")
    tf_biases = signal.get('tf_biases', {})
    if tf_biases:
        cols = st.columns(4)
        for i, (tf, bias_tf) in enumerate(tf_biases.items()):
            cols[i].metric(tf, bias_tf)
    else:
        st.write("No timeframe bias data available.")

    # ------------------------------------------------------------
    # Chart (simple OHLC + SMC levels) – basic plot
    # ------------------------------------------------------------
    st.subheader("📉 Price Chart (15M)")
    data_15m = signal.get('data', {}).get('15M')
    if data_15m is not None and not data_15m.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data_15m.index,
            open=data_15m['Open'],
            high=data_15m['High'],
            low=data_15m['Low'],
            close=data_15m['Close'],
            name='15M'
        ))
        # Add SMC levels if available
        if signal.get('entry'):
            fig.add_hline(y=signal['entry'], line_dash="dash", line_color="blue", annotation_text="Entry")
        if signal.get('stop'):
            fig.add_hline(y=signal['stop'], line_dash="dash", line_color="red", annotation_text="Stop")
        if signal.get('tp1'):
            fig.add_hline(y=signal['tp1'], line_dash="dash", line_color="green", annotation_text="TP1")
        if signal.get('tp2'):
            fig.add_hline(y=signal['tp2'], line_dash="dash", line_color="green", annotation_text="TP2")
        if signal.get('tp3'):
            fig.add_hline(y=signal['tp3'], line_dash="dash", line_color="green", annotation_text="TP3")

        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No 15M data to display.")

    # ------------------------------------------------------------
    # Telegram Alert (optional – send on strong signal)
    # ------------------------------------------------------------
    # Uncomment when you have the telegram_alerter.py and secrets set
    # if bias in ("BUY", "SELL"):
    #     send_telegram_alert(signal)

    # ------------------------------------------------------------
    # Data Integrity / Debug info
    # ------------------------------------------------------------
    with st.expander("🔍 Data Integrity (Debug)"):
        st.json({
            "symbol": signal.get('symbol'),
            "available_timeframes": signal.get('available_timeframes'),
            "unavailable_timeframes": signal.get('unavailable_timeframes'),
            "data_integrity": signal.get('data_integrity'),
        })

else:
    st.info("Please select an instrument from the sidebar.")
