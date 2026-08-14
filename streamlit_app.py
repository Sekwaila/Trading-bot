import streamlit as st
import pandas as pd
from datetime import datetime, timezone

# Defensive Config Imports
try:
    from config import (
        ASSETS, DEFAULT_MIN_TF_AGREEMENT, DEFAULT_MIN_SCORE, DEFAULT_MIN_RR,
        WORKER_POLL_SECONDS
    )
except Exception as _cfg_exc:
    ASSETS = {"XAUUSD": "Gold Spot", "BTCUSD": "Bitcoin"}
    DEFAULT_MIN_TF_AGREEMENT = 2
    DEFAULT_MIN_SCORE = 70.0
    DEFAULT_MIN_RR = 1.5
    WORKER_POLL_SECONDS = 300

# Safe Module Imports
try:
    from settings_store import load_settings
except Exception:
    load_settings = lambda: {"ai": {"enabled": False}}

try:
    from Signals.signal_engine import generate_omega_signal
except Exception as _engine_exc:
    generate_omega_signal = None
    _engine_exc_msg = str(_engine_exc)

try:
    import news
except Exception:
    news = None

try:
    import ai_provider
except Exception:
    ai_provider = None

try:
    from telegram_bot import send_telegram_signal
except Exception:
    send_telegram_signal = lambda *args, **kwargs: False

# -------------------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM DARK NEON CSS
# -------------------------------------------------------------------
st.set_page_config(
    page_title="SEKWAILA OMEGA X",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #111622 !important; border-right: 1px solid #1E2638; }
    .metric-card { background: #131A27; border: 1px solid #1E293B; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 12px; }
    .metric-value-green { font-size: 24px; font-weight: 700; color: #10B981; }
    .metric-value-red { font-size: 24px; font-weight: 700; color: #EF4444; }
    .metric-label { font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; }
    .signal-container { background: linear-gradient(145deg, #131A27, #0F141F); border: 1px solid #1E293B; border-radius: 16px; padding: 20px; }
    .badge-buy { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #10B981; padding: 8px 16px; border-radius: 8px; font-weight: 800; font-size: 18px; text-align: center; }
    .badge-sell { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF4444; padding: 8px 16px; border-radius: 8px; font-weight: 800; font-size: 18px; text-align: center; }
    .tp-box { background: #1A2333; border-radius: 8px; padding: 10px; text-align: center; border-left: 3px solid #10B981; }
    .sl-box { background: #1A2333; border-radius: 8px; padding: 10px; text-align: center; border-left: 3px solid #EF4444; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SIDEBAR NAVIGATION & RISK CALCULATOR
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **SEKWAILA**")
    st.caption("OMEGA X ENGINE v2.4")
    st.markdown("---")
    
    symbols = list(ASSETS.keys()) if ASSETS else ["XAUUSD"]
    selected = st.selectbox("🎯 Asset Focus", symbols)
    
    st.markdown("---")
    st.markdown("#### ⚙️ **Confluence Rules**")
    min_tf = st.slider("Min TF Agreement", 1, 4, int(DEFAULT_MIN_TF_AGREEMENT))
    min_score = st.slider("Min Score Cutoff", 0.0, 100.0, float(DEFAULT_MIN_SCORE))
    min_rr = st.number_input("Min Risk:Reward", 0.1, 10.0, float(DEFAULT_MIN_RR), 0.1)

    st.markdown("---")
    st.markdown("#### 🧮 **Risk Calculator**")
    account_size = st.number_input("Account Balance ($)", min_value=10.0, value=500.0, step=50.0)
    risk_pct = st.slider("Risk Per Trade %", 0.25, 5.0, 1.0, 0.25)
    st.caption(f"Risk Amount: **${(account_size * risk_pct) / 100.0:.2f}**")

# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
h1, h2 = st.columns([3, 1])
with h1:
    st.title("👑 SEKWAILA OMEGA X")
    st.caption(f"LIVE FEED — {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
with h2:
    st.markdown('<div style="background:#131A27; padding:8px 16px; border-radius:20px; border:1px solid #1E293B; text-align:center;"><span style="color:#10B981;">● ENGINE LIVE</span></div>', unsafe_allow_html=True)

st.markdown("---")

# Quick Stats
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.markdown('<div class="metric-card"><div class="metric-label">BUY SETUPS</div><div class="metric-value-green">4</div></div>', unsafe_allow_html=True)
with m2: st.markdown('<div class="metric-card"><div class="metric-label">SELL SETUPS</div><div class="metric-value-red">1</div></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric-card"><div class="metric-label">ACTIVE SIGNAL</div><div class="metric-value-green">1</div></div>', unsafe_allow_html=True)
with m4: st.markdown('<div class="metric-card"><div class="metric-label">SESSION</div><div style="font-size:16px; font-weight:bold; color:#F59E0B; margin-top:5px;">LONDON</div></div>', unsafe_allow_html=True)
with m5: st.markdown('<div class="metric-card"><div class="metric-label">DXY BIAS</div><div class="metric-value-red">99.89 ▼</div></div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# SIGNAL SCANNER
# -------------------------------------------------------------------
if generate_omega_signal is not None:
    with st.spinner(f"Scanning market structure for {selected}..."):
        try:
            result = generate_omega_signal(selected, ASSETS.get(selected), min_tf=min_tf, min_score=min_score, min_rr=min_rr)
        except Exception as exc:
            result = {"ok": False, "symbol": selected, "reason": str(exc)}
else:
    result = {"ok": False, "symbol": selected, "reason": f"Engine module import error: {_engine_exc_msg}"}

col_main, col_mtf = st.columns([1.2, 1])

if result.get("ok"):
    bias = result.get("bias", "NEUTRAL")
    score = result.get("score", 0.0)
    entry = result.get("entry_price") or result.get("entry", 0.0)
    sl = result.get("stop_loss") or result.get("stop", 0.0)
    tp1 = result.get("tp1", 0.0)
    tp2 = result.get("tp2", 0.0)

    with col_main:
        st.markdown(f"### 📍 **TOP SIGNAL — {selected}**")
        badge_style = "badge-buy" if bias == "BUY" else "badge-sell"
        st.markdown(f"""
        <div class="signal-container">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="margin:0;">{selected}</h2>
                    <p style="color:#94A3B8; margin:0;">Entry: <b>{entry:.2f}</b></p>
                </div>
                <div class="{badge_style}">
                    {"🔥 STRONG BUY" if bias == "BUY" else "🔴 STRONG SELL"}
                </div>
            </div>
            <hr style="border-color:#1E293B; margin:15px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>Signal Quality Score:</span>
                <span style="font-size:20px; font-weight:bold; color:#10B981;">{score}%</span>
            </div>
            <div style="background:#1E293B; height:8px; border-radius:4px; margin-top:5px; overflow:hidden;">
                <div style="background:#10B981; width:{score}%; height:100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        p1, p2, p3 = st.columns(3)
        with p1: st.markdown(f'<div class="tp-box"><div class="metric-label">TP 1</div><div style="color:#10B981; font-weight:bold;">{tp1:.2f}</div></div>', unsafe_allow_html=True)
        with p2: st.markdown(f'<div class="tp-box"><div class="metric-label">TP 2</div><div style="color:#10B981; font-weight:bold;">{tp2:.2f}</div></div>', unsafe_allow_html=True)
        with p3: st.markdown(f'<div class="sl-box"><div class="metric-label">STOP LOSS</div><div style="color:#EF4444; font-weight:bold;">{sl:.2f}</div></div>', unsafe_allow_html=True)

    with col_mtf:
        st.markdown("### 📊 **MULTI-TIMEFRAME ALIGNMENT**")
        df_mtf = pd.DataFrame({
            "Timeframe": ["1D", "4H", "1H", "15M"],
            "Bias": ["🟢 BULLISH", "🟢 BULLISH", "🔴 BEARISH", "🟢 BULLISH"],
            "Structure": ["BOS ↑", "CHoCH ↑", "Range", "Liquidity Sweep"],
            "Order Block": ["Active", "Mitigated", "Fresh", "Active"]
        })
        st.dataframe(df_mtf, use_container_width=True, hide_index=True)
else:
    st.error(f"Engine Notice for {selected}: {result.get('reason')}")

# -------------------------------------------------------------------
# INTELLIGENCE SECTION
# -------------------------------------------------------------------
st.markdown("---")
exp1, exp2 = st.columns(2)

with exp1:
    with st.expander("📰 News Intelligence"):
        if news:
            headlines, _ = news.fetch_news_for_asset(selected)
            if headlines:
                for h in headlines[:5]: st.markdown(f"- {h}")
            else: st.info("No high-impact news detected.")
        else: st.info("News module offline.")

with exp2:
    with st.expander("🧠 AI SMC Market Narrator"):
        if ai_provider:
            if st.button("Generate Narrative"):
                st.write(ai_provider.summarize_signal(result))
        else: st.info("AI provider module offline.")
