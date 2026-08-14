import streamlit as st
import pandas as pd
from datetime import datetime, timezone

# -------------------------------------------------------------------
# 1. PAGE SETUP
# -------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------
# 2. CUSTOM ULTRA-DARK NEON STYLING (Rocket.new Aesthetic)
# -------------------------------------------------------------------
st.markdown("""
<style>
    /* Dark Theme App Base */
    .stApp {
        background-color: #0A0D14 !important;
        color: #E2E8F0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Remove Top Padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0F131C !important;
        border-right: 1px solid #1E2638;
    }

    /* Custom Card Containers */
    .card-box {
        background: #111622;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }

    /* Signal Card Header Styling */
    .signal-header {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #FFFFFF;
        margin: 0;
    }

    .signal-price {
        font-size: 24px;
        font-weight: 700;
        color: #10B981;
    }

    /* Badges */
    .badge-buy-glow {
        background: rgba(16, 185, 129, 0.1);
        border: 2px solid #10B981;
        color: #10B981;
        padding: 10px 20px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 18px;
        text-align: center;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }

    /* Circular Score Badge */
    .score-circle {
        width: 85px;
        height: 85px;
        border-radius: 50%;
        border: 5px solid #10B981;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }

    .score-value {
        font-size: 24px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
    }

    .score-label {
        font-size: 9px;
        color: #94A3B8;
        letter-spacing: 1px;
    }

    /* Target Boxes */
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

    /* Text Colors */
    .text-green { color: #10B981; }
    .text-red { color: #EF4444; }
    .text-muted { color: #94A3B8; font-size: 11px; text-transform: uppercase; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & RISK MANAGEMENT
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **SEKWAILA**")
    st.caption("OMEGA X — ANCIENT WISDOM. MODERN PROFIT.")
    st.markdown("---")
    
    view = st.radio(
        "Navigation", 
        ["🏠 Dashboard", "📊 Market Scanner", "🔥 Heatmap", "🧠 AI Narrator", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("#### **Account Risk Parameters**")
    account_bal = st.number_input("Account Balance ($)", value=500.0, step=50.0)
    risk_pct = st.slider("Risk %", 0.25, 5.0, 1.0, 0.25)
    st.caption(f"Risk Amount: **${(account_bal * risk_pct) / 100:.2f}**")

# -------------------------------------------------------------------
# 4. HEADER SECTION WITH LIVE UTC TIME
# -------------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px;">
    <div>
        <h1 style="margin:0; font-size: 28px;">👑 SEKWAILA OMEGA X</h1>
        <p style="margin:0; color: #94A3B8; font-size: 12px; letter-spacing: 0.5px;">ANCIENT WISDOM. MODERN PROFIT.</p>
    </div>
    <div style="background: #111622; border: 1px solid #10B981; padding: 6px 16px; border-radius: 20px; color: #10B981; font-weight: 600; font-size: 12px;">
        ● LIVE &nbsp;&nbsp; UTC {datetime.now(timezone.utc).strftime('%H:%M:%S')}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -------------------------------------------------------------------
# 5. TOP METRICS ROW
# -------------------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown("""
    <div class="card-box" style="padding:12px; text-align:center;">
        <div class="text-muted">🟢 BUY SETUPS</div>
        <div style="font-size:26px; font-weight:800; color:#10B981; margin-top:2px;">2</div>
        <div style="font-size:10px; color:#10B981;">↑ SP500, US30</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="card-box" style="padding:12px; text-align:center;">
        <div class="text-muted">🔴 SELL SETUPS</div>
        <div style="font-size:26px; font-weight:800; color:#EF4444; margin-top:2px;">2</div>
        <div style="font-size:10px; color:#EF4444;">↑ XAUUSD, EURUSD</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="card-box" style="padding:12px; text-align:center;">
        <div class="text-muted">🔥 ACTIVE NOW</div>
        <div style="font-size:26px; font-weight:800; color:#10B981; margin-top:2px;">2</div>
        <div style="font-size:10px; color:#10B981;">↑ SP500, US30</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown("""
    <div class="card-box" style="padding:12px; text-align:center;">
        <div class="text-muted">📡 SESSION</div>
        <div style="font-size:18px; font-weight:800; color:#F59E0B; margin-top:4px;">LONDON</div>
        <div style="font-size:10px; color:#10B981;">● Active Killzone</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    st.markdown("""
    <div class="card-box" style="padding:12px; text-align:center;">
        <div class="text-muted">💵 DXY</div>
        <div style="font-size:26px; font-weight:800; color:#10B981; margin-top:2px;">99.73</div>
        <div style="font-size:10px; color:#10B981;">▲ BULL</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------------
# 6. MAIN SIGNAL CARD & TIMEFRAME ANALYSIS
# -------------------------------------------------------------------
c1, c2 = st.columns([1.3, 1])

with c1:
    st.markdown("""
    <div class="card-box">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div class="text-muted">SIGNAL &nbsp; <b>XAUUSD</b></div>
                <div class="signal-header">GOLD SPOT</div>
                <div style="margin-top:8px;">
                    <span class="signal-price">2339.50</span>
                    <span style="color:#94A3B8; font-size:14px; margin-left:10px;">CURRENT: <b style="color:#10B981;">2341.85</b></span>
                </div>
            </div>
            <div class="score-circle">
                <div class="score-value">82</div>
                <div class="score-label">SCORE</div>
            </div>
        </div>
        
        <div style="display:flex; gap:15px; margin-top:20px; align-items:center;">
            <div class="badge-buy-glow" style="flex:1;">
                🚀 STRONG BUY
            </div>
            <div style="background:#161D2A; padding:10px 16px; border-radius:10px; border:1px solid #232D42; text-align:center;">
                <span class="text-muted">GRADE</span><br><b style="color:#10B981; font-size:18px;">A</b>
            </div>
            <div style="background:#161D2A; padding:10px 16px; border-radius:10px; border:1px solid #232D42; text-align:center;">
                <span class="text-muted">R : R</span><br><b style="color:#FFFFFF; font-size:18px;">1 : 2.8</b>
            </div>
        </div>

        <hr style="border-color:#1E293B; margin:20px 0;">

        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px;">
            <div class="target-card">
                <div class="text-muted">TP1</div>
                <div class="target-val text-green">2358.00</div>
                <div style="font-size:10px; color:#94A3B8;">+185p</div>
            </div>
            <div class="target-card">
                <div class="text-muted">TP2</div>
                <div class="target-val text-green">2371.50</div>
                <div style="font-size:10px; color:#94A3B8;">+320p</div>
            </div>
            <div class="target-card">
                <div class="text-muted">TP3</div>
                <div class="target-val text-green">2389.00</div>
                <div style="font-size:10px; color:#94A3B8;">+495p</div>
            </div>
            <div class="target-card" style="border-left: 3px solid #EF4444;">
                <div class="text-muted">STOP LOSS</div>
                <div class="target-val text-red">2328.00</div>
                <div style="font-size:10px; color:#94A3B8;">-115p</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card-box">
        <div class="text-muted" style="margin-bottom:12px;">MULTI-TIMEFRAME ANALYSIS</div>
        <table style="width:100%; color:#E2E8F0; font-size:13px; border-collapse:collapse;">
            <thead>
                <tr style="border-bottom: 1px solid #1E293B; text-align:left; color:#94A3B8;">
                    <th style="padding:8px;">TF</th>
                    <th style="padding:8px;">BIAS</th>
                    <th style="padding:8px;">STRUCTURE</th>
                    <th style="padding:8px;">ORDER BLOCK</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #161D2A;">
                    <td style="padding:10px; font-weight:bold; color:#F59E0B;">1D</td>
                    <td style="padding:10px; color:#10B981;">▲ BULLISH</td>
                    <td style="padding:10px;">BOS ↑</td>
                    <td style="padding:10px; color:#10B981;">Active</td>
                </tr>
                <tr style="border-bottom: 1px solid #161D2A;">
                    <td style="padding:10px; font-weight:bold; color:#F59E0B;">4H</td>
                    <td style="padding:10px; color:#10B981;">▲ BULLISH</td>
                    <td style="padding:10px;">CHoCH ↑</td>
                    <td style="padding:10px; color:#94A3B8;">Mitigated</td>
                </tr>
                <tr style="border-bottom: 1px solid #161D2A;">
                    <td style="padding:10px; font-weight:bold; color:#F59E0B;">1H</td>
                    <td style="padding:10px; color:#10B981;">▲ BULLISH</td>
                    <td style="padding:10px;">BOS ↑</td>
                    <td style="padding:10px; color:#10B981;">Fresh</td>
                </tr>
                <tr>
                    <td style="padding:10px; font-weight:bold; color:#F59E0B;">15M</td>
                    <td style="padding:10px; color:#10B981;">▲ BULLISH</td>
                    <td style="padding:10px;">Liquidity Sweep</td>
                    <td style="padding:10px; color:#10B981;">Active</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
