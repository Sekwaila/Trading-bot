"""
SEKWAILA OMEGA X — STREAMLIT DASHBOARD
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import ASSETS
from signals.signal_engine import generate_omega_signal
from database import load_journal, save_journal_entry
from trade_manager import calculate_position_size
from telegram_bot import send_telegram_message

st.set_page_config(page_title="SEKWAILA OMEGA X", page_icon="👑", layout="wide")

st.title("👑 SEKWAILA OMEGA X — SMC DASHBOARD")

sidebar_asset = st.sidebar.selectbox("Select Asset", list(ASSETS.keys()))
min_tf = st.sidebar.slider("Min Timeframe Agreement", 2, 4, 3)

res = generate_omega_signal(sidebar_asset, ASSETS[sidebar_asset], min_tf)

if res["ok"]:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BIAS", res["bias"])
    col2.metric("OMEGA SCORE", f"{res['score']}/100")
    col3.metric("ENTRY", f"{res['entry']:.2f}")
    col4.metric("R:R", f"{res['rr']:.2f}R")
    
    df_15m = res["data"]["15M"].tail(100)
    fig = go.Figure(data=[go.Candlestick(
        x=df_15m.index, open=df_15m["Open"], high=df_15m["High"],
        low=df_15m["Low"], close=df_15m["Close"]
    )])
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("Save Signal to Journal"):
        save_journal_entry({
            "asset": res["symbol"], "bias": res["bias"],
            "score": res["score"], "entry": res["entry"]
        })
        st.success("Entry saved!")
else:
    st.error(f"Error generating signal: {res.get('reason')}")
