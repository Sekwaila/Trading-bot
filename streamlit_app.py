import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & DARK THEME STYLING
# ==========================================
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS matching the dark Replit UI
st.markdown("""
<style>
    /* Dark Background */
    .stApp {
        background-color: #0b0e14;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Metric Box / Cards */
    .setup-card {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .setup-title {
        font-size: 13px;
        color: #8b949e;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .setup-number {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
        margin: 4px 0;
    }
    .badge-green {
        background: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Top Signal Card */
    .signal-card {
        background: #121721;
        border: 1px solid #238636;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
    }
    .signal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .signal-title {
        font-size: 28px;
        font-weight: 900;
        color: #ffffff;
    }
    .signal-price {
        font-size: 20px;
        color: #3fb950;
        font-weight: 700;
    }
    .btn-buy-now {
        background: #238636;
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 12px;
        display: inline-block;
        margin-top: 6px;
    }
    
    /* Alert Cards */
    .alert-card-green {
        background: #121721;
        border-left: 4px solid #3fb950;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .alert-card-yellow {
        background: #121721;
        border-left: 4px solid #d29922;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    
    /* Hide Default Elements */
    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.markdown("### ⚡ **SEKWAILA**")
    st.caption("OMEGA X ENGINE")
    
    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard", 
            "📊 Market Scanner", 
            "🔥 Heatmap", 
            "🤖 AI Narrator", 
            "📰 News Intelligence", 
            "📈 Multi-Timeframe", 
            "🔗 Correlation Matrix", 
            "📓 Trade Journal", 
            "📉 Performance", 
            "📲 Telegram Alerts", 
            "⚙️ Settings", 
            "❓ Help"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("#### **Account Setup**")
    account_bal = st.number_input("Account (R)", value=500.00, step=50.00)
    risk_pct = st.slider("Risk %", min_value=0.25, max_value=5.00, value=1.00, step=0.25)
    st.caption(f"≈ USD ${round(account_bal / 18.5, 2)} | Risk: R{round(account_bal * (risk_pct/100), 2)}")
    
    st.markdown("---")
    auto_scan = st.toggle("⏱️ Live Auto-Scan", value=True)
    scan_interval = st.slider("Interval (s)", 10, 120, 60)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 3. HELPER GAUGE CHART
# ==========================================
def create_gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#30363d"},
            'bar': {'color': "#3fb950"},
            'bgcolor': "#161b22",
            'borderwidth': 1,
            'bordercolor': "#30363d",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(248, 81, 73, 0.2)'},
                {'range': [40, 70], 'color': 'rgba(210, 153, 34, 0.2)'},
                {'range': [70, 100], 'color': 'rgba(63, 185, 80, 0.2)'}
            ],
        }
    ))
    fig.update_layout(
        height=140, 
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#ffffff", size=14)
    )
    return fig

# ==========================================
# 4. MAIN DASHBOARD CONTENT
# ==========================================
if "Dashboard" in page:
    
    # --- TOP SETUP SUMMARY METRICS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="setup-card">
            <div class="setup-title">🟢 BUY Setups</div>
            <div class="setup-number">3</div>
            <div class="badge-green">↑ SP500, US30, BTCUSD</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="setup-card">
            <div class="setup-title">🔴 SELL Setups</div>
            <div class="setup-number">0</div>
            <div class="badge-green">↑ —</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="setup-card">
            <div class="setup-title">🔥 ACTIVE NOW</div>
            <div class="setup-number">2</div>
            <div class="badge-green">↑ SP500, US30</div>
        </div>
        """, unsafe_allow_html=True)
        
    c4, c5 = st.columns(2)
    with c4:
        st.markdown("""
        <div class="setup-card">
            <div class="setup-title">📡 Session</div>
            <div class="setup-number" style="font-size:22px;">NEW YORK</div>
            <div class="badge-green">↑ No killzone</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown("""
        <div class="setup-card">
            <div class="setup-title">💲 DXY</div>
            <div class="setup-number" style="font-size:22px;">99.60</div>
            <div class="badge-green">↑ BEAR ▼</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- MAIN TOP SIGNAL CARD & GAUGE ---
    st.markdown("### 🎯 Top Active Trade Signal")
    sig_col1, sig_col2 = st.columns([3, 2])
    
    with sig_col1:
        st.markdown("""
        <div class="signal-card">
            <div class="signal-header">
                <div>
                    <span style="color:#8b949e; font-size:11px; font-weight:bold;">TOP SIGNAL</span>
                    <div class="signal-title">SP500</div>
                    <div class="signal-price">7755.61 <span style="font-size:12px; color:#3fb950;">+0.081%</span></div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#3fb950; font-size:28px; font-weight:900;">77%</div>
                    <div style="color:#d29922; font-size:10px; font-weight:bold;">MED QUALITY</div>
                </div>
            </div>
            <div style="margin-top:10px;">
                <span class="btn-buy-now">🔥 BUY NOW</span>
                <span style="background:#8957e5; color:white; padding:4px 8px; border-radius:4px; font-size:10px; font-weight:bold; margin-left:6px;">SWING</span>
            </div>
            <hr style="border-color:#21262d; margin:12px 0;"/>
            <div style="display:flex; justify-content:space-between; font-size:12px;">
                <div><b>ENTRY:</b> 7755.61<br/><span style="color:#3fb950;"><b>TP1:</b> 7769.99</span><br/><span style="color:#3fb950;"><b>TP2:</b> 7784.37</span></div>
                <div><span style="color:#f85149;"><b>SL:</b> 7741.23</span><br/><b>R:R:</b> 1:1.00<br/><b>ADX:</b> 15.7 | <b>RSI:</b> 58.6</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with sig_col2:
        st.markdown("##### **Signal Score Gauge**")
        st.plotly_chart(create_gauge(77), use_container_width=True)
        st.markdown("""
        <div style="font-size:11px; background:#121721; padding:8px; border-radius:6px; border:1px solid #1e2638;">
            <b>Trend Strength:</b> 90/100<br/>
            <b>Momentum Score:</b> 67/100<br/>
            <b>Position Rating:</b> 63/100
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- QUICK QUESTIONS / AI ASSISTANT ---
    st.markdown("### 💬 Quick AI Analysis")
    focus_asset = st.selectbox("Focus instrument", ["BTCUSD", "SP500", "US30", "XAUUSD", "EURUSD"])
    
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        if st.button(f"📊 Analyse {focus_asset}", use_container_width=True):
            st.info(f"Analyzing structure, order blocks, and BOS for {focus_asset}...")
        if st.button("💰 R500 Risk Plan", use_container_width=True):
            st.info("Calculating optimal lot sizing based on R500 capital balance...")
    with q_col2:
        if st.button("🔥 Best Trade Now", use_container_width=True):
            st.success("SP500 shows highest probability setup (77% confidence).")
        if st.button("📰 News Warnings", use_container_width=True):
            st.warning("No high-impact USD economic events scheduled for current session.")
    with q_col3:
        if st.button("⚠️ Market Risks", use_container_width=True):
            st.warning("DXY weakening. High correlation detected between SP500 and US30.")

    prompt = st.chat_input("Ask SEKWAILA AI... e.g. 'Should I buy gold now?'")
    if prompt:
        st.write(f"**You:** {prompt}")
        st.write(f"**SEKWAILA AI:** Analyzed market structure for {focus_asset}. Trend remains bullish supported by higher-timeframe order blocks.")

    st.markdown("---")

    # --- MARKET STRENGTH BARS ---
    st.markdown("### 📊 Market Strength Overview")
    assets = [
        {"name": "SP500", "price": "7755.61", "status": "BUY", "val": 77, "color": "#3fb950"},
        {"name": "US30", "price": "54029.50", "status": "BUY", "val": 75, "color": "#3fb950"},
        {"name": "BTCUSD", "price": "65050.00", "status": "WEAK BUY", "val": 60, "color": "#2ea043"},
        {"name": "EURUSD", "price": "1.15620", "status": "NEUTRAL", "val": 47, "color": "#8b949e"},
        {"name": "XAUUSD", "price": "4399.70", "status": "NEUTRAL", "val": 51, "color": "#8b949e"},
        {"name": "DXY", "price": "99.60", "status": "BEAR", "val": 35, "color": "#f85149"}
    ]

    for item in assets:
        st.markdown(f"**{item['name']}** — `{item['price']}` | <span style='color:{item['color']}; font-weight:bold;'>{item['status']} {item['val']}%</span>", unsafe_allow_html=True)
        st.progress(item['val'] / 100)

    st.markdown("---")

    # --- RECENT SIGNAL ALERTS LOG ---
    st.markdown("### 🔔 Recent Signal Alerts")
    
    st.markdown("""
    <div class="alert-card-green">
        <div style="display:flex; justify-content:space-between; font-size:12px;">
            <b>🟢 US30 — BUY</b> <span style="color:#8b949e;">17:54:52</span>
        </div>
        <div style="font-size:11px; margin-top:4px;">Score: 75/100 · Grade: A · Price: 54029.50 · TP: 54116.50 · SL: 53942.50</div>
    </div>
    <div class="alert-card-yellow">
        <div style="display:flex; justify-content:space-between; font-size:12px;">
            <b>⚠️ US30 — Score jumped to 75</b> <span style="color:#8b949e;">17:54:52</span>
        </div>
        <div style="font-size:11px; margin-top:4px;">Score: 75/100 · Grade: A · Price: 54029.50 · TP: 54116.50 · SL: 53942.50</div>
    </div>
    <div class="alert-card-green">
        <div style="display:flex; justify-content:space-between; font-size:12px;">
            <b>🟢 SP500 — BUY</b> <span style="color:#8b949e;">17:54:52</span>
        </div>
        <div style="font-size:11px; margin-top:4px;">Score: 77/100 · Grade: A · Price: 7755.61 · TP: 7769.99 · SL: 7741.23</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Alerts"):
        st.success("Alert log cleared.")
